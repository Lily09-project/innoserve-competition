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
from media_results import load_metrics


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

    def test_zero_rule_intervention_cannot_be_reported_as_success(self):
        data=copy.deepcopy(read_results())
        for row in data['framework']['cases']:
            row['rules_applied']=0;row['after_success_rate']=1;row['ttl_rollback_elapsed_seconds']=None
        data['framework']['non_disruptive_network_cases']=6
        with self.assertRaisesRegex(ValueError,'policy rules missing'):validate_results(data)

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
            self.assertGreaterEqual(len(xml), 24)
            text = "".join(xml)
            for obsolete in ("96.76%", "94.25%", "95.83%", "鏡像流量，免改"):
                self.assertNotIn(obsolete, text)
            metrics=load_metrics()
            for expected in (f'{metrics["top5"]*100:.2f}%', f'{metrics["mrr5"]*100:.2f}%', f'{metrics["accuracy"]*100:.2f}%', "隔離TCP"):
                self.assertIn(expected, text)
            movies = [
                archive.read(name)
                for name in archive.namelist()
                if name.endswith(".mp4")
            ]
            self.assertEqual(len(movies), 1)
            self.assertEqual(movies[0], film.read_bytes())
            slot = archive.read("ppt/slides/slide2.xml").decode("utf-8")
            self.assertIn("OpeningFilm_30s_Embedded", slot)
            self.assertIn("playFrom(0.0)", slot)
            self.assertEqual(len([n for n in archive.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]), 12)
            relationships = archive.read("ppt/slides/_rels/slide2.xml.rels").decode("utf-8")
            self.assertIn("relationships/video", relationships)
            self.assertNotIn('TargetMode="External"', relationships)
            ending = archive.read("ppt/slides/slide9.xml").decode("utf-8")
            self.assertIn("感謝聆聽", ending)
            appendix="".join(archive.read(f"ppt/slides/slide{i}.xml").decode("utf-8") for i in range(10,13))
            for question in range(1,7):self.assertIn(f"Q{question}",appendix)
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
            for number in range(1, 13):
                slide = ET.fromstring(archive.read(f"ppt/slides/slide{number}.xml"))
                self.assertIsNone(slide.find("p:transition", ns))
                timing = slide.find("p:timing", ns)
                if number == 2:
                    self.assertIsNotNone(timing)
                    self.assertEqual(len(timing.findall(".//p:video", ns)), 1)
                    self.assertIsNone(timing.find(".//p:anim", ns))
                    self.assertIsNone(timing.find(".//p:animMotion", ns))
                else:
                    self.assertIsNone(timing)
                for run in slide.findall(".//a:r", ns):
                    properties = run.find("a:rPr", ns)
                    self.assertIsNotNone(properties)
                    self.assertEqual(properties.find("a:latin", ns).get("typeface"), "Times New Roman")
                    self.assertEqual(properties.find("a:ea", ns).get("typeface"), "DFKai-SB")
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
                palette = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
                self.assertIn(resolved, (palette['white'].lstrip('#'), palette['gray'].lstrip('#')))

    def test_current_documentation_and_movie_contract(self):
        from check_delivery_docs import audit
        report = audit()
        self.assertEqual(report['errors'], [])
        self.assertGreaterEqual(report['document_count'], 13)
