"""Draw the poster's full-page background: a dark cinematic tech canvas and a data-centre footer.

Original vector artwork in a night, neon-lit style; it carries no data. A glowing skyline with
a hologram globe and chart sits behind the masthead, a faint hex grid, bokeh and circuit
traces fill the page behind the translucent cards, every card gets a soft cyan halo, and the
footer is a server-rack aisle receding to the framework emblem, with a switch on the left and
the four stages stacked on the right. Rendered by headless Edge/Chrome at 10 px per mm so
Windows CJK fonts are used.
"""
from pathlib import Path
import math
import random
import subprocess
import tempfile

from capture_exhibit_frames import OUT, browser

WIDTH, HEIGHT = 4200, 5940  # A2 portrait at 10 px per mm
BAND = 5200                 # footer art starts below the poster's last text line (520 mm)


def shield(cx, cy, size):
    s = size/100
    return (f'<g transform="translate({cx-50*s:.1f} {cy-60*s:.1f}) scale({s:.3f})" class="glow" style="color:#1D4ED8">'
            '<path d="M50 0 L100 20 V58 C100 92 76 112 50 122 C24 112 0 92 0 58 V20 Z" fill="url(#shieldFill)" stroke="#FFFFFF" stroke-width="5"/>'
            '<path d="M28 60 L45 77 L74 44" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></g>')


def skyline(rng):
    """Night skyline behind the masthead, lit windows fading into the page."""
    out, x = [], -40
    base = 1240
    while x < WIDTH:
        w, h = rng.uniform(140, 330), rng.uniform(180, 640)
        out.append(f'<rect x="{x:.0f}" y="{base-h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="url(#tower)"/>')
        for wy in range(int(base-h+24), base-20, 34):
            for wx in range(int(x+18), int(x+w-24), 30):
                if rng.random() < .2:
                    color = rng.choice(('#5EEAD4', '#93C5FD', '#FCD34D', '#FFFFFF'))
                    out.append(f'<rect x="{wx}" y="{wy}" width="12" height="16" fill="{color}" fill-opacity="{rng.uniform(.25, .7):.2f}"/>')
        x += w+rng.uniform(6, 30)
    out.append(f'<rect y="0" width="{WIDTH}" height="{base}" fill="url(#mastFade)"/>')
    out.append(f'<rect y="{base-6}" width="{WIDTH}" height="12" fill="#5EEAD4" fill-opacity=".5" filter="url(#blur)"/>')
    out.append(f'<line x1="0" y1="{base}" x2="{WIDTH}" y2="{base}" stroke="#5EEAD4" stroke-opacity=".7" stroke-width="3"/>')
    return ''.join(out)


