# 可編輯來源與素材紀錄

- architecture.svg：Python排版的四區巢狀架構圖；標籤為獨立SVG文字。
- flat-icon-1.svg至flat-icon-4.svg及同名PNG：目前使用的共用平面圖示，來源為design-system/icons.json；PPT使用可編輯向量，海報使用相同圖形的透明PNG。
- icon-1.png至icon-4.png、security-icons-sheet.png：保留的早期AI生成素材，現行簡報、海報與影片均不使用，並非實驗資料。
- slides/：PPT Master逐頁SVG來源；native PowerPoint保留可編輯標籤、圖形及數值。
- speaker-notes.md：正式講者備忘稿。
- poster-a2-spec.md：A2直式海報尺寸、閱讀順序與印刷輸出規格；海報原生製作來源為scripts/presentation/build_a2_poster.py。

歷史AI圖示prompt：transparent background; four isolated evenly spaced icons: network flow switch, neural model chip, retrieval database with magnifier, shield with check and return arrow; no text/numerals/logos; white ceramic, satin pale gray, precise #0070D1 accents, publication-quality scientific illustration. Python僅裁出四個圖示與組合流程，未以AI產生數據、標籤或測試結論。

歷史素材製作方式：內建image_gen，生成2026-10-28；現行成果已改用共用平面圖示。架構圖參考Nature圖表指南的整齊分區、可編輯標籤與清楚閱讀順序，投影版放大字體，使用原創資安圖像。品牌視覺依使用者指定的淺色底與藍色重點設計轉譯，不含PlayStation商標或SST專有字型。

正式成片：30秒、2倍速、1080p／24fps。原始程式時間軸以60秒定義，輸出時直接採樣至30秒，並非交付60秒影片。簡報共12頁，前9頁為正式報告、後3頁為答詢備用；第3頁與本架構SVG採同一排版來源，第4頁雙模型明確並行。

presentation-design-spec.md與presentation-spec-lock.md描述PPT Master製作專案。交付的slides/包含原生向量圖示，直接開啟SVG即可查看，不依賴外部圖片路徑。

三種成果共用design-system/palette.json、typography.json及icons.json。中文與中文標點使用DFKai-SB（標楷體），英文、數字及其他支援符號使用Times New Roman；SVG以tspan分段呈現。PPT匯出後以scripts/presentation/finalize_delivery.py同步清理正文、備忘稿、母片、版型與主題內的所有字型宣告及主題色。內嵌影片頁為第2頁，封面後先展示，影片已內嵌。

完整製作順序：PPT Master匯出靜態原生頁→finalize_delivery.py設定字型→embed_opening_film.ps1以PowerPoint內嵌30秒影片至第2頁→finalize_delivery.py再次確認字型並清除作者中繼資料。第2頁SVG是版面來源，實際MP4由包裝步驟加入，不以外部連結播放。影片與PPT均有結束畫面。

對齊驗收：先以measure_alignment.ps1 -CorrectText另存校正副本，依實際字形邊界調整左右及置中錨點，再以finalize_delivery.py輸出正式檔（海報加--a2以還原Office另存時四捨五入的A2尺寸）；ALIGNMENT_TARGET_X標籤保留原始對齊目標，重跑不累積偏移。audit_alignment.py產生逐頁對齊線圖及0.1pt容差報告，audit_film_alignment.mjs檢查影片標籤置中與對齊線。這些對齊線只供驗收，不出現在正式成果。
