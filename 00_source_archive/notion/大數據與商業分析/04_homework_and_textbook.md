---
source: Notion
workspace_path: "NTU / 碩二課程 / 大數據與商業分析"
pages:
  - title: "HW 1"
    url: "https://app.notion.com/p/3192b4ffdf0b80cb9a8bd72460ed9b58"
    last_edited_snapshot: "2026-03-08T08:56:07Z"
    status: "有完整內容（本檔主體）"
  - title: "HW2（施工中）"
    url: "https://app.notion.com/p/33a2b4ffdf0b8007b0d3d8f1fa803074"
    last_edited_snapshot: "2026-04-06T14:57:09Z"
    status: "空白頁，尚無任何內容"
  - title: "原文書"
    url: "https://app.notion.com/p/3192b4ffdf0b805c8ed4daaebfb98ade"
    last_edited_snapshot: "2026-03-04T12:20:22Z"
    status: "僅有一個 PDF 附件，無正文"
parent_page:
  title: "大數據與商業分析"
  url: "https://app.notion.com/p/3192b4ffdf0b80a6acb2ca7f06467c69"
  siblings:
    - "原文書"
    - "Lecture 1 : Text mining"
    - "Lecture 2：Web mining"
    - "Lecture 3：Classification"
    - "Lecture 4：Clustering"
    - "Lecture 5：Sequence Tagging（施工中）"
    - "HW 1"
    - "HW2（施工中）"
capture_scope: >
  三頁全文抓取（含 toggle / details 內展開內容）。HW1 的 Python 程式碼一字不漏抄錄；
  所有數學公式由 Notion inline LaTeX 轉為標準 LaTeX。HW1 頁面內未附任何實際輸出數值
  （Top20 詞表、診斷表數字、最終 20 keyword 名單皆未貼在 Notion 上），因此本檔只有
  方法與程式，沒有結果數據。HW2 為空白、原文書僅附件，兩者已如實記錄狀態。
language_of_source: 繁體中文（程式碼與欄名混用中英）
captured_at: "2026-07-25"
---

# 大數據與商業分析：HW1 實作 + HW2 + 原文書（Notion 全文 digest）

> **本檔性質**：這是「實際動手做的專案」digest，重點在完整程式碼、資料流、指標公式、
> 作者的決策順序與踩坑紀錄。凡標示「**評註**」的段落是抓取者（Claude）的判斷或推導，
> **不是** Notion 原文內容；其餘皆為原文忠實抄錄或原文的結構化重排。

---

## 0. 三頁狀態總覽

| 頁面 | 內容 | 可用性 |
|---|---|---|
| **HW 1** | 一份可「一鍵執行並呈現所有結果」的 Python 腳本（約 480 行）＋ 6 個指標的公式與直覺說明 ＋ 4 步運行邏輯 ＋ 權重設計理由 ＋ 6 個輸出檔說明 | 完整，是本檔主體 |
| **HW2（施工中）** | `This page is blank and has no content.` | 無內容。標題已標「施工中」，代表作業二尚未開始或筆記未搬上 Notion |
| **原文書** | 單一 PDF 附件，無任何正文、無畫線、無筆記 | 只能取得書目資訊 |

### 頁面首行的自我提醒（HW1 原文第一行）

```
- 記得要填補上所有的資料！
```

**評註**：這行提醒與程式碼裡「避免 Excel 公式沒填滿 / 避免只依賴 Excel 快取值」的動機互相呼應
——作者是先在 Excel workbook 手算，發現公式沒拉滿、或快取值不可信，才決定整套改用 Python 重算。
這是整個 HW1 腳本存在的原因。

---

## 1. 原文書（書目）

- **書名**：An Introduction to Information Retrieval
- **作者**：Christopher D. Manning, Prabhakar Raghavan, Hinrich Schütze
- **版次／年份**：1st, 2008
- **出版社**：Cambridge University Press
- **ISBN（附件檔名中）**：9780511410802
- **檔名（Notion 附件原始檔名，含來源標記）**：
  `An_introduction_to_information_retrieval_--_Christopher_D__Manning_Prabhakar_Raghavan_Hinrich_Schtze_--_1_2008_--_Cambridge_University_Press_--_9780511410802_--_776b1e479b67f46d692cbd9ab6920478_--_Annas_Archive.pdf`
- **Notion 頁面內容**：除附件外只有一個空白 block。沒有摘要、沒有章節筆記、沒有標註。

**評註**：HW1 使用的 log-frequency tf weighting `1 + log10(tf)` 與 `idf = log10(N/df)` 正是這本書
（IIR）第 6 章的標準寫法，這是課程指定教材與作業公式的直接對應關係。但 Notion 上**沒有**
任何章節對照筆記，這層對應是我從公式形式推得的，不是原文所述。

---

## 2. HW1 專案概述（原文「程式執行摘要及輸出說明」）

原文對這支程式的一句話定位：

> 先把四張主表的分數全部重算乾淨，再根據多種方法自動排序、建立候選池，
> 最後用一套規則，替每張表自動選出最終 20 個 keyword。

它同時完成三件事（原文列點）：

1. **重算各種指標**
2. **產生各方法的 Top 20 排序結果**
3. **從多方法結果中，自動選出最終 20 個 keyword**

### 2.1 輸入資料結構：一個 Excel workbook、六張 sheet

| 角色 | Sheet 名稱 | 說明 |
|---|---|---|
| 全體參考表（背景語料庫） | `全部_2gram` | 全部文件的 2-gram 統計 |
| 全體參考表（背景語料庫） | `全部_3gram` | 全部文件的 3-gram 統計 |
| 主表（真正要挑 keyword 的地方） | `產業_2gram` | 目標子語料：產業，2-gram |
| 主表 | `產業_3gram` | 目標子語料：產業，3-gram |
| 主表 | `鴻海_2gram` | 目標子語料：鴻海，2-gram |
| 主表 | `鴻海_3gram` | 目標子語料：鴻海，3-gram |

原文：
> 程式會把 `全部_2gram / 全部_3gram` 當成「背景語料庫」，再把四張主表當成「目標子語料」。

### 2.2 workbook 的兩個非標準版面約定（從程式碼反推，非常重要）

1. **每張 sheet 的 A1 儲存格 = 該表的「文件總數」**（不是欄名）。
   程式用 `pd.read_excel(..., header=None, nrows=1, usecols="A").iloc[0,0]` 專門去撈它。
   這個數就是公式裡的 $N$（全體）或 $N_c$（本地）。
2. **真正的欄名在第 3 列**，所以所有 sheet 都用 `header=2` 讀入。
   欄位為：`編號`、`詞`、`TF`、`DF`、以及一堆 Excel 公式欄。

**評註**：這是典型「作業表格是老師給的模板」造成的資料工程負擔——metadata（文件數）被塞在
資料區塊裡，欄名不在第一列。腳本用兩次不同 header 設定讀同一個檔案來繞過，是務實但脆弱的做法
（見 §8 踩坑清單）。

### 2.3 商業／行銷情境

原文沒有明寫「這是什麼行銷任務」，但從資料設計可讀出：兩個目標類別是
**「產業」（泛產業新聞／文本）** 與 **「鴻海」（單一公司）**，要從新聞或文本語料中
自動抽出各自的代表 keyword。這對應的行銷／商業問題是：

> 給定一批文本（新聞、社群、評論），哪些詞是「這個品牌／這個產業」的特徵詞，
> 而不是所有文本都在講的通用詞？

---

## 3. 完整程式碼（Python，一字不漏抄錄）

原文說明：
> 一鍵執行並呈現所有結果的 Code：路徑及其他個人偏好設定，可以直接在 Config 區自己調整。

**語言與套件**：純 Python，只用 `math`、`pathlib`、`numpy`、`pandas`，
Excel 寫出用 `openpyxl` engine。無 sklearn、無 jieba（切詞是在此腳本之外／Excel 前置作業完成的）、
無視覺化套件。`from __future__ import annotations` 以便用 `dict[str, pd.DataFrame]` 這類新式型別註記。

