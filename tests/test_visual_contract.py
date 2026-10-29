"""Guard the shared media identity, including hidden Office theme defaults."""
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/presentation'))
from style_contract import TYPOGRAPHY, THEME, font_runs, icon_fragment, resolve_colors


class VisualContractTests(unittest.TestCase):
    def test_white_canvas_foreground_contrast(self):
        palette = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
        def luminance(color):
            values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            return sum(w * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
                       for v, w in zip(values, (.2126, .7152, .0722)))
        self.assertEqual(palette['white'], '#FFFFFF')
        for role in ('navy', 'blue', 'teal', 'ink', 'muted'):
            self.assertGreaterEqual(1.05 / (luminance(palette[role]) + .05), 4.5, role)

    def test_legacy_paint_resolves_to_shared_palette(self):
        palette = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
        for old, role in palette['legacy_roles'].items():
            self.assertEqual(resolve_colors('<path fill="#' + old + '"/>'), '<path fill="' + palette[role] + '"/>')

    def test_mixed_text_font_roles(self):
        runs = font_runs('中文，測試：AI 17類（Top-5）97.62% ·')
        self.assertEqual(''.join(text for text, _ in runs), '中文，測試：AI 17類（Top-5）97.62% ·')
        for text, family in runs:
            if any(char in '中文，測試：類（）' for char in text):
                self.assertEqual(family, TYPOGRAPHY['cjk'])
            else:
                self.assertEqual(family, TYPOGRAPHY['latin'])

    def test_all_native_font_declarations_and_theme_colors(self):
        palette = json.loads((ROOT / 'design-system/palette.json').read_text(encoding='utf-8'))
        ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
        for name in ('決賽簡報_AI資安框架.pptx', '決賽海報_AI資安框架_A2.pptx'):
            with zipfile.ZipFile(ROOT / 'deliverables' / name) as archive:
                fonts = set()
                for path in archive.namelist():
                    if not (path.startswith('ppt/') and path.endswith('.xml')):
                        continue
                    root = ET.fromstring(archive.read(path))
                    fonts.update(node.get('typeface') for node in root.iter() if 'typeface' in node.attrib)
                    for scheme in root.findall('.//a:clrScheme', ns):
                        for node in scheme:
                            role = node.tag.rsplit('}', 1)[-1]
                            self.assertEqual(list(node)[0].get('val'), palette[THEME[role]].lstrip('#'), (name, path, role))
                self.assertEqual(fonts, {TYPOGRAPHY['cjk'], TYPOGRAPHY['latin']}, name)

    def test_shared_icon_library_is_text_free_and_flat(self):
        icons = json.loads((ROOT / 'design-system/icons.json').read_text(encoding='utf-8'))
        for name in icons:
            fragment = icon_fragment(name)
            self.assertNotIn('{{', fragment)
            for prohibited in ('<text', '<image', '<filter', '<linearGradient', '<radialGradient'):
                self.assertNotIn(prohibited, fragment, name)

    def test_every_native_text_shape_retains_an_alignment_target(self):
        ns = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
              'p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
        for name in ('決賽簡報_AI資安框架.pptx', '決賽海報_AI資安框架_A2.pptx'):
            with zipfile.ZipFile(ROOT / 'deliverables' / name) as archive:
                count = 0
                for path in archive.namelist():
                    if not (path.startswith('ppt/slides/slide') and path.endswith('.xml')):
                        continue
                    for shape in ET.fromstring(archive.read(path)).findall('.//p:sp',ns):
                        if any(node.text for node in shape.findall('.//a:t',ns)):
                            self.assertIsNotNone(shape.find('.//p:tags',ns),(name,path))
                            count += 1
                targets = []
                for path in archive.namelist():
                    if path.startswith('ppt/tags/') and path.endswith('.xml'):
                        for tag in ET.fromstring(archive.read(path)).findall('p:tag',ns):
                            if tag.get('name') == 'ALIGNMENT_TARGET_X':
                                targets.append(float(tag.get('val')))
                self.assertEqual(len(targets), count, name)
                self.assertTrue(all(0 <= value <= 1300 for value in targets),name)


if __name__ == '__main__':
    unittest.main()
