"""Embed the film by preserving the approved slide-2 media playback wrapper.

The approved wrapper keeps the verified media timing. The native slide-2 header and footer
(kicker, one-line title, page number) are carried over from the freshly built deck, and the film
is placed at FILM_FRAME between them, so the slide reads 「影片展示」 like the other pages.
"""
import argparse
import copy
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

from lxml import etree

REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
R_ID = '{%s}id' % NS['r']
EMU = 12192000 // 1280                  # EMU per authoring pixel on the 1280x720 canvas
FILM_FRAME = (160, 114, 960, 540)       # x, y, width, height in authoring pixels (16:9)
CARRIED = ('headline', 'footer')        # native groups kept on the film slide


def carry_native(native_slide, native_rels, approved_slide, refs):
    """Copy the native header/footer groups and background onto the approved film slide."""
    tree = approved_slide.find('p:cSld/p:spTree', NS)
    for group in tree.findall('p:grpSp', NS):
        if group.find('p:nvGrpSpPr/p:cNvPr', NS).get('name') in CARRIED:
            tree.remove(group)
    kept = {}
    tags = {row.get('Id'): row.get('Target') for row in native_rels if row.get('Type').endswith('/tags')}
    insert_at = 2
    for group in native_slide.findall('p:cSld/p:spTree/p:grpSp', NS):
        if group.find('p:nvGrpSpPr/p:cNvPr', NS).get('name') not in CARRIED:
            continue
        group = copy.deepcopy(group)
        for node in group.iter():
            old = node.get(R_ID)
            if old in tags:
                kept.setdefault(old, f'rIdCarried{len(kept) + 1}')
                node.set(R_ID, kept[old])
        tree.insert(insert_at, group)
        insert_at += 1
    for old, new in kept.items():
        ET.SubElement(refs, '{%s}Relationship' % REL, Id=new, Target=tags[old],
                      Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/tags')
    background = native_slide.find('p:cSld/p:bg', NS)
    if background is not None:
        csld = approved_slide.find('p:cSld', NS)
        for old in csld.findall('p:bg', NS):
            csld.remove(old)
        csld.insert(0, copy.deepcopy(background))
    for picture in tree.iter('{%s}pic' % NS['p']):
        if picture.find('p:nvPicPr/p:cNvPr', NS).get('name') == 'OpeningFilm_30s_Embedded':
            frame = picture.find('p:spPr/a:xfrm', NS)
            x, y, w, h = (value * EMU for value in FILM_FRAME)
            frame.find('a:off', NS).attrib.update({'x': str(x), 'y': str(y)})
            frame.find('a:ext', NS).attrib.update({'cx': str(w), 'cy': str(h)})
    return {'ppt/' + target.replace('../', '', 1) for old, target in tags.items() if old in kept}


def embed(source, reference, movie, poster, output):
    if Path(source).resolve() == Path(output).resolve():
        raise ValueError('Preserve the source deck; choose another output')
    slide='ppt/slides/slide2.xml'
    relationships='ppt/slides/_rels/slide2.xml.rels'
    with zipfile.ZipFile(source) as current, zipfile.ZipFile(reference) as approved:
        for name in current.namelist():
            if name.endswith('.rels') and name != relationships:
                if any(row.get('Target','').lower().endswith('.mp4') for row in ET.fromstring(current.read(name))):
                    raise ValueError('Another slide references video; preserve it explicitly before replacing slide 2')
        refs=ET.fromstring(approved.read(relationships))
        native=ET.fromstring(current.read(relationships))
        layout=next(row.attrib['Target'] for row in native if row.attrib['Type'].endswith('/slideLayout'))
        for row in list(refs):
            kind=row.attrib['Type'].rsplit('/',1)[-1]
            if kind in ('video','media'):row.set('Target','../media/opening-film.mp4')
            elif kind=='image':row.set('Target','../media/opening-poster.png')
            elif kind=='slideLayout':row.set('Target',layout)
            elif kind=='tags':refs.remove(row)  # header tags from an earlier carry; replaced below
            elif kind!='notesSlide':raise ValueError('Unexpected approved media relationship: '+kind)
            if row.get('TargetMode')=='External':raise ValueError('Media must be fully embedded')
        approved_slide=etree.fromstring(approved.read(slide))
        used=carry_native(etree.fromstring(current.read(slide)),native,approved_slide,refs)
        # Tags of the replaced static slide-2 text would otherwise remain as orphan parts.
        orphans={'ppt/'+row.attrib['Target'].replace('../','',1) for row in native if row.attrib['Type'].endswith('/tags')}-used
        types=ET.fromstring(current.read('[Content_Types].xml'))
        for row in [row for row in types if row.get('PartName','').lstrip('/') in orphans]:types.remove(row)
        for extension,kind in (('mp4','video/mp4'),('png','image/png')):
            if not any(row.get('Extension')==extension for row in types):
                ET.SubElement(types,'{'+CT+'}Default',Extension=extension,ContentType=kind)
        replaced={slide:etree.tostring(approved_slide,xml_declaration=True,encoding='UTF-8',standalone=True),
                  relationships:ET.tostring(refs,encoding='utf-8',xml_declaration=True),
                  '[Content_Types].xml':ET.tostring(types,encoding='utf-8',xml_declaration=True)}
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as result:
            for info in current.infolist():
                if (info.filename.startswith('ppt/media/') and info.filename.lower().endswith('.mp4')) or info.filename in orphans or info.filename=='ppt/media/opening-poster.png':
                    continue
                result.writestr(info,replaced.get(info.filename,current.read(info.filename)))
            result.writestr('ppt/media/opening-film.mp4',Path(movie).read_bytes())
            result.writestr('ppt/media/opening-poster.png',Path(poster).read_bytes())
    print('Slide 2: embedded film and poster; header, footer and approved media timing retained; no slideshow launched')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('source','reference','movie','poster','output'):parser.add_argument('--'+key,type=Path,required=True)
    embed(**vars(parser.parse_args()))