```python
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import pandas as pd

# =========================================================
# CONFIG
# =========================================================
INPUT_XLSX = Path(r"")
OUTPUT_DIR = Path(r"")

# 基本輸出設定
TOP_N = 20                                  # 各方法 Top N
BACKUP_N = 10                               # 最終 keyword 候補數（第 21~30 名）
EXPORT_CSV = True
EXPORT_MARKDOWN_BRIEF = True
EXPORT_COMPLETED_WORKBOOK = True
EXPORT_SUMMARY_WORKBOOK = True
EXPORT_FINAL_KEYWORD_WORKBOOK = True
EXPORT_DIAGNOSTICS_WORKBOOK = True

# ---------------------------------------------------------
# 自動挑選「每張表最終 20 個 keyword」
# ---------------------------------------------------------
AUTO_SELECT_FINAL_20 = True
FINAL_KEYWORD_N = 20

# Step A：硬性篩選（Hard Filters）
MIN_LOCAL_DF_2GRAM = 2
MIN_LOCAL_DF_3GRAM = 2
RELAX_LOCAL_DF_3GRAM_TO_1_IF_TOO_FEW = True
MIN_GLOBAL_DF = 2

REQUIRE_LIFT_GT_1 = True
REQUIRE_POSITIVE_DF_CHI = True

# Step C：多方法融合權重（建議總和 = 1）
WEIGHT_TFIDF = 0.25
WEIGHT_LIFT = 0.30
WEIGHT_DF_CHI = 0.30
WEIGHT_MI = 0.15

# Step D：Support penalty（穩定性懲罰）
USE_SUPPORT_PENALTY = True
LOCAL_DF_STABLE_LEVEL = 3
GLOBAL_DF_STABLE_LEVEL = 5

# Step E：方法共識加分
USE_METHOD_AGREEMENT_BONUS = True
AGREEMENT_BONUS_STEP = 0.05

# 參與候選池 / 最終分數的主要方法
CANDIDATE_METHODS = [
    "TF-IDF",
    "MI(用DF)",
    "Lift(用DF)",
    "DF卡方值(保留正負號)",
]
# =========================================================


GLOBAL_SHEETS = {
    "2gram": "全部_2gram",
    "3gram": "全部_3gram",
}

TARGET_SHEETS = {
    "產業_2gram": {"gram": "2gram", "class_name": "產業"},
    "產業_3gram": {"gram": "3gram", "class_name": "產業"},
    "鴻海_2gram": {"gram": "2gram", "class_name": "鴻海"},
    "鴻海_3gram": {"gram": "3gram", "class_name": "鴻海"},
}

METHOD_COLUMNS = [
    "TF-IDF",
    "TF卡方值(保留正負號)",
    "DF卡方值(保留正負號)",
    "MI(用DF)",
    "Lift(用DF)",
]


def log10_series(s: pd.Series | float) -> pd.Series | float:
    """模擬 Excel 的 LOG() 預設 base=10；非正值回傳 NaN。"""
    if isinstance(s, pd.Series):
        s = pd.to_numeric(s, errors="coerce")
        return np.where(s > 0, np.log10(s), np.nan)
    return math.log10(s) if s and s > 0 else np.nan


def get_sheet_counts(xlsx_path: Path) -> dict[str, float]:
    """讀取每張 sheet 的 A1（你的作業表設計中，A1 為該表文件總數）。"""
    xls = pd.ExcelFile(xlsx_path)
    counts = {}
    for name in xls.sheet_names:
        a1 = pd.read_excel(xlsx_path, sheet_name=name, header=None, nrows=1, usecols="A").iloc[0, 0]
        counts[name] = float(a1)
    return counts


def load_sheets(xlsx_path: Path) -> dict[str, pd.DataFrame]:
    """以第 3 列作為欄名（header=2）讀入所有 sheets。"""
    xls = pd.ExcelFile(xlsx_path)
    return {name: pd.read_excel(xlsx_path, sheet_name=name, header=2) for name in xls.sheet_names}


def recompute_target_sheet(
    target_df: pd.DataFrame,
    global_df: pd.DataFrame,
    local_n: float,
    global_n: float,
) -> pd.DataFrame:
    """
    依照你的 hw1_table.xlsx 欄位設計，
    在 Python 端重算所有指標，避免 Excel 公式沒填滿或快取有問題。
    """
    target = target_df[["編號", "詞", "TF", "DF"]].copy()
    global_small = global_df[["詞", "TF", "DF"]].copy().rename(columns={"TF": "全部TF", "DF": "全部DF"})
    out = target.merge(global_small, on="詞", how="left")

    # 本地 TF-IDF
    out["TF-IDF"] = (1 + log10_series(out["TF"])) * log10_series(local_n / out["DF"])

    # 全體語料 TF-IDF
    out["全部TF-IDF"] = (1 + log10_series(out["全部TF"])) * log10_series(global_n / out["全部DF"])

    # 期望值
    out["TF期望值"] = out["全部TF"] / global_n * local_n
    out["DF期望值"] = out["全部DF"] / global_n * local_n

    # 卡方（保留正負號）
    out["TF卡方值(保留正負號)"] = (
        ((out["TF"] - out["TF期望值"]) ** 2) / out["TF期望值"]
    ) * np.where(out["TF"] >= out["TF期望值"], 1, -1)

    out["DF卡方值(保留正負號)"] = (
        ((out["DF"] - out["DF期望值"]) ** 2) / out["DF期望值"]
    ) * np.where(out["DF"] >= out["DF期望值"], 1, -1)

    # 完全比照你 workbook 目前的公式邏輯
    out["MI(用DF)"] = log10_series(out["DF"] / (out["全部DF"] * local_n))
    out["Lift(用DF)"] = (out["DF"] / local_n) / (out["全部DF"] / global_n)

    ordered_cols = [
        "編號", "詞", "TF", "DF", "TF-IDF", "全部TF", "全部DF", "全部TF-IDF",
        "TF期望值", "DF期望值", "TF卡方值(保留正負號)", "DF卡方值(保留正負號)",
        "MI(用DF)", "Lift(用DF)"
    ]
    return out[ordered_cols]


def build_top20_tables(completed_sheets: dict[str, pd.DataFrame], top_n: int = 20):
    """針對每張表、每個方法自動排序並擷取 Top N。"""
    top_tables = {}
    overview_rows = []

    for sheet_name, df in completed_sheets.items():
        for method in METHOD_COLUMNS:
            temp = df[["編號", "詞", "TF", "DF", method]].copy()
            temp = temp.dropna(subset=[method]).sort_values(method, ascending=False).head(top_n)
            temp.insert(0, "方法", method)
            top_tables[f"{sheet_name}__{method}"] = temp

            for rank, (_, row) in enumerate(temp.iterrows(), start=1):
                overview_rows.append({
                    "來源表": sheet_name,
                    "方法": method,
                    "排名": rank,
                    "詞": row["詞"],
                    "TF": row["TF"],
                    "DF": row["DF"],
                    "分數": row[method],
                })

    return top_tables, pd.DataFrame(overview_rows)


def build_candidate_pools(completed_sheets: dict[str, pd.DataFrame], top_n: int = 20):
    """
    建立每張表的候選池：
    把 TF-IDF / MI / Lift / DF卡方 的 top N 合併去重。
    """
    pools = {}
    for sheet_name, df in completed_sheets.items():
        pieces = []
        for method in CANDIDATE_METHODS:
            temp = df[["詞", "TF", "DF", "TF-IDF", "MI(用DF)", "Lift(用DF)", "DF卡方值(保留正負號)"]].copy()
            temp = temp.dropna(subset=[method]).sort_values(method, ascending=False).head(top_n)
            temp["來源方法"] = method
            pieces.append(temp)

        merged = pd.concat(pieces, ignore_index=True)
        counts = merged.groupby("詞").size().rename("入選方法數").reset_index()
        merged = merged.merge(counts, on="詞", how="left")
        merged = merged.drop_duplicates(subset=["詞"]).sort_values(
            ["入選方法數", "Lift(用DF)", "MI(用DF)", "TF-IDF"],
            ascending=[False, False, False, False]
        )
        pools[sheet_name] = merged
    return pools


def _rank01(series: pd.Series) -> pd.Series:
    """將分數轉成 0~1 百分位排名；越大越好。"""
    s = pd.to_numeric(series, errors="coerce")
    # pandas rank(pct=True) 最高值趨近 1
    return s.rank(method="average", pct=True)


def _support_penalty(local_df: pd.Series, global_df: pd.Series) -> pd.Series:
    """穩定性懲罰：local/global DF 太低則降權。"""
    if not USE_SUPPORT_PENALTY:
        return pd.Series(1.0, index=local_df.index)
    local_pen = np.minimum(1.0, pd.to_numeric(local_df, errors="coerce") / LOCAL_DF_STABLE_LEVEL)
    global_pen = np.minimum(1.0, pd.to_numeric(global_df, errors="coerce") / GLOBAL_DF_STABLE_LEVEL)
    return local_pen * global_pen


def _agreement_bonus(method_count: pd.Series) -> pd.Series:
    """方法共識加分：同時被多個方法支持的詞，稍微加分。"""
    if not USE_METHOD_AGREEMENT_BONUS:
        return pd.Series(0.0, index=method_count.index)
    count = pd.to_numeric(method_count, errors="coerce").fillna(1)
    return AGREEMENT_BONUS_STEP * np.maximum(0, count - 1)


def select_final_keywords(
    completed_sheets: dict[str, pd.DataFrame],
    candidate_pools: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    """
    最終 keyword 選擇流程：
    Step A. 硬性篩選（support + direction）
    Step B. 多方法排序融合（rank-based fusion）
    Step C. support penalty
    Step D. method agreement bonus
    Step E. 取最終 20 + 候補 10
    """
    final_tables = {}
    backup_tables = {}
    diagnostics_rows = []

    for sheet_name, df in completed_sheets.items():
        temp = df.copy()
        n_before = len(temp)

        # --- Step A：硬性篩選 ---
        gram = "3gram" if "3gram" in sheet_name else "2gram"
        min_local_df = MIN_LOCAL_DF_3GRAM if gram == "3gram" else MIN_LOCAL_DF_2GRAM

        mask_local_df = temp["DF"] >= min_local_df
        after_local_df = int(mask_local_df.sum())

        # 若 3-gram 太少，允許放寬到 DF >= 1
        relaxed = False
        if gram == "3gram" and RELAX_LOCAL_DF_3GRAM_TO_1_IF_TOO_FEW and after_local_df < FINAL_KEYWORD_N:
            min_local_df = 1
            mask_local_df = temp["DF"] >= min_local_df
            after_local_df = int(mask_local_df.sum())
            relaxed = True

        temp = temp[mask_local_df].copy()

        mask_global_df = temp["全部DF"] >= MIN_GLOBAL_DF
        after_global_df = int(mask_global_df.sum())
        temp = temp[mask_global_df].copy()

        if REQUIRE_LIFT_GT_1:
            mask_lift = temp["Lift(用DF)"] > 1
            after_lift = int(mask_lift.sum())
            temp = temp[mask_lift].copy()
        else:
            after_lift = len(temp)

        if REQUIRE_POSITIVE_DF_CHI:
            mask_dfchi = temp["DF卡方值(保留正負號)"] > 0
            after_dfchi = int(mask_dfchi.sum())
            temp = temp[mask_dfchi].copy()
        else:
            after_dfchi = len(temp)

        # 若篩完太少，至少保底用 candidate pool 的詞補進來（但仍保留分數紀錄）
        pool = candidate_pools[sheet_name][["詞", "入選方法數"]].copy()
        temp = temp.merge(pool, on="詞", how="left")
        temp["入選方法數"] = temp["入選方法數"].fillna(0)

        # --- Step B：多方法排序融合（rank 0~1）---
        if len(temp) > 0:
            temp["rank_tfidf"] = _rank01(temp["TF-IDF"])
            temp["rank_lift"] = _rank01(temp["Lift(用DF)"])
            temp["rank_dfchi"] = _rank01(temp["DF卡方值(保留正負號)"])
            temp["rank_mi"] = _rank01(temp["MI(用DF)"])

            temp["CompositeScore"] = (
                WEIGHT_TFIDF * temp["rank_tfidf"] +
                WEIGHT_LIFT * temp["rank_lift"] +
                WEIGHT_DF_CHI * temp["rank_dfchi"] +
                WEIGHT_MI * temp["rank_mi"]
            )

            # --- Step C：support penalty ---
            temp["SupportPenalty"] = _support_penalty(temp["DF"], temp["全部DF"])
            temp["AdjustedScore"] = temp["CompositeScore"] * temp["SupportPenalty"]

            # --- Step D：agreement bonus ---
            temp["AgreementBonus"] = _agreement_bonus(temp["入選方法數"])
            temp["FinalKeywordScore"] = temp["AdjustedScore"] + temp["AgreementBonus"]

            temp = temp.sort_values("FinalKeywordScore", ascending=False).reset_index(drop=True)
            temp["最終排名"] = np.arange(1, len(temp) + 1)
        else:
            # 全空表時，仍保留結構
            temp["rank_tfidf"] = np.nan
            temp["rank_lift"] = np.nan
            temp["rank_dfchi"] = np.nan
            temp["rank_mi"] = np.nan
            temp["CompositeScore"] = np.nan
            temp["SupportPenalty"] = np.nan
            temp["AgreementBonus"] = np.nan
            temp["FinalKeywordScore"] = np.nan
            temp["最終排名"] = np.nan

        diagnostics_rows.append({
            "來源表": sheet_name,
            "原始列數": n_before,
            "local_df_threshold": min_local_df,
            "3gram_df條件放寬": "Y" if relaxed else "N",
            "local_df篩後列數": after_local_df,
            "global_df篩後列數": after_global_df,
            "Lift>1篩後列數": after_lift,
            "DF卡方>0篩後列數": after_dfchi,
            "最終可排序候選數": len(temp),
            "最終輸出筆數": min(FINAL_KEYWORD_N, len(temp)),
            "候補輸出筆數": min(BACKUP_N, max(0, len(temp) - FINAL_KEYWORD_N)),
        })

        final_tables[sheet_name] = temp.head(FINAL_KEYWORD_N).copy()
        backup_tables[sheet_name] = temp.iloc[FINAL_KEYWORD_N:FINAL_KEYWORD_N + BACKUP_N].copy()

    diagnostics_df = pd.DataFrame(diagnostics_rows)
    return final_tables, backup_tables, diagnostics_df


def write_outputs(
    output_dir: Path,
    completed_sheets: dict[str, pd.DataFrame],
    top_tables: dict[str, pd.DataFrame],
    overview_df: pd.DataFrame,
    candidate_pools: dict[str, pd.DataFrame],
    final_tables: dict[str, pd.DataFrame] | None = None,
    backup_tables: dict[str, pd.DataFrame] | None = None,
    diagnostics_df: pd.DataFrame | None = None,
):
    """輸出你寫 Word 前最需要看的所有整理結果。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir = output_dir / "csv_exports"
    if EXPORT_CSV:
        csv_dir.mkdir(exist_ok=True)

    completed_wb = output_dir / "hw1_table_completed.xlsx"
    summary_wb = output_dir / "hw1_top20_summary.xlsx"
    final_wb = output_dir / "final_keywords_auto.xlsx"
    backup_wb = output_dir / "final_keywords_backup.xlsx"
    diagnostics_wb = output_dir / "selection_diagnostics.xlsx"
    brief_md = output_dir / "hw1_before_word_brief.md"

    # 1) 重算後四張主表
    if EXPORT_COMPLETED_WORKBOOK:
        with pd.ExcelWriter(completed_wb, engine="openpyxl") as writer:
            for sheet_name, df in completed_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    # 2) Top20 + 候選池摘要
    if EXPORT_SUMMARY_WORKBOOK:
        with pd.ExcelWriter(summary_wb, engine="openpyxl") as writer:
            overview_df.to_excel(writer, sheet_name="00_overview_top20", index=False)
            for sheet_name, df in completed_sheets.items():
                df.to_excel(writer, sheet_name=f"raw_{sheet_name}"[:31], index=False)
            for key, df in top_tables.items():
                safe_name = key.replace("(", "").replace(")", "").replace("/", "_")[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)
            for sheet_name, df in candidate_pools.items():
                df.to_excel(writer, sheet_name=f"候選池_{sheet_name}"[:31], index=False)

    # 3) 最終 20 keyword
    if EXPORT_FINAL_KEYWORD_WORKBOOK and final_tables is not None:
        with pd.ExcelWriter(final_wb, engine="openpyxl") as writer:
            for sheet_name, df in final_tables.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    # 4) 候補 10 keyword
    if EXPORT_FINAL_KEYWORD_WORKBOOK and backup_tables is not None:
        with pd.ExcelWriter(backup_wb, engine="openpyxl") as writer:
            for sheet_name, df in backup_tables.items():
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    # 5) 診斷表
    if EXPORT_DIAGNOSTICS_WORKBOOK and diagnostics_df is not None:
        with pd.ExcelWriter(diagnostics_wb, engine="openpyxl") as writer:
            diagnostics_df.to_excel(writer, sheet_name="diagnostics", index=False)

    # 6) CSV
    if EXPORT_CSV:
        overview_df.to_csv(csv_dir / "00_overview_top20.csv", index=False, encoding="utf-8-sig")
        for sheet_name, df in completed_sheets.items():
            df.to_csv(csv_dir / f"raw_{sheet_name}.csv", index=False, encoding="utf-8-sig")
        for key, df in top_tables.items():
            safe_name = key.replace("(", "").replace(")", "").replace("/", "_")
            df.to_csv(csv_dir / f"{safe_name}.csv", index=False, encoding="utf-8-sig")
        for sheet_name, df in candidate_pools.items():
            df.to_csv(csv_dir / f"候選池_{sheet_name}.csv", index=False, encoding="utf-8-sig")
        if final_tables is not None:
            for sheet_name, df in final_tables.items():
                df.to_csv(csv_dir / f"最終20_{sheet_name}.csv", index=False, encoding="utf-8-sig")
        if backup_tables is not None:
            for sheet_name, df in backup_tables.items():
                df.to_csv(csv_dir / f"候補10_{sheet_name}.csv", index=False, encoding="utf-8-sig")
        if diagnostics_df is not None:
            diagnostics_df.to_csv(csv_dir / "selection_diagnostics.csv", index=False, encoding="utf-8-sig")

    # 7) Markdown 摘要
    if EXPORT_MARKDOWN_BRIEF:
        lines = []
        lines.append("# HW1 自動整理摘要\n\n")
        lines.append("這份摘要是程式自動重算四張主表後輸出。\n\n")

        if diagnostics_df is not None:
            lines.append("## 篩選診斷總表\n")
            for _, row in diagnostics_df.iterrows():
                lines.append(
                    f"- {row['來源表']}｜原始列數={row['原始列數']}｜"
                    f"local_df篩後={row['local_df篩後列數']}｜global_df篩後={row['global_df篩後列數']}｜"
                    f"Lift>1篩後={row['Lift>1篩後列數']}｜DF卡方>0篩後={row['DF卡方>0篩後列數']}｜"
                    f"最終候選={row['最終可排序候選數']}\n"
                )
            lines.append("\n")

        for sheet_name, df in completed_sheets.items():
            lines.append(f"## {sheet_name}\n")
            lines.append(f"- 總列數：{len(df):,}\n")
            lines.append(f"- TF-IDF 可用筆數：{df['TF-IDF'].notna().sum():,}\n")
            lines.append(f"- MI(用DF) 可用筆數：{df['MI(用DF)'].notna().sum():,}\n")
            lines.append(f"- Lift(用DF) 可用筆數：{df['Lift(用DF)'].notna().sum():,}\n\n")

            lines.append("### 候選池前 10 詞\n")
            pool = candidate_pools[sheet_name].head(10)
            for i, (_, row) in enumerate(pool.iterrows(), start=1):
                lines.append(
                    f"{i}. {row['詞']}｜入選方法數={row['入選方法數']}｜"
                    f"TF-IDF={row['TF-IDF']:.4f}｜MI={row['MI(用DF)']:.4f}｜"
                    f"Lift={row['Lift(用DF)']:.4f}\n"
                )

            if final_tables is not None:
                lines.append("\n### 自動挑選最終 20 個 keyword（前 10 示意）\n")
                final_df = final_tables[sheet_name].head(10)
                for i, (_, row) in enumerate(final_df.iterrows(), start=1):
                    lines.append(
                        f"{i}. {row['詞']}｜FinalScore={row['FinalKeywordScore']:.4f}｜"
                        f"Composite={row['CompositeScore']:.4f}｜Penalty={row['SupportPenalty']:.4f}｜"
                        f"Bonus={row['AgreementBonus']:.4f}\n"
                    )
            lines.append("\n")

        brief_md.write_text("".join(lines), encoding="utf-8")

    return {
        "completed_wb": completed_wb,
        "summary_wb": summary_wb,
        "final_wb": final_wb,
        "backup_wb": backup_wb,
        "diagnostics_wb": diagnostics_wb,
        "brief_md": brief_md,
        "csv_dir": csv_dir,
    }


def main():
    if not INPUT_XLSX.exists():
        raise FileNotFoundError(f"找不到輸入檔案：{INPUT_XLSX}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = get_sheet_counts(INPUT_XLSX)
    sheets = load_sheets(INPUT_XLSX)

    completed_sheets = {}
    for target_sheet, meta in TARGET_SHEETS.items():
        gram = meta["gram"]
        global_sheet = GLOBAL_SHEETS[gram]
        local_n = float(counts[target_sheet])
        global_n = float(counts[global_sheet])

        completed_sheets[target_sheet] = recompute_target_sheet(
            target_df=sheets[target_sheet],
            global_df=sheets[global_sheet],
            local_n=local_n,
            global_n=global_n,
        )

    top_tables, overview_df = build_top20_tables(completed_sheets, top_n=TOP_N)
    candidate_pools = build_candidate_pools(completed_sheets, top_n=TOP_N)

    final_tables = None
    backup_tables = None
    diagnostics_df = None
    if AUTO_SELECT_FINAL_20:
        final_tables, backup_tables, diagnostics_df = select_final_keywords(
            completed_sheets=completed_sheets,
            candidate_pools=candidate_pools,
        )

    outputs = write_outputs(
        output_dir=OUTPUT_DIR,
        completed_sheets=completed_sheets,
        top_tables=top_tables,
        overview_df=overview_df,
        candidate_pools=candidate_pools,
        final_tables=final_tables,
        backup_tables=backup_tables,
        diagnostics_df=diagnostics_df,
    )

    print("完成！")
    print(f"1. 重算後主表：{outputs['completed_wb']}")
    print(f"2. Top20 摘要總表：{outputs['summary_wb']}")
    if AUTO_SELECT_FINAL_20:
        print(f"3. 自動選出的最終 20 keyword：{outputs['final_wb']}")
        print(f"4. 候補 10 keyword：{outputs['backup_wb']}")
        print(f"5. 選詞診斷表：{outputs['diagnostics_wb']}")
        print(f"6. 摘要：{outputs['brief_md']}")
        if EXPORT_CSV:
            print(f"7. CSV 資料夾：{outputs['csv_dir']}")
    else:
        print(f"3. Word 前摘要：{outputs['brief_md']}")
        if EXPORT_CSV:
            print(f"4. CSV 資料夾：{outputs['csv_dir']}")


if __name__ == "__main__":
    main()
```

