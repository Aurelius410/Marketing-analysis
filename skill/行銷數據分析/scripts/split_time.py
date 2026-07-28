#!/usr/bin/env python3
"""
時間切分驗證（12 §二）—— 三種切法的最小實作，外加五道洩漏關卡。

12 §二 只給了三行 sklearn 呼叫（reference 自己標「待實作」）。三行本身不難，
難的是**切完之後沒有人去驗**。這支腳本的價值在後半段：切完，逐折把數字攤開來，
讓「看起來很正常其實已經洩漏」的切法當場現形。

三種切法（照 12 §二 列的三種，不多不少）：

  ① stratified  StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                 目標與時間無關（顧客屬性分類、商品歸類、評論情感）才可以用
  ② group       GroupKFold(n_splits=5)，groups=顧客欄
                 同一顧客有多筆列時**必須**用它，不能按列切
  ③ time        TimeSeriesSplit(n_splits=4, gap=gap_rows, test_size=test_rows)
                 rolling origin；有時間結構就是它

五道關（每一道的門檻都標了出處，沒有一條是憑感覺）：

  1. 切法與資料結構相符    12 §二 判準表
  2. **未來洩漏（逐折）**   訓練集最晚時點 < 驗證集最早時點   ← 這支腳本的核心
  3. 顧客跨邊（分組洩漏）  12 §二「行銷資料最常見的隱藏洩漏」
  4. 各段樣本數與正例率    正例 = 0 是靜默失敗；正類 < 200 見 12 §九
  5. gap 與入庫延遲        12 §二 的 assert gap_days >= max_ingest_lag_days

關卡 2 的兩個陷阱（這兩件事是本腳本大半的價值）：

  · **逐折比，不可用全域 max/min 比。** rolling origin 的折 4 訓練集本來就晚於
    折 1 的驗證集，拿 全域train_max 去比 全域valid_min，**正確的 pipeline 也一定
    被判成洩漏**（12 §二 明寫這一條）。本腳本每一折各自比自己的。
  · **切點落在同一時點內部也是洩漏。** 一顧客一月一列的面板，同一個 as_of 有幾千列；
    TimeSeriesSplit 按「列數」切會把這幾千列從中間剖開，訓練集與驗證集共用同一天。
    此時 train_max == valid_min，間隔 0 天 —— 排序沒錯、程式沒報錯、AUC 漂亮。
    本腳本預設 --boundary auto：偵測到時間欄有重複值就改切在**時點邊界**上。

gap 的單位陷阱（12 §二 明寫）：`TimeSeriesSplit(gap=)` 的單位是**列數**，
`make_label(gap_days=)` 的單位是**日曆天**。只有每列等時距時前者才換算得回後者；
交易明細那種不等時距的資料，`TimeSeriesSplit(gap=)` 擋不住洩漏，唯一的防線是
`make_label(gap_days=)`。關卡 5 會實際量相鄰時點的間距來判斷等不等時距。

用法：
    # 時間切分（流失、下期購買、CLV —— 標籤含「未來 N 天」的一律走這條）
    python split_time.py 2026Q3_電商 --method time \\
        --label-col 是否流失 --time-col as_of --group-col 客戶編號 \\
        --gap-days 30 --max-ingest-lag-days 30 --horizon-days 90

    # 同一顧客多筆列（每次交易一列、每月一列）
    python split_time.py 2026Q3_電商 --method group \\
        --label-col 是否回應 --group-col 客戶編號

    # 目標與時間無關（顧客屬性分類、商品歸類）
    python split_time.py 2026Q3_電商 --method stratified --label-col 性別

    python split_time.py --self-test

輸出：
    統計表/預測模型/切分_逐折摘要.csv    逐折的樣本數、正例率、時間邊界、跨邊顧客數
    統計表/預測模型/切分_五道關.csv      五道關結果
    模型輸出/split_time.json             機器可讀（切分規格 + 逐折 + 關卡）
    模型輸出/split_folds.parquet         逐列的折別指派，供下游重現同一組切分

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 五道關全過
    1  = 有 error 擋住（洩漏、某折沒有正例、切法違反判準表的「必須」）
    2  = 只有 warning，可往下但報告要寫明
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import project_dir  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 門檻。出處寫在每一行後面，不要在這裡調 ────────────────────
MIN_POSITIVE_TOTAL = 200      # 12 §九：正類 < 200 筆 → 不建模，改業務規則
MIN_TIME_FOLDS = 3            # 12 §二：資料期間 < 2 個完整週期 → rolling origin 至少 3 折
SEASON_CYCLE_DAYS = 365       # 12 §二：測試集長度 ≥ 一個完整週期（多數零售 = 12 個月）
POS_RATE_RATIO_MAX = 2.0      # 折間驗證正例率 max/min ——【本腳本自訂】reference 未給門檻
EQUAL_SPACING_RATIO_MAX = 1.5 # 相鄰時點間距 max/min ——【本腳本自訂】判定「等時距」用

# 12 §二 的三行程式碼各自帶的預設折數：分層與分組 5 折、rolling origin 4 折
FOLD_DEFAULTS = {"stratified": 5, "group": 5, "time": 4}
METHOD_NAMES = {
    "stratified": "StratifiedKFold（隨機分層）",
    "group": "GroupKFold（依顧客分組）",
    "time": "TimeSeriesSplit（rolling origin）",
}

_errors: list[str] = []
_warnings: list[str] = []
_infos: list[str] = []


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def detail(msg: str) -> None:
    print(f"     · {msg}")


def warn(fact: str, todo: str) -> None:
    _warnings.append(f"{fact}｜{todo}")
    print(f"  ⚠ {fact}")
    print(f"     → {todo}")


def err(fact: str, todo: str) -> None:
    _errors.append(f"{fact}｜{todo}")
    print(f"  ⛔ {fact}")
    print(f"     → {todo}")


def info(msg: str) -> None:
    _infos.append(msg)
    print(f"  · {msg}")


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy／Timestamp，讓它存成字串而不是整支掛掉。

    正規做法是在**來源**就轉成原生型別（summarize_folds 的每個 int()／round()
    都是為此），因為折編號、樣本數一路從 numpy 陣列帶出來時型別是 int64，
    json.dumps 會在所有關卡都跑完、CSV 都寫好之後才丟 TypeError，
    退出碼 70 蓋掉前面全綠的結論。這個 default= 只是最後一道網。
    """
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    return str(o)


# ══════════════════════════════════════════════════════════════
#  參數值檢查（→ 64。獨立成函式，自我測試才驗得到）
# ══════════════════════════════════════════════════════════════
def validate_values(method: str | None, n_splits: int | None, gap_days: int,
                    horizon_days: int | None, max_ingest_lag_days: int | None,
                    gap_rows: int, test_rows: int | None,
                    time_col: str | None, group_col: str | None) -> list[str]:
    """回傳用法錯誤訊息清單（空 = 合法）。

    為什麼要在 argparse 層擋：值不合法代表**腳本根本沒跑起來**，那是 64；
    掉到執行期才丟 ValueError 會被判成 1（資料問題），驅動腳本分不出來。
    """
    msgs: list[str] = []
    if method not in (None, *FOLD_DEFAULTS):
        msgs.append(f"--method 只能是 {'／'.join(FOLD_DEFAULTS)}（收到 {method}）")
    if n_splits is not None and n_splits < 2:
        msgs.append(f"--n-splits 至少 2（收到 {n_splits}）")
    if gap_days < 0:
        msgs.append(f"--gap-days 不可為負（收到 {gap_days}）")
    if horizon_days is not None and horizon_days <= 0:
        msgs.append(f"--horizon-days 要 > 0（收到 {horizon_days}）")
    if max_ingest_lag_days is not None and max_ingest_lag_days < 0:
        msgs.append(f"--max-ingest-lag-days 不可為負（收到 {max_ingest_lag_days}）")
    if gap_rows < 0:
        msgs.append(f"--gap-rows 不可為負（收到 {gap_rows}）")
    if test_rows is not None and test_rows < 1:
        msgs.append(f"--test-rows 至少 1（收到 {test_rows}）")
    if method == "time" and not time_col:
        msgs.append("--method time 一定要給 --time-col（沒有時間欄就切不出 rolling origin）")
    if method == "group" and not group_col:
        msgs.append("--method group 一定要給 --group-col（GroupKFold 沒有 groups 就退化成 KFold）")
    return msgs


