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
# Seconds on the exhibit timeline, and the board region (CSS px of a 1920x1080 projector view).
FRAMES = {
    'overview': (38, (144, 206, 1776, 816)),
    'detect': (16, (149, 250, 826, 797)),
    'retrieve': (27.5, (826, 240, 1416, 787)),
    'audit': (31, (1255, 245, 1745, 553)),
    'act': (38, (1421, 432, 1766, 811)),
}
PANEL_ASPECT = 1.2
HOOK = """<script>
addEventListener('load', () => {
  const q = new URLSearchParams(location.search);
  setTimeout(() => {
    document.querySelector('[data-scenario="' + q.get('cap') + '"]').click();
    setTimeout(() => {
      const seek = document.getElementById('seek');
      seek.value = q.get('t');
      seek.dispatchEvent(new Event('input'));
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
        for seconds in sorted({t for t, _ in FRAMES.values()}):
            shot = Path(folder) / f'{seconds}.png'
            url = page.as_uri() + f'?present&cap={SCENARIO}&t={seconds}'
            subprocess.run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=5000',
                            '--window-size=1920,1080', f'--screenshot={shot}', url],
                           check=True, capture_output=True)
            shots[seconds] = Image.open(shot).convert('RGB')
        for name, (seconds, box) in FRAMES.items():
            frame = shots[seconds].crop(tuple(v*SCALE for v in box))
            if name != 'overview':
                frame = pad(frame, PANEL_ASPECT)
            frame.save(OUT / f'exhibit-{name}.png', optimize=True)
            print(f'exhibit-{name}.png', frame.size)


if __name__ == '__main__':
    capture()
