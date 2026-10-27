"""17-class integration contract. No fabricated embeddings, retrieval or LLM output."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
import sys

import numpy as np
from network_contract import B_NAMES
# LABELS is the detector order; B_NAMES maps only validated profiles to upstream names.

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sources" / "paper_code" / "scripts"))
from run_active_defense_shadow_experiment import ActionIntent, compile_intent, validate_intent

LABELS = [
    "BENIGN",
    "FTP-BruteForce",
    "SSH-Bruteforce",
    "DoS-GoldenEye",
    "DoS-Hulk",
    "DoS-Slowloris",
    "DoS-SlowHTTPTest",
    "DDoS-LOIC-HTTP",
    "DDoS-LOIC-UDP",
    "DDOS-HOIC",
    "Web-BruteForce",
    "Web-XSS",
    "SQL-Injection",
    "Bot",
    "Infiltration",
    "PortScan",
    "Heartbleed",
]
ACTIONS = {
    1: "auth_hardening",
    2: "auth_hardening",
    3: "rate_limit",
    4: "rate_limit",
    7: "upstream_scrubbing",
    9: "upstream_scrubbing",
    10: "rate_limit",
    11: "waf_virtual_patch",
    12: "waf_virtual_patch",
    13: "block_c2_destination",
}
SCOPES = {
    "monitor": "event",
    "capture_evidence": "event",
    "auth_hardening": "target_service",
    "rate_limit": "suspected_source",
    "upstream_scrubbing": "upstream_edge",
    "waf_virtual_patch": "target_service",
    "block_c2_destination": "confirmed_c2",
}


from integrity import digest, verify_ledger as verify_ledger


def probabilities(values):
    a = np.asarray(values, dtype=float)
    if a.shape != (17,) or not np.isfinite(a).all() or (a < 0).any():
        raise ValueError("invalid_17_class_probabilities")
    if not np.isclose(a.sum(), 1.0, atol=1e-5):
        raise ValueError("probabilities_must_sum_to_one")
    return a


def task_vector(embedding, probs):
    e = np.asarray(embedding, dtype=float)
    if e.shape != (512,) or not np.isfinite(e).all() or np.linalg.norm(e) == 0:
        raise ValueError("invalid_512_dimension_embedding")
    p = probabilities(probs)
    v = np.concatenate((e, p))
    return v / np.linalg.norm(v)


class TrainOnlyBank:
    """NPZ rows and a matching provenance manifest are mandatory."""

    def __init__(self, vectors, ids, labels, splits, representation_id, model_sha256):
        self.vectors = np.asarray(vectors, dtype=float)
        self.ids = list(ids)
        self.labels = list(labels)
        if self.vectors.ndim != 2 or self.vectors.shape[1] != 529 or len(ids) != len(self.vectors):
            raise ValueError("invalid_bank_shape")
        if len(self.vectors) < 5 or len(labels) != len(ids) or len(splits) != len(ids):
            raise ValueError("incomplete_bank")
        if len(set(ids)) != len(ids) or set(splits) != {"train"}:
            raise ValueError("bank_must_be_unique_and_train_only")
        if any(type(x) is not int or not 0 <= x < 17 for x in self.labels):
            raise ValueError("invalid_bank_label_mapping")
        if not representation_id or not model_sha256 or len(model_sha256) != 64:
            raise ValueError("missing_representation_provenance")
        norms = np.linalg.norm(self.vectors, axis=1)
        if not np.isfinite(self.vectors).all() or (norms == 0).any():
            raise ValueError("invalid_bank_vector")
        self.vectors = self.vectors / norms[:, None]
        self.representation_id = representation_id
        self.model_sha256 = model_sha256

    @classmethod
    def load(cls, npz_path, manifest_path):
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if hashlib.sha256(Path(npz_path).read_bytes()).hexdigest() != manifest["npz_sha256"]:
            raise ValueError("bank_hash_mismatch")
        if manifest["label_order"] != LABELS:
            raise ValueError("bank_label_order_mismatch")
        with np.load(npz_path, allow_pickle=False) as bank:
            return cls(
                bank["vectors"],
                bank["ids"].tolist(),
                bank["labels"].tolist(),
                bank["splits"].tolist(),
                manifest["representation_id"],
                manifest["model_sha256"],
            )

    def retrieve(self, vector, query_id, representation_id, model_sha256):
        if query_id in self.ids:
            raise ValueError("query_bank_id_overlap")
        if representation_id != self.representation_id or model_sha256 != self.model_sha256:
            raise ValueError("query_bank_representation_mismatch")
        q = np.asarray(vector, dtype=float)
        if q.shape != (529,) or not np.isfinite(q).all() or np.linalg.norm(q) == 0:
            raise ValueError("invalid_query_vector")
        scores = self.vectors @ (q / np.linalg.norm(q))
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], self.ids[i]))[:5]
        return [
            {
                "rank": rank + 1,
                "case_id": self.ids[i],
                "label_id": self.labels[i],
                "label": LABELS[self.labels[i]],
                "similarity": float(scores[i]),
            }
            for rank, i in enumerate(order)
        ]


def check_judge(cached, event_id, prediction, evidence):
    if cached is None:
        return {
            "assessment": "review",
            "mode": "manual_review",
            "reason": "缺少同事件授權稽核回覆，保留人工複核。",
        }
    if not evidence or len(evidence) != 5:
        raise ValueError("judge_requires_five_retrieved_cases")
    expected = digest({"event_id": event_id, "prediction": prediction, "evidence": evidence})
    if cached.get("input_sha256") != expected:
        raise ValueError("judge_input_binding_mismatch")
    if cached.get("assessment") not in {"support", "review", "uncertain"}:
        raise ValueError("invalid_judge_assessment")
    if (
        not cached.get("model")
        or not cached.get("prompt_sha256")
        or cached.get("store") is not False
    ):
        raise ValueError("missing_judge_provenance")
    if cached.get("classification_changed") is not False:
        raise ValueError("judge_cannot_change_formal_classification")
    return {
        "assessment": cached["assessment"],
        "mode": cached.get("execution_mode", "authorized_cached_response"),
        "reason": str(cached.get("reason", "")),
        "input_sha256": expected,
        "model": cached["model"],
        "valid_json": cached.get("valid_json", True),
    }


def audit_payload(event, evidence):
    p = probabilities(event["probabilities"])
    return {
        "detector_class": LABELS[event["prediction"]],
        "confidence": round(float(p.max()), 6),
        "branch_predictions": [LABELS[event["pred_ctbm"]], LABELS[event["pred_pbcnn"]]],
        "train_only_neighbours": [
            {"rank": x["rank"], "class": x["label"], "similarity": round(x["similarity"], 6)}
            for x in evidence
        ],
    }


def guard(prediction, assessment, requested_action=None, ttl=300):
    if type(prediction) is not int or not 0 <= prediction < 17:
        raise ValueError("invalid_class_id")
    if assessment not in {"support", "review", "uncertain"}:
        raise ValueError("invalid_assessment")
    action = requested_action or (
        "monitor" if prediction == 0 else ACTIONS.get(prediction, "capture_evidence")
    )
    if assessment != "support" and action not in {"monitor", "capture_evidence"}:
        return {
            "allowed": False,
            "action": "capture_evidence",
            "reason": "複核或不確定事件保留蒐證，需人工核准處置。",
        }
    if prediction == 0 and action not in {"monitor", "capture_evidence"}:
        return {"allowed": False, "action": "monitor", "reason": "正常事件禁止破壞性處置。"}
    if action not in {"monitor", "capture_evidence", ACTIONS.get(prediction)}:
        return {"allowed": False, "action": "capture_evidence", "reason": "動作與類別策略不相容。"}
    if action not in {"monitor", "capture_evidence"} and (
        type(ttl) is not int or not 30 <= ttl <= 900
    ):
        return {
            "allowed": False,
            "action": "capture_evidence",
            "reason": "處置存活時間超出策略範圍。",
        }
    label = B_NAMES.get(prediction)
    if label is None:
        return {
            "allowed": True,
            "action": "capture_evidence",
            "execution_mode": "evidence_only",
            "reason": "此類事件採蒐證與人工處理策略。",
        }
    intent = ActionIntent(
        action,
        SCOPES[action],
        None if action in {"monitor", "capture_evidence"} else ttl,
        "17-class-adapter.v1",
        label,
        assessment,
    )
    errors = validate_intent(intent)
    return {
        "allowed": not errors,
        "action": action,
        "errors": errors,
        "command": compile_intent(intent) if not errors else None,
        "execution_mode": "compile_only",
        "reason": "白名單及範圍檢核後產生結構化動作，設備執行另經隔離驗證。",
    }


def run_event(event, bank=None, cached=None):
    p = probabilities(event["probabilities"])
    prediction = int(np.argmax(p))
    if prediction != event["prediction"]:
        raise ValueError("formal_prediction_does_not_match_probabilities")
    evidence = []
    started = time.perf_counter()
    if bank is not None:
        evidence = bank.retrieve(
            task_vector(event["embedding"], p),
            event["event_id"],
            event["representation_id"],
            event["model_sha256"],
        )
    retrieval_ms = (time.perf_counter() - started) * 1000 if bank is not None else None
    if (
        cached is not None
        and "payload" in cached
        and cached["payload"] != audit_payload(event, evidence)
    ):
        raise ValueError("judge_payload_binding_mismatch")
    judge = check_judge(cached, event["event_id"], prediction, evidence)
    policy = guard(prediction, judge["assessment"], ttl=event.get("policy_ttl_seconds", 300))
    if judge["assessment"] == "support" and (
        float(p.max()) < 0.8 or sum(x["label_id"] == prediction for x in evidence) < 4
    ):
        policy = {
            "allowed": False,
            "action": "capture_evidence",
            "execution_mode": "manual_review",
            "reason": "模型信心或證據支持未達策略門檻，保留人工複核。",
        }
    stages = [
        {
            "stage": "detection",
            "mode": event.get("mode", "frozen_prediction_replay"),
            "prediction": prediction,
            "execution_id": event.get("execution_id"),
        },
        {
            "stage": "retrieval",
            "mode": "live_vector_retrieval" if bank else "asset_not_loaded",
            "count": len(evidence),
        },
        {"stage": "judge", **judge},
        {"stage": "policy", **policy},
    ]
    previous = "0" * 64
    ledger = []
    for index, stage in enumerate(stages):
        entry = {
            "event_id": event["event_id"],
            "sequence": index,
            "previous_sha256": previous,
            **stage,
        }
        entry["sha256"] = digest(entry)
        previous = entry["sha256"]
        ledger.append(entry)
    return {
        "event_id": event["event_id"],
        "prediction": prediction,
        "evidence": evidence,
        "judge": judge,
        "policy": policy,
        "retrieval_ms": retrieval_ms,
        "ledger": ledger,
        "network_action_executed": False,
    }
