# AI 資安框架：淺色介面規格

適用：web/index.html、web/styles.css、web/app.js、web/film。

依 UI/UX Pro Max 檢索「security operations light dashboard」。採用回傳的 Minimalism & Swiss Style，保留清楚網格、留白、可見焦點及狀態文字；回傳的深色配色與行銷轉換區塊不符本案，因此不採用。使用者明確要求整體淺色，以下為本案正式決策。

## 視覺（2026-10 決賽版）

- 網頁、簡報、展示影片一律採淺色：底色 #F5F8FC、面板 #FFFFFF、主文字 #0B1B33、次要文字 #5B6B82、主色 #1D4ED8。
- 六階段固定配色，跨網頁、簡報、影片與架構圖一致：資料輸入 #1D4ED8、偵測 #0F766E、檢索 #6D28D9、稽核 #B45309、處置 #C2410C、輸出 #0B1B33。
- 「事件鏈」（節點＋連線）是共同視覺符號；架構圖與圖示以 Python（matplotlib 向量圖元）繪製。
- 用語採正式報告語氣；畫面數字一律引用 `results/` 或系統概述文件的實測值。
- 決賽匿名審查：任何畫面不得出現校名、校徽或指導老師姓名。

## 視覺（初版，保留參考）

- 主背景 #F4F7FB，面板 #FFFFFF，主文字 #192B46，次要文字 #5D6C80。
- 藍色 #1558D6 表示主要動作與流程；綠色 #087963 表示驗證通過與回復；警告 #93600C、錯誤 #B32D3A 均搭配文字。
- 微軟正黑體與系統字型，不依賴外部字型服務。以 4/8px 間距節奏、7/12px 圓角及細邊線區分資訊，避免堆疊陰影。
- 左側導覽、上方模式標籤、執行控制、案例清單及事件面板構成正式工作台。窄螢幕改成頂端導覽與單欄流程。

## 操作

- 首次連線顯示可即時執行的 17 類輸入，預設 Bot。其他 463 筆保存案例透過篩選取得，列表以 40 筆逐批載入。
- 正式區分保存結果、即時模型及隔離回條。工作執行期間鎖定事件切換與互斥操作。
- 頁籤支援方向鍵、Home、End；表單具標籤；提供跳至主內容連結；動態工作狀態以 status 宣告。
- 匯出沿用後端原始 JSON 字串，保留既有雜湊數值格式。重設步驟不移除網路回條。
- 桌面、平板及手機尺寸檢查橫向溢位。動效只用於操作回饋；系統展示影片由使用者明確播放，可暫停及跳章。

## 參考方向

- [Cloudflare Application Services](https://www.cloudflare.com/application-services/products/)：服務資訊分層與將解決方案、驗證內容分開呈現；未複製品牌、圖片或文案。
- [Cisco Packet Tracer Simulation Mode](https://tutorials.ptnetacad.net/help/default/mode_simulation.htm)：以設備、封包路徑、事件與播放控制說明網路流程；本作以自行繪製的流程圖呈現。
- [Remotion 的逐幀概念](https://www.remotion.dev/docs/idea)：採用「時間決定畫面」的程式動畫方式。本案實作為原生 JavaScript/SVG、sharp 與 FFmpeg，未使用 Remotion 套件。
