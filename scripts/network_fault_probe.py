"""Linux-only recovery experiment on a saved approved isolated scenario."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from provenance import code_revision


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    tested_revision=code_revision()
    probe_hash=hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    if json.loads(args.scenario.read_text(encoding='utf-8'))['action'] in {'monitor','capture_evidence'}:
        raise ValueError('Choose a disruptive approved isolated scenario for cleanup testing')
    args.output.mkdir(parents=True,exist_ok=False)
    children=[]
    def launch(name,deadline):
        output=args.output/(name+'.json')
        with (args.output/(name+'.log')).open('wb') as log:
            process=subprocess.Popen([sys.executable,str(ROOT/'scripts/live_network_test.py'),
                '--scenario',str(args.scenario),'--output',str(output),'--deadline-seconds',str(deadline)],stdout=log,stderr=log)
        children.append(process)
        return process,output
    def cleanup(path):return json.loads(path.with_suffix('.cleanup.json').read_text(encoding='utf-8'))
    try:
        timed,path=launch('deadline',8)
        rc=timed.wait(timeout=25);first=cleanup(path)
        if rc==0 or path.exists() or first['failure_type']!='TimeoutError' or not first['passed'] or not first['policy_started']:
            raise RuntimeError('deadline_cleanup_failed')
        interrupted,path=launch('interrupted',100)
        progress=path.with_suffix('.progress.json')
        until=time.monotonic()+25
        while not progress.exists() and time.monotonic()<until:
            if interrupted.poll() is not None:raise RuntimeError('network_did_not_reach_policy')
            time.sleep(.1)
        if not progress.exists():raise TimeoutError('policy_setup')
        rejected,rejected_path=launch('concurrent',20)
        rejection=rejected.wait(timeout=10)
        if rejection==0 or rejected_path.exists() or interrupted.poll() is not None:
            raise RuntimeError('network_lease_not_exclusive')
        interrupted.send_signal(signal.SIGTERM)
        rc=interrupted.wait(timeout=20);second=cleanup(path)
        if rc==0 or path.exists() or second['failure_type']!='InterruptedError' or not second['passed'] or not second['policy_started']:
            raise RuntimeError('interrupt_cleanup_failed')
        retry,path=launch('retry',100)
        if retry.wait(timeout=115)!=0:raise RuntimeError('retry_after_interrupt_failed')
        receipt=json.loads(path.read_text(encoding='utf-8'))
        if not receipt['cleanup']['passed'] or not receipt['rollback_integrity']:raise RuntimeError('retry_receipt_failed')
        if code_revision()!=tested_revision:raise RuntimeError('source_changed_during_recovery_probe')
        summary={'status':'passed','source_revision':tested_revision,'probe_script_sha256':probe_hash,
            'deadline_cleanup':True,'signal_cleanup':True,'concurrent_rejected':True,
            'retry_with_rules_and_expiry':True,'owned_links_remaining':[],
            'scope':'Real Mininet/iptables recovery on one saved approved scenario. No fresh detector or LLM calls; not an attack effectiveness experiment.'}
        (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(summary),flush=True)
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait(timeout=5)


if __name__=='__main__':main()
