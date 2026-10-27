"""Rebuild 17-class train-only retrieval using frozen, verified IDS checkpoints.

New experiment: deterministic first 100 real train rows/class, first 30 test
rows/class. Does not reproduce historical 1550/463 selection or B's 522D FE-Net.
No test labels are used by models, Gate fitting, representations or retrieval.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import time
import types
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from pipeline import LABELS, TrainOnlyBank, task_vector, digest, run_event

from settings import asset_path, optional_asset_path
REF = asset_path("ids_reference_root")
DATA = asset_path("ids_data_root")
OUT = ROOT / "evidence" / "fresh17"
MODEL_ROOT = REF / "models" / "augmented" / "seed_42"
REPRESENTATION = "ctbm512_plus_frozen_gate17_concat_l2.v1"


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def model_module(path, name):
    """Omit optional plotting imports/config only; preserve model definitions."""
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    def keep(node):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("matplotlib"): return False
        if isinstance(node, ast.Import) and any(x.name.startswith("matplotlib") for x in node.names): return False
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call): return False
        if isinstance(node, ast.Assign) and any("plt." in ast.unparse(x) for x in node.targets): return False
        return True
    tree.body = [n for n in tree.body if keep(n)]
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def load_gate():
    p = optional_asset_path("gate_impl_path",REF.parent / "gate_soft_oof_search.py")
    spec = importlib.util.spec_from_file_location("frozen_gate_impl", p)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    conf = json.loads((REF / "gate_results/augmented/seed_42/gate_summary.json").read_text(encoding="utf-8"))
    va = g.read(REF / "gate_exports/augmented/seed_42/ctbm_validation_predictions.csv")
    vb = g.read(REF / "gate_exports/augmented/seed_42/pbcnn_validation_predictions.csv")
    g.align(va, vb)
    t = conf["branch_temperatures"]
    ca, cb = g.temp(va["p"], t["ctbm"]), g.temp(vb["p"], t["pbcnn"])
    w = conf["winner"]
    gate = g.fit_gate(ca, cb, va["y"], w["C"], None, w["minority_power"], seed=42)
    def infer(a, b):
        ca, cb = g.temp(a, t["ctbm"]), g.temp(b, t["pbcnn"])
        mixed = g.temp(g.soft_route(ca, cb, gate, 1, w["beta"], w["q_power"]), conf["output_temperature"])
        fallback = g.temp(ca, conf["output_temperature"])
        mask = np.isin(mixed.argmax(1), conf["guarded_classes"]) & (mixed.argmax(1) != fallback.argmax(1))
        mixed[mask] = fallback[mask]
        return mixed
    return infer


def select_rows(path, limit, ctbm):
    selected = []
    counts = Counter()
    source_hash = hashlib.sha256()
    with path.open("rb") as f:
        for index, line in enumerate(f):
            source_hash.update(line)
            row = json.loads(line)
            if ctbm.is_synthetic_record(row): continue
            name = ctbm.read_fine_label(row)
            if name not in LABELS or counts[name] >= limit: continue
            counts[name] += 1
            identity = ctbm.get_flow_id(row)
            selected.append({"row": row, "source_row": index, "id": identity, "label": LABELS.index(name)})
    print("SELECTED", path.name, len(selected), dict(counts), flush=True)
    return selected, source_hash.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    np.random.seed(42)
    torch.backends.cudnn.benchmark = False
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ctbm = model_module(REF / "runtime_sources/ctbm_full_none_real_only_seed_42.py", "final_ctbm_runtime")
    pbcnn = model_module(REF / "runtime_sources/SMOTE_校準式類別感知Gate動態融合訓練_nofilm.py", "final_pbcnn_runtime")
    checkpoints = {name: torch.load(MODEL_ROOT / name / "best_model.pt", map_location="cpu", weights_only=False)
                   for name in ["CTBM_Full", "PBCNN_M1", "PBCNN_M2"]}
    ck = checkpoints["CTBM_Full"]
    if ck["idx_to_label"] != LABELS: raise ValueError("checkpoint_label_order_mismatch")
    models = {"CTBM_Full": ctbm.build_model_for_stage("rgb_time_heat", 17, ck["hparams"])}
    for name, classes, cls in [("PBCNN_M1", 2, pbcnn.PBCNNM1Classifier), ("PBCNN_M2", 16, pbcnn.PBCNNM2Classifier)]:
        hp = checkpoints[name]["hparams"]
        models[name] = cls(classes, hp["h_dim"], hp["dropout"])
    for name, model in models.items():
        model.load_state_dict(checkpoints[name]["model_state_dict"], strict=True)
        model.to(device).eval()
    model_hashes = {name: sha(MODEL_ROOT / name / "best_model.pt") for name in models}
    combined_hash = digest(model_hashes)
    gate_infer = load_gate()
    train, train_hash = select_rows(DATA / "SMOTE_train.jsonl", 100, ctbm)
    queries, test_hash = select_rows(DATA / "SMOTE_test.jsonl", 30, ctbm)
    if set(x["id"] for x in train) & set(x["id"] for x in queries): raise ValueError("train_test_id_overlap")
    print("MODELS_READY", str(device), flush=True)

    def infer(rows):
        embeddings, probs, blue, latencies, c_preds, p_preds = [], [], [], [], [], []
        for start in range(0, len(rows), 16):
            chunk = rows[start:start+16]
            rgb_features = [ctbm.build_rgb_tensor(x["row"]) for x in chunk]
            byte_features = [pbcnn.build_pbcnn_input(x["row"]) for x in chunk]
            tensors = [torch.from_numpy(np.stack([x[i] for x in rgb_features])).to(device) for i in range(4)]
            bx = torch.from_numpy(np.stack([x[0] for x in byte_features])).to(device)
            bm = torch.from_numpy(np.stack([x[1] for x in byte_features])).to(device)
            if device.type == "cuda": torch.cuda.synchronize()
            begin = time.perf_counter()
            with torch.inference_mode():
                out = models["CTBM_Full"](x_a=tensors[0], x_rgb=tensors[1], mask_rgb=tensors[2], direction_ids=tensors[3])
                m1 = models["PBCNN_M1"](bx, mask_a=bm)
                m2 = models["PBCNN_M2"](bx, mask_a=bm)
                threshold = checkpoints["PBCNN_M1"]["hparams"].get("m1_attack_threshold", 0.5)
                active = torch.softmax(m1["logits"], 1)[:, 1] >= threshold
                pp, _ = pbcnn.hierarchical_pbcnn_distribution(m1["logits"], m2["logits"], active)
                cp = torch.softmax(out["logits"], 1).cpu().numpy()
                pp = pp.cpu().numpy()
                e = out["z_B"].cpu().numpy()
            gp = gate_infer(cp, pp)
            if device.type == "cuda": torch.cuda.synchronize()
            latency = (time.perf_counter() - begin) * 1000
            embeddings.extend(e)
            probs.extend(gp)
            c_preds.extend(cp.argmax(1).tolist())
            p_preds.extend(pp.argmax(1).tolist())
            # Real model heat output only, if present. No invented heat values.
            heat_key = next((k for k in out if "blue" in k.lower() and hasattr(out[k], "shape") and len(out[k].shape) == 2), None)
            blue.extend(out[heat_key].cpu().numpy().tolist() if heat_key else [None] * len(chunk))
            latencies.append({"batch_size": len(chunk), "milliseconds": latency})
            print("INFER", start + len(chunk), "/", len(rows), flush=True)
        return np.asarray(embeddings), np.asarray(probs), blue, latencies, c_preds, p_preds

    te, tp, _, train_latency, _, _ = infer(train)
    qe, qp, heat, query_latency, cpred, ppred = infer(queries)
    # Validate fresh inference against the existing sealed predictions before reporting.
    frozen = pd.read_csv(REF / "gate_results/augmented/seed_42/test_predictions.csv").set_index("flow_id")
    expected = np.array([int(frozen.loc[x["id"], "pred_gate"]) for x in queries])
    agreement = float(np.mean(expected == qp.argmax(1)))
    dump(OUT / "fresh_prediction_alignment.json", {"queries": len(queries), "agreement": agreement,
        "mismatches": int(np.sum(expected != qp.argmax(1))), "claim": "fresh checkpoint inference vs frozen Gate prediction"})
    if agreement != 1.0: raise RuntimeError("fresh_prediction_alignment_failed; investigate before retrieval claims")
    tv = np.asarray([task_vector(e, p) for e, p in zip(te, tp)])
    qv = np.asarray([task_vector(e, p) for e, p in zip(qe, qp)])
    train_ids = ["train-" + hashlib.sha256(x["id"].encode()).hexdigest()[:20] for x in train]
    bank_path = OUT / "train_bank.npz"
    np.savez_compressed(bank_path, vectors=tv, ids=np.array(train_ids), labels=np.array([x["label"] for x in train]),
                        splits=np.array(["train"] * len(train)))
    bank_manifest = {"npz_sha256": sha(bank_path), "label_order": LABELS, "representation_id": REPRESENTATION,
                     "model_sha256": combined_hash, "selection": "first 100 real rows per class in original train order",
                     "source_split_sha256": train_hash, "rows": len(train), "model_hashes": model_hashes,
                     "query_labels_used_in_representation": False}
    dump(OUT / "train_bank_manifest.json", bank_manifest)
    bank = TrainOnlyBank.load(bank_path, OUT / "train_bank_manifest.json")
    events, hits, rr, purities, timings = [], [], [], [], []
    for i, item in enumerate(queries):
        event_id = "event-" + hashlib.sha256(item["id"].encode()).hexdigest()[:20]
        start = time.perf_counter()
        evidence = bank.retrieve(qv[i], event_id, REPRESENTATION, combined_hash)
        timings.append((time.perf_counter() - start) * 1000)
        matches = [e["label_id"] == item["label"] for e in evidence]
        hits.append(any(matches)); rr.append(1 / (matches.index(True) + 1) if any(matches) else 0)
        purities.append(sum(matches) / 5)
        event = {"event_id": event_id, "prediction": int(qp[i].argmax()), "probabilities": qp[i].tolist(),
                 "confidence": float(qp[i].max()), "embedding": qe[i].tolist(), "representation_id": REPRESENTATION,
                 "model_sha256": combined_hash, "mode": "fresh_checkpoint_inference_saved_replay",
                 "validation_label": item["label"], "source_split": "test", "pred_ctbm": cpred[i], "pred_pbcnn": ppred[i],
                 "blue_heat": heat[i], "evidence": evidence}
        result = run_event(event, bank)
        event["result"] = result
        events.append(event)
    dump(OUT / "events.json", events)
    # Byte tensors for a small live rerun are private and remain outside web/.
    selected = []
    seen = set()
    for i, item in enumerate(queries):
        if item["label"] not in seen:
            selected.append(i); seen.add(item["label"])
    tensors = [ctbm.build_rgb_tensor(queries[i]["row"]) for i in selected]
    bytes_inputs = [pbcnn.build_pbcnn_input(queries[i]["row"]) for i in selected]
    np.savez_compressed(OUT / "live_inputs_private.npz", temporal=np.stack([x[0] for x in tensors]),
                        content=np.stack([x[1] for x in tensors]), mask=np.stack([x[2] for x in tensors]),
                        directions=np.stack([x[3] for x in tensors]), bytes=np.stack([x[0] for x in bytes_inputs]),
                        byte_mask=np.stack([x[1] for x in bytes_inputs]), event_ids=np.array([events[i]["event_id"] for i in selected]))
    dump(OUT / "query_manifest_private.json", [{"event_id": e["event_id"], "source_row": x["source_row"],
         "original_id": x["id"], "validation_label": x["label"]} for e, x in zip(events, queries)])
    summary = {"experiment": "new 17-class CTBM+Gate task-vector retrieval rebuild", "seed": 42,
               "bank_rows": len(train), "queries": len(queries), "label_count": 17,
               "selection": "first 100 real train and first 30 real test rows per class, source order; no tuning on query labels",
               "top5": float(np.mean(hits)), "mrr5": float(np.mean(rr)), "precision5": float(np.mean(purities)),
               "query_class_counts": dict(Counter(LABELS[x["label"]] for x in queries)),
               "train_class_counts": dict(Counter(LABELS[x["label"]] for x in train)),
               "fresh_prediction_agreement": agreement, "test_source_sha256": test_hash,
               "train_test_id_overlap": 0, "representation_id": REPRESENTATION,
               "inference_batch_measurements": query_latency, "retrieval_ms_median": float(np.median(timings)),
               "device": str(device), "llm_calls": 0,
               "llm_status": "manual_review_until_configured_authorized_model_response",
               "scope": "new bounded integration experiment, not the historical 1550/463 or Fine-11 FE-Net experiment"}
    dump(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__": main()
