<!-- ppt-master-schema: design-spec/v1 -->

# Finals Editorial - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | Finals Editorial |
| Canvas Format | PPT 16:9, 1280×720 |
| Page Count | 12 |
| Primary Language | zh-TW |
| Target Audience | 資安技術組決賽評審 |
| Communication Intent | 以圖形說明創新方法及已量測效果 |
| Desired Audience Outcome | 了解同事件的偵測、證據稽核與受控處置 |
| Core Message / Ask / Action | 完整框架以事件回條連結判定、證據及回復 |
| Delivery Context | presenter-led；五分鐘含展示，另留一分鐘緩衝，七分鐘答詢 |
| Artifact Afterlife | GitHub審查及離線展演 |
| Reading Mode | presentation |
| Content Strategy | 保留正式實測範圍，精簡文字，重畫方法圖 |
| Design Style | 白底與淺灰章節，深藍、中藍與金黃重點；原創產品視覺 |
| AI Image Acquisition Path | built-in image_gen |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — workflow default |
| Custom Animations | disabled for decoration；第二頁全幅內嵌影片保留媒體播放時序，其他頁面靜態 |
| Narration Audio | disabled — workflow default |
| Created Date | 2026-10-28 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 64px |
| Content Area | 1152 × 592 |

## III. Visual Theme

### Theme Style

- **Mode**: custom
- **Mode Behavior**: 一頁一個主張，以方法流程引出實測結果。
- **Visual style**: custom
- **Visual Style Behavior**: 白底與淺灰章節，結語淺灰底#F0F2F3；輕量大標題、8px資訊面板、原創白藍AI圖示。
- **Theme**: 相同事件的四階段延續。
- **Tone**: 正式、簡潔、可核對。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | light canvas |
| Secondary background | #F0F2F3 | pale gray canvas |
| Primary | #105186 | main emphasis |
| Accent | #FDB338 | key evidence and active state |
| Title | #092B42 | headline |
| Secondary accent | #F0F2F3 | light panels |
| Body text | #171C1D | light ink |
| Secondary text | #53666E | captions |
| Divider | #D6DDE0 | hairline |

### AI Image Strategy

- **Image Rendering**: custom
- **Image Rendering Behavior**: 白色陶瓷與精確藍色細節的原創圖示。
- **Visual**: 四個透明圖示，Python排版，文字另層。
- **Mood**: 專業技術產品。

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | light | DFKai-SB | Times New Roman | none |
| Body | clear | DFKai-SB | Times New Roman | none |
- **Title stack**: DFKai-SB, Times New Roman
- **Body stack**: DFKai-SB, Times New Roman

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 44 |
| Subtitle | 28 |
| Annotation | 18 |
| Footer | 14 |
| Card title | 32 |
| Display | 56 |
| Q&A evidence metric | 38 |

## V. Layout Principles

- **Hierarchy direction**: 一個主張，再看圖，再看來源範圍。
- **Composition tendency**: 大圖與大型數值交替。
- **Cross-page continuity**: 四階段模型與原創圖示。
- **Spacing posture**: 章節寬鬆、流程緊密。
- **Spacing anchors**: margin64, gap24, gutter32, radius8, leading36。

## VI. Icon Usage Specification

- **Primary bundled library**: none
| Icon Path | Suitable Scenarios |
| --- | --- |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| icon-1.png | 600×600 | 1:1 | 方法節點 | Illustrated icon | isolated diagram cue | no-crop | slice | Generated | security-icons-sheet.png | none | support |
| icon-2.png | 600×600 | 1:1 | 方法節點 | Illustrated icon | isolated diagram cue | no-crop | slice | Generated | security-icons-sheet.png | none | support |
| icon-3.png | 600×600 | 1:1 | 方法節點 | Illustrated icon | isolated diagram cue | no-crop | slice | Generated | security-icons-sheet.png | none | support |
| icon-4.png | 600×600 | 1:1 | 方法節點 | Illustrated icon | isolated diagram cue | no-crop | slice | Generated | security-icons-sheet.png | none | support |

## IX. Content Outline

