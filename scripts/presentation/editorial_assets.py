"""Build the evidence-chain presentation art with the shared icon, palette and font system."""
from pathlib import Path
from html import escape
import json
import sys
from style_contract import TYPOGRAPHY, font_runs, icon_fragment, resolve_colors

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from media_results import load_metrics
DEST = ROOT / 'deliverables/source'
PROJECT = ROOT / 'projects/finals_editorial_ppt169_20261028'
PALETTE = json.loads((ROOT/'design-system/palette.json').read_text(encoding='utf-8'))
NAVY, BLUE, TEAL, GOLD = (PALETTE[key] for key in ('navy', 'blue', 'teal', 'gold'))
INK, MUTED, LINE, GRAY, WHITE = (PALETTE[key] for key in ('ink', 'muted', 'line', 'gray', 'white'))
BLUE_TINT, TEAL_TINT, BLUE_MUTED = (PALETTE[key] for key in ('blue_tint', 'teal_tint', 'blue_muted'))
NIGHT_PANEL, NIGHT_LINE, CYAN, DARK_MUTED = (PALETTE[key] for key in ('night_panel', 'night_line', 'cyan', 'on_dark_muted'))
FONT = TYPOGRAPHY['latin']
PAGE_NUMBERS = {1:1, 6:2, 2:3, 3:4, 4:5, 5:6, 7:7, 8:8, 9:9}
# Icons drawn on the night canvas swap their light fills for night surfaces.
ON_DARK = {'white':'night_panel', 'blue':'cyan', 'gray':'night_line', 'blue_tint':'night_panel', 'line':'night_line'}


def text(x, y, value, size=22, color=INK, weight=400, anchor='start'):
    runs=''.join(f'<tspan font-family="{family}">{escape(part)}</tspan>' for part, family in font_runs(value))
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{runs}</text>'


def rect(x, y, w, h, fill=GRAY, radius=10, stroke='none', width=1):
    edge=f' stroke-width="{width}"' if stroke!='none' else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"{edge}/>'


def circle(cx, cy, r, fill=WHITE, stroke='none', width=2):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def rule(x1, y1, x2, y2, color=LINE, width=1.5, dashed=False):
    dash=' stroke-dasharray="5 5"' if dashed else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"{dash}/>'


def arrow(points, color=BLUE, dashed=False, width=2.5):
    path='M'+' L'.join(f'{x} {y}' for x,y in points)
    (px,py),(x,y)=points[-2:]
    if x>px: head=f'M{x-8} {y-6}L{x} {y}L{x-8} {y+6}'
    elif x<px: head=f'M{x+8} {y-6}L{x} {y}L{x+8} {y+6}'
    elif y>py: head=f'M{x-6} {y-8}L{x} {y}L{x+6} {y-8}'
    else: head=f'M{x-6} {y+8}L{x} {y}L{x+6} {y+8}'
    dash=' stroke-dasharray="6 5"' if dashed else ''
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"{dash}/>'
            f'<path d="{head}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def chevron(x, y, color=BLUE_MUTED):
    return f'<path d="M{x-4} {y-8}L{x+4} {y}L{x-4} {y+8}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'


def icon(name, x, y, size, dark=False):
    return f'<g transform="translate({x} {y}) scale({size/64})">{icon_fragment(name, **(ON_DARK if dark else {}))}</g>'


