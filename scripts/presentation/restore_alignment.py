"""Restore measured alignment targets after a paint-only native round trip."""
import argparse
from pathlib import Path
import posixpath
import re
import zipfile
from lxml import etree as ET

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'p': P, 'a': A}


def restore(source, reference, output):
    if Path(output).resolve() in {Path(source).resolve(), Path(reference).resolve()}:
        raise ValueError('preserve_roundtrip_and_reference')
    with zipfile.ZipFile(source) as current, zipfile.ZipFile(reference) as approved:
        parts = {name: current.read(name) for name in current.namelist()}
        removable = {name for name in parts if name.startswith('ppt/tags/') and name.endswith('.xml')
                     and all(n.get('name') == 'ALIGNMENT_TARGET_X' for n in ET.fromstring(parts[name]))}
        types = ET.fromstring(parts['[Content_Types].xml'])
        for item in list(types):
            if item.get('PartName', '').lstrip('/') in removable:
                types.remove(item)
        for name in removable:
            del parts[name]
        restored = 0
        slides = sorted(n for n in parts if re.fullmatch(r'ppt/slides/slide\d+\.xml', n))
        for name in slides:
            root = ET.fromstring(parts[name])
            old = ET.fromstring(approved.read(name))
            relpath = 'ppt/slides/_rels/' + Path(name).name + '.rels'
            rels = ET.fromstring(parts[relpath])
            oldrels = {r.get('Id'): r.get('Target') for r in ET.fromstring(approved.read(relpath))}
            oldshapes = {s.find('p:nvSpPr/p:cNvPr', NS).get('id'): s for s in old.findall('.//p:sp', NS)}
            for rel in list(rels):
                target = posixpath.normpath(posixpath.join('ppt/slides', rel.get('Target', '')))
                if target in removable:
                    rels.remove(rel)
            for shape in root.findall('.//p:sp', NS):
                text = ''.join(shape.xpath('.//a:t/text()', namespaces=NS))
                if not text:
                    continue
                ident = shape.find('p:nvSpPr/p:cNvPr', NS).get('id')
                original = oldshapes.get(ident)
                if original is None or re.sub(r'\s+', '', text) != re.sub(r'\s+', '', ''.join(original.xpath('.//a:t/text()', namespaces=NS))):
                    raise ValueError('text_identity_changed_not_paint_only')
                tag = original.find('.//p:tags', NS)
                if tag is None:
                    raise ValueError('reference_lacks_measured_alignment')
                oldpath = posixpath.normpath(posixpath.join('ppt/slides', oldrels[tag.get('{' + R + '}id')]))
                data = ET.fromstring(approved.read(oldpath))
                if len(data) != 1 or data[0].get('name') != 'ALIGNMENT_TARGET_X':
                    raise ValueError('reference_has_other_custom_tags')
                tagname = 'ppt/tags/alignment_' + Path(name).stem + '_' + ident + '.xml'
                parts[tagname] = ET.tostring(data, encoding='utf-8', xml_declaration=True, standalone=True)
                rid = 'rIdAlignment' + ident
                if any(r.get('Id') == rid for r in rels):
                    raise ValueError('alignment_relationship_collision')
                ET.SubElement(rels, '{' + REL + '}Relationship', Id=rid, Type=R + '/tags', Target='../tags/' + Path(tagname).name)
                ET.SubElement(types, '{' + CT + '}Override', PartName='/' + tagname, ContentType='application/vnd.openxmlformats-officedocument.presentationml.tags+xml')
                nv = shape.find('p:nvSpPr/p:nvPr', NS)
                for child in list(nv):
                    if child.tag == '{' + P + '}custDataLst':
                        nv.remove(child)
                custom = ET.SubElement(nv, '{' + P + '}custDataLst')
                ET.SubElement(custom, '{' + P + '}tags', attrib={'{' + R + '}id': rid})
                restored += 1
            parts[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True, standalone=True)
            parts[relpath] = ET.tostring(rels, encoding='utf-8', xml_declaration=True, standalone=True)
        parts['[Content_Types].xml'] = ET.tostring(types, encoding='utf-8', xml_declaration=True, standalone=True)
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, content in parts.items():
                archive.writestr(name, content)
    return restored


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('source', 'reference', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    print('Restored measured alignment targets:', restore(**vars(args)))
