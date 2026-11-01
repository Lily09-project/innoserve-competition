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
BLUE, NAVY, GOLD, TEAL = (PALETTE[key].lstrip('#') for key in ('blue', 'navy', 'gold', 'teal'))
INK, MUTED, PALE, LINE = (PALETTE[key].lstrip('#') for key in ('ink', 'muted', 'gray', 'line'))
BLUE_TINT, TEAL_TINT, GOLD_TINT, BLUE_MUTED = (PALETTE[key].lstrip('#') for key in ('blue_tint', 'teal_tint', 'gold_tint', 'blue_muted'))
WHITE = 'FFFFFF'


def build():
    data = validate_results(read_results())
    m = load_metrics(ROOT)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Mm(420), Mm(594)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(WHITE)
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

    def card(x, y, w, h, fill=PALE, stroke=None):
        s = shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, stroke)
        s.adjustments[0] = min(.5, 2.4/min(w, h))
        return s

    def disc(x, y, d, fill, stroke=None):
        return shape(MSO_SHAPE.OVAL, x, y, d, d, fill, stroke)

    def text(x, y, w, h, content, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT, lead=None, spacing=1.1):
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
            p.line_spacing = spacing
            runs = ([(lead[0], lead[1])] if lead and i == 0 else []) + [(paragraph, color)]
            for part, tint in runs:
                for token, family in font_runs(part):
                    r = p.add_run()
                    r.text = token
                    r.font.name = family
                    r.font.size, r.font.bold = Pt(size), bold
                    r.font.color.rgb = RGBColor.from_string(tint)
        return box

    def line(x1, y1, x2, y2, color=LINE, width=1):
        s = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Mm(x1), Mm(y1), Mm(x2), Mm(y2))
        s.line.color.rgb = RGBColor.from_string(color)
        s.line.width = Pt(width)
        s._element.spPr.append(OxmlElement('a:effectLst'))

    def arrow(x, y, w, h, kind=MSO_SHAPE.RIGHT_ARROW, color=BLUE):
        return shape(kind, x, y, w, h, color)

    def picture(name, x, y, w, h):
        slide.shapes.add_picture(str(ROOT / f'deliverables/source/poster/exhibit-{name}.png'), Mm(x), Mm(y), width=Mm(w), height=Mm(h))

    def badge(x, y, number, d=9):
        disc(x, y, d, GOLD)
        text(x, y, d, d, str(number), 17, WHITE, True, PP_ALIGN.CENTER)

    def section(y, number, title):
        text(24, y-1.5, 372, 13, title, 26, NAVY, True, PP_ALIGN.CENTER, (number+'　', TEAL))
        line(24, y+13, 396, y+13)

    # Light masthead matching the deck cover: formal name, one takeaway and the originality note.
    rect(0, 0, 420, 124, PALE)
    line(0, 124, 420, 124, LINE, 1.5)
    text(24, 12, 372, 8, '2026 資安技術組 · 決賽作品', 18, TEAL, True, PP_ALIGN.CENTER)
    title = text(24, 20, 372, 71, '融合新型內容相依時序方向模型入侵偵測\n與任務導向檢索增強稽核之 AI 資安框架', 57, NAVY, True, PP_ALIGN.CENTER)
    title.name = 'PosterTitle_Masthead'
    rect(199, 93.2, 22, 1.4, GOLD)
    text(24, 97, 372, 11, '從流量告警，走到有證據、可回復的處置', 27, BLUE, True, PP_ALIGN.CENTER)
    card(50, 111.5, 320, 8, GOLD_TINT)
    text(50, 111.5, 320, 8, '本團隊原創：CTBM、校準融合、任務導向檢索、本機AI稽核、受控回復　｜　引用既有：PBCNN（Yu et al., 2021）', 14, NAVY, True, PP_ALIGN.CENTER, ('★ ', GOLD))

    # 01: the exhibit's own HTTP-flood run, whole board first, then each stage enlarged.
    section(131, '01', '一次 HTTP 洪流攻擊，從輸入走到處置')
    text(24, 147, 372, 7, '畫面擷取自本作品 HTML 互動展示（合成封包與示意輸出；實測數值見 02）', 15, MUTED, align=PP_ALIGN.CENTER)
    card(24, 157, 372, 158, WHITE, LINE)
    for k, tone in enumerate((LINE, LINE, LINE)):
        disc(29+k*5, 159.6, 3, tone)
    text(46, 157.5, 300, 7.5, '互動展示 · HTTP 洪流情境 · 00:38 展示完成', 14, MUTED)
    line(24, 165.5, 396, 165.5, LINE, .8)
    hero_w, hero_h = 368, 368*1220/3264
    picture('overview', 26, 166, hero_w, hero_h)
    # Badges sit on the top-left corner of each stage's card in the captured board.
    for number, (fx, fy) in enumerate(((.150, .084), (.450, .059), (.810, .084), (.785, .575)), 1):
        badge(26+fx*hero_w-4.5, 166+fy*hero_h-4.5, number)
    # Input-to-output strip: what enters the framework and what leaves it in this run.
    line(24, 305, 396, 305, LINE, .8)
    text(32, 306.5, 120, 7, '輸入：8 筆 HTTP 封包（FLOW-001）', 16, NAVY, True, lead=('▶ ', TEAL))
    line(158, 310, 262, 310, BLUE_MUTED, 1.5)
    arrow(262, 307.5, 5, 5, color=BLUE_MUTED)
    text(272, 306.5, 116, 7, '輸出：限速決定送達路由器 r1', 16, NAVY, True, PP_ALIGN.RIGHT, ('◆ ', GOLD))

    panels = [('偵測', '互補判定', 'detect', '8 筆封包經 CTBM＋PBCNN 編碼', 'DDoS-LOIC-HTTP 正式分類'),
              ('檢索', '任務證據', 'retrieve', '512＋17＝529 維查詢向量', 'cosine 排序取 Top-5 案例'),
              ('稽核', '證據稽核', 'audit', '本機AI核對分類與五筆證據', '支持，保留正式分類'),
              ('處置', '受控可追溯', 'act', '策略檢查通過才下發指令', '來源限速＋30秒到期回復')]
    for i, (stage, heading, frame, body, output) in enumerate(panels):
        x, y = 24+i*95, 322
        card(x, y, 87, 104, WHITE, LINE)
        picture(frame, x+1.5, y+1.5, 84, 70)
        badge(x+3.5, y+3.5, i+1, 8)
        text(x, y+74, 87, 8, heading, 19, NAVY, True, PP_ALIGN.CENTER, (f'{stage}｜', TEAL))
        text(x, y+83, 87, 6, body, 14, INK, align=PP_ALIGN.CENTER)
        card(x+5, y+91, 77, 9, TEAL_TINT)
        text(x+5, y+91, 77, 9, output, 14, TEAL, True, PP_ALIGN.CENTER, ('輸出 ', MUTED))
        if i < 3:
            arrow(x+88.5, y+34, 5, 5, color=BLUE_MUTED)

    # 02: recorded aggregates, one card per stage family.
    section(434, '02', '實測結果，分階段驗證同一套框架')
    for x in (24, 150, 276):
        card(x, 454, 120, 106, PALE)
    text(24, 458, 120, 9, '17類偵測', 20, NAVY, True, PP_ALIGN.CENTER, ('互補判定｜', TEAL))
    text(24, 468, 120, 7, f'相同{m["detection_n"]:,}筆測試的 Macro-F1', 14, MUTED, align=PP_ALIGN.CENTER)
    for i, name in enumerate(('PBCNN', 'CTBM', 'OOF Gate')):
        y = 480+i*17
        value = data['detection'][name]['macro_f1']*100
        best = i == 2
        text(37, y, 50, 7, name, 16, TEAL if best else INK, True)
        text(87, y-.5, 44, 8, f'{value:.2f}%', 18, TEAL if best else INK, True, PP_ALIGN.RIGHT)
        rect(37, y+8, 94, 5, WHITE)
        rect(37, y+8, 94*value/100, 5, TEAL if best else BLUE_MUTED)
    for tick in (0, 50, 100):
        x = 37 + 94*tick/100
        line(x, 531, x, 533, MUTED, .6)
        text(x-9, 533.5, 18, 5, str(tick)+'%', 12, MUTED, align=PP_ALIGN.CENTER)
    text(24, 541, 120, 8, f'整體準確率 {m["accuracy"]*100:.2f}%', 17, NAVY, True, PP_ALIGN.CENTER)
    text(24, 549.5, 120, 6, '固定17類輸出 · OOF Gate', 13, MUTED, align=PP_ALIGN.CENTER)

    r, j = data['retrieval'], data['judge']
    text(150, 458, 120, 9, '檢索與稽核', 20, NAVY, True, PP_ALIGN.CENTER, ('任務證據｜', TEAL))
    text(150, 468, 120, 7, f'{m["bank_rows"]:,}筆訓練案例／{m["queries"]}筆查詢', 14, MUTED, align=PP_ALIGN.CENTER)
    text(150, 476, 120, 14, f'Top-5  {r["top5"]*100:.2f}%', 32, TEAL, True, PP_ALIGN.CENTER)
    text(150, 490, 120, 7, f'MRR@5  {r["mrr5"]*100:.2f}%·訓練／查詢重疊{m["overlap"]}', 14, MUTED, align=PP_ALIGN.CENTER)
    for i, (name, key) in enumerate((('支持', 'support'), ('複核', 'review'), ('不確定', 'uncertain'))):
        x = 155.5+i*37.5
        card(x, 500, 34, 26, TEAL_TINT if key == 'support' else WHITE)
        text(x, 501, 34, 13, str(j['assessment_counts'][key]), 26, TEAL if key == 'support' else NAVY, True, PP_ALIGN.CENTER)
        text(x, 514, 34, 9, name, 15, INK, align=PP_ALIGN.CENTER)
    text(150, 531, 120, 14, f'{m["errors"]}筆偵測誤判中{m["intercepted"]}筆分流\n其餘{m["false_support"]}筆獲支持，處置另經策略檢查', 14, MUTED, align=PP_ALIGN.CENTER)

    framework = data['framework']
    text(276, 458, 120, 9, '隔離TCP驗證', 20, NAVY, True, PP_ALIGN.CENTER, ('受控可追溯｜', TEAL))
    text(276, 468, 120, 7, f'{m["live_classes"]}類本機重跑·{m["network_cases"]}種隔離TCP情境', 14, MUTED, align=PP_ALIGN.CENTER)
    case_labels = {'BENIGN': '正常', 'FTP-BruteForce': 'FTP', 'SSH-Bruteforce': 'SSH',
                   'DDoS-LOIC-HTTP': 'HTTP', 'Web-XSS': 'XSS', 'Bot': 'Bot'}
    for i, case in enumerate(framework['cases']):
        x, y = 282+(i % 3)*37, 478+(i//3)*20
        active = case['rules_applied'] > 0
        card(x, y, 34, 17, GOLD_TINT if active else WHITE, None if active else LINE)
        text(x, y+.5, 34, 9, case_labels[case['validation_label']], 15, NAVY, True, PP_ALIGN.CENTER)
        status = '規則' if active else '監測' if case['action'] == 'monitor' else '蒐證'
        text(x, y+9, 34, 7, status, 12, MUTED, align=PP_ALIGN.CENTER)
    text(276, 520, 120, 9, f'背景保留 {framework["background_preserved_cases"]}/{m["network_cases"]}　到期回復 {framework["rollback_passed_cases"]}/{m["network_cases"]}', 18, TEAL, True, PP_ALIGN.CENTER)
    text(276, 532, 120, 13, f'{m["rules_cases"]}種套用規則、{m["passive_cases"]}種監測或蒐證\n策略允許才下發，讀回後到期撤銷', 14, MUTED, align=PP_ALIGN.CENTER)
    text(24, 566, 372, 7, f'{m["rollback"]}/{m["network_cases"]}為隔離交易與回復結果，非原生攻擊防禦率；01 展示畫面為合成資料，實測數值以 02 為準。', 15, MUTED, align=PP_ALIGN.CENTER)

    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
