"""Capture the HTTP-flood run of the interactive exhibit for the poster.

build_poster_panels.py crops the CTBM and PBCNN matrices from the detect frame, so the
poster shows the exhibit's own encoding.

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
SKIN = Path(__file__).with_name('exhibit_capture_dark.css')
SCENARIO = 'ddos'
SCALE = 2
# Seconds on the exhibit timeline, the view, and the regions stacked into one frame (CSS px).
# 'present' is the board fixed at 1920x768 (1.2x the 1600x640 diagram); a tab name would open
# that inspector tab in a 1440x1100 page showing only the inspector.
FRAMES = {
    'detect': (16, 'present', [(18, 70, 745, 710)]),
}
WINDOWS = {'present': (1920, 1080)}
PANEL_ASPECT = 115.67/80
HOOK = """<script>
addEventListener('load', () => {
  const q = new URLSearchParams(location.search);
  // Board views draw the 1600x640 diagram at exactly 1.2x in a fixed 1920x768 box, so crops
  // stay put however the page around the board is laid out.
  if (q.has('present')) document.head.insertAdjacentHTML('beforeend', '<style>' +
    '#diagramRegion{position:fixed!important;left:0!important;top:0!important;width:1920px!important;height:768px!important;' +
    'z-index:9999;overflow:hidden!important;padding:0!important;margin:0!important;border:0!important}' +
    '#board{width:1920px!important;height:768px!important;max-width:none!important}</style>');
  setTimeout(() => {
    document.querySelector('[data-scenario="' + q.get('cap') + '"]').click();
    setTimeout(() => {
      const seek = document.getElementById('seek');
      seek.value = q.get('t');
      seek.dispatchEvent(new Event('input'));
      if (q.get('tab')) setTimeout(() => {
        document.querySelector('[data-tab="' + q.get('tab') + '"]').click();
        // Only the inspector stays, pinned to the page top, so crops do not move with the layout above it.
        for (const el of document.querySelectorAll('main > *')) if (el.id !== 'inspector') el.style.display = 'none';
      }, 300);
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
    """Extend with the night canvas so every panel shares one aspect ratio."""
    w, h = image.size
    width, height = (round(h*aspect), h) if w/h < aspect else (w, round(w/aspect))
    canvas = Image.new('RGB', (width, height), '#06101F')
    canvas.paste(image, ((width-w)//2, (height-h)//2))
    return canvas


def capture():
    OUT.mkdir(parents=True, exist_ok=True)
    exe = browser()
    with tempfile.TemporaryDirectory() as folder:
        page = Path(folder) / 'exhibit.html'
        # The poster is dark, so frames are taken with a night skin; the exhibit file itself is untouched.
        skin = '<style>' + SKIN.read_text(encoding='utf-8') + '</style>'
        page.write_text(EXHIBIT.read_text(encoding='utf-8').replace('</head>', skin+'</head>').replace('</body>', HOOK+'</body>'), encoding='utf-8')
        shots = {}
        for seconds, view in sorted({(t, v) for t, v, _ in FRAMES.values()}):
            shot = Path(folder) / f'{seconds}-{view}.png'
            query = 'present' if view == 'present' else f'tab={view}'
            width, height = WINDOWS.get(view, (1440, 1100))
            url = page.as_uri() + f'?{query}&cap={SCENARIO}&t={seconds}'
            subprocess.run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            f'--force-device-scale-factor={SCALE}', '--virtual-time-budget=6000',
                            f'--window-size={width},{height}', f'--screenshot={shot}', url],
                           check=True, capture_output=True)
            shots[seconds, view] = Image.open(shot).convert('RGB')
        for name, (seconds, view, boxes) in FRAMES.items():
            parts = [shots[seconds, view].crop(tuple(v*SCALE for v in box)) for box in boxes]
            gap = 16*SCALE
            frame = Image.new('RGB', (max(i.width for i in parts), sum(i.height for i in parts)+gap*(len(parts)-1)), '#06101F')
            y = 0
            for part in parts:
                frame.paste(part, (0, y))
                y += part.height+gap
            frame = pad(frame, PANEL_ASPECT)
            frame.save(OUT / f'exhibit-{name}.png', optimize=True)
            print(f'exhibit-{name}.png', frame.size)


if __name__ == '__main__':
    capture()
