"""Print the speaker script as an A4 PDF for rehearsal and the lectern.

Text comes from deliverables/source/speaker-notes.md (the same notes embedded in the PPTX);
page titles and timings come from docs/決賽五分鐘口語稿.md. Each page shows the slide
thumbnail (deliverables/source/slides) beside the words to read. Rendered with headless Edge.
"""
import html
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / 'deliverables/source/speaker-notes.md'
ORAL = ROOT / 'docs/決賽五分鐘口語稿.md'
SLIDES = ROOT / 'deliverables/source/slides'
OUTPUT = ROOT / 'deliverables/決賽講稿_AI資安框架.pdf'
PAGE_HTML = ROOT / 'build/speaker-script.html'
BROWSERS = ['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
            'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
            'C:/Program Files/Google/Chrome/Application/chrome.exe']
QA_TITLES = {10: '答詢｜速度與誤判', 11: '答詢｜處置與 AI 可靠度', 12: '答詢｜新攻擊與導入'}

CSS = '''
@page{size:A4;margin:14mm 15mm 14mm}
body{margin:0;background:#FFFFFF;color:#15233A;font:11.5pt/1.75 "Microsoft JhengHei","Segoe UI",sans-serif}
header{border-bottom:2px solid #0B1B2E;padding-bottom:4mm;margin-bottom:5mm}
header h1{margin:0;font-size:20pt;color:#0B1B2E}
header p{margin:1.5mm 0 0;color:#52637A;font-size:10pt}
.page{display:grid;grid-template-columns:62mm 1fr;gap:6mm;padding:4.5mm 0;border-bottom:1px solid #DCE3EC;break-inside:avoid}
.page img{width:62mm;border:1px solid #DCE3EC;border-radius:2mm}
.meta{display:flex;align-items:baseline;gap:3mm;margin-bottom:1.5mm}
.num{background:#0B1B2E;color:#FFFFFF;border-radius:3mm;padding:0 2.4mm;font-weight:700;font-size:10pt}
.title{font-weight:700;color:#0B1B2E;font-size:12pt}
.time{margin-left:auto;color:#0F766E;font-weight:700;font-size:10pt;white-space:nowrap}
.say{margin:0;font-size:13pt;line-height:1.85}
.cue{margin:0;color:#52637A;font-size:11pt}
.qa{break-before:page}
.qa .page{grid-template-columns:1fr}
.qa .page img{width:70mm}
.q{margin:3mm 0 1mm;font-weight:700;color:#0F766E;font-size:12pt}
.qa-head{display:grid;grid-template-columns:70mm 1fr;gap:6mm;align-items:center}
'''


def sections():
    text = NOTES.read_text(encoding='utf-8')
    found = re.findall(r'^# (\d+)_slide\n\n(.*?)(?=\n\n---|\Z)', text, re.M | re.S)
    return [(int(n), body.strip()) for n, body in found]


def headings():
    return {int(n): (title, seconds) for n, title, seconds
            in re.findall(r'^## 第(\d+)頁｜(.+?)｜(\d+)秒$', ORAL.read_text(encoding='utf-8'), re.M)}


def thumbnail(n):
    return f'<img src="{(SLIDES / f"{n:02d}_slide.svg").as_uri()}" alt="第{n}頁">'


def render():
    heads = headings()
    total = sum(int(seconds) for n, (_, seconds) in heads.items() if n != 2)
    runbook = json.loads((ROOT / 'deliverables/source/finals-runbook.json').read_text(encoding='utf-8'))
    out = [f'<header><h1>決賽講稿｜AI資安框架</h1><p>第1至9頁正式報告：口述約{total}秒＋影片30秒，'
           f'另留一分鐘緩衝。第10至12頁為答詢備用，共{len(runbook["qa"])}題。照稿唸即可，數字已寫成口語念法。</p></header>']
    qa_open = False
    for n, body in sections():
        if n in heads:
            title, seconds = heads[n]
            paragraphs = ''.join(f'<p class="{"cue" if p.startswith("（") else "say"}">{html.escape(p)}</p>' for p in body.split('\n\n'))
            out.append(f'<section class="page">{thumbnail(n)}<div><div class="meta"><span class="num">{n:02d}</span>'
                       f'<span class="title">{html.escape(title)}</span><span class="time">{seconds} 秒</span></div>{paragraphs}</div></section>')
            continue
        if not qa_open:
            out.append('<div class="qa">')
            qa_open = True
        blocks = [p for p in body.split('\n\n') if not p.startswith('（')]
        items = ''.join(f'<p class="q">{html.escape(p)}</p>' if re.match(r'Q\d：', p) else f'<p class="say">{html.escape(p)}</p>' for p in blocks)
        out.append(f'<section class="page"><div class="qa-head">{thumbnail(n)}<div class="meta"><span class="num">{n:02d}</span>'
                   f'<span class="title">{QA_TITLES[n]}</span><span class="time">報告時不講</span></div></div>{items}</section>')
    if qa_open:
        out.append('</div>')
    return f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>決賽講稿</title><style>{CSS}</style></head><body>{"".join(out)}</body></html>'


def build():
    browser = next((path for path in BROWSERS if Path(path).exists()), None)
    if not browser:
        raise SystemExit('Edge or Chrome is required to print the speaker script')
    PAGE_HTML.parent.mkdir(exist_ok=True)
    PAGE_HTML.write_text(render(), encoding='utf-8')
    OUTPUT.unlink(missing_ok=True)
    subprocess.run([browser, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files',
                    f'--print-to-pdf={OUTPUT}', PAGE_HTML.as_uri()], check=True, capture_output=True, timeout=120)
    # Edge can return before the PDF is flushed; wait until the file exists and stops growing.
    size, deadline = -1, time.time() + 60
    while time.time() < deadline:
        current = OUTPUT.stat().st_size if OUTPUT.exists() else -1
        if current > 0 and current == size:
            break
        size = current
        time.sleep(0.5)
    else:
        raise SystemExit('Speaker script PDF was not written')
    print(f'Speaker script: {OUTPUT.relative_to(ROOT)}')


if __name__ == '__main__':
    build()
