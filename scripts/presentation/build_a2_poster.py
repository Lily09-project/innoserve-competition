"""Build the A2 poster from the team's finished poster image.

The team designed the poster as one image (deliverables/source/poster/ai-poster.png). This
places it full-bleed on a single A2 portrait slide, so the delivery keeps the same PPTX / PDF /
preview set as before. The image's text is part of the artwork and is not editable here.
"""
from pathlib import Path
import sys

from pptx import Presentation
from pptx.util import Mm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from finalize_delivery import normalize

IMAGE = ROOT / 'deliverables/source/poster/ai-poster.png'


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
