"""Python-drawn figures for the deck and docs. All shapes/icons are vector primitives (matplotlib)."""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon, FancyArrowPatch, Wedge, Ellipse, Arc
from matplotlib import font_manager

for f in ("C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjhbd.ttc"):
    font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Microsoft JhengHei", "Segoe UI Symbol", "DejaVu Sans"]
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

INK, MUTED, LINE = "#0B1B33", "#5B6B82", "#C9D3E3"
STAGE = [  # (header, fill, border)
    ("#1D4ED8", "#EEF4FF", "#B9CCF6"),
    ("#0F766E", "#ECF8F5", "#A9DCD2"),
    ("#6D28D9", "#F4F0FE", "#CFC0F5"),
    ("#C2410C", "#FFF4EC", "#F5C9A8"),
]


def rbox(ax, x, y, w, h, fc="white", ec=LINE, lw=1.2, r=1.2, z=2, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


def t(ax, x, y, s, size=9, c=INK, w="normal", ha="center", va="center", z=6, **kw):
    ax.text(x, y, s, fontsize=size, color=c, fontweight=w, ha=ha, va=va, zorder=z, **kw)


def arrow(ax, x1, y1, x2, y2, c=MUTED, lw=1.6, z=5, style="-|>", ms=10, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms, color=c, lw=lw, zorder=z, ls=ls, shrinkA=0, shrinkB=0))


# ---------------------------------------------------------------- icons
def ic_doc(ax, x, y, c, label=None, s=1.0):
    w, h = 3.6 * s, 4.6 * s
    ax.add_patch(Polygon([(x - w/2, y - h/2), (x + w/2, y - h/2), (x + w/2, y + h/2 - 1.1*s), (x + w/2 - 1.1*s, y + h/2), (x - w/2, y + h/2)], closed=True, fc="white", ec=c, lw=1.6, zorder=7))
    if label:
        t(ax, x, y - 0.3*s, label, 6.2*s, c, "bold", z=8)


def ic_db(ax, x, y, c, s=1.0):
    w, h = 4.0 * s, 4.2 * s
    ax.add_patch(Rectangle((x - w/2, y - h/2), w, h, fc="white", ec="none", zorder=7))
    for k in (0, 1, 2):
        ax.add_patch(Ellipse((x, y - h/2 + k*h/2), w, 1.3*s, fc="white" if k < 2 else c + "33", ec=c, lw=1.5, zorder=8 + k))
    ax.plot([x - w/2, x - w/2], [y - h/2, y + h/2], color=c, lw=1.5, zorder=8)
    ax.plot([x + w/2, x + w/2], [y - h/2, y + h/2], color=c, lw=1.5, zorder=8)


def ic_shield(ax, x, y, c, s=1.0, check=True):
    pts = [(x, y + 2.4*s), (x + 2.1*s, y + 1.5*s), (x + 1.9*s, y - 0.8*s), (x, y - 2.5*s), (x - 1.9*s, y - 0.8*s), (x - 2.1*s, y + 1.5*s)]
    ax.add_patch(Polygon(pts, closed=True, fc=c + "22", ec=c, lw=1.6, zorder=7))
    if check:
        ax.plot([x - 0.9*s, x - 0.15*s, x + 1.0*s], [y, y - 0.8*s, y + 0.8*s], color=c, lw=2.0, zorder=8, solid_capstyle="round")


def ic_robot(ax, x, y, c, s=1.0):
    rbox(ax, x - 2.0*s, y - 1.6*s, 4.0*s, 3.0*s, fc="white", ec=c, lw=1.6, r=0.7*s, z=7)
    for dx in (-0.85, 0.85):
        ax.add_patch(Circle((x + dx*s, y - 0.05*s), 0.38*s, fc=c, zorder=8))
    ax.plot([x, x], [y + 1.4*s, y + 2.2*s], color=c, lw=1.5, zorder=7)
    ax.add_patch(Circle((x, y + 2.35*s), 0.32*s, fc=c, zorder=8))
    ax.plot([x - 0.7*s, x + 0.7*s], [y - 0.95*s, y - 0.95*s], color=c, lw=1.4, zorder=8)


def ic_clock(ax, x, y, c, s=1.0, frac=0.75):
    ax.add_patch(Circle((x, y), 2.0*s, fc="white", ec=c, lw=1.6, zorder=7))
    ax.add_patch(Wedge((x, y), 1.6*s, 90 - 360*frac, 90, fc=c + "40", ec="none", zorder=8))
    ax.plot([x, x], [y, y + 1.3*s], color=c, lw=1.6, zorder=9)
    ax.plot([x, x + 0.9*s], [y, y], color=c, lw=1.6, zorder=9)


