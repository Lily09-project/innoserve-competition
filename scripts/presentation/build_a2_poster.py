"""Build an editable A2 methods poster from validated recorded aggregates."""
from pathlib import Path
import json
import re
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
from finalize_delivery import normalize

PALETTE = json.loads((ROOT/'design-system/palette.json').read_text(encoding='utf-8'))
BLUE, NAVY, GOLD = (PALETTE[key].lstrip('#') for key in ('blue', 'navy', 'gold'))
INK = '171C1D'
MUTED = '53666E'
PALE = 'F0F2F3'
LINE = 'D6DDE0'


def build():
    data = validate_results(read_results())
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

    def text(x, y, w, h, content, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT):
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
            for token in re.findall(r'[\x00-\x7f]+|[^\x00-\x7f]+', paragraph):
                r = p.add_run()
                r.text = token
                r.font.name = 'Times New Roman' if token.isascii() else 'DFKai-SB'
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
        slide.shapes.add_picture(str(ROOT / f'deliverables/source/icon-{n}.png'), Mm(x), Mm(y), width=Mm(size), height=Mm(size))

    def section(y, number, title):
        text(16, y, 12, 10, number, 20, BLUE, True)
        text(31, y, 370, 10, title, 24, NAVY)

    def module(x, y, number, title, image):
        rect(x, y, 184, 91, 'F0F2F3', LINE)
        rect(x, y, 184, 1.3, BLUE)
        text(x+8, y+5, 12, 10, number, 18, BLUE, True)
        text(x+23, y+5, 146, 10, title, 23)
        if image:
            icon(image, x+8, y+22, 25)
        else:
            rect(x+12, y+24, 18, 22, 'FFFFFF', BLUE)
            for yy in (y+29, y+34, y+39):
                line(x+15, yy, x+25, yy, BLUE)
            line(x+25, y+42, x+29, y+46, BLUE, 2)
            line(x+29, y+46, x+35, y+37, BLUE, 2)

    # Header: exact official title with print-safe margins.
    text(16, 15, 388, 8, '資安技術組決賽作品', 14, BLUE)
    text(16, 24, 388, 46, '融合新型內容相依時序方向模型\n入侵偵測與任務導向檢索增強稽核\n之 AI 資安框架', 32, NAVY)
    icon(4, 344, 29, 50)
    text(16, 73, 388, 10, '同一事件串起流量判定、案例證據與可回復的處置', 22, BLUE)
    line(16, 87, 404, 87)
    icon(1, 16, 94, 27)
    text(50, 94, 354, 10, '從辨識告警，走到可查核的資安處理流程', 23)
    text(50, 107, 354, 13, '面向校園與中小型組織的資安管理需求，協助管理者核對事件依據。', 17, MUTED)

    section(129, '01', '四階段方法，以同一事件銜接')
    module(16, 145, '1', '互補模型判定', 2)
    text(56, 168, 137, 13, 'CTBM：內容、時間差、方向', 18)
    text(56, 182, 137, 13, 'PBCNN：短窗位元組模式', 18)
    arrow(98, 200, 18, 7, MSO_SHAPE.DOWN_ARROW)
    text(24, 211, 168, 10, '校準＋OOF Gate 融合', 20, BLUE, True, PP_ALIGN.CENTER)
    text(24, 225, 168, 7, '輸出：17類判定、信心與512維表徵', 15, MUTED, align=PP_ALIGN.CENTER)

    module(220, 145, '2', '任務導向案例檢索', 3)
    text(260, 168, 137, 13, '512維表徵＋17維機率', 20)
    text(260, 182, 137, 13, '529維任務向量，L2正規化', 18)
    arrow(302, 200, 18, 7, MSO_SHAPE.DOWN_ARROW)
    text(228, 211, 168, 10, 'Top-5 訓練案例證據', 20, BLUE, True, PP_ALIGN.CENTER)
    text(228, 225, 168, 7, '案例庫僅由訓練資料建立', 15, MUTED, align=PP_ALIGN.CENTER)
    arrow(202, 183, 16, 8)
    arrow(307, 238, 10, 13, MSO_SHAPE.DOWN_ARROW)

    module(220, 253, '3', '本機AI證據稽核', None)
    text(260, 275, 137, 12, '核對正式判定與相似案例', 19)
    text(260, 289, 137, 12, '保留分類，附加稽核結論', 19)
    for j, label in enumerate(('支持', '複核', '不確定')):
        xx = 228+j*55
        rect(xx, 308, 51, 15, 'EAF0F4')
        text(xx, 308, 51, 15, label, 20, BLUE, align=PP_ALIGN.CENTER)
    text(228, 331, 168, 8, '複核與不確定事件保留監測或蒐證', 15, MUTED, align=PP_ALIGN.CENTER)

    module(16, 253, '4', '受控處置與回復', 4)
    text(56, 275, 137, 12, '檢查範圍、允許動作與期限', 19)
    text(56, 289, 137, 12, '允許的策略才進入執行', 19)
    for j, label in enumerate(('套用', '讀回', '回復')):
        xx = 24+j*56
        text(xx, 308, 44, 15, label, 21, BLUE, align=PP_ALIGN.CENTER)
        if j < 2:
            arrow(xx+45, 312, 9, 5)
    text(24, 331, 168, 8, '同次執行回條綁定，規則到期撤銷', 15, MUTED, align=PP_ALIGN.CENTER)
    arrow(202, 291, 16, 8, MSO_SHAPE.LEFT_ARROW)
    rect(16, 351, 388, 13, 'FFF4DD')
    text(20, 351, 380, 13, '同一事件識別碼：正式分類／案例證據／稽核結論／處置回條', 18, NAVY, align=PP_ALIGN.CENTER)

    section(376, '02', '創新落在模型互補與證據銜接')
    innovations = [
        ('互補判定', '時序關係與局部內容共同判斷\n由校準與Gate形成正式分類'),
        ('任務證據', '表徵與類別機率共同檢索\n為每個事件找可核對的案例'),
        ('可追溯處置', '稽核附回原事件，策略另檢查\n讀回與到期回復留下紀錄'),
    ]
    for i, (heading, copy) in enumerate(innovations):
        x = 16+i*133
        if i:
            line(x-6, 396, x-6, 430)
        text(x, 394, 122, 11, heading, 23, BLUE)
        text(x, 408, 124, 23, copy, 16, MUTED)

    section(443, '03', '以分階段實測呈現效果')
    text(16, 458, 184, 10, '相同18,998筆測試的 Macro-F1', 18)
    for i, name in enumerate(('PBCNN', 'CTBM', 'OOF Gate')):
        y = 476+i*17
        value = data['detection'][name]['macro_f1']*100
        text(16, y, 44, 10, name, 18, BLUE if i == 2 else INK, i == 2)
        rect(64, y+2, 94, 6, 'F0F2F3')
        rect(64, y+2, 94*value/100, 6, GOLD if i == 2 else '7294A9')
        text(161, y, 39, 10, f'{value:.2f}%', 21, BLUE if i == 2 else INK, i == 2, PP_ALIGN.RIGHT)
    text(16, 530, 184, 9, '融合判定 Accuracy 98.08%', 17, MUTED)
    text(16, 542, 184, 9, '比較使用相同資料與17類標籤', 15, MUTED)

    line(210, 458, 210, 550)
    r, j = data['retrieval'], data['judge']
    text(220, 458, 184, 10, '1,550筆訓練案例／463筆查詢', 18)
    text(220, 473, 184, 12, f'Top-5  {r["top5"]*100:.2f}%', 28, BLUE, True)
    text(220, 488, 184, 10, f'MRR@5  {r["mrr5"]*100:.2f}%　訓練／查詢重疊0', 16, MUTED)
    for i, (name, key) in enumerate((('支持', 'support'), ('複核', 'review'), ('不確定', 'uncertain'))):
        x = 220+i*62
        text(x, 505, 58, 12, str(j['assessment_counts'][key]), 27, BLUE, align=PP_ALIGN.CENTER)
        text(x, 520, 58, 9, name, 18, align=PP_ALIGN.CENTER)
    text(220, 537, 184, 14, '30筆偵測誤判中18筆分流\n其餘12筆獲支持，處置另經策略檢查', 14, MUTED)

    line(16, 558, 404, 558)
    text(16, 563, 388, 10, '整合驗證：17類真實張量重跑；6種隔離TCP情境，背景保留與回復皆6/6。', 17, BLUE)
    text(16, 573, 388, 6, '6種情境含4種套用規則、2種監測或蒐證；6/6為隔離交易與回復結果，非原生攻擊防禦率。', 11.5, MUTED)

    target = ROOT / 'deliverables/決賽海報_AI資安框架_A2.pptx'
    intermediate = ROOT / 'validation/poster-a2/authoring.pptx'
    intermediate.parent.mkdir(parents=True, exist_ok=True)
    prs.save(intermediate)
    normalize(intermediate, target)
    print(target.name)


if __name__ == '__main__':
    build()
