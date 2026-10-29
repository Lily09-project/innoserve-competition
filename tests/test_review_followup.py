"""Deployment, publication and data-source regressions from the full review."""
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import settings
from media_results import SOURCES, SNAPSHOT, snapshot, load_metrics
from check_delivery_docs import audit
from release_inventory import VISUAL_SOURCES, bindings


class ReviewFollowupTests(unittest.TestCase):
    def test_imported_model_helpers_do_not_require_raw_data(self):
        def asset(name):
            if name=='ids_data_root':raise FileNotFoundError('raw data absent')
            return ROOT
        with patch.object(settings,'asset_path',side_effect=asset) as configured, patch.dict(sys.modules,{
            'pandas':types.ModuleType('pandas'),'torch':types.ModuleType('torch')
        }):
            module=runpy.run_path(str(ROOT/'scripts/rebuild_retrieval.py'),run_name='review_model_import')
            self.assertEqual([row.args[0] for row in configured.call_args_list],['ids_reference_root'])
            with self.assertRaisesRegex(FileNotFoundError,'raw data absent'):
                module['main']()

    def test_snapshot_rejects_stale_or_manually_altered_metrics(self):
        with tempfile.TemporaryDirectory(prefix='media-results-contract-') as folder:
            root=Path(folder)
            for name in [SNAPSHOT,*[Path('results')/name for name in SOURCES.values()]]:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/name,target)
            self.assertEqual(load_metrics(root),snapshot(root)['values'])
            result=root/'results/retrieval_17class.json'
            value=json.loads(result.read_text(encoding='utf-8'));value['top5']=.98
            result.write_text(json.dumps(value),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'stale'):load_metrics(root)
            (root/SNAPSHOT).write_text(json.dumps(snapshot(root)),encoding='utf-8')
            self.assertEqual(load_metrics(root)['top5'],.98)
            tampered=json.loads((root/SNAPSHOT).read_text(encoding='utf-8'))
            tampered['values']['support']=999
            (root/SNAPSHOT).write_text(json.dumps(tampered),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'stale'):load_metrics(root)
            value['top5']=0
            result.write_text(json.dumps(value),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'retrieval scope'):snapshot(root)

    def test_ci_executes_data_and_delivery_checks(self):
        workflow=(ROOT/'.github/workflows/tests.yml').read_text(encoding='utf-8')
        for command in ('python scripts/media_results.py --check','python scripts/check_delivery_docs.py','node tests/media-data.cjs'):
            self.assertIn('run: '+command,workflow)
        self.assertTrue(all(f'deliverables/source/slides/{i:02d}_slide.svg' in VISUAL_SOURCES for i in range(1,13)))

    def test_delivery_check_rejects_changed_slide_and_broken_document(self):
        with tempfile.TemporaryDirectory(prefix='delivery-manifest-contract-') as folder:
            root=Path(folder)
            # Copy only public delivery dependencies; never private model assets.
            manifest=json.loads((ROOT/'deliverables/source/delivery-manifest.json').read_text(encoding='utf-8'))
            names=set(manifest['files'])|{'deliverables/source/delivery-manifest.json','deliverables/source/release-validation.json'}
            for group in bindings().values():names.update(group)
            for name in names:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
            (root/'REVIEW.md').write_text('[broken](missing.md)',encoding='utf-8')
            svg=root/'deliverables/source/slides/01_slide.svg'
            svg.write_bytes(svg.read_bytes()+b'\n<!-- changed in disposable test -->')
            with patch('check_delivery_docs.subprocess.check_output',return_value=b'REVIEW.md\0'):
                errors=audit(root)['errors']
            self.assertIn('REVIEW.md: missing link missing.md',errors)
            self.assertIn('deliverables/source/slides/01_slide.svg: delivery digest mismatch',errors)
            self.assertIn('Release source/artifact/preview evidence binding mismatch',errors)

    def test_retired_renderer_cannot_write_an_output(self):
        with tempfile.TemporaryDirectory(prefix='retired-renderer-contract-') as folder:
            output=Path(folder)/'must-not-exist.mp4'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/render_film_resvg.py'),'node',str(ROOT),str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('renderer is retired',result.stderr)
            self.assertFalse(output.exists())
