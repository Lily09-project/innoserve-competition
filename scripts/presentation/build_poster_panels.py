"""Draw the poster's six stage panels as neon HUD screens for one HTTP-flood run.

Every value shown is what the interactive exhibit displays in its HTTP-flood (ddos) scenario:
the eight synthetic packets, the 97% demonstration confidence, the case-bank and Top-5
similarities, the policy checks and the r1 iptables preview. The CTBM and PBCNN matrices are
cropped from the exhibit's own captured encoding (exhibit-detect.png), not redrawn. The panels
restyle that run for the poster; they are illustrations of the exhibit, not new results.
"""
from pathlib import Path
import base64
import io
import subprocess
import tempfile

from PIL import Image

from capture_exhibit_frames import OUT, browser

W, H = 1735, 1200  # 115.67 x 80 mm at 15 px per mm

PACKETS = [('#1', '0 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'), ('#2', '4 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'),
           ('#3', '8 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'), ('#4', '12 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'),
           ('#5', '16 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'), ('#6', '20 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d'),
           ('#7', '24 ms', 'Server → 來源', 'HTTP/1.1 200 OK'), ('#8', '28 ms', '來源 → Server', 'GET / HTTP/1.1 LOIC Host: d')]
BANK = [('正常連線', -0.031), ('DDoS / HTTP', 0.936), ('DoS / Hulk', 0.800), ('SSH 暴力破解', 0.001), ('Web / XSS', -0.010), ('Web / 登入', -0.007)]
TOP5 = [('DDoS / HTTP', 0.9956), ('DDoS / HTTP', 0.9815), ('DDoS / HTTP', 0.9586), ('DDoS / HTTP', 0.9358), ('DoS / Hulk', 0.8633)]
IPTABLES = ['iptables -N ACTIVE_DEFENSE', 'iptables -I FORWARD 1 -j ACTIVE_DEFENSE',
            'iptables -A ACTIVE_DEFENSE -s 10.10.1.10 -d 10.10.3.10 -p tcp --dport 80 --syn -m limit --limit 1/second --limit-burst 1 -j ACCEPT',
            'iptables -A ACTIVE_DEFENSE -s 10.10.1.10 -d 10.10.3.10 -p tcp --dport 80 --syn -j DROP']

CSS = '''
html,body{margin:0;width:%(w)dpx;height:%(h)dpx;overflow:hidden;background:#050c1a;color:#e2e8f0;
  font-family:"Segoe UI","Microsoft JhengHei",sans-serif}
.panel{position:absolute;inset:0;padding:175px 70px 50px;box-sizing:border-box;
  background:radial-gradient(ellipse at 78%% 12%%,var(--glow),transparent 58%%),
  linear-gradient(rgba(94,234,212,.05) 1px,transparent 1px) 0 0/40px 40px,
  linear-gradient(90deg,rgba(94,234,212,.05) 1px,transparent 1px) 0 0/40px 40px,
  linear-gradient(165deg,#0a1830,#050c1a 70%%)}
.frame{position:absolute;inset:14px;border:4px solid var(--a);border-radius:30px;
  box-shadow:0 0 22px var(--a),inset 0 0 40px rgba(0,0,0,.4)}
.hud{position:absolute;top:44px;right:70px;font:700 30px "Segoe UI";letter-spacing:6px;color:var(--a);
  text-shadow:0 0 14px var(--a)}
.mono{font-family:Consolas,"Cascadia Mono",monospace}
.glow{text-shadow:0 0 16px var(--a)}
.chip{border:3px solid var(--a);border-radius:22px;background:rgba(10,24,48,.85);box-shadow:0 0 18px color-mix(in srgb,var(--a) 55%%,transparent)}
.label{font-size:30px;color:#93a7c0}
.big{font-weight:800;color:#fff}
.row{display:flex;align-items:center}
''' % {'w': W, 'h': H}


def data_uri(image):
    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()


def panel_input():
    rows = ''.join(f'''<div class="row mono" style="height:100px;margin:9px 0;padding:0 26px;border-radius:14px;font-size:37px;
      background:{'rgba(34,197,94,.14)' if n == '#7' else 'rgba(59,130,246,.12)'};border-left:6px solid {'#22c55e' if n == '#7' else '#3b82f6'}">
      <span style="width:90px;color:#93c5fd">{n}</span><span style="width:160px;color:#93a7c0">{t}</span>
      <span style="width:350px">{d}</span><span style="color:{'#86efac' if n == '#7' else '#fda4af'}">{c}</span></div>''' for n, t, d, c in PACKETS)
    return f'''<div class="row mono" style="font-size:34px;color:#93c5fd;margin:-50px 0 14px 360px">FLOW-001 · TCP
      <span style="margin-left:auto;color:#93a7c0">10.10.1.10:41000 ⇄ 10.10.3.10:80</span></div>{rows}'''


