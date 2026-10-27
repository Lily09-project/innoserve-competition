"""Finals deck (16:9, light theme, 6-minute talk incl. embedded video). Numbers follow 系統概述.docx and results/."""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Pt

OUT, FIG, VIDEO, POSTER = (Path(a) for a in sys.argv[1:5])

TITLE_EN = ("An AI Security Framework Integrating Novel Content Dependent Temporal Directional "
            "Intrusion Detection and Task Oriented Retrieval Augmented")
INK, MUTED, LINE = "0B1B33", "5B6B82", "DCE3EE"
BG, PANEL = "F5F8FC", "FFFFFF"
BLUE, TEAL, VIOLET, AMBER, ORANGE, RED = "1D4ED8", "0F766E", "6D28D9", "B45309", "C2410C", "B42318"
FONT = "Microsoft JhengHei"
IN = 914400
W, H = 13.333, 7.5

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
blank = prs.slide_layouts[6]


def rgb(h):
    return RGBColor.from_string(h)


def E(v):
    return Emu(int(v * IN))


def box(s, x, y, w, h, fill=PANEL, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None, lw=1):
    b = s.shapes.add_shape(shape, E(x), E(y), E(w), E(h))
    if fill is None:
        b.fill.background()
    else:
        b.fill.solid(); b.fill.fore_color.rgb = rgb(fill)
    if line is None:
        b.line.fill.background()
    else:
        b.line.color.rgb = rgb(line); b.line.width = Pt(lw)
    if radius is not None:
        b.adjustments[0] = radius
    b.shadow.inherit = False
    return b


def rbox(s, x, y, w, h, fill=PANEL, line=LINE, radius=0.08, lw=1):
    return box(s, x, y, w, h, fill, line, MSO_SHAPE.ROUNDED_RECTANGLE, radius, lw)


def text(s, x, y, w, h, runs, size=18, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.5, font=FONT):
    """runs: str | list of paragraphs; paragraph: str | list of (text, overrides)."""
    tb = s.shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(runs if isinstance(runs, list) else [runs]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        for seg in (para if isinstance(para, list) else [(para, {})]):
            tx, o = seg if isinstance(seg, tuple) else (seg, {})
            r = p.add_run(); r.text = tx; f = r.font
            f.name = o.get("font", font); f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold); f.color.rgb = rgb(o.get("color", color))
            rpr = r._r.get_or_add_rPr(); rpr.set("lang", "zh-TW")
            rpr.append(rpr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}ea", {"typeface": o.get("font", font)}))
    return tb


def line(s, x1, y1, x2, y2, color=LINE, width=1.25):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(width)
    return c


def notes(s, body):
    s.notes_slide.notes_text_frame.text = body


page = [0]
TOTAL = 8


def header(s, kicker, title, accent=BLUE):
    page[0] += 1
    box(s, 0, 0, W, H, fill=BG)
    box(s, 0, 0, W, 0.08, fill=accent)
    text(s, 0.6, 0.38, 8, 0.3, kicker, size=12, color=accent, bold=True, spacing=1.0)
    text(s, 0.6, 0.66, 11.5, 0.6, title, size=32, bold=True, spacing=1.1)
    text(s, 0.6, 7.08, 9, 0.25, "融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架", size=10, color="8A97AB", spacing=1.0)
    text(s, W - 1.6, 7.08, 1.0, 0.25, f"{page[0]:02d} / {TOTAL:02d}", size=10, color="8A97AB", align=PP_ALIGN.RIGHT, spacing=1.0, font="Segoe UI")


STAGE_C = [BLUE, TEAL, VIOLET, AMBER, ORANGE, INK]
STAGE_L = ["資料輸入", "17 類偵測", "Top-5 檢索", "AI 稽核", "受控處置", "事件輸出"]

