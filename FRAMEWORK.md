# 框架交接與展示範圍

本作品將入侵判斷、案例證據、AI稽核、受控處置及恢復驗證接成同一事件流程。可操作的成果是本機展示系統與隔離網路概念驗證。

## 資料如何交接

1. CTBM與PBCNN讀取已準備的真實前處理輸入，經凍結Gate輸出17類機率與正式類別。
2. CTBM的512維表徵與17維機率串接為529維向量，正規化後查詢僅含訓練資料的Top-5案例。
3. 本機Llama接收分類、信心、分支結果及Top-5標籤與相似度，產生支持、複核或不確定的JSON回覆。測試答案不進入模型提示。
4. 確定性策略閘門根據正式類別、AI稽核及證據門檻選擇白名單動作。AI不直接產生或執行Shell命令，也不覆寫正式分類。
5. 同次即時推論的策略送入Mininet，在自行建立的虛擬網路套用iptables規則、讀回規則、檢查測試交易及背景服務，並在30秒到期後撤銷規則、驗證恢復。
6. 執行回條綁定事件ID、執行ID、來源結果摘要與情境摘要，接續偵測至策略的雜湊鏈。摘要用來檢查替換或毀損，不等同數位簽章。

模型預載時核對checkpoint與案例庫摘要。API匯出直接保留後端JSON的數值格式。即時匯出與網路執行要求同一事件的執行ID；再次推論後，舊執行ID無法用於部署。

## 17類與處置路徑

| 偵測類別 | 支持且通過門檻時的策略 | 隔離設備實作 |
|---|---|---|
| BENIGN | 監測 | 不套用阻擋規則 |
| FTP、SSH暴力破解 | 服務驗證防護 | 限制來源對目標服務的新連線 |
| DoS-GoldenEye、DoS-Hulk、Web-BruteForce | 來源限速 | iptables新連線限速 |
| DDoS-LOIC-HTTP、DDOS-HOIC | 上游緩解策略 | 隔離路由器對目標服務限速 |
| Web-XSS、SQL-Injection | Web防護策略 | 限制疑似來源對HTTP服務的連線 |
| Bot | 對外連線限制 | 阻擋測試端點指定連接埠 |
| DoS-Slowloris、DoS-SlowHTTPTest、DDoS-LOIC-UDP、Infiltration、PortScan、Heartbleed | 蒐證與人工處理 | 保留事件證據，不部署破壞性規則 |

「支持」還需正式分類信心至少0.8，且Top-5至少4筆支持該類，才能通過可干預處置門檻。複核與不確定事件保留蒐證。

## 如何解讀後段的修復

此處的修復指受控緩解與服務恢復驗證：限速、限制連線、撤銷規則及確認連線恢復。隔離版的Web防護是來源連線限制，不是修補應用程式漏洞；上游緩解採限速驗證，不是商用清洗中心。評估流量是合成TCP交易，不是原始攻擊封包或真實漏洞利用。

## 與來源方法的關係

前段沿用已驗證的17類模型。後段沿用案例檢索、不可變分類、AI稽核、策略檢核及隔離處置的設計，並使用來源庫的動作驗證及網路元件。

本整合版使用529維任務向量。歷史Fine-11的522維改良FE-Net與1,830筆比較為獨立模組證據，不能視為目前17類整合流程的重現結果。本次整合效能以`results/`的17類重跑結果及本機逐筆驗證為準。

## 操作與重現

1. 依[README](README.md)設定本機資產，執行「啟動作品.cmd」啟動API服務。
2. 以 `GET /api/status` 取得模型狀態與可重跑事件ID；`POST /api/operate` 的 `action=warmup` 預載模型。
3. 以 `action=live`、`event_id` 執行同事件完整推論，透過 `GET /api/jobs/{job_id}` 等待工作完成。回應包含正式類別、Top-5、本機AI稽核、策略與 `execution_id`。
4. 在隔離測試床中，以 `action=network`、同一 `event_id` 與 `execution_id` 檢查規則、交易、背景服務與到期回復。服務拒絕不符或過期的執行ID。
5. 以 `POST /api/export`、`mode=live_local_models`、同一事件與執行ID匯出結果；保存事件重播使用 `mode=saved_prediction_replay`，不取得即時部署資格。

網站介面已移除，以上均為本機API。完整17類與6種隔離情境驗證在展前執行；現場使用9頁簡報及30秒、2倍速影片，正式報告5分鐘，另留1分鐘緩衝。

```bash
python scripts/preflight.py --warmup
python scripts/audit_alignment_assets.py
python scripts/audit_final_chain.py
```

`audit_alignment_assets.py`核對模型與表徵來源；`audit_final_chain.py`重跑17類及6種隔離情境，並掃描正式簡報、架構圖與影片來源的匿名文字。`verify_delivery.py`另提供保存事件與可選隔離路徑的檢查，其回復測試模式與自動到期量測分開記錄。

上述驗證保存於Git忽略的`validation/`與`evidence/`。模型推論、AI回覆及網路隔離測試各自保留執行模式，不把重播標示為即時執行。
