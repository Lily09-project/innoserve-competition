"""Build original light-canvas/blue presentation art from verified results.

Python composes the architecture; AI supplies only four text-free icon cutouts.
All diagram labels remain editable SVG text. No generated experimental values.
"""
from pathlib import Path
from html import escape
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'deliverables/source'
PROJECT = ROOT / 'projects/finals_editorial_ppt169_20261028'
BLUE = '#0070D1'
FONT = 'Microsoft JhengHei'
SY, OY = 1, 0


def text(x, y, value, size=26, color='#000000', weight=400, anchor='start'):
    return f'<text x="{x}" y="{y*SY+OY}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>'


def rect(x, y, w, h, fill='#F5F7FA', radius=8, stroke='none'):
    return f'<rect x="{x}" y="{y*SY+OY}" width="{w}" height="{h*SY}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(body, height=720, bg='#FFFFFF'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="{height}" viewBox="0 0 1280 {height}" font-family="{FONT}">{rect(0,0,1280,height,bg,0)}{body}</svg>'


def image(x, y, w, h, file):
    return f'<image x="{x}" y="{y*SY+OY}" width="{w}" height="{h*SY}" href="../images/{file}" preserveAspectRatio="xMidYMid meet"/>'


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
    s=rect(16,16,226,205,'#F5F7FA',8,'#CCCCCC')
    s+=text(34,48,'a  流量表徵',24,BLUE,600)+image(190,20,34,34,'icon-1.png')
    s+=text(34,97,'真實前處理張量',21)+text(34,142,'封包內容',22)+text(34,174,'時間差・方向',22)
    s+=text(34,204,'遮罩欄位・流量切窗',20,'#6B6B6B')
    s+=rect(266,16,998,205,'#F5F7FA',8,'#CCCCCC')
    s+=image(282,22,36,36,'icon-2.png')+text(328,48,'b  互補模型與 17 類判定',24,BLUE,600)
    for y,title,sub in [(70,'CTBM','內容・時間差・方向'),(148,'PBCNN','短窗位元組模式')]:
        s+=rect(292,y,300,60,'#FFFFFF',8,'#CCCCCC')+text(310,y+26,title,24,weight=600)+text(310,y+50,sub,20)
    s+=rect(660,90,278,90,'#FFFFFF',8,'#CCCCCC')+text(682,123,'校準＋OOF Gate',24,weight=600)+text(682,160,'依事件證據融合',22)
    s+=rect(966,90,276,90,'#FFFFFF',8,'#CCCCCC')+text(986,123,'17 類正式判定',24,weight=600)+text(986,160,'512 維表徵＋17 維機率',20)
    s+=route([(242,118),(280,118),(280,100),(292,100)])+route([(280,118),(280,178),(292,178)])
    s+=route([(592,100),(625,100),(625,135),(660,135)])+route([(592,178),(625,178),(625,135),(660,135)])+route([(938,135),(966,135)])
    s+=rect(16,282,840,186,'#F5F7FA',8,'#CCCCCC')+image(34,288,36,36,'icon-3.png')+text(80,314,'c  任務導向檢索與 AI 稽核',24,BLUE,600)
    for x,w,title,sub in [(40,190,'529 維任務向量','L2 正規化'),(260,244,'Top-5 相似案例','僅訓練資料案例庫'),(540,292,'本機 AI 稽核','支持／複核／不確定')]:
        s+=rect(x,340,w,82,'#FFFFFF',8,'#CCCCCC')+text(x+14,374,title,22,weight=600)+text(x+14,405,sub,20)
    s+=route([(1104,180),(1104,249),(5,249),(5,381),(40,381)])
    s+=text(620,240,'正式類別・信心・模型表徵',22,anchor='middle')
    s+=route([(230,381),(260,381)])+route([(504,381),(540,381)])
    s+=text(380,454,'訓練案例庫',20,'#6B6B6B',anchor='middle')+route([(380,434),(380,422)],'#6B6B6B',True)
    s+=text(554,454,'稽核保留正式分類',20,'#6B6B6B')
    s+=rect(880,282,384,186,'#F5F7FA',8,'#CCCCCC')+image(898,287,36,36,'icon-4.png')+text(944,314,'d  受控處置與回復',24,BLUE,600)
    s+=text(904,364,'策略檢查 → 套用',24)+text(904,401,'讀回 → 到期撤銷',24)+text(904,451,'複核／不確定 → 蒐證',20,'#6B6B6B')
    s+=route([(832,381),(880,381)])
    s+=rect(16,484,1248,38,'#F5F7FA',8,'#CCCCCC')+text(640,510,'共用事件 ID：正式判定｜Top-5 證據｜AI 稽核｜處置與回復回條',22,anchor='middle')
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


