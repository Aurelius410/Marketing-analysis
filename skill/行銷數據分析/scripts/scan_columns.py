#!/usr/bin/env python3
"""
建模前的欄位掃描（12 §七）—— 這一步在切分之前做，五分鐘，抵掉整個專案最常見的返工。

輸出直接進**表 11.4「特徵清單與 as_of_date」**（19 §1.7 規定欄名／計算窗／有無洩漏
風險三件事，缺一張報告即不完整）。

它只回答一個問題：**這個欄位能不能進模型。** 七項檢查，每一項的門檻都標了出處：

  ① 高基數 ID        nunique/n > 0.5 或欄名像 ID          → 排除（12 §七 表）
  ② 時間可得性       欄位含 as_of 之後的值 = 建模當下拿不到 → 擋住（12 §二、18-G4）
  ③ 事後欄位語意     語意上「只有結果發生後才有值」        → 人工複核（12 §七 表、§409 註）
  ④ 常數與近常數     top1 佔比 > 99%                       → 排除（12 §七 表）
  ⑤ 覆蓋率           有值的顧客佔比 < 30%                  → 標註或排除（12 §七、00 §五）
  ⑥ 與目標可疑高關聯 單變數關聯逼近完美 = 先懷疑洩漏        → 擋住（12 §六 警語二）
  ⑦ 哨兵值           9999／1900-01-01 之類的魔術數         → 擋住（04 §4.1 Q2）

**為什麼「排除」是 warning，而②⑥⑦是 error**（這個分桶是本腳本的設計決定，寫在這裡
是為了讓下一個人知道能不能改）：

  · ①④⑤ 的處置是「把這一欄拿掉」——動作明確、成本為零、下游照 排除清單 執行即可。
    把它們判成 error 會讓每一張建模表都退 1（每張表都有客戶編號），gate 變成雜訊，
    真正該擋的那幾條就沒人看了。
  · ②「欄位含 as_of 之後的值」拿掉那一欄擋不住 —— 它代表 build_features 根本沒切
    as_of，同一個錯很可能已經污染了所有聚合欄。要回去重建整張表（12 §二）。
  · ⑥ 需要人判斷「這是洩漏還是真的很強」，機器判不了，所以停下來問（12 §六 警語二：
    「查完沒問題才寫」）。確認過就用 --reviewed 放行。
  · ⑦ 照 04 §4.1 的原話：「哨兵放 error 不放 warning，理由很現實 —— warning 會被
    忽略，而它會讓平均間隔差 18.5 倍」。

用法：
    python scan_columns.py 2026Q3_電商 --as-of 2011-06-30 --label 是否流失
    python scan_columns.py 2026Q3_電商 --as-of 2011-06-30 --label y \
        --table 顧客特徵表/feat_customer_asof2011-06-30.parquet --id-col 客戶編號
    python scan_columns.py 2026Q3_電商 --as-of 2011-06-30 --label y \
        --reviewed 歷史退貨次數,門市代號      # 人工複核過、確認可用的欄位
    python scan_columns.py --self-test

輸出（統計表/預測模型/）：
    表11.4_特徵清單與as_of.csv     ← 直接進報告，欄序照 19 §1.7
    欄位掃描_人工複核清單.csv       ← ③ 的逐欄提問，機器判不出語意的那一類
    欄位掃描_門檻敏感度.csv         ← 12 §七 註明門檻為【推導，待驗證】，要求跑敏感度
    模型輸出/scan_columns.json     ← 機器可讀；含 排除清單／保留清單，給切分與訓練直接吃

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全部欄位可用，沒有需要處置的
    1  = 有 error 擋住（時間可得性／疑似洩漏／哨兵／可用特徵為零／標籤不合格）
    2  = 只有 warning，可往下但要照 排除清單 把欄位拿掉，並在報告寫明
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
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

# ══════════════════════════════════════════════════════════════
#  門檻。出處全部標在後面，要改就要同時改 reference（00 §九）
# ══════════════════════════════════════════════════════════════
UNIQUE_RATIO_MAX = 0.50      # 12 §七 表：nunique/n_rows > 0.5 = 高基數 ID
                             #   註明【推導，待驗證】，所以本腳本強制跑敏感度（見下）
TOP1_SHARE_MAX = 0.99        # 12 §七 表：最大類別佔比 > 99% = 近常數
COVERAGE_MIN = 0.30          # 12 §七 表 + 00 §五：有值的顧客佔比 < 30% 不准進報告
SENSITIVITY_RATIOS = (0.30, 0.50, 0.70)   # 12 §七 註：「門檻放在 0.5 或 0.3 結果一樣。
                                          #   **但要跑一次敏感度並記錄**」——就是這個

# ── 以下四個門檻 reference 沒給數字，是本腳本補的。理由寫在各自的檢查函式裡 ──
TARGET_ASSOC_BLOCK = 0.95    # 單變數關聯 ≥ 此值 → 擋住（幾乎必然是洩漏）
TARGET_ASSOC_WARN = 0.90     # ≥ 此值 → warning（12 §六「單一特徵獨大 = 先懷疑洩漏」）
MISSING_ASSOC_WARN = 0.80    # 「缺值與否」本身就能預測目標 → 事後欄位的機器可見長相
SENTINEL_CLIFF = 1.0         # 哨兵候選值與次極值的距離 ÷ 其餘值的 p1–p99 全距
MIN_ROWS_FOR_ASSOC = 30      # 少於這麼多有效列就不算關聯，回「樣本不足」而不是回一個數
MIN_LABELED = 100            # 12 §一：標註 < 100 筆不做模型（【實測】02_classification §19.1）

# 04 §4.1 Q2 的哨兵候選集（與 check_data_quality.py 同一組，不要各寫各的）
SENTINEL_NUMBERS = [-1, -9, -99, -999, 0, 9999, 99999, 999999]
SENTINEL_DATES = ["1900-01-01", "1970-01-01", "2099-12-31", "9999-12-31"]
# 0 不進數值欄的哨兵掃描：金額 0、次數 0、退貨額 0 都是合法值，掃它只會製造假警報。
# 0 佔比過高的情況由 ④ 近常數（top1 > 99%）負責，不會漏。
SENTINEL_NUMBERS_SCAN = [v for v in SENTINEL_NUMBERS if v != 0]
# 文字欄的哨兵：10 §5 實測「學生 D 的 Step 2-2 裡 6666 欄真的存在，變成一個假品類」
SENTINEL_TEXTS = [str(v) for v in SENTINEL_NUMBERS if v != 0] + ["6666", "8888"]

# 12 §七 程式碼區塊的原式。它是 ASCII-only 的，中文欄名一個都抓不到。
ID_PAT_REF = re.compile(r"(_id|_no|_code|mail|phone|uuid)$", re.I)
# 本腳本補的中文與無底線形式。台灣的建模表欄名是「客戶編號」「刷卡ID」不是 cust_id，
# 只用上面那條的話 ① 這一關在中文資料上等於沒開。
ID_PAT_EXT = re.compile(
    r"(?:(?<![a-z0-9])id|編號|代號|序號|卡號|單號|帳號|統編|身分證|護照|"
    r"電話|手機|信箱|郵箱|e-?mail|uuid|guid)$", re.I)

# ③ 事後欄位的語意關鍵詞。12 §七 表舉的四個例子（是否已喚回／本期回購金額／
# 退貨次數／最後一次登入）拆出來的詞根，加上同義的英文。命中只送人工複核，
# 不自動排除 —— 「歷史退貨次數」是合法特徵，「標籤窗內的退貨次數」是洩漏，
# 兩者欄名可能一模一樣，機器分不出來。
POSTHOC_KEYWORDS = [
    "已喚回", "已回購", "已成交", "已完成", "已回應", "已兌換", "已退",
    "本期", "下期", "次月", "隔月", "次季", "未來", "事後", "後續",
    "回購", "喚回", "退貨", "退款", "取消", "實際", "結果", "成交",
    "最後一次登入", "最近一次登入", "最後登入",
    "redeem", "respond", "convert", "churn", "actual", "outcome",
    "post_", "future_", "next_", "final_", "is_won", "won_",
]


# ══════════════════════════════════════════════════════════════
#  三桶輸出
# ══════════════════════════════════════════════════════════════
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


def _reset_buckets() -> None:
    _errors.clear()
    _warnings.clear()
    _infos.clear()


# ══════════════════════════════════════════════════════════════
#  資料結構
# ══════════════════════════════════════════════════════════════
@dataclass
class Flag:
    """一條檢查結果。桶 = error / warning / info。"""
    項目: str
    桶: str
    事實: str
    怎麼辦: str
    依據: str
    洩漏風險: str = ""      # 非空才會進表 11.4 的「洩漏風險」欄
    判定: str = ""          # 非空才會覆蓋表 11.4 的「判定」欄


@dataclass
class ColScan:
    """單一欄位的掃描結果。"""
    欄位: str
    型別: str
    n: int
    unique: int
    unique_ratio: float
    覆蓋率: float
    top1佔比: float
    值域: str = ""
    角色: str = "特徵"       # 特徵 / 標籤 / 分組鍵
    flags: list[Flag] = field(default_factory=list)

    @property
    def 最重桶(self) -> str:
        buckets = {f.桶 for f in self.flags}
        for b in ("error", "warning", "info"):
            if b in buckets:
                return b
        return "pass"


def _py(v: Any) -> Any:
    """numpy 純量 → 原生 Python。

    unique 數來自 pandas，是 numpy int64；佔比是 numpy float64。它們會一路帶進
    結果 dict，直到 json.dumps 才丟 TypeError —— 而且是在七項檢查都跑完、CSV 都
    寫好之後才炸，退出碼 70 蓋掉前面全部的結論。在來源轉掉。
    """
    if isinstance(v, (np.datetime64, pd.Timestamp)):
        return str(v)
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy 型別時，讓它寫得出去而不是讓整支腳本掛掉。"""
    if isinstance(o, (np.datetime64, pd.Timestamp, date, datetime)):
        return str(o)
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in list(o)]
    return str(o)


