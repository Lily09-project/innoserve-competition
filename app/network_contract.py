"""Standard-library-only binding from model decision to isolated execution receipt.

Hashes detect accidental substitution; they are not signatures or attacker-proof storage.
Ground truth selects only the synthetic evaluation traffic, never the action.
"""

from __future__ import annotations

B_NAMES = {
    0: "Benign",
    1: "BruteForce-FTP",
    2: "BruteForce-SSH",
    3: "DoS-GoldenEye",
    4: "DoS-Hulk",
    7: "DDoS-LOIC-HTTP",
    9: "DDoS-HOIC",
    10: "WebAttack-BruteForce",
    11: "WebAttack-XSS",
    12: "WebAttack-SQLInjection",
    13: "Bot",
}


from integrity import digest, verify_ledger

# Compatibility aliases keep existing scripts and serialized contracts unchanged.
valid_ledger = verify_ledger


def build_network_scenario(event, ttl=30):
    result = event["result"]
    prediction = event["prediction"]
    if prediction not in B_NAMES or event["validation_label"] not in B_NAMES:
        raise ValueError("no_validated_synthetic_traffic_profile")
    if event.get("execution_mode") != "live_local_models" or not event.get("execution_id"):
        raise ValueError("fresh_model_execution_required")
    policy = result["policy"]
    scenario = {
        "event_id": event["event_id"],
        "execution_id": event["execution_id"],
        "true_label": B_NAMES[event["validation_label"]],
        "reason_label": B_NAMES[prediction],
        "assessment": result["judge"]["assessment"],
        "action": policy["action"] if policy["allowed"] else "capture_evidence",
        "ttl_seconds": ttl,
        "source_result": result,
        "source_result_sha256": digest(result),
        "traffic_scope": "ground truth selects synthetic evaluation traffic only; policy uses prediction and judge",
    }
    validate_network_scenario(scenario)
    return scenario


def validate_network_scenario(scenario):
    result = scenario["source_result"]
    ledger = result["ledger"]
    if (
        digest(result) != scenario["source_result_sha256"]
        or not valid_ledger(ledger)
        or len(ledger) != 4
    ):
        raise ValueError("network_source_integrity_mismatch")
    if [x["stage"] for x in ledger] != ["detection", "retrieval", "judge", "policy"]:
        raise ValueError("network_source_stages_mismatch")
    if (
        any(x["event_id"] != scenario["event_id"] for x in ledger)
        or result["event_id"] != scenario["event_id"]
    ):
        raise ValueError("network_event_binding_mismatch")
    if (
        not scenario.get("execution_id")
        or ledger[0].get("execution_id") != scenario["execution_id"]
    ):
        raise ValueError("network_execution_binding_mismatch")
    if (
        ledger[0]["mode"] != "live_checkpoint_inference"
        or ledger[2]["mode"] != "live_local_llm_inference"
    ):
        raise ValueError("network_requires_live_model_chain")
    prediction = result["prediction"]
    if ledger[0]["prediction"] != prediction or scenario["reason_label"] != B_NAMES.get(prediction):
        raise ValueError("network_prediction_binding_mismatch")
    for key in ("judge", "policy"):
        source = {
            k: v
            for k, v in ledger[2 if key == "judge" else 3].items()
            if k not in {"stage", "event_id", "sequence", "previous_sha256", "sha256"}
        }
        if source != result[key]:
            raise ValueError("network_decision_ledger_mismatch")
    policy = result["policy"]
    action = policy["action"] if policy["allowed"] else "capture_evidence"
    if scenario["action"] != action or scenario["assessment"] != result["judge"]["assessment"]:
        raise ValueError("network_action_binding_mismatch")
    if scenario["true_label"] not in B_NAMES.values():
        raise ValueError("unsupported_evaluation_profile")
    ttl = scenario["ttl_seconds"]
    if type(ttl) is not int or not 30 <= ttl <= 900:
        raise ValueError("invalid_ttl")
    # The live detector/Guard always compiles a 30-second demonstration policy.
    if ttl != 30:
        raise ValueError("live_policy_ttl_binding_mismatch")


def bind_network_receipt(scenario, measurement):
    validate_network_scenario(scenario)
    if any(
        measurement.get(k) != scenario[k]
        for k in ("event_id", "action", "assessment", "ttl_seconds")
    ):
        raise ValueError("network_receipt_decision_mismatch")
    result = dict(measurement)
    result.update(
        {
            "execution_id": scenario["execution_id"],
            "source_result_sha256": scenario["source_result_sha256"],
            "scenario_sha256": digest(scenario),
        }
    )
    ledger = list(scenario["source_result"]["ledger"])
    entry = {
        "event_id": scenario["event_id"],
        "sequence": len(ledger),
        "previous_sha256": ledger[-1]["sha256"],
        "stage": "isolated_execution",
        "measurement": dict(result),
    }
    entry["sha256"] = digest(entry)
    result["ledger"] = ledger + [entry]
    return result


def verify_network_receipt(scenario, receipt):
    try:
        value = {k: v for k, v in receipt.items() if k != "ledger"}
        return bind_network_receipt(scenario, value) == receipt and valid_ledger(receipt["ledger"])
    except (KeyError, TypeError, ValueError):
        return False
