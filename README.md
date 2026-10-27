# 資服競賽

AI資安框架展示專案，整合固定17類入侵偵測、任務導向Top-5案例檢索、本機AI稽核與可回復的隔離策略驗證。

正式作品名稱：融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架。

完整交接、17類策略路徑與展示範圍見[框架說明](FRAMEWORK.md)。

## 功能

- 深色事件介面，可逐步查看正式分類、相似案例、AI理由與策略。
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
python -m pip install -r requirements.txt
```

依執行設備選擇適合的PyTorch安裝來源。本機模型展示已於RTX 4090驗證。

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
web/                    展示介面
scripts/                資料重建、稽核與隔離驗證
tests/                  合約與異常處理測試
results/                可公開彙整結果
sources/paper_code/     研究B固定版本submodule
config.example.json     本機資產設定範例
```

來源與使用範圍見[NOTICE.md](NOTICE.md)。
