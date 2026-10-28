"""Set native East Asian/Latin font slots without losing XML namespaces."""
import argparse
from pathlib import Path
import zipfile
from lxml import etree as ET

A="http://schemas.openxmlformats.org/drawingml/2006/main"
NS={"a":A}

def normalize(source,target):
    if Path(source).resolve()==Path(target).resolve():
        raise ValueError("Keep the original exporter output; choose a distinct delivery path")
    changed=0
    with zipfile.ZipFile(source) as original,zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as delivery:
        for info in original.infolist():
            content=original.read(info.filename)
            if info.filename.endswith(".xml") and info.filename.startswith(("ppt/slides/","ppt/notesSlides/","ppt/slideMasters/","ppt/notesMasters/","ppt/theme/")):
                root=ET.fromstring(content)
                for node in root.xpath("//a:rPr | //a:defRPr | //a:endParaRPr | //a:majorFont | //a:minorFont",namespaces=NS):
                    for kind,font in [("latin","Times New Roman"),("ea","DFKai-SB"),("cs","Times New Roman")]:
                        child=node.find("{"+A+"}"+kind)
                        if child is None:child=ET.SubElement(node,"{"+A+"}"+kind)
                        child.set("typeface",font)
                    changed+=1
                content=ET.tostring(root,encoding="UTF-8",xml_declaration=True,standalone=True)
            delivery.writestr(info,content)
    print("Normalized native font properties:",changed)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("source");parser.add_argument("target")
    args=parser.parse_args();normalize(args.source,args.target)