---

## 4. 六個指標：公式、直覺、以及「回答什麼行銷／商業問題」

以下 §4.1–§4.6 的「公式」與「直覺」段落為 HW1 原文（Notion toggle 內容）忠實抄錄；
「回答什麼行銷／商業問題」是把原文直覺轉譯為商業提問，屬於改寫而非新增知識。

### 4.1 TF-IDF

**公式：**

$$\text{TF-IDF}(t,d)=\text{tf-weight}(t,d)\cdot idf_t$$

其中 tf-weight 採用的是 log frequency：

$$\text{tf-weight}(t,d)=
\begin{cases}
1+\log_{10}(tf_{t,d}), & tf_{t,d}>0 \\
0, & tf_{t,d}=0
\end{cases}$$

IDF：

$$idf_t=\log_{10}\left(\frac{N}{df_t}\right)$$

**程式對應**（本地／全體兩版都算）：

```python
out["TF-IDF"]     = (1 + log10_series(out["TF"]))     * log10_series(local_n  / out["DF"])
out["全部TF-IDF"] = (1 + log10_series(out["全部TF"])) * log10_series(global_n / out["全部DF"])
```

**直覺（原文）：**
- 在這張表裡出現越多次 → 越重要。
- 在這張表的文件裡越少見 → 越有鑑別力。

