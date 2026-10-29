"""Readiness and optional warmup must fail closed without real model execution."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import preflight


class PreflightTests(unittest.TestCase):
    def test_missing_private_asset_does_not_become_ready(self):
        with tempfile.TemporaryDirectory(prefix='preflight-assets-contract-') as folder:
            root=Path(folder);data=root/'evidence/fresh17';data.mkdir(parents=True)
            with patch.object(preflight.TrainOnlyBank,'load',return_value=SimpleNamespace(ids=[1],representation_id='fixture')):
                with self.assertRaises(FileNotFoundError):preflight.Preflight(root).assets()

    def test_wsl_timeout_propagates_as_failed_check(self):
        with patch.object(preflight.subprocess,'run',side_effect=subprocess.TimeoutExpired('wsl',20)):
            with self.assertRaises(subprocess.TimeoutExpired):preflight.Preflight().network()

    def status(self, ready=False):
        return {'product':'ai-security-demo.v3','source_revision':preflight.source_revision(),
                'model_ready':ready,'live_event_ids':[str(i) for i in range(17)]}

    def test_no_warmup_never_posts_a_job(self):
        probe=preflight.Preflight(warmup=False)
        with patch.object(probe,'get',return_value=self.status()),patch.object(preflight.urllib.request,'urlopen') as post:
            with self.assertRaises(RuntimeError):probe.service()
            post.assert_not_called()

    def test_ready_service_does_not_preload_again(self):
        probe=preflight.Preflight(warmup=True)
        with patch.object(probe,'get',return_value=self.status(True)),patch.object(preflight.urllib.request,'urlopen') as post:
            self.assertTrue(probe.service()['model_ready']);post.assert_not_called()

    def test_wrong_service_source_and_duplicate_inputs_rejected(self):
        for change in ({'product':'wrong'},{'source_revision':'old'},{'live_event_ids':['same']*17}):
            probe=preflight.Preflight()
            with patch.object(probe,'get',return_value={**self.status(True),**change}):
                with self.assertRaises(ValueError):probe.service()

    def warmup(self, state, clock=None):
        probe=preflight.Preflight(warmup=True)
        response=io.BytesIO(b'{"job_id":"fixture"}')
        with patch.object(probe,'get',side_effect=[self.status(),state]),patch.object(preflight.urllib.request,'urlopen',return_value=response),patch.object(preflight.time,'monotonic',side_effect=clock or [0,1]):
            return probe.service()

    def test_warmup_requires_readiness_receipt(self):
        self.assertTrue(self.warmup({'state':'done','result':{'ready':True}})['model_ready'])
        for state in ({'state':'done'},{'state':'done','result':{'ready':False}}):
            with self.assertRaises(ValueError):self.warmup(state)

    def test_warmup_error_and_timeout_are_not_ready(self):
        with self.assertRaises(RuntimeError):self.warmup({'state':'error'})
        with self.assertRaises(TimeoutError):self.warmup({},[0,1000000])

    def test_gpu_failure_and_timeout_are_reported(self):
        probe=preflight.Preflight()
        with patch.object(preflight.subprocess,'run',return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(RuntimeError):probe.gpu()
        with patch.object(preflight.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',30)):
            with self.assertRaises(subprocess.TimeoutExpired):probe.gpu()

    def test_network_uses_configured_runtime_and_checks_marker(self):
        probe=preflight.Preflight()
        with patch.object(preflight,'execution_settings',return_value={'wsl_distribution':'Chosen','wsl_user':'tester'}),patch.object(preflight.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'MININET_READY')) as run:
            probe.network();self.assertEqual(run.call_args.args[0][:5],['wsl','-d','Chosen','-u','tester'])
            self.assertNotIn('iptables -',run.call_args.args[0][-1])
        with patch.object(preflight.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'')):
            with self.assertRaises(RuntimeError):probe.network()

    def test_failed_prerequisite_prevents_preload(self):
        probe=preflight.Preflight(warmup=True)
        with patch.object(probe,'assets',side_effect=ValueError('missing')),patch.object(probe,'models',return_value={}),patch.object(probe,'gpu',return_value={}),patch.object(probe,'network',return_value={}),patch.object(probe,'service') as service:
            result=probe.run();self.assertFalse(result['passed']);service.assert_not_called()
            self.assertFalse(result['checks'][-1]['passed'])

    def test_all_check_results_are_preserved(self):
        probe=preflight.Preflight()
        with patch.object(probe,'assets',return_value={}),patch.object(probe,'models',side_effect=ValueError('hash mismatch')),patch.object(probe,'gpu',side_effect=RuntimeError('CUDA')),patch.object(probe,'network',return_value={}),patch.object(probe,'service',return_value={}):
            result=probe.run();self.assertFalse(result['passed']);self.assertEqual(len(result['checks']),5)
            self.assertEqual([r['passed'] for r in result['checks']],[True,False,False,True,True])

    def test_model_hash_mismatch_and_missing_weights_fail(self):
        with tempfile.TemporaryDirectory(prefix='preflight-model-contract-') as folder:
            root=Path(folder);data=root/'evidence/fresh17';data.mkdir(parents=True)
            ref=root/'reference';names=('CTBM_Full','PBCNN_M1','PBCNN_M2')
            hashes={}
            for name in names:
                path=ref/'models/augmented/seed_42'/name/'best_model.pt';path.parent.mkdir(parents=True);path.write_bytes(b'disposable checkpoint fixture')
                hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
            manifest={'model_hashes':hashes,'model_sha256':preflight.digest(hashes)}
            path=data/'train_bank_manifest.json';path.write_text(json.dumps(manifest))
            gate=root/'gate.py';gate.write_text('# fixture')
            llm=root/'llm';llm.mkdir();(llm/'config.json').write_text('{}');(llm/'part.safetensors').write_bytes(b'fixture')
            probe=preflight.Preflight(root)
            with patch.object(preflight,'asset_path',side_effect=lambda key:ref if key=='ids_reference_root' else llm),patch.object(preflight,'optional_asset_path',return_value=gate):
                self.assertEqual(probe.models()['verified_checkpoints'],3)
                (ref/'models/augmented/seed_42'/names[0]/'best_model.pt').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'checkpoint mismatch'):probe.models()
                manifest['model_hashes']={};path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError,'three detector'):probe.models()
