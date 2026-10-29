# AI 資安框架｜資服競賽

融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架

**[下載決賽簡報](deliverables/決賽簡報_AI資安框架.pptx)** · **[觀看／下載30秒方法動畫](deliverables/AI資安框架_系統展示影片_30秒快版.mp4)**

**[A2海報印刷PDF](deliverables/決賽海報_AI資安框架_A2.pdf)** · **[海報可編輯PPTX](deliverables/決賽海報_AI資安框架_A2.pptx)**

[下載離線簡報、影片與海報備援包](deliverables/決賽離線展示包.zip)

![決賽投影片預覽](deliverables/figures/slides-preview.png)

[![播放30秒方法動畫](deliverables/figures/film-preview.png)](deliverables/AI資安框架_系統展示影片_30秒快版.mp4)

簡報採白底、淺灰章節及深藍、中藍與金黃重點，9頁正式報告說明方法與成果，結束頁後另附3頁、6題答詢備用；每頁附繁體中文講者備忘稿。中文使用標楷體，英文與數字使用Times New Roman。所有換頁特效及裝飾動畫已關閉，僅第二頁保留影片播放時序，第2頁內嵌16:9影片，自動播放一次。影片同時提供內嵌與獨立MP4交付，採網路拓樸與封包動畫說明方法，不需連線或網站即可播放。正式動畫為30秒、2倍速，計入五分鐘正式報告，另保留一分鐘緩衝，符合六分鐘上限。

海報與影片的近期參考、查核範圍及採用方式見[設計轉譯記錄](docs/海報與影片參考轉譯.md)。

## 架構與三項創新

![四階段系統架構](deliverables/figures/fig_architecture.png)

1. **互補偵測**：CTBM讀取封包內容、時間差與方向，PBCNN補充短窗位元組模式，校準後由OOF Gate融合為固定17類判定。
2. **任務證據**：512維流量表徵與17維機率組成529維任務向量，檢索訓練案例庫的Top-5，由本機AI回傳支持、複核或不確定。
3. **受控處置**：策略閘門檢查範圍、動作白名單與期限，完成規則套用、讀回及到期撤銷。同一事件識別碼串接各階段產物。

## 實測結果

| 範圍 | 結果 |
| --- | --- |
| 18,998筆封存偵測測試 | Accuracy 98.08%；Macro-F1 93.05% |
| 1,550筆訓練案例、463筆查詢 | Top-5 97.62%；MRR@5 93.89% |
| 相同463筆事件的本機AI稽核 | 415支持、13複核、35不確定；支持精確率97.11% |
| 17類真實前處理張量重跑 | 正式分類、案例、AI稽核與同事件回條銜接 |
| 6種隔離情境：4規則、2監測或蒐證 | 背景服務6/6保留；回復完整性6/6通過 |

30筆偵測誤判中18筆分流至複核或不確定，12筆獲支持。AI稽核保留正式分類，處置另受策略閘門控制。隔離驗證量測TCP測試交易與規則回復，並非原始攻擊封包防禦率。簡報與影片使用 [`results/`](results/) 的四份實測彙整。

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
python app/server.py
```

本機服務提供模型與事件 API，網址為 `http://127.0.0.1:8765/api/status`；不提供網頁介面。Windows 可執行「啟動作品.cmd」。

已有本機交付包時，可直接匯入私有展示資料（不下載或上傳資料，也不含模型授權）：

```bash
python scripts/import_local_assets.py --source PATH_TO_LOCAL_DELIVERY
```

匯入檔案位於 Git 忽略的 `evidence/`，只在本機使用。

## 展示交付

- [決賽內容與數據基準](docs/決賽內容基準.md)
- [本機匿名展示操作單](docs/本機展示操作單.md)
- [展前驗收與備援](docs/展前驗收與備援.md)
- [完整交付驗收](docs/完整交付驗收.md)
- [A2海報規格與重製](deliverables/source/poster-a2-spec.md)
- [方法與現場答詢](docs/決賽展示與答詢.md)
- [簡報及影片視覺規格](design-system/DESIGN.md)
- [架構圖可編輯SVG](deliverables/source/architecture.svg)
- [圖示與生成紀錄](deliverables/source/README.md)
- [講者備忘稿](deliverables/source/speaker-notes.md)
- [架構圖設計與驗收](docs/架構圖設計與驗收.md)
- [文件同步紀錄](docs/版本與檢查紀錄.md)

## 驗證與協作

- [全項測試矩陣](docs/測試矩陣.md)
- [驗收與重現方式](docs/驗收與重現方式.md)
- [實測與證據索引](docs/實測與證據索引.md)


```bash
git submodule update --init --recursive
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
pnpm install --frozen-lockfile
pnpm run test:media
pnpm run check:media
node tests/media-render-smoke.cjs
python scripts/check_delivery_docs.py
```

`app/`保留模型服務、策略閘門與本機API；`media/film/`為純程式動畫；`scripts/`為重建、驗證與製作工具；`deliverables/`為正式簡報、影片與圖檔。

透過PR審查後合併。模型、封包、逐筆事件、案例庫與本機設定不納入公開儲存庫。原創程式採[Apache-2.0](LICENSE)，第三方模型與子模組維持原授權，見[NOTICE.md](NOTICE.md)。