**在這支程式中的角色（原文）：**
- TF-IDF 是「篇內代表性」最主要的分數之一。
- 但它不是唯一標準，因為 HW1 的目標不是只找「區分文件的詞」，而是要找「適合當 keyword 的詞」。

**回答什麼行銷／商業問題：**
> 在這批（品牌／產業）文本內部，哪些詞是「常被提到、又不是每篇都提」的代表性用語？
> ——適合當內容摘要、報告標題、SEO 內容主題的詞。

### 4.2 全部TF / 全部DF / 全部TF-IDF（背景語料統計量）

**原文：**
- 它在計算的是同一個詞在「全體語料（`全部_2gram` / `全部_3gram`）」裡的統計量。
- 在 HW1 不只要看一個詞在子語料中重不重要，還要看它相對於全體語料是不是「特別偏向某個主題」。

**直覺（原文）：**
- 如果一個詞在鴻海表裡很常出現，但在全部語料裡也到處都是 → 那它不一定是好的「鴻海 keyword」。
- 反過來，如果它在鴻海表很突出、在全體卻沒那麼常見 → 更可能是有鑑別力的 keyword。

**回答什麼行銷／商業問題：**
> 這個詞是「這個品牌／類別專屬的話題」，還是「整個市場都在講的通用詞」？
> ——這是品牌 share-of-voice 與差異化定位的基本判準。

### 4.3 TF 期望值 / DF 期望值

**原文：** 這個計算的是，如果這個詞在目標類別中**只是平均分布**，那它理論上應該出現多少次。

**公式：**

$$E_{TF}=\frac{\text{全部TF}}{\text{全體文件數}} \times \text{本地文件數}$$

$$E_{DF}=\frac{\text{全部DF}}{\text{全體文件數}} \times \text{本地文件數}$$

**程式對應：**

```python
out["TF期望值"] = out["全部TF"] / global_n * local_n
out["DF期望值"] = out["全部DF"] / global_n * local_n
```

**直覺（原文）：**
- 這是「背景期望值」。
- 後面卡方值就是拿「觀察值」去跟「期望值」比較。

**回答什麼行銷／商業問題：**
> 如果這個詞的討論量只是「按語料規模比例分配」，我們該看到多少？
> ——建立 benchmark 基線，後續才能說「超出預期多少」。

### 4.4 TF 卡方值 / DF 卡方值（保留正負號）

**原文：** 這個計算的是，一個詞在目標子語料中的出現情況，是否**高於期望值**，以及高了多少。

**公式：**

$$\chi^2=\frac{(O-E)^2}{E}$$

- $O$ = 觀察值
- $E$ = 期望值

但這支程式不是只算普通卡方，而是**保留正負號**：

$$\chi^2_{\text{signed}}=\frac{(O-E)^2}{E}\times
\begin{cases}
+1, & O \ge E \\
-1, & O < E
\end{cases}$$

**程式對應：**

```python
out["TF卡方值(保留正負號)"] = (((out["TF"] - out["TF期望值"]) ** 2) / out["TF期望值"]) \
                              * np.where(out["TF"] >= out["TF期望值"], 1, -1)
out["DF卡方值(保留正負號)"] = (((out["DF"] - out["DF期望值"]) ** 2) / out["DF期望值"]) \
                              * np.where(out["DF"] >= out["DF期望值"], 1, -1)
```

