# 公開成果網站：Console Chrome

依使用者提供的Nintendo.com circa 2001 design.md重新排版，保留實測內容、正式名稱、下載與方法動畫。此頁規格優先於MASTER中先前適用公開站的空間與卡片風格；本機模型與簡報資料不受視覺重排影響。

## Layout

- 桌面機身830px，頂部吉祥圖形／類別搜尋、碳黑主導覽、淺藍第二層工具列。
- 斜角hero全寬，主視覺採原創網路設備SVG與電路板色域，白色粗描邊字及硬陰影。
- 四項實測數據列；內容區兩欄，左側為方法、圖表與驗證，右側214px操作欄。
- 小於720px採單欄，操作欄接於內容後；主導覽改按鈕展開、工具列可水平捲動。原型固定寬度的美感保留於桌面，手機避免整頁橫向捲動。

## Tokens

canvas #7a8aba；raised #8ba1d4；sky #9fbee7；lavender #acace7；chrome #3d4f97；carbon #21242e；platinum #dedede。
導覽文字 #e48600；工具chip #ecab37；前進箭頭與操作 #f68d1f。暖色只用於操作、導覽與工具。

Arial／Helvetica／Microsoft JhengHei系統字型；標籤大寫及0.5px字距，正文12px；hero42px/36px白色描邊硬陰影。板件細線亮頂／暗底，0–2px直角，斜切主面板，logo與箭頭使用圓形。無柔焦陰影。

## Components and behavior

碳黑面板用CSS點陣，不載入外部字型或素材。品牌與像素盾牌為本作品原創，沒有Nintendo或Mario素材，也沒有未取得的認證標章。
首頁類別搜尋會直接填入17類結果篩選；GO有實際作用。手機選單維護aria-expanded，選取導覽後收起。桌面原型小chip保留密度；手機按鈕及獨立箭頭擴大至44px。

影片頁套用相同碳黑標頭、霧藍機身與橘金控制項。動畫本體、實測數字及速度不變。

## Verification

沿用數據一致性與下載檢查；補驗主頁搜尋、行動版導覽。以瀏覽器檢查830px機身、手機390px視窗、表格獨立水平捲動及所有連結。
