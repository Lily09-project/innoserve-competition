# 決賽交付

| 檔案 | 用途 |
| --- | --- |
| 決賽簡報_AI資安框架.pptx | 12頁可編輯簡報（9頁正式＋3頁答詢備用），附講者備忘稿；第2頁全幅內嵌30秒影片 |
| 決賽簡報_AI資安框架.pdf | 簡報預覽與離線備援 |
| AI資安框架_系統展示影片_30秒快版.mp4 | 1080p、2倍速、30秒正式展示 |
| figures/fig_architecture.png | 四區巢狀架構圖，2560×1072 |
| source/architecture.svg | 文字可編輯原稿 |
| source/slides/ | 逐頁可編輯SVG |

簡報與影片採白底、淺灰章節與藍色重點。所有數值取自results四份實測彙整；動畫拓樸為方法說明，隔離驗證效果為TCP測試交易與回條。交付內容保持匿名。簡報第2頁內嵌影片，並保留獨立MP4備援；正式順序為第1頁封面、第2頁影片、第3至9頁方法與成果；第10至12頁供答詢。

製作來源：scripts/presentation/editorial_assets.py、media/film/scene.mjs、scripts/render_product_film.mjs。PPTX以PPT Master原生DrawingML編譯，圖示為AI生成，流程與文字由Python排版。詳見source/README.md與design-system/DESIGN.md。