def bokeh(rng):
    out = []
    for _ in range(90):
        x, y = rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT)
        color = rng.choice(('#5EEAD4', '#3B82F6', '#3B82F6', '#F59E0B'))
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(8, 46):.0f}" fill="{color}" fill-opacity="{rng.uniform(.05, .16):.2f}" filter="url(#soft)"/>')
    return ''.join(out)


def circuits(rng):
    """Right-angled traces with pads along both margins."""
    out = []
    for side in (0, 1):
        for _ in range(9):
            y = rng.uniform(1400, BAND-200)
            x0 = 0 if side == 0 else WIDTH
            step = 1 if side == 0 else -1
            x1 = x0+step*rng.uniform(60, 150)
            y1 = y+rng.choice((-1, 1))*rng.uniform(40, 160)
            x2 = x1+step*rng.uniform(30, 70)
            out.append(f'<path d="M{x0} {y:.0f}H{x1:.0f}L{x2:.0f} {y1:.0f}" fill="none" stroke="#5EEAD4" stroke-opacity=".35" stroke-width="3"/>'
                       f'<circle cx="{x2:.0f}" cy="{y1:.0f}" r="7" fill="none" stroke="#5EEAD4" stroke-opacity=".6" stroke-width="3"/>')
    return ''.join(out)


def halos():
    """Soft cyan glow behind each card on the poster's 3-column grid (mm x 10)."""
    cw = (372-16)/3
    cols = [24+k*(cw+8) for k in range(3)]
    boxes = [(cols[k], 147, cw, 16) for k in range(3)]
    boxes += [(cols[n % 3], (168, 283)[n//3], cw, 107) for n in range(6)]
    boxes += [(cols[0], 414, 2*cw+8, 96), (cols[2], 414, cw, 96)]
    return ''.join(f'<rect x="{x*10:.0f}" y="{y*10:.0f}" width="{w*10:.0f}" height="{h*10:.0f}" rx="24" fill="#5EEAD4" fill-opacity=".05" '
                   f'stroke="#5EEAD4" stroke-opacity=".55" stroke-width="10" filter="url(#halo)"/>' for x, y, w, h in boxes)


def aisle():
    """Data-centre aisle panorama for the footer: racks recede to a glowing framework emblem."""
    y0, h = BAND+40, HEIGHT-BAND-40
    vx, vy = WIDTH/2, y0+270
    out = [f'<rect y="{y0}" width="{WIDTH}" height="{h}" fill="url(#aisleBg)"/>']
    # Ceiling light strips and floor seams converge on the vanishing point.
    for k in range(-7, 8):
        out.append(f'<line x1="{vx+k*40}" y1="{vy-40}" x2="{vx+k*620}" y2="{y0}" stroke="#BFDBFE" stroke-opacity=".38" stroke-width="7"/>')
        out.append(f'<line x1="{vx+k*30}" y1="{vy+50}" x2="{vx+k*700}" y2="{y0+h}" stroke="#5EEAD4" stroke-opacity=".16" stroke-width="3"/>')
    out.append(f'<ellipse cx="{vx}" cy="{y0+h-40}" rx="1500" ry="90" fill="#1D4ED8" fill-opacity=".25" filter="url(#blur)"/>')
    rng = random.Random(5)
    for side in (-1, 1):
        for k in range(7):
            t1, t2 = 1-0.74**k, 1-0.74**(k+1)
            def at(t, top):
                x = (0 if side < 0 else WIDTH)-side*(vx-460)*t
                y = (y0+10 if top else y0+h)+((vy-120 if top else vy+120)-(y0+10 if top else y0+h))*t
                return x, y
            (ax, ay), (bx, by) = at(t1+.01, True), at(t2-.01, True)
            (cx, cy), (dx, dy) = at(t2-.01, False), at(t1+.01, False)
            out.append(f'<polygon points="{ax:.0f},{ay:.0f} {bx:.0f},{by:.0f} {cx:.0f},{cy:.0f} {dx:.0f},{dy:.0f}" fill="url(#rackFace)" stroke="#3B6EA8" stroke-width="5"/>')
            for col in range(3):
                f = .25+col*.25
                x = ax+(bx-ax)*f
                ytop, ybot = ay+(by-ay)*f, dy+(cy-dy)*f
                for r in range(10):
                    if rng.random() < .7:
                        y = ytop+(ybot-ytop)*(r+.5)/10
                        color = rng.choice(('#5EEAD4', '#3B82F6', '#60A5FA', '#22C55E'))
                        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{max(3, 12*(1-t1)):.1f}" fill="{color}" class="glow" style="color:{color}"/>')
    # Framework emblem at the end of the aisle.
    out.append(f'<circle cx="{vx}" cy="{vy}" r="330" fill="url(#emblemGlow)"/>')
    out.append(shield(vx, vy-70, 170))
    out.append(f'<text x="{vx}" y="{vy+120}" text-anchor="middle" class="emblem">AI 資安框架</text>')
    out.append(f'<text x="{vx}" y="{vy+182}" text-anchor="middle" class="emblemSub">偵測 · 檢索 · 稽核 · 處置</text>')
    out.append(f'<path d="M{vx-360} {vy+225} C{vx-120} {vy+200} {vx+140} {vy+212} {vx+380} {vy+185}" fill="none" stroke="#F59E0B" stroke-width="12" stroke-linecap="round" class="glow" style="color:#F59E0B"/>')
    # Foreground switch on the left and stacked stage slabs on the right.
    sx, sy = 260, y0+330
    out.append(f'<path d="M{sx} {sy} L{sx+80} {sy-60} L{sx+980} {sy-60} L{sx+900} {sy} Z" fill="#22324A"/>')
    out.append(f'<rect x="{sx}" y="{sy}" width="900" height="170" rx="10" fill="#141F31" stroke="#3B5578" stroke-width="4"/>')
    out.append(f'<path d="M{sx+900} {sy} L{sx+980} {sy-60} L{sx+980} {sy+110} L{sx+900} {sy+170} Z" fill="#0E1726"/>')
    for k in range(16):
        px = sx+260+k*38+(k//8)*20
        out.append(f'<rect x="{px}" y="{sy+50}" width="28" height="26" rx="3" fill="#05080F" stroke="#64748B" stroke-width="2"/>'
                   f'<rect x="{px}" y="{sy+92}" width="28" height="26" rx="3" fill="#05080F" stroke="#64748B" stroke-width="2"/>'
                   f'<circle cx="{px+14}" cy="{sy+40}" r="4" fill="{"#22C55E" if k % 3 else "#F59E0B"}"/>')
    out.append(f'<text x="{sx+40}" y="{sy+100}" class="device">AI SEC</text>')
    for k, (zh, en) in enumerate((('偵測', 'DETECTION'), ('檢索', 'RETRIEVAL'), ('稽核', 'AI AUDIT'), ('處置', 'RESPONSE'))):
        bx, by = 3180+k*18, y0+500-k*74
        out.append(f'<path d="M{bx} {by} L{bx+60} {by-34} L{bx+820} {by-34} L{bx+760} {by} Z" fill="#26364F"/>'
                   f'<rect x="{bx}" y="{by}" width="760" height="64" fill="#101B2D" stroke="#3B5578" stroke-width="3"/>'
                   f'<path d="M{bx+760} {by} L{bx+820} {by-34} L{bx+820} {by+30} L{bx+760} {by+64} Z" fill="#0A1220"/>'
                   f'<text x="{bx+380}" y="{by+46}" text-anchor="middle" class="slab">{zh}　{en}</text>')
    return ''.join(out)


def globe(cx, cy, r):
    """Wireframe hologram globe with orbit arcs (decorative)."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#1D4ED8" fill-opacity=".10" stroke="#5EEAD4" stroke-opacity=".55" stroke-width="3"/>']
    for k in range(1, 6):
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r*k/6:.0f}" ry="{r}" fill="none" stroke="#5EEAD4" stroke-opacity=".28" stroke-width="2"/>')
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*k/6:.0f}" fill="none" stroke="#5EEAD4" stroke-opacity=".22" stroke-width="2"/>')
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r*1.5:.0f}" ry="{r*.42:.0f}" fill="none" stroke="#F59E0B" stroke-opacity=".55" stroke-width="3" transform="rotate(-18 {cx} {cy})"/>')
    return ''.join(out)


def chart(x, y):
    """Translucent hologram bar and line chart (decorative, no values)."""
    out = [f'<rect x="{x}" y="{y}" width="620" height="360" rx="18" fill="#0E2238" fill-opacity=".45" stroke="#5EEAD4" stroke-opacity=".45" stroke-width="3"/>']
    for k, hgt in enumerate((90, 150, 120, 210, 170, 250, 230)):
        out.append(f'<rect x="{x+50+k*78}" y="{y+320-hgt}" width="44" height="{hgt}" rx="6" fill="#3B82F6" fill-opacity=".55"/>')
    pts = ' '.join(f'{x+72+k*78},{y+300-v}' for k, v in enumerate((60, 120, 90, 180, 150, 220, 260)))
    out.append(f'<polyline points="{pts}" fill="none" stroke="#5EEAD4" stroke-width="5" class="glow" style="color:#5EEAD4"/>')
    return ''.join(out)


def hexes():
    out = []
    r = 70
    for row in range(0, int(BAND/(r*1.5))+1):
        for col in range(0, int(WIDTH/(r*1.732))+2):
            cx = col*r*1.732+(r*.866 if row % 2 else 0)
            cy = 1300+row*r*1.5
            if cy > BAND:
                continue
            pts = ' '.join(f'{cx+r*.95*math.cos(a):.0f},{cy+r*.95*math.sin(a):.0f}' for a in (i*math.pi/3+math.pi/6 for i in range(6)))
            out.append(f'<polygon points="{pts}"/>')
    return f'<g fill="none" stroke="#3B82F6" stroke-opacity=".07" stroke-width="2">{"".join(out)}</g>'


def build():
    rng = random.Random(11)
    art = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="page" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#040A16"/><stop offset=".22" stop-color="#081529"/>
      <stop offset=".6" stop-color="#0B1B2E"/><stop offset="1" stop-color="#06101F"/>
    </linearGradient>
    <linearGradient id="tower" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12284A"/><stop offset="1" stop-color="#0A1830"/></linearGradient>
    <linearGradient id="mastFade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#040A16" stop-opacity=".82"/><stop offset=".55" stop-color="#040A16" stop-opacity=".62"/>
      <stop offset="1" stop-color="#040A16" stop-opacity=".25"/>
    </linearGradient>
    <radialGradient id="beam" cx=".5" cy=".42" r=".5"><stop offset="0" stop-color="#1D4ED8" stop-opacity=".45"/><stop offset="1" stop-color="#1D4ED8" stop-opacity="0"/></radialGradient>
    <radialGradient id="glowBand" cx=".5" cy="1" r=".6"><stop offset="0" stop-color="#5EEAD4" stop-opacity=".18"/><stop offset="1" stop-color="#5EEAD4" stop-opacity="0"/></radialGradient>
    <linearGradient id="aisleBg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#06101F" stop-opacity="0"/><stop offset=".18" stop-color="#050B17"/><stop offset="1" stop-color="#03070F"/></linearGradient>
    <linearGradient id="rackFace" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1A3253"/><stop offset="1" stop-color="#0C1A2E"/></linearGradient>
    <radialGradient id="emblemGlow"><stop offset="0" stop-color="#3B82F6" stop-opacity=".55"/><stop offset="1" stop-color="#3B82F6" stop-opacity="0"/></radialGradient>
    <linearGradient id="shieldFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3B82F6"/><stop offset="1" stop-color="#0F766E"/></linearGradient>
    <pattern id="dots" width="60" height="60" patternUnits="userSpaceOnUse"><circle cx="30" cy="30" r="2.2" fill="#5EEAD4" fill-opacity=".10"/></pattern>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>
    <filter id="halo" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="16"/></filter>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#page)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dots)"/>
  <rect x="300" y="-400" width="3600" height="2000" fill="url(#beam)"/>
  {globe(3720, 420, 300)}{chart(170, 240)}
  {skyline(rng)}
  {hexes()}
  {bokeh(rng)}
  {circuits(rng)}
  <rect y="{BAND-300}" width="{WIDTH}" height="{HEIGHT-BAND+300}" fill="url(#glowBand)"/>
  {halos()}
  {aisle()}
</svg>'''
    page = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#040A16}}
.glow{{filter:drop-shadow(0 0 8px color-mix(in srgb,currentColor 60%,transparent)) drop-shadow(0 0 22px color-mix(in srgb,currentColor 35%,transparent))}}
.emblem{{font:800 100px "Microsoft JhengHei","Segoe UI",sans-serif;fill:#FFFFFF;filter:drop-shadow(0 0 18px #3B82F6)}}
.emblemSub{{font:700 44px "Microsoft JhengHei","Segoe UI",sans-serif;fill:#5EEAD4;letter-spacing:6px}}
.device{{font:800 44px "Segoe UI",sans-serif;fill:#E2E8F0;letter-spacing:4px}}
.slab{{font:700 34px "Microsoft JhengHei","Segoe UI",sans-serif;fill:#CBD5E1;letter-spacing:3px}}
</style></head><body>{art}</body></html>'''
    with tempfile.TemporaryDirectory() as folder:
        html = Path(folder) / 'art.html'
        html.write_text(page, encoding='utf-8')
        subprocess.run([browser(), '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        f'--window-size={WIDTH},{HEIGHT}', f'--screenshot={OUT / "poster-background.png"}', html.as_uri()],
                       check=True, capture_output=True)
    print('poster-background.png', WIDTH, HEIGHT)


if __name__ == '__main__':
    build()