# ================================================================ 1 cover
s = prs.slides.add_slide(blank); page[0] += 1
box(s, 0, 0, W, H, fill="FFFFFF")
box(s, 0, 0, W, 0.1, fill=BLUE)
box(s, 8.7, 0.1, W - 8.7, H - 0.1, fill=BG)
text(s, 0.8, 0.9, 7.6, 0.3, "2026 第 31 屆大專校院資訊應用服務創新競賽　·　資安技術組　·　決賽", size=12, color=BLUE, bold=True, spacing=1.0)
text(s, 0.8, 1.55, 7.7, 2.7, [[("融合新型", {}), ("內容相依時序方向模型", {"color": BLUE})],
                              [("入侵偵測與", {}), ("任務導向檢索增強稽核", {"color": BLUE})],
                              [("之 AI 資安框架", {})]], size=34, bold=True, spacing=1.3)
box(s, 0.82, 4.45, 1.3, 0.06, fill=BLUE)
text(s, 0.8, 4.7, 7.6, 0.8, TITLE_EN, size=13, color=MUTED, spacing=1.3, font="Segoe UI")
for k, (v, l) in enumerate([("98.08%", "17 類偵測 Accuracy"), ("96.76%", "任務檢索 Top-5"), ("6 / 6", "隔離情境完整回復")]):
    x = 0.8 + k * 2.55
    line(s, x, 5.9, x + 2.25, 5.9, LINE, 1.25)
    text(s, x, 6.0, 2.4, 0.5, v, size=24, bold=True, color=[BLUE, VIOLET, TEAL][k], spacing=1.0, font="Segoe UI")
    text(s, x, 6.5, 2.4, 0.3, l, size=12, color=MUTED, spacing=1.0)
text(s, 9.2, 0.9, 3.6, 0.3, "端到端事件鏈", size=14, bold=True, color=MUTED, spacing=1.0)
for k, (lab, sub) in enumerate([("資料輸入", "PCAP・鏡像流量"), ("17 類偵測", "CTBM ＋ PBCNN"), ("Top-5 檢索", "529 維任務向量"),
                                ("AI 稽核", "支持・複核・不確定"), ("受控處置", "Policy Guard・TTL"), ("事件輸出", "雜湊鏈回條")]):
    y = 1.45 + k * 0.93
    if k < 5:
        line(s, 9.48, y + 0.58, 9.48, y + 1.07, "C9D3E3", 2)
    box(s, 9.26, y + 0.14, 0.44, 0.44, fill=PANEL, line=STAGE_C[k], shape=MSO_SHAPE.OVAL, lw=2)
    text(s, 9.26, y + 0.22, 0.44, 0.3, f"{k + 1}", size=12, bold=True, color=STAGE_C[k], align=PP_ALIGN.CENTER, spacing=1.0, font="Segoe UI")
    text(s, 9.95, y + 0.08, 3.0, 0.35, lab, size=16, bold=True, spacing=1.0)
    text(s, 9.95, y + 0.43, 3.0, 0.3, sub, size=12, color=MUTED, spacing=1.0)
notes(s, "【0:00–0:10】各位評審好，我們的作品是「融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架」。"
         "一句話：把只有標籤的告警，變成可查證、可稽核、可回復的事件鏈。")

# ================================================================ 2 problem -> solution
s = prs.slides.add_slide(blank)
header(s, "01　問題與解方", "告警只有標籤，查證與處置全靠人工")
for k, (v, l, c) in enumerate([("缺乏佐證", "告警只給類別與分數", RED), ("查證耗時", "人工調閱日誌比對", AMBER), ("誤阻斷風險", "手動下規則、撤銷易遺漏", ORANGE)]):
    x = 0.6 + k * 4.08
    rbox(s, x, 1.55, 3.88, 0.95, fill=PANEL, line=LINE)
    box(s, x, 1.55, 0.08, 0.95, fill=c)
    text(s, x + 0.3, 1.66, 3.5, 0.4, v, size=20, bold=True, color=c, spacing=1.0)
    text(s, x + 0.3, 2.08, 3.5, 0.3, l, size=14, color=MUTED, spacing=1.0)
