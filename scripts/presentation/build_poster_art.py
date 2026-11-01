"""Turn the team's AI-generated poster artwork into a text-free backdrop for the A2 poster.

The source (deliverables/source/poster/ai-poster-source.png) was produced with an image
generator from this poster's layout. Generated text is unreliable — misspelt characters, wrong
numbers, skewed lines — so every region that carried text is blurred and darkened here, and
the poster sets the real title, data and stage panels on top as native objects. What stays
sharp is pure imagery: the hero scene with the presenters and hologram shield, the side
racks and the isometric footer scene.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/source/poster'
SOURCE = OUT / 'ai-poster-source.png'
WIDTH, HEIGHT = 4200, 5940  # A2 portrait at 10 px per mm
# Text regions in mm (x0, y0, x1, y1) with an edge feather in px: masthead lettering, the whole
# content area whose generated panels and figures the native cards replace, and the footnote
# line just above the footer scene.
TEXT_REGIONS = [((0, 0, 420, 86), 60), ((10, 160, 410, 512), 60), ((40, 509, 380, 525), 25)]


def mask_for(region, feather):
    x0, y0, x1, y1 = region
    mask = Image.new('L', (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(mask).rectangle((x0*10, y0*10, x1*10, y1*10), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather))


def build():
    art = Image.open(SOURCE).convert('RGB').resize((WIDTH, HEIGHT), Image.LANCZOS)
    # Unreadable stand-in: a heavy blur keeps the glow and colour, a darkening keeps text legible.
    hidden = ImageEnhance.Brightness(art.filter(ImageFilter.GaussianBlur(42))).enhance(.55)
    for region, feather in TEXT_REGIONS:
        art = Image.composite(hidden, art, mask_for(region, feather))
    art.save(OUT / 'poster-background.png', optimize=True)
    print('poster-background.png', WIDTH, HEIGHT)


if __name__ == '__main__':
    build()
