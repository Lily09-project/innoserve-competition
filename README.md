# 融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架

> An AI Security Framework Integrating Novel Content Dependent Temporal Directional Intrusion Detection and Task Oriented Retrieval Augmented

**[開啟正式成果網站](https://lily09-project.github.io/innoserve-competition/)** ｜ **[40秒方法導覽](https://lily09-project.github.io/innoserve-competition/film/)** ｜ **[下載決賽簡報](https://lily09-project.github.io/innoserve-competition/deliverables/finals-deck.pptx)**

**2026 第 31 屆大專校院資訊應用服務創新競賽 · 資安技術組 · 決賽作品**

把「只有攻擊標籤的告警」，轉成**可查證、可稽核、可回復**的事件鏈。所有模組使用同一個事件識別碼，分析人員可以在同一個事件中回查判定依據、證據與處置結果。

```text
流量 ──▶ ① 17 類偵測 ──▶ ② Top-5 案例證據 ──▶ ③ AI 三態稽核 ──▶ ④ 受控處置與回復
          CTBM + PBCNN      529 維任務向量        支持／複核／不確定     Policy Guard
          OOF Gate          train-only 案例庫     不覆寫正式分類         限時・讀回・Rollback
```

## 三項創新

| | 創新 | 做法 | 輸出 |
|---|---|---|---|
| 一 | 內容相依時序方向判定 | CTBM 讀取封包內容、時間差與方向；PBCNN 補充短窗位元組模式；溫度校準後由 OOF Gate 依 59 項證據調權，並以 class-F1 guard 保護少數類別 | 固定 17 類事件與校準信心 |
| 二 | 任務導向證據檢索 | 512 維流量表徵與 17 維機率組成 529 維任務向量，L2 正規化後以餘弦相似度查詢只用訓練資料建立的案例庫 | 前五筆案例、相似度、類別共識 |
| 三 | 受控智慧稽核與可回復處置 | 本機大語言模型依證據回傳支持、複核或不確定；Policy Guard 檢查白名單、範圍、風險與有效期後才套用、讀回並到期回復 | 同事件的稽核與處置回條 |

## 實測成果

| 模組 | 評估範圍 | 實際結果 |
|---|---|---|
| 17類偵測（OOF Gate） | 18,998筆封存測試 | Accuracy **98.08%** · Macro-F1 **93.05%** |
| 任務導向檢索 | 1,550筆真實訓練案例 · 463筆測試查詢 | Top-5 **97.62%** · MRR@5 **93.89%** |
| 本機AI證據稽核 | 同一組463筆整合事件 | 支持415筆、複核13筆、不確定35筆；支持精確率 **97.11%** |
| 同事件鏈路驗證 | 17類真實張量輸入 · 17次本機AI呼叫 | 正式分類、Top-5、AI稽核與同批次處置回條銜接 |
| 隔離策略與回復 | 6種事件：4種套用規則、2種監測或蒐證 | 背景服務 **6/6** 保留；回復完整性 **6/6** 通過 |

30筆偵測誤判中，18筆分流至複核或不確定，12筆得到支持。AI稽核不改寫正式分類，處置仍由策略閘門檢查。隔離測試量測TCP測試交易、規則讀回及到期撤銷；實際施加規則的4種情境約30.11–30.14秒完成到期撤銷。

網站、簡報與影片統一引用 [`results/`](results/) 的四份實測彙整。偵測測試、463筆整合評估及隔離驗證各自標示範圍；本頁不混用歷史Fine-11模組結果。

## 網頁與交付內容

公開網站採主機控制面板風格：霧藍金屬板件、碳黑雙層導覽與橘色操作提示。桌面為830px固定機身與雙欄模組，手機改為單欄與可展開選單；頁首類別查詢直接連動17類實測結果。

公開網站可直接查看模型比較、17類可篩選結果、檢索與稽核統計、六種隔離驗證、系統架構與方法影片。所有圖表取自實測彙整檔，可下載JSON並核對來源SHA-256。瀏覽器版不執行GPU模型或網路處置，也不包含虛構事件、預設告警或合成案例庫。

- [正式成果網站](https://lily09-project.github.io/innoserve-competition/)
- [方法動畫](https://lily09-project.github.io/innoserve-competition/film/)：預設1.5倍速約40秒，可切換原速60秒或2倍速30秒；拓樸與封包路徑用於解說方法。
- [決賽簡報](deliverables/決賽簡報_AI資安框架.pptx)：8頁、含方法影片與逐頁備忘稿。
- [答詢與現場操作](docs/決賽展示與答詢.md)：方法、數據範圍、現場展示與備援。

## 本機執行



```bash
git clone --recurse-submodules https://github.com/Lily09-project/innoserve-competition.git
cd innoserve-competition
python -m venv .venv
python -m pip install -r requirements.txt   # 啟用虛擬環境後執行
```

依執行設備選擇合適的 PyTorch 安裝來源。本機模型展示已於 RTX 4090 驗證。

### 本機資產設定

公開版只包含程式與彙整結果；模型權重、原始封包、逐筆資料、模型回覆及本機設定不納入 Git。

1. 將 `config.example.json` 複製為 `config.local.json`，填入正式 IDS 結果目錄、流量資料目錄與本機 Llama 模型目錄。
2. 正式 IDS 結果目錄需包含 `runtime_sources/`、`models/augmented/seed_42/`、`gate_exports/` 及 `gate_results/`。以 `gate_impl_path` 指定對應的 `gate_soft_oof_search.py`；未設定時使用正式結果目錄上一層的同名檔案。模型、標籤順序與前處理版本必須一致。
3. 依序重建與稽核，再啟動服務：

```bash
python scripts/rebuild_retrieval.py
python scripts/run_local_judge.py
python scripts/prepare_closed_loop.py
python scripts/export_web_data.py
python app/server.py
```

開啟 <http://127.0.0.1:8765/>（Windows 也可直接執行「啟動作品.cmd」）。頁面可預載模型、選擇 17 類真實展示輸入、即時重跑、查看案例與匯出事件。

已有本機交付包時，可直接匯入私有展示資料（不下載或上傳資料，也不含模型授權）：

```bash
python scripts/import_local_assets.py --source PATH_TO_LOCAL_DELIVERY
```

匯入檔案位於 Git 忽略的 `evidence/` 與 `web/data.js`。尚未產生 `web/data.js` 時，工作台會顯示設定提示。

## 介面與系統展示影片

- **事件工作台**：全淺色介面，四階段事件鏈會隨「下一步」同步亮起；支援桌面、平板與手機、鍵盤頁籤及逐步檢視分類、證據、稽核與策略。設計規格見 [介面規格](design-system/MASTER.md)。
- **系統展示影片**：點選左側「系統展示影片」，預設以1.5倍速約40秒播放原長60秒動畫。影片以類似Packet Tracer的拓樸與封包動作說明方法流程，可暫停、跳章與全螢幕，並可輸出 MP4 嵌入簡報或作為離線備案，見 [影片說明](web/film/README.md)。

## 隔離網路驗證

需要 Windows WSL 的 Ubuntu-24.04、Mininet（實測 2.3.0）及 iptables，操作僅限自行建立的虛擬網路，展示服務只綁定 127.0.0.1。

- 「支持」且分類信心 ≥ 0.8、Top-5 至少 4 筆同類，才通過可干預處置門檻；複核與不確定事件維持蒐證或人工確認。
- 網路執行回條綁定同一事件與同次模型執行，拒絕過期批次的處置請求。
- 即時模式使用已準備的真實前處理張量，未包含任意 PCAP 上傳或實際鏡像擷取入口；隔離交易效果不等同原始攻擊封包的防禦率。

17 類與處置路徑對照見 [框架說明](FRAMEWORK.md)。

### 決賽前檢查

啟動服務後執行下列指令，核對模型與案例庫版本、CUDA、WSL 隔離環境及模型預載。預檢不部署網路規則，結果存於本機 `validation/finals_preflight.json`。

```bash
python scripts/preflight.py --warmup
```

> 決賽採匿名審查：簡報、影片與畫面不可出現學校名稱、校徽或指導老師姓名。`scripts/audit_final_chain.py` 會掃描交付內容中的可識別字串。

## 測試

合約測試不需要模型權重或原始流量：

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

## 目錄

```text
app/                    事件服務、策略閘門與本機模型服務
web/                    事件工作台（index.html / styles.css / app.js）
web/film/               系統展示影片與播放器
scripts/                資料重建、稽核、隔離驗證與影片輸出
tests/                  合約與異常處理測試
results/                可公開的彙整結果
design-system/          介面與視覺規格
sources/paper_code/     研究 B 固定版本 submodule
config.example.json     本機資產設定範例
```

## 協作

- 以 feature branch 開發，透過 Pull Request 合併到 `main`。
- 不要提交 `config.local.json`、`web/data.js`、`evidence/`、模型權重或原始封包（已列在 `.gitignore`）。
- 修改數字前核對 `results/` 的原始實測紀錄，簡報、動畫與網站一律引用同一版本。不得為了統一畫面而直接變更來源數據。

來源與使用範圍見 [NOTICE.md](NOTICE.md)。

## 公開網站建置

```bash
python scripts/build_public_site.py --output build/site
pnpm install --frozen-lockfile
pnpm run test:public
```

建置流程從混淆矩陣重新核對Accuracy、Macro-F1及逐類結果，檢查檢索、稽核、隔離情境的筆數與比率，再只複製公開彙整、簡報與方法影片。禁止將私有資料、模型權重、逐筆事件或本機設定加入網站產物。發布來源與雜湊記錄於 `publication-manifest.json`。

GitHub Actions 自動部署至 GitHub Pages；發布分支為 `release/verified-results-website`，合併後由 `main` 延續。原創程式採 [Apache-2.0](LICENSE)，第三方模型、資料與子模組維持原授權。
