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
BADGE_LIFT = 0.015


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
        # The digit box is lifted by BADGE_LIFT of the diameter: CJK line boxes sit low,
        # and this places the rendered digit on the disc's optical centre.
        disc(x, y, d, GOLD)
        digit = text(x, y-d*BADGE_LIFT, d, d, str(number), 17*d/9, WHITE, True, PP_ALIGN.CENTER)
        digit.name = f'PosterBadge_{number}'

    def section(y, number, title, x=24, w=372):
        text(x, y-1.5, w, 13, title, 26, NAVY, True, PP_ALIGN.CENTER, (number+'　', TEAL))
        line(x, y+13, x+w, y+13)

    def tag(x, y, label, w=22):
        card(x, y, w, 7, TEAL)
        text(x, y, w, 7, label, 14, WHITE, True, PP_ALIGN.CENTER)

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

    # Every block below sits on one 4-column grid (87 mm columns, 8 mm gutters) inside 24-396 mm.
    cols = [24+k*95 for k in range(4)]

    # 01: original data and method together — the data the models learned from, then one
    # HTTP-flood run of the HTML exhibit from input to response.
    section(130, '01', '原始資料與方法：一次 HTTP 洪流攻擊，從輸入走到處置')
    data_cells = [('原始資料', '17 類網路流量'),
                  ('訓練／驗證', 'CICIDS2017＋CSE-CIC-IDS2018'),
                  ('封存測試', f'CSE-CIC-IDS2018 {m["detection_n"]:,} 筆'),
                  ('案例庫', f'{m["bank_rows"]:,} 筆訓練案例／{m["queries"]} 查詢')]
    for k, (label, value) in enumerate(data_cells):
        x = cols[k]
        card(x, 147, 87, 18, PALE)
        if k == 0:
            tag(x+32.5, 148.5, label)
        else:
            text(x, 148.5, 87, 7, label, 14, TEAL, True, PP_ALIGN.CENTER)
        text(x, 156.5, 87, 7, value, 15, NAVY, True, PP_ALIGN.CENTER)

    card(24, 170, 372, 157, WHITE, LINE)
    for k in range(3):
        disc(30+k*5, 172.5, 3, LINE)
    tag(48, 170.5, '方法', 16)
    text(67, 170.5, 300, 7, '互動展示 · HTTP 洪流情境 · 00:38 展示完成（合成封包與示意輸出；實測數值見 02）', 14, MUTED)
    line(24, 178.5, 396, 178.5, LINE, .8)
    hero_w, hero_h = 368, 368*1220/3264
    picture('overview', 26, 179, hero_w, hero_h)
    # Badges sit on the top-left corner of each stage's card in the captured board.
    for number, (fx, fy) in enumerate(((.150, .084), (.450, .059), (.810, .084), (.785, .575)), 1):
        badge(26+fx*hero_w-4.5, 179+fy*hero_h-4.5, number)
    # Input-to-output strip: what enters the framework and what leaves it in this run.
    line(24, 317, 396, 317, LINE, .8)
    text(30, 318.5, 150, 7, '輸入：8 筆 HTTP 封包（FLOW-001）', 16, NAVY, True, lead=('▶ ', TEAL))
    line(160, 322, 254, 322, BLUE_MUTED, 1.5)
    arrow(254, 319.5, 5, 5, color=BLUE_MUTED)
    text(240, 318.5, 150, 7, '輸出：限速決定送達路由器 r1', 16, NAVY, True, PP_ALIGN.RIGHT, ('◆ ', GOLD))

    panels = [('偵測', '互補判定', 'detect', 'DDoS-LOIC-HTTP 正式分類'),
              ('檢索', '任務證據', 'retrieve', 'cosine 排序取 Top-5 案例'),
              ('稽核', '證據稽核', 'audit', '支持，保留正式分類'),
              ('處置', '受控可追溯', 'act', '來源限速＋30秒到期回復')]
    for i, (stage, heading, frame, output) in enumerate(panels):
        x, y = cols[i], 333
        card(x, y, 87, 96, WHITE, LINE)
        picture(frame, x+1.5, y+1.5, 84, 70)
        badge(x+3.5, y+3.5, i+1, 8)
        text(x, y+74, 87, 8, heading, 19, NAVY, True, PP_ALIGN.CENTER, (f'{stage}｜', TEAL))
        card(x+5, y+84, 77, 9, TEAL_TINT)
        text(x+5, y+84, 77, 9, output, 14, TEAL, True, PP_ALIGN.CENTER, ('輸出 ', MUTED))
        if i < 3:
            arrow(x+88.5, y+34, 5, 5, color=BLUE_MUTED)

    # 02 results (columns 1-2) and 03 defence mechanism (columns 3-4) share one baseline.
    section(436, '02', '結果', cols[0], 182)
    section(436, '03', '防禦機制', cols[2], 182)
    card(cols[0], 453, 182, 106, PALE)
    card(cols[2], 453, 182, 106, PALE)

    x0 = cols[0]
    text(x0, 456, 182, 8, f'17類偵測 Macro-F1（相同{m["detection_n"]:,}筆封存測試）', 17, NAVY, True, PP_ALIGN.CENTER, ('互補判定｜', TEAL))
    for i, name in enumerate(('PBCNN', 'CTBM', 'OOF Gate')):
        y = 467+i*9
        value = data['detection'][name]['macro_f1']*100
        best = i == 2
        text(x0+8, y, 34, 7, name, 15, TEAL if best else INK, True)
        rect(x0+44, y+1, 94, 5, WHITE)
        rect(x0+44, y+1, 94*value/100, 5, TEAL if best else BLUE_MUTED)
        text(x0+140, y-.5, 34, 8, f'{value:.2f}%', 17, TEAL if best else INK, True, PP_ALIGN.RIGHT)
    for tick in (0, 50, 100):
        x = x0+44 + 94*tick/100
        line(x, 494, x, 496, MUTED, .6)
        text(x-9, 496.5, 18, 5, str(tick)+'%', 12, MUTED, align=PP_ALIGN.CENTER)
    text(x0, 503, 182, 7, f'整體準確率 {m["accuracy"]*100:.2f}%　·　固定17類輸出（OOF Gate）', 15, NAVY, True, PP_ALIGN.CENTER)
    line(x0+8, 513, x0+174, 513, LINE, .8)

    r, j = data['retrieval'], data['judge']
    text(x0, 515.5, 87, 7, '檢索與稽核', 15, NAVY, True, PP_ALIGN.CENTER, ('任務證據｜', TEAL))
    text(x0, 523, 87, 13, f'Top-5  {r["top5"]*100:.2f}%', 28, TEAL, True, PP_ALIGN.CENTER)
    text(x0, 537, 87, 12, f'MRR@5 {r["mrr5"]*100:.2f}%\n{m["bank_rows"]:,}筆案例／{m["queries"]}查詢·重疊{m["overlap"]}', 13, MUTED, align=PP_ALIGN.CENTER)
    for i, (name, key) in enumerate((('支持', 'support'), ('複核', 'review'), ('不確定', 'uncertain'))):
        x = x0+95+i*28
        card(x, 517, 25, 22, TEAL_TINT if key == 'support' else WHITE)
        text(x, 518, 25, 11, str(j['assessment_counts'][key]), 22, TEAL if key == 'support' else NAVY, True, PP_ALIGN.CENTER)
        text(x, 530, 25, 7, name, 14, INK, align=PP_ALIGN.CENTER)
    text(x0+95, 542, 81, 12, f'{m["errors"]}筆偵測誤判中{m["intercepted"]}筆分流\n其餘{m["false_support"]}筆獲支持', 13, MUTED, align=PP_ALIGN.CENTER)

    x0 = cols[2]
    framework = data['framework']
    text(x0, 456, 182, 8, '策略允許才執行，讀回驗證，到期撤銷', 17, NAVY, True, PP_ALIGN.CENTER, ('受控可追溯｜', TEAL))
    steps = [('策略檢查', '範圍·動作·期限'), ('套用規則', '如來源限速'), ('讀回驗證', '核對規則與回條'), ('到期回復', '撤銷並確認服務')]
    for k, (label, note) in enumerate(steps):
        x = x0+6+k*44
        card(x, 467, 38, 12, TEAL_TINT if k == 3 else WHITE, None if k == 3 else LINE)
        text(x, 467, 38, 12, label, 15, TEAL if k == 3 else NAVY, True, PP_ALIGN.CENTER)
        text(x-3, 480.5, 44, 6, note, 12, MUTED, align=PP_ALIGN.CENTER)
        if k < 3:
            arrow(x+38.8, 471, 4.4, 4, color=BLUE_MUTED)
    text(x0, 490, 182, 7, f'{m["live_classes"]}類本機重跑 · {m["network_cases"]}種隔離TCP情境', 14, MUTED, align=PP_ALIGN.CENTER)
    case_labels = {'BENIGN': '正常', 'FTP-BruteForce': 'FTP', 'SSH-Bruteforce': 'SSH',
                   'DDoS-LOIC-HTTP': 'HTTP', 'Web-XSS': 'XSS', 'Bot': 'Bot'}
    for i, case in enumerate(framework['cases']):
        x = x0+6+i*29
        active = case['rules_applied'] > 0
        card(x, 499, 25, 17, GOLD_TINT if active else WHITE, None if active else LINE)
        text(x, 499.5, 25, 9, case_labels[case['validation_label']], 15, NAVY, True, PP_ALIGN.CENTER)
        status = '規則' if active else '監測' if case['action'] == 'monitor' else '蒐證'
        text(x, 508, 25, 7, status, 12, MUTED, align=PP_ALIGN.CENTER)
    line(x0+8, 522, x0+174, 522, LINE, .8)
    for k, (label, value) in enumerate((('背景服務保留', framework['background_preserved_cases']), ('到期回復完整', framework['rollback_passed_cases']))):
        x = x0+k*91
        text(x, 525, 91, 14, f'{value}/{m["network_cases"]}', 30, TEAL, True, PP_ALIGN.CENTER)
        text(x, 539, 91, 7, label, 15, INK, align=PP_ALIGN.CENTER)
    text(x0, 548, 182, 7, f'{m["rules_cases"]}種套用規則、{m["passive_cases"]}種監測或蒐證', 13, MUTED, align=PP_ALIGN.CENTER)
    text(24, 564, 372, 7, f'{m["rollback"]}/{m["network_cases"]}為隔離交易與回復結果，非原生攻擊防禦率；01 展示畫面為合成資料，實測數值以 02、03 為準。', 15, MUTED, align=PP_ALIGN.CENTER)

    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
