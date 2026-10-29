# 決賽交付

| 檔案 | 用途 |
| --- | --- |
| 決賽簡報_AI資安框架.pptx | 12頁可編輯簡報（9頁正式＋3頁答詢備用），附講者備忘稿；第2頁全幅內嵌30秒影片 |
| 決賽簡報_AI資安框架.pdf | 簡報預覽與離線備援 |
| AI資安框架_系統展示影片_30秒快版.mp4 | 1080p、2倍速、30秒正式展示 |
| 決賽海報_AI資安框架_A2.pptx | A2直式420×594mm，原生可編輯方法海報 |
| 決賽海報_AI資安框架_A2.pdf | PowerPoint PDF/A輸出，中英文字型嵌入，供印刷 |
| 決賽離線展示包.zip | 簡報、影片、海報與備忘稿備援，附SHA256清單；不含模型部署 |
| figures/poster-a2-preview.png | 海報螢幕預覽，印刷請用PDF |
| figures/fig_architecture.png | 四區巢狀架構圖，2560×1072 |
| source/architecture.svg | 文字可編輯原稿 |
| source/slides/ | 逐頁可編輯SVG |

簡報與影片採白底、淺灰章節及深藍、中藍與金黃重點。所有數值取自results四份實測彙整；動畫拓樸為方法說明，隔離驗證效果為TCP測試交易與回條。交付內容保持匿名。簡報第2頁內嵌影片，並保留獨立MP4備援；正式順序為第1頁封面、第2頁影片、第3至9頁方法與成果；第10至12頁供答詢。

簡報製作來源：scripts/presentation/editorial_assets.py；影片來源：media/film/scene.mjs及scripts/render_product_film.mjs。三種成果共用配色、字型及平面向量圖示。簡報PPTX以PPT Master原生DrawingML編譯，圖形及文字可編輯。海報由scripts/presentation/build_a2_poster.py使用python-pptx製作，經PowerPoint輸出與文字框檢查。詳見source/README.md與design-system/DESIGN.md。

海報保留15mm安全邊界，不含品牌識別或公開庫二維碼。印刷前依印刷廠確認紙材、出血及局部實際尺寸打樣。模型展示操作與實際彩排清單見docs/本機展示操作單.md及docs/展前驗收與備援.md。

加豐版海報包含四階段產物、Top-5順位圖卡、多類事件策略及六種隔離情境的實測路徑。source/slides/已同步最新12頁設計，並納入source/delivery-manifest.json逐檔雜湊。公開內容與私有資料的盤點見[公開發布盤點](../docs/公開發布盤點.md)。