def ic_gear(ax, x, y, c, s=1.0):
    n = 8; pts = []
    for k in range(n * 2):
        a = np.pi * k / n; r = (2.0 if k % 2 == 0 else 1.55) * s
        for da in (-0.17, 0.17):
            pts.append((x + r*np.cos(a + da), y + r*np.sin(a + da)))
    ax.add_patch(Polygon(pts, closed=True, fc=c + "22", ec=c, lw=1.4, zorder=7))
    ax.add_patch(Circle((x, y), 0.65*s, fc="white", ec=c, lw=1.4, zorder=8))


def ic_rollback(ax, x, y, c, s=1.0):
    ax.add_patch(Arc((x, y), 3.8*s, 3.8*s, theta1=40, theta2=330, color=c, lw=2.0, zorder=7))
    a = np.deg2rad(40); ex, ey = x + 1.9*s*np.cos(a), y + 1.9*s*np.sin(a)
    ax.add_patch(Polygon([(ex - 0.2*s, ey + 0.9*s), (ex + 0.8*s, ey - 0.3*s), (ex - 0.6*s, ey - 0.5*s)], closed=True, fc=c, zorder=8))


def ic_swap(ax, x, y, c, s=1.0):
    arrow(ax, x - 2.0*s, y + 0.7*s, x + 2.0*s, y + 0.7*s, c=c, lw=2.0, ms=11*s, z=8)
    arrow(ax, x + 2.0*s, y - 0.7*s, x - 2.0*s, y - 0.7*s, c=c, lw=2.0, ms=11*s, z=8)


def ic_lock(ax, x, y, c, s=1.0):
    ax.add_patch(Arc((x, y + 0.6*s), 2.4*s, 3.0*s, theta1=0, theta2=180, color=c, lw=1.8, zorder=7))
    rbox(ax, x - 1.7*s, y - 1.8*s, 3.4*s, 2.6*s, fc=c + "22", ec=c, lw=1.6, r=0.4*s, z=8)
    ax.add_patch(Circle((x, y - 0.5*s), 0.35*s, fc=c, zorder=9))


# ---------------------------------------------------------------- mini charts
def mini_heat(ax, x, y, w, h, cmap="Blues", rows=10, cols=18, seed=0):
    m = np.full((rows, cols),0.35)
    m[:, :4] *= 0.4
    ax.imshow(m, extent=(x, x + w, y, y + h), cmap=cmap, aspect="auto", zorder=7, vmin=0, vmax=1, interpolation="nearest")
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=LINE, lw=0.8, zorder=8))


def mini_bars(ax, x, y, w, h, vals, c, hi=None, hc=None):
    n = len(vals); bw = w / n
    for k, v in enumerate(vals):
        ax.add_patch(Rectangle((x + k*bw + bw*0.15, y), bw*0.7, h*v, fc=(hc if k == hi else c), ec="none", zorder=7))
    ax.plot([x, x + w], [y, y], color=LINE, lw=0.8, zorder=7)


def mini_seq(ax, x, y, w, h, c1, c2, n=20, seed=3):
    for k in range(n):
        up = k % 2 == 0; v = 0.7
        ax.add_patch(Rectangle((x + k*w/n, y + (h/2 if up else h/2 - h/2*v)), w/n*0.7, h/2*v, fc=c1 if up else c2, ec="none", zorder=7))
    ax.plot([x, x + w], [y + h/2, y + h/2], color=MUTED, lw=0.6, zorder=8)


