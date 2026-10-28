"""Set native East Asian/Latin font slots without losing XML namespaces."""
import argparse
import json
from pathlib import Path
import zipfile
from style_contract import TYPOGRAPHY, THEME
from lxml import etree as ET

A="http://schemas.openxmlformats.org/drawingml/2006/main"
NS={"a":A}
PALETTE = json.loads((Path(__file__).resolve().parents[2]/'design-system/palette.json').read_text(encoding='utf-8'))

def normalize(source,target,slide_size_emu=None):
    if Path(source).resolve()==Path(target).resolve():
        raise ValueError("Keep the original exporter output; choose a distinct delivery path")
    changed=0
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as delivery:
        for info in original.infolist():
            content=original.read(info.filename)
            if info.filename.endswith(".xml") and info.filename.startswith("ppt/"):
                root=ET.fromstring(content)
                if info.filename == 'ppt/presentation.xml' and slide_size_emu:
                    size = root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz')
                    size.set('cx',str(slide_size_emu[0]))
                    size.set('cy',str(slide_size_emu[1]))
                for node in root.xpath("//a:rPr | //a:defRPr | //a:endParaRPr | //a:majorFont | //a:minorFont",namespaces=NS):
                    for kind,font in [("latin",TYPOGRAPHY['latin']),("ea",TYPOGRAPHY['cjk']),("cs",TYPOGRAPHY['latin'])]:
                        child=node.find("{"+A+"}"+kind)
                        if child is None:child=ET.SubElement(node,"{"+A+"}"+kind)
                        child.set("typeface",font)
                    changed+=1
                for node in root.xpath('//*[@typeface]'):
                    kind = ET.QName(node).localname
                    cjk = kind == 'ea' or (kind == 'font' and node.get('script') in {'Hans', 'Hant', 'Hani', 'Bopo'})
                    node.set('typeface', TYPOGRAPHY['cjk'] if cjk else TYPOGRAPHY['latin'])
                for scheme in root.xpath('//a:clrScheme', namespaces=NS):
                    scheme.set('name', 'AI Security Navy Blue Gold')
                    for node in scheme:
                        role = THEME.get(ET.QName(node).localname)
                        if role:
                            for old in list(node):node.remove(old)
                            ET.SubElement(node, '{'+A+'}srgbClr', val=PALETTE[role].lstrip('#'))
                content=ET.tostring(root,encoding="UTF-8",xml_declaration=True,standalone=True)
            if info.filename=="docProps/core.xml":
                root=ET.fromstring(content)
                for node in root:
                    if node.tag.rsplit("}",1)[-1] in {"creator","lastModifiedBy"}:node.text=""
                content=ET.tostring(root,encoding="UTF-8",xml_declaration=True,standalone=True)
            delivery.writestr(info,content)
    print("Normalized native font properties:",changed)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("source");parser.add_argument("target")
    parser.add_argument('--a2',action='store_true',help='Restore exact 420 x 594 mm size after Office rounding')
    args=parser.parse_args();normalize(args.source,args.target,(420*36000,594*36000) if args.a2 else None)
