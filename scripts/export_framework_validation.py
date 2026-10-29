"""Export aggregate validation only; exclude event IDs, paths and raw responses."""
import json
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from server import source_revision
from audit_selection import select_audit
from provenance import runtime_assets, identifier
from pipeline import LABELS
from network_contract import build_network_scenario, expected_effect


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-dir',type=Path)
    args=parser.parse_args()
    folder=select_audit(ROOT/'validation',source_revision(),args.audit_dir,identifier(runtime_assets(ROOT)))
    read=lambda name:json.loads((folder / name).read_text(encoding="utf-8"))
    summary=read("summary.json")
    assert summary["status"]=="passed"
    live=read("live_events_private.json")
    rows=read("network_receipts_private.json")
    result={k:summary[k] for k in ("started_utc","api_version","source_revision","asset_revision","real_live_classes","real_local_llm_calls",
        "network_cases","network_validation_labels","network_receipts_bound_to_same_execution",
        "stale_execution_rejected","background_preserved_cases","rollback_passed_cases","non_disruptive_network_cases","scope")}
    result["frozen_prediction_agreement_cases"]=len(live)
    result["cases"]=[]
    events={e['event_id']:e for e in live}
    rows=sorted(rows,key=lambda row:events[row['event_id']]['validation_label'])
    for row in rows:
        event=events[row['event_id']]
        label=LABELS[event['validation_label']]
        scenario=build_network_scenario(event)
        result["cases"].append({"validation_label":label,"action":row["action"],"assessment":row["assessment"],
            'reason_label':scenario['reason_label'],'expected_policy_effect':expected_effect(scenario),
            "rules_applied":row["rules_applied"],"baseline_success_rate":row["baseline"]["success_rate"],
            "after_success_rate":row["subject_after"]["success_rate"],"background_success_rate":row["background_after"]["success_rate"],
            "recovery_success_rate":row["recovery"]["success_rate"],"rollback_integrity":row["rollback_integrity"],
            "cleanup_passed":row['cleanup']['passed'],
            "ttl_rollback_elapsed_seconds":row["ttl_rollback_elapsed_seconds"]})
    (ROOT / "results/framework_validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Exported aggregate framework validation:",len(live),"live inputs,",len(rows),"network cases.")


if __name__=="__main__":main()