# ================================================================ architecture
def architecture():
    fig = plt.figure(figsize=(16, 8.4), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 84); ax.axis("off")
    t(ax, 80, 81, "AI 資安框架　系統架構：判定、證據與可回復處置的四階段事件鏈", 15, INK, "bold")
    heads = ["① 資料輸入與前處理", "② 內容相依時序方向偵測", "③ 任務導向檢索與 AI 稽核", "④ 受控處置與回復驗證"]
    subs = ["流量前處理 → 真實輸入張量", "CTBM ＋ PBCNN → 17 類機率", "529 維任務向量 → Top-5 → 三態", "Policy Guard → 套用・讀回・Rollback"]
    X = [2, 41.5, 81, 120.5]; W = 37.5; Y0, H0 = 14, 63
    for i, x in enumerate(X):
        hc, fc, ec = STAGE[i]
        rbox(ax, x, Y0, W, H0, fc=fc, ec=ec, lw=1.4, r=1.8, z=1)
        rbox(ax, x, Y0 + H0 - 6.2, W, 6.2, fc=hc, ec=hc, r=1.8, z=2)
        ax.add_patch(Rectangle((x, Y0 + H0 - 6.2), W, 2.5, fc=hc, ec="none", zorder=2))
        t(ax, x + W/2, Y0 + H0 - 2.6, heads[i], 11.5, "white", "bold")
        t(ax, x + W/2, Y0 + H0 - 4.95, subs[i], 7.6, "#FFFFFFDD")
        if i < 3:
            arrow(ax, x + W + 0.2, 45, X[i+1] - 0.2, 45, c=STAGE[i+1][0], lw=2.6, ms=18)

    def card(x, y, w, h, title, c, sub=None):
        rbox(ax, x, y, w, h, fc="white", ec=c + "66", lw=1.0, r=1.0, z=3)
        t(ax, x + 1.0, y + h - 1.5, title, 8.3, INK, "bold", ha="left")
        if sub:
            t(ax, x + 1.0, y + 1.3, sub, 6.6, MUTED, ha="left")

    # ---- stage 1
    c = STAGE[0][0]; x = X[0]
    card(x + 1.5, 57.5, 16.5, 11.6, "原始流量", c, "PCAP／鏡像埠")
    ic_doc(ax, x + 6.2, 62.5, c, "PCAP", 0.95); ic_doc(ax, x + 12.8, 62.5, c, "Mirror", 0.95)
    card(x + 19.5, 57.5, 16.5, 11.6, "雙向 Flow 組裝", c, "5-tuple・時間序")
    ic_swap(ax, x + 27.7, 62.6, c, 1.15)
    card(x + 1.5, 43.5, 16.5, 12.0, "去識別化", c, "IP／Port 移除")
    ic_lock(ax, x + 9.7, 49.3, c, 1.0)
    card(x + 19.5, 43.5, 16.5, 12.0, "內容張量結構", c, "前20封包 × bytes")
    mini_heat(ax, x + 20.6, 46.6, 14.3, 6.0, "Blues", seed=1)
    card(x + 1.5, 28.5, 34.5, 13.0, "時序與方向輸入格式", c, "↑ 用戶端→服務端　↓ 服務端→用戶端")
    mini_seq(ax, x + 3.0, 31.8, 31.5, 6.6, c, "#93C5FD")
    rbox(ax, x + 1.5, 16, 34.5, 10.5, fc=c + "12", ec=c, lw=1.0, r=1.0, z=3, ls="--")
    t(ax, x + 18.75, 23.6, "輸出：模型輸入張量", 8.6, c, "bold")
    t(ax, x + 18.75, 19.4, "內容 bytes ＋ Δt ＋ 方向，雙資料集同格式", 7.2, INK)

    # ---- stage 2
    c = STAGE[1][0]; x = X[1]
    card(x + 1.5, 52.0, 16.5, 17.1, "CTBM", c, "內容・時序・方向")
    for k in range(4):
        rbox(ax, x + 3.6, 55.0 + k*2.6, 12.3, 2.0, fc=c + ("22" if k % 2 else "44"), ec=c, lw=0.8, r=0.4, z=6)
    t(ax, x + 9.75, 59.0, "Transformer × Blue Heat", 6.4, INK, z=8)
    card(x + 19.5, 52.0, 16.5, 17.1, "PBCNN", c, "短窗位元組模式")
    for k, (hh, ww) in enumerate([(9, 2.4), (7, 2.4), (5, 2.4), (3, 2.4)]):
        ax.add_patch(Rectangle((x + 21.8 + k*3.3, 59.6 - hh/2), ww, hh, fc=c + ["33", "55", "77", "AA"][k], ec=c, lw=0.8, zorder=6))
    card(x + 1.5, 38.0, 16.5, 12.0, "溫度校準", c, "降低過度自信")
    xs = np.linspace(0, 1, 40)
    ax.plot(x + 3 + xs*13.5, 41.7 + (xs**3)*6.2, color="#9CA3AF", lw=1.2, zorder=7)
    ax.plot(x + 3 + xs*13.5, 41.7 + xs*6.2, color=c, lw=1.8, zorder=7)
    card(x + 19.5, 38.0, 16.5, 12.0, "OOF Gate", c, "59 項證據＋F1 guard")
    ax.add_patch(Polygon([(x + 24.0, 47.6), (x + 31.5, 44.4), (x + 24.0, 41.2)], closed=True, fc=c + "33", ec=c, lw=1.4, zorder=7))
    t(ax, x + 26.6, 44.4, "g", 9, c, "bold", z=8, style="italic")
    arrow(ax, x + 9.75, 51.8, x + 9.75, 50.2, c=c); arrow(ax, x + 27.75, 51.8, x + 27.75, 50.2, c=c)
    card(x + 1.5, 16, 34.5, 20.0, "輸出：17 類正式機率", c, "BENIGN … Heartbleed；保留 512 維表徵")
    for k in range(17):
        xx=x+3.1+k*1.8
        ax.add_patch(Rectangle((xx,29.0),1.4,2.6,fc=c+"22",ec=c,lw=0.5,zorder=6))
        t(ax,xx+0.7,30.3,str(k),5,c)
    t(ax,x+18.75,26.8,"固定類別順序 → 每類機率與校準信心",7.2,c,"bold")
    t(ax,x+18.75,23.6,"512維表徵 → 後段任務檢索",7.2,INK)

    # ---- stage 3
    c = STAGE[2][0]; x = X[2]
    card(x + 1.5, 57.0, 34.5, 12.1, "529 維任務向量", c, "512 維流量表徵 ∥ 17 維機率 → L2 正規化")
    for k in range(32):
        ax.add_patch(Rectangle((x + 3.0 + k*0.84, 61.0), 0.74, 3.6, fc=plt.cm.Purples(0.55), ec="none", zorder=7))
    for k in range(6):
        ax.add_patch(Rectangle((x + 30.4 + k*0.84, 61.0), 0.74, 3.6, fc=plt.cm.Oranges(0.55), ec="none", zorder=7))
    t(ax, x + 16.2, 66.0, "512", 6.5, c); t(ax, x + 32.7, 66.0, "17", 6.5, "#C2410C")
    card(x + 1.5, 39.5, 12.5, 15.4, "案例庫", c, "train-only")
    ic_db(ax, x + 7.75, 47.6, c, 1.05)
    card(x + 15.5, 39.5, 20.5, 15.4, "Top-5 相似案例", c, "餘弦相似度")
    for k in range(5):
        yy=50.9-k*1.85
        t(ax,x+17.2,yy,f"#{k+1}",6.0,MUTED,ha="left")
        t(ax,x+19.4,yy,"案例ID・類別・相似度",5.8,c,ha="left")
    arrow(ax, x + 14.0, 47.2, x + 15.4, 47.2, c=c)
    card(x + 1.5, 16, 34.5, 21.5, "AI Judge 證據稽核", c, "本機 LLM・結構化 JSON・不覆寫分類")
    ic_robot(ax, x + 8.0, 27.6, c, 1.25)
    for k, (lab, col) in enumerate([("支持 support", "#0F766E"), ("複核 review", "#B45309"), ("不確定 uncertain", "#B45309")]):
        rbox(ax, x + 15.0, 30.6 - k*3.9, 19.0, 3.0, fc=col + "18", ec=col, lw=1.0, r=1.4, z=6)
        t(ax, x + 24.5, 32.1 - k*3.9, lab, 7.2, col, "bold")

    # ---- stage 4
    c = STAGE[3][0]; x = X[3]
    card(x + 1.5, 52.5, 16.5, 16.6, "Policy Guard", c, "白名單・範圍・風險")
    ic_shield(ax, x + 9.75, 61.0, c, 1.4)
    card(x + 19.5, 52.5, 16.5, 16.6, "處置門檻", c, "未通過 → 人工複核")
    for k, s_ in enumerate(["稽核 = 支持", "信心 ≥ 0.80", "Top-5 同類 ≥ 4"]):
        t(ax, x + 21.0, 64.6 - k*3.2, "✓", 8.5, "#0F766E", "bold", ha="left")
        t(ax, x + 23.2, 64.6 - k*3.2, s_, 7.2, INK, ha="left")
    card(x + 1.5, 36.0, 10.8, 14.2, "套用", c, "iptables")
    ic_gear(ax, x + 6.9, 43.6, c, 1.15)
    card(x + 13.35, 36.0, 10.8, 14.2, "讀回", c, "規則比對")
    ic_doc(ax, x + 18.75, 43.6, c, "✓", 0.95)
    card(x + 25.2, 36.0, 10.8, 14.2, "到期回復", c, "TTL 30 秒")
    ic_clock(ax, x + 30.6, 43.6, c, 1.05)
    arrow(ax, x + 12.3, 43.1, x + 13.3, 43.1, c=c); arrow(ax, x + 24.15, 43.1, x + 25.15, 43.1, c=c)
    card(x + 1.5, 16, 34.5, 17.8, "輸出：處置回條", c, "背景服務保留・回復驗證・雜湊鏈")
    ic_rollback(ax, x + 8.0, 24.6, c, 1.25)
    for k, s_ in enumerate(["事件 ID ＋ 執行 ID 綁定", "規則數、交易成功率", "撤銷時間與回復結果"]):
        t(ax, x + 14.5, 28.4 - k*3.0, "•  " + s_, 7.2, INK, ha="left")

    # ---- ledger band
    rbox(ax, 2, 2.2, 156, 9.4, fc="#F8FAFC", ec=LINE, lw=1.2, r=1.6, z=1)
    t(ax, 4.5, 6.9, "同一事件識別碼", 9.5, INK, "bold", ha="left")
    items = [("DetectionEvent", STAGE[0][0]), ("類別・信心・表徵", STAGE[1][0]), ("Top-5・稽核理由", STAGE[2][0]), ("策略・回條・Rollback", STAGE[3][0]), ("匯出 JSON 紀錄", INK)]
    for k, (s_, col) in enumerate(items):
        xx = 28 + k*26.5
        rbox(ax, xx, 4.4, 22.0, 5.0, fc="white", ec=col, lw=1.1, r=1.0, z=3)
        t(ax, xx + 11, 6.9, s_, 8.0, col, "bold")
        if k < 4:
            arrow(ax, xx + 22.2, 6.9, xx + 26.3, 6.9, c=MUTED, lw=1.3)
    fig.savefig(OUT / "fig_architecture.png", dpi=220, facecolor="white")
    plt.close(fig)