#### Slide 01 - 融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: order：偵測→檢索→稽核→回復
- **Topology**: yes
- **Composition**: 封面標題搭配四節點事件鏈
- **Geometry signature**: 融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架 → 封面標題搭配四節點事件鏈 → 淺色原生形狀與藍色連線。
- **Title**: 融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架
- **Core message**: 四個互相銜接的能力，從流量走到可回復處置。
- **Content**: 四個互相銜接的能力，從流量走到可回復處置。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 02 - 一個事件，走完完整流程

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: none
- **Topology**: no
- **Composition**: 淺色16:9空間與置中播放提示
- **Geometry signature**: 一個事件，走完完整流程 → 淺色16:9空間與置中播放提示 → 淺色原生形狀與藍色連線。
- **Title**: 一個事件，走完完整流程
- **Core message**: 保留16:9全幅影片，產品方法動畫30秒、2倍速，以內嵌MP4播放。
- **Content**: 保留16:9全幅影片，產品方法動畫30秒、2倍速，以內嵌MP4播放。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 03 - 一個框架，四個連續階段

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: link / membership：四區及同事件交接
- **Topology**: yes
- **Composition**: 沿用兩層完整總架構
- **Geometry signature**: 一個框架，四個連續階段 → 沿用兩層完整總架構 → 淺色原生形狀與藍色連線。
- **Title**: 一個框架，四個連續階段
- **Core message**: 四區巢狀架構，CTBM/PBCNN並行，529維檢索，本機AI及受控處置。
- **Content**: 四區巢狀架構，CTBM/PBCNN並行，529維檢索，本機AI及受控處置。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 04 - 互補模型，形成同一次判定

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: link：同輸入平行兩支，再匯流至Gate
- **Topology**: yes
- **Composition**: 雙分支匯流，圖中列出模型讀取的資訊
- **Geometry signature**: 互補模型，形成同一次判定 → 雙分支匯流，圖中列出模型讀取的資訊 → 淺色原生形狀與藍色連線。
- **Title**: 互補模型，形成同一次判定
- **Core message**: 內容、時間差、方向進入CTBM；短窗位元組模式進入PBCNN；校準融合後17類、信心及表徵交接。
- **Content**: 內容、時間差、方向進入CTBM；短窗位元組模式進入PBCNN；校準融合後17類、信心及表徵交接。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 05 - 把偵測表徵，變成可核對的證據

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: order / link：向量組合→檢索→稽核分支
- **Topology**: yes
- **Composition**: 向量拼接與案例卡列，接三態稽核
- **Geometry signature**: 把偵測表徵，變成可核對的證據 → 向量拼接與案例卡列，接三態稽核 → 淺色原生形狀與藍色連線。
- **Title**: 把偵測表徵，變成可核對的證據
- **Core message**: 512維表徵＋17維機率形成529維任務向量；L2正規化後檢索訓練庫Top-5，本機AI輸出支持/複核/不確定。
- **Content**: 512維表徵＋17維機率形成529維任務向量；L2正規化後檢索訓練庫Top-5，本機AI輸出支持/複核/不確定。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 06 - 受控執行，留下可回復的處置紀錄

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: order / link：通過路徑與蒐證分支
- **Topology**: yes
- **Composition**: 四站主路徑與低位蒐證支線
- **Geometry signature**: 受控執行，留下可回復的處置紀錄 → 四站主路徑與低位蒐證支線 → 淺色原生形狀與藍色連線。
- **Title**: 受控執行，留下可回復的處置紀錄
- **Core message**: 政策檢查→套用→讀回→到期回復，複核/不確定分流蒐證，6種隔離TCP情境背景與回復6/6。
- **Content**: 政策檢查→套用→讀回→到期回復，複核/不確定分流蒐證，6種隔離TCP情境背景與回復6/6。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 07 - 互補融合，提升整體辨識效果

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: contrast：同資料集三方法比較
- **Topology**: no
- **Composition**: 0–100%水平長條與獨立準確率面板
- **Geometry signature**: 互補融合，提升整體辨識效果 → 0–100%水平長條與獨立準確率面板 → 淺色原生形狀與藍色連線。
- **Title**: 互補融合，提升整體辨識效果
- **Core message**: 同18,998筆測試Macro-F1：79.75%、92.10%、93.05%；Accuracy98.08%。
- **Content**: 同18,998筆測試Macro-F1：79.75%、92.10%、93.05%；Accuracy98.08%。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json
- **Visualization**: detector-comparison | horizontal_bar_chart | direct-calc | Macro-F1, scale 0–100%, same 18,998 tests; rect x=200,y=220,x_max=850,y_max=550.
- **Native-ready**: detector-comparison=no; editable native SVG shapes, not an embedded chart object.

#### Slide 08 - 案例提供證據，AI完成分流

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: link / parent：463事件分成三個稽核結論
- **Topology**: yes
- **Composition**: 左側檢索效果，右側三態分流，底部誤判結果
- **Geometry signature**: 案例提供證據，AI完成分流 → 左側檢索效果，右側三態分流，底部誤判結果 → 淺色原生形狀與藍色連線。
- **Title**: 案例提供證據，AI完成分流
- **Core message**: 1550訓練案例、463查詢；Top5 97.62%、MRR@5 93.89%；415支持13複核35不確定；18/30誤判分流。
- **Content**: 1550訓練案例、463查詢；Top5 97.62%、MRR@5 93.89%；415支持13複核35不確定；18/30誤判分流。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 09 - 偵測有依據，稽核有證據，處置可回復