# ══════════════════════════════════════════════════════════════
#  關聯度工具（不吃 scipy／sklearn，setup_check 只保證 numpy+pandas）
# ══════════════════════════════════════════════════════════════
def _rankdata(a: np.ndarray) -> np.ndarray:
    """平均秩（同 scipy.stats.rankdata 的 'average'）。"""
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(a.size, dtype=float)
    ranks[order] = np.arange(1, a.size + 1, dtype=float)
    sa = a[order]
    i = 0
    while i < sa.size:
        j = i
        while j + 1 < sa.size and sa[j + 1] == sa[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def auc_binary(x: np.ndarray, y: np.ndarray) -> float | None:
    """單變數 AUC（Mann-Whitney U）。回 max(auc, 1-auc)。

    為什麼取對稱值：反向的完美預測（AUC=0）跟正向的完美預測一樣是洩漏，
    差別只在符號。這裡量的是「這一欄離完美分離有多近」，不是方向。
    """
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if x.size < MIN_ROWS_FOR_ASSOC:
        return None
    pos = y > 0.5
    n1, n0 = int(pos.sum()), int((~pos).sum())
    if n1 == 0 or n0 == 0:
        return None
    r = _rankdata(x)
    auc = (r[pos].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)
    return float(max(auc, 1.0 - auc))


def spearman_abs(x: np.ndarray, y: np.ndarray) -> float | None:
    """|Spearman|。連續標籤用它，理由同 auc_binary：量的是接近程度不是方向。"""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if x.size < MIN_ROWS_FOR_ASSOC:
        return None
    rx, ry = _rankdata(x), _rankdata(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(abs(np.corrcoef(rx, ry)[0, 1]))


def oof_target_encode(codes: np.ndarray, y: np.ndarray,
                      k: int = 5, seed: int = 42) -> np.ndarray:
    """類別欄的 out-of-fold 目標編碼。

    為什麼一定要 out-of-fold：in-sample 的類別平均對高基數欄天生就能完美重建目標
    （每個類別只有幾筆，平均就是那幾筆的答案），直接算會把所有類別欄都判成洩漏。
    這正是 12 §六 講 tree importance 對高基數有偏的同一個結構性問題。
    """
    n = y.size
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(n), min(k, max(2, n // 10)))
    enc = np.full(n, np.nan)
    for f in folds:
        mask = np.ones(n, dtype=bool)
        mask[f] = False
        if not mask.any():
            continue
        means = pd.Series(y[mask]).groupby(pd.Series(codes[mask])).mean()
        gm = float(y[mask].mean())
        enc[f] = pd.Series(codes[f]).map(means).astype(float).fillna(gm).to_numpy()
    return enc


def label_kind(y: pd.Series) -> str:
    """binary / continuous / multiclass。決定用哪個關聯度量。"""
    nu = int(y.nunique(dropna=True))
    if nu <= 1:
        return "constant"
    if nu == 2:
        return "binary"
    if pd.api.types.is_numeric_dtype(y) and nu > 10:
        return "continuous"
    return "multiclass"


def to_binary(y: pd.Series) -> np.ndarray:
    """二元標籤 → 0/1 float。字串（是/否、Y/N）也吃。"""
    if pd.api.types.is_numeric_dtype(y) or pd.api.types.is_bool_dtype(y):
        arr = y.astype(float).to_numpy()
        vals = np.unique(arr[np.isfinite(arr)])
        return (arr == vals.max()).astype(float) if vals.size else arr
    vals = sorted(str(v) for v in y.dropna().unique())
    pos_tokens = {"1", "true", "yes", "y", "是", "有", "流失", "回應", "present"}
    pos = next((v for v in vals if str(v).strip().lower() in pos_tokens), vals[-1])
    out = np.where(y.astype(str) == pos, 1.0, 0.0)
    out[y.isna().to_numpy()] = np.nan
    return out


def numeric_view(s: pd.Series) -> np.ndarray | None:
    """把一欄轉成可算關聯的數值向量。類別欄回 None（交給 oof 編碼）。"""
    if pd.api.types.is_bool_dtype(s):
        return s.astype(float).to_numpy()
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float).to_numpy()
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.astype("int64").where(s.notna()).astype(float).to_numpy()
    return None


# ══════════════════════════════════════════════════════════════
#  基本統計
# ══════════════════════════════════════════════════════════════
def dtype_label(s: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(s):
        return "日期"
    if pd.api.types.is_bool_dtype(s):
        return "布林"
    if pd.api.types.is_numeric_dtype(s):
        return "數值"
    return "類別"


def base_stats(name: str, s: pd.Series) -> ColScan:
    n = int(len(s))
    nu = int(s.nunique(dropna=True))
    cov = float(s.notna().mean()) if n else 0.0
    if nu:
        vc = s.value_counts(normalize=True, dropna=True)
        # 注意：value_counts 預設丟 NaN，所以 top1 是「非缺值之中」的佔比。
        # 12 §七 的原程式碼就是這樣算的，這裡保持一致，欄名也標明。
        top1 = float(vc.iloc[0])
    else:
        top1 = float("nan")
    rng_txt = ""
    if pd.api.types.is_datetime64_any_dtype(s) and s.notna().any():
        rng_txt = f"{s.min().date()}〜{s.max().date()}"
    elif pd.api.types.is_numeric_dtype(s) and s.notna().any():
        rng_txt = f"{float(s.min()):.4g}〜{float(s.max()):.4g}"
    return ColScan(欄位=name, 型別=dtype_label(s), n=n, unique=nu,
                   unique_ratio=(nu / n if n else float("nan")),
                   覆蓋率=cov, top1佔比=top1, 值域=rng_txt)


# ══════════════════════════════════════════════════════════════
#  ① 高基數 ID（12 §七 表第一列）
# ══════════════════════════════════════════════════════════════
def check_high_card_id(cs: ColScan, ratio_max: float) -> None:
    """教材原話：用「顧客 ID」分裂會讓每個子集合都只含一個類別 → 高純度 → 高 IG，
    「但『顧客 ID』對新顧客完全沒有預測力」（12 §七 引 02_classification §15.10）。
    """
    name_hit = bool(ID_PAT_REF.search(cs.欄位) or ID_PAT_EXT.search(cs.欄位))
    ratio_hit = cs.unique_ratio > ratio_max

    if ratio_hit:
        cs.flags.append(Flag(
            "①高基數ID", "warning",
            f"{cs.欄位}：相異值 {cs.unique:,} / {cs.n:,} 列 = {cs.unique_ratio:.3f}"
            f" > {ratio_max:.2f}" + ("，且欄名符合 ID 樣式" if name_hit else ""),
            "直接排除，照 排除清單 從特徵集拿掉。若它其實是分組鍵（同一顧客多列），"
            "用 --id-col 指定它 —— 排除但保留給 GroupKFold 當 groups（12 §二）",
            "12 §七 表第一列", 判定="排除-高基數ID"))
        return

    if name_hit:
        cs.flags.append(Flag(
            "①高基數ID", "warning",
            f"{cs.欄位}：欄名符合 ID 樣式，但相異值只有 {cs.unique:,}"
            f"（比值 {cs.unique_ratio:.3f}）",
            "兩條路二選一：(a) 它其實是有語意的類別欄（通路、門市、地區）→ 照 12 §七 "
            "改成聚合特徵（該門市的歷史回應率，且**必須用 as_of 之前的資料算**），"
            "改完用 --reviewed 放行；(b) 它真的是識別碼 → 排除",
            "12 §七 表第一列", 判定="排除-欄名像ID"))


# ══════════════════════════════════════════════════════════════
#  ② 時間可得性（12 §二、18-G4）
# ══════════════════════════════════════════════════════════════
def check_time_availability(cs: ColScan, s: pd.Series, as_of: date,
                            ingest_lag_days: int) -> None:
    """建模當下（as_of 那天）拿不拿得到這個值。

    只有日期／時間欄能被機器驗到 —— 它自己帶時間戳。聚合欄（近 90 天金額）沒有
    時間戳，機器看不出它是用哪一段算的，那一類只能靠 ③ 的人工複核。
    這個能力邊界要誠實講，不要讓「② 全過」被讀成「沒有時間洩漏」。
    """
    if cs.型別 != "日期" or not s.notna().any():
        return

    mx = s.max()
    mx_d = mx.date() if hasattr(mx, "date") else mx
    if mx_d > as_of:
        n_late = int((s > pd.Timestamp(as_of)).sum())
        cs.flags.append(Flag(
            "②時間可得性", "error",
            f"{cs.欄位}：最大值 {mx_d} 晚於 as_of {as_of}，"
            f"{n_late:,} / {cs.n:,} 列（{n_late / cs.n:.1%}）落在 as_of 之後",
            "不要只把這一欄拿掉 —— 這代表 build_features 沒有切 as_of，"
            "同一個錯很可能已經污染了所有聚合欄（近 N 天金額、最近一次購買日）。"
            "回 build_features(as_of) 重建整張表，它是唯一的介面（18-G4）",
            "12 §二 + 18-G4", 洩漏風險="高：含 as_of 之後的值",
            判定="擋住-時間可得性"))
        return

    if ingest_lag_days > 0:
        cutoff = pd.Timestamp(as_of) - pd.Timedelta(days=ingest_lag_days)
        n_late = int((s > cutoff).sum())
        if n_late:
            cs.flags.append(Flag(
                "②時間可得性", "warning",
                f"{cs.欄位}：{n_late:,} 列落在入庫延遲窗 "
                f"({cutoff.date()}, {as_of}] 內",
                f"你宣告了 {ingest_lag_days} 天的入庫延遲，代表 as_of 當天跑分時"
                f"這幾列還沒進倉。要嘛把 as_of 往前推 {ingest_lag_days} 天，"
                f"要嘛確認這個欄的來源沒有延遲（12 §二：POS T+1／廣告 T+3／退貨 T+30，"
                f"gap 取最長的那個）",
                "12 §二 gap 段", 洩漏風險="中：入庫延遲窗內"))


# ══════════════════════════════════════════════════════════════
#  ③ 事後欄位語意（12 §七 表第二列 + §409 註）
# ══════════════════════════════════════════════════════════════
def check_posthoc_semantics(cs: ColScan) -> None:
    """12 §409 的註解原話：「人工複核『事後欄位』那一類 —— 機器判不出語意，
    必須逐欄問『這個值在 as_of 當天真的存在嗎？』」

    所以這裡只做關鍵詞提示，不做排除。「歷史退貨次數」與「標籤窗內的退貨次數」
    欄名可以一模一樣，判它們的是語意不是字串。
    """
    low = cs.欄位.lower()
    hits = [k for k in POSTHOC_KEYWORDS if k.lower() in low]
    if not hits:
        return
    cs.flags.append(Flag(
        "③事後欄位語意", "warning",
        f"{cs.欄位}：欄名含「{'、'.join(hits[:3])}」，語意疑似事後才有值",
        f"逐欄問一句：「{cs.欄位} 這個值在 as_of 當天真的存在嗎？」"
        "答是 → --reviewed 放行；答否或不確定 → 排除。"
        "12 §七 表：欄位更新時間戳晚於 as_of、或語意上只有結果發生後才有值 = 直接排除，"
        "這是 18-G4 最常見的長相",
        "12 §七 表第二列 + §409 註", 洩漏風險="待人工複核：語意疑似事後欄"))


# ══════════════════════════════════════════════════════════════
#  ④ 常數與近常數（12 §七 表第三列）
# ══════════════════════════════════════════════════════════════
def check_constant(cs: ColScan) -> None:
    """不帶資訊，但會拖慢訓練並污染 SHAP 排序（12 §七 表原話）。"""
    if cs.unique <= 1:
        cs.flags.append(Flag(
            "④常數與近常數", "warning",
            f"{cs.欄位}：全表只有 {cs.unique} 個相異值",
            "排除。常數欄不帶任何資訊，但會佔一個特徵位、拖慢訓練，"
            "並在 SHAP summary 上佔一條沒有意義的線",
            "12 §七 表第三列", 判定="排除-常數"))
        return
    if np.isfinite(cs.top1佔比) and cs.top1佔比 > TOP1_SHARE_MAX:
        cs.flags.append(Flag(
            "④常數與近常數", "warning",
            f"{cs.欄位}：最大類別佔非缺值的 {cs.top1佔比:.2%}"
            f" > {TOP1_SHARE_MAX:.0%}",
            "排除。少於 1% 的另一類撐不起任何分裂；若那 1% 剛好就是正類，"
            "更要先查它是不是洩漏（見 ⑥），不要當特徵用",
            "12 §七 表第三列", 判定="排除-近常數"))


# ══════════════════════════════════════════════════════════════
#  ⑤ 覆蓋率（12 §七 表第四列 + 00 §五）
# ══════════════════════════════════════════════════════════════
def check_coverage(cs: ColScan, cov_min: float) -> None:
    """素材案例：某汽車專案 CAI 覆蓋率只有 3.0%，交出 18 人名單，被理解成
    「全庫只有 18 人有流失風險」，2,329 位（97%）沒被納入喚回設計
    （12 §七 表引 research/gap-business-translation BT-07）。
    """
    if cs.覆蓋率 >= cov_min:
        return
    cs.flags.append(Flag(
        "⑤覆蓋率", "warning",
        f"{cs.欄位}：有值的比例 {cs.覆蓋率:.1%} < {cov_min:.0%}",
        f"二選一，不准兩者皆非：(a) 排除；(b) 保留，但**圖表下方必須標覆蓋率**，"
        f"且名單交付時要寫明「本欄只涵蓋 {cs.覆蓋率:.1%} 的顧客」。"
        f"00 §五：低於門檻不准進報告。CAI 需 ≥3 次購買、CRI 需分群層，"
        f"這兩個指標天生就會卡在這一關",
        "12 §七 表第四列 + 00 §五", 判定="標註或排除-覆蓋率不足"))


# ══════════════════════════════════════════════════════════════
#  ⑥ 與目標的可疑高關聯（12 §六 警語二）
# ══════════════════════════════════════════════════════════════
def check_target_assoc(cs: ColScan, s: pd.Series, y_num: np.ndarray | None,
                       kind: str) -> None:
    """12 §六 警語二：「單一特徵獨大 = 先懷疑洩漏」，教材原例是「用『已成交金額』
    預測『是否成交』」。那個錯誤在欄位掃描階段就看得見 —— 該欄單獨拿去排序，
    AUC 會接近 1。

    **0.95 / 0.90 兩個門檻是本腳本補的**，reference 只給了診斷順序沒給數字。
    取值理由：12 §九 的硬門檻是「候選模型相對 naive baseline 提升 < 0.03 AUC 就不上線」，
    也就是整套模型工程的合理增益在 0.03 這個量級；那麼**單獨一欄**就打到 0.95 以上，
    不是找到金礦，是那一欄裡有答案。門檻可用 --assoc-block / --assoc-warn 調，
    調了就要照 00 §1.4 在報告寫理由。
    """
    if y_num is None or kind in ("constant", "multiclass"):
        return

    x = numeric_view(s)
    src = "原值"
    if x is None:
        # 類別欄：out-of-fold 目標編碼後再算，避免高基數欄天生高分（12 §六）
        codes = s.astype("object").where(s.notna(), other="__NA__").astype(str).to_numpy()
        m = np.isfinite(y_num)
        if int(m.sum()) < MIN_ROWS_FOR_ASSOC:
            return
        enc = np.full(y_num.size, np.nan)
        enc[m] = oof_target_encode(codes[m], y_num[m])
        x, src = enc, "out-of-fold 目標編碼"

    assoc = (auc_binary(x, y_num) if kind == "binary"
             else spearman_abs(x, y_num))
    if assoc is None:
        return

    metric = "單變數 AUC" if kind == "binary" else "|Spearman|"
    if assoc >= TARGET_ASSOC_BLOCK:
        cs.flags.append(Flag(
            "⑥目標關聯", "error",
            f"{cs.欄位}：{metric} = {assoc:.3f} ≥ {TARGET_ASSOC_BLOCK:.2f}"
            f"（{src}）—— 單獨一欄就幾乎完美分離目標",
            "停下來查兩件事（12 §六 的診斷順序）：① 這一欄是不是標籤的衍生物"
            "（教材原例：用「已成交金額」預測「是否成交」）；② 它的計算窗是不是"
            "跨進了標籤窗。查完確認不是洩漏，用 --reviewed 放行並在報告寫明理由；"
            "不確定就排除 —— 驗證集 AUC 0.95、上線崩盤就是這麼來的（18-G4）",
            "12 §六 警語二 + 18-G4（門檻為本腳本所補）",
            洩漏風險="高：與目標近乎完美關聯", 判定="擋住-疑似洩漏"))
    elif assoc >= TARGET_ASSOC_WARN:
        cs.flags.append(Flag(
            "⑥目標關聯", "warning",
            f"{cs.欄位}：{metric} = {assoc:.3f} ≥ {TARGET_ASSOC_WARN:.2f}（{src}）",
            "先懷疑洩漏再高興。查它的計算窗有沒有跨進標籤窗；"
            "確認乾淨就留著，但要記進表 11.4 的洩漏風險欄，"
            "並在 SHAP summary 出來時回頭對照（12 §六 警語二）",
            "12 §六 警語二（門檻為本腳本所補）",
            洩漏風險="中：與目標高度關聯，待查計算窗"))
    else:
        cs.flags.append(Flag(
            "⑥目標關聯", "info",
            f"{cs.欄位}：{metric} = {assoc:.3f}（{src}）",
            "", "12 §六"))


def check_missing_pattern(cs: ColScan, s: pd.Series,
                          y_num: np.ndarray | None, kind: str) -> None:
    """「有沒有值」本身能不能預測目標。

    **這一項是本腳本補的**，但它補的正是 reference 說機器判不出來的那一類。
    12 §七 表第二列把事後欄位定義成「語意上只有在結果發生後才會有值」——
    「才會有值」這五個字有機器可見的長相：那一欄的缺值型態會跟著目標走
    （例如「喚回券使用日」只有被喚回的人才有）。欄名可以偽裝，缺值型態不會。
    門檻 0.80 是本腳本取的，比 ⑥ 的 0.90 寬，因為缺值型態常常只是「新客沒有歷史」
    這種合法的結構性缺值，不該一有關聯就叫。
    """
    if y_num is None or kind != "binary":
        return
    if cs.覆蓋率 <= 0.0 or cs.覆蓋率 >= 1.0:
        return
    miss = s.isna().astype(float).to_numpy()
    assoc = auc_binary(miss, y_num)
    if assoc is None or assoc < MISSING_ASSOC_WARN:
        return
    cs.flags.append(Flag(
        "⑥缺值型態", "warning",
        f"{cs.欄位}：光用「有沒有值」就能把目標排到 AUC {assoc:.3f}"
        f"（覆蓋率 {cs.覆蓋率:.1%}）",
        "查這一欄為什麼會缺：若是「只有發生過的人才有值」（喚回券使用日、"
        "退貨處理日），那它就是 12 §七 的事後欄位，直接排除。"
        "若是結構性缺值（新客沒有歷史），改成明示的旗標欄（是否為新客）再用，"
        "不要讓模型從 NaN 去學",
        "12 §七 表第二列（缺值型態判準為本腳本所補）",
        洩漏風險="中：缺值型態與目標關聯"))


# ══════════════════════════════════════════════════════════════
#  ⑦ 哨兵值（04 §4.1 Q2）
# ══════════════════════════════════════════════════════════════
def check_sentinel(cs: ColScan, s: pd.Series) -> None:
    """04 §4.1 Q2 的實測代價：`int` 欄有 100 個 `9999`（恰等於客戶數），不排除算
    平均購買間隔得 199.46 天，真值 10.79 天，差 18.5 倍 → 流失門檻訂成 200 天 →
    100 人只標出 3 人流失（真實 28 人），漏掉 25 人合計 NT$947,152（6.4% 營收）。

    **判定規則與 04 Q2 不同，這是刻意的**：04 Q2 的觸發條件是「出現次數恰等於某個
    group-by 鍵的相異值數」，那條規則在**交易明細**上成立（每位顧客一個 9999）。
    但建模表是一列一顧客，鍵欄的相異值數就等於列數 n，拿它去比對永遠不會命中 ——
    照抄 04 Q2 到這裡等於這一關沒開。所以改用「斷崖」判準：候選值是該欄的極值，
    且它與次極值的距離 ≥ 其餘值的 p1–p99 全距（SENTINEL_CLIFF=1.0，本腳本所補）。
    真值分布不會在最頂端留一個這麼大的空洞。
    """
    if cs.型別 == "日期":
        vals = s.dropna()
        if vals.empty:
            return
        d = pd.to_datetime(vals).dt.date
        for token in SENTINEL_DATES:
            tgt = pd.Timestamp(token).date()
            cnt = int((d == tgt).sum())
            if cnt:
                cs.flags.append(Flag(
                    "⑦哨兵值", "error",
                    f"{cs.欄位}：{cnt:,} 列的值是 {token}，命中 04 §4.1 Q2 的日期哨兵候選集",
                    "回 M1：在 contracts/<來源>.yml 的 sentinels: 宣告 "
                    "{column, value, action: to_null|keep|exclude, reason} 後重跑 "
                    "check_data_quality.py，再重建特徵表。"
                    "不要在這裡就地補值 —— 1900-01-01 進 recency 會算出四萬多天，"
                    "整條分布跟著歪（04 §4.1 Q2：哨兵放 error 不放 warning）",
                    "04 §4.1 Q2", 判定="擋住-哨兵值"))
        return

    if cs.型別 == "類別":
        txt = s.dropna().astype(str).str.strip()
        if txt.empty:
            return
        for token in SENTINEL_TEXTS:
            cnt = int((txt == token).sum())
            if cnt >= 2:
                cs.flags.append(Flag(
                    "⑦哨兵值", "error",
                    f"{cs.欄位}：{cnt:,} 列的值是字串 \"{token}\"，"
                    f"命中哨兵候選集（10 §5 實測：6666 曾變成一個假品類）",
                    "回 M1 在契約的 sentinels: 宣告後重跑；"
                    "一個叫 \"9999\" 的類別會在 one-hot 之後變成一個真的特徵，"
                    "模型會認真學它",
                    "04 §4.1 Q2 + 10 §5", 判定="擋住-哨兵值"))
        return

    if cs.型別 not in ("數值",):
        return
    x = s.dropna().astype(float).to_numpy()
    if x.size < MIN_ROWS_FOR_ASSOC:
        return
    for v in SENTINEL_NUMBERS_SCAN:
        cnt = int((x == v).sum())
        if cnt < max(2, int(0.001 * x.size)):
            continue
        others = x[x != v]
        if others.size == 0:
            continue
        is_max, is_min = v >= x.max(), v <= x.min()
        if not (is_max or is_min):
            continue
        neighbour = others.max() if is_max else others.min()
        spread = float(np.percentile(others, 99) - np.percentile(others, 1))
        gap = abs(v - neighbour)
        cliff = gap / spread if spread > 0 else (float("inf") if gap > 0 else 0.0)
        if cliff < SENTINEL_CLIFF:
            continue
        cs.flags.append(Flag(
            "⑦哨兵值", "error",
            f"{cs.欄位}：{cnt:,} 列的值是 {v:g}，且它與次極值 {neighbour:g} 之間"
            f"隔了 {gap:g}，是其餘值 p1–p99 全距（{spread:g}）的 {cliff:.1f} 倍 "
            f"—— 真值分布不會在頂端留這麼大的空洞",
            "回 M1：contracts/<來源>.yml 的 sentinels: 宣告 "
            "{column, value, action: to_null|keep|exclude, reason} 後重跑 "
            "check_data_quality.py 與 build_features.py。"
            "04 §4.1 Q2 的實測：9999 沒排掉，平均購買間隔 199.46 天 vs 真值 10.79 天，"
            "差 18.5 倍，流失門檻連帶訂成 200 天，漏掉 25 人共 NT$947,152（6.4% 營收）。"
            f"確認 {v:g} 是真值就用 --reviewed {cs.欄位} 放行",
            "04 §4.1 Q2（斷崖判準為本腳本所補）", 判定="擋住-哨兵值"))


# ══════════════════════════════════════════════════════════════
#  標籤自身檢查
# ══════════════════════════════════════════════════════════════
def check_label(df: pd.DataFrame, label_cols: list[str]) -> tuple[np.ndarray | None, str]:
    """回 (y_num, kind)。標籤不合格直接 err，讓退出碼變 1。"""
    print("\n標籤欄（12 §一 進場門檻）")
    primary = label_cols[0]
    y = df[primary]
    kind = label_kind(y)
    n_na = int(y.isna().sum())

    if kind == "constant":
        err(f"標籤 {primary} 只有 {y.nunique(dropna=True)} 個相異值",
            "常數標籤訓練不出任何東西。回去確認標籤窗（make_label 的 "
            "horizon_days / gap_days）是不是取得太短或太長，讓所有人都是同一類")
        return None, kind

    if n_na:
        warn(f"標籤 {primary} 有 {n_na:,} 列缺值（共 {len(df):,} 列）",
             "這些列不能進訓練也不能進評估。決定怎麼處理並寫進 執行紀錄："
             "刪除（多數情況）或補成負類（只有在「沒有事件 = 沒發生」成立時才行）")

    if kind == "binary":
        yb = to_binary(y)
        n_pos = int(np.nansum(yb))
        n_lab = int(np.isfinite(yb).sum())
        rate = n_pos / n_lab if n_lab else 0.0
        detail(f"{primary}：{n_lab:,} 筆有標籤，正類 {n_pos:,} 筆（{rate:.2%}）")
        if n_lab < MIN_LABELED:
            err(f"有標籤的樣本只有 {n_lab:,} 筆 < {MIN_LABELED}",
                "12 §一：「一旦有 100+ 個標籤，就可以考慮機器學習」。"
                "不到就不要做模型 —— 寫規則做 MVP，邊跑邊蒐集標籤")
        elif n_pos < MIN_LABELED:
            warn(f"正類只有 {n_pos:,} 筆（< {MIN_LABELED}）",
                 "正類筆數才是模型實際學得到的量。12 §四：用 class_weight／"
                 "scale_pos_weight，不要用 SMOTE；並在 §八 用 profit curve 調門檻")
        elif rate < 0.05:
            info(f"正類比例 {rate:.2%}，屬 12 §四 的稀有正類 —— "
                 f"主指標看 PR/AP 不看 Accuracy，且校準必做（§三）")
        else:
            ok(f"標籤可用：{n_lab:,} 筆、正類 {rate:.2%}")
        return yb, kind

    if kind == "continuous":
        ok(f"{primary}：連續標籤，{int(y.notna().sum()):,} 筆有值 —— "
           f"⑥ 用 |Spearman| 量關聯")
        return y.astype(float).to_numpy(), kind

    warn(f"標籤 {primary} 是多類別（{y.nunique(dropna=True)} 類）",
         "⑥ 目標關聯這一關本次不跑 —— 多類別的單變數關聯要逐類 one-vs-rest，"
         "本腳本未實作。改法：把它拆成幾個二元標籤各跑一次 scan_columns")
    return None, kind


# ══════════════════════════════════════════════════════════════
#  門檻敏感度（12 §七 註明門檻為【推導，待驗證】，要求跑一次並記錄）
# ══════════════════════════════════════════════════════════════
def sensitivity_table(scans: list[ColScan]) -> pd.DataFrame:
    """12 §七 註：「門檻放在 0.5 或 0.3 結果一樣。**但要跑一次敏感度並記錄**」
    （00 §1.4）。不記錄的話，下一個人不知道 0.5 這個數字能不能動。
    """
    rows = []
    for cs in scans:
        if cs.角色 != "特徵":
            continue
        verdicts = {r: ("排除" if cs.unique_ratio > r else "保留")
                    for r in SENSITIVITY_RATIOS}
        rows.append({
            "欄位": cs.欄位,
            "unique_ratio": round(cs.unique_ratio, 4),
            **{f"門檻{r:.1f}": verdicts[r] for r in SENSITIVITY_RATIOS},
            "判定隨門檻改變": "是" if len(set(verdicts.values())) > 1 else "否",
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════
#  掃描主體
# ══════════════════════════════════════════════════════════════
def scan(df: pd.DataFrame, as_of: date, label_cols: list[str],
         id_cols: list[str], reviewed: set[str],
         cov_min: float = COVERAGE_MIN,
         ratio_max: float = UNIQUE_RATIO_MAX,
         ingest_lag_days: int = 0,
         y_num: np.ndarray | None = None,
         kind: str = "binary") -> list[ColScan]:
    """逐欄跑七項檢查。簽章與 12 §409 的 scan(df, as_of, label_cols, n_min_coverage)
    相容，多出來的參數都有預設值。
    """
    scans: list[ColScan] = []
    for c in df.columns:
        cs = base_stats(str(c), df[c])
        if c in label_cols:
            cs.角色 = "標籤"
            scans.append(cs)
            continue
        if c in id_cols:
            cs.角色 = "分組鍵"
        check_high_card_id(cs, ratio_max)
        check_time_availability(cs, df[c], as_of, ingest_lag_days)
        check_posthoc_semantics(cs)
        check_constant(cs)
        check_coverage(cs, cov_min)
        check_target_assoc(cs, df[c], y_num, kind)
        check_missing_pattern(cs, df[c], y_num, kind)
        check_sentinel(cs, df[c])

        if cs.欄位 in reviewed:
            # 人工複核過的：降級成 info，並保留原本的事實敘述當作留痕。
            # 不是刪掉那條 flag —— 報告要看得到「這一欄被誰放行、放行的是哪一項」。
            for f in cs.flags:
                if f.桶 in ("error", "warning"):
                    f.桶 = "info"
                    f.怎麼辦 = f"（已由 --reviewed 放行）原處置：{f.怎麼辦}"
                    f.判定 = ""
        scans.append(cs)
    return scans


def verdict_of(cs: ColScan) -> str:
    if cs.角色 == "標籤":
        return "標籤欄（不掃描）"
    if cs.角色 == "分組鍵":
        return "分組鍵：排除出特徵集，保留給 GroupKFold（12 §二）"
    named = [f.判定 for f in cs.flags if f.判定]
    return "；".join(dict.fromkeys(named)) if named else "保留"


def leak_of(cs: ColScan) -> str:
    risks = [f.洩漏風險 for f in cs.flags if f.洩漏風險]
    if risks:
        return "；".join(dict.fromkeys(risks))
    return "無（機器可見範圍內）"


def window_of(cs: ColScan, as_of: date) -> str:
    """表 11.4 的「計算窗」欄。日期欄有實測值域可寫，其餘只能寫宣告值。"""
    if cs.型別 == "日期" and cs.值域:
        return f"實測 {cs.值域}（宣告 ≤ {as_of}）"
    return f"宣告 ≤ {as_of}（本欄無時間戳，機器驗不到）"


def build_table_114(scans: list[ColScan], as_of: date) -> pd.DataFrame:
    """表 11.4「特徵清單與 as_of_date」。欄序照 19 §1.7：欄名／計算窗／有無洩漏風險。

    欄名刻意帶 % 與括號（「覆蓋率(%)」「top1佔比(%)」）—— 這是報告要的寫法。
    下游讀這張表時**一律用欄名取值**：itertuples 會把這種欄名改成位置代號 _4、_5，
    欄序一動就對到別欄，而且不會報錯。
    """
    rows = []
    for cs in scans:
        todo = "；".join(f.怎麼辦 for f in cs.flags
                         if f.桶 in ("error", "warning") and f.怎麼辦)
        base = "；".join(dict.fromkeys(
            f.依據 for f in cs.flags if f.桶 in ("error", "warning")))
        rows.append({
            "欄位": cs.欄位,
            "角色": cs.角色,
            "型別": cs.型別,
            "n": cs.n,
            "unique": cs.unique,
            "unique_ratio": round(cs.unique_ratio, 4),
            "覆蓋率(%)": round(cs.覆蓋率 * 100, 2),
            "top1佔比(%)": (round(cs.top1佔比 * 100, 2)
                            if np.isfinite(cs.top1佔比) else None),
            "值域": cs.值域,
            "as_of_date": str(as_of),
            "計算窗": window_of(cs, as_of),
            "洩漏風險": leak_of(cs),
            "判定": verdict_of(cs),
            "該怎麼辦": todo or "—",
            "依據": base or "—",
        })
    return pd.DataFrame(rows)


def build_review_list(scans: list[ColScan], as_of: date) -> pd.DataFrame:
    """③ 的人工複核清單。12 §409 註：必須逐欄問「這個值在 as_of 當天真的存在嗎？」"""
    rows = []
    for cs in scans:
        for f in cs.flags:
            if f.項目 in ("③事後欄位語意", "⑥缺值型態") or (
                    f.項目 == "⑥目標關聯" and f.桶 in ("error", "warning")):
                rows.append({
                    "欄位": cs.欄位,
                    "檢查項": f.項目,
                    "要問的問題": f"{cs.欄位} 這個值在 as_of={as_of} 當天真的存在嗎？"
                                  f"它的計算窗有沒有跨進標籤窗？",
                    "事實": f.事實,
                    "答『存在且沒跨窗』怎麼辦": f"--reviewed {cs.欄位} 放行，"
                                                f"並把理由寫進 執行紀錄",
                    "答『不確定』怎麼辦": "排除。12 §七：語意上只有結果發生後才有值的欄位"
                                          "直接排除，這是 18-G4 最常見的長相",
                    "目前桶": f.桶,
                })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════
#  載入
# ══════════════════════════════════════════════════════════════
def load_table(p: Any, explicit: Path | None, as_of: date) -> tuple[pd.DataFrame, Path]:
    path = explicit
    if path is not None and not path.is_absolute():
        cand = p.root / path
        path = cand if cand.exists() else path
    if path is None:
        path = p.features / f"feat_customer_asof{as_of}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"找不到建模表：{path}\n"
            f"  先跑 build_features.py <專案> --as-of {as_of} —— 它會產出 "
            f"顧客特徵表/feat_customer_asof{as_of}.parquet。"
            f"或用 --table 指定路徑。")
    df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
          else pd.read_csv(path, encoding="utf-8-sig"))
    return df, path


def guess_id_cols(df: pd.DataFrame) -> list[str]:
    out = []
    for c in df.columns:
        name = str(c)
        if ID_PAT_REF.search(name) or ID_PAT_EXT.search(name):
            out.append(name)
    return out


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    as_of: date = args.as_of
    df, tpath = load_table(p, args.table, as_of)

    if len(df) == 0:
        raise ValueError(f"建模表 {tpath.name} 是空的（0 列），沒有東西可以掃描。")

    label_cols = [c.strip() for c in args.label.split(",") if c.strip()]
    missing = [c for c in label_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"--label 指定的欄位不在建模表裡：{'、'.join(missing)}\n"
            f"  表裡有：{'、'.join(map(str, df.columns[:20]))}"
            f"{' …' if df.shape[1] > 20 else ''}")

    reviewed = {c.strip() for c in (args.reviewed or "").split(",") if c.strip()}
    bad_rev = [c for c in reviewed if c not in df.columns]
    if bad_rev:
        raise ValueError(
            f"--reviewed 指定的欄位不在建模表裡：{'、'.join(bad_rev)} —— "
            f"打錯欄名的話會以為自己放行了，其實那一關還擋著")

    if args.id_col:
        id_cols = [c.strip() for c in args.id_col.split(",") if c.strip()]
        bad_id = [c for c in id_cols if c not in df.columns]
        if bad_id:
            raise ValueError(f"--id-col 指定的欄位不在建模表裡：{'、'.join(bad_id)}")
        id_src = "指定"
    else:
        id_cols = guess_id_cols(df)
        id_src = "推測"

    print("=" * 74)
    print("行銷數據分析 Skill — 建模前的欄位掃描（12 §七）")
    print(f"專案：{args.project}｜建模表：{tpath.name}"
          f"（{len(df):,} 列 × {df.shape[1]} 欄）")
    print(f"as_of：{as_of}｜標籤：{'、'.join(label_cols)}"
          f"｜入庫延遲：{args.ingest_lag_days} 天")
    print(f"分組鍵（{id_src}）：{'、'.join(id_cols) if id_cols else '（無）'}")
    if reviewed:
        print(f"已人工複核放行：{'、'.join(sorted(reviewed))}")
    print("=" * 74)

    y_num, kind = check_label(df, label_cols)

    # 同一顧客多筆列：12 §二 稱之為行銷資料「最常見的隱藏洩漏」
    print("\n分組鍵與切分（12 §二）")
    if not id_cols:
        warn("沒有可辨識的分組鍵（--id-col 未指定，欄名也沒有 ID 樣式）",
             "指定 --id-col <顧客編號欄>。沒有它就檢查不到「同一顧客多筆列」——"
             "12 §二 說那是行銷資料最常見的隱藏洩漏：隨機 8:2 切列之後幾乎每位顧客"
             "都同時出現在訓練集與測試集，模型只要記住那個人就能拿高分")
    for c in id_cols:
        nu = int(df[c].nunique(dropna=True))
        if nu and nu < len(df):
            warn(f"{c}：{len(df):,} 列只有 {nu:,} 個相異值"
                 f"（平均每個 {len(df) / nu:.2f} 列）= 同一顧客多筆",
                 f"切分**必須** GroupKFold(groups={c})，不能按列切。"
                 f"同時有時間結構就用 GroupTimeSeriesSplit（先按時間切，"
                 f"再檢查 group 不跨邊）。12 §二 判準表最後一列")
        elif nu:
            ok(f"{c}：{nu:,} 個相異值 = {len(df):,} 列，一顧客一列，"
               f"不需要 GroupKFold（時間結構仍要另外看）")

    print("\n逐欄掃描（七項）")
    scans = scan(df, as_of, label_cols, id_cols, reviewed,
                 cov_min=args.coverage_min, ratio_max=args.unique_ratio_max,
                 ingest_lag_days=args.ingest_lag_days, y_num=y_num, kind=kind)

    for cs in scans:
        for f in cs.flags:
            if f.桶 == "error":
                err(f.事實, f.怎麼辦)
            elif f.桶 == "warning":
                warn(f.事實, f.怎麼辦)

    keep = [cs.欄位 for cs in scans
            if cs.角色 == "特徵" and verdict_of(cs) == "保留"]
    drop = [cs.欄位 for cs in scans
            if cs.角色 == "特徵" and verdict_of(cs) != "保留"]
    clean = [cs.欄位 for cs in scans if cs.角色 == "特徵" and cs.最重桶 in ("pass", "info")]
    if not clean:
        err("掃完之後沒有任何欄位可以進模型",
            "全部欄位都被判出問題。先照 排除清單 修，再回 build_features 重建特徵表；"
            "若修完仍然沒有可用特徵，12 §九：不建議上線，用 naive baseline "
            "（R 排序、RFM Score 排序）即可")

    print("\n" + "=" * 74)
    n_err = len(_errors)
    n_warn = len(_warnings)
    print(f"掃描 {len(scans)} 欄（特徵 {sum(1 for c in scans if c.角色 == '特徵')}、"
          f"標籤 {sum(1 for c in scans if c.角色 == '標籤')}、"
          f"分組鍵 {sum(1 for c in scans if c.角色 == '分組鍵')}）"
          f"｜error {n_err}、warning {n_warn}")
    print(f"可直接進模型：{len(keep)} 欄｜要處置：{len(drop)} 欄")

    # 機器判不到的那一段，要在主控台講清楚，不要讓「全過」被讀成「沒有洩漏」
    print("\n這支腳本驗不到什麼（12 §七 §409 註）：")
    print("  · 聚合欄（近 90 天金額、最近一次購買日）沒有自己的時間戳，")
    print("    機器看不出它是用哪一段資料算的。②只驗得到日期欄。")
    print("  · 語意上的事後欄位要人工逐欄問「這個值在 as_of 當天真的存在嗎？」")
    print("    清單已寫進 欄位掃描_人工複核清單.csv。")

    if n_err:
        print(f"\n結果：⛔ 有 {n_err} 條 error → 不准進切分與訓練。")
    elif n_warn:
        print(f"\n結果：⚠ 有 {n_warn} 條 warning → 可往下，"
              f"但要照 排除清單 拿掉欄位，並在報告逐條寫明處置。")
    else:
        print("\n結果：✅ 七項全過，所有欄位可用。")

    tbl = build_table_114(scans, as_of)
    review = build_review_list(scans, as_of)
    sens = sensitivity_table(scans)
    changed = (sens[sens["判定隨門檻改變"] == "是"]["欄位"].tolist()
               if len(sens) else [])
    print("\n門檻敏感度（12 §七 註：門檻為【推導，待驗證】，必須跑一次並記錄）")
    if changed:
        warn(f"{len(changed)} 欄的判定會隨 unique_ratio 門檻改變："
             f"{'、'.join(changed[:8])}",
             f"門檻 {SENSITIVITY_RATIOS} 三個值下結論不一致，"
             f"代表 0.5 這個數字在你的資料上不是無關緊要的。"
             f"報告要寫明用了哪一個門檻與理由（00 §1.4）")
    else:
        ok(f"門檻 {SENSITIVITY_RATIOS} 三個值下判定完全一致 —— "
           f"與 12 §七 的說法相符（「門檻放在 0.5 或 0.3 結果一樣」）")

    if not args.no_write:
        out_dir = p.tables / "預測模型"
        out_dir.mkdir(parents=True, exist_ok=True)
        t114 = out_dir / "表11.4_特徵清單與as_of.csv"
        tbl.to_csv(t114, index=False, encoding="utf-8-sig")
        print(f"\n✓ 表 11.4：{t114}")

        rp = out_dir / "欄位掃描_人工複核清單.csv"
        review.to_csv(rp, index=False, encoding="utf-8-sig")
        print(f"✓ 人工複核清單（{len(review)} 條）：{rp}")

        sp = out_dir / "欄位掃描_門檻敏感度.csv"
        sens.to_csv(sp, index=False, encoding="utf-8-sig")
        print(f"✓ 門檻敏感度：{sp}")

        p.models.mkdir(parents=True, exist_ok=True)
        jp = p.models / "scan_columns.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "table": str(tpath),
            "as_of_date": str(as_of),
            "n_rows": _py(len(df)),
            "label_cols": label_cols,
            "label_kind": kind,
            "id_cols": id_cols,
            "id_cols_source": id_src,
            "reviewed": sorted(reviewed),
            "thresholds": {
                "unique_ratio_max": args.unique_ratio_max,
                "top1_share_max": TOP1_SHARE_MAX,
                "coverage_min": args.coverage_min,
                "target_assoc_block": TARGET_ASSOC_BLOCK,
                "target_assoc_warn": TARGET_ASSOC_WARN,
                "missing_assoc_warn": MISSING_ASSOC_WARN,
                "sentinel_cliff": SENTINEL_CLIFF,
                "ingest_lag_days": args.ingest_lag_days,
            },
            "保留清單": keep,
            "排除清單": drop,
            "敏感度_判定會變的欄": changed,
            "columns": [{
                "欄位": cs.欄位, "角色": cs.角色, "型別": cs.型別,
                "unique": _py(cs.unique),
                "unique_ratio": round(float(cs.unique_ratio), 4),
                "覆蓋率": round(float(cs.覆蓋率), 4),
                "top1佔比": (round(float(cs.top1佔比), 4)
                             if np.isfinite(cs.top1佔比) else None),
                "判定": verdict_of(cs), "洩漏風險": leak_of(cs),
                "flags": [{"項目": f.項目, "桶": f.桶, "事實": f.事實,
                           "怎麼辦": f.怎麼辦, "依據": f.依據} for f in cs.flags],
            } for cs in scans],
            "errors": _errors,
            "warnings": _warnings,
            "infos": _infos,
        }, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        print(f"✓ 機器可讀結果（含 保留/排除清單）：{jp}")

    if n_err:
        return EX_ERROR
    if n_warn:
        return EX_WARN
    return EX_OK


# ══════════════════════════════════════════════════════════════
#  自我測試
#  每一項都成對：「該抓的有抓到」＋「不該叫的沒亂叫」。
#  只驗前者的話，一支永遠回 pass 的假檢查器也會通過。
# ══════════════════════════════════════════════════════════════
def _selftest() -> int:  # noqa: C901 - 測試就是一長串斷言，拆開反而難讀
    print("=" * 74)
    print("scan_columns.py 自我測試")
    print("=" * 74)
    rng = np.random.default_rng(20260728)
    failed: list[str] = []
    total = [0]

    def check(name: str, cond: bool, got: str = "") -> None:
        total[0] += 1
        if cond:
            print(f"  ✓ {name}" + (f"（{got}）" if got else ""))
        else:
            print(f"  ✗ {name}" + (f"（{got}）" if got else ""))
            failed.append(name)

    def one(name: str, s: pd.Series, fn, *a, **kw) -> ColScan:
        cs = base_stats(name, s)
        fn(cs, *a, **kw)
        return cs

    def buckets(cs: ColScan, 項目: str | None = None) -> set[str]:
        return {f.桶 for f in cs.flags if 項目 is None or f.項目 == 項目}

    n = 800
    as_of = date(2011, 6, 30)

    # ── ① 高基數 ID ───────────────────────────────────────────
    cs = one("cust_id", pd.Series(np.arange(n)), check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 抓到 unique_ratio=1.0 的 cust_id", "warning" in buckets(cs))
    cs = one("客戶編號", pd.Series(np.arange(n)), check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 抓到中文欄名『客戶編號』（原式 ASCII regex 抓不到）",
          "warning" in buckets(cs))
    cs = one("Unnamed: 10", pd.Series(np.arange(n, dtype=float)),
             check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 抓到欄名無線索、但比值=1.0 的欄", "warning" in buckets(cs))
    cs = one("性別", pd.Series(rng.choice(["男", "女"], n)),
             check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 沒有誤判 2 類的性別欄", not cs.flags)
    cs = one("近90天金額", pd.Series(rng.normal(1000, 300, n)),
             check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 沒有誤判連續金額欄（比值高但欄名不像 ID？）",
          "warning" in buckets(cs),
          f"比值 {cs.unique_ratio:.3f} → 照 12 §七 的規則本來就該排除")
    cs = one("valid_flag", pd.Series(rng.choice([0, 1], n)),
             check_high_card_id, UNIQUE_RATIO_MAX)
    check("① 沒有把 valid_flag 誤判成 ID（lookbehind 有效）", not cs.flags)

    # ── ② 時間可得性 ─────────────────────────────────────────
    late = pd.Series(pd.to_datetime(["2011-06-29"] * (n - 5) + ["2011-07-15"] * 5))
    cs = one("最後登入日", late, check_time_availability, as_of, 0)
    check("② 抓到日期欄含 as_of 之後的值 → error",
          "error" in buckets(cs, "②時間可得性"))
    early = pd.Series(pd.to_datetime(["2011-05-01"] * n))
    cs = one("最近購買日", early, check_time_availability, as_of, 0)
    check("② 沒有誤判全部早於 as_of 的日期欄", not cs.flags)
    edge = pd.Series(pd.to_datetime(["2011-06-30"] * n))
    cs = one("最近購買日", edge, check_time_availability, as_of, 0)
    check("② as_of 當天不算晚（邊界是 <=，不是 <）", not cs.flags)
    cs = one("最近購買日", pd.Series(pd.to_datetime(["2011-06-29"] * n)),
             check_time_availability, as_of, 3)
    check("② 入庫延遲 3 天 → 落在延遲窗內的欄位出 warning",
          "warning" in buckets(cs, "②時間可得性"))
    cs = one("最近購買日", pd.Series(pd.to_datetime(["2011-06-01"] * n)),
             check_time_availability, as_of, 3)
    check("② 延遲窗外的日期不亂叫", not cs.flags)

    # ── ③ 事後欄位語意 ───────────────────────────────────────
    cs = one("本期回購金額", pd.Series(rng.normal(0, 1, n)), check_posthoc_semantics)
    check("③ 抓到『本期回購金額』", "warning" in buckets(cs))
    cs = one("是否已喚回", pd.Series(rng.choice([0, 1], n)), check_posthoc_semantics)
    check("③ 抓到『是否已喚回』", "warning" in buckets(cs))
    cs = one("最近一次購買日距今天數", pd.Series(rng.integers(1, 300, n)),
             check_posthoc_semantics)
    check("③ 沒有誤判合法的 Recency 特徵", not cs.flags)
    cs = one("年齡", pd.Series(rng.integers(20, 70, n)), check_posthoc_semantics)
    check("③ 沒有誤判人口統計欄", not cs.flags)

    # ── ④ 常數與近常數 ───────────────────────────────────────
    cs = one("幣別", pd.Series(["TWD"] * n), check_constant)
    check("④ 抓到常數欄", "warning" in buckets(cs))
    near = ["A"] * (n - 4) + ["B"] * 4           # 99.5%
    cs = one("通路", pd.Series(near), check_constant)
    check("④ 抓到 99.5% 近常數欄", "warning" in buckets(cs),
          f"top1={cs.top1佔比:.4f}")
    near2 = ["A"] * int(n * 0.98) + ["B"] * (n - int(n * 0.98))
    cs = one("通路", pd.Series(near2), check_constant)
    check("④ 98% 不誤判（門檻是 99%，不是『看起來很不平衡』）", not cs.flags,
          f"top1={cs.top1佔比:.4f}")

    # ── ⑤ 覆蓋率 ─────────────────────────────────────────────
    v = pd.Series(rng.normal(0, 1, n))
    low = v.copy(); low[rng.choice(n, int(n * 0.75), replace=False)] = np.nan
    cs = one("CAI", low, check_coverage, COVERAGE_MIN)
    check("⑤ 抓到覆蓋率 25% 的欄", "warning" in buckets(cs),
          f"覆蓋率 {cs.覆蓋率:.1%}")
    hi = v.copy(); hi[rng.choice(n, int(n * 0.05), replace=False)] = np.nan
    cs = one("CRI", hi, check_coverage, COVERAGE_MIN)
    check("⑤ 沒有誤判覆蓋率 95% 的欄", not cs.flags, f"覆蓋率 {cs.覆蓋率:.1%}")
    edge_cov = v.copy(); edge_cov[rng.choice(n, int(n * 0.70), replace=False)] = np.nan
    cs = one("邊界", edge_cov, check_coverage, COVERAGE_MIN)
    check("⑤ 恰好 30% 不叫（門檻是 <，不是 <=）", not cs.flags,
          f"覆蓋率 {cs.覆蓋率:.1%}")

    # ── ⑥ 目標關聯 ───────────────────────────────────────────
    y = (rng.random(n) < 0.25).astype(float)
    leak = y * 100 + rng.normal(0, 1, n)          # 標籤的線性函數
    cs = one("已成交金額", pd.Series(leak), check_target_assoc, y, "binary")
    check("⑥ 抓到洩漏欄（教材原例：用已成交金額預測是否成交）",
          "error" in buckets(cs, "⑥目標關聯"),
          f"AUC={next(f.事實 for f in cs.flags).split('=')[1][:6]}")
    weak = y * 0.6 + rng.normal(0, 1.6, n)        # 有訊號但不是答案
    cs = one("近90天金額", pd.Series(weak), check_target_assoc, y, "binary")
    check("⑥ 沒有誤判「有訊號但不是答案」的正常特徵",
          buckets(cs, "⑥目標關聯") == {"info"},
          f"桶={buckets(cs, '⑥目標關聯')}")
    noise = pd.Series(rng.normal(0, 1, n))
    cs = one("年齡", noise, check_target_assoc, y, "binary")
    check("⑥ 沒有誤判純噪音欄", buckets(cs, "⑥目標關聯") == {"info"})
    hi_card = pd.Series([f"C{i}" for i in range(n)])
    cs = one("活動代碼", hi_card, check_target_assoc, y, "binary")
    check("⑥ 高基數類別欄不因 in-sample 目標編碼被誤判成洩漏"
          "（out-of-fold 有生效）",
          "error" not in buckets(cs, "⑥目標關聯"),
          "；".join(f.事實.split("：")[-1] for f in cs.flags) or "無 flag")
    cat_leak = pd.Series(np.where(y > 0.5, "回應", "未回應"))
    cs = one("回應狀態", cat_leak, check_target_assoc, y, "binary")
    check("⑥ 抓到類別型的洩漏欄", "error" in buckets(cs, "⑥目標關聯"))

    yc = rng.normal(0, 1, n)                       # 連續標籤
    cs = one("本期營收", pd.Series(yc * 3 + rng.normal(0, 0.01, n)),
             check_target_assoc, yc, "continuous")
    check("⑥ 連續標籤用 |Spearman| 也抓得到",
          "error" in buckets(cs, "⑥目標關聯"))
    cs = one("年齡", pd.Series(rng.normal(0, 1, n)),
             check_target_assoc, yc, "continuous")
    check("⑥ 連續標籤下不誤判無關欄",
          buckets(cs, "⑥目標關聯") == {"info"})

    # 缺值型態
    only_pos = pd.Series(np.where(y > 0.5, rng.normal(5, 1, n), np.nan))
    cs = one("喚回券使用日距今", only_pos, check_missing_pattern, y, "binary")
    check("⑥ 抓到「只有正類才有值」的缺值型態", "warning" in buckets(cs))
    rand_na = v.copy(); rand_na[rng.choice(n, int(n * 0.3), replace=False)] = np.nan
    cs = one("隨機缺值欄", rand_na, check_missing_pattern, y, "binary")
    check("⑥ 沒有誤判隨機缺值欄", not cs.flags)
    cs = one("全有值欄", pd.Series(rng.normal(0, 1, n)),
             check_missing_pattern, y, "binary")
    check("⑥ 全有值的欄不進缺值檢查", not cs.flags)

    # ── ⑦ 哨兵值 ─────────────────────────────────────────────
    gap_days = rng.integers(1, 30, n).astype(float)
    gap_days[rng.choice(n, 100, replace=False)] = 9999      # 04 §4.1 Q2 的實測長相
    cs = one("平均購買間隔", pd.Series(gap_days), check_sentinel)
    check("⑦ 抓到混進購買間隔的 9999", "error" in buckets(cs))
    real = pd.Series(rng.integers(9000, 10000, n).astype(float))
    cs = one("刷卡金額", real, check_sentinel)
    check("⑦ 沒有誤判「最大值恰好是 9999 但沒有斷崖」的真值欄",
          not cs.flags, f"max={real.max():.0f}")
    zeros = pd.Series(np.where(rng.random(n) < 0.4, 0.0, rng.normal(500, 100, n)))
    cs = one("退貨金額", zeros, check_sentinel)
    check("⑦ 沒有把合法的 0 當哨兵（0 不進掃描集）", not cs.flags)
    cs = one("生日", pd.Series(pd.to_datetime(["1900-01-01"] * 20
                                              + ["1980-05-05"] * (n - 20))),
             check_sentinel)
    check("⑦ 抓到日期哨兵 1900-01-01", "error" in buckets(cs))
    cs = one("刷卡日", pd.Series(pd.to_datetime(["2011-01-05"] * n)), check_sentinel)
    check("⑦ 沒有誤判正常日期欄", not cs.flags)
    cs = one("品類", pd.Series(["6666"] * 10 + ["烘焙"] * (n - 10)), check_sentinel)
    check("⑦ 抓到文字型哨兵 \"6666\"（10 §5 的假品類）", "error" in buckets(cs))
    cs = one("品類", pd.Series(rng.choice(["烘焙", "生鮮", "日用"], n)), check_sentinel)
    check("⑦ 沒有誤判正常類別欄", not cs.flags)
    neg = rng.integers(1, 50, n).astype(float)
    neg[rng.choice(n, 30, replace=False)] = -999
    cs = one("最近購買天數", pd.Series(neg), check_sentinel)
    check("⑦ 抓到負向哨兵 -999", "error" in buckets(cs))

    # ── 標籤檢查 ─────────────────────────────────────────────
    _reset_buckets()
    dfl = pd.DataFrame({"y": np.r_[np.ones(30), np.zeros(30)]})
    check_label(dfl, ["y"])
    check("標籤：有標籤樣本 60 < 100 → error（12 §一）", len(_errors) == 1,
          f"errors={len(_errors)}")
    _reset_buckets()
    dfl = pd.DataFrame({"y": np.r_[np.ones(200), np.zeros(800)]})
    check_label(dfl, ["y"])
    check("標籤：200 正類 / 1000 筆 → 不叫", not _errors and not _warnings,
          f"errors={len(_errors)}, warnings={len(_warnings)}")
    _reset_buckets()
    check_label(pd.DataFrame({"y": np.ones(500)}), ["y"])
    check("標籤：常數標籤 → error", len(_errors) == 1)
    _reset_buckets()

    # ── 整表：退出碼三態 ─────────────────────────────────────
    clean_df = pd.DataFrame({
        "年齡": rng.integers(20, 70, n),
        "近90天金額": rng.normal(1000, 300, n).round(2),
        "性別": rng.choice(["男", "女"], n),
        "y": (rng.random(n) < 0.3).astype(int),
    })
    yb = to_binary(clean_df["y"])
    sc = scan(clean_df, as_of, ["y"], [], set(), y_num=yb, kind="binary")
    worst = {c.最重桶 for c in sc if c.角色 == "特徵"}
    check("整表：乾淨的表沒有 error / warning", worst <= {"pass", "info"},
          f"桶={sorted(worst)}")

    dirty_df = clean_df.copy()
    dirty_df["客戶編號"] = np.arange(n)
    dirty_df["幣別"] = "TWD"
    dirty_df["已成交金額"] = yb * 100 + rng.normal(0, 1, n)
    sc2 = scan(dirty_df, as_of, ["y"], ["客戶編號"], set(), y_num=yb, kind="binary")
    by = {c.欄位: c for c in sc2}
    check("整表：客戶編號 → 排除", by["客戶編號"].最重桶 == "warning")
    check("整表：幣別常數 → 排除", by["幣別"].最重桶 == "warning")
    check("整表：已成交金額 → 擋住", by["已成交金額"].最重桶 == "error")
    check("整表：年齡仍然乾淨（沒有被鄰居連坐）",
          by["年齡"].最重桶 in ("pass", "info"))
    check("整表：標籤欄不進掃描", by["y"].角色 == "標籤" and not by["y"].flags)

    # --reviewed 放行
    sc3 = scan(dirty_df, as_of, ["y"], ["客戶編號"], {"已成交金額"},
               y_num=yb, kind="binary")
    by3 = {c.欄位: c for c in sc3}
    check("--reviewed 把 error 降成 info，且留痕",
          by3["已成交金額"].最重桶 == "info"
          and any("已由 --reviewed 放行" in f.怎麼辦 for f in by3["已成交金額"].flags))
    check("--reviewed 只放行指定欄，不會順手放行別人",
          by3["客戶編號"].最重桶 == "warning")

    # ── 表 11.4 ──────────────────────────────────────────────
    tbl = build_table_114(sc2, as_of)
    need = ["欄位", "as_of_date", "計算窗", "洩漏風險", "判定", "該怎麼辦"]
    check("表 11.4 欄位齊全（19 §1.7：欄名／計算窗／有無洩漏風險）",
          all(c in tbl.columns for c in need),
          "缺 " + "、".join(c for c in need if c not in tbl.columns) or "無缺")
    check("表 11.4 每一列都有 as_of_date",
          tbl["as_of_date"].eq(str(as_of)).all())
    # itertuples 會把「覆蓋率(%)」改成位置代號 _7，欄序一動就對到別欄。
    # 這裡示範並驗證：一律用欄名取值。
    row = tbl.loc[tbl["欄位"] == "已成交金額"].iloc[0]
    check("表 11.4 用欄名取到含 % 與括號的欄（不用 itertuples）",
          isinstance(row["覆蓋率(%)"], (int, float, np.floating))
          and row["洩漏風險"].startswith("高"),
          f"覆蓋率(%)={row['覆蓋率(%)']}, 洩漏風險={row['洩漏風險']}")
    fields = list(tbl.head(1).itertuples(index=False))[0]._fields
    check("itertuples 確實把「覆蓋率(%)」改成位置代號（所以規約要求用欄名）",
          "覆蓋率(%)" not in fields and any(f.startswith("_") for f in fields),
          f"itertuples 產出的欄名={fields[6:8]}")
    check("每一條 error / warning 都有『該怎麼辦』",
          all(f.怎麼辦.strip() for cs in sc2 for f in cs.flags
              if f.桶 in ("error", "warning")))

    # ── 人工複核清單 ─────────────────────────────────────────
    rev = build_review_list(sc2, as_of)
    check("人工複核清單有列出疑似洩漏欄", len(rev) and "已成交金額" in set(rev["欄位"]))
    rev_clean = build_review_list(sc, as_of)
    check("乾淨的表不產生人工複核項目", len(rev_clean) == 0, f"{len(rev_clean)} 條")

    # ── 門檻敏感度 ───────────────────────────────────────────
    sens_df = pd.DataFrame({
        "四成基數": rng.choice(np.arange(int(n * 0.4)), n),   # ratio≈0.4
        "全唯一": np.arange(n),                                # ratio=1.0
        "兩類": rng.choice(["A", "B"], n),                     # ratio≈0.002
        "y": yb,
    })
    sc4 = scan(sens_df, as_of, ["y"], [], set(), y_num=yb, kind="binary")
    sens = sensitivity_table(sc4)
    g = {r["欄位"]: r for _, r in sens.iterrows()}
    check("敏感度：ratio≈0.4 的欄判定會隨門檻改變",
          g["四成基數"]["判定隨門檻改變"] == "是",
          f"ratio={g['四成基數']['unique_ratio']}")
    check("敏感度：ratio=1.0 的欄三個門檻都排除（不會假報敏感）",
          g["全唯一"]["判定隨門檻改變"] == "否")
    check("敏感度：兩類欄三個門檻都保留", g["兩類"]["判定隨門檻改變"] == "否")

    # ── JSON 序列化 ──────────────────────────────────────────
    payload = {
        "columns": [{"欄位": cs.欄位, "unique": cs.unique,
                     "unique_ratio": cs.unique_ratio,
                     "覆蓋率": cs.覆蓋率, "top1佔比": cs.top1佔比,
                     "值域": cs.值域,
                     "flags": [f.__dict__ for f in cs.flags]} for cs in sc2],
        "表11.4": tbl.to_dict(orient="records"),
        "as_of": as_of,
    }
    try:
        json.dumps(payload, ensure_ascii=False, default=_json_default)
        ser_ok, ser_msg = True, "含 numpy 純量與 date 仍可序列化"
    except TypeError as e:
        ser_ok, ser_msg = False, str(e)
    check("結果可寫成 JSON（numpy 純量／date 不外洩）", ser_ok, ser_msg)
    check("unique 已轉成原生 int",
          all(type(_py(cs.unique)) is int for cs in sc2))

    # ── 關聯度工具本身 ───────────────────────────────────────
    xx = np.arange(200, dtype=float)
    yy = (xx >= 100).astype(float)
    check("auc_binary 完美分離回 1.0", abs(auc_binary(xx, yy) - 1.0) < 1e-9)
    check("auc_binary 反向完美分離也回 1.0（取對稱值）",
          abs(auc_binary(-xx, yy) - 1.0) < 1e-9)
    rand_auc = auc_binary(rng.normal(0, 1, 4000), (rng.random(4000) < 0.3).astype(float))
    check("auc_binary 對隨機資料回 ~0.5", 0.5 <= rand_auc < 0.56, f"{rand_auc:.4f}")
    check("auc_binary 樣本不足回 None",
          auc_binary(np.arange(10.0), np.r_[np.ones(5), np.zeros(5)]) is None)
    check("spearman_abs 單調關係回 1.0",
          abs(spearman_abs(xx, xx ** 3) - 1.0) < 1e-9)

    print("\n" + "=" * 74)
    if failed:
        print(f"⛔ {len(failed)}／{total[0]} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print(f"✅ 自我測試全部通過（{total[0]} 項）")
    return EX_OK


# ══════════════════════════════════════════════════════════════
def parse_as_of(v: str) -> date:
    """--as-of 的值。格式不合法要在 argparse 層擋（→64），不要掉到執行期變成 1。"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"as_of 格式不對：{v}（要 YYYY-MM-DD）")


def main() -> int:
    ap = GateArgumentParser(
        description="建模前的欄位掃描（12 §七），輸出直接進表 11.4。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--as-of", help="特徵窗切點 YYYY-MM-DD。表 11.4 規定要記它")
    ap.add_argument("--label", help="標籤欄名（逗號分隔可多個，第一個為主標籤）")
    ap.add_argument("--table", type=Path,
                    help="建模表（預設 顧客特徵表/feat_customer_asof<as_of>.parquet）")
    ap.add_argument("--id-col", help="顧客／分組鍵欄名（逗號分隔）。"
                                     "排除出特徵集，但保留給 GroupKFold")
    ap.add_argument("--reviewed", help="已人工複核並確認可用的欄名（逗號分隔），"
                                       "把它們的 error/warning 降成 info 並留痕")
    ap.add_argument("--coverage-min", type=float, default=COVERAGE_MIN,
                    help=f"覆蓋率門檻（預設 {COVERAGE_MIN}，出處 12 §七 + 00 §五）")
    ap.add_argument("--unique-ratio-max", type=float, default=UNIQUE_RATIO_MAX,
                    help=f"高基數門檻（預設 {UNIQUE_RATIO_MAX}，"
                         f"12 §七 標【推導，待驗證】）")
    ap.add_argument("--ingest-lag-days", type=int, default=0,
                    help="資料入庫延遲天數（POS T+1／廣告 T+3／退貨 T+30，12 §二）")
    ap.add_argument("--no-write", action="store_true", help="只檢查，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()

    # ── 值不合法一律在這裡擋 → 64。掉到 run() 會被判成 1（資料側問題），
    #    但這幾條根本還沒碰到資料。
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")
    if not args.as_of:
        ap.error("要給 --as-of YYYY-MM-DD —— 表 11.4 規定每一欄都要記 as_of_date"
                 "（19 §1.7），沒有它這張表交不出去")
    if not args.label:
        ap.error("要給 --label <標籤欄名> —— 12 §七 的 scan(df, as_of, label_cols) "
                 "把標籤當必填；沒有標籤就沒有『⑥ 與目標的可疑高關聯』這一關")
    try:
        args.as_of = parse_as_of(args.as_of)
    except ValueError as e:
        ap.error(str(e))
    if not 0.0 <= args.coverage_min <= 1.0:
        ap.error(f"--coverage-min 要在 0–1 之間（收到 {args.coverage_min}）；"
                 f"12 §七 的值是 0.30")
    if not 0.0 < args.unique_ratio_max <= 1.0:
        ap.error(f"--unique-ratio-max 要在 (0, 1] 之間（收到 {args.unique_ratio_max}）；"
                 f"12 §七 的值是 0.5")
    if args.ingest_lag_days < 0:
        ap.error(f"--ingest-lag-days 不能是負數（收到 {args.ingest_lag_days}）；"
                 f"它是資料入庫延遲，方向只能往前推")

    try:
        return run(args)
    except FileNotFoundError as e:
        print(f"\n⛔ {e}", file=sys.stderr)
        print(f"   退出碼 {EX_ERROR} —— 補齊檔案後重跑。", file=sys.stderr)
        return EX_ERROR
    except ValueError as e:
        print(f"\n⛔ {e}", file=sys.stderr)
        print(f"   退出碼 {EX_ERROR} —— 資料／參數的問題，不是腳本壞了。",
              file=sys.stderr)
        return EX_ERROR


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ scan_columns.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