def graphic_page(n,title,body,kicker='METHOD',role='content',bg='#FFFFFF'):
    heading=group('headline',text(64,56,kicker,16,BLUE,600)+text(64,116,title,42,'#121314',300))
    footer=group('footer',text(64,687,'AI 資安框架 · 資安技術組',14,'#6B6B6B')+text(1216,687,f'{n:02d} / 09',14,'#6B6B6B',400,'end'))
    background=rect(0,0,1280,720,bg,0).replace('<rect ','<rect id="page-background" data-pptx-role="background" ',1)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="{FONT}" data-pptx-page-role="{role}">{background}{heading}{group("page-content",body)}{footer}</svg>'


def build_pages(limit=9):
    global SY, OY
    import json,shutil
    out=PROJECT/'svg_output';out.mkdir(parents=True,exist_ok=True)
    imgs=PROJECT/'images';imgs.mkdir(exist_ok=True)
    for i in range(1,5):shutil.copy2(DEST/f'icon-{i}.png',imgs/f'icon-{i}.png')
    detector=json.loads((ROOT/'results/detection_17class.json').read_text(encoding='utf-8'))
    pages=[]
    # P01: formal name plus a compact, connected product chain.
    s=''
    for k,l in enumerate(['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架']):s+=text(64,205+k*65,l,43,'#121314',300)
    s+=text(64,430,'從流量判定，走到有證據的處置。',28,'#6B6B6B')
    for i,label in enumerate(['偵測','檢索','稽核','回復']):
        x=64+i*222
        s+=rect(x,500,188,72)+text(x+94,546,label,28,BLUE,600,'middle')
        if i<3:s+=arrow([(x+188,536),(x+222,536)])
    s+=image(980,430,208,208,'icon-4.png')
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
        s+=text(86,y,label,24)+rect(196,y-24,66,30,'#E2EDF8',4)
        for z in range(4):s+=rect(202+z*13,y-18,7,18 if j!=1 else 8+z*3,BLUE,1)
    s+=arrow([(284,365),(328,365),(328,270),(370,270)])+arrow([(328,365),(328,455),(370,455)])
    s+=rect(370,196,340,148)+text(394,240,'CTBM',32,BLUE,600)+text(394,286,'內容 × 時間差 × 方向',24)+text(394,319,'讀取流量的時序關係',21,'#6B6B6B')
    s+=rect(370,381,340,148)+text(394,425,'PBCNN',32,BLUE,600)+text(394,471,'短視窗位元組模式',24)+text(394,504,'補充局部內容特徵',21,'#6B6B6B')
    s+=arrow([(710,270),(760,270),(760,365),(810,365)])+arrow([(710,455),(760,455),(760,365)])
    s+=rect(810,273,406,180,'#EAF3FC')+text(835,320,'校準＋OOF Gate',30,BLUE,600)+text(835,365,'依事件證據融合',25)+text(835,412,'形成同一次正式判定',23,'#6B6B6B')
    s+=arrow([(1013,453),(1013,565)])+rect(64,565,1152,64)+text(88,605,'17 類判定  ＋  校準信心  ＋  模型表徵  →  後段檢索與稽核',25)
    pages.append(graphic_page(3,'互補模型，形成同一次判定',s,'DETECTION'))
    # P04: vector composition is qualitative, not a falsely scaled 512:17 chart.
    s=text(64,192,'01  組合任務向量',23,BLUE,600)
    s+=rect(64,226,260,75)+text(194,272,'512 維流量表徵',24,anchor='middle')
    s+=text(194,335,'＋',30,BLUE,600,'middle')+rect(64,357,260,75)+text(194,403,'17 維類別機率',24,anchor='middle')
    s+=arrow([(324,264),(350,264),(350,460),(194,460),(194,478)])+arrow([(194,432),(194,478)])
    s+=rect(64,478,260,98,'#EAF3FC')+text(194,521,'529 維任務向量',26,BLUE,600,'middle')+text(194,556,'L2 正規化',21,'#6B6B6B',400,'middle')
    s+=arrow([(324,527),(390,527),(390,323),(430,323)])
    s+=text(430,192,'02  找出相似案例',23,BLUE,600)+image(444,213,135,135,'icon-3.png')
    s+=text(606,249,'訓練案例庫',25)+text(606,286,'1,550 筆案例',22,'#6B6B6B')
    for i in range(5):
        x=430+i*66
        s+=rect(x,390,56,90,'#EAF3FC',4,BLUE)+text(x+28,444,str(i+1),24,BLUE,600,'middle')
    s+=text(430,520,'Top-5 相似案例',25)+text(430,557,'只檢索訓練資料',21,'#6B6B6B')
    s+=arrow([(756,435),(800,435),(800,296),(850,296)])+text(850,192,'03  本機 AI 稽核',23,BLUE,600)
    s+=rect(850,240,366,112,'#EAF3FC')+text(1033,288,'判定＋案例證據',26,BLUE,600,'middle')+text(1033,325,'核對同一事件',22,'#6B6B6B',400,'middle')
    s+=arrow([(1033,352),(1033,371),(909,371),(909,390)])+arrow([(1033,371),(1033,390)])+arrow([(1033,371),(1157,371),(1157,390)])
    for i,label in enumerate(['支持','複核','不確定']):
        x=850+i*124
        s+=rect(x,390,118,65)+text(x+59,432,label,24,anchor='middle')
    s+=text(850,520,'保留正式分類',25)+text(850,557,'稽核結論附回事件紀錄',21,'#6B6B6B')
    s+=text(64,628,'同一事件 ID：分類結果與檢索證據一路可追溯。',24)
    pages.append(graphic_page(4,'把偵測表徵，變成可核對的證據',s,'EVIDENCE'))
    # P05: actual action sequence and a separate non-disruptive branch.
    s=''
    labels=[('政策檢查','範圍・白名單・期限'),('套用規則','受允許策略才執行'),('讀回驗證','確認規則及事件回條'),('到期回復','撤銷並確認服務恢復')]
    for i,(a,b) in enumerate(labels):
        x=64+i*294
        s+=rect(x,230,270,200,'#EAF3FC' if i==0 else '#F5F7FA')+text(x+24,269,f'0{i+1}',20,BLUE,600)
        s+=text(x+24,331,a,30)+text(x+24,383,b,21,'#6B6B6B')
        if i<3:s+=arrow([(x+270,330),(x+294,330)])
    s+=arrow([(199,430),(199,505),(424,505)],'#6B6B6B',True)
    s+=rect(424,473,792,68)+text(448,516,'複核／不確定  →  監測或蒐證，保留事件紀錄',25)
    s+=rect(64,574,1152,66)+text(88,615,'6 種隔離 TCP 情境：4 種套用規則、2 種監測或蒐證；背景保留與回復皆 6/6。',22)
    pages.append(graphic_page(5,'受控執行，留下可回復的處置紀錄',s,'CONTROL'))
    # P06: reserved editable 16:9 insertion frame; deliberately no video media.
    s=rect(192,151,896,504,'#F5F7FA',8,'#D6E1EC')
    s+='<circle cx="640" cy="350" r="40" fill="#E2EDF8"/>'
    s+=text(640,366,'▶',38,BLUE,400,'middle')+text(640,430,'產品方法動畫',32,'#121314',300,'middle')+text(640,476,'30 秒 · 2 倍速',23,'#6B6B6B',400,'middle')
    pages.append(graphic_page(6,'一個事件，走完完整流程',group('video-slot',s),'METHOD FILM'))
    # P07: genuine zero-baseline comparison. Plot domain 0..100, x=200..850.
    s=text(64,180,'相同 18,998 筆封存測試 · Macro-F1',23,'#6B6B6B')
    chart=''
    for tick in [0,50,100]:
        x=200+650*tick/100
        chart+=f'<line x1="{x}" y1="220" x2="{x}" y2="550" stroke="#DDE5ED" stroke-width="1"/>'+text(x,585,str(tick)+'%',20,'#6B6B6B',400,'middle')
    marks=''
    for i,(name,label) in enumerate([('PBCNN','PBCNN'),('CTBM','CTBM'),('OOF Gate','OOF Gate')]):
        value=detector[name]['macro_f1']*100
        y=254+i*110
        marks+=text(64,y+29,label,23,BLUE if i==2 else '#121314',600 if i==2 else 400)
        marks+=rect(200,y,650*value/100,42,BLUE if i==2 else '#9ABDE0',0)
        marks+=text(200+650*value/100+12,y+29,f'{value:.2f}%',23,BLUE if i==2 else '#121314',600)
    chart+= '<!-- chart-plot-area: object=detector-comparison | 200,220,850,550 -->'+marks
    s+=group('detector-comparison',group('detector-comparison-chartArea',chart))
    s+=rect(953,221,263,329,'#EAF3FC')+text(978,276,'整體準確率',26)+text(978,366,f"{detector['OOF Gate']['accuracy']*100:.2f}%",48,BLUE,300)+text(978,425,'17 類分類',25)+text(978,479,'同一封存測試集',21,'#6B6B6B')
    s+=text(64,632,'融合相較 PBCNN 提升 13.30 個百分點；相較 CTBM 提升 0.95 個百分點。',23)
    pages.append(graphic_page(7,'互補融合，提升整體辨識效果',s,'MEASURED RESULTS'))
    # P08: outcomes form a qualitative branch; card area does not encode counts.
    s=rect(64,190,362,369)+text(88,232,'檢索效果',25,BLUE,600)+text(88,309,'97.62%',48,BLUE,300)+text(88,347,'Top-5 命中率',24)+text(88,426,'93.89%',44,BLUE,300)+text(88,463,'MRR@5 排序品質',24)+text(88,527,'1,550 案例／463 查詢',21,'#6B6B6B')
    s+=rect(515,190,616,70,'#EAF3FC')+text(823,234,'463 筆事件 → 本機 AI 稽核',27,BLUE,600,'middle')
    s+=arrow([(823,260),(823,298),(576,298),(576,336)])+arrow([(823,298),(823,336)])+arrow([(823,298),(1070,298),(1070,336)])
    for i,(value,label) in enumerate([('415','支持'),('13','複核'),('35','不確定')]):
        x=470+i*247
        s+=rect(x,336,212,151)+text(x+106,395,value,42,BLUE,300,'middle')+text(x+106,447,label,25,anchor='middle')
    s+=text(470,538,'支持精確率 97.11% · 正式分類保持可追溯',23)
    s+=rect(64,584,1152,61,'#EAF3FC')+text(88,624,'18 / 30 偵測誤判分流至複核或不確定；其餘 12 筆仍獲支持。',25)
    pages.append(graphic_page(8,'案例提供證據，AI完成分流',s,'MEASURED RESULTS'))
    # P09: explain the actual linked artifacts, rather than slogans alone.
    s=text(64,195,'偵測有依據，稽核有證據，處置可回復。',36,'#121314',300)
    for i,(a,b) in enumerate([('正式判定','17 類＋信心'),('檢索證據','Top-5 訓練案例'),('稽核結論','支持／複核／不確定'),('處置回條','讀回＋到期回復')]):
        x=64+i*294
        s+=rect(x,292,270,174,'#FFFFFF',8)+text(x+24,347,a,30,BLUE,600)+text(x+24,409,b,21,'#6B6B6B')
        if i<3:s+=arrow([(x+270,379),(x+294,379)])
    s+=rect(64,502,1152,56,'#E2EDF8')+text(640,540,'同一事件 ID，串起分類、證據、判斷與回復紀錄。',26,anchor='middle')
    s+=text(64,621,'17 類真實張量重跑 · 6 種隔離 TCP 情境驗證',26)
    pages.append(graphic_page(9,'一套可展示、可查核的資安框架',s,'AI SECURITY FRAMEWORK','ending','#F2F7FC'))
    for i,p in enumerate(pages[:limit]):(out/f'{i+1:02d}_slide.svg').write_text(p,encoding='utf-8')
    print(f'Authored {min(limit,len(pages))} graphical slides; all static.')


if __name__ == '__main__':
    import sys
    architecture();build_pages(int(sys.argv[1]) if len(sys.argv)>1 else 9)
