"""Package offline presentation assets only; exclude private models and raw events."""
import hashlib
import os
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    'deliverables/決賽簡報_AI資安框架.pptx',
    'deliverables/決賽簡報_AI資安框架.pdf',
    'deliverables/AI資安框架_系統展示影片_30秒快版.mp4',
    'deliverables/決賽海報_AI資安框架_A2.pptx',
    'deliverables/決賽海報_AI資安框架_A2.pdf',
    'deliverables/source/speaker-notes.md',
    'deliverables/source/finals-runbook.json',
    'docs/決賽五分鐘口語稿.md',
    'docs/決賽六題答詢口徑.md',
    'docs/現場控場與備援卡.md',
    'deliverables/interactive/AI資安框架_離線互動展示.html',
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
interactive內的HTML可直接離線開啟，預設2倍速，可暫停或跳轉章節。
HTML使用合成示意資料，不執行模型或網路規則，匯出數字不可當作實測成果。
正式投影前關閉通知，隱藏個人路徑、帳號與可識別資訊。
docs內另附五分鐘口語稿、六題答詢與現場備援卡，source內含頁序與時間設定。
這些時間是配置目標；講者朗讀、場地可讀性及印刷打樣由現場人員確認。
SHA256SUMS.txt列出本包資產雜湊，可比對檔案是否變動。
'''


def asset_bytes(name):
    content = (ROOT / name).read_bytes()
    return content.replace(b'\r\n', b'\n') if name.endswith(('.md', '.json', '.html')) else content


def build(root=ROOT):
    root = Path(root)
    output = root / 'deliverables/決賽離線展示包.zip'
    if output.is_symlink() or not output.resolve().is_relative_to(root.resolve()):
        raise ValueError('unsafe_package_target')
    hashes = []
    descriptor, temporary = tempfile.mkstemp(prefix='.offline-', suffix='.tmp', dir=output.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    def put(archive, name, content):
        entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.create_system = 3
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, content)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in ASSETS:
                path = root / name
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('unsafe_package_asset')
                content = path.read_bytes()
                if name.endswith(('.md', '.json', '.html')):
                    content = content.replace(b'\r\n', b'\n')
                put(archive, name, content)
                hashes.append(hashlib.sha256(content).hexdigest()+'  '+name)
            put(archive, '使用說明.txt', INSTRUCTIONS.encode('utf-8'))
            put(archive, 'SHA256SUMS.txt', ('\n'.join(hashes)+'\n').encode('utf-8'))
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('package_crc_failed')
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    print('Offline package:', len(ASSETS), 'assets; no private model assets')
    return output


if __name__ == '__main__':
    build()
