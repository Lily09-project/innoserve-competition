"""Real SSH service in owned namespaces, three trials and measured 30s TTL."""
import argparse
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'app'))
from live_network_test import build_owned_network
from active_defense_mininet_replay import apply_policy, reset_policy, inspect_policy
from network_safety import NetworkLease, NetworkDeadline, cleanup_owned
from network_contract import validate_network_scenario
from provenance import code_revision
import hashlib


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import paramiko
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(str(args.output / 'host.key'))
    (args.output / 'credentials.json').write_text(json.dumps({'username': 'isolated-lab', 'password': secrets.token_urlsafe(32)}))
    scenario = json.loads(args.scenario.read_text())
    validate_network_scenario(scenario)
    if scenario['action'] != 'auth_hardening' or scenario['ttl_seconds'] != 30:
        raise ValueError('requires_validated_ssh_30s_scenario')
    endpoint = ROOT / 'experiments/ssh_endpoint.py'
    owner = {}
    trials = []
    with NetworkLease(), NetworkDeadline(240) as deadline:
        if any(Path('/sys/class/net', n).exists() for n in ('s1', 's2', 's3')):
            raise RuntimeError('existing_network_busy')
        try:
            # Build using existing owned topology; replace its idle TCP endpoint immediately.
            subject, background, router = build_owned_network(str(ROOT / 'sources/paper_code/sim/mininet_traffic_endpoint.py'), owner)
            owner['process'].terminate()
            owner['process'].wait(timeout=5)
            owner['process'] = owner['net'].get('server').popen(
                [sys.executable, str(endpoint), 'server', '--folder', str(args.output)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)

            def wave(host, kind):
                process = host.popen([sys.executable, str(endpoint), 'wave', '--folder', str(args.output), '--kind', kind, '--count', '8'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process.communicate(timeout=12)
                if process.returncode:
                    raise RuntimeError('ssh_wave_failed:' + err.decode()[-200:])
                return json.loads(out)

            for trial in range(3):
                reset_policy(router)
                row = {'trial': trial + 1, 'baseline_invalid': wave(subject, 'invalid'),
                       'baseline_valid_subject': wave(subject, 'valid'), 'baseline_valid_background': wave(background, 'valid')}
                if row['baseline_invalid']['rejected'] != 8 or row['baseline_valid_subject']['healthy'] != 8 or row['baseline_valid_background']['healthy'] != 8:
                    raise RuntimeError('ssh_baseline_failed')
                owner['policy_started'] = True
                apply_policy(router, scenario)
                started = time.monotonic()
                row['rule_readback'] = inspect_policy(router)
                row['limited_invalid'] = wave(subject, 'invalid')
                row['limited_valid_background'] = wave(background, 'valid')
                row['limited_valid_subject'] = wave(subject, 'valid')
                while time.monotonic() - started < 30:
                    time.sleep(.1)
                reset_policy(router)
                row['ttl_rollback_seconds'] = time.monotonic() - started
                row['rollback_empty'] = not inspect_policy(router)['iptables'].strip()
                row['recovered_subject'] = wave(subject, 'valid')
                row['recovered_background'] = wave(background, 'valid')
                trials.append(row)
                (args.output / 'progress.json').write_text(json.dumps(trials, indent=2))
                print('SSH_TRIAL', trial + 1, flush=True)
        finally:
            deadline.begin_cleanup()
            cleanup = cleanup_owned(owner, reset_policy, inspect_policy)
            (args.output / 'cleanup.json').write_text(json.dumps(cleanup, indent=2))
    if not cleanup['passed']:
        raise RuntimeError('ssh_cleanup_failed')
    report = {'status': 'completed', 'source_revision': code_revision(), 'trials': trials, 'cleanup': cleanup,
              'scenario_sha256': file_sha(args.scenario), 'source_result_sha256': scenario['source_result_sha256'],
              'experiment_sources': {name: file_sha(ROOT / 'experiments' / name) for name in ('service_poc.py', 'ssh_endpoint.py')},
              'scope': 'Paramiko SSH password authentication on isolated namespace port 22. Policy selected from CIC SSH event; no claim of detecting generated SSH packets. Invalid passwords never authenticate. Rate limiting reduces reachability, not vulnerability repair. Same-source valid requests measure collateral restriction.'}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