**為什麼保留正負號（原文）：**
- 因為一般卡方只有「偏離程度」，看不出是「高於期望」還是「低於期望」。
  但在 keyword extraction 裡，我們比較在意的是：這個詞是不是**高於期望**地集中在這個類別？
- 所以保留正負號，可以直接分辨：
  - 正值：偏向該類別。
  - 負值：不偏向該類別。

**為什麼程式最後主要用 DF 卡方，而不是 TF 卡方（原文）：**
- **TF 卡方**容易被少數文件內的高頻重複影響。
- **DF 卡方**更穩，因為它看的是「出現在哪些文件」，比較接近類別特徵詞的概念。

**回答什麼行銷／商業問題：**
> 這個話題在這個品牌／類別上的「討論廣度」，是否顯著高於市場平均應有的水準？
> 高多少（強度）？方向是正的還是負的（品牌被討論／被迴避）？
> ——用來做 over-index 分析：找出品牌的過度指標話題。

### 4.5 MI（用 DF）

**原文：**
- 這個計算的是，詞與類別的關聯程度。
- 這份作業 workbook 中，`MI(用DF)` 是依照表內既有公式來算的。
  - 它的角色比較像是「相對排序分數」，不完全等同於教科書中最標準的 mutual information 定義。
- 程式的設計原則是不去改動作業原本的邏輯，直接照 workbook 既有公式重算，讓結果能跟你的 Excel 表保持一致。
- 它在選詞中的角色，是一個「輔助關聯性指標」，不是最主要權重來源，但值得保留。

**程式中實際採用的公式（workbook 版）：**

$$\text{MI}_{\text{workbook}}(t,c)=\log_{10}\!\left(\frac{df_{t,c}}{df_t \times N_c}\right)$$

```python
out["MI(用DF)"] = log10_series(out["DF"] / (out["全部DF"] * local_n))
```

**回答什麼行銷／商業問題：**
> 這個詞與這個類別的關聯有多強？（作為 Lift 的輔助排序訊號）

> **評註（重要，非原文）**：把 workbook 的 MI 與 Lift 展開比較，可證明**兩者在同一張 sheet 內
> 是嚴格單調對應**，即排序完全相同：
> $$\text{Lift}=\frac{df_{t,c}/N_c}{df_t/N}=N\cdot\frac{df_{t,c}}{df_t \cdot N_c}
> \;\Longrightarrow\; \text{MI}_{\text{workbook}}=\log_{10}(\text{Lift})-\log_{10}(N)$$
> 因為 $N$（`global_n`）在同一 gram 下是常數，$\text{MI}$ 只是 $\text{Lift}$ 的
> 「取 log 再平移」。後果有三個，都是實質的方法論瑕疵：
> 1. `rank_mi` 與 `rank_lift` **完全相同**，所以 Lift 訊號的實際權重是 $0.30+0.15=0.45$，
>    而不是宣稱的 0.30；四方法融合實際上只是三方法。
> 2. 候選池中 MI 與 Lift 的 Top-20 **是同一批詞**，因此這些詞的 `入選方法數` 自動 +2，
>    `AgreementBonus` 被系統性放大 0.05，「共識」是假共識。
> 3. 原文說「MI 只給 15% 比較穩健」，但這個防衛在數學上失效了。
>    修法：把 MI 換成真正的 PMI $\log\frac{P(t,c)}{P(t)P(c)}$（等於 $\log \text{Lift}$，仍同單調，
>    所以真正該做的是**換一個不同族的指標**，例如 log-likelihood ratio、Jensen–Shannon
>    divergence 或 KL 貢獻量），或直接把 MI 從 `CANDIDATE_METHODS` 移除並把權重併回。

### 4.6 Lift（用 DF）

**原文：** 這個計算的是，一個詞在目標類別中的出現比例，相對於它在整體語料出現比例的放大倍數。

**公式：**

$$\text{Lift}(t,c)=\frac{P(t\mid c)}{P(t)}$$

在這份作業中，用 DF 版本寫就是：

$$\text{Lift}(t,c)=\frac{\dfrac{df_{t,c}}{N_c}}{\dfrac{df_t}{N}}$$

- $df_{t,c}$：詞 $t$ 在類別 $c$ 出現的文件數。
- $N_c$：類別 $c$ 的文件總數。
- $df_t$：詞 $t$ 在全體語料出現的文件數。
- $N$：全體文件總數。

**程式對應：**

```python
out["Lift(用DF)"] = (out["DF"] / local_n) / (out["全部DF"] / global_n)
```

**直覺（原文）：**
- $\text{Lift} > 1$：這個詞在該類別中比在全體更常見 → 偏向該類別。
- $\text{Lift} = 1$：沒有特別偏向。
- $\text{Lift} < 1$：不偏向該類別。

**原文對 Lift 地位的評價：**
- $\text{Lift}$ 在這個運算邏輯中的地位非常高。
- 因為 HW1 的核心不是只有「代表詞」，而是要挑出偏向某主題／類別的 keyword。
- 在這種情況下，Lift 非常關鍵。

**回答什麼行銷／商業問題：**
> 這個話題在這個品牌／類別裡的「富集倍數」是多少？
> ——與消費者研究中的 index（例：某族群購買某品類的 index = 130）完全同構，
> 是做 target audience profiling、品牌聯想強度排序的主力指標。

### 4.7 六指標對照表（依原文論述整理）

| 指標 | 看的是 | 量尺 | 對雜訊的穩健性 | 回答的商業問題 | 在最終分數的權重 |
|---|---|---|---|---|---|
| TF-IDF（本地） | 篇內代表性 | 無上界正數 | 中（受單篇高頻影響） | 這批文本內部的代表用語 | 0.25 |
| 全部TF-IDF | 背景語料的代表性 | 無上界正數 | — | 市場整體的通用語 | 不入最終分數（僅參考） |
| TF 卡方（signed） | TF 偏離背景期望的強度＋方向 | 無上界，可正可負 | 低（易被單篇重複衝高） | 提及次數是否 over-index | 不入最終分數（只出 Top20） |
| DF 卡方（signed） | DF 偏離背景期望的強度＋方向 | 無上界，可正可負 | 高 | 討論廣度是否 over-index | 0.30 |
| MI（用DF, workbook 版） | 詞與類別的關聯（相對排序） | 負值 log 尺度 | 中 | 關聯強度輔助 | 0.15 |
| Lift（用DF） | 類別內富集倍數 | 以 1 為基準的倍數 | 中高 | 富集倍數／index | 0.30 |

---

## 5. 程式的運行邏輯（原文四大 Step，完整抄錄與程式對應）

### Step 1：讀取與重算四張主表

原文：
- 程式先讀：
  - 全體參考表（2gram / 3gram）
  - 四張主表（產業、鴻海）
- 接著把四張主表所有分數重新算一遍。這樣做有兩個目的：
  1. 避免 Excel 公式沒有填滿
  2. 避免只依賴 Excel 的快取值
- 先將「把資料整理成可比較的乾淨數值表」。

**程式對應**：`get_sheet_counts()` → `load_sheets()` → 對四張 TARGET_SHEETS 逐一
`recompute_target_sheet(target_df, global_df, local_n, global_n)`。
主表與全體表以 `詞` 做 `how="left"` merge，把 `全部TF / 全部DF` 帶進來。

### Step 2：先輸出各方法的 Top 20 總表

原文：
- 這一步是在回答：**若只看單一方法排序，前 20 名是誰？**
- 程式會對每張表、每個方法各自排序，輸出：
  - TF-IDF top 20
  - TF卡方 top 20
  - DF卡方 top 20
  - MI top 20
  - Lift top 20

**程式對應**：`build_top20_tables()`。對 `METHOD_COLUMNS` 五個方法各自
`dropna → sort_values(desc) → head(20)`，同時攤平成一張長表 `overview_df`
（欄位：來源表 / 方法 / 排名 / 詞 / TF / DF / 分數）。
$4 \text{ sheets} \times 5 \text{ methods} = 20$ 張 Top20 表。

### Step 3：建立候選池

原文：
- 程式不會直接從全表去選最終 keyword，而是先把下列方法的 top N 合併成候選池：
  - TF-IDF
  - MI
  - Lift
  - DF卡方
- 接著進行：
  - 去重複
  - 計算每個詞被幾個方法同時支持（`入選方法數`）
- 為什麼要有候選池？
  - 最終 keyword selection 不應從全表直接做。
  - 應該先從「有一定證據支持的詞」開始挑。

**程式對應**：`build_candidate_pools()`。注意排序 tie-break 順序是
`["入選方法數", "Lift(用DF)", "MI(用DF)", "TF-IDF"]` 全部降冪；
`drop_duplicates(subset=["詞"])` 在 sort 之前執行（見 §8 踩坑）。
注意 `CANDIDATE_METHODS` 只有 4 個方法——**TF 卡方被刻意排除在候選池之外**，
理由見 §4.4「為什麼主要用 DF 卡方」。