# ================================================================ before / after
def problem_solution():
    fig = plt.figure(figsize=(16, 5.6), dpi=220)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 160); ax.set_ylim(0, 56); ax.axis("off")
    rows = [("典型告警流程", "#9AA8BC", "#F3F5F9", [("只有攻擊標籤", "缺乏佐證"), ("人工查找相似事件", "耗時、依賴經驗"), ("手動下設備規則", "誤阻斷風險"), ("手動撤銷與確認", "規則殘留")], 33),
            ("本框架", "#1D4ED8", "#EEF4FF", [("17 類＋校準信心", "CTBM＋PBCNN"), ("自動 Top-5 證據", "529 維任務向量"), ("AI 三態稽核", "不覆寫正式分類"), ("限時處置＋自動回復", "Policy Guard")], 6)]
    for title, c, fc, steps, y in rows:
        rbox(ax, 2, y, 156, 18, fc=fc, ec=c + "88", lw=1.3, r=2.0, z=1)
        t(ax, 13, y + 9, title, 13, c if c != "#9AA8BC" else MUTED, "bold")
        for k, (a, b) in enumerate(steps):
            xx = 26 + k*33
            rbox(ax, xx, y + 3, 28, 12, fc="white", ec=c, lw=1.2, r=1.4, z=3)
            t(ax, xx + 14, y + 10.6, a, 11, INK, "bold")
            t(ax, xx + 14, y + 6.0, b, 9, MUTED)
            if k < 3:
                arrow(ax, xx + 28.3, y + 9, xx + 32.7, y + 9, c=c, lw=2, ms=14)
    for k, s_ in enumerate(["判定依據", "查證效率", "處置安全", "可追溯性"]):
        xx = 40 + k*33
        arrow(ax, xx, 32.6, xx, 24.4, c="#0F766E", lw=2.2, ms=16)
        rbox(ax, xx + 1.6, 26.6, 11.4, 4.2, fc="#ECF8F5", ec="#0F766E", lw=1, r=1.2, z=4)
        t(ax, xx + 7.3, 28.7, s_ + " ↑", 9, "#0F766E", "bold")
    fig.savefig(OUT / "fig_problem.png", dpi=220, facecolor="white")
    plt.close(fig)


architecture()
problem_solution()
print("figures ->", OUT)
