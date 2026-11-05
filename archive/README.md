# 舊版本封存

這裡放已被新版取代、現行交付不再使用的文件、工具與素材，保留作為製作歷程的參考。正式成果以[首頁](../README.md)與最新[版本封存](https://github.com/Lily09-project/innoserve-competition/releases/latest)為準；此資料夾內容不再更新，數字與流程可能與現行版本不同。

| 路徑 | 原位置 | 被什麼取代 |
| --- | --- | --- |
| [docs/決賽五分鐘口語稿.md](docs/決賽五分鐘口語稿.md) | docs/ | 講稿改放在PPT講者備忘稿；報告時間改為含影片5分30秒 |
| [docs/完整交付驗收.md](docs/完整交付驗收.md) | docs/ | [展前驗收與備援](../docs/展前驗收與備援.md)、[測試矩陣](../docs/測試矩陣.md) |
| [docs/程式審查修正.md](docs/程式審查修正.md)、[docs/完整程式審查追補修正.md](docs/完整程式審查追補修正.md) | docs/ | 修正已併入程式與[版本與檢查紀錄](../docs/版本與檢查紀錄.md) |
| [docs/公開發布盤點.md](docs/公開發布盤點.md) | docs/ | [公開檔案檢查](../scripts/check_public_files.py)與首頁「公開內容與版本維護」 |
| [docs/海報與影片參考轉譯.md](docs/海報與影片參考轉譯.md) | docs/ | 海報改為團隊完成的單一PNG，影片改為互動展示實錄 |
| [docs/架構圖設計與驗收.md](docs/架構圖設計與驗收.md) | docs/ | 架構圖由[editorial_assets.py](../scripts/presentation/editorial_assets.py)產生 |
| [docs/互動展示UX檢查.md](docs/互動展示UX檢查.md) | docs/ | 互動展示的檢查由[offline-exhibit.cjs](../tests/offline-exhibit.cjs)自動執行 |
| [scripts/embed_opening_film.ps1](scripts/embed_opening_film.ps1) | scripts/presentation/ | [embed_movie_package.py](../scripts/presentation/embed_movie_package.py) |
| [scripts/verify_native_delivery.ps1](scripts/verify_native_delivery.ps1) | scripts/presentation/ | 原生播放測試已排除，改用[export_static_delivery.ps1](../scripts/presentation/export_static_delivery.ps1)靜態輸出 |
| [scripts/audit_alignment.py](scripts/audit_alignment.py)、[scripts/audit_film_alignment.mjs](scripts/audit_film_alignment.mjs) | scripts/presentation/ | [measure_alignment.ps1](../scripts/presentation/measure_alignment.ps1) |
| [assets/security-icons-sheet.png](assets/security-icons-sheet.png) | deliverables/source/ | [design-system/icons.json](../design-system/icons.json) |

封存的工具不保證能在現行專案直接執行，路徑與參數維持移出前的樣子。

仍留在原位置的舊版檔案：A2海報的PPTX、PDF與預覽圖，以及舊版產品動畫來源（media/film、scripts/render_product_film.mjs）。它們被已驗證的版本綁定紀錄（release_inventory與release-validation.json）列為必要檔案，移動會讓實測證據失效，因此只在首頁標明為舊版、不作為交付使用。

更早的完整版本可在[GitHub版本列表](https://github.com/Lily09-project/innoserve-competition/releases)下載；v1.11-finals以前為舊版。