### Step 4：進階版自動挑最終 20 keyword

#### 4.1 硬性篩選（Hard Filters）

原文：先把不可靠的詞排掉。

| 條件 | 2-gram | 3-gram |
|---|---|---|
| 本地 DF | ≥ 2 | ≥ 2，**如果篩太少，允許放寬成 DF ≥ 1** |
| 全體 DF | ≥ 2 | ≥ 2 |
| Lift | > 1 | > 1 |
| DF 卡方 | > 0 | > 0 |

原文理由：
> 因為在本次的情境中，要的不是「偶然出現的怪詞」，而是：
> - 有最基本支持度。
> - 確實偏向該類別。
> - 並且高於背景期望。

**程式對應**：四道 mask 依序套用，每道都記下存活筆數進 `diagnostics_rows`。
3-gram 放寬條件寫在第一道之後、其餘三道之前：
`if gram == "3gram" and RELAX_... and after_local_df < FINAL_KEYWORD_N:` → `min_local_df = 1`。

#### 4.2 多方法融合排序（Rank Fusion）

原文：
- 篩選後，程式不直接用原始分數加總，而是先把每個方法都轉成 **0~1 的百分位排名**：
  `rank_tfidf`、`rank_lift`、`rank_dfchi`、`rank_mi`
- 不同指標的量尺不同，因此先轉 rank，而不直接加總原始分數：
  - TF-IDF 範圍一種。
  - Lift 範圍一種。
  - χ² 範圍一種。
  - MI 也一種。
- 若直接加總，某一個量級大的方法會主導結果，因此採 rank-based fusion。

**程式對應**：`_rank01()` = `s.rank(method="average", pct=True)`。

#### 4.3 加權組合分數

$$\text{CompositeScore}=0.25 \times rank_{\text{TF-IDF}}+0.30 \times rank_{\text{Lift}}+0.30 \times rank_{\text{DFChi}}+0.15 \times rank_{\text{MI}}$$

原文備註：**權重可以自己調整！**

#### 4.4 Support penalty（穩定性懲罰）

原文：
- 意義：讓「穩定出現的詞」比「偶發衝高的詞」更有優勢。

$$\text{SupportPenalty}=\min\left(1,\frac{DF}{3}\right)\times\min\left(1,\frac{\text{全部}DF}{5}\right)$$

$$\text{AdjustedScore}=\text{CompositeScore}\times\text{SupportPenalty}$$

- 主要用來懲罰這類詞彙：本地 DF 很低、全體 DF 也很低。
- 這類詞即使某個方法分數很高，也不一定是好的 keyword：
  - 偶發事件。
  - 特殊拼法。
  - 切詞錯誤。
  - 僅在單一文件出現的噪音。

#### 4.5 Agreement bonus（方法共識加分）

原文：多個方法都認為它重要，那它更值得被列入最終 20。

$$\text{AgreementBonus}=0.05 \times (\text{入選方法數}-1)$$

$$\text{FinalKeywordScore}=\text{AdjustedScore}+\text{AgreementBonus}$$

原文白話：
> 如果某個詞同時被 TF-IDF、Lift、DF 卡方支持，那它通常比「只被一種方法支持」的詞更可靠。

原文自我定位這一步在做的事：
- ensemble ranking
- evidence aggregation

#### 4.6 取最終 20 + 候補 10

```python
final_tables[sheet_name]  = temp.head(FINAL_KEYWORD_N).copy()             # 1~20
backup_tables[sheet_name] = temp.iloc[FINAL_KEYWORD_N:FINAL_KEYWORD_N + BACKUP_N].copy()  # 21~30
```

---

## 6. 權重設計理由（原文 toggle「為什麼這樣安排權重？」完整抄錄）

### 1. 為什麼 Lift 給 30%？

因為 HW1 要你挑的是 **keyword**，而且很多情境其實是在挑「某主題／類別的代表詞」。
Lift 最能回答：

> 這個詞是不是在這個類別裡特別富集？

這件事對 keyword selection 非常關鍵，所以給高權重合理。

### 2. 為什麼 DF 卡方也給 30%？

因為 DF 卡方在衡量的是：

> 這個詞在這個類別中的出現文件數，是否高於背景期望？

這比單純看 TF 更穩定，也更不容易被單篇高頻重複干擾。
對「類別特徵詞」來說，DF 卡方非常有價值，所以也給高權重。

### 3. 為什麼 TF-IDF 是 25%，不是最高？

TF-IDF 當然重要，因為它能抓出「在這張表裡很有代表性」的詞。
但 HW1 已經提醒了一個核心問題：

> 有些詞可能是好 keyword，但不一定是好 feature；
> 有些詞在小語料中 TF-IDF 高，但不代表它最適合拿來當最終 keyword。

所以 TF-IDF 不應該完全主導最終結果。
它應該保留，但不該凌駕於「類別偏向性」之上。

### 4. 為什麼 MI 只有 15%？

因為你這份 workbook 的 `MI(用DF)` 雖然有參考意義，
但它更適合做「關聯性輔助排序」，不建議當作最主導的分數來源。
所以保留它、但權重較低，是比較穩健的做法。

---

## 7. 輸出檔案清單（原文「程式最後會輸出哪些東西？」）

| # | 檔名 | 作用（原文） | 用途（原文） |
|---|---|---|---|
| 1 | `hw1_table_completed.xlsx` | 四張主表全部重算好的版本 | 確認每個欄位都有值，作為正式分析底稿 |
| 2 | `hw1_top20_summary.xlsx` | 各方法排序後的 Top 20 總表 | 比較不同方法偏好的詞有什麼差異 |
| 3 | `final_keywords_auto.xlsx` | 每張表最終自動挑選出的 20 個 keyword | 這是最接近「最終答案」的檔案 |
| 4 | `final_keywords_backup.xlsx` | 第 21–30 名候補詞 | 若覺得某個詞不好看、切得怪、太泛，可以用候補替換 |
| 5 | `selection_diagnostics.xlsx` | 記錄每張表經過每個篩選條件後還剩多少詞 | **非常適合放進 Word 報告方法論中**，說明如何從大量候選詞縮減到最終 20 個 |
| 6 | `hw1_before_word_brief.md` | 在寫 Word 前，先用文字快速看每張表的關鍵結果 | 快速掌握整體結果，不用先開 Excel 慢慢找 |

外加 `csv_exports/` 資料夾（`encoding="utf-8-sig"`，讓 Excel 開中文 CSV 不亂碼），
內含 `00_overview_top20.csv`、`raw_*.csv`、20 張 `*__方法.csv`、
`候選池_*.csv`、`最終20_*.csv`、`候補10_*.csv`、`selection_diagnostics.csv`。

### 7.1 診斷表（diagnostics）的欄位設計

這是整份專案最值得複製的一張表——它把「漏斗每一關剩幾個」寫成報告可直接引用的證據鏈：

| 欄位 | 意義 |
|---|---|
| `來源表` | 哪張主表 |
| `原始列數` | 篩選前總詞數 |
| `local_df_threshold` | 實際用的本地 DF 門檻（可能已被放寬成 1） |
| `3gram_df條件放寬` | `Y` / `N`，是否觸發放寬 |
| `local_df篩後列數` | 過第 1 關存活數 |
| `global_df篩後列數` | 過第 2 關存活數 |
| `Lift>1篩後列數` | 過第 3 關存活數 |
| `DF卡方>0篩後列數` | 過第 4 關存活數 |
| `最終可排序候選數` | 進入 rank fusion 的筆數 |
| `最終輸出筆數` | `min(20, 候選數)` |
| `候補輸出筆數` | `min(10, max(0, 候選數 - 20))` |

---

## 8. 作者的思考順序（依原文重建）與踩過的坑

### 8.1 思考順序

1. **先在 Excel workbook 手做**（六張 sheet、A1 放文件數、第 3 列放欄名、公式欄手拉）。
2. **發現 Excel 不可信**：公式可能沒填滿、也不想依賴快取值 → 決定「所有指標在 Python 端重算一遍」。
   頁面第一行的「記得要填補上所有的資料！」就是這個焦慮的殘留。
3. **不改作業原本的公式邏輯**：即使發現 workbook 的 `MI(用DF)` 不是教科書標準 MI，
   仍照 workbook 公式重算，理由是「讓結果能跟你的 Excel 表保持一致」。
   → 這是「可對帳性 > 理論正確性」的明確取捨。
4. **先看單一方法 Top 20**，弄清楚不同方法各自偏好什麼詞（Step 2）。
5. **意識到單一方法不可靠** → 改成「先建候選池、再從候選池裡選」（Step 3）。
   原文明說：「最終 keyword selection 不應從全表直接做。」
6. **加硬性篩選**（Step 4.1），把偶發詞、方向錯的詞先排除。
7. **發現量尺不可加總** → 改 rank-based fusion（Step 4.2）。
8. **發現低 DF 的詞會靠單一指標衝上榜** → 加 support penalty（Step 4.4）。
9. **想獎勵多方法共識** → 加 agreement bonus（Step 4.5）。
10. **預留人工覆核空間** → 額外輸出候補 10 名，因為「若覺得某個詞不好看、切得怪、太泛，可以用候補替換」。
11. **為寫 Word 報告做準備** → 額外輸出 diagnostics 表與 markdown brief，
    diagnostics 明確是為了「放進 Word 報告方法論中，說明如何從大量候選詞縮減到最終 20 個」。

