"""Validate recorded aggregate results against counts and confusion matrices."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "detection": "detection_17class.json",
    "retrieval": "retrieval_17class.json",
    "judge": "local_judge_17class.json",
    "framework": "framework_validation.json",
}


def read_results(root=ROOT):
    return {
        key: json.loads((root / "results" / name).read_text(encoding="utf-8"))
        for key, name in SOURCES.items()
    }


def validate_results(data):
    detection, retrieval, judge, framework = (data[key] for key in SOURCES)
    expected_labels = [row["label"] for row in detection["OOF Gate"]["per_class"]]
    if len(set(expected_labels)) != 17:
        raise ValueError("Expected 17 unique labels")

    def close(actual, expected):
        if not math.isclose(actual, expected, abs_tol=1e-10):
            raise ValueError("Aggregate metric does not match recorded counts")

    for model in ("CTBM", "PBCNN", "OOF Gate"):
        value = detection[model]
        matrix = value["confusion_matrix"]
        rows = value["per_class"]
        if len(matrix) != 17 or any(
            len(row) != 17 or any(type(n) is not int or n < 0 for n in row)
            for row in matrix
        ):
            raise ValueError("Invalid confusion matrix")
        total = sum(sum(row) for row in matrix)
        if value["n"] != total or [row["label"] for row in rows] != expected_labels:
            raise ValueError("Detection sample or label mismatch")
        close(value["accuracy"], sum(matrix[i][i] for i in range(17)) / total)
        scores = []
        for i, row in enumerate(rows):
            tp = matrix[i][i]
            support = sum(matrix[i])
            predicted = sum(matrix[j][i] for j in range(17))
            if row["support"] != support:
                raise ValueError("Class support mismatch")
            precision = tp / predicted if predicted else 0
            recall = tp / support if support else 0
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0
            )
            close(row["precision"], precision)
            close(row["recall"], recall)
            close(row["f1"], f1)
            scores.append(f1)
        close(value["macro_f1"], sum(scores) / 17)
    if (
        sum(retrieval["query_class_counts"].values()) != retrieval["queries"]
        or sum(retrieval["train_class_counts"].values()) != retrieval["bank_rows"]
    ):
        raise ValueError("Retrieval counts mismatch")
    if (
        retrieval["label_count"] != 17
        or retrieval["train_test_id_overlap"] != 0
        or not 0 <= retrieval["mrr5"] <= retrieval["top5"] <= 1
    ):
        raise ValueError("Invalid retrieval scope")
    if (
        judge["cases"] != retrieval["queries"]
        or sum(judge["assessment_counts"].values()) != judge["cases"]
    ):
        raise ValueError("Judge count mismatch")
    if (
        judge["intercepted_error_count"] + judge["false_support_count"]
        != judge["detector_error_count"]
        or judge["support_count"] != judge["assessment_counts"]["support"]
    ):
        raise ValueError("Judge error counts mismatch")
    close(
        judge["error_interception_rate"],
        judge["intercepted_error_count"] / judge["detector_error_count"],
    )
    close(
        judge["support_precision"],
        (judge["support_count"] - judge["false_support_count"])
        / judge["support_count"],
    )
    cases = framework["cases"]
    network_labels=['BENIGN','FTP-BruteForce','SSH-Bruteforce','DDoS-LOIC-HTTP','Web-XSS','Bot']
    if framework['network_validation_labels']!=network_labels or [row['validation_label'] for row in cases]!=network_labels:
        raise ValueError('Framework predetermined class coverage mismatch')
    if (
        len(cases) != framework["network_cases"]
        or framework["real_live_classes"] != 17
        or framework["real_local_llm_calls"] != 17
    ):
        raise ValueError("Framework count mismatch")
    if (
        sum(bool(row["rollback_integrity"]) for row in cases)
        != framework["rollback_passed_cases"]
        or sum(row["background_success_rate"] == 1 for row in cases)
        != framework["background_preserved_cases"]
    ):
        raise ValueError("Framework success counts mismatch")
    if (
        sum(row["rules_applied"] == 0 for row in cases)
        != framework["non_disruptive_network_cases"]
    ):
        raise ValueError("Framework deployment count mismatch")
    for row in cases:
        counts={'monitor':0,'capture_evidence':0,'auth_hardening':2,'rate_limit':2,
                'upstream_scrubbing':2,'waf_virtual_patch':1,'block_c2_destination':1}
        if row['action'] not in counts or type(row['rules_applied']) is not int or row['rules_applied']!=counts[row['action']]:
            raise ValueError('Framework policy rules missing')
        for key in ('baseline_success_rate','after_success_rate','background_success_rate','recovery_success_rate'):
            rate=row[key]
            if isinstance(rate,bool) or not isinstance(rate,(int,float)) or not math.isfinite(rate) or not 0<=rate<=1:
                raise ValueError('Invalid framework transaction rate')
            if key!='after_success_rate' and rate!=1:
                raise ValueError('Framework baseline, background or recovery failed')
        if row['rollback_integrity'] is not True:
            raise ValueError('Framework rollback failed')
        if row.get('cleanup_passed') is not True:
            raise ValueError('Framework cleanup failed')
        if row['rules_applied']:
            if row['assessment']!='support':raise ValueError('Framework intervention lacks support')
            # Derive the expected effect from actual predicted and measured service ports.
            ports={'Benign':8080,'BruteForce-FTP':21,'BruteForce-SSH':22,'Bot':4444}
            true_ports={'BENIGN':8080,'FTP-BruteForce':21,'SSH-Bruteforce':22,'Bot':4444}
            effect=row['action']=='rate_limit' or ports.get(row['reason_label'],80)==true_ports.get(row['validation_label'],80)
            if row['expected_policy_effect'] is not effect or (effect and row['after_success_rate']>=row['baseline_success_rate']):
                raise ValueError('Framework expected policy effect missing')
        elif row['after_success_rate']!=1 or row['ttl_rollback_elapsed_seconds'] is not None:
            raise ValueError('Framework non-disruptive scope mismatch')
        if (
            row["rules_applied"] > 0
            and not 30 <= row["ttl_rollback_elapsed_seconds"] < 35
        ):
            raise ValueError("Invalid expiry evidence")
    return data
