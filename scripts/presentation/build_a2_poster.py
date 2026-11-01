"""Wrap the A2 poster PNG in the PPTX that the recorded release bindings expect.

The poster is the team's finished image, deliverables/決賽海報_AI資安框架_A2.png. Release bindings
(scripts/release_inventory.py, part of the recorded code revision) still list the poster
PPTX, PDF and preview, so this places the PNG full-bleed on one A2 slide; those files carry
no other content. Use the PNG itself for viewing and printing.
"""
from pathlib import Path
import sys

from pptx import Presentation
from pptx.util import Mm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from finalize_delivery import normalize

IMAGE = ROOT / 'deliverables/決賽海報_AI資安框架_A2.png'


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Mm(420), Mm(594)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    for key in ('author', 'last_modified_by'):
        setattr(prs.core_properties, key, '')
    prs.core_properties.title = 'AI資安框架｜A2海報'
    picture = slide.shapes.add_picture(str(IMAGE), 0, 0, width=Mm(420), height=Mm(594))
    picture.name = 'PosterImage_A2'
    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
