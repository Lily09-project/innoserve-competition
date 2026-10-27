# 決賽交付檔案

| 檔案 | 說明 |
|---|---|
| `決賽簡報_AI資安框架.pptx` | 8 頁決賽簡報（5 分鐘，已嵌入展示影片，備忘稿含逐頁講稿與時間） |
| `AI資安框架_系統展示影片_60秒.mp4` | Packet Tracer 模擬模式系統展示影片（1080p，亦為離線備案） |
| `figures/fig_architecture.png` | 系統架構圖（Python 繪製） |
| `figures/fig_problem.png` | 問題與解方對照圖 |

重新產生：`python scripts/presentation/figures.py deliverables/figures`、`python scripts/render_film_resvg.py NODE . deliverables/AI資安框架_系統展示影片_60秒.mp4`、`python scripts/presentation/build_deck.py deliverables/決賽簡報_AI資安框架.pptx deliverables/figures deliverables/AI資安框架_系統展示影片_60秒.mp4 deliverables/figures/video_poster.png`。
