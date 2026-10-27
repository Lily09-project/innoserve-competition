# 資服競賽

**[直接開啟線上展示](https://lily09-project.github.io/innoserve-competition/)** · **[45秒產品動畫](https://lily09-project.github.io/innoserve-competition/film/)**

AI資安框架展示專案，整合固定17類入侵偵測、任務導向Top-5案例檢索、本機AI稽核與可回復的隔離策略驗證。

正式作品名稱：融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架。

完整交接、17類策略路徑與展示範圍見[框架說明](FRAMEWORK.md)。

## 功能

- 淺色正式事件工作台，支援桌面與行動版、鍵盤頁籤、案例分頁及逐步檢視分類、證據、稽核與策略。
- CTBM與PBCNN經凍結OOF Gate輸出17類正式機率。
- 512維流量表徵與17維正式機率組成529維任務向量，執行train-only Top-5檢索。
- 本機Llama 3 8B Instruct回傳支持、複核或不確定，正式分類保持不變。
- 事件識別碼、輸入綁定及雜湊鏈支援結果追溯。
- 支援Mininet合成TCP交易驗證、規則讀回與實際30秒到期回復。
- 網路執行回條綁定同一事件及同次模型執行，接續前段紀錄；拒絕過期批次的處置請求。

## 取得程式

```bash
git clone --recurse-submodules https://github.com/Lily09-project/innoserve-competition.git
cd innoserve-competition
python -m venv .venv
```

啟用虛擬環境後安裝：

```bash
python -m pip install -r requirements-test.txt
```

以上安裝足以啟動公開合成展示，不需要 PyTorch、模型權重或私有資料：

```bash
python app/server.py --demo
```

開啟 http://127.0.0.1:8765/ 。服務自動在 `runtime/synthetic-demo/` 產生17筆合成事件及85筆合成案例，畫面標示「合成資料，非實測」。可操作流程、重算檢索及匯出紀錄；模型、AI生成及網路處置均停用。重算走正式的檢索與策略合約，沒有模型推論成效宣稱。

也可先執行 `python scripts/make_demo_assets.py --output PATH_TO_EMPTY_DEMO_FOLDER`，再用 `python app/server.py --demo --demo-root PATH_TO_EMPTY_DEMO_FOLDER` 啟動。產生器拒絕覆寫非空資料夾。已生成展示資產不會自動更新；修改介面後請指定新的空展示目錄。

完整本機模型模式再安裝 `python -m pip install -r requirements.txt`。依設備先從 PyTorch 官方來源安裝符合 CUDA 的版本（requirements 要求 torch>=2.7,<3），再安裝其餘需求；pip 會保留符合範圍的既有版本。本機模型展示已於 RTX 4090 驗證。

## 本機資產設定

公開版包含程式與彙整結果。模型權重、原始封包、逐筆資料、模型回覆及本機設定不納入Git。

1. 將`config.example.json`複製為`config.local.json`，填入正式IDS結果目錄、流量資料目錄與本機Llama模型目錄。
2. 正式IDS結果目錄需包含`runtime_sources/`、`models/augmented/seed_42/`、`gate_exports/`及`gate_results/`。以`gate_impl_path`指定對應的`gate_soft_oof_search.py`；未設定時使用正式結果目錄上一層的同名檔案。模型、標籤順序與前處理版本必須一致。
3. 依序執行重建與稽核：

```bash
python scripts/rebuild_retrieval.py
python scripts/run_local_judge.py
python scripts/prepare_closed_loop.py
python scripts/export_web_data.py
python app/server.py
```

開啟 http://127.0.0.1:8765/ 。Windows也可使用「啟動作品.cmd」。頁面可預載模型、選擇17類真實展示輸入、即時重跑、查看案例與匯出事件。

既有本機交付包可用下列指令匯入私有展示資料：

```bash
python scripts/import_local_assets.py --source PATH_TO_LOCAL_DELIVERY
```

匯入檔案位於Git忽略的`evidence/`與`web/data.js`。這個步驟不下載或上傳資料，也不包含模型授權。

## 驗證範圍

本次重建使用1,550筆真實train案例與463筆test查詢，Top-5命中率97.62%，MRR@5為93.89%。採每類前100筆train與前30筆test，稀有類別依可用數量納入，因此這是類別配額的整合驗證。

本機Llama對463筆事件產生結構化回覆，30筆偵測誤判中攔截18筆，12筆得到支持。系統保留證據門檻、策略檢核與人工複核，不將稽核解讀為零誤判保證。詳見`results/`。

即時模式使用已準備的真實前處理張量，未包含任意PCAP上傳或實際網路鏡像擷取入口。隔離交易效果不等同原始攻擊封包的防禦率。

## 隔離網路

網路驗證需要Windows WSL的Ubuntu-24.04、Mininet及iptables，操作僅限自行建立的虛擬網路。實測Mininet版本為2.3.0。

複核與不確定事件維持蒐證或人工確認；無既有驗證策略的類別走蒐證處理。展示服務只綁定127.0.0.1。

決賽上場前，啟動服務後執行`python scripts/preflight.py --warmup`，核對模型與案例庫版本、CUDA、WSL隔離環境及模型預載。預檢不部署網路規則，結果保存在本機`validation/finals_preflight.json`。

## 測試

合約測試不需要模型權重或原始流量：

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

## 目錄

```text
app/                    事件介面、策略閘門與本機模型服務
web/                    展示介面（私有 data.js 不提交）
web/film/               程式動畫
design-system/          介面設計規範
.github/                CI、PR 範本及 CODEOWNERS
scripts/                資料重建、稽核與隔離驗證
tests/                  合約與異常處理測試
results/                可公開彙整結果
sources/paper_code/     研究B固定版本submodule
config.example.json     本機資產設定範例
```

原創程式採 [Apache-2.0](LICENSE)。第三方來源與使用範圍見 [NOTICE.md](NOTICE.md)，協作流程見 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 產品動畫與介面

工作台採用淺色介面，設計決策見 [介面規格](design-system/MASTER.md)。啟動服務後，點選「產品動畫」即可播放45秒快版，另可切換約30秒／23秒播放，支援暫停、跳章及全螢幕。動畫來源、影片輸出方式及示意範圍見 [動畫說明](web/film/README.md)。

## 架構

```mermaid
flowchart LR
  Input[17類事件輸入] --> Detector[CTBM / PBCNN + OOF Gate]
  Detector --> Vector[512維表徵 + 17維機率]
  Vector --> Retrieve[訓練案例 Top-5]
  Retrieve --> Judge[本機 AI 證據稽核]
  Judge --> Guard[策略檢核與人工複核分流]
  Guard --> Network[隔離網路驗證與回復]
  Network --> Ledger[同事件／同批次雜湊紀錄]
```

正式分類保持不變；17類均有明確策略路徑，其中11類具有已驗證的隔離流量設定，其餘採蒐證或複核。`LABELS` 是17類模型輸出順序，`B_NAMES` 是其中11類對應上游隔離設定的名稱，不能以其長度取代正式分類數。

## 設定與品質檢查

`config.example.json` 列出資產位置、WSL 發行版／使用者、掛載根目錄、網路逾時、工作保留時間與服務埠。預設只綁定 localhost；設定寫入不提交的 `config.local.json`，不需修改原始碼。

CI 使用最小 Python 依賴驗證合約與公開展示，另執行 Ruff、Prettier、公開檔案／常見憑證模式掃描及實際 DOM 煙霧測試。輕量掃描不能取代完整憑證稽核。前端測試需 Node.js 24 與 pnpm 11.25.0，完整指令見 CONTRIBUTING.md。

## English abstract

This prototype connects fixed 17-class intrusion detection, task-oriented train-only retrieval, local AI evidence review, and reversible policy validation in an isolated network. Event and execution identifiers bind detection, evidence, review, and network receipts. A standalone synthetic demo supports public collaboration without redistributing private datasets or model weights; synthetic fixtures are explicitly labelled and are not experimental results.

## GitHub Pages 線上展示

GitHub Pages 版不需安裝或啟動 Python：可篩選17類合成事件、逐步查看分類／證據／稽核／策略、在瀏覽器重算Top-5排序並核對保存案例，以及匯出原始合成事件紀錄。模型、AI生成與網路處置按鈕停用，保留完整本機版功能邊界。線上匯出沿用建置時的原始Python JSON字串，避免JavaScript重新序列化破壞雜湊格式。

`.github/workflows/pages.yml` 只打包新產生的合成資料與公開web檔案，不會上傳私有evidence或本機設定。候選分支與main可部署；PR合併前線上版對應候選分支。部署後的實際版本以Actions紀錄為準。

```bash
python scripts/build_pages.py --output build/pages
pnpm run test:pages
```

建置拒絕覆寫非空目錄。影片以約1.8MB的720p快版提供點擊播放，減少等待與流量。