def panel_detect(ctbm, pbcnn):
    gauge = 2*3.14159*120
    return f'''<div style="position:absolute;left:70px;top:150px;width:640px">
      <div class="chip" style="padding:18px 24px;margin-bottom:26px">
        <div class="row" style="font-size:40px"><b class="big">CTBM</b><span class="label" style="margin-left:18px">本團隊設計</span></div>
        <img src="{ctbm}" style="width:100%;margin-top:10px;border-radius:12px"></div>
      <div class="chip" style="padding:18px 24px;--a:#fb7185">
        <div class="row" style="font-size:40px"><b class="big">PBCNN</b><span class="label" style="margin-left:18px">既有模型</span></div>
        <img src="{pbcnn}" style="width:100%;margin-top:10px;border-radius:12px"></div></div>
    <svg style="position:absolute;left:710px;top:150px" width="400" height="980">
      <path d="M0 220 C200 220 200 450 390 450 M0 690 C200 690 200 490 390 490" fill="none" stroke="var(--a)" stroke-width="7"
        stroke-dasharray="4 16" stroke-linecap="round" style="filter:drop-shadow(0 0 8px var(--a))"/></svg>
    <div class="chip" style="position:absolute;left:1100px;top:470px;width:250px;height:250px;border-radius:50%;display:flex;
      flex-direction:column;align-items:center;justify-content:center;text-align:center">
      <div class="big glow" style="font-size:44px">融合</div><div class="label">校準 · OOF Gate</div></div>
    <svg style="position:absolute;left:1352px;top:560px" width="80" height="80"><path d="M6 40H70M50 18L72 40 50 62" fill="none" stroke="var(--a)" stroke-width="7"/></svg>
    <div style="position:absolute;left:1420px;top:300px;width:260px;text-align:center">
      <svg width="260" height="260" viewBox="0 0 260 260"><circle cx="130" cy="130" r="120" fill="none" stroke="#1e3a5c" stroke-width="16"/>
        <circle cx="130" cy="130" r="120" fill="none" stroke="var(--a)" stroke-width="16" stroke-linecap="round" transform="rotate(-90 130 130)"
          stroke-dasharray="{gauge*.97:.1f} {gauge:.1f}" style="filter:drop-shadow(0 0 10px var(--a))"/>
        <text x="130" y="150" text-anchor="middle" fill="#fff" font-size="64" font-weight="800">97%</text></svg>
      <div class="label" style="margin-top:6px">信心（示範）</div>
      <div class="big glow" style="font-size:38px;margin-top:26px;line-height:1.2">DDoS-LOIC<br>-HTTP</div>
      <div class="label" style="margin-top:8px">正式分類</div></div>'''


def panel_retrieve():
    bank = ''.join(f'''<div class="row" style="height:118px;font-size:34px"><span style="width:250px;color:#cbd5e1">{name}</span>
      <div style="flex:1;height:22px;background:#132a44;border-radius:11px;position:relative">
        <div style="position:absolute;left:0;top:0;bottom:0;width:{max(0, v)*100:.1f}%;border-radius:11px;background:{'var(--a)' if v > .5 else '#64748b'};
          box-shadow:{'0 0 14px var(--a)' if v > .5 else 'none'}"></div></div>
      <span class="mono" style="width:130px;text-align:right">{v:.3f}</span></div>''' for name, v in BANK)
    top = ''.join(f'''<div class="row" style="height:118px;margin:16px 0;padding:0 24px;border-radius:16px;font-size:36px;
      background:{'rgba(245,158,11,.16)' if label.startswith('DDoS') else 'rgba(100,116,139,.18)'};border:2px solid {'var(--a)' if label.startswith('DDoS') else '#475569'}">
      <b style="width:70px;color:var(--a)">#{k+1}</b><span style="flex:1">{label}</span><span class="mono big">{v:.4f}</span></div>''' for k, (label, v) in enumerate(TOP5))
    return f'''<div class="row" style="font-size:32px;gap:18px;margin-bottom:26px">
      <div class="chip row" style="padding:14px 22px;gap:10px"><span style="background:#0f766e;padding:6px 40px;border-radius:8px">512</span>
        <span style="background:#1d4ed8;padding:6px 14px;border-radius:8px">17</span><span class="label">= 529 維查詢向量</span></div>
      <span class="glow" style="color:var(--a)">→ L2 → cosine</span></div>
    <div style="display:flex;gap:40px">
      <div style="flex:1.05"><div class="label" style="margin-bottom:10px">訓練案例庫相似度（24 筆示例）</div>{bank}</div>
      <div style="flex:1"><div class="label" style="margin-bottom:4px">排序取 Top-5</div>{top}</div></div>'''


