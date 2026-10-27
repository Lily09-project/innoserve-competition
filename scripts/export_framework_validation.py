"""Export aggregate validation only; exclude event IDs, paths and raw responses."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = sorted((ROOT / "validation").glob("framework_audit_*"))[-1]

    def read(name):
        return json.loads((folder / name).read_text(encoding="utf-8"))

    summary = read("summary.json")
    assert summary["status"] == "passed"
    live = read("live_events_private.json")
    rows = read("network_receipts_private.json")
    result = {
        k: summary[k]
        for k in (
            "started_utc",
            "api_version",
            "real_live_classes",
            "real_local_llm_calls",
            "network_cases",
            "network_validation_labels",
            "network_receipts_bound_to_same_execution",
            "stale_execution_rejected",
            "background_preserved_cases",
            "rollback_passed_cases",
            "non_disruptive_network_cases",
            "scope",
        )
    }
    result["frozen_prediction_agreement_cases"] = len(live)
    result["cases"] = []
    for label, row in zip(summary["network_validation_labels"], rows):
        result["cases"].append(
            {
                "validation_label": label,
                "action": row["action"],
                "assessment": row["assessment"],
                "rules_applied": row["rules_applied"],
                "baseline_success_rate": row["baseline"]["success_rate"],
                "after_success_rate": row["subject_after"]["success_rate"],
                "background_success_rate": row["background_after"]["success_rate"],
                "recovery_success_rate": row["recovery"]["success_rate"],
                "rollback_integrity": row["rollback_integrity"],
                "ttl_rollback_elapsed_seconds": row["ttl_rollback_elapsed_seconds"],
            }
        )
    (ROOT / "results/framework_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        "Exported aggregate framework validation:",
        len(live),
        "live inputs,",
        len(rows),
        "network cases.",
    )


if __name__ == "__main__":
    main()
