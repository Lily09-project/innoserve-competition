# 系統展示影片（Packet Tracer 模擬模式）

啟動作品後開啟 `http://127.0.0.1:8765/film/index.html`，或從事件工作台點「系統展示影片」。

全片 60 秒，嵌入決賽 5 分鐘簡報（另留 1 分鐘緩衝），也是現場網路不穩時的離線備案。畫面採 Packet Tracer 模擬模式的呈現方式：

- **網路拓樸**：User-PC、Bot-PC、Switch、Mirror-TAP、Router、Policy-Guard、Web-Server，以及 IDS-Server、RAG-Store、LLM-Judge 三台 AI 節點。
- **PDU 封包**：信封圖示沿連線移動；正常流量（綠）持續通行，Bot 流量（紅）在 ACL 生效期間於策略閘道被攔下，到期後恢復。
- **PDU Information 視窗**：鏡頭推近目前處理的設備，視窗顯示該設備的 Inbound（輸入）、處理步驟與 Outbound（輸出）。
- **Simulation Panel · Event List**：底部事件清單依時間列出 Last Device、At Device 與 PDU 類型。

| 時間 | 設備 | 輸入 → 輸出 |
|---|---|---|
| 0:09 | Mirror-TAP | 原始封包 → 內容 bytes、Δt、方向張量 |
| 0:17 | IDS-Server | 模型張量 → 17 類正式機率 |
| 0:25 | RAG-Store | 529 維任務向量 → Top-5 案例證據 |
| 0:32 | LLM-Judge | 類別、信心、Top-5 → 稽核 JSON |
| 0:39 | Policy-Guard | 支持事件 → ACL 套用、讀回、30 秒到期回復 |
| 0:50 | Event Record | 各階段結果 → 雜湊綁定的事件紀錄 |

畫面上的數字全部取自 `results/` 與系統概述文件；處置段落使用 `results/framework_validation.json` 的 Bot 情境實測值（攻擊型測試交易成功率 100%→0%、背景服務 100%、30.12 秒到期撤銷）。封包內容一律以去識別化方式呈現。

- `scene.mjs`：時間軸、鏡頭、拓樸與純函式 `frameSvg(time)`。
- `player.mjs`：播放、暫停、拖曳進度、速度、跳章、全螢幕與鍵盤。
- `index.html`：播放器，不會自動啟動模型或部署策略。

## 輸出 MP4

HTML 與 MP4 共用同一個 `frameSvg`：

1. Node.js＋sharp＋FFmpeg：設定 `RENDER_NODE_MODULES`、`FFMPEG_BINARY` 後執行 `node scripts/render_product_film.mjs OUTPUT_DIRECTORY`。
2. Node.js＋Python：`pip install resvg-py imageio-ffmpeg` 後執行

```text
python scripts/render_film_resvg.py PATH_TO_NODE REPO_DIR OUTPUT.mp4
```

輸出 1920×1080、24fps、H.264／yuv420p、無語音。
