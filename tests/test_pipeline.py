"""Synthetic fixtures test code contracts only, not IDS or LLM performance."""

import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from pipeline import (
    TrainOnlyBank,
    audit_payload,
    check_judge,
    digest,
    guard,
    run_event,
    task_vector,
    verify_ledger,
)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.p = np.eye(17)[7]
        self.e = np.ones(512)
        self.v = task_vector(self.e, self.p)
        self.bank = TrainOnlyBank(
            np.tile(self.v, (6, 1)),
            [f"train-{i}" for i in range(6)],
            [7] * 6,
            ["train"] * 6,
            "fixture.v1",
            "a" * 64,
        )
        self.event = {
            "event_id": "query-1",
            "prediction": 7,
            "probabilities": self.p.tolist(),
            "embedding": self.e.tolist(),
            "representation_id": "fixture.v1",
            "model_sha256": "a" * 64,
            "mode": "synthetic_test_fixture",
        }

    def test_vector_dimensions_normalization(self):
        self.assertEqual(self.v.shape, (529,))
        self.assertAlmostEqual(np.linalg.norm(self.v), 1)

    def test_bad_vectors_fail(self):
        for p in [np.ones(17), [float("nan")] * 17, np.ones(16), [-1] * 17]:
            with self.assertRaises(ValueError):
                task_vector(self.e, p)
        with self.assertRaises(ValueError):
            task_vector(np.zeros(512), self.p)

    def test_no_test_bank(self):
        with self.assertRaises(ValueError):
            TrainOnlyBank(
                np.tile(self.v, (5, 1)),
                list("abcde"),
                [7] * 5,
                ["test"] * 5,
                "fixture.v1",
                "a" * 64,
            )

    def test_overlap_and_representation_rejected(self):
        for query, version in [("train-0", "fixture.v1"), ("query", "other")]:
            with self.assertRaises(ValueError):
                self.bank.retrieve(self.v, query, version, "a" * 64)

    def test_top5_ties_deterministic(self):
        result = self.bank.retrieve(self.v, "query", "fixture.v1", "a" * 64)
        self.assertEqual([x["case_id"] for x in result], [f"train-{i}" for i in range(5)])
        self.assertTrue(all(abs(x["similarity"] - 1) < 1e-8 for x in result))

    def test_missing_assets_route_review(self):
        result = run_event(self.event)
        self.assertEqual(result["judge"]["assessment"], "review")
        self.assertFalse(result["policy"]["allowed"])
        self.assertFalse(result["network_action_executed"])
        self.assertEqual(result["evidence"], [])

    def test_cached_judge_bound_to_same_input(self):
        evidence = self.bank.retrieve(self.v, "query-1", "fixture.v1", "a" * 64)
        cached = {
            "input_sha256": digest({"event_id": "query-1", "prediction": 7, "evidence": evidence}),
            "assessment": "support",
            "model": "fixture",
            "prompt_sha256": "b" * 64,
            "store": False,
            "classification_changed": False,
        }
        result = run_event(self.event, self.bank, cached)
        self.assertEqual(result["judge"]["assessment"], "support")
        self.assertTrue(result["policy"]["allowed"])
        with self.assertRaises(ValueError):
            check_judge(cached, "other", 7, evidence)

    def test_guard_all17_have_explicit_route(self):
        for cls in range(17):
            for assessment in ["support", "review", "uncertain"]:
                result = guard(cls, assessment)
                self.assertIn("allowed", result)
                if assessment != "support" and result["allowed"]:
                    self.assertIn(result["action"], {"monitor", "capture_evidence"})

    def test_guard_rejects_mismatch_ttl_benign(self):
        self.assertFalse(guard(0, "support", "block_source")["allowed"])
        self.assertFalse(guard(7, "support", ttl=99999)["allowed"])
        self.assertFalse(guard(7, "support", "run_shell")["allowed"])
        self.assertFalse(guard(7, "support", "rate_limit")["allowed"])

    def test_low_confidence_support_cannot_auto_act(self):
        event = {
            **self.event,
            "pred_ctbm": 7,
            "pred_pbcnn": 7,
            "probabilities": ([0.4] + [0.0] * 6 + [0.6] + [0.0] * 9),
        }
        evidence = self.bank.retrieve(
            task_vector(self.e, event["probabilities"]), "query-1", "fixture.v1", "a" * 64
        )
        cached = {
            "input_sha256": digest({"event_id": "query-1", "prediction": 7, "evidence": evidence}),
            "assessment": "support",
            "model": "fixture",
            "prompt_sha256": "b" * 64,
            "store": False,
            "classification_changed": False,
            "payload": audit_payload(event, evidence),
        }
        self.assertFalse(run_event(event, self.bank, cached)["policy"]["allowed"])
        cached["payload"]["confidence"] = 0.99
        with self.assertRaises(ValueError):
            run_event(event, self.bank, cached)

    def test_ledger_tamper_detected(self):
        result = run_event(self.event)
        self.assertTrue(verify_ledger(result["ledger"]))
        result["ledger"][0]["prediction"] = 0
        self.assertFalse(verify_ledger(result["ledger"]))


if __name__ == "__main__":
    unittest.main()