s.shapes.add_picture(str(FIG / "fig_problem.png"), E(0.6), E(2.7), E(12.13), E(12.13 * 1232 / 3520))
text(s, 0.6, 6.78, 12.1, 0.3, "本框架以同一事件識別碼串接偵測、證據、稽核與處置，任何一段未通過檢核即降級為人工複核。", size=14, color=MUTED, spacing=1.0)
notes(s, "【0:10–0:35】校園與企業每天有大量告警，一般 IDS 只輸出攻擊類別，後面的查證、處置與確認恢復都靠人工，"
         "告警一多就慢，也容易誤阻斷。我們把這四段人工接力，換成四個有依據、可回溯的自動化步驟。")

# ================================================================ 3 architecture
s = prs.slides.add_slide(blank)
header(s, "02　系統架構", "四階段端到端架構：從原始流量到可回復處置")
fw = 10.55; fh = fw * 1848 / 3520
s.shapes.add_picture(str(FIG / "fig_architecture.png"), E((W - fw) / 2), E(1.45), E(fw), E(fh))
notes(s, "【0:35–1:20】這是完整架構。① 原始流量組成雙向 Flow、去識別化，轉成內容位元組、時間差與方向三種輸入。"
         "② CTBM 讀內容、時序與方向，PBCNN 補短窗位元組，經溫度校準與 OOF Gate 輸出固定 17 類。"
         "③ 512 維表徵加 17 維機率組成 529 維任務向量，從訓練案例庫取回 Top-5，再由本機大語言模型三態稽核。"
         "④ Policy Guard 檢查白名單與門檻後才套用規則，讀回驗證並 30 秒到期自動回復。下方是貫穿全程的同一事件識別碼。")

# ================================================================ 4 innovations
s = prs.slides.add_slide(blank)
header(s, "03　核心技術創新", "三項創新，各自解決一個關鍵瓶頸")
cards = [
    (BLUE, "01", "內容相依時序方向偵測", "解決：只有標籤、少數類別判不準",
     ["CTBM：內容×時間差×方向", "PBCNN：短窗位元組模式", "溫度校準＋OOF Gate 融合", "class-F1 guard 保護少數類別"], "93.05%", "Macro-F1（17 類）"),
    (VIOLET, "02", "任務導向證據檢索", "解決：判定沒有可回查依據",
     ["529 維任務向量＝表徵 ∥ 機率", "L2 正規化＋餘弦相似度", "只查訓練資料案例庫", "檢索中位數 1.01 ms"], "96.76%", "Top-5 命中率"),
    (TEAL, "03", "受控 AI 稽核與可回復處置", "解決：AI 幻覺與誤阻斷",
     ["本機 LLM 三態證據稽核", "AI 不覆寫分類、不產生指令", "Policy Guard 白名單＋門檻", "TTL 到期撤銷與回復驗證"], "95.83%", "改良 RAG 錯誤攔截率"),
]
for k, (c, n, t_, why, pts, kpi, kl) in enumerate(cards):
    x = 0.6 + k * 4.08
    rbox(s, x, 1.55, 3.88, 5.3, fill=PANEL, line=LINE, radius=0.04)
    box(s, x, 1.55, 3.88, 0.07, fill=c)
    text(s, x + 0.3, 1.8, 1.0, 0.45, n, size=24, bold=True, color=c, spacing=1.0, font="Segoe UI")
    text(s, x + 0.3, 2.3, 3.4, 0.4, t_, size=20, bold=True, spacing=1.0)
    text(s, x + 0.3, 2.78, 3.4, 0.3, why, size=14, color=MUTED, spacing=1.0)
    for j, p in enumerate(pts):
        yy = 3.3 + j * 0.5
        box(s, x + 0.32, yy + 0.1, 0.12, 0.12, fill=c, shape=MSO_SHAPE.OVAL)
        text(s, x + 0.58, yy, 3.2, 0.35, p, size=16, spacing=1.0)
    rbox(s, x + 0.25, 5.5, 3.38, 1.15, fill=BG, line=None, radius=0.1)
    text(s, x + 0.45, 5.6, 3.0, 0.6, kpi, size=30, bold=True, color=c, spacing=1.0, font="Segoe UI")
    text(s, x + 0.45, 6.2, 3.0, 0.3, kl, size=14, color=MUTED, spacing=1.0)
