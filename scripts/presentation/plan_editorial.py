"""Retain the already delegated two-stage presentation decisions."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'projects/finals_editorial_ppt169_20261028'
titles=['融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架','一個框架，四個連續階段','創新一：讓互補模型共同判斷','創新二：用任務證據完成稽核','創新三：處置可驗證，也可回復','互補融合，提升整體辨識效果','從相似案例，走到可核對的結論','偵測有依據，稽核有證據，處置可回復']
contents=['完整作品名稱；從流量判定到有證據的處置。','流量表徵→17類判定→證據檢索與稽核→受控處置與回復；同一事件ID。','CTBM內容與時序；PBCNN短窗模式；校準後OOF Gate融合。','512＋17＝529維；Top-5訓練案例；本機AI支持、複核、不確定。','政策閘門→套用與讀回→到期回復；4規則＋2監測，背景6/6與回復6/6。','同18,998筆：PBCNN79.75%、CTBM92.10%、OOF Gate93.05% Macro-F1；Accuracy98.08%。','463查詢、1550案例；Top-5 97.62%、MRR@5 93.89%、支持精確率97.11%；415/13/35；18/30誤判分流。','17類真實張量重跑、6種隔離情境；獨立方法動畫。']
fields={'Project Name':'Finals Editorial','Canvas Format':'PPT 16:9, 1280×720','Page Count':'8','Primary Language':'zh-TW','Target Audience':'資安技術組決賽評審','Communication Intent':'以圖形說明創新方法及已量測效果','Desired Audience Outcome':'了解同事件的偵測、證據稽核與受控處置','Core Message / Ask / Action':'完整框架以事件回條連結判定、證據及回復','Delivery Context':'presenter-led；六分鐘含展示，七分鐘答詢','Artifact Afterlife':'GitHub審查及離線展演','Reading Mode':'presentation','Content Strategy':'保留正式實測範圍，精簡文字，重畫方法圖','Design Style':'黑白章節與精準藍色強調；原創產品視覺','AI Image Acquisition Path':'built-in image_gen','Generation Mode':'continuous','Spec Refinement':'disabled','Speaker Notes':'enabled — workflow default','Custom Animations':'disabled — workflow default；影片獨立','Narration Audio':'disabled — workflow default','Created Date':'2026-10-28'}
s='<!-- ppt-master-schema: design-spec/v1 -->\n# Finals Editorial - Design Spec\n\n## I. Project Information\n\n| Item | Value |\n| --- | --- |\n'+''.join(f'| {k} | {v} |\n' for k,v in fields.items())
s+='''
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
- **Visual Style Behavior**: 黑白全幅章節交替，結尾一頁#0070D1；輕量大標題、8px資訊面板、原創白藍AI圖示。
- **Theme**: 相同事件的四階段延續。
- **Tone**: 正式、簡潔、可核對。
### Color Scheme
| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | light canvas |
| Secondary background | #000000 | dark canvas |
| Primary | #0070D1 | main emphasis |
| Accent | #53B1FF | dark-canvas emphasis |
| Secondary accent | #181818 | dark panels |
| Body text | #000000 | light ink |
| Secondary text | #6B6B6B | captions |
| Divider | #CCCCCC | hairline |
### AI Image Strategy
- **Image Rendering**: custom
- **Image Rendering Behavior**: 白色陶瓷與精確藍色細節的原創圖示。
- **Visual**: 四個透明圖示，Python排版，文字另層。
- **Mood**: 專業技術產品。
## IV. Typography System
### Font Plan
| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | light | Microsoft JhengHei | Arial | Helvetica |
| Body | clear | Microsoft JhengHei | Arial | Helvetica |
- **Title stack**: Microsoft JhengHei, Arial
- **Body stack**: Microsoft JhengHei, Arial
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
'''
for i in range(1,5):s+=f'| icon-{i}.png | 600×600 | 1:1 | 方法節點 | Illustrated icon | isolated diagram cue | no-crop | slice | Generated | security-icons-sheet.png | none | support |\n'
s+='\n## IX. Content Outline\n'
for i,(t,c) in enumerate(zip(titles,contents),1):s+=f'\n#### Slide {i:02d} - {t}\n- **Audience move**: 理解本頁方法與結果。\n- **Relationships**: '+('依序串接同一事件。' if i in (2,3,4,5) else '同範圍資料的比較與說明。')+f'\n- **Title**: {t}\n- **Core message**: {c}\n- **Content**: {c}\n- **Fact IDs**: results/detection_17class.json; results/retrieval_17class.json; results/local_judge_17class.json; results/framework_validation.json\n'
s+='\n## X. Speaker Notes Requirements\n- **Generation**: enabled\n- **Filename**: match SVG names under notes/\n- **Content**: 只解說頁面與實測範圍。\n- **Total duration**: 六分鐘含40秒方法動畫。\n- **Notes style**: 正式口語繁體中文。\n- **Presentation purpose**: 說明方法創新與實測成果。\n'
(P/'design_spec.md').write_text(s,encoding='utf-8')
lock='''<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock
## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9
## communication
- primary_language: zh-TW
- audience: 資安技術組決賽評審
- objective: 了解四階段方法創新與正式實測效果。
- core_message: 同一事件串接偵測、證據、稽核及回復。
- consumption_mode: presentation
## mode
- mode: custom
- mode_behavior: 方法圖引導，實測結果佐證。
## visual_style
- visual_style: custom
- visual_style_behavior: 黑白章節交替，單頁藍色收尾，輕量標題，8px平面面板與原創圖示。
## colors
- background: #FFFFFF
- secondary_bg: #000000
- primary: #0070D1
- accent: #53B1FF
- secondary_accent: #181818
- body_text: #000000
- secondary_text: #6B6B6B
- divider: #CCCCCC
## typography
- font_family: Microsoft JhengHei, Arial
- title_family: Microsoft JhengHei, Arial
- body_family: Microsoft JhengHei, Arial
- body: 24
- title: 44
- subtitle: 28
- annotation: 18
- footer: 14
- card_title: 32
- display: 56
## icons
- library: none
- inventory: none
## page_rhythm
- P01: anchor
- P02: dense
- P03: anchor
- P04: anchor
- P05: anchor
- P06: breathing
- P07: breathing
- P08: anchor
## pptx_structure
- mode: flat
## images
'''+''.join(f'- icon{i}: images/icon-{i}.png | source=slice | crop=no-crop\n' for i in range(1,5))+'''## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
'''
(P/'spec_lock.md').write_text(lock,encoding='utf-8')
print(P)
