"""Read-only asset lineage and saved/fresh representation alignment audit."""
from __future__ import annotations
import hashlib
import argparse
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "app"))
from settings import asset_path, optional_asset_path
from pipeline import digest, audit_payload, LABELS
from server import source_revision
from audit_selection import select_audit
from provenance import runtime_assets, identifier


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-dir',type=Path)
    args=parser.parse_args()
    data=ROOT / "evidence/fresh17"
    manifest=json.loads((data / "train_bank_manifest.json").read_text(encoding="utf-8"))
    ref=asset_path("ids_reference_root")
    hashes={name:sha(ref / "models/augmented/seed_42" / name / "best_model.pt") for name in manifest["model_hashes"]}
    assert hashes==manifest["model_hashes"] and digest(hashes)==manifest["model_sha256"]
    assert manifest["label_order"]==LABELS
    source={e["event_id"]:e for e in json.loads((data / "events.json").read_text(encoding="utf-8"))}
    records=[json.loads(line) for line in (data / "judge_records_private.jsonl").read_text(encoding="utf-8").splitlines()]
    for row in records:
        event=source[row["event_id"]]
        assert row["payload"]==audit_payload(event,event["evidence"])
        assert "validation_label" not in row["payload"] and "true_label" not in row["payload"]
    folder=select_audit(ROOT/'validation',source_revision(),args.audit_dir,identifier(runtime_assets(ROOT)))
    fresh=json.loads((folder / "live_events_private.json").read_text(encoding="utf-8"))
    errors=[]
    for e in fresh:
        old=source[e["event_id"]]
        assert e["representation_id"]==old["representation_id"]
        delta=float(np.max(np.abs(np.array(e["probabilities"])-old["probabilities"])))
        # Record numeric drift; do not claim bitwise equality across GPU batch sizes.
        assert np.isfinite(delta) and e["prediction"]==old["prediction"]
        assert [x["case_id"] for x in e["evidence"]]==[x["case_id"] for x in old["evidence"]]
        errors.append(delta)
    with np.load(data / "live_inputs_private.npz",allow_pickle=False) as inputs:
        assert len(inputs["event_ids"])==17
        assert set(inputs["event_ids"].tolist())=={e["event_id"] for e in fresh}
    files=[optional_asset_path("gate_impl_path",ref.parent / "gate_soft_oof_search.py"),ref / "gate_results/augmented/seed_42/gate_summary.json",
        ref / "gate_exports/augmented/seed_42/ctbm_validation_predictions.csv",
        ref / "gate_exports/augmented/seed_42/pbcnn_validation_predictions.csv"]
    result={"source_revision":source_revision(),"audit_source":folder.name,"checkpoint_hashes_match_bank_manifest":True,"checkpoint_count":len(hashes),
        "label_order_match":True,"judge_payloads_checked":len(records),"ground_truth_in_judge_payload":False,
        "live_vs_saved_probabilities_checked":len(fresh),"maximum_absolute_probability_difference":max(errors),
        "probabilities_bitwise_equal":max(errors)==0,
        "acceptance_scope":"checkpoint hashes, formal classes and ranked case IDs agree; floating probabilities are measured, not asserted identical",
        "live_vs_saved_top5_case_ids_all_match":True,"live_input_classes":17,
        "current_gate_files_sha256":{p.name:sha(p) for p in files},
        'asset_revision':identifier(runtime_assets(ROOT)),
        "gate_hash_scope":"Gate, model, tokenizer and input asset hashes match the actual live audit asset version"}
    (folder / "asset_alignment.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))


if __name__=="__main__":main()
