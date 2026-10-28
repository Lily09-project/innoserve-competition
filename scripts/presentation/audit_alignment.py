"""Audit measured text anchors and panel grids; draw explicit alignment guides."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / 'validation/alignment-20261029'
COLORS = {1: '#008050', 2: '#004FFF', 3: '#D62D20'}


def audit():
    report = {'tolerance_pt': .1, 'text_anchors': 0, 'grid_checks': 0, 'errors': [], 'pages': []}
    for kind in ('slides', 'poster'):
        pages = json.loads((FOLDER / f'{kind}.json').read_text(encoding='utf-8-sig'))
        for page in pages:
            number = page['page']
            image = (ROOT / f'validation/aligned-powerpoint-20261029/slide-{number:02d}.png'
                     if kind == 'slides' else ROOT / 'deliverables/figures/poster-a2-preview.png')
            canvas = Image.open(image).convert('RGB')
            draw = ImageDraw.Draw(canvas)
            sx, sy = canvas.width/page['width'], canvas.height/page['height']
            count = 0
            for shape in page['shapes']:
                if 'target_x' not in shape:
                    continue
                count += 1
                x, y, w, h = shape['bound']
                align = shape['align']
                actual = x+(w/2 if align == 2 else w if align == 3 else 0)
                delta = actual-shape['target_x']
                if abs(delta) > .1:
                    report['errors'].append({'media': kind, 'page': number, 'text': shape['text'], 'delta_pt': delta})
                if x < -.1 or y < -.1 or x+w > page['width']+.1 or y+h > page['height']+.1:
                    report['errors'].append({'media': kind, 'page': number, 'text': shape['text'], 'error': 'outside canvas'})
                color = COLORS[align]
                draw.rectangle((x*sx,y*sy,(x+w)*sx,(y+h)*sy),outline=color,width=1)
                anchor = shape['target_x']*sx
                draw.line((anchor,(y-3)*sy,anchor,(y+h+3)*sy),fill=color,width=2)
            # Same-size cards must share top/bottom edges and equal gutters.
            if kind == 'slides' and number in (6,9):
                unit = page['width']/1280
                y,h = (195,257) if number == 6 else (292,174)
                expected = [(64+i*294,y,270,h) for i in range(4)]
            elif kind == 'poster':
                unit = 72/25.4
                expected = [(x,y,184,91) for y in (145,253) for x in (16,220)]
            else:
                expected = []
            for box in expected:
                found = any(all(abs(shape[key]-value*unit)<.1 for key,value in zip(('x','y','w','h'),box)) for shape in page['shapes'])
                report['grid_checks'] += 1
                if not found:
                    report['errors'].append({'media':kind,'page':number,'missing_grid_box':box})
                x,y,w,h = (value*unit for value in box)
                draw.rectangle((x*sx,y*sy,(x+w)*sx,(y+h)*sy),outline='#B000B0',width=2)
                draw.line(((x+w/2)*sx,y*sy,(x+w/2)*sx,(y+h)*sy),fill='#B000B0',width=1)
            canvas.save(FOLDER / f'{kind}-{number:02d}-guides.png')
            report['text_anchors'] += count
            report['pages'].append({'media':kind,'page':number,'texts':count})
    (FOLDER / 'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key != 'pages'},ensure_ascii=True))
    if report['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    audit()
