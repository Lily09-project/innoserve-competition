"""Standard-library-only binding from model decision to isolated execution receipt.

Hashes detect accidental substitution; they are not signatures or attacker-proof storage.
Ground truth selects only the synthetic evaluation traffic, never the action.
"""
from __future__ import annotations
import hashlib
import json
import math

NON_DISRUPTIVE = {'monitor','capture_evidence'}
RULE_COUNTS = {'auth_hardening':2,'rate_limit':2,'upstream_scrubbing':2,
               'waf_virtual_patch':1,'block_c2_destination':1}
PROFILE_PORTS = {'Benign':8080,'BruteForce-FTP':21,'BruteForce-SSH':22,'Bot':4444}


def expected_effect(scenario):
    if scenario['action'] in NON_DISRUPTIVE:
        return False
    return scenario['action'] == 'rate_limit' or PROFILE_PORTS.get(scenario['true_label'],80) == PROFILE_PORTS.get(scenario['reason_label'],80)


def validate_measurement(scenario, receipt):
    """Verify isolation actions actually occurred; hashes alone do not prove success."""
    for key in ('baseline','background_baseline','subject_after','background_after','recovery','background_recovery'):
        rate = receipt[key]['success_rate']
        if isinstance(rate,bool) or not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 0 <= rate <= 1:
            raise ValueError('invalid_transaction_measurement')
        if key != 'subject_after' and rate != 1:
            raise ValueError('baseline_background_or_recovery_failed')
    disruptive = scenario['action'] not in NON_DISRUPTIVE
    count = RULE_COUNTS.get(scenario['action'],0)
    if type(receipt['rules_applied']) is not int or receipt['rules_applied'] != count:
        raise ValueError('expected_policy_rules_missing')
    if receipt.get('network_test_executed') is not True or receipt.get('network_action_executed') is not disruptive:
        raise ValueError('policy_execution_flag_mismatch')
    rules = [line for line in receipt['rule_readback']['iptables'].splitlines() if line.startswith('-A ')]
    if len(rules) != count:
        raise ValueError('policy_readback_count_mismatch')
    if disruptive:
        port = PROFILE_PORTS.get(scenario['reason_label'],80)
        if any('-s 10.10.1.10' not in line or '-p tcp' not in line for line in rules):
            raise ValueError('policy_readback_scope_mismatch')
        if scenario['action'] != 'rate_limit' and any('--dport '+str(port)+' ' not in line+' ' for line in rules):
            raise ValueError('policy_readback_port_mismatch')
        if not any('-j DROP' in line for line in rules):
            raise ValueError('policy_readback_has_no_drop')
        if receipt.get('commands_executed',0) <= 0:
            raise ValueError('policy_commands_missing')
        elapsed = receipt.get('ttl_rollback_elapsed_seconds')
        if isinstance(elapsed,bool) or not isinstance(elapsed,(int,float)) or not math.isfinite(elapsed) or not scenario['ttl_seconds'] <= elapsed < scenario['ttl_seconds']+5:
            raise ValueError('policy_expiry_not_verified')
        if receipt.get('expiry_mode') != 'actual_monotonic_ttl_scheduler':
            raise ValueError('policy_expiry_mode_mismatch')
        if expected_effect(scenario) and receipt['subject_after']['success_rate'] >= receipt['baseline']['success_rate']:
            raise ValueError('expected_policy_effect_missing')
    elif receipt['subject_after']['success_rate'] != 1 or receipt.get('commands_executed') != 0:
        raise ValueError('non_disruptive_policy_altered_traffic')
    if receipt.get('rollback_integrity') is not True or receipt['rollback_rule_readback']['iptables'].strip():
        raise ValueError('rollback_not_verified')
    return True

