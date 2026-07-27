# 行銷數據分析 — 工作目錄速查

這個資料夾是 **行銷與商品數據分析** 的完整工具包，給包子（andychen050229@gmail.com）用。

## 開工前必讀

1. **`SKILL.md`** — 完整流程總覽（十三個模組、四個硬卡點、觸發條件、檔案地圖）
2. **`references/00_通則與紀律.md`** — 橫切紀律：留成果、雙路徑驗算、證據等級、降級（必讀，其他 20 份 reference 都假設你讀過它）
3. **`references/18_分析陷阱清單.md`** — E/G/T 三系列實證防呆規則（必讀，每條都有樣本實證）
4. **`references/02_資料模型規格.md`** — 六域模型完整 DDL，所有分析的地基
5. **`references/04_資料體檢.md`** — M1 進場檢核與失敗案例（資料錯了後面全錯）
6. **`references/17_指標公式庫.md`** — RFM/CAI/CRI/CLV 公式與已驗證的基準值
7. **`references/01_商業框架與提問.md`** — 開案五問與 Check List 矩陣

## 工作根目錄

**路徑不寫死。** 用 `scripts/paths.py` 解析：

```python
from paths import project_dir
p = project_dir("2026Q3_電商")     # 不存在會自動建好標準目錄
p.raw, p.staging, p.mart, p.features, p.figures, p.memory
```

預設落在 `<skill 所在 repo>/projects/<專案代號>/`，要改就複製 `config.example.yml` 成 `config.yml` 再改。

專案底下是：`專案記憶 / 開案與問題定義 / 原始資料 / 清理後資料 / 分析資料表 / 顧客特徵表 / 模型輸出 / 統計表 / 圖表 / 交付物 / 隔離區 / SQL / 執行紀錄`。詳細規範見 `references/03_倉儲與檔案結構.md`。

教材 digest 由 `paths.archive_root()` 自動尋找，找不到不影響運作，只是查不到方法論出處。

## 可攜性

整個 `行銷數據分析/` 資料夾複製到任何機器就能用。**新機器第一件事**：

```bash
python scripts/setup_check.py
```

退出碼 0 = 全通過、1 = 有 error 不能開工、2 = 可開工但部分模組不可用。它會告訴你缺什麼套件、缺哪幾份 reference、字型在不在。

## 環境（有陷阱）

主環境跑統計＋倉儲＋交付（`requirements.txt`）。**因果推論與 Meridian MMM 必須切 Python 3.12 次環境**（`requirements-causal.txt`）——在 3.14 裝 dowhy 會**靜默降版到 2022 年的 0.8 版且不警告**。兩個環境用 Parquet 交換資料。

## 觸發本 skill 的關鍵字

分析資料、交易數據、會員資料、廣告成效、RFM、ARFM、CAI、CRI、CLV、顧客分群、購物籃、流失預測、歸因、ROAS、MMM、儀表板、分析報告。上傳 .csv/.xlsx/.parquet/.duckdb 也算。

## 核心原則（一句話）

決策驅動欄位，不是資料驅動分析。假設不成立就降級並說明，不要留空。每個數字都要能追回它的計算過程。
