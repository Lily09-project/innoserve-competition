# 決賽交付檔案

| 檔案 | 說明 |
|---|---|
| `決賽簡報_AI資安框架.pptx` | 8頁決賽簡報（已嵌入40秒快版方法影片，備忘稿含逐頁講稿；數據取自本repo四份實測彙整） |
| `AI資安框架_系統展示影片_40秒快版.mp4` | 正式展示用快版，已嵌入簡報，可直接離線播放 |
| `AI資安框架_系統展示影片_60秒.mp4` | Packet Tracer風格方法動畫（1080p、60秒；網站預設1.5倍速約40秒，可切換原速或2倍速） |
| `figures/fig_architecture.png` | 系統架構圖（Python 繪製） |
| `figures/fig_problem.png` | 問題與解方對照圖 |

重新產生：`python scripts/presentation/figures.py deliverables/figures`、`python scripts/render_film_resvg.py NODE . deliverables/AI資安框架_系統展示影片_60秒.mp4`、`python scripts/presentation/build_deck.py deliverables/決賽簡報_AI資安框架.pptx deliverables/figures deliverables/AI資安框架_系統展示影片_40秒快版.mp4 deliverables/figures/video_poster.png`。


## 正式呈現口徑

本版簡報與影片採用同一組17類實測彙整：偵測Accuracy98.08%、Macro-F1 93.05%；檢索Top-5 97.62%、MRR@5 93.89%；稽核415筆支持、13筆複核、35筆不確定。六種隔離情境包含四種規則套用與兩種監測／蒐證，不將六種都描述為套用規則。

影片的網路設備、封包路徑及PDU視窗用於方法解說；數據取自實測彙整。完整模型實測使用真實預處理張量，隔離測試量測TCP交易與規則回復。

[正式成果網站](https://lily09-project.github.io/innoserve-competition/)提供相同數據、互動圖表及下載。現場答詢見[決賽展示與答詢](../docs/決賽展示與答詢.md)。
