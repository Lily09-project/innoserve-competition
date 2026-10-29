"""Build light-canvas presentation art with the shared flat icon and font system."""
from pathlib import Path
from html import escape
import json
from PIL import Image
from style_contract import TYPOGRAPHY, font_runs, icon_fragment

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'deliverables/source'
PROJECT = ROOT / 'projects/finals_editorial_ppt169_20261028'
PALETTE = json.loads((ROOT/'design-system/palette.json').read_text(encoding='utf-8'))
BLUE, NAVY, GOLD = (PALETTE[key] for key in ('blue', 'navy', 'gold'))
FONT = TYPOGRAPHY['latin']
CJK_FONT = TYPOGRAPHY['cjk']
PAGE_NUMBERS = {1:1, 6:2, 2:3, 3:4, 4:5, 5:6, 7:7, 8:8, 9:9}
SY, OY = 1, 0


def text(x, y, value, size=26, color='#171C1D', weight=400, anchor='start'):
    runs=[]
    for part, family in font_runs(value):
        runs.append(f'<tspan font-family="{family}">{escape(part)}</tspan>')
    return f'<text x="{x}" y="{y*SY+OY}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{"".join(runs)}</text>'


def rect(x, y, w, h, fill='#F0F2F3', radius=8, stroke='none'):
    return f'<rect x="{x}" y="{y*SY+OY}" width="{w}" height="{h*SY}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(body, height=720, bg='#FFFFFF'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="{height}" viewBox="0 0 1280 {height}" font-family="{FONT}">{rect(0,0,1280,height,bg,0)}{body}</svg>'


def image(x, y, w, h, file):
    index = int(file.rsplit('-', 1)[1].split('.')[0])-1
    name = ('network', 'model', 'retrieval', 'shield')[index]
    return f'<g transform="translate({x} {y*SY+OY}) scale({w/64} {h*SY/64})">{icon_fragment(name)}</g>'