**核心洞見（原文兩處都提到）**：
> 有些詞可能是好 keyword，但不一定是好 feature。

這是整套設計的哲學支點——因此 TF-IDF（分類 feature 導向）被降權，
Lift / DF 卡方（類別富集導向）被升權。

### 8.2 踩過的坑與 workaround 清單

| # | 坑 | 作者的 workaround | 在程式中的位置 |
|---|---|---|---|
| 1 | Excel 公式沒拉滿 / 快取值不可信 | 全部指標在 Python 重算，不讀 Excel 的計算結果，只讀 `編號/詞/TF/DF` 四個原始欄 | `recompute_target_sheet()` 只取 `[["編號","詞","TF","DF"]]` |
| 2 | 文件總數被放在 A1（不是欄名列） | 對同一檔案讀兩次：一次 `header=None, nrows=1, usecols="A"` 撈 A1，一次 `header=2` 讀資料 | `get_sheet_counts()` / `load_sheets()` |
| 3 | Excel `LOG()` 預設 base 10，Python `np.log` 是自然對數 | 自寫 `log10_series()` 明確用 `np.log10`，並在 docstring 註明「模擬 Excel 的 LOG() 預設 base=10」 | `log10_series()` |
| 4 | `log(0)` / `log(負數)` 會炸或出 `-inf` | `np.where(s > 0, np.log10(s), np.nan)`，非正值一律轉 NaN；下游用 `dropna(subset=[method])` 排除 | `log10_series()` |
| 5 | 一般卡方看不出方向 | 自創「保留正負號的卡方」，用 `np.where(O >= E, 1, -1)` 乘上去 | 卡方兩欄 |
| 6 | TF 卡方被單篇高頻重複污染 | 最終分數只用 DF 卡方；TF 卡方仍算、仍出 Top20，但**不列入 `CANDIDATE_METHODS`、不進 Composite** | `CANDIDATE_METHODS` |
| 7 | 不同指標量級差太多，直接加總會被某一指標主導 | 全部先轉 0~1 百分位 rank 再加權 | `_rank01()` |
| 8 | 低 DF 詞靠偶發衝高分（切詞錯誤、特殊拼法、單篇噪音） | 乘上 `min(1, DF/3) × min(1, 全部DF/5)` 的 support penalty | `_support_penalty()` |
| 9 | **3-gram 篩完不足 20 個** | 條件放寬：本地 DF 門檻由 2 降為 1（`RELAX_LOCAL_DF_3GRAM_TO_1_IF_TOO_FEW`），並在 diagnostics 記 `3gram_df條件放寬 = Y` 留下痕跡 | `select_final_keywords()` Step A |
| 10 | 候選池補詞（原文註解宣稱的保底機制） | 註解寫「若篩完太少，至少保底用 candidate pool 的詞補進來（但仍保留分數紀錄）」；**實作只做了 `merge` 把 `入選方法數` 帶進來，並沒有真的把池中被篩掉的詞加回 `temp`** | 見下方評註 |
| 11 | 篩完可能是空表，後續 `_rank01` 會出錯 | `if len(temp) > 0: ... else:` 分支，空表時把所有計算欄位塞 `np.nan`，保住輸出結構 | `select_final_keywords()` |
| 12 | 候選詞不在池中 → `入選方法數` 為 NaN → bonus 算不出來 | `fillna(0)`（欄位層）＋ `_agreement_bonus()` 內再 `fillna(1)`（雙重保險，使 bonus = 0） | 兩處 |
| 13 | Excel sheet 名稱上限 31 字、且不可含特殊字元 | 所有 `sheet_name=...[:31]`；Top20 表名再 `.replace("(","").replace(")","").replace("/","_")` | `write_outputs()` |
| 14 | 中文 CSV 在 Excel 開啟亂碼 | 全部 `encoding="utf-8-sig"` | `write_outputs()` |
| 15 | 自動選出的詞可能「不好看、切得怪、太泛」 | 額外輸出第 21–30 名候補檔，保留人工替換的餘地 | `final_keywords_backup.xlsx` |
| 16 | 寫 Word 報告時無法交代「怎麼從幾千詞縮到 20 詞」 | 專門做 diagnostics 漏斗表 + markdown brief | `selection_diagnostics.xlsx` / `hw1_before_word_brief.md` |

> **評註（第 10 項，非原文）**：這是本專案最實質的 bug。註解意圖是
> 「hard filter 太嚴時用候選池保底」，但實際程式是
> ```python
> pool = candidate_pools[sheet_name][["詞", "入選方法數"]].copy()
> temp = temp.merge(pool, on="詞", how="left")     # left join → 只補欄，不補列
> temp["入選方法數"] = temp["入選方法數"].fillna(0)
> ```
> `how="left"` 表示 `temp`（已被四道 filter 砍過）的列數不變，只是多一個 `入選方法數` 欄。
> 被 filter 砍掉但在候選池裡的詞，**不會**被加回來。
> 因此若某張表 hard filter 後只剩 8 個詞，最終就只會輸出 8 個 keyword，
> diagnostics 的「最終輸出筆數」會誠實顯示 8，但作業要求的 20 個不會被補滿。
> 真要實作保底，需要 outer/right join 或 `pd.concat` 把池中缺的詞接回並標記「保底補入」。

> **評註（其他值得注意的實作細節，非原文）**
> - `build_candidate_pools()` 的 `drop_duplicates(subset=["詞"])` 在 `sort_values` **之前**執行，
>   所以保留下來的那一列是 `pd.concat` 順序中最早出現的（即 `CANDIDATE_METHODS` 中較前的方法），
>   `來源方法` 欄因此不代表「該詞的最佳方法」，只代表「第一個撞到它的方法」。
>   排序本身用的是 `入選方法數` 等欄，不受影響，但 `來源方法` 欄在解讀時容易誤導。
> - `_rank01()` 是在**已篩選的子集**上算百分位，不是在全表上。
>   所以 `CompositeScore` 的絕對數值不可跨表比較，只能在同一張表內比較排序。
> - 3-gram 的放寬判斷發生在**第一道 filter 之後、其餘三道之前**，
>   所以「放寬後仍不足 20」是可能的（Lift>1 與 DF卡方>0 還會再砍），而程式不會二次放寬。
> - `get_sheet_counts()` 對 workbook 內**所有** sheet 都做 `float(A1)`，
>   若日後在檔案裡多加一張非數值 A1 的說明頁，整支程式會在讀檔階段就 crash。
> - `TARGET_SHEETS` 裡的 `class_name`（"產業"/"鴻海"）在程式中**從未被使用**，是預留但未接的欄位。
> - `gram` 判斷用 `"3gram" in sheet_name` 的字串比對，而 `TARGET_SHEETS` 已明確帶了
>   `meta["gram"]`；此處沒有沿用 meta，是可簡化的重複邏輯。
> - 沒有任何 unit test、沒有 log 檔、沒有隨機種子問題（全程 deterministic）。
> - `AdjustedScore` 與 `FinalKeywordScore` 都輸出到最終檔，所以評審可以逐項拆解每個詞的得分來源
>   （Composite / Penalty / Bonus 三段），這點做得很好——是可解釋性設計。

---

## 9. 報告呈現慣例（從 HW1 的輸出設計反推）

作者把「分析」與「寫報告」明確分成兩個階段，並為報告階段預先生產素材：

1. **底稿層**：`hw1_table_completed.xlsx` — 所有欄位都有值的乾淨表，作為「正式分析底稿」。
2. **比較層**：`hw1_top20_summary.xlsx` — 一張 `00_overview_top20` 長表（來源表／方法／排名／詞／TF／DF／分數）
   讓「不同方法偏好的詞有什麼差異」可以直接做交叉比較；後面再附每張 Top20 明細與候選池。
3. **結論層**：`final_keywords_auto.xlsx` — 「最接近最終答案的檔案」。
4. **備援層**：`final_keywords_backup.xlsx` — 承認自動化會選出不合語感的詞，預留人工替換。
5. **方法論層**：`selection_diagnostics.xlsx` — 漏斗表，直接對應 Word 報告的「方法」章節。
6. **速讀層**：`hw1_before_word_brief.md` — 寫作前的文字摘要，避免「先開 Excel 慢慢找」。

**慣例要點**：
- 用 toggle（`<details>`）把「公式 / 直覺 / 在本專案的角色」三段固定結構化，每個指標一個 toggle。
- 每個指標都寫「**直覺**」段落——用一句白話說明「越高代表什麼」。
- 每個設計選擇都寫「**為什麼**」（為什麼保留正負號、為什麼用 DF 而非 TF 卡方、為什麼 Lift 給 30%）。
- 誠實標註方法的限制（明說 workbook 的 MI「不完全等同於教科書中最標準的 mutual information 定義」）。
- 所有可調參數集中在 CONFIG 區並附中文註解，配上「權重可以自己調整！」的邀請。

