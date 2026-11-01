"""Draw the poster's full-page background: a dark cinematic tech canvas and an isometric scene.

Original vector artwork in a night, neon-lit style; it carries no data. A glowing skyline
sits behind the masthead, bokeh and circuit traces fill the margins, every content card gets
a soft cyan halo, and the bottom scene tells the poster's story as floating isometric islands: attack traffic, a switch, the AI security framework (firewall,
AI chip and shield) and the protected servers, joined by packet flows — red packets stop at
the framework, green ones continue. Rendered by headless Edge/Chrome at 10 px per mm so
Windows CJK fonts are used for the island captions.
"""
from pathlib import Path
import math
import random
import subprocess
import tempfile

from capture_exhibit_frames import OUT, browser

WIDTH, HEIGHT = 4200, 5940  # A2 portrait at 10 px per mm
BAND = 5200                 # scene starts below the poster's last text line (520 mm)
NAVY, INK, BLUE, TEAL, GOLD, RED = '#0B1B2E', '#15233A', '#1D4ED8', '#0F766E', '#F59E0B', '#E5484D'
S = 54                      # isometric unit in px
C30, S30 = math.cos(math.pi/6), 0.5


def shade(hex_color, k):
    """Lighten (k > 0) or darken (k < 0) a colour by mixing with white or black."""
    r, g, b = (int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    t = 255 if k > 0 else 0
    k = abs(k)
    return '#%02X%02X%02X' % tuple(round(c+(t-c)*k) for c in (r, g, b))


class Iso:
    """Isometric drawing anchored so that point (cx, cy, 0) of the island lands on (sx, sy)."""

    def __init__(self, sx, sy, cx, cy):
        self.ox = sx-(cx-cy)*C30*S
        self.oy = sy-(cx+cy)*S30*S
        self.parts = []

    def p(self, x, y, z):
        return self.ox+(x-y)*C30*S, self.oy+(x+y)*S30*S-z*S

    def poly(self, points, fill, stroke='none', width=0, extra=''):
        d = ' '.join(f'{a:.1f},{b:.1f}' for a, b in (self.p(*q) for q in points))
        self.parts.append(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"{extra}/>')

    def line(self, a, b, color, width=2, opacity=1):
        (x1, y1), (x2, y2) = self.p(*a), self.p(*b)
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}" stroke-opacity="{opacity}" stroke-linecap="round"/>')

    def box(self, x, y, z, w, d, h, color, top=None):
        edge = shade(color, -.25)
        self.poly([(x, y+d, z), (x+w, y+d, z), (x+w, y+d, z+h), (x, y+d, z+h)], shade(color, -.08), edge, 1.5)
        self.poly([(x+w, y, z), (x+w, y+d, z), (x+w, y+d, z+h), (x+w, y, z+h)], shade(color, -.22), edge, 1.5)
        self.poly([(x, y, z+h), (x+w, y, z+h), (x+w, y+d, z+h), (x, y+d, z+h)], top or shade(color, .12), edge, 1.5)

    def platform(self, w, d):
        cx, cy = self.p(w/2, d/2, -1.4)
        self.parts.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{(w+d)*C30*S*.55:.0f}" ry="{(w+d)*S30*S*.32:.0f}" fill="#5EEAD4" fill-opacity=".16" filter="url(#blur)"/>')
        self.box(0, 0, -.55, w, d, .55, '#1B2F4A', '#14263E')
        for k in range(1, int(w)):
            self.line((k, 0, 0), (k, d, 0), '#5EEAD4', 1.2, .18)
        for k in range(1, int(d)):
            self.line((0, k, 0), (w, k, 0), '#5EEAD4', 1.2, .18)
        for a, b in (((0, 0, 0), (w, 0, 0)), ((w, 0, 0), (w, d, 0)), ((w, d, 0), (0, d, 0)), ((0, d, 0), (0, 0, 0))):
            (x1, y1), (x2, y2) = self.p(*a), self.p(*b)
            self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#5EEAD4" stroke-width="4" class="glow" style="color:#5EEAD4"/>')

    def svg(self):
        return ''.join(self.parts)


def laptop(g, x, y):
    g.box(x, y, 0, 1.5, 1.05, .12, '#64748B')
    g.poly([(x+.05, y, .12), (x+1.45, y, .12), (x+1.45, y, 1.15), (x+.05, y, 1.15)], INK, shade(INK, -.3), 1.5)
    g.poly([(x+.17, y, .25), (x+1.33, y, .25), (x+1.33, y, 1.03), (x+.17, y, 1.03)], shade(RED, -.15), extra=' class="glow" style="color:#E5484D"')
    g.line((x+.4, y, .75), (x+1.1, y, .55), '#FFFFFF', 3, .9)
    g.line((x+.4, y, .55), (x+1.1, y, .75), '#FFFFFF', 3, .9)


def cube(g, x, y, z, color, size=.38):
    g.box(x, y, z, size, size, size, color)


def switch(g, x, y):
    g.box(x, y, 0, 3.2, 1.3, .55, '#2B3B55')
    for k in range(10):
        t = x+.22+k*.29
        g.poly([(t, y+1.3, .14), (t+.2, y+1.3, .14), (t+.2, y+1.3, .36), (t, y+1.3, .36)], '#0A1626', '#7F90A8', 1)
        g.line((t+.1, y+1.3, .44), (t+.1, y+1.3, .46), TEAL if k % 4 else GOLD, 6)
    for k, h in enumerate((1.0, 1.25)):
        g.line((x+.5+k*2.2, y+.3, .55), (x+.5+k*2.2, y+.3, .55+h), '#64748B', 5)


def firewall(g, x, y):
    w, d, h = 3.4, .8, 1.7
    g.box(x, y, 0, w, d, h, '#F08A5D')
    for r in range(1, 5):
        z = h*r/5
        g.line((x, y+d, z), (x+w, y+d, z), '#FFFFFF', 2, .65)
        g.line((x+w, y, z), (x+w, y+d, z), '#FFFFFF', 2, .5)
    for r in range(5):
        for c in range(7):
            t = x+(c+(.5 if r % 2 else 0))*w/7
            if x < t < x+w:
                g.line((t, y+d, h*r/5), (t, y+d, h*(r+1)/5), '#FFFFFF', 2, .65)


def chip(g, x, y):
    g.box(x, y, 0, 1.7, 1.7, .4, INK, '#22324A')
    g.poly([(x+.4, y+.4, .4), (x+1.3, y+.4, .4), (x+1.3, y+1.3, .4), (x+.4, y+1.3, .4)], TEAL, extra=' class="glow" style="color:#0F766E"')
    for k in range(5):
        t = .2+k*.32
        g.line((x+t, y+1.7, .1), (x+t, y+2.0, .1), '#94A3B8', 3)
        g.line((x+1.7, y+t, .1), (x+2.0, y+t, .1), '#94A3B8', 3)


def rack(g, x, y, h):
    g.box(x, y, 0, 1.05, 1.05, h, '#1E2C44', '#33445E')
    for k in range(int(h/.32)):
        z = .18+k*.32
        g.poly([(x+.1, y+1.05, z), (x+.95, y+1.05, z), (x+.95, y+1.05, z+.2), (x+.1, y+1.05, z+.2)], '#2E4060', '#4B5F80', 1)
        g.line((x+.82, y+1.05, z+.1), (x+.84, y+1.05, z+.1), '#2EE6A6', 7)


def shield(cx, cy, size):
    s = size/100
    return (f'<g transform="translate({cx-50*s:.1f} {cy-60*s:.1f}) scale({s:.3f})" class="glow" style="color:#1D4ED8">'
            '<path d="M50 0 L100 20 V58 C100 92 76 112 50 122 C24 112 0 92 0 58 V20 Z" fill="url(#shieldFill)" stroke="#FFFFFF" stroke-width="5"/>'
            '<path d="M28 60 L45 77 L74 44" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></g>')


def caption(x, y, text):
    return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" class="cap">{text}</text>'


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


def scene():
    out = []
    base = BAND+365
    # Islands, left to right: attack traffic, switch, framework, protected servers.
    a = Iso(640, base, 2.2, 2.0)
    a.platform(4.4, 4.0)
    for i, (x, y) in enumerate(((.4, .4), (2.5, .5), (1.4, 2.4))):
        laptop(a, x, y)
    cube(a, 3.3, 2.7, 1.4, RED)
    cube(a, .6, 2.9, 1.8, RED)
    b = Iso(1500, base+10, 1.9, 1.6)
    b.platform(3.8, 3.2)
    switch(b, .3, .9)
    c = Iso(2420, base+20, 3.0, 2.6)
    c.platform(6.0, 5.2)
    chip(c, 3.6, 2.6)
    firewall(c, .5, .6)
    cube(c, .9, 3.6, 0, RED)
    cube(c, 1.6, 4.1, 0, RED, .3)
    d = Iso(3420, base+10, 2.3, 2.0)
    d.platform(4.6, 4.0)
    for i, h in enumerate((2.6, 3.1, 2.3)):
        rack(d, .5+i*1.3, .6, h)
    cube(d, 3.4, 3.1, 0, '#2EE6A6', .34)
    # Packet flows between islands (screen space), red into the framework, green out of it.
    flows = [((900, base-60), (1290, base-90), RED), ((1700, base-90), (2140, base-150), RED),
             ((2700, base-150), (3160, base-120), '#10B981')]
    for (x1, y1), (x2, y2), color in flows:
        mx, my = (x1+x2)/2, min(y1, y2)-120
        out.append(f'<path d="M{x1} {y1} Q{mx} {my} {x2} {y2}" fill="none" stroke="{color}" stroke-width="6" stroke-dasharray="4 18" stroke-linecap="round" class="glow" style="color:{color}"/>')
        for k in (.3, .55, .8):
            px = (1-k)**2*x1+2*(1-k)*k*mx+k*k*x2
            py = (1-k)**2*y1+2*(1-k)*k*my+k*k*y2
            out.append(f'<rect x="{px-11:.0f}" y="{py-11:.0f}" width="22" height="22" rx="5" fill="{color}" class="glow" style="color:{color}"/>')
    out += [a.svg(), b.svg(), c.svg(), d.svg()]
    # Hologram ring and shield above the framework island.
    rx, ry = c.p(4.45, 3.45, .45)
    out.append(f'<ellipse cx="{rx:.0f}" cy="{ry:.0f}" rx="150" ry="86" fill="none" stroke="#14B8A6" stroke-width="5" stroke-dasharray="14 10" class="glow" style="color:#14B8A6"/>')
    sx, sy = c.p(3.0, 2.6, 4.1)
    out.append(f'<line x1="{rx:.0f}" y1="{ry:.0f}" x2="{sx:.0f}" y2="{sy+60:.0f}" stroke="#60A5FA" stroke-width="3" stroke-dasharray="6 8" stroke-opacity=".6"/>')
    out.append(shield(sx, sy, 190))
    # A blocked mark where the red flow meets the firewall.
    bx, by = 2150, base-150
    out.append(f'<g transform="translate({bx:.0f} {by:.0f})" class="glow" style="color:#E5484D"><circle r="34" fill="#FFFFFF" stroke="#E5484D" stroke-width="6"/>'
               '<path d="M-14 -14L14 14M14 -14L-14 14" stroke="#E5484D" stroke-width="8" stroke-linecap="round"/></g>')
    cy = BAND+598
    out += [caption(640, cy, '攻擊流量'), caption(1500, cy, '交換器'), caption(2420, cy, 'AI 資安框架'), caption(3420, cy, '受保護服務')]
    return ''.join(out)


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
      <stop offset="0" stop-color="#040A16" stop-opacity=".96"/><stop offset=".55" stop-color="#040A16" stop-opacity=".78"/>
      <stop offset="1" stop-color="#040A16" stop-opacity=".25"/>
    </linearGradient>
    <radialGradient id="beam" cx=".5" cy=".42" r=".5"><stop offset="0" stop-color="#1D4ED8" stop-opacity=".45"/><stop offset="1" stop-color="#1D4ED8" stop-opacity="0"/></radialGradient>
    <radialGradient id="glowBand" cx=".5" cy="1" r=".6"><stop offset="0" stop-color="#5EEAD4" stop-opacity=".18"/><stop offset="1" stop-color="#5EEAD4" stop-opacity="0"/></radialGradient>
    <linearGradient id="shieldFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3B82F6"/><stop offset="1" stop-color="#0F766E"/></linearGradient>
    <pattern id="dots" width="60" height="60" patternUnits="userSpaceOnUse"><circle cx="30" cy="30" r="2.2" fill="#5EEAD4" fill-opacity=".10"/></pattern>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>
    <filter id="halo" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="16"/></filter>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#page)"/>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#dots)"/>
  <rect x="300" y="-400" width="3600" height="2000" fill="url(#beam)"/>
  {skyline(rng)}
  {bokeh(rng)}
  {circuits(rng)}
  <rect y="{BAND-300}" width="{WIDTH}" height="{HEIGHT-BAND+300}" fill="url(#glowBand)"/>
  {halos()}
  {scene()}
</svg>'''
    page = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#040A16}}
.glow{{filter:drop-shadow(0 0 8px color-mix(in srgb,currentColor 60%,transparent)) drop-shadow(0 0 22px color-mix(in srgb,currentColor 35%,transparent))}}
.cap{{font:700 40px "Microsoft JhengHei","Segoe UI",sans-serif;fill:#E2E8F0;letter-spacing:2px}}
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
