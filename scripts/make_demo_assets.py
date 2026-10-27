"""Build isolated, deterministic synthetic fixtures; never performance evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from pipeline import LABELS, TrainOnlyBank, run_event, task_vector

DEMO_MARKER = "synthetic-demo.v1"


def make_demo_assets(destination=None, source=ROOT):
    destination = Path(destination or ROOT / "runtime/synthetic-demo").resolve()
    # Do not overwrite a user's local assets or another delivery.
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("Demo destination is not empty; choose another directory")
    if destination == Path(source).resolve():
        raise ValueError("demo_destination_must_be_separate")
    rng = np.random.default_rng(42)
    data = destination / "evidence/fresh17"
    data.mkdir(parents=True)
    web = destination / "web"
    shutil.copytree(Path(source) / "web", web, ignore=shutil.ignore_patterns("data.js"))
    embeddings = rng.normal(size=(17, 512))
    embeddings /= np.linalg.norm(embeddings, axis=1)[:, None]
    vectors, ids, labels, events = [], [], [], []
    model_hash = hashlib.sha256(b"SYNTHETIC-NO-MODEL").hexdigest()
    for label in range(17):
        probs = (np.eye(17)[label] * 0.85 + np.ones(17) * (0.15 / 17)).tolist()
        for index in range(5):
            vectors.append(task_vector(embeddings[label] + rng.normal(0, 0.001, 512), probs))
            ids.append(f"synthetic-train-{label:02}-{index}")
            labels.append(label)
        events.append(
            {
                "event_id": f"synthetic-event-{label:02}",
                "prediction": label,
                "validation_label": label,
                "confidence": max(probs),
                "probabilities": probs,
                "embedding": embeddings[label].tolist(),
                "representation_id": DEMO_MARKER,
                "model_sha256": model_hash,
                "pred_ctbm": label,
                "pred_pbcnn": label,
                "mode": "synthetic_fixture",
                "synthetic": True,
                "execution_mode": "synthetic_demo",
            }
        )
    bank_path = data / "train_bank.npz"
    np.savez(
        bank_path,
        vectors=np.asarray(vectors),
        ids=np.array(ids),
        labels=np.array(labels),
        splits=np.array(["train"] * len(ids)),
    )
    manifest = {
        "npz_sha256": hashlib.sha256(bank_path.read_bytes()).hexdigest(),
        "label_order": LABELS,
        "representation_id": DEMO_MARKER,
        "model_sha256": model_hash,
        "synthetic": True,
    }
    (data / "train_bank_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    bank = TrainOnlyBank.load(bank_path, data / "train_bank_manifest.json")
    for event in events:
        event["result"] = run_event(event, bank)
        event["evidence"] = event["result"]["evidence"]
    (data / "events.json").write_text(json.dumps(events), encoding="utf-8")
    np.savez(data / "live_inputs_private.npz", event_ids=np.array([], dtype="U1"))
    summary = {
        "synthetic": True,
        "labels": LABELS,
        "bank_rows": len(ids),
        "queries": len(events),
        "detection": {},
        "fresh_retrieval": None,
        "local_judge": None,
        "judge_comparison": [],
        "network": None,
        "faults": None,
    }
    public = [
        {k: v for k, v in event.items() if k not in {"embedding", "model_sha256"}}
        for event in events
    ]
    (web / "data.js").write_text(
        "window.FINAL_DATA="
        + json.dumps({"summary": summary, "events": public}, ensure_ascii=False, allow_nan=False)
        + ";\n",
        encoding="utf-8",
    )
    (destination / "demo.json").write_text(
        json.dumps({"kind": DEMO_MARKER, "synthetic": True}), encoding="utf-8"
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(make_demo_assets(args.output))
    print("Synthetic data only. No model inference, LLM response or network action.")


if __name__ == "__main__":
    main()
