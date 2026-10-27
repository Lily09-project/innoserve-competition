# 協作規範

使用獨立分支與小型 Pull Request；先說明實際問題、修改後行為與驗證方式。不要直接推送 main。

## 本機檢查

```bash
python -m pip install -r requirements-test.txt
pnpm install --frozen-lockfile
python -m ruff check app scripts tests
python -m ruff format --check app scripts tests
pnpm run format:check
python -m unittest discover -s tests -v
pnpm run test:frontend
python scripts/check_public_files.py
```

開發前執行 `git submodule update --init --recursive`。Python 3.11+、Node.js 24、pnpm 11.25.0。PR 中不得變動上游子模組內容；更新固定版本需另行說明授權、相容性與測試。

核心事件合約、策略閘門、模型版本設定及 CI 修改由 @Lily09-project 審查。作者不能將自己的 PR 核准視為獨立審查。合併前所有必要 CI 檢查需通過。

## 資料與授權

新協作者使用 `python app/server.py --demo`。合成資料不能用於成果數據或宣稱模型推論成功。私有模型、原始資料、逐筆回覆、API key、工作站路徑及 `config.local.json` 不得提交。

本專案原創程式採 Apache-2.0；第三方程式、資料及模型維持原授權，請查閱 NOTICE.md。新增素材須保留來源及授權證明。

## 發版

從通過 CI 且經審查的 main 建立版本標籤，再發布 Release，附上測試結果、資產需求及已知限制。競賽送件版本需另外完成匿名檢查。展示影片與投影片不得包含帳號或可識別參賽單位的資訊。
