"""Build original black/white/blue presentation art from verified results.

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


def page(n,title,body,dark=False,kicker='METHOD'):
    bg,ink,muted = ('#000000','#FFFFFF','#CCCCCC') if dark else ('#FFFFFF','#000000','#6B6B6B')
    s = text(64,57,kicker,16,'#53B1FF' if dark else BLUE,600)+text(64,120,title,44,ink,300)
    s += body + text(64,687,'AI 資安框架 · 資安技術組',14,muted)+text(1216,687,f'{n:02d} / 08',14,muted,400,'end')
    return svg(s,bg=bg)


def build_pages(limit=8):
    global SY, OY
    out = PROJECT/'svg_output'; out.mkdir(parents=True,exist_ok=True)
    imgs = PROJECT/'images'; imgs.mkdir(exist_ok=True)
    import shutil
    for i in range(1,5): shutil.copy2(DEST/f'icon-{i}.png',imgs/f'icon-{i}.png')
    shutil.copy2(DEST/'architecture.svg',imgs/'architecture.svg')
    pages=[]
    s = text(64,66,'2026 資安技術組 · 決賽',18,'#53B1FF',600)
    for k,l in enumerate(['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架']):
        s+=text(64,206+k*68,l,43,'#FFFFFF',300)
    s+=text(64,470,'從流量判定，走到有證據的處置。',28,'#CCCCCC')
    s+=rect(64,520,266,48,BLUE,24)+text(197,552,'偵測 → 檢索 → 稽核 → 回復',17,'#FFFFFF',600,'middle')
    s+=image(900,385,250,250,'icon-4.png')
    pages.append(svg(s,bg='#000000'))
    SY, OY=1,142
    body = architecture(False)
    SY, OY=1,0
    pages.append(page(2,'一個框架，四個連續階段',body,kicker='FRAMEWORK'))
    s=rect(64,220,210,220,'#181818',8)+image(104,237,130,110,'icon-1.png')+text(95,395,'同一流量輸入',24,'#FFFFFF')
    for y,title,sub in [(190,'CTBM','內容・時間差・方向'),(370,'PBCNN','短窗位元組模式')]:
        s+=rect(370,y,340,130,'#181818',8)+text(398,y+45,title,30,'#FFFFFF',600)+text(398,y+92,sub,24,'#CCCCCC')
    s+='<path d="M274 330H322V255H370 M322 330V435H370 M710 255H780V345H870 M710 435H780V345" fill="none" stroke="#53B1FF" stroke-width="3"/>'
    s+='<path d="M364 249L370 255L364 261 M364 429L370 435L364 441 M864 339L870 345L864 351" fill="none" stroke="#53B1FF" stroke-width="3"/>'
    s+=rect(870,270,346,150,'#181818',8)+text(896,322,'校準＋OOF Gate',30,'#FFFFFF')+text(896,374,'依事件證據融合',24,'#CCCCCC')
    s+=rect(64,550,1152,56,'#181818',8)+text(88,588,'固定 17 類輸出，連同校準信心與模型表徵交給後端。',24,'#FFFFFF')
    pages.append(page(3,'創新一：讓互補模型共同判斷',s,True,'DETECTION'))
    s=image(60,182,250,250,'icon-3.png')
    for i,(a,b) in enumerate([('512＋17 → 529 維','流量表徵＋類別機率，建立任務向量'),('Top-5 訓練案例','只檢索訓練庫；保留相似案例與類別共識'),('本機 AI 證據稽核','支持、複核、不確定；保留正式分類')]):
        y=208+i*116
        s+=rect(350,y-25,866,95)+text(374,y+8,a,28)+text(374,y+46,b,22,'#6B6B6B')
    s+=text(64,620,'同一事件識別碼貫穿判定、案例、稽核與回條。',26)
    pages.append(page(4,'創新二：用任務證據完成稽核',s,kicker='EVIDENCE'))
    s=''
    for i,(a,b) in enumerate([('政策閘門','確認範圍、白名單與期限'),('套用與讀回','回條綁定同次事件與執行'),('到期與回復','撤銷規則，確認服務恢復')]):
        x=64+i*395
        s+=rect(x,208,360,290,'#181818',8)+text(x+25,259,f'0{i+1}',20,'#53B1FF')+text(x+25,340,a,32,'#FFFFFF',300)+text(x+25,404,b,22,'#CCCCCC')
    s+=text(64,566,'4 種規則情境＋2 種監測或蒐證情境',27,'#FFFFFF')+text(64,610,'隔離TCP交易驗證：背景服務 6/6 保留，回復完整性 6/6 通過。',22,'#CCCCCC')
    pages.append(page(5,'創新三：處置可驗證，也可回復',s,True,'CONTROL'))
    s=text(64,198,'相同 18,998 筆封存測試',22,'#6B6B6B')
    # Deliberately use exact numeric comparison labels, not fabricated bar geometry.
    for i,(name,value) in enumerate([('PBCNN','79.75%'),('CTBM','92.10%'),('OOF Gate','93.05%')]):
        x=64+i*395
        s+=text(x,280,name,26,BLUE if i==2 else '#6B6B6B',600 if i==2 else 400)
        s+=text(x,360,value,56,'#000000',300)+text(x,406,'Macro-F1',20,'#6B6B6B')
    s+=rect(64,475,1152,130)+text(88,524,'98.08%',48,BLUE,300)+text(390,524,'17 類整體準確率',28)+text(88,570,'各模型使用相同測試集，呈現融合後的分類效果。',24,'#6B6B6B')
    pages.append(page(6,'互補融合，提升整體辨識效果',s,kicker='MEASURED RESULTS'))
    s=''
    for i,(v,l,sub) in enumerate([('97.62%','Top-5 命中率','463 筆查詢／1,550 筆訓練案例'),('93.89%','MRR@5','前五筆結果的排序品質'),('97.11%','支持精確率','415 支持／13 複核／35 不確定')]):
        x=64+i*395
        s+=text(x,266,v,54,'#FFFFFF',300)+text(x,328,l,28,'#FFFFFF')+text(x,384,sub,19,'#CCCCCC')
    s+=rect(64,476,1152,130,'#181818',8)+text(88,525,'18 / 30',45,'#53B1FF',300)+text(390,525,'偵測誤判分流至複核或不確定',26,'#FFFFFF')+text(88,570,'AI 依案例證據給出稽核結論；正式分類保持可追溯。',23,'#CCCCCC')
    pages.append(page(7,'從相似案例，走到可核對的結論',s,True,'MEASURED RESULTS'))
    s=text(64,92,'AI SECURITY FRAMEWORK',18,'#FFFFFF',600)
    for i,l in enumerate(['偵測有依據','稽核有證據','處置可回復']):s+=text(64,225+i*85,l,56,'#FFFFFF',300)
    s+=image(900,175,275,275,'icon-4.png')+text(64,570,'17 類真實張量重跑 · 6 種隔離情境驗證',28,'#FFFFFF')+text(64,620,'方法動畫獨立交付，可搭配本機流程與回條展示。',22,'#FFFFFF')
    pages.append(svg(s,bg=BLUE))
    for i,p in enumerate(pages[:limit]):(out/f'{i+1:02d}_slide.svg').write_text(p,encoding='utf-8')
    print(f'Authored {min(limit,len(pages))} slides')


if __name__ == '__main__':
    import sys
    split_icons(); architecture(); build_pages(int(sys.argv[1]) if len(sys.argv)>1 else 8)
