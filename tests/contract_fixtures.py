"""Disposable synthetic contract fixtures; never performance or release evidence."""

import hashlib
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from pipeline import (
    LABELS,
    TrainOnlyBank,
    audit_payload,
    digest,
    judge_context_digest,
    run_event,
    task_vector,
)
from judge_response import JUDGE_PROMPT
from network_contract import (
    build_network_scenario,
    bind_network_receipt,
    RULE_COUNTS,
    NON_DISRUPTIVE,
    PROFILE_PORTS,
)
from asset_validation import INPUT_SHAPES


def judge_record(event, evidence, assessment="support"):
    payload = audit_payload(event, evidence)
    prompt = hashlib.sha256(JUDGE_PROMPT.encode()).hexdigest()
    return {
        "event_id": event["event_id"],
        "assessment": assessment,
        "model": "fixture",
        "model_revision": "fixture.v1",
        "prompt_sha256": prompt,
        "valid_json": True,
        "store": False,
        "classification_changed": False,
        "payload": payload,
        "execution_mode": "live_local_llm_inference",
        "binding_version": 2,
        "input_sha256": digest(
            {
                "event_id": event["event_id"],
                "prediction": event["prediction"],
                "evidence": evidence,
            }
        ),
        "context_sha256": judge_context_digest(
            event["event_id"], payload, prompt, "fixture.v1"
        ),
    }


def event_bundle():
    vectors = [
        task_vector(np.eye(512)[label], np.eye(17)[label])
        for label in range(17)
        for _ in range(5)
    ]
    bank = TrainOnlyBank(
        vectors,
        [f"train-{i:03}" for i in range(85)],
        [i // 5 for i in range(85)],
        ["train"] * 85,
        "fixture.v1",
        "a" * 64,
    )
    events = []
    records = []
    for label in range(17):
        event = {
            "event_id": f"query-{label}",
            "execution_id": f"run-{label}",
            "execution_mode": "live_local_models",
            "mode": "live_checkpoint_inference",
            "prediction": label,
            "validation_label": label,
            "pred_ctbm": label,
            "pred_pbcnn": label,
            "probabilities": np.eye(17)[label].tolist(),
            "embedding": np.eye(512)[label].tolist(),
            "representation_id": "fixture.v1",
            "model_sha256": "a" * 64,
            "asset_revision": "fixture-assets",
            "judge_model_revision": "fixture.v1",
            "confidence": 1.0,
            "source_split": "test",
            "policy_ttl_seconds": 30,
        }
        evidence = bank.retrieve(
            task_vector(event["embedding"], event["probabilities"]),
            event["event_id"],
            "fixture.v1",
            "a" * 64,
        )
        record = judge_record(event, evidence)
        event["result"] = run_event(event, bank, record)
        event["evidence"] = evidence
        events.append(event)
        records.append(record)
    return bank, events, records


def measurement(scenario):
    action = scenario["action"]
    active = action not in NON_DISRUPTIVE
    count = RULE_COUNTS.get(action, 0)
    port = PROFILE_PORTS.get(scenario["reason_label"], 80)
    prefix = f"-A ACTIVE_DEFENSE -s 10.10.1.10/32 -p tcp --dport {port} "
    rules = (
        [prefix + "-m limit --limit 1/sec -j RETURN", prefix + "-j DROP"]
        if count == 2
        else [prefix + "-j DROP"]
        if count
        else []
    )
    result = {
        key: scenario[key]
        for key in ("event_id", "action", "assessment", "ttl_seconds")
    }
    result.update(
        {
            key: {"success_rate": 0.0 if key == "subject_after" and active else 1.0}
            for key in (
                "baseline",
                "background_baseline",
                "subject_after",
                "background_after",
                "recovery",
                "background_recovery",
            )
        }
    )
    result.update(
        {
            "rules_applied": count,
            'cleanup':{'passed':True,'commands_drained':True,'policy_reset':True,'server_stopped':True,'network_stopped':True,'remaining_owned_links':[],'errors':[]},
            "network_test_executed": True,
            "network_action_executed": active,
            "commands_executed": count,
            "rule_readback": {"iptables": "\n".join(rules)},
            "ttl_rollback_elapsed_seconds": 30.01 if active else None,
            "expiry_mode": "actual_monotonic_ttl_scheduler"
            if active
            else "non_disruptive_no_rule",
            "rollback_integrity": True,
            "rollback_rule_readback": {"iptables": ""},
        }
    )
    return result


def audit_bundle():
    _, events, _ = event_bundle()
    receipts = []
    for label in (0, 1, 2, 7, 11, 13):
        scenario = build_network_scenario(events[label])
        receipts.append(bind_network_receipt(scenario, measurement(scenario)))
    summary = {
        "status": "passed",
        "source_revision": "current",
        "asset_revision": "fixture-assets",
        "real_live_classes": 17,
        "real_local_llm_calls": 17,
        "network_cases": 6,
        "network_validation_labels": [LABELS[i] for i in (0, 1, 2, 7, 11, 13)],
        "background_preserved_cases": 6,
        "rollback_passed_cases": 6,
        "non_disruptive_network_cases": 1,
    }
    return summary, events, receipts


def write_private_bundle(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    bank, events, records = event_bundle()
    path = folder / "train_bank.npz"
    np.savez_compressed(
        path,
        vectors=bank.vectors,
        ids=bank.ids,
        labels=bank.labels,
        splits=["train"] * len(bank.ids),
    )
    manifest = {
        "npz_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "label_order": LABELS,
        "representation_id": bank.representation_id,
        "model_sha256": bank.model_sha256,
    }
    (folder / "train_bank_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (folder / "events.json").write_text(json.dumps(events), encoding="utf-8")
    (folder / "judge_records_private.jsonl").write_text(
        "\n".join(json.dumps(row) for row in records), encoding="utf-8"
    )
    tensors = {
        key: np.zeros(
            shape, dtype=np.int64 if key in {"bytes", "directions"} else np.float32
        )
        for key, shape in INPUT_SHAPES.items()
    }
    np.savez_compressed(
        folder / "live_inputs_private.npz",
        event_ids=[e["event_id"] for e in events],
        **tensors,
    )