def panel_audit():
    inputs = [('正式分類', 'DDoS-LOIC-HTTP'), ('信心', '0.97'), ('Top-5 證據', '4 / 5 同類')]
    cards = ''.join(f'''<div class="chip" style="padding:20px 26px;margin-bottom:30px"><div class="label">{k}</div>
      <div class="big" style="font-size:40px;margin-top:4px">{v}</div></div>''' for k, v in inputs)
    return f'''<div style="position:absolute;left:70px;top:200px;width:470px">{cards}</div>
    <svg style="position:absolute;left:560px;top:200px" width="160" height="900"><path d="M0 110 C90 110 90 470 150 470 M0 330 C90 330 90 470 150 470 M0 560 C90 560 90 470 150 470"
      fill="none" stroke="var(--a)" stroke-width="6" stroke-dasharray="4 14" stroke-linecap="round" style="filter:drop-shadow(0 0 8px var(--a))"/></svg>
    <div style="position:absolute;left:720px;top:350px;width:420px;height:420px">
      <svg width="420" height="420" viewBox="0 0 420 420" style="filter:drop-shadow(0 0 18px var(--a))">
        <circle cx="210" cy="210" r="196" fill="none" stroke="var(--a)" stroke-width="4" stroke-dasharray="10 12"/>
        <rect x="95" y="95" width="230" height="230" rx="34" fill="#140c2b" stroke="var(--a)" stroke-width="8"/>
        <rect x="150" y="150" width="120" height="120" rx="16" fill="var(--a)" fill-opacity=".25" stroke="var(--a)" stroke-width="5"/>
        {''.join(f'<line x1="{x}" y1="70" x2="{x}" y2="95" stroke="var(--a)" stroke-width="7"/><line x1="{x}" y1="325" x2="{x}" y2="350" stroke="var(--a)" stroke-width="7"/>'
                 f'<line x1="70" y1="{x}" x2="95" y2="{x}" stroke="var(--a)" stroke-width="7"/><line x1="325" y1="{x}" x2="350" y2="{x}" stroke="var(--a)" stroke-width="7"/>' for x in (140, 180, 220, 260, 280))}
        <text x="210" y="226" text-anchor="middle" fill="#fff" font-size="54" font-weight="800">AI</text></svg>
      <div style="text-align:center;margin-top:12px;font-size:32px" class="glow">本機 AI 稽核 · Llama 3 8B</div></div>
    <svg style="position:absolute;left:1150px;top:530px" width="90" height="70"><path d="M6 35H80M58 12L82 35 58 58" fill="none" stroke="var(--a)" stroke-width="7"/></svg>
    <div class="chip" style="position:absolute;left:1250px;top:380px;width:420px;padding:36px 20px;text-align:center;--a:#22c55e">
      <svg width="140" height="140" viewBox="0 0 140 140" style="filter:drop-shadow(0 0 14px #22c55e)"><circle cx="70" cy="70" r="60" fill="none" stroke="#22c55e" stroke-width="9"/>
        <path d="M40 72L62 94 102 50" fill="none" stroke="#22c55e" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <div class="big" style="font-size:64px;color:#86efac">支持</div><div class="label">示範回覆</div>
      <div style="margin-top:22px;font-size:30px;color:#cbd5e1">正式分類保留不變<br>只附加稽核結論</div></div>'''


