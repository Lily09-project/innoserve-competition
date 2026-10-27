"""Binding tests use synthetic fixtures, never represent model performance."""
import copy
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from pipeline import TrainOnlyBank, task_vector, digest, run_event
from network_contract import build_network_scenario, bind_network_receipt, verify_network_receipt, validate_network_scenario


class NetworkContractTests(unittest.TestCase):
    def setUp(self):
        p = np.eye(17)[7]
        vector = task_vector(np.ones(512), p)
        bank = TrainOnlyBank(np.tile(vector, (5, 1)), list("abcde"), [7]*5, ["train"]*5, "fixture", "a"*64)
        self.event = {"event_id":"query", "execution_id":"run-1", "execution_mode":"live_local_models",
            "mode":"live_checkpoint_inference", "prediction":7, "validation_label":7,
            "embedding":np.ones(512).tolist(), "probabilities":p.tolist(), "representation_id":"fixture",
            "model_sha256":"a"*64, "policy_ttl_seconds":30}
        evidence = bank.retrieve(vector, "query", "fixture", "a"*64)
        record = {"input_sha256":digest({"event_id":"query", "prediction":7, "evidence":evidence}),
            "assessment":"support", "model":"fixture", "prompt_sha256":"b"*64,
            "store":False, "classification_changed":False, "execution_mode":"live_local_llm_inference"}
        self.event["result"] = run_event(self.event, bank, record)
        self.scenario = build_network_scenario(self.event)

    def test_live_chain_receipt(self):
        raw = {k:self.scenario[k] for k in ("event_id","action","assessment","ttl_seconds")}
        raw.update({"rollback_integrity":True, "rules_applied":2})
        receipt = bind_network_receipt(self.scenario, raw)
        self.assertTrue(verify_network_receipt(self.scenario, receipt))
        self.assertEqual(len(receipt["ledger"]), 5)
        self.assertEqual(receipt["ledger"][-1]["stage"], "isolated_execution")
        receipt["rules_applied"] = 0
        self.assertFalse(verify_network_receipt(self.scenario, receipt))

    def test_scenario_substitutions_rejected(self):
        for key,value in (("event_id","another"),("execution_id","old-run"),
            ("action","rate_limit"),("assessment","review"),("reason_label","Bot"),("ttl_seconds",60)):
            scenario = {**self.scenario, key:value}
            with self.subTest(key=key), self.assertRaises(ValueError):validate_network_scenario(scenario)

    def test_ground_truth_does_not_choose_action(self):
        # Deliberately misclassified query: evaluating it must not replace its decision with the answer.
        event = {**self.event, "validation_label":13}
        scenario = build_network_scenario(event)
        self.assertEqual(scenario["true_label"], "Bot")
        self.assertEqual(scenario["reason_label"], "DDoS-LOIC-HTTP")
        self.assertEqual(scenario["action"], self.scenario["action"])

    def test_replay_and_mutated_decision_rejected(self):
        with self.assertRaises(ValueError):build_network_scenario({**self.event, "execution_mode":"replay"})
        event = copy.deepcopy(self.event)
        event["result"]["judge"]["assessment"] = "review"
        with self.assertRaises(ValueError):build_network_scenario(event)


if __name__ == "__main__":unittest.main()
