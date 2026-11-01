"""Projector console: same flow and checks as showcase.py, shown as staged result cards.

showcase.py and demo_walkthrough.py stay byte-identical because their hashes are part of the
recorded code revision; this file only reuses their verified functions and changes the display.
"""
import argparse
import json
import sys
import urllib.error

import console_card
import demo_walkthrough
from demo_walkthrough import api, job, summarize, summarize_receipt
from network_contract import build_network_scenario, verify_network_receipt, validate_measurement
from showcase import SCENARIOS, choose_event, ensure_service, prepare, request

MENU = {'1': 'normal', '2': 'ftp', '3': 'ssh', '4': 'http', '5': 'bot', '6': 'review'}


def walkthrough(port, index, mode, network, card):
    """demo_walkthrough.main with the same API calls and checks, rendered as cards."""
    demo_walkthrough.BASE = f'http://127.0.0.1:{port}'
    try:
        status = api('/api/status')
        ids = status['live_event_ids']
        if status['product'] != 'ai-security-demo.v3' or len(ids) != 17 or not 0 <= index < len(ids):
            raise ValueError('unexpected_service')
        key = ids[index]
        if mode == 'live':
            console_card.status('本次執行：即時模型推論、重新檢索與本機AI稽核。', card=card)
            if not status['model_ready']:
                console_card.status('預載本機模型中。', card=card)
                job({'action': 'warmup'})
            event = job({'action': 'live', 'event_id': key})
        else:
            console_card.status('本次執行：保存的模型判定與稽核回覆，案例檢索重新計算。', card=card)
            event = api('/api/export', {'event_id': key, 'mode': 'saved_prediction_replay'})
        summary = summarize(event, mode)
        console_card.render_summary(summary, card)
        if network:
            console_card.status('執行隔離TCP情境並等待期限回復，不接觸正式網路。', card=card)
            scenario = build_network_scenario(event)
            receipt = job({'action': 'network', 'event_id': key, 'execution_id': event['execution_id']})
            if not verify_network_receipt(scenario, receipt):
                raise ValueError('invalid_network_receipt')
            validate_measurement(scenario, receipt)
            summary['network_receipt'] = summarize_receipt(receipt)
            summary['network_executed_in_this_walkthrough'] = True
            console_card.render_receipt(summary['network_receipt'], card)
        else:
            console_card.status('本次未套用網路規則；處置回條可另以隔離情境展示。', card=card)
        folder = demo_walkthrough.ROOT / 'validation'
        folder.mkdir(exist_ok=True)
        (folder / 'demo-walkthrough-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        console_card.status('匿名展示摘要已保存。', card=card)
    except (urllib.error.URLError, KeyError, ValueError, TypeError, TimeoutError):
        print('展示中止：請在非投影畫面檢查本機服務、輸入或執行紀錄。', file=sys.stderr)
        return 1
    return 0


def run_scenario(port, scenario, mode, network, card):
    event = choose_event(request(port, '/api/status'), scenario)
    console_card.status('選擇情境依保存判定；本次即時結果以模型實際輸出為準。', card=card)
    return walkthrough(port, event['index'], mode, network, card)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--scenario', choices=SCENARIOS)
    parser.add_argument('--mode', choices=('live', 'saved'), default='live')
    parser.add_argument('--network', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args(argv)
    if args.network and args.mode != 'live':
        parser.error('--network requires live mode')
    card = console_card.Card()
    try:
        ensure_service(args.port)
        if args.prepare_only:
            prepare(args.port)
            return 0
        if args.scenario:
            if args.mode == 'live':
                prepare(args.port)
            return run_scenario(args.port, args.scenario, args.mode, args.network, card)
        console_card.menu(card)
        while True:
            selected = input('展示> ').strip()
            if selected == '0':
                return 0
            if selected == '7':
                try:
                    prepare(args.port)
                except (OSError, ValueError, RuntimeError, KeyError, TimeoutError):
                    print('即時模型預檢失敗；可選擇保存結果備援。')
                continue
            if selected not in MENU:
                print('請輸入0至7。')
                continue
            mode = input('1 即時模型　2 保存結果備援：').strip()
            if mode not in {'1', '2'}:
                print('未執行；請重新選擇。')
                continue
            network = False
            if mode == '1':
                try:
                    prepare(args.port)
                except (OSError, ValueError, RuntimeError, KeyError, TimeoutError):
                    print('即時模型預檢失敗；可重新選擇保存結果備援。')
                    continue
                network = input('1 僅判讀　2 加入隔離TCP處置（等待30秒回復）：').strip() == '2'
            run_scenario(args.port, MENU[selected], 'live' if mode == '1' else 'saved', network, card)
            console_card.menu(card)
    except (OSError, ValueError, RuntimeError, KeyError, TimeoutError):
        print('展示準備中止。請在非投影畫面檢查設定與本機診斷；可明確選擇保存結果備援。', file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\n已離開控制台。服務持續保留；隔離工作由服務端期限及清理流程管理。')
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
