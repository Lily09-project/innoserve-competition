"""One-entry anonymous terminal demonstration; no website or automatic fallback."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from settings import optional_asset_path
from provenance import code_revision
from preflight import Preflight
import demo_walkthrough

SCENARIOS={'normal':'BENIGN','ftp':'FTP-BruteForce','ssh':'SSH-Bruteforce',
           'http':'DDoS-LOIC-HTTP','bot':'Bot','review':None}


def request(port,path,payload=None):
    req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,
        data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=5) as response:return json.load(response)


def ensure_service(port):
    try:
        status=request(port,'/api/status')
    except urllib.error.HTTPError:
        raise RuntimeError('port_used_by_other_service') from None
    except urllib.error.URLError:
        status=None
    if status is not None:
        if status.get('product')!='ai-security-demo.v3' or status.get('source_revision')!=code_revision():
            raise RuntimeError('restart_outdated_service')
        return False
    folder=ROOT/'runtime/service_logs';folder.mkdir(parents=True,exist_ok=True)
    stem=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    executable=optional_asset_path('python_executable',sys.executable)
    with (folder/(stem+'.stdout.log')).open('wb') as out,(folder/(stem+'.stderr.log')).open('wb') as err:
        process=subprocess.Popen([str(executable),'-X','utf8',str(ROOT/'app/server.py'),'--port',str(port)],
            cwd=ROOT,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for _ in range(60):
        if process.poll() is not None:raise RuntimeError('service_start_failed')
        try:
            status=request(port,'/api/status')
            if status.get('product')=='ai-security-demo.v3' and status.get('source_revision')==code_revision():return True
        except urllib.error.URLError:
            pass
        time.sleep(.5)
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill();process.wait(timeout=5)
    raise TimeoutError('service_start_timeout')


def choose_event(status,scenario):
    options=status.get('live_event_options',[])
    if scenario=='review':
        choices=[row for row in options if row.get('saved_assessment') in {'review','uncertain'}]
    else:
        choices=[row for row in options if row['prediction_label']==SCENARIOS[scenario]]
    if not choices:raise ValueError('scenario_unavailable')
    return choices[0]


def prepare(port):
    report=Preflight(warmup=True,port=port).run()
    for row in report['checks']:print(('PASS ' if row['passed'] else 'FAIL ')+row['check'])
    if not report['passed']:raise RuntimeError('preflight_failed')
    print('READY：本機模型、版本與隔離工具已核對。')


def run_scenario(port,scenario,mode,network=False):
    event=choose_event(request(port,'/api/status'),scenario)
    print('選擇情境依保存判定；本次即時結果以模型實際輸出為準。')
    args=['--port',str(port),'--mode',mode,'--event-index',str(event['index'])]
    if network:args.append('--network')
    return demo_walkthrough.main(args)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--scenario',choices=SCENARIOS)
    parser.add_argument('--mode',choices=('live','saved'),default='live')
    parser.add_argument('--network',action='store_true')
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args(argv)
    if args.network and args.mode!='live':parser.error('--network requires live mode')
    try:
        ensure_service(args.port)
        if args.prepare_only:
            prepare(args.port)
            return 0
        if args.scenario:
            if args.mode=='live':prepare(args.port)
            return run_scenario(args.port,args.scenario,args.mode,args.network)
        print('AI 資安框架｜匿名展示控制台')
        print('1 正常　2 FTP　3 SSH　4 HTTP　5 Bot　6 複核／不確定　7 預檢與預載　0 結束')
        while True:
            selected=input('展示> ').strip()
            if selected=='0':return 0
            if selected=='7':
                try:prepare(args.port)
                except (OSError,ValueError,RuntimeError,KeyError,TimeoutError):print('即時模型預檢失敗；可選擇保存結果備援。')
                continue
            if selected not in {'1','2','3','4','5','6'}:
                print('請輸入0至7。');continue
            mode=input('1 即時模型　2 保存結果備援：').strip()
            if mode not in {'1','2'}:print('未執行；請重新選擇。');continue
            network=False
            if mode=='1':
                try:prepare(args.port)
                except (OSError,ValueError,RuntimeError,KeyError,TimeoutError):
                    print('即時模型預檢失敗；可重新選擇保存結果備援。');continue
                network=input('1 僅判讀　2 加入隔離TCP處置（等待30秒回復）：').strip()=='2'
            scenario=list(SCENARIOS)[int(selected)-1]
            run_scenario(args.port,scenario,'live' if mode=='1' else 'saved',network)
            print('可繼續選擇情境；0結束。')
    except (OSError,ValueError,RuntimeError,KeyError,TimeoutError):
        print('展示準備中止。請在非投影畫面檢查設定與本機診斷；可明確選擇保存結果備援。',file=sys.stderr)
        return 1
    except (KeyboardInterrupt,EOFError):
        print('\n已離開控制台。服務持續保留；隔離工作由服務端期限及清理流程管理。')
        return 130


if __name__=='__main__':raise SystemExit(main())