def svg(body, height=720, bg=WHITE):
    return resolve_colors(f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="{height}" viewBox="0 0 1280 {height}" font-family="{FONT}">{rect(0,0,1280,height,bg,0)}{body}</svg>')


def glyph(kind, x, y, size=64, stroke=BLUE, fill=WHITE, soft=BLUE_MUTED):
    """Qualitative object illustrations: no data values are encoded."""
    def line(a,b,c,d,color=stroke,width=2.5):
        return f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
    body=''
    if kind=='packet':
        body=rect(5,15,54,36,fill,5,stroke,2.5)+line(5,15,32,35)+line(32,35,59,15)
    elif kind=='clock':
        body=circle(32,32,25,fill,stroke,2.5)+line(32,32,32,15)+line(32,32,45,39)
    elif kind=='firewall':
        body=rect(5,8,54,48,fill,4,stroke,2.5)
        for yy in (24,40):body+=line(5,yy,59,yy,soft,2)
        for xx,a,b in [(23,8,24),(43,8,24),(15,24,40),(37,24,40),(23,40,56),(43,40,56)]:body+=line(xx,a,xx,b,soft,2)
    elif kind=='server':
        for j in range(3):body+=rect(9,7+j*18,46,14,fill,3,stroke,2.5)+circle(47,14+j*18,2,stroke,stroke,1)+line(15,14+j*18,35,14+j*18,soft,2)
    elif kind=='document':
        body=rect(12,5,40,54,fill,4,stroke,2.5)
        for yy in (18,29,40,51):body+=line(21,yy,44,yy,soft,2)
    elif kind=='vector':
        body=line(12,7,5,7)+line(5,7,5,57)+line(5,57,12,57)+line(52,7,59,7)+line(59,7,59,57)+line(59,57,52,57)
        for yy in (16,27,38,49):body+=rect(18,yy-3,28,6,soft,2)
    elif kind=='search':
        body=circle(26,26,19,fill,stroke,2.5)+line(40,40,58,58,stroke,5)
    elif kind=='check':
        body=circle(32,32,26,TEAL_TINT if fill==WHITE else fill,stroke,2.5)+line(19,33,28,42,stroke,4)+line(28,42,46,22,stroke,4)
    elif kind=='review':
        body=circle(26,26,17,fill,stroke,2.5)+line(39,39,56,56,stroke,4)
    elif kind=='question':
        body=circle(32,32,26,BLUE_TINT if fill==WHITE else fill,stroke,2.5)+line(32,44,32,45,stroke,5)+f'<path d="M24 24C24 14 40 14 40 24C40 31 32 31 32 37" fill="none" stroke="{stroke}" stroke-width="4" stroke-linecap="round"/>'
    else:
        body=rect(12,12,40,40,fill,5,stroke,2.5)+rect(23,23,18,18,BLUE_TINT,2,stroke,2)
        for v in (20,32,44):body+=line(v,3,v,12)+line(v,52,v,61)+line(3,v,12,v)+line(52,v,61,v)
    return f'<g transform="translate({x} {y}) scale({size/64})">{body}</g>'


def node(x, y, w, h, title, sub='', tone='plain', size=19):
    """A labelled card; tone marks the stage output (teal) or a neutral step."""
    fill, stroke, color = {'plain':(WHITE,LINE,INK), 'out':(TEAL_TINT,'none',TEAL), 'key':(BLUE_TINT,'none',BLUE)}[tone]
    body=rect(x,y,w,h,fill,10,stroke)
    if sub:
        body+=text(x+16,y+h/2-3,title,size,color,700)+text(x+16,y+h/2+20,sub,14,MUTED)
    else:
        body+=text(x+w/2,y+h/2+7,title,size,color,700,'middle')
    return body


STAGES=[('network','流量表徵','前處理張量'),('model','互補判定','CTBM＋PBCNN'),('retrieval','證據稽核','Top-5＋本機 AI'),('shield','受控回復','策略·讀回·到期')]


def architecture(save=True, oy=24):
    """Four lanes, read left to right; every lane hands the same event ID forward."""
    s=''
    xs=[64+i*294 for i in range(4)]
    for i,(name,title,sub) in enumerate(STAGES):
        x=xs[i]
        s+=circle(x+22,oy+22,22,BLUE_TINT)+icon(name,x+8,oy+8,28)
        s+=text(x+56,oy+16,f'0{i+1}',13,TEAL,700)+text(x+82,oy+16,sub,13,MUTED)
        s+=text(x+56,oy+40,title,21,NAVY,700)
        if i<3:s+=chevron(x+282,oy+22)
        s+=rect(x,oy+60,270,312,GRAY,14)
    x=xs[0]
    s+=node(x+16,oy+78,238,62,'真實前處理張量','遮罩欄位 · 流量切窗')
    s+=text(x+16,oy+170,'三種線索',14,MUTED,700)
    for k,label in enumerate(['內容','時間差','方向']):
        s+=rect(x+16+k*82,oy+182,74,40,WHITE,8,LINE)+text(x+53+k*82,oy+208,label,16,INK,700,'middle')
    s+=arrow([(x+135,oy+226),(x+135,oy+272)])
    s+=node(x+16,oy+276,238,62,'流量表徵','送入兩個互補模型','out')
    x=xs[1]
    s+=node(x+16,oy+78,222,58,'CTBM','內容 · 時間差 · 方向')+node(x+16,oy+150,222,58,'PBCNN','短窗位元組模式')
    s+=arrow([(x+238,oy+107),(x+256,oy+107),(x+256,oy+251),(x+240,oy+251)])+rule(x+238,oy+179,x+256,oy+179,BLUE,2.5)
    s+=node(x+16,oy+222,222,58,'校準＋OOF Gate','依事件證據融合','key')
    s+=arrow([(x+127,oy+280),(x+127,oy+296)])
    s+=node(x+16,oy+298,238,58,'17 類正式判定','信心 ＋ 512 維表徵','out')
    x=xs[2]
    s+=node(x+16,oy+78,238,58,'529 維任務向量','512 表徵 ＋ 17 機率 · L2')
    s+=arrow([(x+135,oy+136),(x+135,oy+152)])
    s+=rect(x+16,oy+154,238,74,WHITE,10,LINE)+text(x+32,oy+180,'Top-5 相似案例',19,INK,700)
    for k in range(5):s+=rect(x+32+k*30,oy+194,24,22,BLUE_TINT,4)+text(x+44+k*30,oy+210,str(k+1),13,BLUE,700,'middle')
    s+=text(x+188,oy+210,'訓練庫',13,MUTED)
    s+=arrow([(x+135,oy+228),(x+135,oy+244)])
    s+=node(x+16,oy+246,238,50,'本機 AI 稽核','')
    for k,label in enumerate(['支持','複核','不確定']):
        s+=rect(x+16+k*82,oy+308,74,48,TEAL_TINT,10)+text(x+53+k*82,oy+339,label,16,TEAL,700,'middle')
    x=xs[3]
    for k,(label,tone) in enumerate([('策略檢查','plain'),('套用規則','plain'),('讀回驗證','plain'),('到期回復','out')]):
        s+=node(x+16,oy+78+k*66,238,50,label,'',tone)
        if k<3:s+=arrow([(x+135,oy+128+k*66),(x+135,oy+144+k*66)])
    s+=text(x+135,oy+354,'複核／不確定 → 監測或蒐證',14,MUTED,400,'middle')
    s+=rect(64,oy+392,1152,48,NAVY,12)
    for x in xs:
        s+=rule(x+135,oy+372,x+135,oy+392,BLUE_MUTED,1.5,True)+circle(x+135,oy+392,5,GOLD)
    s+=text(640,oy+423,'同一事件 ID 串起  正式判定 · Top-5 證據 · AI 稽核結論 · 處置回條',19,WHITE,700,'middle')
    if save:(DEST/'architecture.svg').write_text(svg(s,oy+464),encoding='utf-8')
    return s


def group(key, body):
    bounds={'headline':'64 36 1152 100','footer':'64 664 1152 44','page-content':'0 140 1280 520'}.get(key)
    bound=f' data-pptx-bounds="{bounds}"' if bounds else ''
    return f'<g id="{key}"{bound}>{body}</g>'


def graphic_page(n, title, body, kicker='METHOD', role='content', dark=False, canvas=None):
    title_color, kicker_color, footer_color, rail = (WHITE, CYAN, DARK_MUTED, NIGHT_LINE) if dark else (NAVY, TEAL, MUTED, LINE)
    heading=rect(64,50,10,10,GOLD,2)+text(84,60,kicker,15,kicker_color,700)
    if title:heading+=text(64,114,title,38,title_color,700)
    current=PAGE_NUMBERS[n]-1 if n<=9 else n-10
    progress=''.join(rect(916+k*20,688,14,4,GOLD if k==current else rail,2) for k in range(9 if n<=9 else 3))
    label=f'{PAGE_NUMBERS[n]:02d} / 09' if n<=9 else f'答詢備用 {n-9} / 3'
    footer=rule(64,672,1216,672,rail,1)+text(64,697,'AI 資安框架 · 資安技術組決賽',14,footer_color)+progress+text(1216,697,label,14,footer_color,700,'end')
    bg=canvas or (NAVY if dark else WHITE)
    background=rect(0,0,1280,720,bg,0).replace('<rect ','<rect id="page-background" data-pptx-role="background" ',1)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="{FONT}" data-pptx-page-role="{role}">{background}{group("headline",heading)}{group("page-content",body)}{group("footer",footer)}</svg>'


def evidence_chain(y, labels, dark=True, x0=98, step=210):
    """The brand motif: four stages strung on one line, the same event moving through."""
    stroke, panel, title, sub = (CYAN, NIGHT_PANEL, WHITE, DARK_MUTED) if dark else (BLUE, WHITE, NAVY, MUTED)
    s=rule(x0,y,x0+step*(len(labels)-1),y,NIGHT_LINE if dark else LINE,2)
    for i,(name,label,detail) in enumerate(labels):
        cx=x0+i*step
        s+=circle(cx,y,36,panel,stroke,2)
        s+=icon(name,cx-19,y-19,38,dark) if name in ('network','model','retrieval','shield') else glyph(name,cx-19,y-19,38,stroke,panel,DARK_MUTED if dark else BLUE_MUTED)
        s+=text(cx,y+70,label,22,title,700,'middle')+text(cx,y+98,detail,15,sub,400,'middle')
    return s


def build_pages(limit=12):
    out=PROJECT/'svg_output';out.mkdir(parents=True,exist_ok=True)
    detector=json.loads((ROOT/'results/detection_17class.json').read_text(encoding='utf-8'))
    m=load_metrics(ROOT)
    pages=[]
    # P01: light cover matching the film canvas; the formal name, then the four-stage chain the talk follows.
    s=''
    for k,l in enumerate(['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架']):s+=text(64,206+k*62,l,44,BLUE if k==2 else NAVY,700)
    s+=rect(64,350,56,4,GOLD,2)+text(64,400,'從流量判定，走到有證據、可回復的處置。',24,MUTED)
    s+=evidence_chain(512,[('model','偵測','17 類互補判定'),('retrieval','檢索','Top-5 訓練案例'),('document','稽核','本機 AI 三態'),('shield','回復','讀回＋到期回復')],False)
    s+=f'<g transform="translate(912 150) scale(4.6)">{icon_fragment("framework")}</g>'
    pages.append(graphic_page(1,'',s,'2026 資安技術組 · 決賽','cover',canvas=GRAY))
    # P02 (source order): the four-lane architecture.
    pages.append(graphic_page(2,'一個框架，四個連續階段',architecture(False,150),'FRAMEWORK'))
    # P03: two complementary paths, one calibrated output.
    s=rect(64,150,280,300,GRAY,14)+text(88,190,'同一流量輸入',18,TEAL,700)
    for j,label in enumerate(['封包內容','時間差','方向']):
        y=246+j*70
        s+=text(88,y,label,21,INK,700)+rect(222,y-26,98,34,WHITE,6)
        for z in range(5):s+=rect(232+z*16,y-20+(0 if j!=1 else 12-z*3),9,22 if j!=1 else 10+z*3,BLUE,2)
    s+=arrow([(344,300),(372,300),(372,218),(400,218)])+arrow([(372,300),(372,383),(400,383)])
    for y,name,sub,desc,art in [(150,'CTBM','內容 · 時序 · 方向','讀取流量的時序關係','model'),(316,'PBCNN','短窗位元組模式','補充局部內容特徵','packet')]:
        s+=rect(400,y,360,134,WHITE,14,LINE)+rect(400,y+24,4,86,BLUE,2)
        s+=(icon('model',428,y+33,68) if art=='model' else glyph('packet',428,y+33,68))
        s+=text(520,y+52,name,28,BLUE,700)+text(520,y+84,sub,18,INK)+text(520,y+110,desc,15,MUTED)
    s+=arrow([(760,218),(790,218),(790,300),(820,300)])+arrow([(760,383),(790,383),(790,300)])
    s+=rect(820,196,396,208,TEAL_TINT,16)+text(850,250,'校準＋OOF Gate',30,TEAL,700)+text(850,292,'依事件證據融合',21,INK)+text(850,328,'形成同一次正式判定',18,MUTED)
    s+=text(850,378,f'Macro-F1 {m["macro_f1"]["OOF Gate"]*100:.2f}%',18,TEAL,700)+text(1010,378,'見第 07 頁',15,MUTED)
    s+=arrow([(1018,404),(1018,486)])+rect(64,488,1152,72,NAVY,14)
    s+=text(640,532,'17 類判定  ＋  校準信心  ＋  模型表徵   →   後段檢索與稽核',22,WHITE,700,'middle')
    s+=text(64,612,'兩個模型讀同一筆流量：CTBM 看時序與方向，PBCNN 看短窗位元組，再由 Gate 依證據融合。',17,MUTED)
    pages.append(graphic_page(3,'互補模型，形成同一次判定',s,'DETECTION'))
    # P04: vector composition is qualitative, not a falsely scaled 512:17 chart.
    cols=[64,467,870]
    s=''
    for i,title in enumerate(['組合任務向量','找出相似案例','本機 AI 稽核']):
        s+=text(cols[i],172,f'STEP 0{i+1}',14,TEAL,700)+text(cols[i],204,title,24,NAVY,700)
        if i<2:s+=arrow([(cols[i]+352,380),(cols[i+1]-16,380)],BLUE_MUTED)
    x=cols[0]
    s+=rect(x,232,346,66,WHITE,12,LINE)+glyph('vector',x+18,243,44)+text(x+80,278,'512 維表徵',21,INK,700)
    s+=text(x+173,330,'＋',26,BLUE,700,'middle')
    s+=rect(x,344,346,66,WHITE,12,LINE)+glyph('vector',x+18,355,44)+text(x+80,390,'17 維類別機率',21,INK,700)
    s+=arrow([(x+173,410),(x+173,444)])
    s+=rect(x,446,346,96,TEAL_TINT,14)+text(x+173,490,'529 維任務向量',27,TEAL,700,'middle')+text(x+173,523,'L2 正規化後檢索',17,MUTED,400,'middle')
    x=cols[1]
    s+=icon('retrieval',x,236,92)+text(x+112,270,'訓練案例庫',22,INK,700)+text(x+112,302,f'{m["bank_rows"]:,} 筆案例',18,MUTED)
    for i in range(5):s+=rect(x+i*70,350,60,84,BLUE_TINT if i else BLUE,10)+text(x+30+i*70,402,str(i+1),26,WHITE if not i else BLUE,700,'middle')
    s+=text(x,474,'Top-5 相似案例',22,INK,700)+text(x,504,'只檢索訓練資料，依相似度排序',16,MUTED)
    x=cols[2]
    s+=rect(x,232,346,92,BLUE_TINT,14)+text(x+173,272,'判定＋案例證據',24,BLUE,700,'middle')+text(x+173,304,'核對同一事件',17,MUTED,400,'middle')
    s+=arrow([(x+173,324),(x+173,340),(x+57,340),(x+57,356)])+arrow([(x+173,340),(x+173,356)])+arrow([(x+173,340),(x+289,340),(x+289,356)])
    for i,(label,art) in enumerate([('支持','check'),('複核','review'),('不確定','question')]):
        s+=rect(x+i*120,358,106,100,WHITE,12,LINE)+glyph(art,x+i*120+35,370,36,TEAL if not i else BLUE)+text(x+i*120+53,440,label,19,INK,700,'middle')
    s+=text(x,494,'保留正式分類',22,INK,700)+text(x,524,'稽核結論附回事件紀錄',16,MUTED)
    s+=rect(64,584,1152,56,GRAY,12)+circle(92,612,6,GOLD)+text(112,619,'同一事件 ID：分類結果與檢索證據一路可追溯。',20,INK,700)
    pages.append(graphic_page(4,'把偵測表徵，變成可核對的證據',s,'EVIDENCE'))
    # P05: four object illustrations explain controlled execution and expiry.
    s=''
    stages=[('政策檢查','範圍 · 允許動作 · 期限','shield'),('套用規則','受允許策略才執行','firewall'),('讀回驗證','核對規則與事件回條','document'),('到期回復','撤銷並確認服務恢復','clock')]
    for i,(label,detail,kind) in enumerate(stages):
        x=64+i*294
        s+=rect(x,156,270,250,TEAL_TINT if i==3 else WHITE,16,'none' if i==3 else LINE)
        s+=text(x+24,190,f'0{i+1}',16,TEAL,700)
        s+=icon('shield',x+87,206,96) if kind=='shield' else glyph(kind,x+87,206,96)
        s+=text(x+135,346,label,26,TEAL if i==3 else NAVY,700,'middle')+text(x+135,378,detail,16,MUTED,400,'middle')
        if i<3:s+=chevron(x+282,281)
    s+=arrow([(160,406),(160,456),(410,456)],BLUE_MUTED,True,2)
    s+=rect(424,430,792,52,GRAY,12)+glyph('document',444,438,36)+text(496,464,'複核／不確定  →  不自動處置，改為監測或蒐證',19,INK,700)
    s+=rule(64,520,1216,520)
    s+=text(64,566,f'{m["network_cases"]} 種隔離 TCP 情境',26,NAVY,700)+text(64,600,f'{m["rules_cases"]} 種套用規則、{m["passive_cases"]} 種監測或蒐證',18,MUTED)
    s+=text(64,632,'隔離交易與回復驗證，不等同原生攻擊防禦率',15,MUTED)
    for i,(value,label) in enumerate([(f'{m["background"]}/{m["network_cases"]}','背景服務保留'),(f'{m["rollback"]}/{m["network_cases"]}','到期回復完整')]):
        x=760+i*228
        s+=text(x,606,value,56,TEAL,700)+text(x,636,label,16,MUTED)
    pages.append(graphic_page(5,'受控執行，留下可回復的處置紀錄',s,'CONTROL'))
    # P06: native 16:9 movie frame; embedded in the packaging pass.
    s=rect(192,151,896,504,NAVY,16)+circle(640,376,44,NIGHT_PANEL,CYAN,2)+'<path d="M628 356L658 376L628 396Z" fill="#5EEAD4"/>'
    s+=text(640,470,'產品方法動畫',30,WHITE,700,'middle')+text(640,508,'30 秒 · 2 倍速',20,DARK_MUTED,400,'middle')
    pages.append(graphic_page(6,'一個事件，走完完整流程',group('video-slot',s),'METHOD FILM'))
    # P07: genuine zero-baseline comparison. Plot domain 0..100, x=200..820.
    s=text(64,176,f'相同 {m["detection_n"]:,} 筆封存測試 · Macro-F1',18,MUTED)
    chart=''
    for tick in [0,50,100]:
        x=200+620*tick/100
        chart+=rule(x,206,x,498,LINE,1)+text(x,528,f'{tick}%',15,MUTED,400,'middle')
    marks=''
    for i,name in enumerate(['PBCNN','CTBM','OOF Gate']):
        value=detector[name]['macro_f1']*100
        y=232+i*92
        best=i==2
        marks+=text(64,y+33,name,22,TEAL if best else INK,700)
        marks+=rect(200,y,620*value/100,48,TEAL if best else BLUE_MUTED,6)
        marks+=text(200+620*value/100+14,y+33,f'{value:.2f}%',24,TEAL if best else INK,700)
    chart+='<!-- chart-plot-area: object=detector-comparison | 200,206,820,498 -->'+marks
    s+=group('detector-comparison',group('detector-comparison-chartArea',chart))
    s+=rect(916,176,300,340,NAVY,18)+text(946,226,'整體準確率',18,DARK_MUTED)
    s+=text(946,306,f"{detector['OOF Gate']['accuracy']*100:.2f}%",62,CYAN,700)+text(946,348,'17 類分類 · OOF Gate',18,WHITE)
    s+=rule(946,396,1186,396,NIGHT_LINE,1)+text(946,436,'同一封存測試集',16,DARK_MUTED)+text(946,466,'固定 17 類輸出',16,DARK_MUTED)
    s+=rect(64,572,1152,64,TEAL_TINT,12)
    s+=text(92,612,f'融合相較 PBCNN 提升 {m["gain_pbcnn"]:.2f} 個百分點；相較 CTBM 提升 {m["gain_ctbm"]:.2f} 個百分點。',20,INK,700)
    pages.append(graphic_page(7,'互補融合，提升整體辨識效果',s,'RESULT · DETECTION'))
    # P08: outcomes form a qualitative branch; card area does not encode counts.
    s=rect(64,164,380,388,GRAY,18)+text(94,206,'檢索效果',16,TEAL,700)
    s+=text(94,286,f'{m["top5"]*100:.2f}%',62,TEAL,700)+text(94,320,'Top-5 命中率',19,INK,700)
    s+=rule(94,354,414,354)+text(94,414,f'{m["mrr5"]*100:.2f}%',42,NAVY,700)+text(94,444,'MRR@5 排序品質',18,INK)
    s+=text(94,516,f'{m["bank_rows"]:,} 案例 ／ {m["queries"]} 查詢 · 重疊 {m["overlap"]}',15,MUTED)
    s+=rect(500,164,716,62,NAVY,14)+text(858,204,f'{m["queries"]} 筆事件  →  本機 AI 稽核',22,WHITE,700,'middle')
    s+=arrow([(858,226),(858,252),(612,252),(612,276)])+arrow([(858,252),(858,276)])+arrow([(858,252),(1104,252),(1104,276)])
    for i,(value,label,art) in enumerate([(str(m['support']),'支持','check'),(str(m['review']),'複核','review'),(str(m['uncertain']),'不確定','question')]):
        x=500+i*246
        s+=rect(x,278,224,196,TEAL_TINT if not i else WHITE,16,'none' if not i else LINE)
        s+=glyph(art,x+90,296,44,TEAL if not i else BLUE)+text(x+112,400,value,52,TEAL if not i else NAVY,700,'middle')+text(x+112,442,label,19,INK,700,'middle')
    s+=text(500,516,f'支持精確率 {m["support_precision"]*100:.2f}% · 正式分類保持可追溯',18,MUTED)
    s+=rect(64,580,1152,58,BLUE_TINT,12)+text(92,617,f'{m["intercepted"]} / {m["errors"]}',24,BLUE,700)
    s+=text(176,617,f'筆偵測誤判分流至複核或不確定；其餘 {m["false_support"]} 筆仍獲支持，處置另經策略檢查。',19,INK)
    pages.append(graphic_page(8,'案例提供證據，AI 完成分流',s,'RESULT · EVIDENCE'))
    # P09: light ending with the actual linked artifacts, rather than slogans alone.
    s=text(64,196,'偵測有依據，稽核有證據，處置可回復。',30,BLUE,700)
    s+=evidence_chain(318,[('document','正式判定','17 類＋信心'),('search','檢索證據','Top-5 訓練案例'),('check','稽核結論','支持／複核／不確定'),('clock','處置回條','讀回＋到期回復')],False,180,307)
    s+=rect(64,480,1152,56,WHITE,14,LINE)+text(640,516,'同一事件 ID，串起分類、證據、判斷與回復紀錄。',21,NAVY,700,'middle')
    s+=text(64,592,f'{m["live_classes"]} 類真實張量重跑 · {m["network_cases"]} 種隔離 TCP 情境驗證',19,MUTED)
    s+=text(1216,630,'感謝聆聽，敬請指教。',30,NAVY,700,'end')
    pages.append(graphic_page(9,'一套可展示、可查核的資安框架',s,'AI SECURITY FRAMEWORK','ending',canvas=GRAY))
    pages=[pages[i] for i in [0,5,1,2,3,4,6,7,8]]
    qa=[('創新在哪裡？與一般 IDS 加上 RAG 有何不同？', '529 維', '任務導向證據向量', '正式分類保留 · 稽核證據可追溯 · 策略可回復'), ('如何證明前段判斷與後段處置已經串起來？', '同一 ID', '事件與執行可追溯', '分類、Top-5、Judge、策略與回條綁定同一事件'), ('評估資料如何切分？案例庫是否洩漏測試答案？', '0', '訓練／查詢重疊', '訓練庫只讀 · 查詢不重疊 · AI 不看真實標籤'), ('AI 若支持錯誤判斷，如何避免直接誤封？', f'{m["intercepted"]} / {m["errors"]}', '偵測誤判分流', f'{m["false_support"]} 筆為支持統計；處置與回復另以隔離情境驗證'), (f'{m["rollback"]}/{m["network_cases"]} 是否代表各種真實攻擊都能完全防住？', f'{m["rollback"]} / {m["network_cases"]}', '背景保留與回復', f'{m["rollback"]}/{m["network_cases"]} 驗證服務保留與回復；不等同真實攻擊防禦率'), ('如何部署、保護資料，並接到既有環境？', '0', '外部 API 呼叫', '本機 AI 稽核；私有權重、輸入及逐筆回覆不公開')]
    def qa_node(x,y,w,label,fill=WHITE,size=19):
        return rect(x,y,w,46,fill,10,LINE if fill==WHITE else 'none')+text(x+w/2,y+30,label,size,INK,700,'middle')

    for page_index in range(3):
        content=''
        for slot in range(2):
            qi=page_index*2+slot
            question,metric,metric_label,proof=qa[qi]
            y=150+slot*256
            content+=rect(64,y,1152,236,GRAY,16)+rect(960,y,256,236,TEAL_TINT,16)
            content+=rect(88,y+22,54,30,NAVY,15)+text(115,y+43,f'Q{qi+1}',16,WHITE,700,'middle')+text(158,y+44,question,22,INK,700)
            d=y+8
            if qi==0:
                for j,(name,label) in enumerate([('model','互補判定'),('retrieval','529 維檢索'),('document','AI 稽核'),('shield','策略與回復')]):
                    x=88+j*212
                    content+=circle(x+94,d+108,40,WHITE)+(icon(name,x+70,d+84,48) if name!='document' else glyph('document',x+70,d+84,48))+text(x+94,d+174,label,18,INK,700,'middle')
                    if j<3:content+=arrow([(x+144,d+108),(x+256,d+108)],BLUE_MUTED)
            elif qi==1:
                for j,label in enumerate(['正式類別','Top-5 案例','稽核結論','處置回條']):
                    x=88+j*212
                    content+=glyph('document',x+72,d+66,46)+text(x+94,d+136,label,18,INK,700,'middle')
                    if j<3:content+=arrow([(x+128,d+90),(x+268,d+90)],BLUE_MUTED)
                content+=rect(88,d+152,800,34,BLUE_TINT,10)+text(488,d+175,'同一 event_id  ＋  同次 execution_id',18,BLUE,700,'middle')
            elif qi==2:
                content+=icon('retrieval',176,d+70,70)+text(211,d+168,f'訓練案例 {m["bank_rows"]:,}',19,INK,700,'middle')
                content+=glyph('search',462,d+72,64)+text(494,d+168,'Top-5 檢索',19,BLUE,700,'middle')
                content+=glyph('document',760,d+74,60)+text(790,d+168,f'測試查詢 {m["queries"]}',19,INK,700,'middle')
                content+=arrow([(280,d+106),(450,d+106)],BLUE_MUTED)+arrow([(744,d+106),(540,d+106)],BLUE_MUTED)
            elif qi==3:
                content+=qa_node(88,d+104,150,f'{m["errors"]} 筆誤判')
                content+=arrow([(238,d+127),(272,d+127),(272,d+89),(306,d+89)],BLUE_MUTED)+arrow([(272,d+127),(272,d+151),(306,d+151)],BLUE_MUTED)
                content+=qa_node(306,d+66,240,f'{m["intercepted"]} 複核／不確定')+qa_node(306,d+128,240,f'{m["false_support"]} 仍支持')
                content+=arrow([(546,d+89),(600,d+89)],BLUE_MUTED)+arrow([(546,d+151),(600,d+151)],BLUE_MUTED)
                content+=qa_node(600,d+66,288,'監測／蒐證',BLUE_TINT)+qa_node(600,d+128,288,'若觸發 → 策略檢查',BLUE_TINT,18)
            elif qi==4:
                content+=rect(88,d+64,330,120,WHITE,12,LINE)+text(253,d+92,'隔離 TCP 測試床',18,INK,700,'middle')+glyph('server',124,d+104,40)+glyph('firewall',233,d+104,40)+glyph('server',342,d+104,40)
                content+=arrow([(166,d+124),(231,d+124)])+arrow([(275,d+124),(340,d+124)])+text(253,d+170,f'{m["rules_cases"]} 規則＋{m["passive_cases"]} 監測',16,BLUE,700,'middle')
                content+=arrow([(418,d+124),(450,d+124),(450,d+93),(480,d+93)],BLUE_MUTED)+arrow([(450,d+124),(450,d+153),(480,d+153)],BLUE_MUTED)
                content+=qa_node(480,d+70,408,f'背景服務保留 {m["background"]} / {m["network_cases"]}',BLUE_TINT)+qa_node(480,d+130,408,f'回復完整性 {m["rollback"]} / {m["network_cases"]}',BLUE_TINT)
            else:
                content+=rect(88,d+62,800,118,WHITE,12,LINE)+text(110,d+90,'本機工作站 · GPU 模型與案例庫',17,BLUE,700)
                for j,(art,label) in enumerate([('document','欄位遮罩'),('model','17 類推論'),('retrieval','檢索＋AI'),('shield','策略回條')]):
                    x=104+j*196
                    content+=rect(x,d+108,170,52,GRAY,10)+(glyph('document',x+8,d+114,40) if art=='document' else icon(art,x+8,d+114,40))+text(x+106,d+141,label,17,INK,700,'middle')
                    if j<3:content+=chevron(x+183,d+134)
            content+=text(88,y+222,proof,15,TEAL,700)
            content+=text(1088,y+124,metric,46,TEAL,700,'middle')+text(1088,y+162,metric_label,16,MUTED,400,'middle')
        pages.append(graphic_page(10+page_index,['答詢圖解｜創新與整合','答詢圖解｜評估與誤判','答詢圖解｜效果與部署'][page_index],content,'JUDGES · Q&A'))
    for i,p in enumerate(pages[:limit]):(out/f'{i+1:02d}_slide.svg').write_text(resolve_colors(p),encoding='utf-8')
    print(f'Authored {min(limit,len(pages))} graphical slides; all static.')


if __name__ == '__main__':
    architecture();build_pages(int(sys.argv[1]) if len(sys.argv)>1 else 12)