# ══════════════════════════════════════════════════════════════
#  載入
# ══════════════════════════════════════════════════════════════
def load_table(p: Any, explicit: Path | None) -> tuple[pd.DataFrame, Path]:
    """讀建模表（特徵 + 標籤 + as_of 一列一觀測）。"""
    candidates = [explicit] if explicit else [
        p.mart / "model_table.parquet",
        p.mart / "model_table.csv",
    ]
    for path in candidates:
        if path and path.exists():
            df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
                  else pd.read_csv(path))
            return df, path
    tried = "、".join(str(c) for c in candidates if c)
    raise FileNotFoundError(
        f"找不到建模表：{tried}\n"
        f"  建模表是「一列一觀測，含特徵 + 標籤 + as_of」的那張表 —— "
        f"由 build_features(as_of) 與 make_label(as_of, horizon_days, gap_days) "
        f"兩支獨立函式合出來（12 §二）。用 --table 指定路徑。")


def as_binary_label(s: pd.Series, col: str) -> np.ndarray:
    """標籤轉 0/1。不是二元就明說 —— 這是資料問題（1），不是用法錯誤（64）。"""
    if s.isna().any():
        raise ValueError(
            f"標籤欄 {col} 有 {int(s.isna().sum())} 個缺值。\n"
            f"  標籤缺值不可補值 —— make_label() 沒給出答案的列代表「這個人在標籤窗"
            f"裡根本沒有觀察機會」，應該整列剔除並在報告交代剔除筆數。")
    if pd.api.types.is_bool_dtype(s):
        return s.to_numpy().astype(int)
    vals = set(pd.unique(s.dropna()).tolist())
    if not vals <= {0, 1, 0.0, 1.0, True, False}:
        raise ValueError(
            f"標籤欄 {col} 不是二元（實際值：{sorted(vals, key=str)[:8]}）。\n"
            f"  本腳本的正例率統計假設 1 = 正類。多類別目標請先轉成 one-vs-rest，"
            f"或改用 --label-col 指向真正的二元標籤欄。")
    return s.to_numpy().astype(int)


def as_time(s: pd.Series, col: str) -> pd.Series:
    t = pd.to_datetime(s, errors="coerce")
    if t.isna().any():
        raise ValueError(
            f"時間欄 {col} 有 {int(t.isna().sum())} 個值轉不成日期。\n"
            f"  先修資料再切分 —— 轉不成日期的列會被 pandas 排到最後，"
            f"等於把它們塞進最晚的那一折，這本身就是洩漏。")
    return t


# ══════════════════════════════════════════════════════════════
#  三種切法（12 §二 列的三種，不多不少）
# ══════════════════════════════════════════════════════════════
def spacing_ratio(times: np.ndarray) -> float | None:
    """相鄰「唯一時點」間距的 max/min。用來判斷是不是等時距。

    12 §二：gap_rows 只有在每列等時距時才換算得回日曆天。交易明細那種
    每列時距不等的資料，TimeSeriesSplit(gap=) 擋不住洩漏。
    """
    uniq = np.unique(times)
    if uniq.size < 3:
        return None
    d = np.diff(uniq).astype("timedelta64[s]").astype(float)
    d = d[d > 0]
    if d.size == 0:
        return None
    return float(d.max() / d.min())


def make_folds(n_rows: int, method: str, y: np.ndarray,
               times: np.ndarray | None, groups: np.ndarray | None,
               n_splits: int, seed: int, gap_rows: int,
               test_rows: int | None, boundary: str
               ) -> tuple[list[tuple[np.ndarray, np.ndarray]], str]:
    """回傳 [(train_pos, valid_pos), …] 與實際採用的邊界模式。

    一律回**位置索引**（iloc），不回索引標籤 —— 建模表的 index 常常是
    非唯一的顧客編號，用標籤取值會悄悄多取到別人的列。
    """
    from sklearn.model_selection import (
        GroupKFold, StratifiedKFold, TimeSeriesSplit,
    )
    idx = np.arange(n_rows)

    if method == "stratified":
        # ① 目標與時間無關 → 隨機分層。stratify 是硬要求：
        #    不分層的話稀有正類可能整批落在同一邊（12 §二 判準表）
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return list(cv.split(idx.reshape(-1, 1), y)), "n/a"

    if method == "group":
        # ② 同一顧客多筆 → 依顧客分組，不按列切
        cv = GroupKFold(n_splits=n_splits)
        return list(cv.split(idx.reshape(-1, 1), y, groups=groups)), "n/a"

    # ③ 有時間結構 → rolling origin。切之前一定要先按時間排序。
    #    kind="stable"：同一時點的列維持原本的相對順序，重跑結果才可重現。
    order = np.argsort(times, kind="stable")
    ts_sorted = np.asarray(times)[order]
    n_uniq = int(np.unique(ts_sorted).size)

    if boundary == "auto":
        # 時間欄有重複值（面板資料的典型長相）→ 按列切必然把同一時點剖成兩半，
        # 訓練集與驗證集共用同一天。這種洩漏不會報錯，只會讓 AUC 變漂亮。
        boundary = "row" if n_uniq == n_rows else "time"

    cv = TimeSeriesSplit(n_splits=n_splits, gap=gap_rows, test_size=test_rows)
    folds: list[tuple[np.ndarray, np.ndarray]] = []
    if boundary == "row":
        for tr, te in cv.split(np.arange(n_rows)):
            folds.append((order[tr], order[te]))
    else:
        uniq, codes = np.unique(ts_sorted, return_inverse=True)
        for tr_t, te_t in cv.split(np.arange(uniq.size)):
            folds.append((order[np.isin(codes, tr_t)],
                          order[np.isin(codes, te_t)]))
    return folds, boundary


