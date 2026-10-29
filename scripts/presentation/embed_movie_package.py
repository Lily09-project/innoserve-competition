"""Embed the film by preserving the approved slide-2 media playback wrapper."""
import argparse
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'


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
        for row in refs:
            kind=row.attrib['Type'].rsplit('/',1)[-1]
            if kind in ('video','media'):row.set('Target','../media/opening-film.mp4')
            elif kind=='image':row.set('Target','../media/opening-poster.png')
            elif kind=='slideLayout':row.set('Target',layout)
            elif kind!='notesSlide':raise ValueError('Unexpected approved media relationship: '+kind)
            if row.get('TargetMode')=='External':raise ValueError('Media must be fully embedded')
        types=ET.fromstring(current.read('[Content_Types].xml'))
        for extension,kind in (('mp4','video/mp4'),('png','image/png')):
            if not any(row.get('Extension')==extension for row in types):
                ET.SubElement(types,'{'+CT+'}Default',Extension=extension,ContentType=kind)
        replaced={slide:approved.read(slide),relationships:ET.tostring(refs,encoding='utf-8',xml_declaration=True),
                  '[Content_Types].xml':ET.tostring(types,encoding='utf-8',xml_declaration=True)}
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as result:
            for info in current.infolist():
                if (info.filename.startswith('ppt/media/') and info.filename.lower().endswith('.mp4')) or info.filename=='ppt/media/opening-poster.png':
                    continue
                result.writestr(info,replaced.get(info.filename,current.read(info.filename)))
            result.writestr('ppt/media/opening-film.mp4',Path(movie).read_bytes())
            result.writestr('ppt/media/opening-poster.png',Path(poster).read_bytes())
    print('Slide 2: embedded film and poster; approved media timing retained; no slideshow launched')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for key in ('source','reference','movie','poster','output'):parser.add_argument('--'+key,type=Path,required=True)
    embed(**vars(parser.parse_args()))
