from __future__ import annotations
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "app"))
from pipeline import TrainOnlyBank, run_event, verify_ledger, digest


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    out=ROOT / "evidence/fresh17"
    bank=TrainOnlyBank.load(out / "train_bank.npz",out / "train_bank_manifest.json")
    events=json.loads((out / "events.json").read_text(encoding="utf-8"))
    cached={v["event_id"]:v for v in map(json.loads,(out / "judge_records_private.jsonl").read_text(encoding="utf-8").splitlines())}
    results=[]
    for event in events:
        result=run_event(event,bank,cached[event["event_id"]])
        assert verify_ledger(result["ledger"])
        assert result["prediction"]==event["prediction"]
        assert len(result["evidence"])==5
        assert result["evidence"]==event["evidence"]
        results.append(result)
    repeated=0; timings=[]
    selected=events[::max(1,len(events)//17)][:17]
    for _ in range(10):
        for e in selected:
            started=time.perf_counter(); result=run_event(e,bank,cached[e["event_id"]]);timings.append((time.perf_counter()-started)*1000)
            assert result["evidence"]==e["evidence"] and verify_ledger(result["ledger"])
            repeated+=1
    summary={"events":len(events),"five_evidence_records_per_event":True,"bound_llm_response_per_event":True,
        "valid_ledgers":len(events),"classification_changed_count":0,"deterministic_replays":repeated,
        "replay_median_ms":statistics.median(timings),"replay_min_ms":min(timings),"replay_max_ms":max(timings),
        "timing_scope":"retrieval + bound LLM response validation + Guard + ledger; excludes packet inference and fresh LLM generation",
        "policy_allowed_count":sum(r["policy"]["allowed"] for r in results),
        "wrong_prediction_with_allowed_policy":sum(e["prediction"]!=e["validation_label"] and r["policy"]["allowed"] for e,r in zip(events,results)),
        "wrong_prediction_with_disruptive_allowed_policy":sum(e["prediction"]!=e["validation_label"] and r["policy"]["allowed"] and r["policy"]["action"] not in {"monitor","capture_evidence"} for e,r in zip(events,results))}
    dump(ROOT / "validation/integration.json",summary)
    logs=[]
    for cwd,args,label in [(ROOT,["-m","unittest","discover","-s",str(ROOT / "tests"),"-v"],"integration_contracts"),
                          (ROOT / "sources/paper_code",["-m","unittest","discover","-s","tests","-p","test_active_defense_*.py","-v"],"original_B_tests")]:
        result=subprocess.run([sys.executable,"-X","utf8",*args],cwd=cwd,capture_output=True,text=True,encoding="utf-8")
        (ROOT / "validation" / (label+".log")).write_text(result.stdout+result.stderr,encoding="utf-8")
        logs.append({"suite":label,"returncode":result.returncode})
    dump(ROOT / "validation/unit_tests.json",logs)
    assert all(x["returncode"]==0 for x in logs)
    p=ROOT / "evidence/network/closed_loop_replays.jsonl"
    if p.exists():
        rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        attacks=[x for x in rows if x["true_label"]!="Benign"]
        benign=[x for x in rows if x["true_label"]=="Benign"]
        interventions=[x for x in attacks if x["disruptive_action"]]
        network={"scenario_count":len({x["scenario_id"] for x in rows}),"replays":len(rows),
            "attack_replays":len(attacks),"normal_replays":len(benign),
            "attack_suppression_all_attack_cases":float(np.mean([1-x["subject_after_policy"]["success_rate"] for x in attacks])),
            "attack_suppression_intervened_only":float(np.mean([1-x["subject_after_policy"]["success_rate"] for x in interventions])) if interventions else None,
            "normal_service":float(np.mean([x["subject_after_policy"]["success_rate"] for x in benign])) if benign else None,
            "background_service":float(np.mean([x["background_after_policy"]["success_rate"] for x in rows])),
            "rollback":float(np.mean([x["rollback_integrity"] for x in rows])),
            "selection":"first event per predicted label with a supported traffic profile; no correctness filtering",
            "llm_mode":"same-event local model responses reused, input hash bound",
            "inference_mode":"saved fresh detector predictions; retrieval recomputed",
            "scope":"virtual TCP transaction controller verification, not native attack replay",
            "ttl":"explicit test rollback; not automatic expiry measurement"}
        dump(ROOT / "evidence/network/closed_loop_summary.json",network)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":main()