notes(s, "【1:20–2:00】三項創新各解決一個瓶頸：第一，內容相依時序方向偵測，17 類 Macro-F1 93.05%；"
         "第二，任務導向檢索，讓每個判定都有 Top-5 案例可回查，命中率 96.76%；"
         "第三，AI 只做證據稽核、不覆寫分類，處置交給 Policy Guard 並且一定可回復，錯誤攔截率 95.83%。接著用影片看一筆事件的實際輸入與輸出。")

# ================================================================ 5 video
s = prs.slides.add_slide(blank)
header(s, "04　系統展示", "Packet Tracer 模擬：一筆事件的輸入、處理與輸出")
vw = 9.6; vh = vw * 9 / 16
rbox(s, 0.55, 1.4, vw + 0.1, vh + 0.1, fill=PANEL, line=LINE, radius=0.02)
s.shapes.add_movie(str(VIDEO), E(0.6), E(1.45), E(vw), E(vh), poster_frame_image=str(POSTER), mime_type="video/mp4")
x0 = 10.55
text(s, x0, 1.45, 2.3, 0.35, "影片段落 · 60 秒", size=16, bold=True, color=MUTED, spacing=1.0)
for k, (lab, d) in enumerate(zip(STAGE_L, ["Mirror-TAP · 流量→張量", "IDS-Server · 17 類機率", "RAG-Store · Top-5", "LLM-Judge · 稽核 JSON", "Policy-Guard · ACL・回復", "Event Record · 匯出"])):
    y = 1.95 + k * 0.78
    box(s, x0, y + 0.06, 0.22, 0.22, fill=STAGE_C[k], shape=MSO_SHAPE.OVAL)
    text(s, x0 + 0.35, y, 2.3, 0.3, lab, size=16, bold=True, spacing=1.0)
    text(s, x0 + 0.35, y + 0.33, 2.3, 0.3, d, size=12, color=MUTED, spacing=1.0)
notes(s, "【2:00–3:05】點擊播放影片（60 秒，Packet Tracer 模擬模式）。旁白重點：輸入是原始流量，處理是雙分支偵測、任務檢索、AI 稽核與受控處置，"
         "輸出是 17 類機率、Top-5 證據、結構化 JSON 稽核與網路處置回條。Bot 事件實測：攻擊型測試交易成功率 100% 降到 0%，"
         "背景服務 100% 保留，30.12 秒到期撤銷後完整回復。影片同時是網路不穩時的備案。")

# ================================================================ 6 results


def chart(s, x, y, w, h, cats, series, colors, xmin, xmax):
    data = CategoryChartData(); data.categories = list(reversed(cats))
    for name, vals in reversed(series):
        data.add_series(name, list(reversed(vals)))
    ch = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, E(x), E(y), E(w), E(h), data).chart
    ch.has_title = False; ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.TOP; ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(12); ch.legend.font.name = FONT; ch.legend.font.color.rgb = rgb(MUTED)
    va = ch.value_axis; va.minimum_scale, va.maximum_scale = xmin, xmax
    va.has_major_gridlines = True; va.major_gridlines.format.line.color.rgb = rgb("E3E8F0")
    va.format.line.fill.background(); va.tick_labels.font.size = Pt(11); va.tick_labels.font.color.rgb = rgb(MUTED)
    ca = ch.category_axis; ca.tick_labels.font.size = Pt(14); ca.tick_labels.font.name = FONT; ca.tick_labels.font.color.rgb = rgb(INK)
    ca.format.line.color.rgb = rgb(LINE)
    pl = ch.plots[0]; pl.gap_width = 60; pl.overlap = -10; pl.has_data_labels = True
    dl = pl.data_labels; dl.number_format = "0.00"; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(12); dl.font.bold = True; dl.font.color.rgb = rgb(INK)
    for sr, c in zip(pl.series, list(reversed(colors))):
        sr.format.fill.solid(); sr.format.fill.fore_color.rgb = rgb(c)


