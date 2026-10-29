# 決賽補充實驗協定

先固定協定，再執行；不依測試結果調整門檻或刪除不利結果。

- 對照：同一463筆保存偵測輸入、同一1550筆訓練庫及同一本機LLM。比較信心／分支規則、529維證據規則，以及無檢索、512維檢索、529維檢索的三組AI輸入。三組AI使用相同、支援選擇性證據的實驗提示詞，全部重新呼叫，不沿用既有稽核回覆。此提示詞與歷史正式提示詞分開記錄。
- 共同策略比較：各組稽核結果接入相同的正式529維證據與策略閘門，避免把「無證據所以禁止處置」誤當AI改善。這是稽核輸入對照，不是把整條系統的檢索全部移除。
- 指標：支持精確率、支持涵蓋率、錯誤支持數、正確事件未獲支持比例，以及共同閘門下的錯誤策略授權。分類結果不改寫，實驗不部署規則。
- 服務PoC：Mininet內的真實SSH協定與密碼驗證服務，不建立主機帳號。惡意嘗試與正常登入使用同一服務及連接埠，觀察來源限制、同來源正常登入副作用、其他來源正常登入與到期回復。偵測／策略證據來自CIC事件，不能描述為直接偵測本次生成的SSH封包。
- 效能：冷啟動與固定輸入的連續端到端操作分開量測；不把批次生成耗時除以批次大小當成單筆延遲。
- 抽樣：在既有train-only案例庫內，以預定種子抽取分層子集，固定查詢與權重，比較檢索指標。這是案例庫敏感性，不是跨資料集或新查詢泛化證明。

逐筆輸入、回覆、服務帳密及回條保留validation或runtime等Git忽略目錄；公開部分只包含協定、彙整與雜湊。

## 執行入口

公開驗收不需GPU或私有資料：

```bash
python experiments/export_results.py
python -m unittest discover -s tests -p test_supplementary_experiments.py -v
```

完整重跑需依主README設定合法取得的私有模型、案例庫及CUDA環境。使用一個全新的輸出根目錄；下例以`validation/REPRO`表示，不能覆寫既有證據：

```bash
python experiments/ablation.py --output validation/REPRO/supplementary-ablation-20261029
python experiments/retrieval_sensitivity.py --output validation/REPRO/retrieval-sensitivity-20261029.json
python experiments/latency.py --output validation/REPRO/latency-processes-20261029
```

稽核實驗只有在程式、資料與協定均未變動時，才能加`--resume`接續；其他實驗拒絕覆寫已存在結果。先完成稽核再執行效能量測，避免兩個模型程序同時占用GPU。效能腳本建立三個獨立程序，各載入一次模型、執行一次首次推論及102次循環呼叫；量測整合函式，排除HTTP排程與網路套用，不測併發容量。

SSH測試須在已配置Mininet與`python3-paramiko`的WSL／Linux環境中，以root執行`experiments/service_poc.py --scenario <private-scenario.json> --output <new-private-output>`。情境檔由`app/network_contract.py`的`build_network_scenario()`對成功真實SSH事件產生；測試再核對完整事件鏈與雜湊，不能自行寫入允許結論。輸出資料夾名稱須為`ssh-service-final-20261029`並位於同一REPRO根目錄，供彙整器讀取。服務與客戶端只使用自建命名空間；不得把目標改成外部服務。程序有240秒期限，持有獨占網路鎖，並清除自身規則與拓樸，不執行全域網路清理。

各項完成後執行`python experiments/export_results.py --build-from validation/REPRO`匯出公開彙整，再執行`python scripts/check_delivery_docs.py`及完整測試。匯出會更新公開JSON與來源索引，不更動既有權重或正式媒體。GitHub CI只重驗公開合約與來源綁定，不會重跑上述私有模型或SSH實驗。

本輪實際結果與適用範圍見[補充實驗報告](../docs/補充實驗與適用範圍.md)。規則與AI對照保留所有不利結果；本輪不依答案重調提示詞或門檻。
