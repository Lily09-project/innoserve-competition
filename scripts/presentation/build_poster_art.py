"""Draw the poster's decorative footer art: a network switch and glowing threat panels.

Original vector artwork in a light lab style that continues the poster's pale masthead; it
carries no data. The panels name the attack families of the six isolated TCP scenarios and
end on the controlled response. Switch and panels sit on the poster's 3-column grid
(switch in column 1, panels across columns 2-3). Rendered by headless Edge/Chrome so
Windows CJK fonts are used.
"""
from pathlib import Path
import subprocess
import tempfile

from capture_exhibit_frames import OUT, browser

WIDTH, HEIGHT = 4200, 700  # 10 px per mm for a 420 x 70 mm band
GRID = [240+k*1266.7 for k in range(3)]  # poster columns: 24 mm start, 118.67 mm + 8 mm pitch
COLUMN = 1186.7
PANEL_W, PANEL_GAP = 359.4, 60
PANELS = [
    ('#E5484D', 'DDoS 洪流', 'HTTP FLOOD', 'flood'),
    ('#F59E0B', 'SSH 暴力破解', 'AUTH ATTACK', 'key'),
    ('#0EA5A4', 'FTP 暴力破解', 'FILE SERVICE', 'folder'),
    ('#7C3AED', 'Web XSS', 'SCRIPT INJECTION', 'code'),
    ('#1D4ED8', 'Bot 殭屍網路', 'BOTNET C2', 'bot'),
    ('#0F766E', '受控回復', 'POLICY GATE', 'shield'),
]
ICONS = {
    'flood': '<path d="M20 60h90M20 90h110M20 120h90"/><path d="M100 45l25 15-25 15M120 75l25 15-25 15M100 105l25 15-25 15"/>'
             '<rect x="150" y="40" width="40" height="100" rx="6"/>',
    'key': '<circle cx="70" cy="90" r="34"/><circle cx="70" cy="90" r="10"/><path d="M104 90h86M160 90v26M182 90v18"/>',
    'folder': '<path d="M20 50h60l14 16h86v84H20z"/><rect x="88" y="94" width="44" height="36" rx="5"/><path d="M98 94v-12a12 12 0 0 1 24 0v12"/>',
    'code': '<rect x="20" y="40" width="160" height="110" rx="10"/><path d="M20 66h160"/><path d="M78 92l-22 18 22 18M122 92l22 18-22 18M108 86l-16 48"/>',
    'bot': '<rect x="45" y="60" width="110" height="80" rx="16"/><circle cx="78" cy="98" r="10"/><circle cx="122" cy="98" r="10"/>'
           '<path d="M100 60V38M80 124h40M45 100H28M155 100h17"/><circle cx="100" cy="32" r="7"/>',
    'shield': '<path d="M100 30l60 22v42c0 36-26 58-60 70-34-12-60-34-60-70V52z"/><path d="M74 96l18 18 36-38"/>',
}
TOP, PANEL_H = 150, 470


def panel(i, color, title, subtitle, icon):
    x = GRID[1]+i*(PANEL_W+PANEL_GAP)
    return f'''<g transform="translate({x:.1f} {TOP})">
  <rect width="{PANEL_W}" height="{PANEL_H}" rx="28" fill="#FFFFFF" fill-opacity=".86" stroke="{color}" stroke-width="5" class="glow" style="color:{color}"/>
  <rect x="14" y="14" width="{PANEL_W-28}" height="{PANEL_H-28}" rx="20" fill="{color}" fill-opacity=".05" stroke="{color}" stroke-opacity=".22" stroke-width="2"/>
  <circle cx="{PANEL_W/2}" cy="150" r="96" fill="{color}" fill-opacity=".08"/>
  <g transform="translate({PANEL_W/2-100} 58) scale(1)" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" class="soft" style="color:{color}">{ICONS[icon]}</g>
  <text x="{PANEL_W/2}" y="318" text-anchor="middle" class="title" fill="#0B1B2E">{title}</text>
  <text x="{PANEL_W/2}" y="372" text-anchor="middle" class="sub" fill="{color}">{subtitle}</text>
  <rect x="{PANEL_W/2-60}" y="410" width="120" height="6" rx="3" fill="{color}" fill-opacity=".75"/>
</g>'''


