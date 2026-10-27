"""Recorded public metrics must match counts; never substitute demonstration fixtures."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_public_site import read_results, validate_results, build_public_site


class PublicResultsTests(unittest.TestCase):
    def test_all_recorded_aggregates_match(self):
        data = validate_results(read_results())
        self.assertEqual(data["retrieval"]["queries"], 463)
        self.assertEqual(data["framework"]["network_cases"], 6)

    def test_tampered_metrics_rejected(self):
        for path, value in (
            (("detection", "OOF Gate", "accuracy"), 0.9999),
            (("judge", "intercepted_error_count"), 30),
            (("retrieval", "bank_rows"), 85),
            (("framework", "rollback_passed_cases"), 5),
        ):
            data = copy.deepcopy(read_results())
            parent = data
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                validate_results(data)

    def test_publication_contains_only_approved_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = build_public_site(Path(temporary) / "site")
            manifest = json.loads((output / "publication-manifest.json").read_text())
            for name, expected in manifest["source_files_sha256"].items():
                self.assertEqual(
                    hashlib.sha256((output / name).read_bytes()).hexdigest(), expected
                )
            for forbidden in (
                "evidence",
                "runtime",
                "config.local.json",
                "data.js",
                "events.json",
                "static-adapter.js",
            ):
                self.assertFalse((output / forbidden).exists())
            script = (output / "results-data.js").read_text(encoding="utf-8")
            self.assertNotIn("FINAL_DATA", script)
            self.assertNotIn("synthetic-event", script)
            self.assertIn('"queries": 463', script)
            with self.assertRaises(FileExistsError):
                build_public_site(output)

    def test_method_animation_has_no_fabricated_outputs(self):
        source = (ROOT / "web/film/scene.mjs").read_text(encoding="utf-8")
        stages = source[
            source.index("function stage1(") : source.index("function stage5(")
        ]
        self.assertNotIn("hash(", stages)
        self.assertNotIn('"reason": "Top-5 證據一致"', stages)
        self.assertIn("彙整結果", stages)
        self.assertIn("隔離TCP交易回條", source)
        self.assertNotIn("Math.round(v*100*o)", source)

    def test_release_text_uses_current_results(self):
        for name in (
            "README.md",
            "public/index.html",
            "web/film/scene.mjs",
            "scripts/presentation/build_deck.py",
        ):
            text = (ROOT / name).read_text(encoding="utf-8")
            for obsolete in ("96.76", "94.25", "95.83"):
                self.assertNotIn(obsolete, text, name)
