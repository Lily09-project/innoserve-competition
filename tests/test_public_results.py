"""Recorded public metrics must match counts; never substitute demonstration fixtures."""

import copy
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_results import read_results, validate_results


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

    def test_deck_and_film_are_synchronized(self):
        deck = ROOT / "deliverables/決賽簡報_AI資安框架.pptx"
        film = ROOT / "deliverables/AI資安框架_系統展示影片_30秒快版.mp4"
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
            self.assertGreaterEqual(len(xml), 16)
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
            self.assertEqual(len(movies), 0)
            self.assertGreater(film.stat().st_size, 100_000)

    def test_method_animation_has_no_fabricated_outputs(self):
        source = (ROOT / "media/film/scene.mjs").read_text(encoding="utf-8")
        self.assertNotIn("Math.random", source)
        self.assertIn("隔離TCP交易實測", source)
        self.assertFalse((ROOT / "public").exists())
        self.assertFalse((ROOT / ".github/workflows/pages.yml").exists())

    def test_release_text_uses_current_results(self):
        for name in (
            "README.md",
            "media/film/scene.mjs",
            "scripts/presentation/editorial_assets.py",
        ):
            text = (ROOT / name).read_text(encoding="utf-8")
            for obsolete in ("96.76", "94.25", "95.83"):
                self.assertNotIn(obsolete, text, name)

    def test_deck_metadata_namespaces_and_light_backgrounds(self):
        import io
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(ROOT / "deliverables/決賽簡報_AI資安框架.pptx") as archive:
            core = archive.read("docProps/core.xml")
            namespaces = dict(item for _, item in ET.iterparse(io.BytesIO(core), events=["start-ns"]))
            tree = ET.fromstring(core)
            for node in tree.iter():
                value = node.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
                if ":" in value:
                    self.assertIn(value.split(":", 1)[0], namespaces)
            ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                  "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
            for number in range(1, 9):
                slide = ET.fromstring(archive.read(f"ppt/slides/slide{number}.xml"))
                fill = slide.find(".//p:bg/p:bgPr/a:solidFill", ns)
                self.assertIsNotNone(fill)
                color = list(fill)[0]
                if color.tag.endswith("schemeClr"):
                    theme = ET.fromstring(archive.read("ppt/theme/theme1.xml"))
                    theme_color = theme.find(".//a:clrScheme/a:" + color.get("val") + "/a:srgbClr", ns)
                    self.assertIsNotNone(theme_color)
                    resolved = theme_color.get("val")
                else:
                    resolved = color.get("val")
                self.assertIn(resolved, ("FFFFFF", "F2F7FC"))

    def test_current_documentation_and_movie_contract(self):
        from check_delivery_docs import audit
        report = audit()
        self.assertEqual(report['errors'], [])
        self.assertGreaterEqual(report['document_count'], 13)
