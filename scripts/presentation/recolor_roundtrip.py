"""Apply shared colors to imported authoring paint, preserving native identity."""
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from style_contract import PALETTE, resolve_color


def recolor(workspace):
    changes = []
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    for path in sorted((Path(workspace) / 'authoring-svg-flat').glob('slide_*.svg')):
        if path.stem == 'slide_02':
            continue  # The approved media timing wrapper is restored, then re-embedded.
        tree = ET.parse(path)
        parents = {node: parent for parent in tree.iter() for node in parent}
        count = 0
        for node in tree.iter():
            for key in ('fill', 'stroke', 'stop-color', 'flood-color', 'style'):
                value = node.get(key)
                if not value:
                    continue
                updated = re.sub(r'#[0-9a-fA-F]{6}\b', lambda m: resolve_color(m[0]), value)
                parent = parents.get(node)
                frame = parent.get('data-pptx-frame', '') if parent is not None else ''
                numbers = frame.split()
                if key == 'fill' and len(numbers) == 4:
                    _, _, width, height = map(float, numbers)
                    if value.upper() == '#FDB338' and width > 200 and height > 15:
                        updated = PALETTE['teal']  # Main-method chart bar, not warm signal.
                    if value.upper() == '#FFF4DD' and width > 600 and height > 30:
                        updated = PALETTE['teal_tint']  # Event-chain summary band.
                if updated != value:
                    node.set(key, updated)
                    if parent is tree.getroot() and node.tag.endswith('}rect') and not node.get('id'):
                        node.set('id', 'page-background')
                    count += 1
        if count:
            tree.write(path, encoding='utf-8', xml_declaration=True)
        changes.append({'page': path.stem, 'paint_changes': count})
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    print(json.dumps(recolor(args.workspace)))
