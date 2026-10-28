"""Package offline presentation assets only; exclude private models and raw events."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    'deliverables/決賽簡報_AI資安框架.pptx',
    'deliverables/決賽簡報_AI資安框架.pdf',
    'deliverables/AI資安框架_系統展示影片_30秒快版.mp4',
    'deliverables/決賽海報_AI資安框架_A2.pptx',
    'deliverables/決賽海報_AI資安框架_A2.pdf',
    'deliverables/source/speaker-notes.md',
]
INSTRUCTIONS = '''決賽離線展示包

正式簡報為12頁：第1至9頁報告，第10至12頁為六題答詢。
封面後第2頁內嵌30秒影片，自動播放一次，換頁由講者手動操作。
簡報目標五分鐘，另保留一分鐘緩衝。請在正式設備實際朗讀彩排。
影片不能播放時，使用獨立MP4；簡報不能開啟時，使用PDF。
海報PDF為A2直式420×594mm，交印時選擇實際尺寸，不縮放至A3。
重要內容保留15mm安全邊界；紙材與出血依印刷廠另行確認。
可編輯PPTX使用標楷體與Times New Roman；海報PDF已嵌入字型。

本包為離線簡報、影片與海報備援，不包含模型部署、私有權重、案例庫或逐筆事件。
模型展示使用已配置的本機工作站及本機展示操作單。
正式投影前關閉通知，隱藏個人路徑、帳號與可識別資訊。
SHA256SUMS.txt列出本包資產雜湊，可比對檔案是否變動。
'''


def asset_bytes(name):
    content = (ROOT / name).read_bytes()
    return content.replace(b'\r\n', b'\n') if name.endswith('.md') else content


def build():
    output = ROOT / 'deliverables/決賽離線展示包.zip'
    hashes = []
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ASSETS:
            content = asset_bytes(name)
            archive.writestr(name, content)
            hashes.append(hashlib.sha256(content).hexdigest()+'  '+name)
        archive.writestr('使用說明.txt', INSTRUCTIONS.encode('utf-8'))
        archive.writestr('SHA256SUMS.txt', ('\n'.join(hashes)+'\n').encode('utf-8'))
    print('Offline package:', len(ASSETS), 'assets; no private model assets')


if __name__ == '__main__':
    build()
