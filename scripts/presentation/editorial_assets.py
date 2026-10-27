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
    s = ''
    blocks = [
        ('a', '流量表徵', ['封包內容・時間差・方向', '遮罩識別欄位・流量切窗'], ['輸入：真實前處理張量', '輸出：統一事件表徵']),
        ('b', '17 類判定', ['CTBM＋PBCNN', '校準信心・OOF Gate'], ['輸出：正式類別', '512 維表徵＋17 維機率']),
        ('c', '證據檢索與稽核', ['529 維任務向量 → Top-5', '本機 AI 核對訓練案例'], ['支持／複核／不確定', '稽核不改寫正式分類']),
        ('d', '受控處置與回復', ['策略閘門檢查範圍與期限', '套用 → 讀回 → 到期撤銷'], ['輸出：處置與回復回條', '複核事件保留蒐證'])
    ]
    for i, (letter,title,steps,outputs) in enumerate(blocks):
        x = 20+i*315
        s += rect(x,38,295,492,'#F5F7FA',8,'#CCCCCC')
        s += text(x+18,76,letter,22,BLUE,700)+text(x+48,76,title,23,'#000000',600)
        s += image(x+86,92,120,120,f'icon-{i+1}.png')
        for k,line in enumerate(steps):
            s += text(x+16,258+k*40,line,22)
        s += rect(x+14,334,267,160,'#FFFFFF',8)
        for k,line in enumerate(outputs):
            s += text(x+25,378+k*48,line,20,'#000000')
        if i<3:
            s += f'<path d="M{x+297} {316*SY+OY}H{x+311}m-6-6 6 6-6 6" fill="none" stroke="{BLUE}" stroke-width="3"/>'
    s += f'<path d="M1110 {532*SY+OY}V{571*SY+OY}H165V{532*SY+OY}" fill="none" stroke="#6B6B6B" stroke-width="2" stroke-dasharray="7 5"/>'
    s += text(640,607,'同一事件 ID 串接偵測、證據、稽核與處置回條',22,'#000000',400,'middle')
    # Save with sibling icon paths for standalone viewing.
    standalone = svg(s,640).replace('../images/','')
    if save: (DEST/'architecture.svg').write_text(standalone,encoding='utf-8')
    return s


def page(n,title,body,dark=False,kicker='METHOD'):
    bg,ink,muted = ('#000000','#FFFFFF','#CCCCCC') if dark else ('#FFFFFF','#000000','#6B6B6B')
    s = text(64,57,kicker,16,BLUE,600)+text(64,120,title,44,ink,300)
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
    SY, OY=.78,145
    body = architecture(False)
    SY, OY=1,0
    pages.append(page(2,'一個框架，四個連續階段',body,kicker='FRAMEWORK'))
    s = ''
    for i,(title,sub,file) in enumerate([('內容與時序','CTBM 讀取內容、時間與方向',2),('短窗模式','PBCNN 補充局部位元組特徵',1),('融合判定','校準後依事件證據動態調權',2)]):
        x=64+i*395
        s+=image(x+55,180,230,200,f'icon-{file}.png')+text(x,440,title,30, '#FFFFFF',300)
        s+=text(x,486,sub,20,'#CCCCCC')
        if i<2:s+=text(x+340,302,'→',36,'#53B1FF')
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
