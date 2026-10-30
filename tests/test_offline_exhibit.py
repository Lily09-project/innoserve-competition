"""Ensure the independent educational exhibit never claims live execution."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from pipeline import LABELS
from judge_response import JUDGE_PROMPT
from provenance import code_revision


class OfflineExhibitTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / 'deliverables/interactive/AI資安框架_自動循環展示.html').read_text(encoding='utf-8')

    def test_formal_class_names_and_prompt_are_consistent(self):
        labels = re.search(r'const LABELS = (\[.*?\]);', self.html, re.S)[1]
        self.assertEqual(json.loads(re.sub(r',\s*]', ']', labels)), LABELS)
        prompt = re.search(r'const SYSTEM_PROMPT = `(.*?)`;', self.html, re.S)[1]
        self.assertEqual(prompt, JUDGE_PROMPT)

    def test_file_has_no_remote_runtime_dependencies_or_identity_links(self):
        found = []
        class Scan(HTMLParser):
            def handle_starttag(self, tag, attrs):
                values = dict(attrs)
                if tag in ('iframe', 'form') or tag == 'script' and values.get('src'):
                    found.append(tag)
                for key in ('href', 'src'):
                    if values.get(key, '').startswith(('http:', 'https:', '//')):
                        found.append(values[key])
        Scan().feed(self.html)
        self.assertEqual(found, [])
        self.assertNotIn('github.com', self.html)
        self.assertNotIn('fetch(', self.html)
        self.assertNotIn('new WebSocket', self.html)

    def test_export_explicitly_labels_synthetic_data_and_no_execution(self):
        for value in ('synthetic_educational_demo', 'learned_models_executed: false',
                      'llm_called: false', 'network_rules_executed: false',
                      'illustrative_not_training_preprocessor', code_revision()):
            self.assertIn(value, self.html)
        self.assertNotIn('first 12 bytes to grayscale', self.html)

    def test_palette_fonts_and_accessible_playback_controls(self):
        palette = json.loads((ROOT / 'design-system/palette.json').read_text())
        for role in ('navy', 'blue', 'teal', 'gold', 'ink', 'gray', 'muted'):
            self.assertIn(palette[role].lower(), self.html.lower())
        for value in ('DFKai-SB', 'Times New Roman', 'unicode-range:', 'prefers-reduced-motion',
                      'id="playPause"', 'id="restart"', 'id="seek"', 'id="speed"'):
            self.assertIn(value, self.html)

    def test_all_literal_ui_colors_belong_to_shared_palette(self):
        palette = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
        allowed = {v.lower() for v in palette.values() if isinstance(v, str) and v.startswith('#')}
        for value in re.findall(r'#[0-9a-fA-F]{3,8}\b', self.html):
            color = value[1:].lower()
            if len(color) in (3, 4):
                color = ''.join(c * 2 for c in color)
            self.assertIn('#' + color[:6], allowed, value)
        self.assertNotIn('fill="hsl(', self.html)
        self.assertNotIn('background:hsl(', self.html)
        for unwanted in ('Consolas', 'Segoe UI', 'Microsoft JhengHei'):
            self.assertNotIn(unwanted, self.html)

    def test_four_stage_navigation_has_explicit_labels_and_boundaries(self):
        for stage in ('traffic', 'detection', 'audit', 'policy'):
            self.assertIn('data-stage="' + stage + '"', self.html)
        self.assertIn('aria-label="四階段方法流程"', self.html)
        self.assertIn('aria-current', self.html)


if __name__ == '__main__':
    unittest.main()
