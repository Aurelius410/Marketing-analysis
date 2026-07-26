# 行銷數據分析 — 工作目錄速查

這個資料夾是 **行銷與商品數據分析** 的完整工具包，給包子（andychen050229@gmail.com）用。

## 開工前必讀

1. **`SKILL.md`** — 完整流程總覽（八階段、四個硬卡點、觸發條件、檔案地圖）
2. **`references/04_資料品質與踩雷庫.md`** — 進場檢核與失敗案例（必讀，資料錯了後面全錯）
3. **`references/07_分析陷阱清單.md`** — E1–E22 實證防呆規則（必讀，每條都有樣本實證）
4. **`references/02_資料模型規格.md`** — 六域模型完整 DDL，所有分析的地基
5. **`references/05_指標公式庫.md`** — RFM/CAI/CRI/CLV 公式與已驗證的基準值
6. **`references/01_商業框架與提問.md`** — 七問倒推鏈與 Check List 矩陣

## 工作根目錄

```
E:\Projects\行銷分析\projects\<專案代號>\
```

底下是 `00_intake / 01_raw / 02_staging / 03_mart / 04_features / 05_models / 06_figures / 07_report / _log`。詳細規範在 `references/03_倉儲與檔案結構.md`。

教材原始 digest 在 `E:\Projects\行銷分析\00_source_archive\`，要查方法論出處時回去看。

## 環境（有陷阱）

主環境 Python 3.14.1 跑統計＋倉儲＋交付。**因果推論與 Meridian MMM 必須切 `.venv-causal`（Python 3.12）**——在 3.14 裝 dowhy 會靜默降版到 2022 年的 0.8 版且不警告。

## 觸發本 skill 的關鍵字

分析資料、交易數據、會員資料、廣告成效、RFM、ARFM、CAI、CRI、CLV、顧客分群、購物籃、流失預測、歸因、ROAS、MMM、儀表板、分析報告。上傳 .csv/.xlsx/.parquet/.duckdb 也算。

## 核心原則（一句話）

決策驅動欄位，不是資料驅動分析。假設不成立就降級並說明，不要留空。每個數字都要能追回它的計算過程。