# ══════════════════════════════════════════════════════════════
#  逐折摘要 —— 關卡 2/3/4 的原料
# ══════════════════════════════════════════════════════════════
def summarize_folds(folds: list[tuple[np.ndarray, np.ndarray]],
                    y: np.ndarray, times: np.ndarray | None,
                    groups: np.ndarray | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fid, (tr, te) in enumerate(folds, start=1):
        n_tr, n_te = int(len(tr)), int(len(te))
        pos_tr, pos_te = int(y[tr].sum()), int(y[te].sum())
        r: dict[str, Any] = {
            "折": fid,
            "訓練列數": n_tr, "驗證列數": n_te,
            "訓練正例數": pos_tr, "驗證正例數": pos_te,
            "訓練正例率": round(pos_tr / n_tr, 6) if n_tr else None,
            "驗證正例率": round(pos_te / n_te, 6) if n_te else None,
        }
        if times is not None and n_tr and n_te:
            t_tr, t_te = np.asarray(times)[tr], np.asarray(times)[te]
            tr_max, te_min = t_tr.max(), t_te.min()
            r["訓練最早"] = pd.Timestamp(t_tr.min())
            r["訓練最晚"] = pd.Timestamp(tr_max)
            r["驗證最早"] = pd.Timestamp(te_min)
            r["驗證最晚"] = pd.Timestamp(t_te.max())
            r["間隔天數"] = round(
                (pd.Timestamp(te_min) - pd.Timestamp(tr_max)) / pd.Timedelta(days=1), 4)
            r["驗證跨度天數"] = round(
                (pd.Timestamp(t_te.max()) - pd.Timestamp(te_min)) / pd.Timedelta(days=1), 4)
            # 洩漏的規模，不只是有沒有：訓練集裡有幾列的時間 >= 驗證集起點。
            # 「有沒有」只給 0/1，這個數字才看得出是切點沒對齊還是整個排序壞掉。
            r["訓練集不早於驗證起點的列數"] = int((t_tr >= te_min).sum())
        if groups is not None and n_tr and n_te:
            g = np.asarray(groups)
            r["跨邊顧客數"] = int(len(set(g[tr].tolist()) & set(g[te].tolist())))
            r["驗證顧客數"] = int(len(set(g[te].tolist())))
        rows.append(r)
    return rows


# ══════════════════════════════════════════════════════════════
#  關卡 1：切法與資料結構是否相符（12 §二 判準表）
# ══════════════════════════════════════════════════════════════
def gate1_method(method: str, n_rows: int, n_groups: int | None,
                 has_time: bool, n_splits: int) -> dict[str, Any]:
    print("\n關卡 1／切法與資料結構相符（12 §二 判準表）")
    res: dict[str, Any] = {"關卡": 1, "名稱": "切法與資料結構相符",
                           "門檻": "12 §二 判準表", "數值": METHOD_NAMES[method]}
    verdicts: list[str] = []

    dup = n_groups is not None and n_rows > n_groups
    if n_groups is not None:
        detail(f"{n_rows:,} 列 / {n_groups:,} 位顧客 = 每人平均 {n_rows / n_groups:.2f} 列")
    else:
        warn("沒給 --group-col，「同一顧客多筆列」這道判準這次沒有驗到",
             "12 §二 說這是行銷資料**最常見的隱藏洩漏**。加 --group-col <顧客欄> 才驗得到；"
             "真的是一人一列也請明確給欄名，讓報告有這個數字")
        verdicts.append("warning")

    if dup and method == "stratified":
        err(f"同一顧客有多筆列（每人平均 {n_rows / n_groups:.2f} 列）卻用隨機分層切",
            "12 §二 判準表：同一顧客多筆列**必須** GroupKFold(groups=顧客欄)，不能按列切。"
            "隨機 8:2 之後幾乎每位顧客都同時出現在兩邊，模型只要記住『這個人的消費水位』"
            "就能拿高分，對新顧客零預測力。改 --method group --group-col <顧客欄>；"
            "若同時有時間結構，改 --method time 並看關卡 3 的跨邊顧客數")
        verdicts.append("error")
    elif dup and method == "time":
        info("同一顧客多筆列 + 時間結構 → 12 §二 要的是 GroupTimeSeriesSplit："
             "先按時間切，再檢查 group 不跨邊。本腳本以「時間切分 + 關卡 3 實際清點跨邊顧客」"
             "實作這件事，跨邊數字看關卡 3")

    if method == "stratified" and has_time:
        warn("目標若與時間有關（流失、下期購買、下季 CLV），隨機分層切就是洩漏",
             "12 §二 判準表：標籤定義裡含「未來 N 天」的一律**必須**時間切分。"
             "確認你的目標真的與時間無關（顧客屬性分類、商品歸類、評論情感）；"
             "只要含未來，改 --method time")
        verdicts.append("warning")

    if method == "time" and n_splits < MIN_TIME_FOLDS:
        warn(f"rolling origin 只切 {n_splits} 折（< {MIN_TIME_FOLDS}）",
             f"12 §二：資料期間 < 2 個完整週期時，單一測試切面只有一次觀測，"
             f"運氣成分太大 —— 至少 {MIN_TIME_FOLDS} 折，且報告要列每折分數與**全距**，"
             f"不能只報平均。加 --n-splits {MIN_TIME_FOLDS}")
        verdicts.append("warning")

    if "error" in verdicts:
        res["結果"] = "error"
    elif "warning" in verdicts:
        res["結果"] = "warning"
    else:
        ok(f"切法 {METHOD_NAMES[method]} 與資料結構相符")
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 2：未來洩漏（逐折）—— 本腳本的核心
# ══════════════════════════════════════════════════════════════
def gate2_no_future_leak(summary: list[dict[str, Any]], method: str,
                         has_time: bool, gap_days: int,
                         horizon_days: int | None,
                         boundary: str) -> dict[str, Any]:
    print("\n關卡 2／未來洩漏（12 §二；門檻 逐折 訓練最晚 < 驗證最早）")
    res: dict[str, Any] = {"關卡": 2, "名稱": "未來洩漏",
                           "門檻": "逐折 訓練最晚 < 驗證最早"}

    if not has_time:
        warn("沒給 --time-col，未來洩漏這道關這次沒有驗到",
             "12 §二 的 out-of-time 驗證是 M9 拿到「預測」證據等級的必要條件"
             "（00 §1.5）。就算目標與時間無關，也請給時間欄讓這個數字被算出來；"
             "真的沒有時間欄，報告要寫「本次切分未做時間洩漏驗證」")
        res.update({"數值": None, "結果": "warning", "依據": "無時間欄 —— 未實際驗證"})
        return res

    # 為什麼逐折比：rolling origin 的折 4 訓練集本來就晚於折 1 的驗證集，
    # 拿 全域train_max 比 全域valid_min，正確的 pipeline 也一定被判成洩漏
    # （12 §二 明寫這一條）。每一折只跟自己比。
    inverted = [r for r in summary if r.get("間隔天數") is not None and r["間隔天數"] < 0]
    touching = [r for r in summary if r.get("間隔天數") is not None and r["間隔天數"] == 0]
    gaps = [r["間隔天數"] for r in summary if r.get("間隔天數") is not None]
    res["數值"] = round(min(gaps), 4) if gaps else None

    for r in summary:
        if r.get("間隔天數") is None:
            continue
        detail(f"折 {r['折']}：訓練 {r['訓練最早'].date()}→{r['訓練最晚'].date()}"
               f"｜驗證 {r['驗證最早'].date()}→{r['驗證最晚'].date()}"
               f"｜間隔 {r['間隔天數']:+.2f} 天"
               f"｜訓練集不早於驗證起點的列數 {r['訓練集不早於驗證起點的列數']:,}")

    if method != "time":
        # 隨機分層／分組切在有時間欄的資料上必然交錯。這不是 bug，是切法的定義；
        # 但它是否可接受完全取決於「目標與時間有沒有關」，機器判不出來。
        n_bad = len(inverted) + len(touching)
        if n_bad:
            worst = min(gaps)
            warn(f"{n_bad}/{len(summary)} 折的訓練集含有不早於驗證集起點的資料"
                 f"（最差間隔 {worst:+.2f} 天）—— {METHOD_NAMES[method]} 必然如此",
                 "12 §二 判準表：只有「目標與時間無關」時這才可以接受。"
                 "標籤裡只要含「未來 N 天」（流失、下期購買、CLV），這就是 18-G4，"
                 "驗證 AUC 會系統性樂觀、上線崩盤。改 --method time")
            res["結果"] = "warning"
        else:
            ok("逐折皆無時間交錯")
            res["結果"] = "pass"
        return res

    if inverted:
        ids = "、".join(f"折 {r['折']}(間隔 {r['間隔天數']:+.2f} 天，"
                       f"{r['訓練集不早於驗證起點的列數']:,} 列)" for r in inverted)
        err(f"{len(inverted)} 折的訓練集有比驗證集更晚的資料：{ids}",
            "這是 18-G4 未來洩漏。先確認建模表真的按時間欄排序、"
            "時間欄沒有轉不成日期的髒值、也沒有把 as_of 與交易日搞混。"
            "修好之前這組切分不可拿去訓練")
        res["結果"] = "error"
        return res

    if touching:
        ids = "、".join(f"折 {r['折']}" for r in touching)
        err(f"{len(touching)} 折的切點落在同一時點內部（間隔 0 天）：{ids}",
            "同一個 as_of 的列被從中間剖開，訓練集與驗證集共用同一天 —— "
            "排序沒錯、程式不報錯，但驗證分數已經樂觀了。"
            "改 --boundary time（切點對齊時點邊界），或確認建模表是不是一列一時點")
        res["結果"] = "error"
        return res

    # 到這裡順序是對的，接著問 gap 夠不夠。
    # 12 §二：該折的 label_window_start = as_of + gap_days。訓練集最後一個 as_of
    # 的標籤窗會延伸到 as_of + gap_days + horizon_days，若驗證集的第一個 as_of
    # 早於那個時點，訓練標籤期與驗證特徵期重疊 —— 這是 rolling origin 的 embargo。
    need = gap_days + (horizon_days or 0)
    thin = [r for r in summary if r["間隔天數"] < need]
    if thin and need > 0:
        ids = "、".join(f"折 {r['折']}(間隔 {r['間隔天數']:.2f} 天)" for r in thin)
        warn(f"{len(thin)} 折的折間間隔 < gap_days({gap_days}) + horizon_days"
             f"({horizon_days or 0}) = {need} 天：{ids}",
             "訓練折最後一個 as_of 的標籤窗延伸到驗證折的特徵窗裡了。"
             "加大 --test-rows 讓每折驗證期拉長，或減少 --n-splits，"
             "或在切分後把落在緩衝區內的驗證列剔除（embargo）並在報告記錄剔除筆數")
        res["結果"] = "warning"
    else:
        ok(f"逐折 訓練最晚 < 驗證最早，最小間隔 {min(gaps):.2f} 天"
           + (f" ≥ gap+horizon = {need} 天" if need > 0 else ""))
        res["結果"] = "pass"

    # 季節性：機器判不出有沒有季節性，但可以把數字擺出來讓人判
    spans = [r["驗證跨度天數"] for r in summary if r.get("驗證跨度天數") is not None]
    if spans:
        total_span = ((summary[-1]["驗證最晚"] - summary[0]["訓練最早"])
                      / pd.Timedelta(days=1))
        if total_span >= SEASON_CYCLE_DAYS and max(spans) < SEASON_CYCLE_DAYS:
            info(f"最長的驗證期只有 {max(spans):.0f} 天（資料總期間 {total_span:.0f} 天）。"
                 f"12 §二：有明顯季節性（檔期、換季、年節）時，測試集長度應 ≥ 一個完整"
                 f"週期（多數零售 = {SEASON_CYCLE_DAYS} 天）。只用淡季當測試集，雙十一就失效")
    res["邊界模式"] = boundary
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 3：顧客跨邊（分組洩漏）
# ══════════════════════════════════════════════════════════════
def gate3_group_leak(summary: list[dict[str, Any]], method: str,
                     has_group: bool) -> dict[str, Any]:
    print("\n關卡 3／顧客跨邊（12 §二「行銷資料最常見的隱藏洩漏」；門檻 跨邊 = 0）")
    res: dict[str, Any] = {"關卡": 3, "名稱": "顧客跨邊", "門檻": "跨邊顧客數 = 0"}

    if not has_group:
        warn("沒給 --group-col，顧客跨邊這道關這次沒有驗到",
             "加 --group-col <顧客欄>。實務徵狀：加入顧客層彙總特徵後 AUC 跳升 0.05 以上，"
             "且 SHAP 前三名全是顧客層均值類特徵 —— 這時先懷疑切分，不要先高興（12 §二）")
        res.update({"數值": None, "結果": "warning", "依據": "無顧客欄 —— 未實際驗證"})
        return res

    crossed = [r for r in summary if r.get("跨邊顧客數", 0) > 0]
    counts = [r.get("跨邊顧客數", 0) for r in summary]
    res["數值"] = int(max(counts)) if counts else None
    for r in summary:
        if "跨邊顧客數" in r:
            pct = (r["跨邊顧客數"] / r["驗證顧客數"] * 100) if r["驗證顧客數"] else 0.0
            detail(f"折 {r['折']}：跨邊 {r['跨邊顧客數']:,} 位 / "
                   f"驗證集 {r['驗證顧客數']:,} 位（{pct:.1f}%）")

    if not crossed:
        ok("逐折皆無顧客同時出現在訓練與驗證")
        res["結果"] = "pass"
    elif method == "group":
        # GroupKFold 保證不跨邊。真的跨了就是 groups 傳錯欄，不是資料問題
        err(f"用了 GroupKFold 卻仍有 {max(counts):,} 位顧客跨邊",
            "GroupKFold 保證不跨邊 —— 跨了代表 --group-col 指到的不是真正的顧客欄，"
            "或同一顧客在不同列有不同寫法（全形半形、前後空白、大小寫）。"
            "先做顧客編號正規化再切")
        res["結果"] = "error"
    elif method == "time":
        worst = max(counts)
        warn(f"最多有 {worst:,} 位顧客同時出現在訓練與驗證集",
             "12 §二：先按時間切，再檢查 group 不跨邊。時間切分下跨邊是常態"
             "（老顧客本來就橫跨整段期間），但模型可能只是在記人。處置二選一："
             "① 報告寫明跨邊比例，並額外報一個「只含新顧客的驗證子集」分數；"
             "② 把跨邊顧客整批移出驗證集再評估。兩者都要記錄")
        res["結果"] = "warning"
    else:
        # method == "stratified"：關卡 1 已經以 error 擋下，這裡只把規模量出來
        worst = max(counts)
        warn(f"最多有 {worst:,} 位顧客同時出現在訓練與驗證集"
             f"（隨機分層按列切必然如此）",
             "這就是關卡 1 說的那件事的實際規模。改 --method group "
             "（純分組）或 --method time（有時間結構時），不要在這裡想辦法補救")
        res["結果"] = "warning"
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 4：各段樣本數與正例率
# ══════════════════════════════════════════════════════════════
def gate4_positives(summary: list[dict[str, Any]], total_pos: int,
                    n_rows: int) -> dict[str, Any]:
    print(f"\n關卡 4／各段樣本數與正例率（12 §九；門檻 每折驗證正例 > 0、"
          f"總正例 ≥ {MIN_POSITIVE_TOTAL}）")
    res: dict[str, Any] = {"關卡": 4, "名稱": "各段樣本數與正例率",
                           "門檻": f"每折驗證正例 > 0；總正例 ≥ {MIN_POSITIVE_TOTAL}",
                           "數值": int(total_pos)}
    verdicts: list[str] = []

    for r in summary:
        detail(f"折 {r['折']}：訓練 {r['訓練列數']:,} 列／正例 {r['訓練正例數']:,}"
               f"（{(r['訓練正例率'] or 0) * 100:.2f}%）｜"
               f"驗證 {r['驗證列數']:,} 列／正例 {r['驗證正例數']:,}"
               f"（{(r['驗證正例率'] or 0) * 100:.2f}%）")

    info(f"全表 {n_rows:,} 列、正例 {total_pos:,} 筆（{total_pos / n_rows * 100:.2f}%）")

    # 正例 = 0 是靜默失敗：AUC/AP 在只有一類的驗證集上算不出來（sklearn 直接丟例外
    # 或回 nan），但很多 pipeline 會把 nan 當 0 平均掉，最後只看到一個偏低的平均分數。
    empty_valid = [r for r in summary if r["驗證正例數"] == 0]
    empty_train = [r for r in summary if r["訓練正例數"] == 0]
    if empty_valid:
        ids = "、".join(f"折 {r['折']}" for r in empty_valid)
        err(f"{len(empty_valid)} 折的**驗證集完全沒有正例**：{ids}",
            "AUC／AP 在單一類別的驗證集上算不出來，很多 pipeline 會把 nan 靜默平均掉。"
            "處置：減少 --n-splits、加大 --test-rows，或回頭改標籤定義"
            "（拉長 horizon_days、換事件），必要時回 M0 與包子確認目標")
        verdicts.append("error")
    if empty_train:
        ids = "、".join(f"折 {r['折']}" for r in empty_train)
        err(f"{len(empty_train)} 折的**訓練集完全沒有正例**：{ids}",
            "模型學不到任何正類，predict_proba 會退化成常數。"
            "同上：減少折數、加大訓練期，或改標籤定義")
        verdicts.append("error")

    if total_pos == 0:
        err("整份建模表一個正例都沒有",
            "標籤全 0 —— 通常是 make_label() 的窗口設錯（as_of + gap 已經超出資料期間），"
            "或 --label-col 指錯欄。先查標籤產生程式")
        verdicts.append("error")
    elif total_pos < MIN_POSITIVE_TOTAL:
        warn(f"總正例只有 {total_pos:,} 筆 < {MIN_POSITIVE_TOTAL}",
             f"12 §九：正類 < {MIN_POSITIVE_TOTAL} 筆 → **不建模**，改用業務規則 + 敘述統計，"
             f"並在報告說明需要多少筆才值得建模。硬跑出來的模型不會有 out-of-time 穩定性")
        verdicts.append("warning")

    rates = [r["驗證正例率"] for r in summary
             if r["驗證正例率"] is not None and r["驗證正例率"] > 0]
    if len(rates) >= 2:
        rng = max(rates) - min(rates)
        ratio = max(rates) / min(rates)
        info(f"折間驗證正例率全距 {rng * 100:.2f} 個百分點"
             f"（{min(rates) * 100:.2f}% – {max(rates) * 100:.2f}%），比值 {ratio:.2f}")
        res["折間正例率比值"] = round(ratio, 3)
        if ratio >= POS_RATE_RATIO_MAX:
            warn(f"折間驗證正例率相差 {ratio:.2f} 倍",
                 "時間切分下這代表**標籤的基準率隨時間漂移**（促銷檔期、政策改變、"
                 "疫情這類外生衝擊）。處置：① 報告逐折列出正例率，不要只報平均分數；"
                 "② 檢查是不是某一折剛好落在檔期上；③ 若漂移是真的，模型上線後"
                 "要按 12 §十 的漂移監控重訓。這個 2 倍門檻是本腳本自訂，"
                 "reference 未給數字，請按你的業務週期調整")
            verdicts.append("warning")
    elif len(rates) < len([r for r in summary if r["驗證正例率"] is not None]):
        pass  # 有折的正例率為 0，上面已經以 error 處理

    if "error" in verdicts:
        res["結果"] = "error"
    elif "warning" in verdicts:
        res["結果"] = "warning"
    else:
        ok(f"每折訓練與驗證都有正例，總正例 {total_pos:,} 筆 ≥ {MIN_POSITIVE_TOTAL}")
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 5：gap 與入庫延遲（12 §二 的 assert）
# ══════════════════════════════════════════════════════════════
def gate5_gap(method: str, gap_days: int, max_ingest_lag_days: int | None,
              gap_rows: int, spacing: float | None) -> dict[str, Any]:
    print("\n關卡 5／gap 與入庫延遲（12 §二；門檻 gap_days ≥ 最長入庫延遲）")
    res: dict[str, Any] = {"關卡": 5, "名稱": "gap 與入庫延遲",
                           "門檻": "gap_days ≥ max_ingest_lag_days",
                           "數值": int(gap_days)}
    verdicts: list[str] = []

    if method != "time":
        info(f"切法為 {METHOD_NAMES[method]}，標籤沒有「未來 N 天」的窗口，"
             f"gap 不適用 —— 這道關本次不判定")
        res.update({"結果": "pass", "依據": "非時間切分，不適用"})
        return res

    if gap_days == 0:
        # 12 §二 原話：gap_days=0 就是沒有 gap，等於沒防
        warn("gap_days = 0",
             "12 §二：gap_days=0 就是沒有 gap，等於沒防。沒有 gap 時，標籤期第一天的"
             "交易可能已經被算進特徵（「最近 7 天消費金額」這種滾動特徵最容易中），"
             "這是最隱蔽的洩漏形態。確認 make_label() 的 gap_days，再用 --gap-days 傳進來")
        verdicts.append("warning")

    if max_ingest_lag_days is None:
        warn("沒給 --max-ingest-lag-days，「gap 夠不夠」這道關這次沒有驗到",
             "12 §二：gap 長度 ≥ 資料入庫延遲，取最長的那一個"
             "（POS T+1／廣告平台回填 T+3／退貨認列 T+30 → 取 30）。"
             "問清楚你這批資料的最長延遲再用 --max-ingest-lag-days 傳進來")
        verdicts.append("warning")
    elif gap_days < max_ingest_lag_days:
        err(f"gap_days = {gap_days} < 最長入庫延遲 {max_ingest_lag_days} 天",
            f"12 §二 的硬條件：gap 必須 ≥ 最長的資料入庫延遲。"
            f"目前 gap 只有 {gap_days} 天，標籤窗前 {max_ingest_lag_days - gap_days} 天的"
            f"資料在 as_of 當下根本還沒進倉 —— 上線時拿不到，離線卻拿得到，"
            f"這就是 18-G4。回頭把 make_label(gap_days={max_ingest_lag_days}) 重跑，"
            f"重建建模表再切")
        verdicts.append("error")
    else:
        ok(f"gap_days = {gap_days} ≥ 最長入庫延遲 {max_ingest_lag_days} 天")

    if gap_rows > 0:
        if spacing is None:
            info(f"--gap-rows = {gap_rows}：唯一時點不足 3 個，等時距與否判不出來")
        elif spacing > EQUAL_SPACING_RATIO_MAX:
            warn(f"--gap-rows = {gap_rows} 但資料**不等時距**"
                 f"（相鄰時點間距 max/min = {spacing:.2f}）",
                 "12 §二：gap_rows 的單位是列數，只有每列等時距時才換算得回日曆天。"
                 "交易明細那種每列時距不等的資料，TimeSeriesSplit(gap=) 擋不住洩漏，"
                 "唯一的防線是 make_label(gap_days=)。把 --gap-rows 歸零，"
                 "改在標籤產生階段留 gap。（1.5 倍這個判定門檻是本腳本自訂）")
            verdicts.append("warning")
        else:
            ok(f"--gap-rows = {gap_rows} 且資料近似等時距"
               f"（間距 max/min = {spacing:.2f} ≤ {EQUAL_SPACING_RATIO_MAX}），"
               f"列數可換算回日曆天")

    if "error" in verdicts:
        res["結果"] = "error"
    elif "warning" in verdicts:
        res["結果"] = "warning"
    else:
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    df, tpath = load_table(p, args.table)

    for col, flag in ((args.label_col, "--label-col"), (args.time_col, "--time-col"),
                      (args.group_col, "--group-col")):
        if col and col not in df.columns:
            raise ValueError(
                f"{flag} 指定的欄位 {col} 不在建模表裡。"
                f"現有欄位：{'、'.join(map(str, df.columns[:20]))}"
                f"{' …' if len(df.columns) > 20 else ''}")

    y = as_binary_label(df[args.label_col], args.label_col)
    times = as_time(df[args.time_col], args.time_col).to_numpy() if args.time_col else None
    groups = df[args.group_col].to_numpy() if args.group_col else None
    n_rows = len(df)
    n_splits = args.n_splits or FOLD_DEFAULTS[args.method]

    if n_rows < n_splits * 2:
        raise ValueError(
            f"只有 {n_rows} 列，切 {n_splits} 折每折不到 2 列。"
            f"減少 --n-splits，或先確認建模表是不是讀錯檔。")

    folds, boundary = make_folds(
        n_rows, args.method, y, times, groups, n_splits, args.seed,
        args.gap_rows, args.test_rows, args.boundary)
    summary = summarize_folds(folds, y, times, groups)
    spacing = spacing_ratio(times) if times is not None else None
    n_groups = int(pd.Series(groups).nunique()) if groups is not None else None
    total_pos = int(y.sum())

    print("=" * 72)
    print("行銷數據分析 Skill — 時間切分驗證（12 §二）")
    print(f"專案：{args.project}｜建模表：{tpath.name}"
          f"（{n_rows:,} 列 × {len(df.columns)} 欄）")
    print(f"切法：{METHOD_NAMES[args.method]}，{n_splits} 折"
          + (f"，邊界模式 {boundary}" if args.method == "time" else ""))
    print(f"標籤：{args.label_col}（正例 {total_pos:,} 筆，{total_pos / n_rows * 100:.2f}%）")
    print(f"時間欄：{args.time_col or '（未給）'}｜顧客欄：{args.group_col or '（未給）'}")
    if args.method == "time":
        print(f"gap_days={args.gap_days}｜horizon_days={args.horizon_days or '（未給）'}"
              f"｜max_ingest_lag_days={args.max_ingest_lag_days or '（未給）'}"
              f"｜gap_rows={args.gap_rows}")
        if boundary == "time":
            print("      · 邊界模式 time：--gap-rows／--test-rows 的單位是**時點數**，"
                  "不是列數")
    print("=" * 72)

    results = [
        gate1_method(args.method, n_rows, n_groups, times is not None, n_splits),
        gate2_no_future_leak(summary, args.method, times is not None,
                             args.gap_days, args.horizon_days, boundary),
        gate3_group_leak(summary, args.method, groups is not None),
        gate4_positives(summary, total_pos, n_rows),
        gate5_gap(args.method, args.gap_days, args.max_ingest_lag_days,
                  args.gap_rows, spacing),
    ]

    n_err = sum(1 for r in results if r["結果"] == "error")
    n_warn = sum(1 for r in results if r["結果"] == "warning")
    n_pass = sum(1 for r in results if r["結果"] == "pass")

    print("\n" + "=" * 72)
    print(f"五道關｜通過 {n_pass}、warning {n_warn}、error {n_err}")
    if n_err:
        print(f"結果：⛔ 有 {n_err} 道關 error → 這組切分不可拿去訓練。")
    elif n_warn:
        print(f"結果：⚠ 有 {n_warn} 道關 warning → 可往下，但報告要逐條寫明處置。")
    else:
        print("結果：✅ 五道關全過。")

    if not args.no_write:
        tdir = p.tables / "預測模型"
        tdir.mkdir(parents=True, exist_ok=True)
        sm = pd.DataFrame(summary)
        sp = tdir / "切分_逐折摘要.csv"
        sm.to_csv(sp, index=False, encoding="utf-8-sig")
        print(f"\n✓ 逐折摘要：{sp}")

        gp = tdir / "切分_五道關.csv"
        pd.DataFrame(results).to_csv(gp, index=False, encoding="utf-8-sig")
        print(f"✓ 五道關結果：{gp}")

        p.models.mkdir(parents=True, exist_ok=True)
        assign = pd.DataFrame(
            [{"列位置": int(i), "折": fid, "段別": seg}
             for fid, (tr, te) in enumerate(folds, start=1)
             for seg, arr in (("train", tr), ("valid", te))
             for i in arr.tolist()])
        ap_ = p.models / "split_folds.parquet"
        try:
            assign.to_parquet(ap_, index=False)
        except (ImportError, ValueError) as e:  # 沒有 pyarrow 就退 CSV，不要整支掛掉
            ap_ = p.models / "split_folds.csv"
            assign.to_csv(ap_, index=False, encoding="utf-8-sig")
            info(f"parquet 寫不出來（{type(e).__name__}），已改存 CSV")
        print(f"✓ 逐列折別指派：{ap_}")

        jp = p.models / "split_time.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "table": str(tpath),
            "n_rows": n_rows,
            "method": args.method,
            "method_name": METHOD_NAMES[args.method],
            "n_splits": n_splits,
            "seed": args.seed,
            "boundary": boundary,
            "label_col": args.label_col,
            "time_col": args.time_col,
            "group_col": args.group_col,
            "n_groups": n_groups,
            "total_positive": total_pos,
            "gap_days": args.gap_days,
            "horizon_days": args.horizon_days,
            "max_ingest_lag_days": args.max_ingest_lag_days,
            "gap_rows": args.gap_rows,
            "test_rows": args.test_rows,
            "time_spacing_ratio": spacing,
            "folds": summary,
            "gates": results,
            "errors": _errors,
            "warnings": _warnings,
            "infos": _infos,
        }, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        print(f"✓ 機器可讀結果：{jp}")

    if n_err:
        return EX_ERROR
    if n_warn:
        return EX_WARN
    return EX_OK