B_NAMES = {0: "Benign", 1: "BruteForce-FTP", 2: "BruteForce-SSH", 3: "DoS-GoldenEye",
           4: "DoS-Hulk", 7: "DDoS-LOIC-HTTP", 9: "DDoS-HOIC", 10: "WebAttack-BruteForce",
           11: "WebAttack-XSS", 12: "WebAttack-SQLInjection", 13: "Bot"}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def valid_ledger(ledger):
    previous = "0" * 64
    for index, entry in enumerate(ledger):
        value = {k: v for k, v in entry.items() if k != "sha256"}
        if value.get("sequence") != index or value.get("previous_sha256") != previous or digest(value) != entry.get("sha256"):
            return False
        previous = entry["sha256"]
    return bool(ledger)


def build_network_scenario(event, ttl=30):
    result = event["result"]
    prediction = event["prediction"]
    if prediction not in B_NAMES or event["validation_label"] not in B_NAMES:
        raise ValueError("no_validated_synthetic_traffic_profile")
    if event.get("execution_mode") != "live_local_models" or not event.get("execution_id"):
        raise ValueError("fresh_model_execution_required")
    policy = result["policy"]
    scenario = {"event_id": event["event_id"], "execution_id": event["execution_id"],
        "true_label": B_NAMES[event["validation_label"]], "reason_label": B_NAMES[prediction],
        "assessment": result["judge"]["assessment"],
        "action": policy["action"] if policy["allowed"] else "capture_evidence", "ttl_seconds": ttl,
        "source_result": result, "source_result_sha256": digest(result),
        "traffic_scope": "ground truth selects synthetic evaluation traffic only; policy uses prediction and judge"}
    validate_network_scenario(scenario)
    return scenario


def validate_network_scenario(scenario):
    result = scenario["source_result"]
    ledger = result["ledger"]
    if digest(result) != scenario["source_result_sha256"] or not valid_ledger(ledger) or len(ledger) != 4:
        raise ValueError("network_source_integrity_mismatch")
    if [x["stage"] for x in ledger] != ["detection", "retrieval", "judge", "policy"]:
        raise ValueError("network_source_stages_mismatch")
    if any(x["event_id"] != scenario["event_id"] for x in ledger) or result["event_id"] != scenario["event_id"]:
        raise ValueError("network_event_binding_mismatch")
    if not scenario.get("execution_id") or ledger[0].get("execution_id") != scenario["execution_id"]:
        raise ValueError("network_execution_binding_mismatch")
    if ledger[0]["mode"] != "live_checkpoint_inference" or ledger[2]["mode"] != "live_local_llm_inference":
        raise ValueError("network_requires_live_model_chain")
    prediction = result["prediction"]
    if ledger[0]["prediction"] != prediction or scenario["reason_label"] != B_NAMES.get(prediction):
        raise ValueError("network_prediction_binding_mismatch")
    for key in ("judge", "policy"):
        source = {k: v for k, v in ledger[2 if key == "judge" else 3].items()
                  if k not in {"stage", "event_id", "sequence", "previous_sha256", "sha256"}}
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
    if any(measurement.get(k) != scenario[k] for k in ("event_id", "action", "assessment", "ttl_seconds")):
        raise ValueError("network_receipt_decision_mismatch")
    result = dict(measurement)
    result.update({"execution_id": scenario["execution_id"],
        "source_result_sha256": scenario["source_result_sha256"], "scenario_sha256": digest(scenario)})
    ledger = list(scenario["source_result"]["ledger"])
    entry = {"event_id": scenario["event_id"], "sequence": len(ledger), "previous_sha256": ledger[-1]["sha256"],
             "stage": "isolated_execution", "measurement": dict(result)}
    entry["sha256"] = digest(entry)
    result["ledger"] = ledger + [entry]
    return result


def verify_network_receipt(scenario, receipt):
    try:
        value = {k: v for k, v in receipt.items() if k != "ledger"}
        return bind_network_receipt(scenario, value) == receipt and valid_ledger(receipt["ledger"])
    except (KeyError, TypeError, ValueError):
        return False
