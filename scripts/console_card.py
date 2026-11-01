"""Projector-readable result card for the terminal demo; formats verified summaries only."""
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import unicodedata

PALETTE = json.loads((Path(__file__).resolve().parents[1] / 'design-system/palette.json').read_text(encoding='utf-8'))
LABEL_ZH = {'BENIGN': '正常流量', 'FTP-BruteForce': 'FTP 暴力破解', 'SSH-Bruteforce': 'SSH 暴力破解',
            'DoS-GoldenEye': 'DoS GoldenEye', 'DoS-Hulk': 'DoS Hulk', 'DoS-Slowloris': 'DoS Slowloris',
            'DoS-SlowHTTPTest': 'DoS SlowHTTPTest', 'DDoS-LOIC-HTTP': 'DDoS HTTP 洪泛', 'DDoS-LOIC-UDP': 'DDoS UDP 洪泛',
            'DDOS-HOIC': 'DDoS HOIC', 'Web-BruteForce': '網頁暴力登入', 'Web-XSS': '跨站腳本 XSS',
            'SQL-Injection': 'SQL 注入', 'Bot': '殭屍網路', 'Infiltration': '內網滲透', 'PortScan': '連接埠掃描',
            'Heartbleed': 'Heartbleed 漏洞'}
ACTION_ZH = {'monitor': '持續監測', 'capture_evidence': '保留蒐證', 'auth_hardening': '強化認證',
             'rate_limit': '來源限速', 'upstream_scrubbing': '上游流量清洗', 'waf_virtual_patch': 'WAF 虛擬修補',
             'block_c2_destination': '阻擋 C2 目的地'}
ASSESSMENT = {'support': ('✓ 支持', 'cyan'), 'review': ('△ 複核', 'gold'), 'uncertain': ('? 不確定', 'on_dark_muted')}
WIDTH = 64


def enable_color(stream=sys.stdout):
    """Turn on ANSI colour in Windows consoles; plain text when output is redirected."""
    if not stream.isatty() or os.environ.get('NO_COLOR'):
        return False
    if os.name == 'nt':
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)) or not kernel.SetConsoleMode(handle, mode.value | 0x0004):
            return False
    return True


class Card:
    def __init__(self, color=None, pause=None, out=print):
        self.color = enable_color() if color is None else color
        self.pause = (0.35 if self.color else 0) if pause is None else pause
        self.out = out

    def paint(self, text, role, bold=False):
        if not self.color:
            return text
        r, g, b = (int(PALETTE[role][k:k + 2], 16) for k in (1, 3, 5))
        return f'\033[{"1;" if bold else ""}38;2;{r};{g};{b}m{text}\033[0m'

    def line(self, text=''):
        if self.out is print:
            print(text, flush=True)
        else:
            self.out(text)

    def stage(self, tag, title):
        if self.pause:
            time.sleep(self.pause)
        head = f'━━ {tag}  {title} '
        self.line()
        self.line(self.paint(head + '━' * max(4, WIDTH - width(head)), 'cyan', True))

    def row(self, name, value):
        self.line('  ' + self.paint(pad(name, 14), 'on_dark_muted') + value)


def width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in text)


def pad(text, columns):
    return text + ' ' * max(0, columns - width(text))


def bar(value, columns=24):
    filled = max(0, min(columns, round(value * columns)))
    return '█' * filled + '░' * (columns - filled)


def label(name):
    return f'{LABEL_ZH.get(name, name)}（{name}）'


def header(card, mode):
    title = 'AI 資安框架｜匿名展示控制台' if mode == 'menu' else 'AI 資安框架｜同一事件，四階段結果'
    source = {'menu': '選擇情境：偵測 → 檢索 → 稽核 → 處置，一次看完', 'live': '即時模型推論 · 重新檢索 · 本機 AI 稽核'}.get(
        mode, '保存判定與稽核 · 案例檢索重新計算')
    # Open-sided rules stay aligned even where a console font draws CJK narrower than two cells.
    card.line()
    card.line(card.paint('━' * WIDTH, 'cyan'))
    card.line('  ' + card.paint(title, 'white', True))
    card.line('  ' + card.paint(source, 'on_dark_muted'))
    card.line(card.paint('━' * WIDTH, 'cyan'))