def panel_act():
    checks = ['分類信心 ≥ 0.8：0.97', 'Top-5 同類支持 ≥ 4：4 / 5', '限制指定來源、目標服務與 30 秒期限']
    items = ''.join(f'<div class="row" style="font-size:34px;margin:12px 0"><span class="glow" style="color:var(--a);width:60px;font-size:40px">✓</span>{c}</div>' for c in checks)
    def node(x, y, label, color, w=150):
        return (f'<g><rect x="{x}" y="{y}" width="{w}" height="84" rx="16" fill="#0a1830" stroke="{color}" stroke-width="5" style="filter:drop-shadow(0 0 10px {color})"/>'
                f'<text x="{x+w/2}" y="{y+56}" text-anchor="middle" fill="#fff" font-size="36" font-weight="700">{label}</text></g>')
    return f'''<div class="chip" style="padding:20px 34px;margin-bottom:28px"><div class="label">策略逐項檢查</div>{items}</div>
    <svg width="1595" height="560" viewBox="0 0 1595 560">
      <path d="M190 120 H330 L560 260 M190 440 H330 L560 300 M720 280 H980 M1130 280 H1300" fill="none" stroke="#3b82f6" stroke-width="7" stroke-dasharray="4 14" stroke-linecap="round"/>
      <path d="M190 120 H330 L560 260" fill="none" stroke="#fb7185" stroke-width="7" stroke-dasharray="4 14" stroke-linecap="round" style="filter:drop-shadow(0 0 8px #fb7185)"/>
      {node(30, 78, '來源', '#fb7185')}{node(30, 398, '正常', '#22c55e')}{node(330, 78, 's1', '#3b82f6', 100)}{node(330, 398, 's2', '#3b82f6', 100)}
      <circle cx="640" cy="280" r="96" fill="#0a1830" stroke="var(--a)" stroke-width="7" style="filter:drop-shadow(0 0 16px var(--a))"/>
      <circle cx="640" cy="280" r="128" fill="none" stroke="var(--a)" stroke-width="3" stroke-dasharray="8 10"/>
      <text x="640" y="272" text-anchor="middle" fill="#fff" font-size="44" font-weight="800">r1</text>
      <text x="640" y="320" text-anchor="middle" fill="#86efac" font-size="30" font-weight="700">限速</text>
      {node(980, 238, 's3', '#3b82f6', 150)}{node(1300, 238, 'Server', '#93c5fd', 230)}
      <text x="30" y="545" fill="#93a7c0" font-size="30">決定送達前（合成交易）：來源通過 720 · 正常背景 72</text></svg>'''


def panel_output():
    facts = ''.join(f'<div class="chip" style="flex:1;padding:18px 22px"><div class="label">{k}</div><div class="big" style="margin-top:4px">{v}</div></div>'
                    for k, v in (('來源', '10.10.1.10'), ('目標服務', '10.10.3.10 : 80'), ('期限', '30 秒到期回復')))
    lines = ''.join(f'<div style="margin:10px 0;color:#a7f3e4">{line.replace("iptables", "<span style=color:#fbbf24>iptables</span>")}</div>' for line in IPTABLES)
    return f'''<div class="chip" style="padding:24px 32px;margin-bottom:30px;--a:#22c55e">
      <div class="big glow" style="font-size:44px;color:#86efac">處置決定已送達 r1（示意）</div>
      <div style="font-size:34px;margin-top:12px;color:#cbd5e1">限制指定來源對目標服務的新連線，每秒允許一個，超額丟棄</div></div>
    <div class="chip" style="padding:0;overflow:hidden">
      <div class="row" style="height:64px;padding:0 24px;gap:14px;background:#0e2238">
        <i style="width:18px;height:18px;border-radius:50%;background:#fb7185"></i><i style="width:18px;height:18px;border-radius:50%;background:#fbbf24"></i>
        <i style="width:18px;height:18px;border-radius:50%;background:#22c55e"></i><span class="label" style="margin-left:14px">r1 · iptables 指令預覽</span></div>
      <div class="mono" style="padding:20px 30px 28px;font-size:32px;line-height:1.4">{lines}</div></div>
    <div class="row" style="gap:24px;margin-top:30px;font-size:32px">{facts}</div>'''


def build():
    detect = Image.open(OUT / 'exhibit-detect.png').convert('RGB')
    ctbm, pbcnn = data_uri(detect.crop((780, 150, 1295, 460))), data_uri(detect.crop((780, 822, 1295, 1130)))
    panels = {
        'input': ('#3B82F6', 'INPUT · RAW PACKETS', panel_input()),
        'detect': ('#F43F5E', 'STAGE 1 · DETECTION', panel_detect(ctbm, pbcnn)),
        'retrieve': ('#F59E0B', 'STAGE 2 · RETRIEVAL', panel_retrieve()),
        'audit': ('#A855F7', 'STAGE 3 · AI AUDIT', panel_audit()),
        'act': ('#22C55E', 'STAGE 4 · RESPONSE', panel_act()),
        'output': ('#22D3EE', 'OUTPUT · DECISION', panel_output()),
    }
    exe = browser()
    with tempfile.TemporaryDirectory() as folder:
        for name, (accent, hud, body) in panels.items():
            html = Path(folder) / f'{name}.html'
            glow = f'color-mix(in srgb,{accent} 30%,transparent)'
            html.write_text(f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="panel" style="--a:{accent};--glow:{glow}"><div class="frame"></div><div class="hud">{hud}</div>{body}</div></body></html>''', encoding='utf-8')
            subprocess.run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                            f'--window-size={W},{H}', f'--screenshot={OUT / f"stage-{name}.png"}', html.as_uri()], check=True, capture_output=True)
            print(f'stage-{name}.png')


if __name__ == '__main__':
    build()
