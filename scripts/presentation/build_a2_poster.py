"""Build an editable A2 methods poster from validated recorded aggregates."""
from pathlib import Path
import json
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Mm, Pt
from pptx.oxml.xmlchemy import OxmlElement

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_results import read_results, validate_results
from media_results import load_metrics
from finalize_delivery import normalize
from style_contract import font_runs

PALETTE = json.loads((ROOT/'design-system/palette.json').read_text(encoding='utf-8'))
BLUE, NAVY, GOLD = (PALETTE[key].lstrip('#') for key in ('blue', 'navy', 'gold'))
TEAL = PALETTE['teal'].lstrip('#')
INK = '171C1D'
MUTED = '53666E'
PALE = 'F0F2F3'
LINE = 'D6DDE0'


def build():
    data = validate_results(read_results())
    m = load_metrics(ROOT)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Mm(420), Mm(594)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string('FFFFFF')
    for key in ('author', 'last_modified_by'):
        setattr(prs.core_properties, key, '')
    prs.core_properties.title = 'AI資安框架｜A2方法海報'

    def shape(kind, x, y, w, h, fill, stroke=None):
        s = slide.shapes.add_shape(kind, Mm(x), Mm(y), Mm(w), Mm(h))
        if fill:
            s.fill.solid()
            s.fill.fore_color.rgb = RGBColor.from_string(fill)
        else:
            s.fill.background()
        if stroke:
            s.line.color.rgb = RGBColor.from_string(stroke)
            s.line.width = Pt(.8)
        else:
            s.line.fill.background()
        s._element.spPr.append(OxmlElement('a:effectLst'))
        return s

    def rect(x, y, w, h, fill=PALE, stroke=None):
        return shape(MSO_SHAPE.RECTANGLE, x, y, w, h, fill, stroke)

    def text(x, y, w, h, content, size=18, color=INK, bold=False, align=PP_ALIGN.CENTER):
        if color == BLUE and '%' in content and (content.startswith('Top-5') or content.replace('.', '').replace('%', '').isdigit()):
            color = TEAL
            if content.startswith('Top-5'):
                size = 32
        box = slide.shapes.add_textbox(Mm(x), Mm(y), Mm(w), Mm(h))
        tf = box.text_frame
        tf.clear()
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = 0
        tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, paragraph in enumerate(content.split('\n')):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.space_before = p.space_after = Pt(0)
            p.line_spacing = 1.1
            for token, family in font_runs(paragraph):
                r = p.add_run()
                r.text = token
                r.font.name = family
                r.font.size, r.font.bold = Pt(size), bold
                r.font.color.rgb = RGBColor.from_string(color)
        return box

    def line(x1, y1, x2, y2, color=LINE, width=1):
        s = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x1), Mm(y1), Mm(x2), Mm(y2))
        s.line.color.rgb = RGBColor.from_string(color)
        s.line.width = Pt(width)
        s._element.spPr.append(OxmlElement('a:effectLst'))

    def arrow(x, y, w, h, kind=MSO_SHAPE.RIGHT_ARROW):
        return shape(kind, x, y, w, h, BLUE)

    def icon(n, x, y, size=23):
        slide.shapes.add_picture(str(ROOT / f'deliverables/source/flat-icon-{n}.png'), Mm(x), Mm(y), width=Mm(size), height=Mm(size))

    def section(y, number, title):
        text(16, y, 388, 12, number+'  '+title, 25, NAVY, align=PP_ALIGN.CENTER)

    def module(x, y, number, title, image):
        rect(x, y, 184, 91, 'F0F2F3', LINE)
        rect(x, y, 184, 1.3, BLUE)
        text(x+8, y+5, 12, 10, number, 18, BLUE, True)
        text(x+23, y+5, 146, 10, title, 23, BLUE)
        if image:
            icon(image, x+8, y+22, 25)
        else:
            rect(x+12, y+24, 18, 22, 'FFFFFF', BLUE)
            for yy in (y+29, y+34, y+39):
                line(x+15, yy, x+25, yy, BLUE)
            line(x+25, y+42, x+29, y+46, BLUE, 2)
            line(x+29, y+46, x+35, y+37, BLUE, 2)

    # Editorial hierarchy: official name, one takeaway, four readable method lanes.
    rect(16, 10, 388, 78, 'F0F2F3')
    text(16, 15, 388, 8, '資安技術組決賽作品', 14, BLUE, align=PP_ALIGN.CENTER)
    title=text(16, 24, 388, 62, '融合新型內容相依時序方向模型\n入侵偵測與任務導向檢索增強稽核\n之 AI 資安框架', 44, NAVY, align=PP_ALIGN.CENTER)
    title.name='PosterTitle_Centered_210mm'
    rect(190, 87, 40, 1.2, GOLD)
    line(16, 90, 404, 90)
    text(16, 92, 388, 13, '從流量告警，走到有證據、可回復的處置', 26, NAVY)
    text(16, 105, 388, 9, '同一事件串起模型判定、相似案例、AI稽核與處置回條。', 19, MUTED)
    text(16, 116, 388, 8, '17類互補判定  ·  本機證據稽核  ·  同事件追溯  ·  策略受控回復', 18, TEAL)
    section(128, '01', '四階段方法，串成同一條事件鏈')

    stages = [('互補判定', '內容＋時序', 2), ('任務檢索', '表徵＋機率', 3),
              ('證據稽核', '保留正式分類', None), ('受控回復', '策略＋期限', 4)]
    stage_outputs = ['產生正式類別、\n信心與流量表徵',
                     '依事件任務找案例\n附上相似類別證據',
                     '核對判定與案例\n附加三態稽核結論',
                     '策略允許才介入\n讀回並確認回復']
    for i, (name, detail, image) in enumerate(stages):
        y = 145+i*56
        rect(16, y, 388, 50, 'EAF0F4' if i in (0,3) else PALE, LINE)
        rect(16, y, 1.5, 50, BLUE)
        text(23, y+3, 90, 10, f'{i+1:02d}  '+name, 23, BLUE, True)
        text(23, y+14, 90, 8, detail, 15, MUTED)
        if image:
            icon(image, 25, y+25, 21)
        else:
            rect(29, y+25, 14, 20, 'FFFFFF', BLUE)
            for dy in (29,34,39):line(32,y+dy,40,y+dy,BLUE)
        text(52, y+25, 61, 21, stage_outputs[i], 16, INK)
        if i < 3:
            arrow(257, y+50.5, 8, 5, MSO_SHAPE.DOWN_ARROW)

    def node(x, y, w, h, label, sub=None):
        rect(x, y, w, h, 'FFFFFF')
        text(x, y+(1 if sub else 0), w, h*(.56 if sub else 1), label, 20, BLUE, True, PP_ALIGN.CENTER)
        if sub:text(x, y+h*.54, w, h*.43, sub, 14, MUTED, align=PP_ALIGN.CENTER)

    # 01: parallel models enter one calibrated output.
    node(120,150,78,17,'CTBM','內容·時間差·方向')
    node(120,173,78,17,'PBCNN','短窗位元組模式')
    line(198,158.5,207,158.5,BLUE);line(198,181.5,207,181.5,BLUE)
    line(207,158.5,207,181.5,BLUE);arrow(208,167,8,6)
    node(218,158,85,25,'校準＋融合','OOF Gate')
    arrow(305,167,14,6)
    node(322,158,76,25,'17類判定','信心與512維表徵')
    # 02: task vector composition and train-only evidence retrieval.
    node(120,206,78,17,'512維表徵')
    node(120,229,78,17,'17維機率')
    line(198,214.5,207,214.5,BLUE);line(198,237.5,207,237.5,BLUE)
    line(207,214.5,207,237.5,BLUE);arrow(208,223,8,6)
    node(218,214,85,25,'529維向量','L2正規化')
    arrow(305,223,14,6)
    rect(322,214,76,25,'FFFFFF')
    text(322,214,76,10,'Top-5訓練案例',20,BLUE,True,PP_ALIGN.CENTER)
    for rank in range(5):
        x=324+rank*14.5
        rect(x,226,12,10,'EAF0F4',LINE)
        text(x,226,12,10,str(rank+1),18,BLUE,align=PP_ALIGN.CENTER)
    # 03: attach an audit; never overwrite the original classifier.
    node(120,262,78,17,'正式判定')
    node(120,285,78,17,'案例證據')
    line(198,270.5,207,270.5,BLUE);line(198,293.5,207,293.5,BLUE)
    line(207,270.5,207,293.5,BLUE);arrow(208,279,8,6)
    node(218,270,85,25,'本機AI稽核','核對同一事件')
    arrow(305,279,14,6)
    for j, label in enumerate(('支持','複核','不確定')):
        node(322,261+j*14,76,12,label)
    # 04: allowed action, readback and expiry, with the review branch explicit.
    text(120,317,278,10,'策略檢查：範圍、動作與期限｜來源限速等',18,INK)
    for j,label in enumerate(('套用規則','讀回驗證','到期回復')):
        x=120+j*98
        node(x,330,78,16,label)
        if j<2:arrow(x+81,335,14,6)
    text(120,349,278,10,'複核／不確定 → 保留監測或蒐證',15,MUTED)
    rect(16,375,388,14,PALETTE['teal_tint'].lstrip('#'))
    text(20,375,380,14,'同一事件識別碼：正式分類／案例證據／稽核結論／處置回條',18,NAVY,align=PP_ALIGN.CENTER)

    section(397, '02', '三項優勢，從判定走到可追溯處置')
    innovations = [('互補判定','內容、時間差與方向互補\n校準融合，固定17類輸出\nMacro-F1達93.05%'),
                   ('任務證據','529維任務向量找Top-5案例\nAI核對判定，保留正式分類\n命中率97.62%'),
                   ('受控可追溯','本機AI，事件資料留在本機\n同事件串接判定、證據與回條\n策略檢查、讀回及到期回復')]
    for i,(heading,copy) in enumerate(innovations):
        x=16+i*133
        rect(x,410,122,39,PALETTE['teal_tint'].lstrip('#'))
        rect(x+50,411,22,1,GOLD)
        text(x,413,122,11,heading,23,TEAL,align=PP_ALIGN.CENTER)
        text(x+2,425,118,24,copy,16.5,INK,align=PP_ALIGN.CENTER)

    section(455,'03','以分階段實測呈現效果')
    text(16,470,184,10,f'相同{m["detection_n"]:,}筆測試的 Macro-F1',17)
    for i,name in enumerate(('PBCNN','CTBM','OOF Gate')):
        y=484+i*17
        value=data['detection'][name]['macro_f1']*100
        text(16,y,44,10,name,18,BLUE if i==2 else INK,i==2,PP_ALIGN.LEFT)
        rect(64,y+2,94,6,PALE)
        rect(64,y+2,94*value/100,6,TEAL if i==2 else '7294A9')
        text(161,y,39,10,f'{value:.2f}%',21,BLUE if i==2 else INK,i==2,PP_ALIGN.RIGHT)
    for tick in (0, 50, 100):
        x = 64 + 94*tick/100
        line(x,530,x,532,LINE,.6)
        text(x-9,532,18,6,str(tick)+'%',12,MUTED,align=PP_ALIGN.CENTER)
    text(16,540,184,9,f'整體準確率{m["accuracy"]*100:.2f}%·固定17類分類',16,MUTED)
    line(210,470,210,549)
    r,j=data['retrieval'],data['judge']
    text(220,470,184,10,f'{m["bank_rows"]:,}筆訓練案例／{m["queries"]}筆查詢',17)
    text(220,481,184,15,f'Top-5  {r["top5"]*100:.2f}%',32,TEAL,True)
    text(220,497,184,10,f'MRR@5  {r["mrr5"]*100:.2f}%·訓練／查詢重疊{m["overlap"]}',15,MUTED)
    for i,(name,key) in enumerate((('支持','support'),('複核','review'),('不確定','uncertain'))):
        x=220+i*63
        rect(x,509,58,24,PALETTE['teal_tint'].lstrip('#') if key=='support' else PALE)
        text(x,510,58,12,str(j['assessment_counts'][key]),26,TEAL if key=='support' else BLUE,align=PP_ALIGN.CENTER)
        text(x,523,58,9,name,17,align=PP_ALIGN.CENTER)
    text(220,536,184,14,f'{m["errors"]}筆偵測誤判中{m["intercepted"]}筆分流\n其餘{m["false_support"]}筆獲支持，處置另經策略檢查',14.5,MUTED)
    line(16,552,404,552)
    text(16,555,67,16,f'{m["live_classes"]}類本機重跑\n{m["network_cases"]}種隔離TCP情境',16,BLUE)
    case_labels = {'BENIGN':'正常','FTP-BruteForce':'FTP','SSH-Bruteforce':'SSH',
                   'DDoS-LOIC-HTTP':'HTTP','Web-XSS':'XSS','Bot':'Bot'}
    for i, case in enumerate(data['framework']['cases']):
        x=90+i*35
        active=case['rules_applied']>0
        rect(x,555,31,9,'FFF4DD' if active else PALE,LINE)
        text(x,555,31,9,case_labels[case['validation_label']],16,BLUE,align=PP_ALIGN.CENTER)
        status='規則' if active else '監測' if case['action']=='monitor' else '蒐證'
        text(x,564,31,6,status,14,INK,align=PP_ALIGN.CENTER)
    framework=data['framework']
    text(308,555,96,16,f'背景保留 {framework["background_preserved_cases"]}/{m["network_cases"]}\n到期回復 {framework["rollback_passed_cases"]}/{m["network_cases"]}',18,BLUE,True,PP_ALIGN.RIGHT)
    text(16,572,388,7,f'{m["rules_cases"]}種套用規則、{m["passive_cases"]}種監測或蒐證；{m["rollback"]}/{m["network_cases"]}為隔離交易與回復結果，非原生攻擊防禦率。',16,MUTED)

    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