def switch():
    x0, w = GRID[0]+60, COLUMN-200
    ports = ''
    for k in range(24):
        col, row = k % 12, k//12
        px = x0+70+col*64+(col//6)*28
        py = 330+row*66
        led = '#0F766E' if k % 5 else '#F59E0B'
        ports += f'<rect x="{px}" y="{py}" width="48" height="46" rx="6" fill="#15233A" stroke="#8A9AB0" stroke-width="3"/><circle cx="{px+24}" cy="{py-9}" r="5" fill="{led}"/>'
    colors = ['#1D4ED8', '#0EA5A4', '#F59E0B', '#1D4ED8', '#0F766E', '#7C3AED', '#1D4ED8']
    cables = ''.join(f'<path d="M{x0+94+k*64} 422 C{x0+94+k*64} 560, {x0+40+k*95} 600, {x0-60+k*130} 760" fill="none" stroke="{c}" stroke-width="14" stroke-linecap="round" opacity=".85"/>'
                     for k, c in enumerate(colors))
    return f'''<g>
  <ellipse cx="{x0+w/2}" cy="560" rx="{w*.62}" ry="46" fill="#1D4ED8" fill-opacity=".10"/>
  <path d="M{x0} 260 L{x0+90} 196 L{x0+w+90} 196 L{x0+w} 260 Z" fill="#E8EEF6" stroke="#B8C4D4" stroke-width="3"/>
  <rect x="{x0}" y="260" width="{w}" height="210" rx="12" fill="#D5DEEA" stroke="#9AAAC0" stroke-width="4"/>
  <path d="M{x0+w} 260 L{x0+w+90} 196 L{x0+w+90} 406 L{x0+w} 470 Z" fill="#B8C5D6" stroke="#9AAAC0" stroke-width="3"/>
  <rect x="{x0+20}" y="282" width="30" height="166" rx="6" fill="#C2CDDB"/>
  {ports}
  <rect x="{x0+w-130}" y="316" width="96" height="40" rx="6" fill="#15233A" stroke="#1D4ED8" stroke-width="4"/>
  <rect x="{x0+w-130}" y="376" width="96" height="40" rx="6" fill="#15233A" stroke="#1D4ED8" stroke-width="4"/>
  <circle cx="{x0+w-82}" cy="440" r="8" fill="#0F766E" class="soft" style="color:#0F766E"/>
  {cables}
</g>'''


def build():
    floor = ''.join(f'<line x1="{2100+(k-24)*44}" y1="470" x2="{2100+(k-24)*230}" y2="700" stroke="#1D4ED8" stroke-opacity=".07" stroke-width="2"/>' for k in range(49))
    floor += ''.join(f'<line x1="0" y1="{y}" x2="{WIDTH}" y2="{y}" stroke="#1D4ED8" stroke-opacity=".07" stroke-width="2"/>' for y in (490, 520, 560, 615, 685))
    # A dotted data line runs from the switch through every panel, the exhibit's packet motif.
    flow_y = TOP+PANEL_H/2+40
    dots = ''.join(f'<circle cx="{x}" cy="{flow_y}" r="5" fill="#1D4ED8" fill-opacity=".35"/>' for x in range(int(GRID[0]+COLUMN-30), int(GRID[1]+6*(PANEL_W+PANEL_GAP)), 26))
    art = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset=".22" stop-color="#F3F6FA"/><stop offset="1" stop-color="#E3EBF7"/>
    </linearGradient>
    <radialGradient id="halo" cx=".6" cy=".6" r=".5"><stop offset="0" stop-color="#1D4ED8" stop-opacity=".10"/><stop offset="1" stop-color="#1D4ED8" stop-opacity="0"/></radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#halo)"/>
  {floor}
  {dots}
  {switch()}
  {''.join(panel(i, *p) for i, p in enumerate(PANELS))}
</svg>'''
    page = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#FFFFFF}}
.glow{{filter:drop-shadow(0 0 10px color-mix(in srgb,currentColor 55%,transparent)) drop-shadow(0 6px 22px color-mix(in srgb,currentColor 30%,transparent))}}
.soft{{filter:drop-shadow(0 0 8px color-mix(in srgb,currentColor 45%,transparent))}}
.title{{font:700 46px "Microsoft JhengHei","Segoe UI",sans-serif}}
.sub{{font:700 26px "Segoe UI",sans-serif;letter-spacing:2px}}
</style></head><body>{art}</body></html>'''
    with tempfile.TemporaryDirectory() as folder:
        html = Path(folder) / 'art.html'
        html.write_text(page, encoding='utf-8')
        subprocess.run([browser(), '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        f'--window-size={WIDTH},{HEIGHT}', f'--screenshot={OUT / "art-banner.png"}', html.as_uri()],
                       check=True, capture_output=True)
    print('art-banner.png', WIDTH, HEIGHT)


if __name__ == '__main__':
    build()