s = prs.slides.add_slide(blank)
header(s, "05　實驗成果", "與基準方法相比，偵測與稽核皆明顯領先")
kp = [("98.08%", "Accuracy", "17 類 · 18,998 筆", BLUE), ("93.05%", "Macro-F1", "17 類 · 18,998 筆", BLUE),
      ("96.76%", "Top-5", "1,550 案例 / 463 查詢", VIOLET), ("94.25%", "MRR@5", "1,550 案例 / 463 查詢", VIOLET)]
for k, (v, l, sc, c) in enumerate(kp):
    x = 0.6 + k * 3.06
    rbox(s, x, 1.5, 2.86, 1.25, fill=PANEL, line=LINE, radius=0.08)
    text(s, x + 0.25, 1.58, 2.5, 0.6, v, size=30, bold=True, color=c, spacing=1.0, font="Segoe UI")
    text(s, x + 0.25, 2.17, 2.5, 0.3, l, size=14, bold=True, spacing=1.0, font="Segoe UI")
    text(s, x + 0.25, 2.43, 2.5, 0.3, sc, size=11, color=MUTED, spacing=1.0)
for k, (ttl, sub) in enumerate([("偵測模組比較（%）", "相同測試設定"), ("檢索稽核比較（%）", "Fine-11 配對 1,830 筆")]):
    x = 0.6 + k * 6.12
    rbox(s, x, 2.95, 5.92, 3.95, fill=PANEL, line=LINE, radius=0.04)
    text(s, x + 0.25, 3.07, 4, 0.35, ttl, size=16, bold=True, spacing=1.0)
    text(s, x + 3.17, 3.1, 2.5, 0.3, sub, size=11, color=MUTED, align=PP_ALIGN.RIGHT, spacing=1.0)
chart(s, 0.75, 3.45, 5.6, 3.4, ["PBCNN-20", "SPIN-IDS-15", "OOF Gate（本作）"], [("Accuracy", [90.06, 96.00, 97.89]), ("Macro-F1", [87.91, 91.69, 93.03])], [BLUE, "93C5FD"], 80, 100)
chart(s, 6.87, 3.45, 5.6, 3.4, ["No-RAG", "原始 RAG", "改良 RAG（本作）"], [("Judge 準確率", [93.44, 93.72, 98.85]), ("錯誤攔截率", [48.15, 52.31, 95.83])], [VIOLET, "F59E0B"], 0, 110)
notes(s, "【3:05–3:45】成果：17 類偵測 Accuracy 98.08%、Macro-F1 93.05%；任務檢索 Top-5 96.76%、MRR@5 94.25%。"
         "相同設定下 OOF Gate 比 PBCNN-20 的 Macro-F1 高 5.12 個百分點；加入改良 RAG 後，錯誤攔截率從 48.15% 提升到 95.83%，約兩倍。")

