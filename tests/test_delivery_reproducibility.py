"""A failed package build must preserve the last complete deliverable."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts/presentation')]
import package_finals
from finals_pipeline import STAGE_METADATA
from merge_static_poster import replace_page
from pypdf import PdfWriter, PdfReader


class PackageTests(unittest.TestCase):
    def test_zip_is_identical_across_repeated_builds_and_newline_styles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'deliverables').mkdir()
            text = root / 'note.md'
            text.write_bytes(b'first\r\nsecond\r\n')
            with patch.object(package_finals, 'ASSETS', ['note.md']):
                output = package_finals.build(root)
                original = output.read_bytes()
                text.write_bytes(b'first\nsecond\n')
                self.assertEqual(package_finals.build(root).read_bytes(), original)
                with zipfile.ZipFile(output) as archive:
                    self.assertEqual(archive.read('note.md'), b'first\nsecond\n')

    def test_missing_asset_preserves_previous_package_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'deliverables').mkdir()
            output = root / 'deliverables/決賽離線展示包.zip'
            output.write_bytes(b'previous-complete-package')
            with patch.object(package_finals, 'ASSETS', ['missing.md']):
                with self.assertRaises(FileNotFoundError):
                    package_finals.build(root)
            self.assertEqual(output.read_bytes(), b'previous-complete-package')
            self.assertEqual(list(output.parent.glob('.offline-*.tmp')), [])

    def test_failed_atomic_replace_preserves_previous_package(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'deliverables').mkdir()
            (root / 'note.md').write_text('fixture')
            output = root / 'deliverables/決賽離線展示包.zip'
            output.write_bytes(b'previous')
            with patch.object(package_finals, 'ASSETS', ['note.md']), patch.object(package_finals.os, 'replace', side_effect=PermissionError('fixture')):
                with self.assertRaises(PermissionError):
                    package_finals.build(root)
            self.assertEqual(output.read_bytes(), b'previous')
            self.assertEqual(list(output.parent.glob('.offline-*.tmp')), [])

    def test_assets_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'deliverables').mkdir()
            with patch.object(package_finals, 'ASSETS', ['../not-an-asset.md']):
                with self.assertRaisesRegex(ValueError, 'unsafe_package_asset'):
                    package_finals.build(root)

    def test_staging_contains_current_validation_and_interactive_guidance(self):
        for name in ('deliverables/source/finals-readiness.json', 'deliverables/source/recovery-validation.json', 'deliverables/interactive/README.md'):
            self.assertIn(name, STAGE_METADATA)


class StaticPosterTests(unittest.TestCase):
    def pdf(self, path, sizes):
        writer = PdfWriter()
        for width, height in sizes:
            writer.add_blank_page(width, height)
        with path.open('wb') as stream:
            writer.write(stream)

    def test_static_replacement_preserves_all_other_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, poster = root / 'source.pdf', root / 'poster.pdf'
            self.pdf(source, [(300, 200), (400, 200), (500, 200)])
            self.pdf(poster, [(400, 200)])
            self.assertEqual(replace_page(source, poster, source), 3)
            self.assertEqual([float(p.mediabox.width) for p in PdfReader(source).pages], [300, 400, 500])

    def test_wrong_size_is_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, poster = root / 'source.pdf', root / 'poster.pdf'
            self.pdf(source, [(300, 200), (400, 200)])
            self.pdf(poster, [(300, 200)])
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, 'size_mismatch'):
                replace_page(source, poster, source)
            self.assertEqual(source.read_bytes(), before)

    def test_invalid_page_is_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, poster = root / 'source.pdf', root / 'poster.pdf'
            self.pdf(source, [(300, 200)])
            self.pdf(poster, [(300, 200)])
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, 'invalid_static_poster_page'):
                replace_page(source, poster, source)
            self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
