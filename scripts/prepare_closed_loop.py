"""Bind actual 17-class events to retrieved evidence, same-event local LLM and Guard.
Select first event/predicted class without selecting for correctness. Six labels
without a validated B traffic/action profile remain evidence-only.
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from pipeline import B_NAMES, TrainOnlyBank, run_event, verify_ledger


def main():
    data = ROOT / "evidence/fresh17"
    events = json.loads((data / "events.json").read_text(encoding="utf-8"))
    records = {v["event_id"]:v for v in map(json.loads,(data / "judge_records_private.jsonl").read_text(encoding="utf-8").splitlines())}
    bank = TrainOnlyBank.load(data / "train_bank.npz", data / "train_bank_manifest.json")
    selected = set()
    scenarios = []
    updated = []
    for e in events:
        record={**records[e["event_id"]],"execution_mode":"fresh_local_llm_saved_replay"}
        result = run_event(e, bank, record)
        assert verify_ledger(result["ledger"])
        e["result"] = result
        updated.append(e)
        p = e["prediction"]
        if p in selected or p not in B_NAMES or e["validation_label"] not in B_NAMES: continue
        selected.add(p)
        policy = result["policy"]
        scenarios.append({"scenario_id":f"bound-event-{p}", "condition":"fresh17_retrieval_cached_local_llm_guard",
            "true_label":B_NAMES[e["validation_label"]], "reason_label":B_NAMES[p],
            "action":policy["action"] if policy["allowed"] else "capture_evidence",
            "assessment":result["judge"]["assessment"], "case_count":1,
            "event_trace":{"event_id":e["event_id"], "ledger_sha256":result["ledger"][-1]["sha256"],
                           "judge_input_sha256":records[e["event_id"]]["input_sha256"],
                           "mode":"saved_fresh_detection_live_retrieval_bound_local_llm_cache",
                           "ttl_seconds":300, "rollback_mode":"explicit_test_rollback_not_ttl_expiry_measurement"}})
    (data / "events.json").write_text(json.dumps(updated,ensure_ascii=False,indent=2),encoding="utf-8")
    payload={"scenarios":scenarios,"scope":"17-class pipeline, 11 shared traffic-profile classes, first per predicted class, no correctness-based selection; same-event local LLM responses reused"}
    network=ROOT / "evidence/network"
    network.mkdir(parents=True,exist_ok=True)
    (network / "closed_loop_scenarios.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"events_checked":len(events),"selected_scenarios":len(scenarios),
                      "actions":[[x["reason_label"],x["assessment"],x["action"]] for x in scenarios]},ensure_ascii=False))


if __name__ == "__main__": main()
