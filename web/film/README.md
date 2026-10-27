# 系統展示影片

啟動作品後開啟 `http://127.0.0.1:8765/film/index.html`，或從事件工作台點「系統展示影片」。

全片 96 秒、八個段落，作為決賽 6 分鐘簡報中的系統展示，也是現場網路不穩時的離線備案。除開場與結語外，每個段落以「輸入｜處理｜輸出」三欄呈現同一筆事件在該階段的資料變化：

| 段落 | 輸入 | 處理 | 輸出 |
|---|---|---|---|
| 01 資料輸入 | 原始封包（PCAP／鏡像埠） | 雙向 Flow 組裝、去識別化 | 內容 bytes、Δt、方向張量 |
| 02 17 類偵測 | 模型輸入張量 | CTBM、PBCNN、溫度校準、OOF Gate | 17 類正式機率 |
| 03 Top-5 檢索 | 529 維任務向量 | train-only 案例庫餘弦檢索 | Top-5 相似案例證據 |
| 04 AI 稽核 | 類別、信心、分支觀察、Top-5 | 本機 Llama 3 8B Instruct | 三態結構化 JSON |
| 05 受控處置 | 通過稽核的 Bot 事件 | Policy Guard、套用、讀回、TTL 撤銷 | 隔離網路處置回條 |
| 06 事件輸出 | 各階段結果 | 事件 ID／執行 ID 與雜湊綁定 | 可匯出的完整事件紀錄 |

畫面上的成果數字全部取自 `results/` 與系統概述文件，包括 17 類偵測（18,998 筆）、任務檢索（1,550 案例／463 查詢）、本機稽核（463 筆）與 Mininet 隔離驗證（`results/framework_validation.json` 的 Bot 情境：攻擊型測試交易成功率 100%→0%、背景服務 100%、30.12 秒到期撤銷）。封包內容一律以去識別化方式呈現。

- `scene.mjs`：段落、字幕、時間軸與純函式 `frameSvg(time)`。
- `player.mjs`：播放、暫停、拖曳進度、速度、跳章、全螢幕與鍵盤。
- `index.html`：播放器，不會自動啟動模型或部署策略。

## 輸出 MP4

HTML 與 MP4 共用同一個 `frameSvg`。有兩種輸出方式：

1. Node.js＋sharp＋FFmpeg：設定 `RENDER_NODE_MODULES`、`FFMPEG_BINARY` 後執行 `node scripts/render_product_film.mjs OUTPUT_DIRECTORY`（加 `--preview` 只輸出段落預覽圖）。
2. Node.js＋Python：`pip install resvg-py imageio-ffmpeg` 後執行

```text
python scripts/render_film_resvg.py PATH_TO_NODE REPO_DIR OUTPUT.mp4
```

正式輸出 1920×1080、24fps、H.264／yuv420p、無語音，可直接嵌入簡報或離線播放。