- **Audience move**: 看懂本頁資料流及可核對的成果。
- **Relationships**: order / membership：同事件四個證據產物
- **Topology**: yes
- **Composition**: 四個具體產物串成完整作品結語
- **Geometry signature**: 偵測有依據，稽核有證據，處置可回復 → 四個具體產物串成完整作品結語 → 淺色原生形狀與藍色連線。
- **Title**: 偵測有依據，稽核有證據，處置可回復
- **Core message**: 17類真實張量與6種隔離情境，事件ID串起分類、證據與回條。
- **Content**: 17類真實張量與6種隔離情境，事件ID串起分類、證據與回條。
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 10 - 答詢備用 1

- **Audience move**: 以既有證據回答評審提問。
- **Relationships**: contrast / membership：兩個獨立問題各以圖解與證據回答。
- **Topology**: no
- **Composition**: 上下雙問題圖解：事件鏈、集合切分、誤判分支、驗證範圍與本機部署圖；右側突出證據。
- **Geometry signature**: 問題 → 流程／分支圖解 → 證據標籤。
- **Title**: 答詢備用 1
- **Content**: 創新在哪裡？與一般 IDS 加上 RAG 有何不同？ 如何證明前段判斷與後段處置已經串起來？
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 11 - 答詢備用 2

- **Audience move**: 以既有證據回答評審提問。
- **Relationships**: contrast / membership：兩個獨立問題各以圖解與證據回答。
- **Topology**: no
- **Composition**: 上下雙問題圖解：事件鏈、集合切分、誤判分支、驗證範圍與本機部署圖；右側突出證據。
- **Geometry signature**: 問題 → 流程／分支圖解 → 證據標籤。
- **Title**: 答詢備用 2
- **Content**: 評估資料如何切分？案例庫是否洩漏測試答案？ AI 若支持錯誤判斷，如何避免直接誤封？
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

#### Slide 12 - 答詢備用 3

- **Audience move**: 以既有證據回答評審提問。
- **Relationships**: contrast / membership：兩個獨立問題各以圖解與證據回答。
- **Topology**: no
- **Composition**: 上下雙問題圖解：事件鏈、集合切分、誤判分支、驗證範圍與本機部署圖；右側突出證據。
- **Geometry signature**: 問題 → 流程／分支圖解 → 證據標籤。
- **Title**: 答詢備用 3
- **Content**: 6/6 是否代表各種真實攻擊都能完全防住？ 如何部署、保護資料，並接到既有環境？
- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match SVG names under notes/
- **Content**: 正式口語；第2頁全幅內嵌播放30秒，不另加講解。
- **Total duration**: 260秒口述＋30秒影片＋10秒正常操作＝5分鐘；另留1分鐘緩衝。
- **Notes style**: 繁體中文。
- **Transitions**: none；manual advance；所有頁面無p:transition；第2頁僅保留影片播放timing，其他頁面無物件動畫。

## XI. Script-specific fonts

中文及中文標點使用標楷體DFKai-SB；英文、數字與其他符號使用Times New Roman，混合文字在同一文字框依字元分段。影片預留頁置於封面後，第2頁，影片以內嵌MP4置入，進入第2頁自動播放一次，結束停留該頁。

## XII. Embedded opening film

第2頁原生內嵌30秒H.264影片，自動播放一次，不循環且不自動換頁。封面後先展示動畫；第9頁為結束頁並保留完整作品價值與答詢提示。影片最後1.5秒獨立結束畫面，兩倍速及30秒總長維持。

## XIII. Q&A appendix

第1至9頁為五分鐘正式報告，第9頁結束；第10至12頁每頁兩題，共六題，只於七分鐘答詢依提問切換，不納入正式講述時間。正文與備詢均以圖解呈現，詳細口語答案放講者備忘稿。問題與答案依實測範圍，不將TCP驗證解讀成原生攻擊防禦率。

## XIV. Illustrated explanation revision

原創PNG圖示與原生線稿共同承擔說明：封包、向量、模型晶片、防火牆、讀回文件、時鐘及狀態標誌。主報告的雙模型、任務向量、受控處置與成果節點均以圖像對應方法角色；備詢加入案例集合、文件產物、隔離設備及本機工作站插圖。圖示僅表示物件與流程，不編碼個別事件機率、特徵值或未量測效果。圖表幾何與結果數值不變。

## XV. User supplied light navy, blue and gold palette

依使用者配色圖標示色碼：深藍#092B42、中藍#105186、淺灰#F0F2F3、金黃#FDB338、深墨#171C1D。白色為主要底色，淺灰為次要底；金黃標示本方法長條、導覽當前步驟與關鍵連結。金黃上只放深色文字，不用金黃細字搭白底。原創立體PNG保留原始藍色高光，不重畫圖示形狀。平面色彩、PPT、影片及海報共用design-system/palette.json。