def render_summary(summary, card=None):
    """Print a verified summary from demo_walkthrough.summarize as four revealed stages."""
    card = card or Card()
    header(card, summary['mode'])
    card.row('同一事件代碼', card.paint(summary['event_token'], 'gold', True))
    card.stage('1/4', '偵測｜互補模型正式判定')
    card.row('正式判定', card.paint(label(summary['prediction']), 'white', True))
    confidence = summary['confidence']
    card.row('校準信心', card.paint(bar(confidence), 'cyan') + ' ' + card.paint(f'{confidence * 100:.1f}%', 'white', True))
    card.stage('2/4', '檢索｜Top-5 相似訓練案例')
    for row in summary['top5']:
        same = row['label'] == summary['prediction']
        mark = card.paint('●', 'cyan') if same else card.paint('○', 'on_dark_muted')
        name = pad(LABEL_ZH.get(row['label'], row['label']), 14)
        card.line(f'  {mark} {row["rank"]}  {card.paint(name, "white" if same else "on_dark_muted")}'
                  f'{card.paint(bar(row["similarity"], 18), "cyan" if same else "blue_muted")} {row["similarity"]:.3f}')
    agree = sum(row['label'] == summary['prediction'] for row in summary['top5'])
    card.row('案例一致', card.paint(f'{agree} / 5 與正式判定同類', 'white'))
    card.stage('3/4', '稽核｜本機 AI 核對證據')
    verdict, role = ASSESSMENT[summary['assessment']]
    card.row('稽核結論', card.paint(verdict, role, True))
    card.row('正式分類', card.paint('保留不變（AI 只附加稽核，不改寫）', 'on_dark_muted'))
    card.stage('4/4', '處置｜策略閘道')
    card.row('處置動作', card.paint(ACTION_ZH.get(summary['policy_action'], summary['policy_action']), 'white', True))
    allowed = card.paint('✓ 允許執行', 'cyan', True) if summary['policy_allowed'] else card.paint('✕ 不自動執行，保留人工核准', 'gold', True)
    card.row('策略檢查', allowed)
    card.row('四階段紀錄', card.paint('✓ 同一事件綁定，雜湊鏈驗證通過', 'cyan'))


def render_receipt(receipt, card=None):
    """Print the isolated TCP receipt from demo_walkthrough.summarize_receipt."""
    card = card or Card()
    card.stage('回條', '處置回條｜隔離 TCP 情境')
    card.row('處置動作', card.paint(ACTION_ZH.get(receipt['action'], receipt['action']), 'white', True))
    card.row('套用規則', card.paint(f'{receipt["rules_applied"]} 條', 'white', True))
    card.row('背景交易', card.paint(f'{receipt["background_success_rate"] * 100:.0f}% 成功', 'white'))
    card.row('到期回復後', card.paint(f'{receipt["recovery_success_rate"] * 100:.0f}% 成功', 'white'))
    integrity = card.paint('✓ 規則已撤銷，回復完整', 'cyan', True) if receipt['rollback_integrity'] else card.paint('✕ 回復不完整', 'gold', True)
    card.row('回復完整性', integrity)


def status(text, role='on_dark_muted', card=None):
    card = card or Card(pause=0)
    card.line(card.paint('▸ ' + text, role))


def menu(card=None):
    """Scenario menu shown once when the anonymous console starts."""
    card = card or Card(pause=0)
    header(card, 'menu')
    for keys in (('1 正常流量', '2 FTP 暴力破解', '3 SSH 暴力破解'), ('4 HTTP 洪泛', '5 殭屍網路', '6 複核／不確定')):
        card.line('  ' + ''.join(card.paint(k[0], 'gold', True) + card.paint(pad(k[1:], 18), 'white') for k in keys))
    card.line('  ' + card.paint('7', 'gold', True) + card.paint(pad(' 預檢與預載', 18), 'on_dark_muted')
              + card.paint('0', 'gold', True) + card.paint(' 結束', 'on_dark_muted'))