# ================================================================ 7 advantages / feasibility
s = prs.slides.add_slide(blank)
header(s, "06　競爭優勢與落地可行性", "可以直接部署、可驗證、可擴充")
adv = [
    (BLUE, "穩定性", ["AI 改寫分類 0 / 463 筆", "稽核 JSON 有效率 463 / 463", "任一檢核失敗即轉人工複核"]),
    (TEAL, "成熟度", ["17 類即時重跑 17 / 17", "6 / 6 隔離情境背景服務保留", "6 / 6 情境 30 秒到期完整回復"]),
    (VIOLET, "完整性", ["偵測→證據→稽核→處置→回條", "事件 ID 與執行 ID 雙重綁定", "雜湊鏈紀錄可匯出稽核"]),
    (ORANGE, "擴充性", ["封存檔或鏡像流量，免改原架構", "模型、案例庫、白名單獨立更新", "全程本機推論，外部 API 0 次"]),
]
for k, (c, t_, pts) in enumerate(adv):
    x, y = 0.6 + (k % 2) * 4.0, 1.5 + (k // 2) * 2.7
    rbox(s, x, y, 3.82, 2.5, fill=PANEL, line=LINE, radius=0.05)
    box(s, x, y + 0.25, 0.07, 0.5, fill=c)
    text(s, x + 0.3, y + 0.22, 3.3, 0.45, t_, size=20, bold=True, color=c, spacing=1.0)
    for j, p in enumerate(pts):
        text(s, x + 0.3, y + 0.85 + j * 0.5, 3.45, 0.35, [[("✓  ", {"color": c, "bold": True, "font": "Segoe UI Symbol"}), (p, {})]], size=14, spacing=1.0)
rbox(s, 8.75, 1.5, 3.98, 5.2, fill=PANEL, line=LINE, radius=0.04)
text(s, 9.05, 1.68, 3.5, 0.4, "與典型方案比較", size=18, bold=True, spacing=1.0)
cmp_ = [("告警內容", "類別＋分數", "17 類＋校準信心"), ("判定依據", "人工查找", "Top-5 案例證據"), ("AI 角色", "開放式建議", "限定證據稽核"),
        ("執行方式", "直接下規則", "白名單劇本"), ("安全控制", "手動撤銷", "TTL・讀回・回復")]
text(s, 9.05, 2.22, 1.2, 0.3, "面向", size=11, color=MUTED, spacing=1.0)
text(s, 10.2, 2.22, 1.2, 0.3, "典型", size=11, color=MUTED, spacing=1.0)
text(s, 11.35, 2.22, 1.3, 0.3, "本框架", size=11, color=BLUE, bold=True, spacing=1.0)
for j, (a, b, c_) in enumerate(cmp_):
    y = 2.6 + j * 0.8
    line(s, 9.05, y - 0.08, 12.45, y - 0.08, LINE, 1)
    text(s, 9.05, y + 0.08, 1.15, 0.5, a, size=13, bold=True, spacing=1.1)
    text(s, 10.2, y + 0.08, 1.15, 0.5, b, size=12, color=MUTED, spacing=1.1)
    text(s, 11.35, y + 0.08, 1.3, 0.6, c_, size=12, color=BLUE, bold=True, spacing=1.1)
notes(s, "【3:45–4:35】落地可行性對應四個面向：穩定性，AI 從不改寫分類、輸出格式 100% 有效；成熟度，17 類即時重跑、6 種隔離情境全部完整回復；"
         "完整性，一個事件 ID 串起所有紀錄；擴充性，直接吃封存檔或鏡像流量，模型、案例庫、白名單都能獨立更新，而且全程本機推論。")

# ================================================================ 8 closing
s = prs.slides.add_slide(blank); page[0] += 1
box(s, 0, 0, W, H, fill="FFFFFF")
box(s, 0, 0, W, 0.1, fill=BLUE)
box(s, 0, H - 2.35, W, 2.35, fill=BG)
text(s, 0.8, 0.9, 6, 0.3, "結語", size=14, bold=True, color=BLUE, spacing=1.0)
text(s, 0.8, 1.4, 11.8, 1.6, [[("讓每一筆告警，", {})], [("都有依據、有證據、可回復。", {"color": BLUE})]], size=40, bold=True, spacing=1.3)
for k, (t_, d, c) in enumerate([("偵測有依據", "內容相依時序方向判定 · 固定 17 類", BLUE), ("稽核有證據", "529 維任務向量 · Top-5 案例證據", VIOLET), ("處置可回復", "Policy Guard · 讀回驗證 · 自動回復", TEAL)]):
    x = 0.8 + k * 4.0
    box(s, x, 3.55, 0.08, 0.95, fill=c)
    text(s, x + 0.3, 3.55, 3.5, 0.45, t_, size=22, bold=True, color=c, spacing=1.0)
    text(s, x + 0.3, 4.05, 3.6, 0.35, d, size=14, color=MUTED, spacing=1.0)
text(s, 0.8, 5.55, 11.8, 0.4, "融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架", size=16, bold=True, spacing=1.0)
text(s, 0.8, 6.0, 11.8, 0.35, "感謝聆聽　敬請指教", size=20, color=BLUE, bold=True, spacing=1.0)
notes(s, "【4:35–5:00】總結：偵測有依據、稽核有證據、處置可回復。感謝評審聆聽，敬請指教。")

prs.save(OUT)
print("saved", OUT, len(prs.slides), "slides")
