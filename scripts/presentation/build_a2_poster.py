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

    # Every block below sits on one 3-column grid (118.67 mm columns, 8 mm gutters) inside 24-396 mm.
    cw = (372-16)/3
    cols = [24+k*(cw+8) for k in range(3)]

    # 01: original data, then one HTTP-flood run of the HTML exhibit as six blocks, raw input to output.
    section(130, '01', '原始資料與方法：一次 HTTP 洪流攻擊，從原始輸入到輸出')
    data_cells = [('訓練／驗證', 'CICIDS2017＋CSE-CIC-IDS2018'),
                  ('封存測試 17 類', f'CSE-CIC-IDS2018 {m["detection_n"]:,} 筆'),
                  ('檢索案例庫', f'{m["bank_rows"]:,} 筆訓練案例／{m["queries"]} 查詢')]
    for k, (label, value) in enumerate(data_cells):
        card(cols[k], 147, cw, 16, PALE)
        text(cols[k], 148, cw, 7, label, 14, TEAL, True, PP_ALIGN.CENTER, ('原始資料｜', MUTED))
        text(cols[k], 155, cw, 7, value, 15, NAVY, True, PP_ALIGN.CENTER)

    blocks = [(None, '原始輸入', 'FLOW-001 封包序列', 'input', '輸入', '8 筆 HTTP 請求與回應（合成封包）'),
              (1, '偵測', '互補判定', 'detect', '輸出', 'DDoS-LOIC-HTTP 正式分類'),
              (2, '檢索', '任務證據', 'retrieve', '輸出', 'cosine 排序取 Top-5 案例'),
              (3, '稽核', '證據稽核', 'audit', '輸出', '支持，保留正式分類'),
              (4, '處置', '受控可追溯', 'act', '輸出', '來源限速＋30秒到期回復'),
              (None, '輸出', '處置決定與 r1 指令', 'output', '結果', '新連線每秒限 1 個，超額丟棄')]
    rows = [168, 283]
    image_w = cw-3
    image_h = image_w*80/115.67
    for n, (number, stage, heading, frame, chip, value) in enumerate(blocks):
        x, y = cols[n % 3], rows[n//3]
        edge = number is None
        card(x, y, cw, 107, WHITE, TEAL if edge else LINE)
        if edge:
            # Input and output keep a header row for their tag; the capture shrinks to fit below it.
            tag(x+3.5, y+3, stage, 22)
            h = image_h-9.5
            picture(frame, x+cw/2-h*115.67/80/2, y+11, h*115.67/80, h)
        else:
            picture(frame, x+1.5, y+1.5, image_w, image_h)
            badge(x+3.5, y+3.5, number, 8)
        text(x, y+84, cw, 8, heading, 19, NAVY, True, PP_ALIGN.CENTER, (f'{stage}｜', TEAL))
        card(x+6, y+94, cw-12, 9, TEAL_TINT)
        text(x+6, y+94, cw-12, 9, value, 14, TEAL, True, PP_ALIGN.CENTER, (chip+' ', MUTED))
        if n % 3 < 2:
            arrow(x+cw+1.5, y+1.5+image_h/2-2.5, 5, 5, color=BLUE_MUTED)
    # Row turn: from the retrieval block down and back to the audit block.
    turn = rows[0]+107+3.5
    line(cols[2]+cw/2, rows[0]+107, cols[2]+cw/2, turn, BLUE_MUTED, 1.5)
    line(cols[0]+cw/2, turn, cols[2]+cw/2, turn, BLUE_MUTED, 1.5)
    arrow(cols[0]+cw/2-2.5, turn, 5, rows[1]-turn, MSO_SHAPE.DOWN_ARROW, BLUE_MUTED)

    # 02 results (columns 1-2) and 03 defence mechanism (column 3) share one baseline.
    section(397, '02', '結果', cols[0], 2*cw+8)
    section(397, '03', '防禦機制', cols[2], cw)
    card(cols[0], 414, 2*cw+8, 96, PALE)
    card(cols[2], 414, cw, 96, PALE)
    line(cols[1]-4, 422, cols[1]-4, 502, LINE, .8)

    x0, y0 = cols[0], 414
    bar = x0+(cw-94)/2
    text(x0, y0+3, cw, 8, '17類偵測', 17, NAVY, True, PP_ALIGN.CENTER, ('互補判定｜', TEAL))
    text(x0, y0+11, cw, 6, f'相同{m["detection_n"]:,}筆封存測試的 Macro-F1', 13, MUTED, align=PP_ALIGN.CENTER)
    for i, name in enumerate(('PBCNN', 'CTBM', 'OOF Gate')):
        y = y0+20+i*15
        value = data['detection'][name]['macro_f1']*100
        best = i == 2
        text(bar, y, 50, 7, name, 15, TEAL if best else INK, True)
        text(bar+50, y-.5, 44, 8, f'{value:.2f}%', 16, TEAL if best else INK, True, PP_ALIGN.RIGHT)
        rect(bar, y+7.5, 94, 5, WHITE)
        rect(bar, y+7.5, 94*value/100, 5, TEAL if best else BLUE_MUTED)
    for tick in (0, 50, 100):
        x = bar + 94*tick/100
        line(x, y0+64, x, y0+66, MUTED, .6)
        text(x-9, y0+66.5, 18, 5, str(tick)+'%', 12, MUTED, align=PP_ALIGN.CENTER)
    text(x0, y0+74, cw, 7, f'整體準確率 {m["accuracy"]*100:.2f}%', 16, NAVY, True, PP_ALIGN.CENTER)
    text(x0, y0+81.5, cw, 6, '固定17類輸出 · OOF Gate', 13, MUTED, align=PP_ALIGN.CENTER)

    r, j = data['retrieval'], data['judge']
    x1 = cols[1]
    text(x1, y0+3, cw, 8, '檢索與稽核', 17, NAVY, True, PP_ALIGN.CENTER, ('任務證據｜', TEAL))
    text(x1, y0+11, cw, 6, f'{m["bank_rows"]:,}筆訓練案例／{m["queries"]}筆查詢', 13, MUTED, align=PP_ALIGN.CENTER)
    text(x1, y0+18, cw, 12, f'Top-5  {r["top5"]*100:.2f}%', 28, TEAL, True, PP_ALIGN.CENTER)
    text(x1, y0+31, cw, 6, f'MRR@5  {r["mrr5"]*100:.2f}%·訓練／查詢重疊{m["overlap"]}', 13, MUTED, align=PP_ALIGN.CENTER)
    for i, (name, key) in enumerate((('支持', 'support'), ('複核', 'review'), ('不確定', 'uncertain'))):
        x = x1+(cw-110)/2+i*38
        card(x, y0+40, 34, 22, TEAL_TINT if key == 'support' else WHITE)
        text(x, y0+41, 34, 11, str(j['assessment_counts'][key]), 22, TEAL if key == 'support' else NAVY, True, PP_ALIGN.CENTER)
        text(x, y0+53, 34, 7, name, 14, INK, align=PP_ALIGN.CENTER)
    text(x1, y0+66, cw, 12, f'{m["errors"]}筆偵測誤判中{m["intercepted"]}筆分流\n其餘{m["false_support"]}筆獲支持，處置另經策略檢查', 13, MUTED, align=PP_ALIGN.CENTER)

    x2 = cols[2]
    framework = data['framework']
    text(x2, y0+3, cw, 8, '策略允許才執行', 17, NAVY, True, PP_ALIGN.CENTER, ('受控可追溯｜', TEAL))
    steps = [('策略檢查', 0, 0), ('套用規則', 0, 1), ('讀回驗證', 1, 1), ('到期回復', 1, 0)]
    for label, row, col in steps:
        x, y = x2+6+col*(cw-62), y0+13+row*15
        last = label == '到期回復'
        card(x, y, 50, 10, TEAL_TINT if last else WHITE, None if last else LINE)
        text(x, y, 50, 10, label, 15, TEAL if last else NAVY, True, PP_ALIGN.CENTER)
    arrow(x2+cw/2-2.5, y0+15.5, 5, 5, color=BLUE_MUTED)
    arrow(x2+6+cw-62+22.5, y0+23.5, 5, 4, MSO_SHAPE.DOWN_ARROW, BLUE_MUTED)
    arrow(x2+cw/2-2.5, y0+30.5, 5, 5, MSO_SHAPE.LEFT_ARROW, BLUE_MUTED)
    text(x2, y0+40, cw, 6, '套用規則如來源限速；讀回驗證後到期撤銷', 12, MUTED, align=PP_ALIGN.CENTER)
    text(x2, y0+48, cw, 6, f'{m["live_classes"]}類本機重跑 · {m["network_cases"]}種隔離TCP情境', 13, MUTED, align=PP_ALIGN.CENTER)
    case_labels = {'BENIGN': '正常', 'FTP-BruteForce': 'FTP', 'SSH-Bruteforce': 'SSH',
                   'DDoS-LOIC-HTTP': 'HTTP', 'Web-XSS': 'XSS', 'Bot': 'Bot'}
    for i, case in enumerate(framework['cases']):
        x, y = x2+(cw-110)/2+(i % 3)*38, y0+55+(i//3)*15
        active = case['rules_applied'] > 0
        card(x, y, 34, 13, GOLD_TINT if active else WHITE, None if active else LINE)
        status = '規則' if active else '監測' if case['action'] == 'monitor' else '蒐證'
        text(x, y+.3, 34, 7, case_labels[case['validation_label']], 15, NAVY, True, PP_ALIGN.CENTER)
        text(x, y+7, 34, 5.5, status, 12, MUTED, align=PP_ALIGN.CENTER)
    text(x2, y0+85, cw, 8, f'背景保留 {framework["background_preserved_cases"]}/{m["network_cases"]}　到期回復 {framework["rollback_passed_cases"]}/{m["network_cases"]}', 16, TEAL, True, PP_ALIGN.CENTER)
    text(24, 513, 372, 7, f'{m["rollback"]}/{m["network_cases"]}為隔離交易與回復結果，非原生攻擊防禦率；01 畫面取自互動展示（合成資料），實測數值以 02、03 為準。', 15, MUTED, align=PP_ALIGN.CENTER)

    # Decorative footer art (no data): switch and neon panels for the six scenario families.
    slide.shapes.add_picture(str(ROOT / 'deliverables/source/poster/art-banner.png'), 0, Mm(524), width=Mm(420), height=Mm(70))

    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