---

## 10. 可重用資產

### 10.1 檢查清單 A：讀入「人手做的 Excel 分析表」

- [ ] 欄名真的在第 1 列嗎？（本案在第 3 列 → `header=2`）
- [ ] 有沒有 metadata（總筆數、日期、樣本數）被塞在資料區塊裡？（本案 A1 = 文件總數）
- [ ] 公式欄有沒有拉滿？→ **預設不信任，只讀原始欄位，指標一律在程式端重算**
- [ ] Excel 的 `LOG()` 是 base 10，程式的 `log()` 通常是自然對數 → 明確指定 base
- [ ] 分母／log 的輸入可能為 0 或負 → 統一轉 NaN，下游 `dropna`
- [ ] 輸出 sheet 名稱 ≤ 31 字、去掉 `( ) /` 等字元
- [ ] 中文 CSV 一律 `utf-8-sig`
- [ ] 讀 A1 這類「全 sheet 掃描」的程式碼，要能容忍未來新增的說明頁

### 10.2 檢查清單 B：任何「多指標融合排序」的專案

- [ ] 各指標量尺是否可比？不可比 → **先轉百分位 rank 再加權，絕不直接加總原始分數**
- [ ] 權重加總是否為 1？每個權重是否寫得出「為什麼是這個數」？
- [ ] **確認各指標彼此不是單調同構**（本案 MI 與 Lift 就是，導致實際權重 0.45 而非 0.30）
- [ ] 低樣本支持度的項目是否會靠單一指標衝上榜？→ 加 support penalty
- [ ] 「多指標共識」的加分，是否被同構指標重複計算？
- [ ] rank 是在全表算還是在篩選後子集算？（影響能否跨組比較）
- [ ] 最終分數是否可拆解回各分項（Composite / Penalty / Bonus）以便解釋？
- [ ] 是否輸出候補名單供人工覆核？

### 10.3 決策規則（可直接套用的判準）

| 情境 | 規則 | 出處 |
|---|---|---|
| 要「類別特徵詞」 | 用 **DF** 基礎的指標（DF 卡方、DF Lift），不用 TF 基礎的 | HW1 §4.4 |
| 要「篇內代表詞」 | 用 TF-IDF | HW1 §4.1 |
| 判斷方向性 | 卡方一定要 **保留正負號**，只留正值（高於期望） | HW1 §4.4 |
| 判斷富集 | `Lift > 1` 才算偏向該類別；`= 1` 無偏向；`< 1` 反向 | HW1 §4.6 |
| 最小支持度 | 本地 DF ≥ 2、全體 DF ≥ 2；3-gram 不足時才降到 1，且必須留紀錄 | HW1 §5 Step 4.1 |
| 穩定性門檻 | 本地 DF < 3 或全體 DF < 5 → 按比例降權，不是直接砍 | HW1 §5 Step 4.4 |
| 共識加分 | 每多一個支持方法 +0.05 | HW1 §5 Step 4.5 |
| 候選池 vs 全表 | **永不從全表直接選最終答案**，先建「有證據支持」的候選池 | HW1 §5 Step 3 |
| 理論正確 vs 可對帳 | 若上游（老師的 workbook / 客戶的既有報表）公式有瑕疵，**照它算以維持可對帳**，但要在文件中明說瑕疵 | HW1 §4.5 |
| 自動化的邊界 | 自動選 Top N，另出第 N+1 ~ N+10 候補；語感／切詞怪的詞由人替換 | HW1 §7 |

### 10.4 診斷順序（Keyword / 特徵詞篩選的標準漏斗）

依序執行，**每一關都記錄存活筆數**，最後把整條漏斗寫進報告方法論：

```
原始詞表（原始列數）
  → 1. 本地支持度：DF ≥ 2                    → local_df篩後列數
       └ 若 3-gram 存活 < 目標 N，降為 DF ≥ 1，並標記「條件放寬 = Y」
  → 2. 背景支持度：全部DF ≥ 2                → global_df篩後列數
  → 3. 方向性（富集）：Lift > 1               → Lift>1篩後列數
  → 4. 方向性（超越期望）：DF卡方 > 0         → DF卡方>0篩後列數
  → 5. 併入候選池的「入選方法數」
  → 6. 各指標轉 0~1 百分位 rank
  → 7. 加權 → CompositeScore
  → 8. × SupportPenalty → AdjustedScore
  → 9. + AgreementBonus → FinalKeywordScore
  → 10. 排序，取前 N（最終）＋ 第 N+1~N+10（候補）
```

### 10.5 可直接搬用的程式片段

| 片段 | 用途 |
|---|---|
| `log10_series()` | 任何要與 Excel 對帳的 log 計算；自帶非正值防護 |
| `get_sheet_counts()` | 從「metadata 塞在 A1」的 workbook 撈參數 |
| signed χ² 兩行 | 需要方向性的偏離度指標（over/under-index 分析） |
| `_rank01()` | 多指標融合前的標準化 |
| `_support_penalty()` | 低樣本平滑降權（比硬砍溫和），可推廣到任何 `min(1, n/n_stable)` 情境 |
| `_agreement_bonus()` | ensemble 共識加分 |
| `diagnostics_rows` 結構 | 任何篩選漏斗的可稽核紀錄表 |
| `write_outputs()` 的分層輸出設計 | 底稿／比較／結論／備援／方法論／速讀 六層交付物 |

### 10.6 可轉譯的行銷分析對應（評註，非原文）

HW1 的指標組合，本質上就是行銷分析中「index / over-index 分析」的文字版，
可以直接換掉輸入資料重用：

| HW1 概念 | 行銷分析對應 |
|---|---|
| 詞 $t$ | 商品 / 品類 / 話題 / 行為 |
| 類別 $c$（鴻海、產業） | 客群 segment / 通路 / 時段 / 活動組 |
| $df_{t,c}$ | 該 segment 中提及／購買該項的人數 |
| $N_c$ | 該 segment 人數 |
| Lift | segment index（>1 = 該客群偏好） |
| signed DF 卡方 | over/under-index 的顯著強度與方向 |
| support penalty | 小樣本 segment 的可信度降權 |
| 候選池 + 共識加分 | 多指標一致才納入行銷洞察，避免單一指標誤導 |
| diagnostics 漏斗表 | 洞察篩選過程的可稽核附錄 |

---

## 11. 材料的不足與待補（評註，非原文）

1. **沒有任何實際結果數據**。HW1 頁面只有方法與程式，Top20 詞表、diagnostics 實際數字、
   最終 20 個 keyword 名單都沒有貼在 Notion 上。因此無法驗證方法在真實資料上的表現，
   也看不出「產業」與「鴻海」兩類別最終選出什麼詞。
2. **上游前處理完全缺失**。切詞（jieba? CKIP?）、停用詞、n-gram 產生、
   文件收集與去重、`TF`/`DF` 怎麼算出來的，全部在這支腳本之外，Notion 上沒有紀錄。
   這是重現性的最大缺口。
3. **`INPUT_XLSX` / `OUTPUT_DIR` 是空字串**。程式碼是「模板狀態」，直接跑會拋 `FileNotFoundError`。
4. **沒有統計顯著性檢定**。signed χ² 只當排序分數用，沒有對照臨界值（例 3.84 / p<0.05），
   也沒有多重比較校正——在數千個詞上做偏離度排序，理論上該處理 FDR。
5. **權重完全靠論述、沒有實證**。0.25/0.30/0.30/0.15 有很好的說理，但沒有做敏感度分析
   （換權重後 Top20 重疊率是多少？），也沒有人工標註的 gold standard 可評估。
6. **沒有評估指標**。整套流程沒有 precision/recall、沒有人工評分、沒有跟基線（純 TF-IDF）比較。
   §10.2 的檢查清單能檢查一致性，但無法回答「這 20 個詞比純 TF-IDF 的 20 個詞好嗎」。
7. **HW2 完全空白**，原文書只有 PDF、沒有讀書筆記，所以這批材料裡沒有任何
   教科書章節對應、沒有課堂概念與作業的橋接說明。
8. **`入選方法數` 的共識訊號被 MI≡Lift 污染**（見 §4.5 評註），這是尚未被作者發現的問題。

---

## 12. 抓取備註

- HW1 全文以 `notion-fetch` 取得，含所有 `<details>` toggle 展開內容；程式碼區塊逐字抄錄，
  未做任何格式修正或 bug 修補（bug 只在評註中指出）。
- Notion 的 inline LaTeX 語法 `$` + 反引號 包裹已轉為標準 `$...$` / `$$...$$`。
- 原文中兩處重複句（「在這份作業中，用 DF 版本寫」出現兩次、
  「這類詞即使某個方法分數很高，也不一定是好的 keyword」出現兩次）已在本檔合併，
  屬於原稿的重複贅述，非資訊遺漏。
- HW2、原文書兩頁確認無隱藏內容（分別回傳 `<blank-page>` 與單一 `<file>` block）。