# ══════════════════════════════════════════════════════════════
#  自我測試
# ══════════════════════════════════════════════════════════════
def _panel(n_cust: int, n_period: int, pos_rate: float = 0.15,
           seed: int = 20260728) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """一顧客一月一列的面板。回 (y, times, groups)。

    這是 M9 建模表的典型長相：同一個 as_of 有 n_cust 列，同一位顧客橫跨全期。
    """
    rng = np.random.default_rng(seed)
    periods = pd.date_range("2025-01-31", periods=n_period, freq="ME").to_numpy()
    times = np.repeat(periods, n_cust)
    groups = np.tile(np.arange(n_cust), n_period)
    y = (rng.random(n_cust * n_period) < pos_rate).astype(int)
    return y, times, groups


def _selftest() -> int:  # noqa: C901 - 逐項列出比抽象化好讀
    print("=" * 72)
    print("split_time.py 自我測試")
    print("=" * 72)
    failed: list[str] = []

    def check(name: str, cond: bool, got: str = "") -> None:
        if cond:
            print(f"  ✓ {name}" + (f"（{got}）" if got else ""))
        else:
            print(f"  ✗ {name}" + (f"（{got}）" if got else ""))
            failed.append(name)

    # ── 假資料：120 位顧客 × 12 個月 = 1,440 列的面板 ──────────
    y, times, groups = _panel(120, 12, pos_rate=0.15)
    n = len(y)

    # ① 時間切分（時點邊界）→ 逐折無洩漏，關卡 2 必須 pass（不該亂叫）
    f_t, b_t = make_folds(n, "time", y, times, groups, 4, 42, 0, None, "auto")
    s_t = summarize_folds(f_t, y, times, groups)
    check("面板資料自動選到時點邊界模式", b_t == "time", f"boundary={b_t}")
    r2 = gate2_no_future_leak(s_t, "time", True, 0, None, b_t)
    check("① 正確的時間切分 → 關卡 2 不誤報洩漏", r2["結果"] == "pass",
          f"最小間隔 {r2['數值']} 天")
    check("① rolling origin：訓練集逐折變大",
          all(s_t[i]["訓練列數"] < s_t[i + 1]["訓練列數"] for i in range(len(s_t) - 1)),
          "、".join(str(r["訓練列數"]) for r in s_t))

    # ② 全域 max/min 比會誤判、逐折比不會（12 §二 明寫的陷阱）
    global_train_max = max(r["訓練最晚"] for r in s_t)
    global_valid_min = min(r["驗證最早"] for r in s_t)
    check("② 全域比在合法的 rolling origin 上會誤判成洩漏（所以不能用全域比）",
          global_train_max > global_valid_min,
          f"全域訓練最晚 {pd.Timestamp(global_train_max).date()} > "
          f"全域驗證最早 {pd.Timestamp(global_valid_min).date()}")
    check("② 同一組折用逐折比則判無洩漏", r2["結果"] == "pass")

    # ③ 真洩漏：把未來的列硬塞進訓練集 → 關卡 2 必須抓到
    # 把「最後一個時點」的列硬塞進每一折的訓練集 —— 這就是沒排序的典型後果
    leaky = [(np.concatenate([tr, np.arange(n - 20, n)]), te) for tr, te in f_t]
    s_leak = summarize_folds(leaky, y, times, groups)
    r2l = gate2_no_future_leak(s_leak, "time", True, 0, None, b_t)
    check("③ 訓練集混入未來的列 → 關卡 2 判 error", r2l["結果"] == "error",
          f"最小間隔 {r2l['數值']} 天")
    check("③ 洩漏規模有被量出來（不只是 0/1）",
          all(r["訓練集不早於驗證起點的列數"] > 0 for r in s_leak),
          "、".join(str(r["訓練集不早於驗證起點的列數"]) for r in s_leak))

    # ④ 切點落在同一時點內部（面板用列邊界切）→ 間隔 0 天，必須判 error
    f_row, b_row = make_folds(n, "time", y, times, groups, 4, 42, 0, None, "row")
    s_row = summarize_folds(f_row, y, times, groups)
    r2r = gate2_no_future_leak(s_row, "time", True, 0, None, b_row)
    check("④ 面板按列切 → 切點剖開同一時點，關卡 2 判 error",
          r2r["結果"] == "error" and any(r["間隔天數"] == 0 for r in s_row),
          "間隔天數 " + "、".join(f"{r['間隔天數']:.0f}" for r in s_row))

    # ⑤ 交易明細（每列唯一時點）用列邊界切 → 不該誤判
    rng = np.random.default_rng(7)
    t_txn = np.sort(np.datetime64("2025-01-01") +
                    rng.choice(np.arange(400 * 24), size=1200, replace=False)
                    .astype("timedelta64[h]"))
    y_txn = (rng.random(1200) < 0.2).astype(int)
    f_x, b_x = make_folds(1200, "time", y_txn, t_txn, None, 4, 42, 0, None, "auto")
    s_x = summarize_folds(f_x, y_txn, t_txn, None)
    r2x = gate2_no_future_leak(s_x, "time", True, 0, None, b_x)
    check("⑤ 每列唯一時點 → 自動選列邊界且不誤報",
          b_x == "row" and r2x["結果"] == "pass", f"boundary={b_x}")

    # ⑥ 隨機分層切在有時間欄的資料上 → 關卡 2 必須出聲（warning）
    f_s, _ = make_folds(n, "stratified", y, times, groups, 5, 42, 0, None, "auto")
    s_s = summarize_folds(f_s, y, times, groups)
    r2s = gate2_no_future_leak(s_s, "stratified", True, 0, None, "n/a")
    check("⑥ 隨機分層 + 有時間欄 → 關卡 2 判 warning", r2s["結果"] == "warning",
          f"最差間隔 {r2s['數值']} 天")

    # ⑦ 判準表：顧客重複卻用隨機分層 → 關卡 1 必須 error；用 group 則不叫
    r1a = gate1_method("stratified", n, 120, True, 5)
    check("⑦ 顧客重複 + 隨機分層 → 關卡 1 判 error", r1a["結果"] == "error")
    r1b = gate1_method("group", n, 120, True, 5)
    check("⑦ 顧客重複 + GroupKFold → 關卡 1 不誤判", r1b["結果"] == "pass",
          f"結果={r1b['結果']}")
    r1c = gate1_method("time", 1200, 1200, True, 2)
    check("⑦ rolling origin 只切 2 折 → 關卡 1 判 warning（12 §二 至少 3 折）",
          r1c["結果"] == "warning")

    # ⑧ 分組洩漏：GroupKFold 後跨邊 = 0；time 切法下跨邊會被點名
    f_g, _ = make_folds(n, "group", y, times, groups, 5, 42, 0, None, "auto")
    s_g = summarize_folds(f_g, y, times, groups)
    r3g = gate3_group_leak(s_g, "group", True)
    check("⑧ GroupKFold → 關卡 3 跨邊 0（不誤報）",
          r3g["結果"] == "pass" and r3g["數值"] == 0, f"最大跨邊 {r3g['數值']}")
    r3t = gate3_group_leak(s_t, "time", True)
    check("⑧ 時間切分下老顧客跨邊 → 關卡 3 判 warning 並報出人數",
          r3t["結果"] == "warning" and r3t["數值"] > 0, f"最大跨邊 {r3t['數值']} 位")
    r3n = gate3_group_leak(s_x, "time", False)
    check("⑧ 沒給顧客欄 → 關卡 3 誠實說「沒驗到」而不是 pass",
          r3n["結果"] == "warning" and r3n["數值"] is None)

    # ⑨ 正例率：某折驗證集沒有正例 → 關卡 4 必須 error
    y_early = np.zeros(n, dtype=int)
    y_early[:300] = 1                      # 正例全擠在最早的三個月
    s_e = summarize_folds(f_t, y_early, times, groups)
    r4e = gate4_positives(s_e, int(y_early.sum()), n)
    check("⑨ 某折驗證集沒有正例 → 關卡 4 判 error", r4e["結果"] == "error",
          "驗證正例數 " + "、".join(str(r["驗證正例數"]) for r in s_e))

    # ⑩ 正例率：正常分布 → 關卡 4 必須 pass（不該亂叫）
    r4ok = gate4_positives(s_t, int(y.sum()), n)
    check("⑩ 正例分布正常 → 關卡 4 不誤報", r4ok["結果"] == "pass",
          f"總正例 {r4ok['數值']}")

    # ⑪ 正例率：總正例 < 200 → warning（12 §九）
    y_rare = np.zeros(n, dtype=int)
    y_rare[::20] = 1                       # 72 筆，各折都有，但總數不足
    s_r = summarize_folds(f_t, y_rare, times, groups)
    r4r = gate4_positives(s_r, int(y_rare.sum()), n)
    check("⑪ 總正例 72 < 200 → 關卡 4 判 warning（12 §九）",
          r4r["結果"] == "warning", f"總正例 {r4r['數值']}")

    # ⑫ 正例率：折間基準率漂移 → warning
    y_drift = np.zeros(n, dtype=int)
    per = 120
    for k in range(12):
        take = int(per * (0.03 + 0.04 * k))          # 3% 一路漂到 47%
        y_drift[k * per: k * per + take] = 1
    s_d = summarize_folds(f_t, y_drift, times, groups)
    r4d = gate4_positives(s_d, int(y_drift.sum()), n)
    check("⑫ 折間正例率漂移 2 倍以上 → 關卡 4 判 warning",
          r4d["結果"] == "warning" and r4d.get("折間正例率比值", 0) >= POS_RATE_RATIO_MAX,
          f"比值 {r4d.get('折間正例率比值')}")

    # ⑬ gap：gap_days < 入庫延遲 → error；≥ 則不叫
    r5a = gate5_gap("time", 1, 30, 0, 1.0)
    check("⑬ gap_days 1 < 入庫延遲 30 → 關卡 5 判 error", r5a["結果"] == "error")
    r5b = gate5_gap("time", 30, 30, 0, 1.0)
    check("⑬ gap_days 30 ≥ 入庫延遲 30 → 關卡 5 不誤報", r5b["結果"] == "pass",
          f"結果={r5b['結果']}")
    r5c = gate5_gap("time", 0, None, 0, 1.0)
    check("⑬ gap_days=0 且沒給入庫延遲 → 關卡 5 判 warning（不准 pass）",
          r5c["結果"] == "warning")

    # ⑭ gap_rows 的單位陷阱：不等時距時要出聲
    sp_panel = spacing_ratio(times)
    sp_txn = spacing_ratio(t_txn)
    check("⑭ 等時距面板的間距比接近 1",
          sp_panel is not None and sp_panel <= EQUAL_SPACING_RATIO_MAX,
          f"max/min = {sp_panel:.2f}")
    check("⑭ 交易明細不等時距",
          sp_txn is not None and sp_txn > EQUAL_SPACING_RATIO_MAX,
          f"max/min = {sp_txn:.2f}")
    r5d = gate5_gap("time", 30, 30, 5, sp_txn)
    check("⑭ 不等時距卻用 --gap-rows → 關卡 5 判 warning", r5d["結果"] == "warning")

    # ⑮ 標籤欄檢查
    try:
        as_binary_label(pd.Series([0, 1, 2, 1]), "y")
        multi_ok = False
    except ValueError:
        multi_ok = True
    check("⑮ 多類別標籤被擋下", multi_ok)
    check("⑮ 布林標籤轉得動",
          as_binary_label(pd.Series([True, False, True]), "y").tolist() == [1, 0, 1])

    # ⑯ 參數值檢查（→64 的那一層）
    bad = validate_values("time", 1, -1, 0, -5, -1, 0, None, None)
    check("⑯ 不合法參數在 argparse 層就被列舉出來（→64）", len(bad) >= 5,
          f"{len(bad)} 條：{bad[0]}")
    good = validate_values("time", 4, 30, 90, 30, 0, None, "as_of", "客戶編號")
    check("⑯ 合法參數不誤報", good == [], f"{good}")
    check("⑯ --method time 缺 --time-col 會被擋",
          any("--time-col" in m for m in validate_values(
              "time", 4, 0, None, None, 0, None, None, "cid")))

    # ⑰ 結果必須 JSON 序列化得出來。
    #    折編號、樣本數都是從 numpy 陣列出來的 int64，Timestamp 也不是 JSON 原生型別；
    #    早期版本會在五道關全跑完、CSV 都寫好之後才丟 TypeError，退出碼 70
    #    蓋掉前面全綠的結論。這一項直接驗序列化。
    try:
        json.dumps({"folds": s_t, "gates": [r1b, r2, r3t, r4ok, r5b]},
                   ensure_ascii=False, default=_json_default)
        ser_ok, ser_msg = True, "含 Timestamp 與 numpy 純量仍可序列化"
    except TypeError as e:
        ser_ok, ser_msg = False, str(e)
    check("⑰ 逐折摘要與五道關可寫成 JSON", ser_ok, ser_msg)
    check("⑰ 折編號與樣本數是原生 int",
          all(type(r["折"]) is int and type(r["訓練列數"]) is int for r in s_t))

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="時間切分驗證（12 §二）：三種切法 + 五道洩漏關卡。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--method", choices=tuple(FOLD_DEFAULTS),
                    help="切法。time=rolling origin｜group=依顧客分組｜stratified=隨機分層")
    ap.add_argument("--table", type=Path,
                    help="建模表（預設 分析資料表/model_table.parquet）")
    ap.add_argument("--label-col", help="二元標籤欄（1 = 正類）")
    ap.add_argument("--time-col", help="時間欄（as_of／觀測時點）。--method time 必填")
    ap.add_argument("--group-col", help="顧客欄。--method group 必填；其餘切法強烈建議給")
    ap.add_argument("--n-splits", type=int,
                    help=f"折數（預設：{'／'.join(f'{k}={v}' for k, v in FOLD_DEFAULTS.items())}）")
    ap.add_argument("--gap-days", type=int, default=0,
                    help="make_label(gap_days=) 用的**日曆天**。0 = 沒有 gap，等於沒防")
    ap.add_argument("--horizon-days", type=int,
                    help="make_label(horizon_days=) 標籤窗長度（日曆天）")
    ap.add_argument("--max-ingest-lag-days", type=int,
                    help="最長資料入庫延遲（POS T+1／廣告 T+3／退貨 T+30 取最長）")
    ap.add_argument("--gap-rows", type=int, default=0,
                    help="TimeSeriesSplit(gap=) 的**列數**（時點邊界模式下為時點數）。"
                         "與 --gap-days 不同物，見 12 §二")
    ap.add_argument("--test-rows", type=int,
                    help="TimeSeriesSplit(test_size=) 每折驗證段大小（列數／時點數）")
    ap.add_argument("--boundary", choices=("auto", "row", "time"), default="auto",
                    help="time 切法的切點對齊方式。auto=時間欄有重複值就對齊時點邊界")
    ap.add_argument("--seed", type=int, default=42, help="StratifiedKFold 的 random_state")
    ap.add_argument("--no-write", action="store_true", help="只檢查，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")
    if not args.method:
        ap.error("要給 --method（time／group／stratified，依 12 §二 判準表選）")
    if not args.label_col:
        ap.error("要給 --label-col —— 沒有標籤就算不出各段正例率")
    for msg in validate_values(args.method, args.n_splits, args.gap_days,
                               args.horizon_days, args.max_ingest_lag_days,
                               args.gap_rows, args.test_rows,
                               args.time_col, args.group_col):
        # 值不合法 = 腳本根本沒跑起來 → 64。掉到 run() 會被判成 1（資料問題）
        ap.error(msg)

    try:
        return run(args)
    except FileNotFoundError as e:
        print(f"\n⛔ {e}", file=sys.stderr)
        print(f"   退出碼 {EX_ERROR} —— 補齊檔案後重跑。", file=sys.stderr)
        return EX_ERROR
    except ValueError as e:
        print(f"\n⛔ {e}", file=sys.stderr)
        print(f"   退出碼 {EX_ERROR} —— 資料／參數的問題，不是腳本壞了。", file=sys.stderr)
        return EX_ERROR


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ split_time.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
