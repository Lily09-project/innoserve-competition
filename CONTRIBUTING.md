# 協作與成果維護

從main建立分支，透過PR提出修改，通過CI後再合併；核心事件合約、模型來源及策略邏輯由專案擁有者審查。不得把自行提出的PR核准當作獨立審查。

## 發布資料

公開儲存庫只收錄 `results/` 四份實測彙整、正式方法影片、簡報及架構圖。私有事件、模型回覆、案例向量庫、設定、原始流量與權重不提交。

更新實驗數據時先保留原始執行紀錄與評估範圍，再更新results來源；各交付物引用相同來源。動畫與簡報必須同步核對，歷史11類與現行17類結果不得混用。方法視覺化不使用虛構單筆機率或AI回覆。

## 驗證

```bash
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
pnpm install --frozen-lockfile
pnpm run test:media
pnpm run check:media
python scripts/check_public_files.py
```

本專案原創部分採Apache-2.0；第三方子模組、模型及資料維持原授權。正式發布從通過CI的提交建立tag，Release需記錄來源版本、實測範圍及交付檔案。
