"""Anonymous terminal walkthrough for the real local API; never prints raw payloads."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from network_contract import build_network_scenario, valid_ledger, verify_network_receipt

LABELS = ['BENIGN', 'FTP-BruteForce', 'SSH-Bruteforce', 'DoS-GoldenEye',
          'DoS-Hulk', 'DoS-Slowloris', 'DoS-SlowHTTPTest', 'DDoS-LOIC-HTTP',
          'DDoS-LOIC-UDP', 'DDOS-HOIC', 'Web-BruteForce', 'Web-XSS',
          'SQL-Injection', 'Bot', 'Infiltration', 'PortScan', 'Heartbleed']
BASE = 'http://127.0.0.1:8765'


def api(path, payload=None):
    body = None if payload is None else json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(BASE+path, data=body,
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def job(payload, deadline_seconds=240):
    response = api('/api/operate', payload)
    job_id = response.get('job_id')
    if not job_id:
        raise ValueError('job_not_created')
    deadline = time.monotonic()+deadline_seconds
    while time.monotonic() < deadline:
        state = api('/api/jobs/'+job_id)
        if state.get('state') == 'done':
            return state['result']
        if state.get('state') == 'error':
            raise ValueError('local_job_failed')
        time.sleep(.5)
    raise TimeoutError('job_wait_expired')


def summarize(event, mode):
    result = event['result']
    ledger = result['ledger']
    if not valid_ledger(ledger) or len(ledger) != 4:
        raise ValueError('invalid_event_ledger')
    if any(row['event_id'] != event['event_id'] for row in ledger):
        raise ValueError('event_binding_mismatch')
    if result['event_id'] != event['event_id'] or result['prediction'] != event['prediction']:
        raise ValueError('result_binding_mismatch')
    if not 0 <= event['prediction'] < len(LABELS) or len(result['evidence']) != 5:
        raise ValueError('invalid_prediction_or_evidence')
    if mode == 'live' and (event.get('execution_mode') != 'live_local_models'
                         or ledger[0].get('execution_id') != event.get('execution_id')):
        raise ValueError('fresh_execution_required')
    summary = {
        'mode': mode,
        'event_token': hashlib.sha256(event['event_id'].encode()).hexdigest()[:12],
        'prediction': LABELS[event['prediction']],
        'confidence': round(float(event['confidence']), 6),
        'top5': [{'rank': row['rank'], 'label': row['label'],
                  'similarity': round(row['similarity'], 4)} for row in result['evidence']],
        'assessment': result['judge']['assessment'],
        'policy_allowed': result['policy']['allowed'],
        'policy_action': result['policy']['action'],
        'event_ledger_verified': True,
        'network_executed_in_this_walkthrough': False,
    }
    if mode == 'live':
        summary['execution_token'] = hashlib.sha256(event['execution_id'].encode()).hexdigest()[:12]
    return summary


def summarize_receipt(receipt):
    return {
        'action': receipt['action'],
        'rules_applied': receipt['rules_applied'],
        'background_success_rate': receipt['background_after']['success_rate'],
        'recovery_success_rate': receipt['recovery']['success_rate'],
        'rollback_integrity': receipt['rollback_integrity'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('live', 'saved'), default='live')
    parser.add_argument('--event-index', type=int, default=0,
                        help='Index in the API live input list, from 0 to 16; not a class label')
    parser.add_argument('--network', action='store_true', help='Run the isolated Mininet validation for this fresh execution')
    args = parser.parse_args()
    if args.network and args.mode != 'live':
        parser.error('--network requires --mode live')
    try:
        status = api('/api/status')
        ids = status['live_event_ids']
        if status['product'] != 'ai-security-demo.v3' or len(ids) != 17:
            raise ValueError('unexpected_service')
        if not 0 <= args.event_index < len(ids):
            raise ValueError('invalid_event_index')
        key = ids[args.event_index]
        if args.mode == 'live':
            print('本次執行：即時模型推論、重新檢索與本機AI稽核。', flush=True)
            if not status['model_ready']:
                print('預載本機模型中。', flush=True)
                job({'action': 'warmup'})
            event = job({'action': 'live', 'event_id': key})
        else:
            print('本次執行：保存的模型判定與稽核回覆，案例檢索重新計算。', flush=True)
            event = api('/api/export', {'event_id': key, 'mode': 'saved_prediction_replay'})
        summary = summarize(event, args.mode)
        print('同一事件代碼：'+summary['event_token'])
        print('正式判定：'+summary['prediction']+'　信心：'+str(summary['confidence']))
        print('Top-5 訓練案例：')
        for row in summary['top5']:
            print(f"  {row['rank']}. {row['label']}　相似度 {row['similarity']:.4f}")
        print('AI稽核：'+{'support': '支持', 'review': '複核', 'uncertain': '不確定'}[summary['assessment']])
        print('策略：'+summary['policy_action']+'　策略允許：'+str(summary['policy_allowed']))
        print('同事件四階段紀錄：驗證通過。', flush=True)
        if args.network:
            print('執行隔離TCP情境並等待期限回復，不接觸正式網路。', flush=True)
            scenario = build_network_scenario(event)
            receipt = job({'action': 'network', 'event_id': key, 'execution_id': event['execution_id']})
            if not verify_network_receipt(scenario, receipt):
                raise ValueError('invalid_network_receipt')
            summary['network_receipt'] = summarize_receipt(receipt)
            summary['network_executed_in_this_walkthrough'] = True
            print('同次執行回條驗證通過。')
            print('規則數：'+str(receipt['rules_applied'])+'　回復完整性：'+str(receipt['rollback_integrity']))
            print('背景交易成功率：'+str(summary['network_receipt']['background_success_rate'])+'　回復後交易成功率：'+str(summary['network_receipt']['recovery_success_rate']))
        else:
            print('本次未套用網路規則；處置回條可另以隔離情境展示。')
        folder = ROOT / 'validation'
        folder.mkdir(exist_ok=True)
        (folder / 'demo-walkthrough-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print('匿名展示摘要已保存。')
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError):
        print('展示中止：請在非投影畫面檢查本機服務、輸入或執行紀錄。', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
