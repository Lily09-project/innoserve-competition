"""Adversarial regressions for review findings, using disposable synthetic data."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from contract_fixtures import event_bundle, measurement, write_private_bundle
from pipeline import run_event
from network_contract import build_network_scenario, validate_measurement
from asset_validation import validate_bundle
from provenance import (
    SOURCE_FILES,
    code_revision,
    runtime_assets,
    identifier,
    file_hash,
)


class JudgeBindingRegressions(unittest.TestCase):
    def setUp(self):
        self.bank, self.events, self.records = event_bundle()

    def test_invalid_or_unbound_judge_cannot_authorize(self):
        changes = [
            {"valid_json": False},
            {"payload": None},
            {"prompt_sha256": "b" * 64},
            {"model_revision": "changed"},
            {"context_sha256": "0" * 64},
            {"valid_json": None},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_event(self.events[7], self.bank, {**self.records[7], **change})

    def test_invalid_json_uncertain_remains_non_disruptive(self):
        record = {**self.records[7], "valid_json": False, "assessment": "uncertain"}
        result = run_event(self.events[7], self.bank, record)
        self.assertFalse(result["policy"]["allowed"])
        self.assertEqual(result["policy"]["action"], "capture_evidence")

    def test_legacy_record_requires_complete_valid_context(self):
        record = {
            k: v
            for k, v in self.records[7].items()
            if k not in {"binding_version", "context_sha256"}
        }
        self.assertTrue(
            run_event(self.events[7], self.bank, record)["policy"]["allowed"]
        )
        del record["payload"]
        with self.assertRaises(ValueError):
            run_event(self.events[7], self.bank, record)


class NetworkEffectRegressions(unittest.TestCase):
    def setUp(self):
        _, events, _ = event_bundle()
        self.events = events
        self.scenario = build_network_scenario(events[7])
        self.receipt = measurement(self.scenario)

    def test_actual_rules_effect_and_expiry_are_required(self):
        self.assertTrue(validate_measurement(self.scenario, self.receipt))
        changes = [
            {"rules_applied": 0},
            {"rule_readback": {"iptables": ""}},
            {"subject_after": {"success_rate": 1.0}},
            {"expiry_mode": "accelerated"},
            {"ttl_rollback_elapsed_seconds": 29.9},
            {"rollback_integrity": False},
            {"background_after": {"success_rate": 0.9}},
            {
                "rule_readback": {
                    "iptables": self.receipt["rule_readback"]["iptables"].replace(
                        "--dport 80", "--dport 22"
                    )
                }
            },
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_measurement(self.scenario, {**self.receipt, **change})

    def test_monitor_has_no_rule_and_preserves_traffic(self):
        scenario = build_network_scenario(self.events[0])
        receipt = measurement(scenario)
        self.assertTrue(validate_measurement(scenario, receipt))
        receipt["subject_after"]["success_rate"] = 0
        with self.assertRaises(ValueError):
            validate_measurement(scenario, receipt)

    def test_different_predicted_service_does_not_claim_effect(self):
        scenario = {**self.scenario, "true_label": "BruteForce-SSH"}
        receipt = copy.deepcopy(self.receipt)
        receipt["subject_after"]["success_rate"] = 1
        self.assertTrue(validate_measurement(scenario, receipt))


class ProvenanceRegressions(unittest.TestCase):
    def test_every_execution_source_affects_revision(self):
        with tempfile.TemporaryDirectory(prefix="lineage-contract-") as folder:
            root = Path(folder)
            for name in SOURCE_FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"baseline\n")
            baseline = code_revision(root)
            for name in SOURCE_FILES:
                path = root / name
                path.write_bytes(b"changed\n")
                self.assertNotEqual(code_revision(root), baseline, name)
                path.write_bytes(b"baseline\r\n")
                self.assertEqual(code_revision(root), baseline)

    def test_gate_weights_tokenizer_and_inputs_affect_assets(self):
        import settings

        with tempfile.TemporaryDirectory(prefix="asset-lineage-contract-") as folder:
            root = Path(folder)
            ref = root / "ref"
            model = root / "llm"
            model.mkdir()
            gate = root / "gate.py"
            paths = [
                gate,
                ref / "gate_results/augmented/seed_42/gate_summary.json",
                ref / "gate_exports/augmented/seed_42/ctbm_validation_predictions.csv",
                ref / "gate_exports/augmented/seed_42/pbcnn_validation_predictions.csv",
                ref / "runtime_sources/ctbm_full_none_real_only_seed_42.py",
                ref / "runtime_sources/SMOTE_校準式類別感知Gate動態融合訓練_nofilm.py",
            ]
            paths += [
                ref / "models/augmented/seed_42" / name / "best_model.pt"
                for name in ("CTBM_Full", "PBCNN_M1", "PBCNN_M2")
            ]
            paths += [
                root / "evidence/fresh17" / name
                for name in (
                    "train_bank.npz",
                    "train_bank_manifest.json",
                    "events.json",
                    "live_inputs_private.npz",
                )
            ]
            paths += [
                model / name
                for name in (
                    "part.safetensors",
                    "config.json",
                    "tokenizer.json",
                    "tokenizer_config.json",
                )
            ]
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"baseline")
            with (
                patch.object(
                    settings,
                    "asset_path",
                    side_effect=lambda name: ref
                    if name == "ids_reference_root"
                    else model,
                ),
                patch.object(settings, "optional_asset_path", return_value=gate),
                patch.object(
                    settings, "execution_settings", return_value={"fixture": 1}
                ),
            ):
                baseline = identifier(runtime_assets(root))
                for path in paths:
                    path.write_bytes(b"changed")
                    self.assertNotEqual(
                        identifier(runtime_assets(root)), baseline, path.name
                    )
                    path.write_bytes(b"baseline")
                self.assertNotIn(str(root), json.dumps(runtime_assets(root)))


class ImportSemanticRegressions(unittest.TestCase):
    def test_hash_missing_tensor_and_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="bundle-contract-") as folder:
            root = Path(folder)
            write_private_bundle(root)
            self.assertEqual(validate_bundle(root)["live_classes"], 17)
            path = root / "events.json"
            original = path.read_text()
            events = json.loads(original)
            events[-1] = events[0]
            path.write_text(json.dumps(events))
            with self.assertRaises(ValueError):
                validate_bundle(root)
            path.write_text(original)
            bank = root / "train_bank.npz"
            bank.write_bytes(b"bad bank")
            with self.assertRaisesRegex(ValueError, "bank_hash"):
                validate_bundle(root)
            write_private_bundle(root)
            with np.load(root / "live_inputs_private.npz") as inputs:
                tensors = {
                    key: inputs[key] for key in inputs.files if key != "temporal"
                }
            np.savez_compressed(root / "live_inputs_private.npz", **tensors)
            with self.assertRaises(KeyError):
                validate_bundle(root)
