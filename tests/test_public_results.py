"""Recorded public metrics must match counts; never substitute demonstration fixtures."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

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

    def test_deck_and_film_are_synchronized(self):
        deck = ROOT / "deliverables/決賽簡報_AI資安框架.pptx"
        film = ROOT / "deliverables/AI資安框架_系統展示影片_40秒快版.mp4"
        with zipfile.ZipFile(deck) as archive:
            xml = [
                archive.read(name).decode("utf-8")
                for name in archive.namelist()
                if name.endswith(".xml")
                and name.startswith(
                    (
                        "ppt/slides/slide",
                        "ppt/notesSlides/notesSlide",
                        "ppt/charts/chart",
                    )
                )
            ]
            self.assertGreaterEqual(len(xml), 18)
            text = "".join(xml)
            for obsolete in ("96.76%", "94.25%", "95.83%", "鏡像流量，免改"):
                self.assertNotIn(obsolete, text)
            for expected in ("97.62%", "93.89%", "隔離TCP"):
                self.assertIn(expected, text)
            movies = [
                archive.read(name)
                for name in archive.namelist()
                if name.endswith(".mp4")
            ]
            self.assertEqual(len(movies), 1)
            self.assertEqual(
                hashlib.sha256(movies[0]).hexdigest(),
                hashlib.sha256(film.read_bytes()).hexdigest(),
            )

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
