"""Capture the HTTP-flood run of the interactive exhibit as poster frames.

Each frame is the exhibit itself, paused at a recorded point of its 38-second timeline and
rendered by a headless Edge/Chrome; nothing is redrawn. The exhibit runs on synthetic packets
with demonstration outputs, so the poster labels these frames as display captures.
"""
from pathlib import Path
import os
import subprocess
import tempfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
EXHIBIT = ROOT / 'deliverables/interactive/AI資安框架_自動循環展示.html'
OUT = ROOT / 'deliverables/source/poster'
SCENARIO = 'ddos'
SCALE = 2
# Seconds on the exhibit timeline, the view, and the regions stacked into one panel (CSS px).
# 'present' is the 1920x1080 projector board; a tab name opens that inspector tab in a
# 1440x2300 page. The output panel skips the policy tab's raw action identifier line.
FRAMES = {
    'input': (38, 'traffic', [(50, 1530, 707, 2005)]),
    'detect': (16, 'present', [(149, 250, 826, 797)]),
    'retrieve': (27.5, 'present', [(826, 240, 1416, 787)]),
    'audit': (31, 'present', [(1255, 245, 1745, 553)]),
    'act': (38, 'present', [(1421, 432, 1766, 811)]),
    'output': (38, 'policy', [(728, 1522, 1385, 1702), (50, 1664, 707, 1857)]),
}
WINDOWS = {'present': (1920, 1080)}
PANEL_ASPECT = 115.67/80
HOOK = """<script>
addEventListener('load', () => {
  const q = new URLSearchParams(location.search);
  setTimeout(() => {
    document.querySelector('[data-scenario="' + q.get('cap') + '"]').click();
    setTimeout(() => {
      const seek = document.getElementById('seek');
      seek.value = q.get('t');
      seek.dispatchEvent(new Event('input'));
      if (q.get('tab')) setTimeout(() => document.querySelector('[data-tab="' + q.get('tab') + '"]').click(), 300);
    }, 400);
  }, 400);
});
</script>"""


def browser():
    candidates = [os.environ.get('EXHIBIT_BROWSER', ''),
                  r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                  r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                  r'C:\Program Files\Google\Chrome\Application\chrome.exe']
    found = next((c for c in candidates if c and Path(c).exists()), None)
    if not found:
        raise SystemExit('Edge or Chrome not found; set EXHIBIT_BROWSER.')
    return found


def pad(image, aspect):
    """Extend with the board's white canvas so every panel shares one aspect ratio."""
    w, h = image.size
    width, height = (round(h*aspect), h) if w/h < aspect else (w, round(w/aspect))
    canvas = Image.new('RGB', (width, height), 'white')
    canvas.paste(image, ((width-w)//2, (height-h)//2))
    return canvas


def capture():
    OUT.mkdir(parents=True, exist_ok=True)
    exe = browser()
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / 'exhibit.html'
        page.write_text(EXHIBIT.read_text(encoding='utf-8').replace('</body>', HOOK+'</body>'), encoding='utf-8')
        shots = {}
        for seconds, view in sorted({(t, v) for t, v, _ in FRAMES.values()}):
            shot = Path(folder) / f'{seconds}-{view}.png'
            query = 'present' if view == 'present' else f'tab={view}'
            width, height = WINDOWS.get(view, (1440, 2300))
            url = page.as_uri() + f'?{query}&cap={SCENARIO}&t={seconds}'
            subprocess.run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=6000',
                            f'--window-size={width},{height}', f'--screenshot={shot}', url],
                           check=True, capture_output=True)
            shots[seconds, view] = Image.open(shot).convert('RGB')
        for name, (seconds, view, boxes) in FRAMES.items():
            parts = [shots[seconds, view].crop(tuple(v*SCALE for v in box)) for box in boxes]
            gap = 16*SCALE
            frame = Image.new('RGB', (max(i.width for i in parts), sum(i.height for i in parts)+gap*(len(parts)-1)), 'white')
            y = 0
            for part in parts:
                frame.paste(part, (0, y))
                y += part.height+gap
            frame = pad(frame, PANEL_ASPECT)
            frame.save(OUT / f'exhibit-{name}.png', optimize=True)
            print(f'exhibit-{name}.png', frame.size)


if __name__ == '__main__':
    capture()
