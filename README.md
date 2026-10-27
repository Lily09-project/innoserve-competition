# 融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架

> An AI Security Framework Integrating Novel Content Dependent Temporal Directional Intrusion Detection and Task Oriented Retrieval Augmented

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

## 實驗結果

| 模組 | 範圍 | 主要指標 |
|---|---|---|
| 17 類偵測（OOF Gate） | 封存測試 18,998 筆 | Accuracy **98.08%** · Macro-F1 **93.05%** |
| 任務檢索（系統概述文件） | 案例庫 1,550 筆 · 查詢 463 筆 | Top-5 **96.76%** · MRR@5 **94.25%** |
| 任務檢索（本 repo 重跑，`results/retrieval_17class.json`） | 同上規模 | Top-5 97.62% · MRR@5 93.89% |
| 本機 AI 稽核 | 463 筆事件 | 30 筆偵測誤判攔截 18 筆；支持精確率 97.11% |
| 歷史 Fine-11 模組（改良 FE-Net RAG） | 1,830 筆配對稽核 | Judge 準確率 98.85% · 錯誤攔截率 95.83% |

> 各項指標依各自實驗範圍呈現。歷史 Fine-11、522 維 FE-Net 的結果是獨立模組證據，不代表目前 17 類、529 維整合流程的重現結果。逐項數據見 [`results/`](results/)。

## 快速開始

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
- **系統展示影片**：點選左側「系統展示影片」播放 60 秒、以 Packet Tracer 模擬模式呈現一筆事件從流量擷取到處置回復的完整過程，可暫停、跳章與全螢幕，並可輸出 MP4 嵌入簡報或作為離線備案，見 [影片說明](web/film/README.md)。

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
- 修改數字前先更新 `results/` 的來源檔，簡報與動畫的數字需與系統概述文件一致。

來源與使用範圍見 [NOTICE.md](NOTICE.md)。
