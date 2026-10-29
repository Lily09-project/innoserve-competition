"""Read-only workstation checks; model preload happens only with --warmup."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from settings import asset_path, optional_asset_path, execution_settings
from pipeline import TrainOnlyBank, digest
from server import source_revision
from asset_validation import validate_bundle
from provenance import runtime_assets, identifier


class Preflight:
    def __init__(self, root=ROOT, warmup=False, port=8765):
        self.root, self.warmup = Path(root), warmup
        self.base = f'http://127.0.0.1:{port}'

    def assets(self):
        folder = self.root / 'evidence/fresh17'
        return validate_bundle(folder)

    def models(self):
        ref = asset_path('ids_reference_root')
        manifest = json.loads((self.root/'evidence/fresh17/train_bank_manifest.json').read_text(encoding='utf-8'))
        if set(manifest.get('model_hashes', {})) != {'CTBM_Full','PBCNN_M1','PBCNN_M2'}:
            raise ValueError('Expected all three detector checkpoints')
        hashes = {}
        for name in manifest['model_hashes']:
            h = hashlib.sha256()
            with (ref/'models/augmented/seed_42'/name/'best_model.pt').open('rb') as stream:
                for block in iter(lambda: stream.read(1024*1024), b''):
                    h.update(block)
            hashes[name] = h.hexdigest()
        if hashes != manifest['model_hashes'] or digest(hashes) != manifest['model_sha256']:
            raise ValueError('checkpoint mismatch')
        gate = optional_asset_path('gate_impl_path', ref.parent/'gate_soft_oof_search.py')
        if not gate.is_file():
            raise FileNotFoundError('gate_impl_path')
        llm = asset_path('llama_model_dir')
        if not list(llm.glob('*.safetensors')) or not (llm/'config.json').is_file():
            raise FileNotFoundError('local Llama weights')
        return {'verified_checkpoints': len(hashes), 'local_llm_weights': True}

    def gpu(self):
        executable = optional_asset_path('python_executable', sys.executable)
        code = "import json,torch; assert torch.cuda.is_available(), 'CUDA unavailable'; print(json.dumps({'device':torch.cuda.get_device_name(0),'torch':torch.__version__}))"
        result = subprocess.run([str(executable), '-c', code], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError('Configured model Python failed CUDA check')
        return json.loads(result.stdout.strip().splitlines()[-1])

    def network(self):
        settings = execution_settings()
        code = "import mininet; from mininet.net import Mininet; import shutil; assert shutil.which('iptables'); print('MININET_READY')"
        result = subprocess.run(['wsl', '-d', settings['wsl_distribution'], '-u', settings['wsl_user'],
                                 '--', 'python3', '-c', code], capture_output=True, timeout=20)
        if result.returncode or b'MININET_READY' not in result.stdout:
            raise RuntimeError('WSL/Mininet/iptables unavailable')
        return 'isolated network dependencies available'

    def get(self, path):
        with urllib.request.urlopen(self.base+path, timeout=5) as response:
            return json.load(response)

    def service(self):
        value = self.get('/api/status')
        ids = value.get('live_event_ids', [])
        if value.get('product') != 'ai-security-demo.v3' or not isinstance(ids, list) or len(set(ids)) != 17:
            raise ValueError('wrong service or inputs')
        if value.get('source_revision') != source_revision():
            raise ValueError('Running service differs from this checkout; restart the local API')
        if value.get('model_ready'):
            if value.get('asset_revision') != identifier(runtime_assets(self.root)):
                raise ValueError('Running model assets differ from this checkout')
            return {'version': value['product'], 'model_ready': True}
        if not self.warmup:
            raise RuntimeError('Preload models before entering the competition area')
        req = urllib.request.Request(self.base+'/api/operate', data=b'{"action":"warmup"}',
                                     headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            job = json.load(response)
        deadline = time.monotonic()+execution_settings()['warmup_timeout_seconds']
        while time.monotonic() < deadline:
            state = self.get('/api/jobs/'+job['job_id'])
            if state.get('state') == 'error':
                raise RuntimeError('model preload failed; inspect local diagnostic log')
            if state.get('state') == 'done':
                if state.get('result', {}).get('ready') is not True:
                    raise ValueError('model preload completion has no readiness receipt')
                status = self.get('/api/status')
                if status.get('model_ready') is not True or status.get('source_revision')!=source_revision():
                    raise ValueError('Preload finished without current ready service')
                if status.get('asset_revision') != identifier(runtime_assets(self.root)):
                    raise ValueError('Preloaded assets differ from this checkout')
                return {'version':value['product'], 'model_ready':True}
            time.sleep(.5)
        raise TimeoutError('model preload')

    def run(self):
        checks = []
        for name, fn in (('private assets',self.assets),('model lineage',self.models),
                         ('CUDA runtime',self.gpu),('WSL isolation',self.network),('local demonstration',self.service)):
            try:
                if name == 'local demonstration' and self.warmup and any(not row['passed'] for row in checks):
                    raise RuntimeError('Model preload withheld because prerequisite checks failed')
                checks.append({'check':name,'passed':True,'detail':fn()})
            except Exception as exc:
                checks.append({'check':name,'passed':False,'error_type':type(exc).__name__,'error':str(exc)})
        return {'passed':all(row['passed'] for row in checks), 'checks':checks,
                'source_revision':source_revision(), 'created_utc':datetime.now(timezone.utc).isoformat(),
                'scope':'workstation readiness; no network policy deployed'}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--warmup',action='store_true')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args(argv)
    result = Preflight(warmup=args.warmup,port=args.port).run()
    output = args.output or ROOT/'validation'/('preflight_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    if output.exists():
        raise FileExistsError('Choose a new preflight report path; existing evidence retained')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for check in result['checks']:
        print('PASS' if check['passed'] else 'FAIL',check['check'],flush=True)
    print('READY' if result['passed'] else 'CHECK_FAILED',flush=True)
    print(output,flush=True)
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
