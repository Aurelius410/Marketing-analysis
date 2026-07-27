#!/usr/bin/env python3
"""
顧客特徵表的**唯一介面** —— 所有顧客層指標都從這裡出，不准在分析腳本裡就地手寫。

為什麼需要它（不寫理由的腳本沒人會用）：

  1. **防目標洩漏（18-G4）**。`as_of` 是必填參數，沒有它不准產生特徵。
     用全期交易算 RFM 再拿去預測「這一期會不會流失」，驗證集 AUC 0.95、上線崩盤。
     這支腳本產生的每一條 SQL 都強制帶 `WHERE biz_date <= as_of`，
     而且有一道 `_exec_guarded()` 守門，忘記加就直接擋下來，不會靜默算錯。

  2. **防公式抄錯（18-E8）**。17 §5 明訂：任何指標都不准在分析腳本裡就地手寫公式。
     公式散在各處被逐份手抄，一旦某處寫成 `BE = w1·GE × w2·IE`（應為加號），
     錯誤會一路傳到結論而且**不會報錯**。這裡是 17 那份規格書的唯一實作。

  3. **防退貨污染（18-G2）**。每條 SQL 同時強制帶 `AND txn_type = 'sale'`。
     少了它，退貨列會把 R 算成「最近極活躍」，一年沒買的人收到 VIP 禮。

  4. **雙路徑交叉驗算（00 §1.3）**。F、M、CRI、RFM 分位、MLE 各有兩條走不同中間量的
     算法，任何一邊分母寫錯兩邊就不會相等。這是免費的斷言 —— 不一致直接 raise，
     不是印個警告讓你自己決定要不要理。

用法：

    # 命令列（三桶 + 退出碼 0/1/2）
    python build_features.py 2026Q3_電商 --as-of 2012-12-01
    python build_features.py 課程驗證 --as-of 2012-12-01 \
        --source ".../ntu_creditcard__transactions.parquet" \
        --dim ".../ntu_creditcard__customers.parquet" \
        --prior-group-cols 性別 --benchmark

    # Python
    from build_features import build_features
    res = build_features("2026Q3_電商", as_of="2012-12-01")
    res.features        # DataFrame，一列一位顧客
    res.checks          # 雙路徑驗算結果（含 max_abs_diff）

退出碼：0 = 全通過｜1 = 有 error（驗算不符／缺必要欄位），特徵表不可用｜
        2 = 只有 warning（如缺 txn_type、先驗群過小），特徵表可用但要在報告註明。

規格出處：17 §一～§五（公式與去重）、18-G4（唯一介面）、00 §1.3（雙路徑）、
          09 §2.1（CRI 的先驗與變異數口徑）、09 §2.2（Bob Stone 不給預設值）。
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect  # noqa: E402
from paths import project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
# 常數
# ══════════════════════════════════════════════════════════════════

# 00 §1.3 的容差。代數等價要到 1e-9（float64 十來次四則運算的累積尾差量級），
# 含迭代或最佳化放寬到 1e-6，整數計數要求完全相等。
EPS = 1e-12
TOL_ALGEBRAIC = 1e-9
TOL_ITERATIVE = 1e-6

# 欄名別名。canonical 欄名以 02 §3.3 的 fact_transaction DDL 為準。
_ALIASES: dict[str, tuple[str, ...]] = {
    "person_key": ("person_key", "cust_id", "customer_id", "客戶ID", "客戶id",
                   "顧客ID", "會員ID", "會員id"),
    "biz_date": ("biz_date", "txn_date", "刷卡日期", "交易日期", "消費日期",
                 "營業日", "營業日期"),
    "amount_twd": ("amount_twd", "amount", "刷卡金額", "交易金額", "金額", "消費金額"),
    "txn_type": ("txn_type", "交易類型", "交易型態", "交易別"),
    # ⚠ 「刷卡類型」刻意**不**列為 txn_type 的別名 —— 它的值是「一般消費／分期消費」，
    #   講的是有沒有分期，不是 sale/return/void。誤映會讓所有列都被 txn_type='sale'
    #   濾光，特徵表整張空掉。這正是 18-G2 反過來咬人的版本。
}

# 17 §3.2 原版 Bob Stone 的 R 級距。(上界含, 分數)
_BOBSTONE_R_BINS: tuple[tuple[float, float], ...] = (
    (90, 24), (180, 12), (270, 6), (360, 3), (math.inf, 0),
)
_BOBSTONE_F_MULT = 4.0
_BOBSTONE_M_RATE = 0.0025
_BOBSTONE_M_CAP = 9.0

# 17 §八 的 ground truth。--benchmark 用，改公式後拿它照一次。
BENCHMARK = {
    "客戶 89 R": (89, "r_days_since_last_sale", 19, 0),
    "客戶 89 f_txn_cnt": (89, "f_txn_cnt", 85, 0),
    "客戶 89 f_active_days": (89, "f_active_days", 69, 0),
    "客戶 89 M": (89, "m_net_twd", 150681, 0),
    "客戶 89 MLE": (89, "mle", 10.279412, 5e-7),
    "客戶 89 WMLE": (89, "wmle", 11.570759, 5e-7),
    "客戶 89 CAI": (89, "cai", -12.562460, 5e-7),
    "客戶 89 間隔數": (89, "interval_cnt", 68, 0),
    "客戶 106 R": (106, "r_days_since_last_sale", 8, 0),
    "客戶 106 F": (106, "f_txn_cnt", 75, 0),
    "客戶 106 M": (106, "m_net_twd", 90192, 0),
    "客戶 131 R": (131, "r_days_since_last_sale", 401, 0),
    "客戶 131 F": (131, "f_txn_cnt", 16, 0),
    "客戶 131 M": (131, "m_net_twd", 69558, 0),
    "客戶 605 MLE": (605, "mle", 2.296530, 5e-7),
}
BENCHMARK_ROWS = {"原始交易": 7764, "去重後": 5294, "間隔數": 5194}
BENCHMARK_CAI_RANGE = (-43.665943, 54.590571)


# ══════════════════════════════════════════════════════════════════
# 資料結構
# ══════════════════════════════════════════════════════════════════

class FeatureBuildError(RuntimeError):
    """特徵表產不出來，或雙路徑驗算不符。訊息一律「事實 — 該怎麼辦」兩段式。"""


@dataclass(frozen=True)
class CrossCheck:
    """一次雙路徑交叉驗算的結果（00 §1.3 硬規則：要連 max_abs_diff 一起留檔）。"""
    metric: str
    path_a: str
    path_b: str
    kind: str               # "整數" | "代數等價" | "迭代" | "分位"
    n_compared: int
    max_abs_diff: float
    max_rel_diff: float
    passed: bool
    detail: str = ""

    @property
    def tolerance(self) -> float:
        return {"整數": 0.0, "代數等價": TOL_ALGEBRAIC,
                "迭代": TOL_ITERATIVE, "分位": 1.0}[self.kind]

    def line(self) -> str:
        mark = "✅" if self.passed else "⛔"
        return (f"{mark} {self.metric}：{self.path_a} vs {self.path_b}"
                f"（{self.kind}，n={self.n_compared}，"
                f"max_abs_diff={self.max_abs_diff:.3e}，"
                f"max_rel_diff={self.max_rel_diff:.3e}，"
                f"容差={self.tolerance:g}）"
                + (f"｜{self.detail}" if self.detail else ""))


@dataclass
class BobStoneCustom:
    """自訂 Bob Stone 參數。

    17 §3.3 與 09 §2.2 的硬規則：**不給預設值**，而且權重必須附產業論證。
    只給權重不給理由 = 核心致命傷。所以 `reasons` 三個構面缺一就 raise。
    """
    r_bins: Sequence[tuple[float, float]]   # [(上界天數含, 分數), ...]，最後一格用 inf
    f_multiplier: float
    m_rate: float
    m_cap: float
    weights: dict[str, float]               # {"R":…, "F":…, "M":…}
    reasons: dict[str, str]                 # 三段產業論證，缺一不可

    def __post_init__(self) -> None:
        for d in ("R", "F", "M"):
            if d not in self.weights:
                raise FeatureBuildError(
                    f"自訂 Bob Stone 缺少 {d} 的權重 — "
                    f"weights 必須同時給 R/F/M 三個構面（17 §3.3）")
            r = (self.reasons or {}).get(d, "").strip()
            if len(r) < 10:
                raise FeatureBuildError(
                    f"自訂 Bob Stone 的 {d} 權重沒有寫理由（目前 {len(r)} 字）— "
                    f"17 §3.3 明訂「只給權重不給理由 = 核心致命傷」。"
                    f"請在 reasons['{d}'] 寫一段產業特性論證"
                    f"（例：信用卡帳單週期 30 天，故 R 首階門檻取 30 天）")
        if not self.r_bins or self.r_bins[-1][0] != math.inf:
            raise FeatureBuildError(
                "自訂 Bob Stone 的 r_bins 最後一格上界必須是 math.inf — "
                "否則 R 超出最後級距的顧客會拿不到分數（靜默變 NaN）")


@dataclass
class BuildResult:
    """`build_features()` 的完整回傳。"""
    features: pd.DataFrame
    as_of: date
    checks: list[CrossCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    written: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors and all(c.passed for c in self.checks)


# ══════════════════════════════════════════════════════════════════
# SQL 守門：兩個「不可省」的 WHERE 條件（17 §一、§二）
# ══════════════════════════════════════════════════════════════════

_ASOF_GUARD = re.compile(r"biz_date\s*<=\s*DATE\s*'\d{4}-\d{2}-\d{2}'", re.I)
_SALE_GUARD = re.compile(r"txn_type\s*=\s*'sale'", re.I)


def _exec_guarded(con: Any, sql: str, *, need_sale: bool = True) -> Any:
    """跑一條讀交易明細的 SQL，先驗兩個不可省的條件都在。

    這不是裝飾用的。17 §一寫得很清楚：少了 `txn_type='sale'`，退貨列會進間隔計算，
    MLE/WMLE/CAI 全部被污染；少了 as_of，特徵就含未來資訊（18-G4）。
    這兩種錯都**不會報錯**，只會給你一組看起來很合理的數字。
    """
    if not _ASOF_GUARD.search(sql):
        raise FeatureBuildError(
            "產生的 SQL 沒有 `WHERE biz_date <= DATE '…'` — "
            "這是 18-G4 目標洩漏的直接成因，擋下不執行。"
            "請檢查 build_features.py 裡組這條 SQL 的地方：\n" + sql[:400])
    if need_sale and not _SALE_GUARD.search(sql):
        raise FeatureBuildError(
            "產生的 SQL 沒有 `AND txn_type = 'sale'` — "
            "退貨列會沉默地污染 R 與購買間隔（18-G2），擋下不執行。"
            "若這條查詢是刻意要算毛額，請用 need_sale=False 明示：\n" + sql[:400])
    return con.execute(sql)


# ══════════════════════════════════════════════════════════════════
# 來源解析與欄名正規化
# ══════════════════════════════════════════════════════════════════

def _sql_path(p: Path) -> str:
    return str(p.resolve().as_posix()).replace("'", "''")


def _scan_expr(source: str | Path | None) -> str:
    """把來源變成可以放進 FROM 的片段。None → 倉儲裡的 fact_transaction。"""
    if source is None:
        return "fact_transaction"
    p = Path(source)
    if p.exists():
        suf = p.suffix.lower()
        if suf == ".parquet":
            return f"read_parquet('{_sql_path(p)}')"
        if suf in (".csv", ".txt"):
            return f"read_csv_auto('{_sql_path(p)}')"
        raise FeatureBuildError(
            f"不認得的來源副檔名：{p.suffix} — "
            f"支援 .parquet / .csv，或不給 --source 直接讀倉儲的 fact_transaction")
    # 不是檔案就當成資料表名
    return str(source)


def _quote(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def _detect_columns(
    con: Any, scan: str, override: dict[str, str] | None,
) -> tuple[dict[str, str], list[str], list[str]]:
    """把來源欄位對到 canonical 欄名。回傳 (對照表, warnings, infos)。"""
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {scan}").fetchall()]
    lower = {c.lower(): c for c in cols}
    mapping: dict[str, str] = {}
    warns: list[str] = []
    infos: list[str] = []

    for canon, cands in _ALIASES.items():
        if override and canon in override:
            want = override[canon]
            if want not in cols:
                raise FeatureBuildError(
                    f"--colmap 指定 {canon}={want}，但來源沒有這一欄 — "
                    f"來源實際欄位：{', '.join(cols)}")
            mapping[canon] = want
            continue
        for cand in cands:
            if cand in cols:
                mapping[canon] = cand
                break
            if cand.lower() in lower:
                mapping[canon] = lower[cand.lower()]
                break

    for must in ("person_key", "biz_date", "amount_twd"):
        if must not in mapping:
            raise FeatureBuildError(
                f"來源找不到 {must} 對應的欄位 — "
                f"來源實際欄位：{', '.join(cols)}。"
                f"用 --colmap {must}=<欄名> 指定，或先在 M3 把欄名對齊 02 §3.3 的 DDL")

    if "txn_type" not in mapping:
        warns.append(
            "來源沒有 txn_type 欄，全部列視為 sale — "
            "退貨／沖銷邏輯在這批資料上**無法被驗證**（17 §八）。"
            "若原始系統其實有退貨列，請補上該欄再重跑，否則 M 會虛胖、R 會偏近（18-G2）")

    infos.append("欄名對照：" + "、".join(
        f"{k}←{v}" for k, v in mapping.items()) +
        ("、txn_type←(缺，補 'sale')" if "txn_type" not in mapping else ""))
    return mapping, warns, infos


def _normalize(con: Any, scan: str, mapping: dict[str, str]) -> None:
    """建 stg_txn_norm：canonical 欄名的交易明細層。這是後面所有 SQL 的唯一入口。"""
    type_expr = (f"lower(CAST({_quote(mapping['txn_type'])} AS VARCHAR))"
                 if "txn_type" in mapping else "'sale'")
    con.execute(f"""
        CREATE OR REPLACE TABLE stg_txn_norm AS
        SELECT
            CAST({_quote(mapping['person_key'])} AS BIGINT)  AS person_key,
            CAST({_quote(mapping['biz_date'])}   AS DATE)    AS biz_date,
            CAST({_quote(mapping['amount_twd'])} AS DOUBLE)  AS amount_twd,
            {type_expr}                                      AS txn_type
        FROM {scan}
    """)


# ══════════════════════════════════════════════════════════════════
# 各段指標（照 17 的公式，不自己發明）
# ══════════════════════════════════════════════════════════════════

def _rfm_sql(con: Any, as_of: date) -> pd.DataFrame:
    """17 §二：R/F/M。欄名一律帶口徑後綴，禁止裸 F / M。"""
    return _exec_guarded(con, f"""
        SELECT
            person_key AS cust_id,
            DATE_DIFF('day', MAX(biz_date), DATE '{as_of}') AS r_days_since_last_sale,
            COUNT(*)                                        AS f_txn_cnt,
            COUNT(DISTINCT biz_date)                        AS f_active_days,
            SUM(amount_twd)                                 AS m_net_twd,
            MIN(biz_date)                                   AS first_sale_date,
            MAX(biz_date)                                   AS last_sale_date,
            DATE_DIFF('day', MIN(biz_date), DATE '{as_of}') AS tenure_days
        FROM stg_txn_norm
        WHERE biz_date <= DATE '{as_of}'
          AND txn_type = 'sale'
        GROUP BY person_key
        ORDER BY person_key
    """).df()


def _gross_sql(con: Any, as_of: date) -> pd.DataFrame:
    """18-G2 要求同時輸出毛額版供對照。這條**刻意**不帶 txn_type 過濾。"""
    return _exec_guarded(con, f"""
        SELECT person_key AS cust_id,
               SUM(amount_twd) AS m_gross_twd,
               COUNT(*)        AS txn_cnt_all_types
        FROM stg_txn_norm
        WHERE biz_date <= DATE '{as_of}'
        GROUP BY person_key
    """, need_sale=False).df()


def _customer_day(con: Any, as_of: date) -> None:
    """17 §一：以「顧客 + 營業日」去重，壓成一天一列。做錯這步後面全錯。"""
    _exec_guarded(con, f"""
        CREATE OR REPLACE TABLE stg_customer_day AS
        SELECT DISTINCT
            person_key AS cust_id,
            biz_date   AS txn_date
        FROM stg_txn_norm
        WHERE biz_date <= DATE '{as_of}'
          AND txn_type = 'sale'
    """)


def _cai_sql(con: Any) -> pd.DataFrame:
    """17 §4.2 的完整六步。分母是間隔數 m_i = n_i − 1，不是購買次數 n_i。

    讀的是 stg_customer_day（已帶 as_of 與 sale 過濾），故這條不再重複守門。
    """
    return con.execute("""
        WITH d AS (
            SELECT cust_id, txn_date,
                   ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY txn_date) AS seq,
                   LEAD(txn_date) OVER (PARTITION BY cust_id ORDER BY txn_date) AS next_date
            FROM stg_customer_day
        ),
        w AS (
            SELECT cust_id, seq AS weight,
                   DATE_DIFF('day', txn_date, next_date) AS interval_days
            FROM d WHERE next_date IS NOT NULL
        )
        SELECT cust_id,
               COUNT(*)                                  AS interval_cnt,
               AVG(interval_days)                        AS mle,
               SUM(weight * interval_days) / SUM(weight) AS wmle,
               (AVG(interval_days) - SUM(weight * interval_days) / SUM(weight))
                   / AVG(interval_days) * 100            AS cai
        FROM w GROUP BY cust_id ORDER BY cust_id
    """).df()


def _ntile_sql(con: Any) -> pd.DataFrame:
    """17 §3.1 五等分法（路徑 A：SQL NTILE）。

    ORDER BY 加上 cust_id 尾鍵讓平手時的切法可重現 —— 否則兩次執行可能給不同分數，
    而那種不穩定在報告上就是「同一份資料跑兩次結論不同」。
    """
    return con.execute("""
        SELECT cust_id,
            6 - NTILE(5) OVER (ORDER BY r_days_since_last_sale ASC, cust_id ASC) AS r_score,
            NTILE(5) OVER (ORDER BY f_txn_cnt ASC, cust_id ASC)                  AS f_score,
            NTILE(5) OVER (ORDER BY m_net_twd ASC, cust_id ASC)                  AS m_score
        FROM feat_rfm ORDER BY cust_id
    """).df()


def _ntile_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """路徑 B：17 §3.1 註明原 Excel 用 PERCENTRANK.INC + 五級對照。

    照那條路徑重做：先取升冪序位（平手以 cust_id 決定，與路徑 A 同一把尺），
    再 `ceil(序位 × 5 / n)`。這與 NTILE 的餘數分配規則**不同**，
    所以兩邊各組大小可以差 1 —— 這正是 00 §1.3 對這一項只要求「各組大小差 ≤1」的原因。
    """
    n = len(df)
    out = pd.DataFrame({"cust_id": df["cust_id"].to_numpy()})
    for col, name, reverse in (("r_days_since_last_sale", "r_score", True),
                               ("f_txn_cnt", "f_score", False),
                               ("m_net_twd", "m_score", False)):
        order = df.sort_values([col, "cust_id"], kind="mergesort").index.to_numpy()
        rank = np.empty(n, dtype=np.int64)
        rank[order] = np.arange(1, n + 1)
        score = np.ceil(rank * 5 / n).astype(np.int64)
        out[name] = (6 - score) if reverse else score
    return out


def _bobstone_original(rfm: pd.DataFrame) -> pd.DataFrame:
    """17 §3.2 原版 Bob Stone。"""
    r = rfm["r_days_since_last_sale"].to_numpy(dtype=float)
    f = rfm["f_txn_cnt"].to_numpy(dtype=float)
    m = rfm["m_net_twd"].to_numpy(dtype=float)

    r_score = np.full(len(r), np.nan)
    prev = -np.inf
    for upper, sc in _BOBSTONE_R_BINS:
        r_score = np.where((r > prev) & (r <= upper), sc, r_score)
        prev = upper
    r_score = np.where(r <= _BOBSTONE_R_BINS[0][0], _BOBSTONE_R_BINS[0][1], r_score)

    # 原文的自訂 R-score 變體 =INT(2^(4-INT(B3/90)))，宣稱值域 1~16。
    # 【此處為實作判斷】R ≥ 450 時指數變負、INT 後為 0，超出宣稱值域。
    # 照原式實作不做截斷，並在 infos 回報實際值域，讓使用者自己決定要不要改級距。
    r_variant = np.floor(np.power(2.0, 4.0 - np.floor(r / 90.0)))

    return pd.DataFrame({
        "cust_id": rfm["cust_id"].to_numpy(),
        "bs_r_score": r_score,
        "bs_f_score": _BOBSTONE_F_MULT * f,
        "bs_m_score": np.minimum(np.floor(_BOBSTONE_M_RATE * m), _BOBSTONE_M_CAP),
        "bs_r_score_variant": r_variant,
    }).assign(bs_total=lambda d: d.bs_r_score + d.bs_f_score + d.bs_m_score)


def _bobstone_custom(rfm: pd.DataFrame, spec: BobStoneCustom) -> pd.DataFrame:
    """17 §3.3 自訂 Bob Stone。權重與級距全部由呼叫端給，這裡不給任何預設值。"""
    r = rfm["r_days_since_last_sale"].to_numpy(dtype=float)
    f = rfm["f_txn_cnt"].to_numpy(dtype=float)
    m = rfm["m_net_twd"].to_numpy(dtype=float)

    r_score = np.full(len(r), np.nan)
    prev = -np.inf
    for upper, sc in spec.r_bins:
        r_score = np.where((r > prev) & (r <= upper), sc, r_score)
        prev = upper
    r_score = np.where(r <= spec.r_bins[0][0], spec.r_bins[0][1], r_score)

    f_score = spec.f_multiplier * f
    m_score = np.minimum(np.floor(spec.m_rate * m), spec.m_cap)
    total = (spec.weights["R"] * r_score + spec.weights["F"] * f_score
             + spec.weights["M"] * m_score)
    return pd.DataFrame({
        "cust_id": rfm["cust_id"].to_numpy(),
        "bsc_r_score": r_score, "bsc_f_score": f_score,
        "bsc_m_score": m_score, "bsc_total": total,
    })


def _prior_stats(con: Any, as_of: date, group_map: pd.DataFrame | None) -> pd.DataFrame:
    """09 §2.1 的 CRI 原料。

    τ²_g 與 μ_g 是**對該群的「交易列」**取變異數與平均（不是對顧客個人均值取）
    —— 這是包子 HW4 的口徑，兩種算法量級差很多，同一份報告不可混用。
    變異數一律 VAR_SAMP（ddof=1），對應 Excel 樞紐 subtotal="var"。
    """
    if group_map is None:
        return pd.DataFrame(columns=["cust_id", "prior_group", "n_i", "ie_xbar",
                                     "s2_i", "ge_mu_g", "tau2_g", "grp_n_cust"])
    con.register("df_group_map", group_map)
    rows = _exec_guarded(con, f"""
        SELECT t.person_key AS cust_id, g.prior_group, t.amount_twd
        FROM stg_txn_norm t
        JOIN df_group_map g ON g.cust_id = t.person_key
        WHERE t.biz_date <= DATE '{as_of}'
          AND t.txn_type = 'sale'
    """).df()
    if rows.empty:
        return pd.DataFrame(columns=["cust_id", "prior_group", "n_i", "ie_xbar",
                                     "s2_i", "ge_mu_g", "tau2_g", "grp_n_cust"])

    per_cust = (rows.groupby(["prior_group", "cust_id"], as_index=False)
                .agg(n_i=("amount_twd", "size"),
                     ie_xbar=("amount_twd", "mean"),
                     s2_i=("amount_twd", lambda s: s.var(ddof=1))))
    per_grp = (rows.groupby("prior_group", as_index=False)
               .agg(ge_mu_g=("amount_twd", "mean"),
                    tau2_g=("amount_twd", lambda s: s.var(ddof=1))))
    out = per_cust.merge(per_grp, on="prior_group", how="left")
    out["grp_n_cust"] = out.groupby("prior_group")["cust_id"].transform("size")
    return out[["cust_id", "prior_group", "n_i", "ie_xbar", "s2_i",
                "ge_mu_g", "tau2_g", "grp_n_cust"]]


def _shrinkage(pri: pd.DataFrame) -> pd.DataFrame:
    """17 §五 + 09 §2.1：貝氏收縮與 CRI。

    W1 = τ²_g / (τ²_g + s²_i/n_i)，W2 = 1 − W1，BE = W1·IE + W2·GE，
    CRI = (IE − BE)/(IE − GE) × 100 ≡ W2 × 100。

    【此處為實作判斷】17／09 都沒講 n_i = 1 或 s²_i 缺值時怎麼辦。
    這裡令 W1 = 0（個人均值只有一筆交易，不帶任何個體資訊）→ BE = GE、CRI = 100，
    語意上就是「完全被拉回群平均」，與 CRI↑ ⇔ 個人平均越不可信 的方向一致。
    """
    if pri.empty:
        return pri.assign(w1=np.nan, w2=np.nan, be_shrunk=np.nan,
                          cri=np.nan, be_precision=np.nan, cri_pathA=np.nan)
    n = pri["n_i"].to_numpy(dtype=float)
    xbar = pri["ie_xbar"].to_numpy(dtype=float)
    s2 = pri["s2_i"].to_numpy(dtype=float)
    mu = pri["ge_mu_g"].to_numpy(dtype=float)
    tau2 = pri["tau2_g"].to_numpy(dtype=float)

    se2 = np.where(n > 0, s2 / np.maximum(n, 1), np.nan)   # s²_i / n_i
    degenerate = ~np.isfinite(se2)                          # n_i = 1 → var 為 NaN
    se2_safe = np.where(degenerate, np.inf, se2)
    denom = tau2 + se2_safe
    w1 = np.where(denom > 0, tau2 / denom, np.nan)
    w1 = np.where(degenerate, 0.0, w1)
    w2 = 1.0 - w1

    be = w1 * xbar + w2 * mu                                # 路徑：加權平均式
    with np.errstate(divide="ignore", invalid="ignore"):
        be_prec = ((xbar * n / s2) + (mu / tau2)) / ((n / s2) + (1.0 / tau2))
        cri_a = (xbar - be) / (xbar - mu) * 100.0           # 路徑 A
    cri_b = w2 * 100.0                                      # 路徑 B

    return pri.assign(w1=w1, w2=w2, be_shrunk=be, be_precision=be_prec,
                      cri=cri_b, cri_pathA=cri_a)


# ══════════════════════════════════════════════════════════════════
# 雙路徑交叉驗算（00 §1.3）
# ══════════════════════════════════════════════════════════════════

def _rel(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.abs(a - b) / np.maximum.reduce(
        [np.abs(a), np.abs(b), np.full_like(a, EPS, dtype=float)])


def _compare(metric: str, pa: str, pb: str, kind: str,
             a: np.ndarray, b: np.ndarray, detail: str = "") -> CrossCheck:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if not m.any():
        return CrossCheck(metric, pa, pb, kind, 0, float("nan"), float("nan"),
                          False, "兩條路徑都沒有可比對的值 → 依 00 §1.6 不算驗算通過")
    ad = np.abs(a[m] - b[m])
    rd = _rel(a[m], b[m])
    tol = {"整數": 0.0, "代數等價": TOL_ALGEBRAIC, "迭代": TOL_ITERATIVE}[kind]
    passed = bool((ad.max() <= tol) if kind == "整數" else (rd.max() <= tol))
    if not passed:
        i = int(np.argmax(rd))
        idx = np.flatnonzero(m)[i]
        detail = (detail + " " if detail else "") + \
            f"最大歧異在第 {idx} 列：A={a[m][i]!r}、B={b[m][i]!r}"
    return CrossCheck(metric, pa, pb, kind, int(m.sum()),
                      float(ad.max()), float(rd.max()), passed, detail)


def _check_quantile(a: pd.DataFrame, b: pd.DataFrame) -> list[CrossCheck]:
    """RFM 分位：00 §1.3 只要求各組大小差 ≤1（兩條路徑的餘數分配規則不同）。"""
    out: list[CrossCheck] = []
    for col in ("r_score", "f_score", "m_score"):
        sa, sb = a[col].to_numpy(), b[col].to_numpy()
        sizes_a = pd.Series(sa).value_counts().reindex(range(1, 6), fill_value=0)
        sizes_b = pd.Series(sb).value_counts().reindex(range(1, 6), fill_value=0)
        gap = int((sizes_a - sizes_b).abs().max())
        mismatch = int((sa != sb).sum())
        out.append(CrossCheck(
            f"RFM 分位 {col}", "SQL NTILE(5)", "pandas 百分位序位切", "分位",
            len(sa), float(gap), float(gap) / max(len(sa), 1), gap <= 1,
            f"各組大小最大差 {gap} 人；逐人分數不同 {mismatch} 人"
            + ("" if gap <= 1 else " → 00 §1.3 門檻是 ≤1，這是實作錯誤不是切法差異")))
    return out


# ══════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════

def build_features(
    project: str,
    as_of: str | date | datetime,
    *,
    source: str | Path | None = None,
    colmap: dict[str, str] | None = None,
    dim_source: str | Path | None = None,
    prior_group_cols: Sequence[str] | None = None,
    bobstone_custom: BobStoneCustom | None = None,
    write: bool = True,
) -> BuildResult:
    """產生顧客特徵表。**這是特徵表的唯一介面（18-G4）。**

    project           專案代號。路徑與資料庫位置由 paths / db 決定，不寫死。
    as_of             基準日，**必填**。17 §二：不可預設用「今天」，否則歷史報告
                      每次重跑數字都變；18-G4：沒有它就是目標洩漏。
    source            交易來源。None → 倉儲裡的 fact_transaction；也可給 parquet/csv。
    colmap            欄名對照覆寫，如 {"amount_twd": "淨額"}。
    dim_source        顧客維度來源（算 CRI 的先驗分群用）。
    prior_group_cols  先驗分群欄位，如 ["性別", "居住地"]。09 §2.1：人口變數**可以**
                      當先驗分群，但**不可以**當下游 k-means 的輸入（18-E2 的邊界）。
    bobstone_custom   自訂 Bob Stone 參數。不給就不算 —— 09 §2.2 明訂不給預設值。
    write             是否把結果寫進倉儲、顧客特徵表/ 與 執行紀錄/。
    """
    if as_of is None or (isinstance(as_of, str) and not as_of.strip()):
        raise FeatureBuildError(
            "as_of 是必填參數 — 18-G4：沒有基準日的特徵一律視為目標洩漏，不准產生。"
            "請傳入分析基準日，例如 build_features(專案, as_of='2012-12-01')")
    as_of_d = _to_date(as_of)

    res = BuildResult(features=pd.DataFrame(), as_of=as_of_d)
    p = project_dir(project)

    with connect(project) as con:
        scan = _scan_expr(source)
        mapping, w0, i0 = _detect_columns(con, scan, colmap)
        res.warnings += w0
        res.infos += i0
        _normalize(con, scan, mapping)

        n_raw_all = con.execute("SELECT COUNT(*) FROM stg_txn_norm").fetchone()[0]
        n_raw = _exec_guarded(con, f"""
            SELECT COUNT(*) FROM stg_txn_norm
            WHERE biz_date <= DATE '{as_of_d}' AND txn_type = 'sale'
        """).fetchone()[0]
        if n_raw == 0:
            raise FeatureBuildError(
                f"as_of={as_of_d} 且 txn_type='sale' 的交易列為 0（來源共 {n_raw_all} 列）— "
                f"多半是基準日訂得太早，或 txn_type 的值不是 'sale'。"
                f"先跑 `SELECT txn_type, COUNT(*) FROM stg_txn_norm GROUP BY 1` 看實際值")
        if n_raw < n_raw_all:
            res.infos.append(
                f"as_of/sale 過濾刪掉 {n_raw_all - n_raw} 列"
                f"（{n_raw_all} → {n_raw}）。18-E22：樣本流失必須在報告交代")

        # ── 1. RFM（17 §二） ───────────────────────────────────
        rfm = _rfm_sql(con, as_of_d)
        gross = _gross_sql(con, as_of_d)
        rfm = rfm.merge(gross, on="cust_id", how="left")
        con.register("df_rfm", rfm)
        con.execute("CREATE OR REPLACE TABLE feat_rfm AS SELECT * FROM df_rfm")

        # 路徑 B：pandas 直接對明細層彙總（不同引擎、不同中間量）
        detail = _exec_guarded(con, f"""
            SELECT person_key AS cust_id, biz_date, amount_twd FROM stg_txn_norm
            WHERE biz_date <= DATE '{as_of_d}' AND txn_type = 'sale'
        """).df()
        pv_f = detail.pivot_table(index="cust_id", aggfunc="size").rename("f_b")
        # M 路徑 B：先壓到「顧客 × 日」（訂單層）再彙總，與明細層 SUM 走不同中間量
        pv_m = (detail.groupby(["cust_id", "biz_date"], as_index=False)["amount_twd"].sum()
                .groupby("cust_id")["amount_twd"].sum().rename("m_b"))
        chk = rfm.set_index("cust_id").join(pv_f.to_frame()).join(pv_m.to_frame())
        res.checks.append(_compare(
            "顧客交易筆數 F", "SQL GROUP BY COUNT", "pandas pivot_table 計數",
            "整數", chk["f_txn_cnt"].to_numpy(), chk["f_b"].to_numpy()))
        res.checks.append(_compare(
            "顧客金額 M", "交易明細層 SUM", "顧客×日彙總後再 SUM",
            "代數等價", chk["m_net_twd"].to_numpy(), chk["m_b"].to_numpy()))

        bad = rfm[rfm["f_active_days"] > rfm["f_txn_cnt"]]
        if len(bad):
            res.errors.append(
                f"{len(bad)} 位顧客的 f_active_days > f_txn_cnt — "
                f"17 §二的恆等不等式被打破，代表去重或 join 出了問題。"
                f"先查這幾位：{bad['cust_id'].head(5).tolist()}")

        # ── 2. 五等分法（17 §3.1） ─────────────────────────────
        nt_a = _ntile_sql(con)
        nt_b = _ntile_pandas(rfm)
        res.checks += _check_quantile(nt_a, nt_b)
        scores = nt_a.assign(
            rfm_score=lambda d: d.r_score + d.f_score + d.m_score,
            rfm_cell=lambda d: (d.r_score.astype(str) + d.f_score.astype(str)
                                + d.m_score.astype(str)))

        # ── 3. Bob Stone（17 §3.2 / §3.3） ────────────────────
        bs = _bobstone_original(rfm)
        vmin, vmax = float(bs.bs_r_score_variant.min()), float(bs.bs_r_score_variant.max())
        if vmin < 1 or vmax > 16:
            res.infos.append(
                f"原文 R-score 變體 INT(2^(4−INT(R/90))) 實際值域 {vmin:g}~{vmax:g}，"
                f"超出 17 §3.2 宣稱的 1~16（R ≥ 450 時指數轉負）。"
                f"要用這個變體就得自訂末段級距")
        if bobstone_custom is not None:
            bs = bs.merge(_bobstone_custom(rfm, bobstone_custom), on="cust_id")
            for d, col in (("R", "bsc_r_score"), ("F", "bsc_f_score"), ("M", "bsc_m_score")):
                top = float((bs[col] == bs[col].max()).mean())
                if top > 0.40:
                    res.warnings.append(
                        f"自訂 Bob Stone 的 {d} 構面有 {top:.0%} 的人撞同一格最高分 — "
                        f"09 §2.2：超過 40% 代表這個構面在你的資料上沒有鑑別力，"
                        f"權重再高也沒用。調換算率或上限再重跑")
        else:
            res.warnings.append(
                "沒有提供自訂 Bob Stone 參數，只算原版 — "
                "09 §2.2 明訂本 skill 不給自訂權重的預設值（那是不能外包的商業判斷）。"
                "要算就傳 bobstone_custom=BobStoneCustom(...)，權重三段理由缺一不可")

        # ── 4. λ / MLE / WMLE / CAI（17 §四） ─────────────────
        _customer_day(con, as_of_d)
        n_dedup = con.execute("SELECT COUNT(*) FROM stg_customer_day").fetchone()[0]
        cai = _cai_sql(con)
        n_interval = int(cai["interval_cnt"].sum()) if len(cai) else 0
        res.row_counts = {"原始交易": int(n_raw), "去重後": int(n_dedup),
                          "間隔數": int(n_interval), "顧客數": int(len(rfm))}

        # 17 §一的去重鏈：去重後每人再刪最後一筆 → 間隔數。
        # 每位顧客不分消費日多寡都剛好被刪掉一列（只有一天的人貢獻 0 個間隔），
        # 所以扣的是「有交易的顧客數」，不是「有 ≥2 天的顧客數」。
        n_cust = int(len(rfm))
        if n_dedup - n_cust != n_interval:
            res.errors.append(
                f"列數不變量被打破：去重後 {n_dedup} − 有交易的顧客 {n_cust} "
                f"≠ 間隔數 {n_interval} — 17 §一的「再刪每人最後一筆」沒有正確執行。"
                f"檢查 _cai_sql 的 next_date IS NOT NULL 那一步")

        # λ 的第二條路徑：(最後一日 − 第一日) / 間隔數。與 AVG(間隔) 走完全不同的中間量，
        # 17 §4.2 註明 MLE ≡ λ，這是免費的斷言。
        lam_b = (rfm.set_index("cust_id")
                 .assign(span=lambda d: (pd.to_datetime(d.last_sale_date)
                                         - pd.to_datetime(d.first_sale_date)).dt.days)
                 .join(cai.set_index("cust_id")[["interval_cnt"]]))
        lam_b["lambda_b"] = lam_b["span"] / lam_b["interval_cnt"]
        j = cai.set_index("cust_id").join(lam_b[["lambda_b"]])
        res.checks.append(_compare(
            "平均購買間隔 λ (≡MLE)", "SQL AVG(interval_days)",
            "(末日−首日)/間隔數", "代數等價",
            j["mle"].to_numpy(), j["lambda_b"].to_numpy()))

        n_no_cai = len(rfm) - len(cai)
        if n_no_cai:
            res.warnings.append(
                f"{n_no_cai} 位顧客只有 1 個消費日，算不出間隔 → MLE/WMLE/CAI 標 N/A — "
                f"00 §四：這是「有樣本但算不出來」，報告寫 N/A 不是留白，"
                f"並依 18-E22 交代人數（覆蓋率 {len(cai)/len(rfm):.1%}）")
        if len(rfm) and len(cai) / len(rfm) < 0.30:
            res.errors.append(
                f"CAI 覆蓋率 {len(cai)/len(rfm):.1%} < 30% — "
                f"00 §五的共同否決條件，這個指標不准進報告。"
                f"要嘛拉長觀察期，要嘛在圖表下標覆蓋率並降級為描述")

        # ── 5. μ 與標準化流失訊號（17 §4.1） ──────────────────
        feat = (rfm.merge(scores, on="cust_id", how="left")
                .merge(bs, on="cust_id", how="left")
                .merge(cai, on="cust_id", how="left"))
        feat["mu_amount_twd"] = feat["m_net_twd"] / feat["f_txn_cnt"]
        feat["lambda_days"] = feat["mle"]
        feat["churn_signal"] = feat["r_days_since_last_sale"] / feat["lambda_days"]

        # ── 6. 貝氏收縮與 CRI（17 §五、09 §2.1） ──────────────
        gmap = _build_group_map(con, dim_source, prior_group_cols, res)
        pri = _shrinkage(_prior_stats(con, as_of_d, gmap))
        if len(pri):
            small = pri.drop_duplicates("prior_group")
            small = small[small["grp_n_cust"] < 30]
            for _, r in small.iterrows():
                res.warnings.append(
                    f"先驗群「{r.prior_group}」只有 {int(r.grp_n_cust)} 位顧客（<30）— "
                    f"09 §2.1：小群的 τ²_g 偏小 → 成員被收縮得更凶，"
                    f"而那個群平均本身正是最不可信的。建議併進上一層再重跑，"
                    f"並在參數表記錄合併規則與合併前後的 CRI 變化")
            ok = np.isfinite(pri["cri_pathA"].to_numpy())
            res.checks.append(_compare(
                "CRI", "(IE−BE)/(IE−GE)×100", "W2×100", "代數等價",
                pri.loc[ok, "cri_pathA"].to_numpy(), pri.loc[ok, "cri"].to_numpy(),
                detail=f"排除 IE≈GE 的 0/0 列 {int((~ok).sum())} 筆"))
            okp = np.isfinite(pri["be_precision"].to_numpy())
            res.checks.append(_compare(
                "貝氏收縮估計 BE", "加權平均式 W1·IE+W2·GE", "精確度加權式",
                "迭代", pri.loc[okp, "be_shrunk"].to_numpy(),
                pri.loc[okp, "be_precision"].to_numpy(),
                detail=f"排除 n_i=1 或 s²_i=0 的 {int((~okp).sum())} 筆"))
            feat = feat.merge(
                pri[["cust_id", "prior_group", "n_i", "ie_xbar", "s2_i", "ge_mu_g",
                     "tau2_g", "w1", "w2", "be_shrunk", "cri"]],
                on="cust_id", how="left")
        else:
            for c in ("prior_group", "n_i", "ie_xbar", "s2_i", "ge_mu_g",
                      "tau2_g", "w1", "w2", "be_shrunk", "cri"):
                feat[c] = np.nan
            res.warnings.append(
                "沒有先驗分群層 → CRI 全部標 N/A（00 §五 M8-1 的降級規則）— "
                "要算就給 dim_source 與 prior_group_cols，"
                "例如 --dim customers.parquet --prior-group-cols 性別")

        feat.insert(1, "as_of_date", pd.Timestamp(as_of_d).date())
        feat["f_item_cnt"] = np.nan   # 來源無品項數欄；17 §二的三段不等式只驗到前兩段
        res.features = feat.sort_values("cust_id").reset_index(drop=True)

        for c in res.checks:
            if not c.passed:
                res.errors.append(
                    f"雙路徑驗算不符：{c.line()} — 00 §1.3：相對誤差超過代數等價門檻"
                    f"就是實作錯誤，不是數值問題。逐項印出分子、分母、權重找第一個分岔的量")

        if write:
            _write_outputs(con, p, res, project)

    if res.errors:
        raise FeatureBuildError(
            "特徵表未通過驗算，不可使用：\n  " + "\n  ".join(res.errors))
    return res


def _to_date(v: str | date | datetime) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v).strip()[:10], "%Y-%m-%d").date()
    except ValueError as e:
        raise FeatureBuildError(
            f"as_of 格式不對：{v!r} — 請用 YYYY-MM-DD，例如 2012-12-01") from e


def _build_group_map(
    con: Any, dim_source: str | Path | None,
    cols: Sequence[str] | None, res: BuildResult,
) -> pd.DataFrame | None:
    """把顧客維度的人口欄位串成先驗分群鍵。"""
    if dim_source is None or not cols:
        return None
    scan = _scan_expr(dim_source)
    have = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {scan}").fetchall()]
    missing = [c for c in cols if c not in have]
    if missing:
        raise FeatureBuildError(
            f"顧客維度缺少先驗分群欄位：{', '.join(missing)} — "
            f"該來源實際欄位：{', '.join(have)}")
    key = None
    for cand in _ALIASES["person_key"]:
        if cand in have:
            key = cand
            break
    if key is None:
        raise FeatureBuildError(
            f"顧客維度找不到顧客 ID 欄 — 實際欄位：{', '.join(have)}")
    expr = " || '×' || ".join(f"CAST({_quote(c)} AS VARCHAR)" for c in cols)
    gm = con.execute(f"""
        SELECT CAST({_quote(key)} AS BIGINT) AS cust_id, {expr} AS prior_group
        FROM {scan}
    """).df()
    res.infos.append(
        f"先驗分群：{'×'.join(cols)} → {gm['prior_group'].nunique()} 群。"
        f"⚠ 09 §2.1：人口變數可以當先驗分群，但不可以當下游 k-means 的輸入（18-E2）")
    return gm


def _write_outputs(con: Any, p: Any, res: BuildResult, project: str) -> None:
    """留成果（00 §1.2）：倉儲表、Parquet、以及帶 max_abs_diff 的執行紀錄。"""
    df = res.features
    con.register("df_feat", df)
    con.execute("CREATE OR REPLACE TABLE feat_customer AS SELECT * FROM df_feat")

    p.features.mkdir(parents=True, exist_ok=True)
    p.log.mkdir(parents=True, exist_ok=True)
    fp = p.features / f"feat_customer_asof{res.as_of}.parquet"
    df.to_parquet(fp, index=False)

    lp = p.log / f"build_features_asof{res.as_of}.md"
    lines = [
        f"# build_features 執行紀錄｜{project}｜as_of = {res.as_of}",
        "",
        f"- 產出：`{fp}`（{len(df)} 位顧客、{df.shape[1]} 欄）",
        f"- 列數流：" + " → ".join(f"{k} {v:,}" for k, v in res.row_counts.items()),
        "",
        "## 雙路徑交叉驗算（00 §1.3）",
        "",
        "| 指標 | 路徑 A | 路徑 B | 類型 | n | max_abs_diff | max_rel_diff | 容差 | 結果 |",
        "|---|---|---|---|---:|---:|---:|---:|:--:|",
    ]
    for c in res.checks:
        lines.append(
            f"| {c.metric} | {c.path_a} | {c.path_b} | {c.kind} | {c.n_compared} | "
            f"{c.max_abs_diff:.3e} | {c.max_rel_diff:.3e} | {c.tolerance:g} | "
            f"{'✅' if c.passed else '⛔'} |")
    if res.warnings:
        lines += ["", "## ⚠ 警告", ""] + [f"- {w}" for w in res.warnings]
    if res.errors:
        lines += ["", "## ⛔ 錯誤", ""] + [f"- {e}" for e in res.errors]
    lines += ["", "## · 明細", ""] + [f"- {i}" for i in res.infos]
    lp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    res.written = {"parquet": str(fp), "log": str(lp), "table": "feat_customer"}


# ══════════════════════════════════════════════════════════════════
# 基準值比對（17 §八 的 ground truth）
# ══════════════════════════════════════════════════════════════════

def check_benchmark(res: BuildResult) -> tuple[list[str], list[str]]:
    """拿 17 §八 的 ground truth 照一次。回傳 (errors, infos)。

    17 §七：任何指標實作改動後都要重跑。這裡把那組值內建，改完公式當場能照。
    """
    errs: list[str] = []
    infos: list[str] = []
    f = res.features.set_index("cust_id")
    for name, (cid, col, want, tol) in BENCHMARK.items():
        if cid not in f.index or col not in f.columns:
            infos.append(f"{name}：資料裡沒有這位顧客或這一欄，跳過")
            continue
        got = float(f.loc[cid, col])
        if abs(got - want) > tol:
            errs.append(f"{name} 期望 {want}、實得 {got!r}（容差 {tol:g}）— "
                        f"公式或口徑被改動了，回 17 §八 對照")
        else:
            infos.append(f"{name} = {got:.6f}（期望 {want}）")
    for k, want in BENCHMARK_ROWS.items():
        got = res.row_counts.get(k)
        if got is None:
            continue
        if got != want:
            errs.append(f"列數「{k}」期望 {want:,}、實得 {got:,} — "
                        f"17 §一的去重鏈斷了，先查粒度與 as_of")
        else:
            infos.append(f"列數 {k} = {got:,}（期望 {want:,}）")
    if "cai" in res.features.columns and res.features["cai"].notna().any():
        lo, hi = float(res.features.cai.min()), float(res.features.cai.max())
        wl, wh = BENCHMARK_CAI_RANGE
        if abs(lo - wl) > 5e-7 or abs(hi - wh) > 5e-7:
            errs.append(f"CAI 值域期望 {wl} ~ {wh}、實得 {lo} ~ {hi} — 回 17 §八 對照")
        else:
            infos.append(f"CAI 值域 = {lo:.6f} ~ {hi:.6f}（期望 {wl} ~ {wh}）")
    return errs, infos


# ══════════════════════════════════════════════════════════════════
# CLI：三桶 + 退出碼 0/1/2
# ══════════════════════════════════════════════════════════════════

def _parse_colmap(items: list[str] | None) -> dict[str, str] | None:
    if not items:
        return None
    out: dict[str, str] = {}
    for it in items:
        if "=" not in it:
            raise SystemExit(f"--colmap 格式錯誤：{it} — 要寫成 canonical=來源欄名")
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="產生顧客特徵表（18-G4 明訂的唯一介面）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="專案代號")
    ap.add_argument("--as-of", required=True, metavar="YYYY-MM-DD",
                    help="基準日，必填。沒有它一律視為目標洩漏（18-G4）")
    ap.add_argument("--source", default=None,
                    help="交易來源 parquet/csv 或表名。省略 → 倉儲的 fact_transaction")
    ap.add_argument("--colmap", action="append", metavar="canon=來源欄",
                    help="欄名對照覆寫，可重複")
    ap.add_argument("--dim", default=None, help="顧客維度來源（算 CRI 的先驗分群用）")
    ap.add_argument("--prior-group-cols", default=None,
                    help="先驗分群欄位，逗號分隔，如「性別,居住地」")
    ap.add_argument("--benchmark", action="store_true",
                    help="與 17 §八 的 ground truth 逐位比對")
    ap.add_argument("--no-write", action="store_true", help="不寫檔，只算")
    args = ap.parse_args()

    print("=" * 66)
    print(f"顧客特徵表 build_features｜專案 {args.project}｜as_of {args.as_of}")
    print("=" * 66)

    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    cols = ([c.strip() for c in args.prior_group_cols.split(",") if c.strip()]
            if args.prior_group_cols else None)
    res: BuildResult | None = None
    try:
        res = build_features(
            args.project, args.as_of, source=args.source,
            colmap=_parse_colmap(args.colmap), dim_source=args.dim,
            prior_group_cols=cols, write=not args.no_write)
    except FeatureBuildError as e:
        errors.append(str(e))
    except Exception as e:  # noqa: BLE001
        errors.append(f"未預期的例外：{e!r} — "
                      f"多半是來源結構與預期不符，先跑 profile_dataset.py 看實際欄位")

    if res is not None:
        warnings += res.warnings
        infos += res.infos
        infos.append("列數流：" + " → ".join(
            f"{k} {v:,}" for k, v in res.row_counts.items()))
        for c in res.checks:
            (infos if c.passed else errors).append(c.line())
        if res.written:
            infos.append(f"已寫出：{res.written['parquet']}")
            infos.append(f"執行紀錄：{res.written['log']}")
        if args.benchmark:
            be, bi = check_benchmark(res)
            errors += [f"基準值不符 — {m}" for m in be]
            infos += [f"基準值 {m}" for m in bi]

    if infos:
        print("\n通過與明細")
        print("-" * 66)
        for m in infos:
            print(f"  · {m}")
    if warnings:
        print("\n⚠ 可以往下走，但報告要交代這幾件事")
        print("-" * 66)
        for m in warnings:
            print(f"  ⚠ {m}")
    if errors:
        print("\n⛔ 特徵表不可使用，必須先處理")
        print("-" * 66)
        for m in errors:
            print(f"  ⛔ {m}")

    print("\n" + "=" * 66)
    if errors:
        print(f"結果：{len(errors)} 個 error、{len(warnings)} 個 warning → 特徵表不可用")
        return 1
    if warnings:
        print(f"結果：{len(warnings)} 個 warning → 特徵表可用，報告需註明")
        return 2
    print(f"結果：全部通過（{len(infos)} 項）→ 特徵表可用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
