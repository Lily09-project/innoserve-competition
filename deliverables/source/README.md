# 可編輯來源與素材紀錄

- architecture.svg：Python排版的四區巢狀架構圖；標籤為獨立SVG文字。
- icon-1.png至icon-4.png：600×600透明圖示。
- security-icons-sheet.png：內建image_gen生成的原始圖示素材，並非實驗資料。
- slides/：PPT Master逐頁SVG來源；native PowerPoint保留可編輯標籤、圖形及數值。
- speaker-notes.md：正式講者備忘稿。

AI圖示prompt：transparent background; four isolated evenly spaced icons: network flow switch, neural model chip, retrieval database with magnifier, shield with check and return arrow; no text/numerals/logos; white ceramic, satin pale gray, precise #0070D1 accents, publication-quality scientific illustration. Python僅裁出四個圖示與組合流程，未以AI產生數據、標籤或測試結論。

製作方式：內建image_gen，生成2026-10-28。架構圖參考Nature圖表指南的整齊分區、可編輯標籤與清楚閱讀順序，投影版放大字體，使用原創資安圖像。品牌視覺依使用者指定的淺色底與藍色重點設計轉譯，不含PlayStation商標或SST專有字型。

正式成片：30秒、2倍速、1080p／24fps。原始程式時間軸以60秒定義，輸出時直接採樣至30秒，並非交付60秒影片。簡報保留9頁；第3頁與本架構SVG採同一排版來源，第4頁雙模型明確並行。

presentation-design-spec.md與presentation-spec-lock.md描述PPT Master製作專案，其中images/指製作工作目錄，editorial_assets.py會同步圖示。交付的slides/另使用相對路徑引用上層icon，直接開啟SVG即可查看。

PPT匯出後以scripts/presentation/finalize_delivery.py設定原生Latin字型Times New Roman及East Asian字型DFKai-SB（標楷體）；SVG同一文字框以tspan分段呈現。影片預留頁為第2頁，封面後先展示，尚未嵌入影片。影片本身的字型維持原版。