def split_icons():
    sheet = Image.open(DEST / 'security-icons-sheet.png').convert('RGBA')
    w, h = sheet.size
    for i in range(4):
        part = sheet.crop((i*w//4, 0, (i+1)*w//4, h))
        if i == 2:
            # Remove the isolated edge fragment of the neighbouring chip icon.
            part.paste((0,0,0,0),(0,0,60,h))
        bbox = part.getchannel('A').point(lambda a: 255 if a > 35 else 0).getbbox()
        part = part.crop(bbox)
        canvas = Image.new('RGBA', (600,600))
        part.thumbnail((530,530), Image.Resampling.LANCZOS)
        canvas.alpha_composite(part, ((600-part.width)//2,(600-part.height)//2))
        canvas.save(DEST / f'icon-{i+1}.png')


def architecture(save=True):
    # Two tiers preserve readable labels without stretching imagery. The IDS
    # branches are parallel; retrieval receives their final event representation.
    def route(points, color=BLUE, dashed=False):
        d='M'+' L'.join(f'{x} {y*SY+OY}' for x,y in points)
        (px,py),(x,y)=points[-2:]
        if x>px: tip=f'M{x-7} {y*SY+OY-5}L{x} {y*SY+OY}L{x-7} {y*SY+OY+5}'
        elif y>py: tip=f'M{x-5} {y*SY+OY-7}L{x} {y*SY+OY}L{x+5} {y*SY+OY-7}'
        else: tip=f'M{x-5} {y*SY+OY+7}L{x} {y*SY+OY}L{x+5} {y*SY+OY+7}'
        dash=' stroke-dasharray="5 4"' if dashed else ''
        return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"{dash}/><path d="{tip}" fill="none" stroke="{color}" stroke-width="2"/>'
    s=rect(16,16,226,205,'#F0F2F3',8,'#D6DDE0')
    s+=text(34,48,'a  流量表徵',24,BLUE,600)+image(190,20,34,34,'icon-1.png')
    s+=text(34,97,'真實前處理張量',21)+text(34,142,'封包內容',22)+text(34,174,'時間差·方向',22)
    s+=text(34,204,'遮罩欄位·流量切窗',20,'#53666E')
    s+=rect(266,16,998,205,'#F0F2F3',8,'#D6DDE0')
    s+=image(282,22,36,36,'icon-2.png')+text(328,48,'b  互補模型與 17 類判定',24,BLUE,600)
    for y,title,sub in [(70,'CTBM','內容·時間差·方向'),(148,'PBCNN','短窗位元組模式')]:
        s+=rect(292,y,300,60,'#FFFFFF',8,'#D6DDE0')+text(310,y+26,title,24,weight=600)+text(310,y+50,sub,20)
    s+=rect(660,90,278,90,'#FFFFFF',8,'#D6DDE0')+text(682,123,'校準＋OOF Gate',24,weight=600)+text(682,160,'依事件證據融合',22)
    s+=rect(966,90,276,90,'#FFFFFF',8,'#D6DDE0')+text(986,123,'17 類正式判定',24,weight=600)+text(986,160,'512 維表徵＋17 維機率',20)
    s+=route([(242,118),(280,118),(280,100),(292,100)])+route([(280,118),(280,178),(292,178)])
    s+=route([(592,100),(625,100),(625,135),(660,135)])+route([(592,178),(625,178),(625,135),(660,135)])+route([(938,135),(966,135)])
    s+=rect(16,282,840,186,'#F0F2F3',8,'#D6DDE0')+image(34,288,36,36,'icon-3.png')+text(80,314,'c  任務導向檢索與 AI 稽核',24,BLUE,600)
    for x,w,title,sub in [(40,190,'529 維任務向量','L2 正規化'),(260,244,'Top-5 相似案例','僅訓練資料案例庫'),(540,292,'本機 AI 稽核','支持／複核／不確定')]:
        s+=rect(x,340,w,82,'#FFFFFF',8,'#D6DDE0')+text(x+14,374,title,22,weight=600)+text(x+14,405,sub,20)
    s+=route([(1104,180),(1104,249),(5,249),(5,381),(40,381)])
    s+=text(620,240,'正式類別·信心·模型表徵',22,anchor='middle')
    s+=route([(230,381),(260,381)])+route([(504,381),(540,381)])
    s+=text(380,454,'訓練案例庫',20,'#53666E',anchor='middle')+route([(380,434),(380,422)],'#53666E',True)
    s+=text(554,454,'稽核保留正式分類',20,'#53666E')
    s+=rect(880,282,384,186,'#F0F2F3',8,'#D6DDE0')+image(898,287,36,36,'icon-4.png')+text(944,314,'d  受控處置與回復',24,BLUE,600)
    s+=text(904,364,'策略檢查 → 套用',24)+text(904,401,'讀回 → 到期撤銷',24)+text(904,451,'複核／不確定 → 蒐證',20,'#53666E')
    s+=route([(832,381),(880,381)])
    s+=rect(16,484,1248,38,'#F0F2F3',8,'#D6DDE0')+text(640,510,'共用事件 ID：正式判定｜Top-5 證據｜AI 稽核｜處置與回復回條',22,anchor='middle')
    standalone = svg(s,536).replace('../images/','')
    if save: (DEST/'architecture.svg').write_text(standalone,encoding='utf-8')
    return s


def group(key, body):
    bounds={'headline':'64 24 1152 110','footer':'64 660 1152 45','page-content':'0 140 1280 520'}.get(key)
    bound=f' data-pptx-bounds="{bounds}"' if bounds else ''
    return f'<g id="{key}"{bound}>{body}</g>'


def arrow(points, color=BLUE, dashed=False):
    path = 'M'+' L'.join(f'{x} {y}' for x,y in points)
    (px,py),(x,y)=points[-2:]
    if x>px: head=f'M{x-7} {y-5}L{x} {y}L{x-7} {y+5}'
    elif x<px: head=f'M{x+7} {y-5}L{x} {y}L{x+7} {y+5}'
    elif y>py: head=f'M{x-5} {y-7}L{x} {y}L{x+5} {y-7}'
    else: head=f'M{x-5} {y+7}L{x} {y}L{x+5} {y+7}'
    dash=' stroke-dasharray="6 5"' if dashed else ''
    return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"{dash}/><path d="{head}" fill="none" stroke="{color}" stroke-width="2.5"/>'


def glyph(kind,x,y,size=64):
    """Qualitative device/object illustrations: no data values are encoded."""
    def line(a,b,c,d,color=BLUE,width=2.5):
        return f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
    def circle(cx,cy,r,fill='none'):
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{BLUE}" stroke-width="2.5"/>'
    body=''
    if kind=='packet':
        body=rect(5,15,54,36,'#FFFFFF',5,BLUE)+line(5,15,32,35)+line(32,35,59,15)
    elif kind=='clock':
        body=circle(32,32,25,'#FFFFFF')+line(32,32,32,14)+line(32,32,46,39)
        body+=line(32,4,32,9)+line(32,55,32,60)
    elif kind=='firewall':
        body=rect(5,8,54,48,'#FFFFFF',4,BLUE)
        for yy in (24,40):body+=line(5,yy,59,yy,'#7294A9',2)
        for xx,a,b in [(23,8,24),(43,8,24),(15,24,40),(37,24,40),(23,40,56),(43,40,56)]:body+=line(xx,a,xx,b,'#7294A9',2)
    elif kind=='server':
        for j in range(3):body+=rect(9,7+j*18,46,14,'#FFFFFF',3,BLUE)+circle(47,14+j*18,2,BLUE)+line(15,14+j*18,35,14+j*18,'#7294A9',2)
    elif kind=='document':
        body=rect(12,5,40,54,'#FFFFFF',4,BLUE)
        for yy in (18,29,40,51):body+=line(21,yy,44,yy,'#7294A9',2)
    elif kind=='vector':
        body=line(12,7,5,7)+line(5,7,5,57)+line(5,57,12,57)+line(52,7,59,7)+line(59,7,59,57)+line(59,57,52,57)
        for yy in (16,27,38,49):body+=rect(18,yy-3,28,6,'#7294A9',2)
    elif kind=='search':
        body=circle(26,26,19,'#FFFFFF')+line(40,40,59,59,BLUE,5)
    elif kind=='check':
        body=circle(32,32,25,'#EAF0F4')+line(18,32,28,42,BLUE,4)+line(28,42,47,21,BLUE,4)
    elif kind=='review':
        body=circle(26,26,17,'#FFFFFF')+line(39,39,56,56,BLUE,4)
    elif kind=='question':
        body=circle(32,32,25,'#EAF0F4')
    else:
        body=rect(12,12,40,40,'#FFFFFF',5,BLUE)+rect(23,23,18,18,'#EAF0F4',2,BLUE)
        for v in (20,32,44):body+=line(v,3,v,12)+line(v,52,v,61)+line(3,v,12,v)+line(52,v,61,v)
    result=f'<g transform="translate({x} {y}) scale({size/64})">{body}</g>'
    if kind=='question':result+=text(x+size/2,y+size*.7,'?',size*.59,BLUE,600,'middle')
    return result


def capability_icon(index,x,y,size):
    if index==0:return image(x,y,size,size,'icon-2.png')
    if index==1:return image(x,y,size,size,'icon-3.png')
    if index==2:return glyph('document',x,y,size*.9)+glyph('check',x+size*.56,y+size*.56,size*.4)
    return image(x,y,size,size,'icon-4.png')


def graphic_page(n,title,body,kicker='METHOD',role='content',bg='#FFFFFF'):
    heading=group('headline',rect(64,27,4,30,GOLD,1)+text(80,49,kicker,17,BLUE,600)+text(64,116,title,42,NAVY,300)+(rect(64,138,80,3,BLUE,0) if title else ''))
    progress=''.join(rect(930+k*20,684,12,3,GOLD if k==(PAGE_NUMBERS[n]-1 if n<=9 else n-10) else '#D6DDE0',1) for k in range(9 if n<=9 else 3))
    footer=group('footer',f'<line x1="64" y1="667" x2="1216" y2="667" stroke="#D6DDE0" stroke-width="1"/>'+text(64,692,'AI 資安框架 · 資安技術組',15,'#53666E')+text(1216,692,(f'{PAGE_NUMBERS[n]:02d} / 09' if n<=9 else f'答詢備用 {n-9} / 3'),15,'#53666E',400,'end')+progress)
    background=rect(0,0,1280,720,bg,0).replace('<rect ','<rect id="page-background" data-pptx-role="background" ',1)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="{FONT}" data-pptx-page-role="{role}">{background}{heading}{group("page-content",body)}{footer}</svg>'


def build_pages(limit=12):
    global SY, OY
    import json
    out=PROJECT/'svg_output';out.mkdir(parents=True,exist_ok=True)
    detector=json.loads((ROOT/'results/detection_17class.json').read_text(encoding='utf-8'))
    pages=[]
    # P01: formal name plus a compact, connected product chain.
    s=''
    for k,l in enumerate(['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架']):s+=text(64,205+k*65,l,43,NAVY,300)
    s+=text(64,430,'從流量判定，走到有證據的處置。',28,'#53666E')
    for i,label in enumerate(['偵測','檢索','稽核','回復']):
        x=64+i*222
        s+=rect(x,500,188,72)+capability_icon(i,x+8,509,50)+text(x+115,546,label,26,BLUE,600,'middle')
        if i<3:s+=arrow([(x+188,536),(x+222,536)])
    s+=f'<g transform="translate(938 170) scale(4.25)">{icon_fragment("framework")}</g>'
    pages.append(graphic_page(1,'',s,'2026 資安技術組 · 決賽','cover'))
    # P02: native architecture carries the full topological contract.
    SY,OY=1,142
    s=architecture(False)
    SY,OY=1,0
    pages.append(graphic_page(2,'一個框架，四個連續階段',s,'FRAMEWORK'))
    # P03: two complementary paths, one calibrated output.
    s=rect(64,190,220,350)+text(86,232,'同一流量輸入',26,BLUE,600)
    for j,(label,pattern) in enumerate([('封包內容','位元組'),('時間差','間隔'),('方向','往返')]):
        y=292+j*82
        s+=text(86,y,label,24)+rect(196,y-24,66,30,'#EAF0F4',4)
        for z in range(4):s+=rect(202+z*13,y-18,7,18 if j!=1 else 8+z*3,BLUE,1)
    s+=arrow([(284,365),(328,365),(328,270),(370,270)])+arrow([(328,365),(328,455),(370,455)])
    s+=rect(370,196,340,148,'#FFFFFF',8,'#D6DDE0')+rect(370,196,4,148,BLUE,0)+image(390,211,82,82,'icon-2.png')+text(492,240,'CTBM',32,BLUE,600)+text(492,278,'內容·時序·方向',21)+text(394,323,'讀取流量的時序關係',21,'#53666E')
    s+=rect(370,381,340,148,'#FFFFFF',8,'#D6DDE0')+rect(370,381,4,148,BLUE,0)+glyph('packet',394,398,70)+text(492,425,'PBCNN',32,BLUE,600)+text(492,465,'短窗位元組模式',21)+text(394,508,'補充局部內容特徵',21,'#53666E')
    s+=arrow([(710,270),(760,270),(760,365),(810,365)])+arrow([(710,455),(760,455),(760,365)])
    s+=rect(810,273,406,180,'#EAF0F4')+text(835,320,'校準＋OOF Gate',30,BLUE,600)+text(835,365,'依事件證據融合',25)+text(835,412,'形成同一次正式判定',23,'#53666E')
    s+=arrow([(1013,453),(1013,565)])+rect(64,565,1152,64)+text(88,605,'17 類判定  ＋  校準信心  ＋  模型表徵  →  後段檢索與稽核',25)
    pages.append(graphic_page(3,'互補模型，形成同一次判定',s,'DETECTION'))
    # P04: vector composition is qualitative, not a falsely scaled 512:17 chart.
    s=text(64,192,'01  組合任務向量',23,BLUE,600)
    s+=rect(64,226,260,75)+glyph('vector',77,238,49)+text(220,272,'512 維表徵',24,anchor='middle')
    s+=text(194,335,'＋',30,BLUE,600,'middle')+rect(64,357,260,75)+glyph('vector',77,370,49)+text(220,403,'17 維類別機率',23,anchor='middle')
    s+=arrow([(324,264),(350,264),(350,460),(194,460),(194,478)])+arrow([(194,432),(194,478)])
    s+=rect(64,478,260,98,'#EAF0F4')+text(194,521,'529 維任務向量',26,BLUE,600,'middle')+text(194,556,'L2 正規化',21,'#53666E',400,'middle')
    s+=arrow([(324,527),(390,527),(390,323),(430,323)])
    s+=text(430,192,'02  找出相似案例',23,BLUE,600)+image(444,213,135,135,'icon-3.png')
    s+=text(606,249,'訓練案例庫',25)+text(606,286,'1,550 筆案例',22,'#53666E')
    for i in range(5):
        x=430+i*66
        s+=rect(x,390,56,90,'#EAF0F4',4,BLUE)+text(x+28,444,str(i+1),24,BLUE,600,'middle')
    s+=text(430,520,'Top-5 相似案例',25)+text(430,557,'只檢索訓練資料',21,'#53666E')
    s+=arrow([(756,435),(800,435),(800,296),(850,296)])+text(850,192,'03  本機 AI 稽核',23,BLUE,600)
    s+=rect(850,240,366,112,'#EAF0F4')+text(1033,288,'判定＋案例證據',26,BLUE,600,'middle')+text(1033,325,'核對同一事件',22,'#53666E',400,'middle')
    s+=arrow([(1033,352),(1033,371),(909,371),(909,390)])+arrow([(1033,371),(1033,390)])+arrow([(1033,371),(1157,371),(1157,390)])
    for i,label in enumerate(['支持','複核','不確定']):
        x=850+i*124
        s+=rect(x,390,118,65)+text(x+59,432,label,24,anchor='middle')
    s+=text(850,520,'保留正式分類',25)+text(850,557,'稽核結論附回事件紀錄',21,'#53666E')
    s+=text(64,628,'同一事件 ID：分類結果與檢索證據一路可追溯。',24)
    pages.append(graphic_page(4,'把偵測表徵，變成可核對的證據',s,'EVIDENCE'))
    # P05: four object illustrations explain controlled execution and expiry.
    s=''
    stages=[('政策檢查','範圍·允許動作·期限','shield'),('套用規則','受允許策略才執行','firewall'),('讀回驗證','核對規則與事件回條','document'),('到期回復','撤銷並確認服務恢復','clock')]
    for i,(label,detail,kind) in enumerate(stages):
        x=64+i*294
        s+=rect(x,195,270,257,'#EAF0F4' if i==0 else '#F0F2F3')
        s+=text(x+22,232,f'0{i+1}',20,BLUE,600)
        s+=image(x+77,239,116,116,'icon-4.png') if kind=='shield' else glyph(kind,x+87,250,96)
        s+=text(x+135,391,label,29,'#171C1D',400,'middle')+text(x+135,431,detail,20,'#53666E',400,'middle')
        if i<3:s+=arrow([(x+270,323),(x+294,323)])
    s+=arrow([(199,452),(199,513),(424,513)],'#53666E',True)
    s+=rect(424,478,792,69)+glyph('document',442,490,42)+text(500,521,'複核／不確定 → 監測或蒐證',26)
    s+=rect(64,576,1152,64)+text(88,616,'6 種隔離 TCP 情境：4 種套用規則、2 種監測或蒐證；背景保留與回復皆 6/6。',22)
    pages.append(graphic_page(5,'受控執行，留下可回復的處置紀錄',s,'CONTROL'))
    # P06: native 16:9 movie frame; embedded in the packaging pass.
    s=rect(192,151,896,504,'#F0F2F3',8,'#D6DDE0')
    s+='<circle cx="640" cy="350" r="40" fill="#EAF0F4"/>'
    s+=text(640,360,'播放',25,BLUE,400,'middle')+text(640,430,'產品方法動畫',32,'#171C1D',300,'middle')+text(640,476,'30 秒 · 2 倍速',23,'#53666E',400,'middle')
    pages.append(graphic_page(6,'一個事件，走完完整流程',group('video-slot',s),'METHOD FILM'))
    # P07: genuine zero-baseline comparison. Plot domain 0..100, x=200..850.
    s=text(64,180,'相同 18,998 筆封存測試 · Macro-F1',24,'#53666E')
    chart=''
    for tick in [0,50,100]:
        x=200+650*tick/100
        chart+=f'<line x1="{x}" y1="220" x2="{x}" y2="550" stroke="#D6DDE0" stroke-width="1"/>'+text(x,585,str(tick)+'%',20,'#53666E',400,'middle')
    marks=''
    for i,(name,label) in enumerate([('PBCNN','PBCNN'),('CTBM','CTBM'),('OOF Gate','OOF Gate')]):
        value=detector[name]['macro_f1']*100
        y=254+i*110
        marks+=text(64,y+29,label,23,BLUE if i==2 else '#171C1D',600 if i==2 else 400)
        marks+=rect(200,y,650*value/100,42,GOLD if i==2 else '#7294A9',0)
        marks+=text(200+650*value/100+12,y+29,f'{value:.2f}%',23,BLUE if i==2 else '#171C1D',600)
    chart+= '<!-- chart-plot-area: object=detector-comparison | 200,220,850,550 -->'+marks
    s+=group('detector-comparison',group('detector-comparison-chartArea',chart))
    s+=rect(953,221,263,329,'#EAF0F4')+text(978,276,'整體準確率',26)+text(978,366,f"{detector['OOF Gate']['accuracy']*100:.2f}%",48,BLUE,300)+text(978,425,'17 類分類',25)+text(978,479,'同一封存測試集',21,'#53666E')
    s+=text(64,632,'融合相較 PBCNN 提升 13.30 個百分點；相較 CTBM 提升 0.95 個百分點。',23)
    pages.append(graphic_page(7,'互補融合，提升整體辨識效果',s,'MEASURED RESULTS'))
    # P08: outcomes form a qualitative branch; card area does not encode counts.
    s=rect(64,190,362,369)+text(88,232,'檢索效果',25,BLUE,600)+text(88,309,'97.62%',48,BLUE,300)+text(88,347,'Top-5 命中率',24)+text(88,426,'93.89%',44,BLUE,300)+text(88,463,'MRR@5 排序品質',24)+text(88,527,'1,550 案例／463 查詢',21,'#53666E')
    s+=rect(515,190,616,70,'#EAF0F4')+text(823,234,'463 筆事件 → 本機 AI 稽核',27,BLUE,600,'middle')
    s+=arrow([(823,260),(823,298),(576,298),(576,336)])+arrow([(823,298),(823,336)])+arrow([(823,298),(1070,298),(1070,336)])
    for i,(value,label) in enumerate([('415','支持'),('13','複核'),('35','不確定')]):
        x=470+i*247
        s+=rect(x,336,212,151)+glyph(['check','review','question'][i],x+86,348,40)+text(x+106,429,value,39,BLUE,300,'middle')+text(x+106,468,label,24,anchor='middle')
    s+=text(470,538,'支持精確率 97.11% · 正式分類保持可追溯',23)
    s+=rect(64,584,1152,61,'#EAF0F4')+text(88,624,'18 / 30 偵測誤判分流至複核或不確定；其餘 12 筆仍獲支持。',25)
    pages.append(graphic_page(8,'案例提供證據，AI完成分流',s,'MEASURED RESULTS'))
    # P09: explain the actual linked artifacts, rather than slogans alone.
    s=text(64,195,'偵測有依據，稽核有證據，處置可回復。',36,'#171C1D',300)
    for i,(a,b) in enumerate([('正式判定','17 類＋信心'),('檢索證據','Top-5 訓練案例'),('稽核結論','支持／複核／不確定'),('處置回條','讀回＋到期回復')]):
        x=64+i*294
        s+=rect(x,292,270,174,'#FFFFFF',8)+glyph(['document','search','check','clock'][i],x+104,305,62)+text(x+135,401,a,27,BLUE,600,'middle')+text(x+135,443,b,20,'#53666E',400,'middle')
        if i<3:s+=arrow([(x+270,381),(x+294,381)])
    s+=rect(64,502,1152,56,'#FFF4DD')+text(640,540,'同一事件 ID，串起分類、證據、判斷與回復紀錄。',26,NAVY,anchor='middle')
    s+=text(64,604,'17 類真實張量重跑 · 6 種隔離 TCP 情境驗證',26)+text(64,645,'感謝聆聽，敬請指教。',24,BLUE)
    pages.append(graphic_page(9,'一套可展示、可查核的資安框架',s,'AI SECURITY FRAMEWORK','ending','#F0F2F3'))
    pages=[pages[i] for i in [0,5,1,2,3,4,6,7,8]]
    qa=[('創新在哪裡？與一般 IDS 加上 RAG 有何不同？', ['把流量表徵與類別機率組成任務向量，檢索相關證據。', 'AI 保留正式分類，同一事件一路連到策略與回復回條。'], '529 維', '任務導向證據向量', '正式分類保留 · 稽核證據可追溯 · 策略可回復'), ('如何證明前段判斷與後段處置已經串起來？', ['17 類本機推論與 AI 稽核已逐類執行，產物使用同一事件 ID。', '6 種隔離情境的回條綁定同次執行，過期執行 ID 會被拒絕。'], '同一 ID', '事件與執行可追溯', '分類、Top-5、Judge、策略與回條綁定同一事件'), ('評估資料如何切分？案例庫是否洩漏測試答案？', ['偵測比較使用相同 18,998 筆測試；案例庫只由訓練資料建立。', '檢索使用 1,550 筆案例、463 筆查詢，訓練與查詢沒有重疊。'], '0', '訓練／查詢重疊', '訓練庫只讀 · 查詢不重疊 · AI 不看真實標籤'), ('AI 若支持錯誤判斷，如何避免直接誤封？', ['30 筆偵測誤判有 18 筆分流；其餘 12 筆仍獲 AI 支持。', '處置另經信心、政策、動作白名單與期限檢查，並可到期撤銷。'], '18 / 30', '偵測誤判分流', '12 筆為支持統計；處置與回復另以隔離情境驗證'), ('6/6 是否代表各種真實攻擊都能完全防住？', ['6/6 指隔離 TCP 情境中的背景服務保留及回復完整性。', '4 種情境套用規則、2 種監測或蒐證；不等同真實攻擊防禦率。'], '6 / 6', '背景保留與回復', '6/6 驗證服務保留與回復；不等同真實攻擊防禦率'), ('如何部署、保護資料，並接到既有環境？', ['本機 GPU 模型與本機案例庫處理事件，敏感欄位先遮罩。', '17 類已以前處理張量驗證；場域接入依資料介面配置。'], '0', '外部 API 呼叫', '本機 AI 稽核；私有權重、輸入及逐筆回覆不公開')]
    def qa_node(x,y,w,label,fill='#FFFFFF',size=22):
        return rect(x,y,w,48,fill,6)+text(x+w/2,y+32,label,size,'#171C1D',400,'middle')

    for page_index in range(3):
        content=''
        for slot in range(2):
            qi=page_index*2+slot
            question,answers,metric,metric_label,proof=qa[qi]
            y=165+slot*244
            content+=rect(64,y,1152,220,'#F0F2F3')+rect(974,y,242,220,'#EAF0F4')
            content+=rect(64,y,4,220,BLUE,0)
            content+=text(88,y+40,f'Q{qi+1}',24,BLUE,600)+text(144,y+40,question,26,'#171C1D',600)
            if qi==0:
                for j,label in enumerate(['互補判定','529 維檢索','AI 稽核','策略與回復']):
                    x=88+j*210
                    content+=capability_icon(j,x+52,y+66,84)+text(x+94,y+177,label,22,anchor='middle')
                    if j<3:content+=arrow([(x+149,y+108),(x+247,y+108)])
            elif qi==1:
                for j,label in enumerate(['正式類別','Top-5 案例','稽核結論','處置回條']):
                    x=88+j*210
                    content+=glyph('document',x+69,y+67,51)+text(x+94,y+140,label,21,anchor='middle')
                    if j<3:content+=arrow([(x+127,y+96),(x+272,y+96)])
                content+=rect(88,y+151,818,31,'#EAF0F4',6)+text(497,y+174,'同一 event_id  ＋  同次 execution_id',22,BLUE,400,'middle')
            elif qi==2:
                content+=image(172,y+72,74,74,'icon-3.png')+text(209,y+161,'訓練案例 1,550',23,'#171C1D',400,'middle')+glyph('search',475,y+71,68)+text(506,y+161,'Top-5 檢索',23,BLUE,400,'middle')+glyph('document',780,y+75,62)+text(811,y+161,'測試查詢 463',23,'#171C1D',400,'middle')
                content+=arrow([(280,y+110),(465,y+110)])+arrow([(764,y+110),(553,y+110)])
            elif qi==3:
                content+=qa_node(88,y+107,150,'30 筆誤判')
                content+=arrow([(238,y+131),(274,y+131),(274,y+91),(312,y+91)])+arrow([(274,y+131),(274,y+153),(312,y+153)])
                content+=qa_node(312,y+67,240,'18 複核／不確定')+qa_node(312,y+129,240,'12 仍支持')
                content+=arrow([(552,y+91),(612,y+91)])+arrow([(552,y+153),(612,y+153)])
                content+=qa_node(612,y+67,296,'監測／蒐證','#EAF0F4')+qa_node(612,y+129,296,'若觸發 → 策略檢查','#EAF0F4',21)
            elif qi==4:
                content+=rect(88,y+70,330,109,'#FFFFFF',6)+text(253,y+96,'隔離 TCP 測試床',22,'#171C1D',400,'middle')+glyph('server',124,y+107,40)+glyph('firewall',233,y+107,40)+glyph('server',342,y+107,40)+arrow([(166,y+128),(233,y+128)])+arrow([(275,y+128),(342,y+128)])+text(253,y+170,'4 規則＋2 監測',20,BLUE,400,'middle')
                content+=arrow([(418,y+126),(450,y+126),(450,y+96),(480,y+96)])+arrow([(450,y+126),(450,y+152),(480,y+152)])
                content+=qa_node(480,y+72,428,'背景服務保留 6 / 6','#EAF0F4')+qa_node(480,y+128,428,'回復完整性 6 / 6','#EAF0F4')
            else:
                content+=rect(88,y+74,820,103,'#EAF0F4',7)+text(110,y+99,'本機工作站  ·  GPU 模型與案例庫',22,BLUE)
                for j,label in enumerate(['欄位遮罩','17 類推論','檢索＋AI','策略回條']):
                    x=104+j*200
                    content+=rect(x,y+114,170,48,'#FFFFFF',6)+(glyph('document',x+3,y+118,40) if j==0 else image(x+3,y+118,40,40,f'icon-{j+1}.png'))+text(x+108,y+145,label,20,anchor='middle')
                    if j<3:content+=arrow([(x+170,y+138),(x+200,y+138)])
            content+=text(88,y+204,proof,20,BLUE)
            content+=text(1095,y+97,metric,38,BLUE,400,'middle')+text(1095,y+147,metric_label,21,'#53666E',400,'middle')
        pages.append(graphic_page(10+page_index,['答詢圖解｜創新與整合','答詢圖解｜評估與誤判','答詢圖解｜效果與部署'][page_index],content,'JUDGES · Q&A'))
    for i,p in enumerate(pages[:limit]):(out/f'{i+1:02d}_slide.svg').write_text(p,encoding='utf-8')
    print(f'Authored {min(limit,len(pages))} graphical slides; all static.')


if __name__ == '__main__':
    import sys
    architecture();build_pages(int(sys.argv[1]) if len(sys.argv)>1 else 12)
