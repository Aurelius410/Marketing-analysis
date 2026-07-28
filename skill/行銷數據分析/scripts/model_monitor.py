#!/usr/bin/env python3
"""
模型上線後監控（12 §十）—— PSI／特徵漂移／預測分布漂移／效能衰退。對應 18-G15。

12 §十 的 MONITOR 字典把監控對象列成七項（precision@門檻、recall@門檻、
top_decile_lift、calib_slope、brier、正類實際發生率、各特徵的 PSI），本腳本
把那七項全部算出來，並照同一節的「告警規則」逐條判定。四類檢查：

  ① 特徵漂移      逐特徵 PSI（母體穩定度指標）
  ② 預測分布漂移  分數本身的 PSI ＋ 正類實際發生率的相對變化
  ③ 效能衰退      precision／recall／top_decile_lift／brier／calib_slope
  ④ 名單穩定度    本期 top 名單與前期的重疊率（12 §十 尾註）

**這支腳本最重要的一件事是把分箱規則存下來。**
PSI 對分箱方式極度敏感：同一對資料，等頻 5 箱與等頻 20 箱算出來的 PSI 可以
差一倍以上（本腳本 --self-test 第 ⑤ 項會當場示範，數字每次都印出來）。
所以「這期 PSI = 0.18」這句話本身沒有意義，必須是「用 <這組切點> 算出來的
PSI = 0.18」。實作上：

  · 分箱切點**只從基準期算**，寫進 模型輸出/monitor_baseline.json，之後每期重用。
    每期各自分箱等於每期換一把尺，量到的是尺的差異不是母體的差異。
  · spec 帶一個 **分箱指紋**（切點 + 方法 + 箱數的 sha1 前 12 碼）。指紋一換，
    PSI 與歷史數字就不可比，本腳本會擋下來（error），要換必須明示 --rebaseline，
    並在 交付物/預測追蹤.md 留下斷點紀錄。
  · 端箱固定是 (-inf, e1) 與 [ek, inf)。當期出現比基準更極端的值仍會落進端箱，
    不會被默默丟掉 —— 丟掉的話占比總和不等於 1，PSI 會被系統性低估。
  · 缺值自成一箱，不是丟掉。「某些特徵突然大量無樣本」正是 12 §十 漂移來源表
    裡「產品／品類改版」的徵狀，把缺值丟掉就剛好看不到它。
  · 類別欄的水準清單也取自基準；當期的新水準統一歸進 __未見類別__ 箱並列名。

門檻全部出自 12 §十 的「告警規則」，每一條的出處寫在常數區。唯一不在 reference
裡的是 PSI 0.10 這條 —— reference 只寫了 0.25。本腳本把 0.10 當「觀察」等級：
列進表、印出來，但**不進 warning 桶**，避免用一個 reference 沒背書的數字擋人。

三桶怎麼分（12 §十 的「動作階梯」就是分桶依據）：
    error   模型不可照原樣繼續用 —— reference 明寫要「重訓」以上動作者，
            以及讓 PSI 根本算不得的設定問題（分箱不可比、欄位對不上）
    warning 可繼續用但要處置或查證 —— reference 明寫「只重做校準，不必重訓
            全模型」「查資料源」「人工看一眼」，以及未經驗證的門檻

用法：
    # 第一次：只建基準（分箱規則從這份資料算，之後每期都用它）
    python model_monitor.py 2026Q3_電商 --baseline 模型輸出/上線基準.parquet

    # 每期監控
    python model_monitor.py 2026Q3_電商 --current 模型輸出/2026M08.parquet

    # 換模型或換特徵定義，必須重建基準（會產生歷史斷點，腳本會要你留紀錄）
    python model_monitor.py 2026Q3_電商 --baseline 新基準.parquet --rebaseline

    python model_monitor.py --self-test

輸出：
    統計表/預測模型/監控_PSI.csv           逐特徵 PSI 與判級
    統計表/預測模型/監控_PSI分箱明細.csv    逐箱基準／當期占比與 PSI 貢獻
    統計表/預測模型/監控_效能對照.csv       七項指標的基準 vs 當期
    模型輸出/monitor_baseline.json          **分箱規則 + 基準占比 + 基準效能**
    模型輸出/model_monitor.json             本次結果，機器可讀
    交付物/預測追蹤.md                      18-G15 指定落點，逐期追加
    執行紀錄/monitor_runs.csv               逐次留痕（時間／樣本數／指紋／最大 PSI）

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 四類檢查都跑到且全過
    1  = 有 error 擋住（PSI 不可比、欄位對不上、或已到「必須重訓」等級）
    2  = 只有 warning，可往下但 預測追蹤.md 要逐條寫明處置
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import hashlib
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

# ── 門檻。出處逐條標在後面，要改門檻請先改 reference ──────────────
PSI_ALERT = 0.25         # 12 §十 告警規則：「任一特徵 PSI > 0.25 → 該特徵分布已
                         # 漂移，查資料源」。reference 自己註明這是信用風險業界
                         # 慣用值、本專案未驗證（【推導，待驗證】）
PSI_WATCH = 0.10         # reference **沒有寫這一條**。信用評分卡的慣例是
                         # 0.1–0.25 為「輕微位移，持續觀察」。因為沒有 reference
                         # 背書，本腳本只列「觀察」不告警（不進 warning 桶）
PR_DROP_ABS = 0.05       # 12 §十：「P 或 R 相對上線基準跌 >5% 絕對值 → 告警
                         # （教材 §21）」。絕對值 = 5 個百分點，不是相對 5%
LIFT_FLOOR = 2.0         # 12 §十：「top_decile_lift 跌破 2.0 → 告警」，
                         # reference 註明此門檻為【推導，待驗證】，需以自己的歷史校準
CALIB_SLOPE_TOL = 0.15   # 12 §十：「calib_slope 偏離 1.0 超過 ±0.15 → 只重做校準，
                         # 不必重訓全模型」。因為「不必重訓」，這條歸 warning
POS_RATE_REL_MAX = 0.30  # 12 §十：「正類實際發生率與訓練期相差 >30% 相對值 →
                         # 母體變了，必須重訓」。因為「必須」，這條歸 error
LIST_OVERLAP_MIN = 0.50  # 12 §十 尾註：「名單重疊率 <50% 時要人工看一眼」
WATCH_CLUSTER_MIN = 3    # 本腳本自訂（【推導，待驗證】）：≥3 個特徵同時落在觀察區
                         # → 符合 12 §十 漂移來源表「外部事件：全體特徵分布同時
                         # 位移」的徵狀。單一特徵輕微位移不叫，一起動才叫

DEFAULT_BINS = 10        # 12 §三 的 calib_report 用等頻 10 箱（`np.quantile(...)`
                         # 那行還特別註明「等頻分箱，不用等寬」）。PSI 沿用同一組
                         # 慣例，同一份報告裡分箱口徑才一致
DEFAULT_TOP_PCT = 10.0   # 12 §五：top decile lift（k=10）是行銷最常引用的單一數字
CALIB_MIN_BIN = 30       # 12 §三：校準曲線每箱樣本 <30 標 N/A（00 §四 的 N/A 紀律）
PSI_FLOOR_OBS = 0.5      # 空箱的平滑值：占比下限 = 0.5/n（半個觀測值）。
                         # 不平滑的話 ln(0) = -inf，PSI 直接爆掉。此規則
                         # reference 未規定，屬本腳本自訂（【推導，待驗證】），
                         # 因此每個被平滑的箱都會標記出來，且平滑後 PSI 只能當
                         # 方向不能當量

MISSING_BIN = "__缺值__"
UNSEEN_BIN = "__未見類別__"
BIN_METHODS = ("quantile", "equal_width")

SCORE_CANDIDATES = ("score", "prob", "probability", "y_prob", "p_hat",
                    "預測機率", "分數", "機率", "預測分數")
LABEL_CANDIDATES = ("label", "y", "target", "actual", "實際", "實際結果",
                    "是否回應", "是否購買", "是否流失")
ID_CANDIDATES = ("客戶編號", "customer_id", "cust_id", "會員編號", "id")

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
    """自我測試在同一支行程裡跑很多情境，桶子要能清空才驗得準。"""
    _errors.clear()
    _warnings.clear()
    _infos.clear()


def _py(v: Any) -> Any:
    """numpy 純量 → 原生 Python 型別。

    分箱後的 count 是 numpy int64、占比是 numpy float64，一路帶進結果 dict，
    json.dumps 會在所有分析都跑完、CSV 都寫好之後才丟 TypeError，退出碼 70
    蓋掉前面全綠的結論。在來源就轉掉。
    """
    return v.item() if hasattr(v, "item") else v


def _fmt_num(v: Any, signed: bool = False, pct: bool = False) -> str:
    """數字轉字串，算不出來一律寫 N/A（00 §四）。

    為什麼要這個而不是直接丟進 DataFrame：一欄裡混了 None 與 float，pandas 會
    把 None 轉成 NaN，印出來變 "nan"、寫進 CSV 變空白格 —— 而 00 §四 的規矩是
    「有樣本但算不出來」寫 N/A、「無樣本」寫 `-`，空白格與 NaN 都不准出現
    （verify_outputs 的 CELL_RULES 會抓）。所以格式化在進表之前做。
    """
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "N/A"
    if pct:
        return f"{v:+.1%}" if signed else f"{v:.4%}"
    return f"{v:+.4f}" if signed else f"{v:.4f}"


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy 型別時，讓它存成字串而不是讓腳本掛掉。"""
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    return str(o)


# ══════════════════════════════════════════════════════════════
#  載入
# ══════════════════════════════════════════════════════════════
def load_table(path: Path, what: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"找不到{what}：{path}\n"
            f"  監控要兩份資料：基準期（--baseline，只給一次）與當期（--current，每期給）。"
        )
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() in (".csv", ".txt"):
        return pd.read_csv(path)
    raise ValueError(f"{what} 只吃 .parquet / .csv，拿到 {path.suffix}：{path}")


def pick_col(df: pd.DataFrame, explicit: str | None,
             candidates: tuple[str, ...], what: str) -> str | None:
    if explicit:
        if explicit not in df.columns:
            raise ValueError(f"資料裡沒有指定的{what}欄：{explicit}"
                             f"（現有欄位：{'、'.join(map(str, df.columns[:12]))}…）")
        return explicit
    low = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def default_features(df: pd.DataFrame, exclude: set[str]) -> list[str]:
    """沒指定就監控除了 id／分數／標籤以外的所有欄位。"""
    out = []
    for c in df.columns:
        if c in exclude:
            continue
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            # 日期欄的 PSI 沒有意義（它必然往後移），監控它只會每期都叫
            continue
        out.append(c)
    return out


# ══════════════════════════════════════════════════════════════
#  分箱：切點只從基準期算，算完就存檔
# ══════════════════════════════════════════════════════════════
def _numeric_labels(interior: list[float]) -> list[str]:
    edges = [float("-inf")] + list(interior) + [float("inf")]
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        lo_s = "-inf" if lo == float("-inf") else f"{lo:.6g}"
        hi_s = "inf" if hi == float("inf") else f"{hi:.6g}"
        out.append(f"[{lo_s}, {hi_s})")
    return out


def is_categorical(s: pd.Series, n_bins: int) -> bool:
    """數值欄唯一值少於箱數時也當類別處理 —— 否則等頻切點會全部重複，
    塌成兩三箱，而使用者以為自己在用 10 箱。"""
    if not pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
        return True
    return int(s.dropna().nunique()) <= n_bins


def build_feature_bins(name: str, s: pd.Series, *, n_bins: int,
                       method: str) -> dict[str, Any]:
    """從基準期的一欄算出分箱規則 + 基準占比。"""
    n_all = int(len(s))
    n_na = int(s.isna().sum())
    v = s.dropna()

    if is_categorical(s, n_bins):
        levels = [str(x) for x in sorted(pd.unique(v.astype(str)))]
        labels = levels + [UNSEEN_BIN, MISSING_BIN]
        fs: dict[str, Any] = {
            "type": "categorical", "method": "levels",
            "levels": levels, "edges": [], "labels": labels,
            "n_bins_requested": int(n_bins), "n_bins_effective": len(labels),
        }
    else:
        x = pd.to_numeric(v, errors="coerce").to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        if x.size == 0:
            raise ValueError(f"特徵 {name} 在基準期沒有任何有限數值，無法建分箱")
        if method == "quantile":
            qs = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
            interior = np.unique(np.quantile(x, qs))
        else:
            interior = np.unique(np.linspace(x.min(), x.max(), n_bins + 1)[1:-1])
        interior = [float(e) for e in interior]
        labels = _numeric_labels(interior) + [MISSING_BIN]
        fs = {
            "type": "numeric", "method": method,
            "levels": [], "edges": interior, "labels": labels,
            "n_bins_requested": int(n_bins),
            "n_bins_effective": len(interior) + 1,   # 不含缺值箱
        }

    cnt, meta = bin_counts(s, fs)
    fs["baseline_count"] = [int(c) for c in cnt]
    fs["baseline_n"] = n_all
    fs["baseline_prop"] = [(float(c) / n_all if n_all else 0.0) for c in cnt]
    fs["baseline_missing_rate"] = (n_na / n_all) if n_all else 0.0
    fs["baseline_bin_meta"] = meta
    return fs


def bin_counts(s: pd.Series, fs: dict[str, Any]) -> tuple[np.ndarray, dict[str, int]]:
    """把一欄套進既有分箱規則，回傳逐箱次數。

    三件事刻意不做：不丟缺值（自成一箱）、不丟超出基準範圍的值（端箱是
    ±inf 開放的）、不丟沒見過的類別（歸 __未見類別__ 箱）。任何一項丟掉，
    占比總和就不等於 1，PSI 會被系統性低估 —— 而且是往「沒漂移」的方向偏。
    """
    labels: list[str] = list(fs["labels"])
    idx_of = {lab: i for i, lab in enumerate(labels)}
    counts = np.zeros(len(labels), dtype=float)
    meta = {"缺值": 0, "未見類別": 0, "轉型失敗": 0}

    isna = s.isna()
    meta["缺值"] = int(isna.sum())
    v = s[~isna]

    if fs["type"] == "numeric":
        x = pd.to_numeric(v, errors="coerce").to_numpy(dtype=float)
        bad = np.isnan(x)
        meta["轉型失敗"] = int(bad.sum())
        counts[idx_of[MISSING_BIN]] = meta["缺值"] + meta["轉型失敗"]
        x = x[~bad]
        interior = np.asarray(fs["edges"], dtype=float)
        # side="right" ⇒ 左閉右開；x < interior[0] 落 0 箱，x >= interior[-1] 落最後一箱
        pos = np.searchsorted(interior, x, side="right") if interior.size else np.zeros(
            x.size, dtype=int)
        if x.size:
            np.add.at(counts, pos.astype(int), 1.0)
    else:
        counts[idx_of[MISSING_BIN]] = meta["缺值"]
        levels = set(fs["levels"])
        vs = v.astype(str)
        seen = vs[vs.isin(levels)]
        unseen_n = int(len(vs) - len(seen))
        meta["未見類別"] = unseen_n
        counts[idx_of[UNSEEN_BIN]] = unseen_n
        if len(seen):
            vc = seen.value_counts()
            for lab in vc.index:
                counts[idx_of[str(lab)]] += float(vc[lab])
    return counts, meta


# ══════════════════════════════════════════════════════════════
#  PSI
# ══════════════════════════════════════════════════════════════
def psi_from_counts(base_cnt: np.ndarray, cur_cnt: np.ndarray,
                    floor_obs: float = PSI_FLOOR_OBS) -> dict[str, Any]:
    r"""PSI = Σ (現期占比 − 基準占比) × ln(現期占比 / 基準占比)。

    空箱處理：占比下限取 floor_obs/n（半個觀測值），floor 完重新歸一化。
    沒有下限的話 ln(0) = −inf，一個空箱就讓整支腳本吐 inf；而 inf 在
    「> 0.25 就告警」這種比較裡會安靜地通過型別檢查、直接判成漂移，
    分不出「真的漂了」與「這箱本來就沒人」。被平滑的箱一律標記回傳。
    """
    base_cnt = np.asarray(base_cnt, dtype=float)
    cur_cnt = np.asarray(cur_cnt, dtype=float)
    if base_cnt.shape != cur_cnt.shape:
        raise ValueError(f"箱數不一致：基準 {base_cnt.shape} vs 當期 {cur_cnt.shape}"
                         f" —— 兩期必須用同一套分箱規則")
    nb, nc = float(base_cnt.sum()), float(cur_cnt.sum())
    if nb <= 0 or nc <= 0:
        raise ValueError(f"樣本數為 0（基準 {nb:.0f}／當期 {nc:.0f}），PSI 算不出來")

    pb, pc = base_cnt / nb, cur_cnt / nc
    smoothed = (base_cnt == 0) | (cur_cnt == 0)
    fb = np.maximum(pb, floor_obs / nb)
    fc = np.maximum(pc, floor_obs / nc)
    fb, fc = fb / fb.sum(), fc / fc.sum()
    contrib = (fc - fb) * np.log(fc / fb)
    return {
        "psi": float(contrib.sum()),
        "contrib": contrib,
        "base_prop": pb, "cur_prop": pc,
        "base_count": base_cnt, "cur_count": cur_cnt,
        "smoothed": smoothed,
        "n_smoothed": int(smoothed.sum()),
        "n_base": int(nb), "n_cur": int(nc),
    }


def expected_noise_psi(n_base: int, n_cur: int, n_bins: int) -> float:
    """兩份來自**同一母體**的樣本，PSI 的期望值（純抽樣雜訊）。

    二階泰勒展開下 (p_c−p_b)·ln(p_c/p_b) ≈ (p_c−p_b)²/p̄，取期望得
        E[PSI] ≈ Σ_j (1−p_j)(1/n_b + 1/n_c) = (B−1)(1/n_b + 1/n_c)
    這個數字是判讀 PSI 的地板：n=200、B=10 時光是抽樣雜訊就有 ≈0.09，
    已經逼近 0.10 的觀察門檻 —— 小樣本下「看起來在漂」是常態。
    本式為本腳本自訂（【推導，待驗證】），--self-test 第 ⑫ 項用模擬對照驗過。
    """
    if n_base <= 0 or n_cur <= 0 or n_bins <= 1:
        return float("nan")
    return float((n_bins - 1) * (1.0 / n_base + 1.0 / n_cur))


def psi_grade(psi: float) -> str:
    if not np.isfinite(psi):
        return "N/A"
    if psi > PSI_ALERT:
        return "告警"
    if psi >= PSI_WATCH:
        return "觀察"
    return "穩定"


def psi_for_feature(name: str, fs: dict[str, Any],
                    s_cur: pd.Series) -> dict[str, Any]:
    """對一欄算 PSI，回傳摘要 + 逐箱明細（明細要跟 PSI 一起存，否則無法複驗）。"""
    cur_cnt, meta = bin_counts(s_cur, fs)
    base_cnt = np.asarray(fs["baseline_count"], dtype=float)
    r = psi_from_counts(base_cnt, cur_cnt)
    n_eff = int(fs["n_bins_effective"])
    noise = expected_noise_psi(r["n_base"], r["n_cur"], len(base_cnt))

    rows = []
    for i, lab in enumerate(fs["labels"]):
        rows.append({
            "特徵": name, "箱": lab,
            "基準次數": int(r["base_count"][i]),
            "基準占比": round(float(r["base_prop"][i]), 6),
            "當期次數": int(r["cur_count"][i]),
            "當期占比": round(float(r["cur_prop"][i]), 6),
            "PSI貢獻": round(float(r["contrib"][i]), 6),
            "已平滑": bool(r["smoothed"][i]),
        })

    base_missing = float(fs.get("baseline_missing_rate", 0.0))
    cur_missing = (meta["缺值"] + meta["轉型失敗"]) / max(len(s_cur), 1)
    return {
        "特徵": name, "型別": fs["type"], "分箱方法": fs["method"],
        "有效箱數": n_eff,
        "PSI": round(r["psi"], 6),
        "判級": psi_grade(r["psi"]),
        "雜訊期望PSI": round(noise, 6),
        "基準n": r["n_base"], "當期n": r["n_cur"],
        "平滑箱數": r["n_smoothed"],
        "基準缺值率": round(base_missing, 6),
        "當期缺值率": round(cur_missing, 6),
        "當期未見類別數": int(meta["未見類別"]),
        "_rows": rows,
    }


# ══════════════════════════════════════════════════════════════
#  效能指標（12 §十 的七項監控對象裡屬於效能的那幾項）
# ══════════════════════════════════════════════════════════════
def calib_slope(p: np.ndarray, y: np.ndarray, n_bins: int = 10,
                min_bin: int = CALIB_MIN_BIN) -> tuple[float | None, int]:
    """校準斜率，照 12 §三 calib_report 的做法：等頻 10 箱、每箱 <30 標 N/A、
    對 (該箱預測均值, 該箱實際發生率) 跑 OLS 取斜率。理想值 1.0。

    這裡沿用 §三 的箱界寫法 `(p >= lo) & (p <= hi)`（兩端閉合），為的是跟
    calibrate.py 寫進表 11.1 的數字口徑一致 —— 切點上的樣本會同時算進相鄰
    兩箱，這是 §三 的既有行為，不在本腳本片面修掉（見回傳說明）。
    PSI 的分箱另走左閉右開，兩者用途不同，不共用。
    """
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    if p.size < min_bin * 2:
        return None, 0
    bins = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    obs, pred = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (p >= lo) & (p <= hi)
        if m.sum() < min_bin:
            continue
        obs.append(float(y[m].mean()))
        pred.append(float(p[m].mean()))
    if len(pred) < 2 or float(np.ptp(pred)) == 0.0:
        return None, len(pred)
    slope = float(np.polyfit(np.asarray(pred), np.asarray(obs), 1)[0])
    # 退化情況（預測值幾乎無變異）polyfit 會吐 nan；nan 在 abs(slope-1)>tol 的
    # 比較裡永遠是 False，會安靜地變成「校準正常」。當成算不出來回 None。
    return (slope if np.isfinite(slope) else None), len(pred)


def perf_metrics(score: np.ndarray, y: np.ndarray, *,
                 threshold: float | None, top_pct: float) -> dict[str, Any]:
    """12 §十 的效能監控對象。門檻沒給就用 top_pct 名單的分位點當門檻
    —— 行銷的門檻本來就是「這次發幾封」決定的（12 §五 Step 2）。"""
    score = np.asarray(score, dtype=float)
    y = np.asarray(y, dtype=float)
    n = int(score.size)
    out: dict[str, Any] = {"n": n}
    if n == 0:
        return out

    pos_rate = float(y.mean())
    out["正類實際發生率"] = pos_rate

    if threshold is None:
        thr = float(np.quantile(score, 1.0 - top_pct / 100.0))
        out["門檻來源"] = f"top {top_pct:.0f}% 名單的分位點"
    else:
        thr = float(threshold)
        out["門檻來源"] = "指定機率門檻"
    out["門檻"] = thr

    sel = score >= thr
    out["名單人數"] = int(sel.sum())
    out["precision@門檻"] = float(y[sel].mean()) if sel.sum() else None
    out["recall@門檻"] = (float(y[sel].sum() / y.sum()) if y.sum() > 0 else None)

    # top decile lift：定義固定 k=10（12 §五），不跟著 --top-pct 動
    k = max(int(round(n * 0.10)), 1)
    order = np.argsort(-score, kind="stable")
    top_y = y[order[:k]]
    out["top_decile_lift"] = (float(top_y.mean() / pos_rate)
                              if pos_rate > 0 else None)
    out["brier"] = float(np.mean((score - y) ** 2))
    slope, nb = calib_slope(score, y)
    out["calib_slope"] = slope
    out["calib_有效箱數"] = nb
    return out


def top_list(ids: pd.Series, score: np.ndarray, top_pct: float) -> list[str]:
    k = max(int(round(len(score) * top_pct / 100.0)), 1)
    order = np.argsort(-np.asarray(score, dtype=float), kind="stable")
    return [str(v) for v in ids.iloc[order[:k]].tolist()]


# ══════════════════════════════════════════════════════════════
#  基準 spec：分箱規則 + 基準占比 + 基準效能，一起存
# ══════════════════════════════════════════════════════════════
def binning_fingerprint(spec: dict[str, Any]) -> str:
    """分箱指紋 —— 只吃「會改變 PSI 可比性」的東西：方法、箱數、切點、水準。

    刻意不吃樣本數與產製時間：同一組切點在不同時間重算出來的 PSI 是可比的，
    但換一組切點就不是。指紋一變，歷史 PSI 就要當成另一條序列。
    """
    payload = {
        "設定": {k: spec["設定"][k] for k in ("n_bins", "method")},
        "features": {
            name: {"type": fs["type"], "method": fs["method"],
                   "edges": [round(float(e), 10) for e in fs["edges"]],
                   "levels": list(fs["levels"])}
            for name, fs in sorted(spec["features"].items())
        },
    }
    if spec.get("score") and spec["score"].get("bins"):
        b = spec["score"]["bins"]
        payload["score"] = {"type": b["type"], "method": b["method"],
                            "edges": [round(float(e), 10) for e in b["edges"]]}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      default=_json_default).encode("utf-8")
    return "sha1:" + hashlib.sha1(blob).hexdigest()[:12]


def build_spec(base_df: pd.DataFrame, feature_cols: list[str], *,
               n_bins: int, method: str,
               score_col: str | None, label_col: str | None,
               id_col: str | None, threshold: float | None,
               top_pct: float, source: str) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "schema_version": "1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "baseline_source": source,
        "baseline_rows": int(len(base_df)),
        "設定": {
            "n_bins": int(n_bins), "method": method,
            "top_pct": float(top_pct), "threshold": threshold,
            "缺值獨立成箱": True, "未見類別箱": UNSEEN_BIN,
            "端箱": "(-inf, e1) 與 [ek, inf)，當期的極端值不會被丟掉",
            "空箱平滑": f"占比下限 {PSI_FLOOR_OBS}/n，平滑後重新歸一化",
        },
        "欄位": {"score": score_col, "label": label_col, "id": id_col},
        "features": {},
    }
    for c in feature_cols:
        spec["features"][c] = build_feature_bins(c, base_df[c],
                                                 n_bins=n_bins, method=method)

    if score_col:
        sb = build_feature_bins(score_col, base_df[score_col],
                                n_bins=n_bins, method=method)
        spec["score"] = {"col": score_col, "bins": sb}

    if score_col and label_col:
        m = perf_metrics(base_df[score_col].to_numpy(dtype=float),
                         base_df[label_col].to_numpy(dtype=float),
                         threshold=threshold, top_pct=top_pct)
        spec["baseline_metrics"] = {k: _py(v) for k, v in m.items()}
        if id_col:
            spec["baseline_top_list"] = top_list(
                base_df[id_col], base_df[score_col].to_numpy(dtype=float), top_pct)

    spec["binning_fingerprint"] = binning_fingerprint(spec)
    return spec


def spec_incompatibilities(spec: dict[str, Any], *, n_bins: int | None,
                           method: str | None) -> list[str]:
    """使用者這次指定的分箱參數與既有基準不一致的地方。有任何一條就不可比。"""
    bad = []
    s = spec.get("設定", {})
    if n_bins is not None and int(s.get("n_bins", -1)) != int(n_bins):
        bad.append(f"箱數：基準 {s.get('n_bins')} vs 本次指定 {n_bins}")
    if method is not None and str(s.get("method")) != str(method):
        bad.append(f"分箱方法：基準 {s.get('method')} vs 本次指定 {method}")
    return bad


# ══════════════════════════════════════════════════════════════
#  四類檢查
# ══════════════════════════════════════════════════════════════
def check_feature_drift(spec: dict[str, Any], cur_df: pd.DataFrame
                        ) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    print("\n① 特徵漂移（12 §十：任一特徵 PSI > 0.25 → 查資料源）")
    feats = spec["features"]
    missing_cols = [c for c in feats if c not in cur_df.columns]
    extra_cols = [c for c in cur_df.columns
                  if c not in feats and c not in spec["欄位"].values()]

    res: dict[str, Any] = {"類別": "特徵漂移", "門檻": f"PSI ≤ {PSI_ALERT}"}
    if missing_cols:
        err(f"當期資料缺了基準有的 {len(missing_cols)} 個特徵欄："
            f"{'、'.join(map(str, missing_cols))}",
            "先查上游欄位是不是被改名（03 W5：union_by_name 遇到改名會靜默拆成"
            "兩欄各半 NULL，全程零報錯）。確認改名後在契約檔 renames: 補一筆並"
            "COALESCE 回舊名，不要在這裡把欄位跳過 —— 跳過等於監控漏掉這個特徵")
        res.update({"結果": "error", "最大PSI": None, "告警特徵": missing_cols})
        return res, pd.DataFrame(), pd.DataFrame()

    summaries, detail_rows = [], []
    for name in feats:
        r = psi_for_feature(name, feats[name], cur_df[name])
        detail_rows.extend(r.pop("_rows"))
        summaries.append(r)

    tbl = pd.DataFrame(summaries).sort_values("PSI", ascending=False)
    det = pd.DataFrame(detail_rows)

    for rec in tbl.to_dict("records"):     # 用欄名取值，不用 itertuples
        detail(f"{rec['特徵']}（{rec['型別']}／{rec['有效箱數']} 箱）"
               f"PSI = {rec['PSI']:.4f}｜{rec['判級']}"
               f"｜雜訊期望 {rec['雜訊期望PSI']:.4f}")

    alert = tbl[tbl["判級"] == "告警"]
    watch = tbl[tbl["判級"] == "觀察"]
    res["最大PSI"] = float(tbl["PSI"].max()) if len(tbl) else None
    res["告警特徵"] = alert["特徵"].tolist()
    res["觀察特徵"] = watch["特徵"].tolist()
    res["結果"] = "pass"

    if len(alert):
        warn(f"{len(alert)} 個特徵 PSI > {PSI_ALERT}："
             + "、".join(f"{r['特徵']}={r['PSI']:.3f}"
                        for r in alert.to_dict("records")),
             "12 §十：該特徵分布已漂移，先查資料源，不要先重訓。"
             "對照漂移來源表點名事件：季節檔期／政策改變（免運門檻之類，"
             "政策上線日要進 dim_event）／品類改版／外部事件／量測變更"
             "（18-G10：口徑進 dim_metric_definition，橫跨變更日的時間窗要切開）")
        res["結果"] = "warning"
    elif len(watch) >= WATCH_CLUSTER_MIN:
        warn(f"{len(watch)} 個特徵同時落在觀察區（{PSI_WATCH} ≤ PSI ≤ {PSI_ALERT}）："
             + "、".join(f"{r['特徵']}={r['PSI']:.3f}"
                        for r in watch.to_dict("records")),
             "單一特徵輕微位移是雜訊，多個特徵同時位移符合 12 §十「外部事件」的"
             "徵狀（疫情、競品大促、平台演算法改版）。查當期有沒有可對應的事件，"
             "有就寫進 dim_event。此複合規則為本腳本自訂【推導，待驗證】")
        res["結果"] = "warning"
    else:
        ok(f"{len(tbl)} 個特徵的 PSI 全部 ≤ {PSI_ALERT}"
           f"（最大 {tbl['PSI'].max():.4f}，{tbl.iloc[0]['特徵']}）")

    # 樣本量太小的話，PSI 量到的是抽樣雜訊不是漂移
    noisy = tbl[tbl["雜訊期望PSI"] >= PSI_WATCH]
    if len(noisy):
        warn(f"{len(noisy)} 個特徵的雜訊期望 PSI ≥ {PSI_WATCH}"
             f"（最大 {noisy['雜訊期望PSI'].max():.4f}），"
             f"樣本量不足以把漂移和抽樣雜訊分開",
             f"當期 n={int(tbl['當期n'].iloc[0])}。要嘛累積到更多樣本再判，"
             f"要嘛減少箱數（E[PSI]≈(B−1)(1/n_基準+1/n_當期)，箱數減半雜訊就減半）。"
             f"在那之前這幾欄的 PSI 只能看方向，不可寫進報告當結論")
        if res["結果"] == "pass":
            res["結果"] = "warning"

    smoothed = tbl[tbl["平滑箱數"] > 0]
    if len(smoothed):
        info(f"{len(smoothed)} 個特徵有空箱被平滑（占比下限 {PSI_FLOOR_OBS}/n）："
             + "、".join(f"{r['特徵']}({r['平滑箱數']}箱)"
                        for r in smoothed.to_dict("records"))
             + " —— 這幾欄的 PSI 數值受平滑規則影響，只能當方向不能當量")

    unseen = tbl[tbl["當期未見類別數"] > 0]
    if len(unseen):
        warn("、".join(f"{r['特徵']} 有 {r['當期未見類別數']} 筆落在基準沒見過的類別"
                      for r in unseen.to_dict("records")),
             "12 §十 漂移來源表「產品／品類改版」：商品下架或品類重編會讓新水準"
             "冒出來。模型對沒見過的水準沒有學過任何東西，這批人的分數不可信。"
             "重訓前先清掉過期特徵、把新水準納入編碼")
        if res["結果"] == "pass":
            res["結果"] = "warning"

    if extra_cols:
        info(f"當期多出 {len(extra_cols)} 個基準沒有的欄位"
             f"（{'、'.join(map(str, extra_cols[:6]))}）—— 沒有基準占比可比，"
             f"本次不計 PSI。要納入監控必須 --rebaseline 重建基準")
    return res, tbl, det


def check_score_drift(spec: dict[str, Any], cur_df: pd.DataFrame,
                      cur_perf: dict[str, Any] | None) -> dict[str, Any]:
    print("\n② 預測分布漂移（12 §十：正類實際發生率相差 >30% 相對值 → 必須重訓）")
    res: dict[str, Any] = {"類別": "預測分布漂移"}
    sc = spec.get("score") or {}
    col = sc.get("col")
    score_done = False

    if not col or col not in cur_df.columns:
        warn("當期資料裡沒有分數欄，預測分布漂移這次沒有驗到",
             "用 --score-col 指定分數欄名；監控的第一手訊號就是分數分布，"
             "沒有它只能看特徵")
        res.update({"結果": "未驗", "分數PSI": None, "分數判級": "未驗"})
    else:
        score_done = True
        r = psi_for_feature(col, sc["bins"], cur_df[col])
        res["分數PSI"] = r["PSI"]
        res["分數判級"] = r["判級"]
        detail(f"分數 {col} 的 PSI = {r['PSI']:.4f}｜{r['判級']}"
               f"（{r['有效箱數']} 箱，雜訊期望 {r['雜訊期望PSI']:.4f}）")
        if r["判級"] == "告警":
            warn(f"分數分布 PSI = {r['PSI']:.4f} > {PSI_ALERT}",
                 "分數是所有特徵的合成，它動代表打進模型的母體變了。"
                 "先查是不是抽樣口徑改了（名單來源、資料表 join 條件），"
                 "再查特徵漂移表哪幾欄在推它。查完才決定要不要重訓")
            res["結果"] = "warning"
        else:
            ok(f"分數分布 PSI = {r['PSI']:.4f} ≤ {PSI_ALERT}")
            res["結果"] = "pass"

    # 正類實際發生率：reference 明寫「必須重訓」，所以這條進 error 桶
    base_m = spec.get("baseline_metrics") or {}
    base_rate = base_m.get("正類實際發生率")
    cur_rate = (cur_perf or {}).get("正類實際發生率")
    res["基準正類率"] = base_rate
    res["當期正類率"] = cur_rate
    if base_rate is None or cur_rate is None:
        info("缺基準或當期的實際結果，正類發生率這次沒有比對"
             "（監控的標籤本來就會落後，回填後補跑）")
        res.update({"正類率相對變化": None, "正類率比對": "未驗"})
        # 分數 PSI 跑掉了就不算整塊未驗；兩項都沒跑到才是未驗。
        # 這裡刻意不把 pass 改成 warning：那會讓 warning 桶與區塊結論對不上，
        # 而 warning 桶是退出碼的依據（00 §八）。
        if not score_done:
            res["結果"] = "未驗"
    elif base_rate <= 0:
        info(f"基準期正類發生率為 {base_rate}，相對變化無定義（分母為 0），標 N/A")
        res.update({"正類率相對變化": None, "正類率比對": "N/A"})
    else:
        rel = (cur_rate - base_rate) / base_rate
        res.update({"正類率相對變化": float(rel), "正類率比對": "已比對"})
        detail(f"正類實際發生率 基準 {base_rate:.4%} → 當期 {cur_rate:.4%}"
               f"（相對變化 {rel:+.1%}）")
        if abs(rel) > POS_RATE_REL_MAX:
            err(f"正類實際發生率相對變化 {rel:+.1%}，超過 ±{POS_RATE_REL_MAX:.0%}",
                "12 §十：母體變了，必須用最新資料重訓。重訓前先確認不是標籤口徑"
                "改了（18-G10）或標籤窗被檔期截斷（12 §二）。重訓後在 執行紀錄/ "
                "留下訓練窗、樣本數、out-of-time 分數、與前一版的名單重疊率")
            res["結果"] = "error"
        else:
            ok(f"正類發生率相對變化 {rel:+.1%} 在 ±{POS_RATE_REL_MAX:.0%} 內")
    return res


def check_performance(spec: dict[str, Any], cur_perf: dict[str, Any] | None
                      ) -> tuple[dict[str, Any], pd.DataFrame]:
    print(f"\n③ 效能衰退（12 §十：P/R 跌 >{PR_DROP_ABS:.0%} 絕對值、"
          f"lift < {LIFT_FLOOR}、calib_slope 偏離 ±{CALIB_SLOPE_TOL}）")
    res: dict[str, Any] = {"類別": "效能衰退"}
    base_m = spec.get("baseline_metrics") or {}

    if cur_perf is None:
        warn("當期沒有實際結果（標籤）欄，效能衰退這次沒有驗到",
             "用 --label-col 指定實際結果欄。監控的標籤本來就落後（要等 horizon "
             "走完），回填後補跑同一支腳本；在那之前報告不可寫「模型表現正常」，"
             "只能寫「分布未漂移，效能待回填」")
        res["結果"] = "未驗"
        return res, pd.DataFrame()
    if not base_m:
        warn("基準期沒有存效能指標，當期算得出來但沒有對照",
             "重建基準時基準資料要同時含分數與實際結果欄（--baseline 那份），"
             "否則 P/R 跌多少無從判斷。本次只印當期數字")
        res["結果"] = "未驗"

    rows = []
    for k in ("正類實際發生率", "precision@門檻", "recall@門檻",
              "top_decile_lift", "brier", "calib_slope"):
        b, c = base_m.get(k), cur_perf.get(k)
        d = (None if b is None or c is None
             or not np.isfinite(float(b)) or not np.isfinite(float(c))
             else float(c) - float(b))
        rows.append({"指標": k, "基準": _fmt_num(b), "當期": _fmt_num(c),
                     "差": _fmt_num(d, signed=True)})
    tbl = pd.DataFrame(rows)
    for rec in tbl.to_dict("records"):
        d = "" if rec["差"] == "N/A" else f"（{rec['差']}）"
        detail(f"{rec['指標']}：基準 {rec['基準']} → 當期 {rec['當期']}{d}")

    if res.get("結果") == "未驗":
        return res, tbl

    res["結果"] = "pass"
    # (a) P / R 跌 >5 個百分點 → 教材 §21 的告警。歸 error：這是效能本身垮了
    for k in ("precision@門檻", "recall@門檻"):
        b, c = base_m.get(k), cur_perf.get(k)
        if b is None or c is None:
            info(f"{k} 基準或當期為 N/A，這條沒有比對到")
            continue
        if (b - c) > PR_DROP_ABS:
            err(f"{k} 從 {b:.4f} 跌到 {c:.4f}（跌 {b - c:.4f}，"
                f"> {PR_DROP_ABS} 絕對值）",
                "12 §十／教材 §21 的告警線。照動作階梯往下走：先看 calib_slope "
                "是不是只是刻度跑掉（那只要重做校準），不是的話用最新資料重訓；"
                "重訓仍不行就回頭改特徵與標籤定義，再不行回 M0 重新問問題")
            res["結果"] = "error"
        else:
            ok(f"{k} {b:.4f} → {c:.4f}，跌幅在 {PR_DROP_ABS} 絕對值內")

    # (b) top_decile_lift < 2.0 → warning（reference 自己標【推導，待驗證】）
    lift = cur_perf.get("top_decile_lift")
    if lift is None:
        info("當期沒有正類，top_decile_lift 無定義（分母為 0），標 N/A")
    elif lift < LIFT_FLOOR:
        warn(f"top_decile_lift = {lift:.2f} 跌破 {LIFT_FLOOR}",
             f"12 §十 的告警線，reference 自己註明此門檻為【推導，待驗證】，"
             f"要以自己的歷史校準。先確認名單的商業價值：lift {lift:.2f} 代表前 "
             f"10% 名單命中率只有亂發的 {lift:.2f} 倍，接近 1 就等於模型沒在排序。"
             f"對照 12 §九：相對 naive baseline 提升 < 0.03 AUC 就該退回 baseline 排序")
        if res["結果"] == "pass":
            res["結果"] = "warning"
    else:
        ok(f"top_decile_lift = {lift:.2f} ≥ {LIFT_FLOOR}")

    # (c) calib_slope 偏離 1.0 超過 ±0.15 → warning（reference 明寫「不必重訓」）
    slope = cur_perf.get("calib_slope")
    if slope is None:
        warn("calib_slope 算不出來（每箱樣本 <30 或預測值無變異）",
             "12 §三：樣本 <30 的箱標 N/A。當期樣本太少就先不要用機率乘金額，"
             "只用排序（12 §五 Step 4）")
        if res["結果"] == "pass":
            res["結果"] = "warning"
    elif abs(slope - 1.0) > CALIB_SLOPE_TOL:
        direction = "高估" if slope < 1.0 else "低估"
        warn(f"calib_slope = {slope:.3f}，偏離 1.0 超過 ±{CALIB_SLOPE_TOL}"
             f"（模型系統性{direction}）",
             "12 §十：只重做校準，不必重訓全模型。用最新的校準集重跑 §三 的 "
             "Platt／Isotonic（正類 <5% 或校準集 <1000 筆選 Platt），比 Brier 決定。"
             "校準修好之前，M11 的所有 sizing 都不准用這個機率乘金額")
        if res["結果"] == "pass":
            res["結果"] = "warning"
    else:
        ok(f"calib_slope = {slope:.3f}，在 1.0 ± {CALIB_SLOPE_TOL} 內")
    return res, tbl


def check_list_overlap(spec: dict[str, Any], cur_df: pd.DataFrame,
                       top_pct: float) -> dict[str, Any]:
    print(f"\n④ 名單穩定度（12 §十 尾註：重疊率 <{LIST_OVERLAP_MIN:.0%} 要人工看一眼）")
    res: dict[str, Any] = {"類別": "名單穩定度"}
    base_list = spec.get("baseline_top_list")
    id_col = spec["欄位"].get("id")
    score_col = (spec.get("score") or {}).get("col")

    if not base_list or not id_col or id_col not in cur_df.columns \
            or not score_col or score_col not in cur_df.columns:
        warn("缺 id 欄或基準名單，名單重疊率這次沒有驗到",
             "用 --id-col 指定顧客 id 欄，並確保基準期那份也有同一欄。"
             "重疊率是行銷團隊唯一看得懂的漂移指標 —— 名單換了一批人，"
             "他們會在你之前發現")
        res.update({"結果": "未驗", "重疊率": None})
        return res

    cur = top_list(cur_df[id_col], cur_df[score_col].to_numpy(dtype=float), top_pct)
    inter = len(set(cur) & set(base_list))
    denom = max(min(len(cur), len(base_list)), 1)
    rate = inter / denom
    res.update({"重疊率": float(rate), "基準名單數": len(base_list),
                "當期名單數": len(cur), "交集": inter})
    detail(f"前 {top_pct:.0f}% 名單：基準 {len(base_list)} 人、當期 {len(cur)} 人、"
           f"交集 {inter} 人 → 重疊率 {rate:.1%}")
    if rate < LIST_OVERLAP_MIN:
        warn(f"名單重疊率 {rate:.1%} < {LIST_OVERLAP_MIN:.0%}",
             "12 §十：模型換了一批人，行銷團隊需要知道為什麼。人工抽 20 位"
             "「新進榜」與 20 位「掉出榜」比對特徵差異，寫進 預測追蹤.md。"
             "同時檢查是不是標籤反饋迴路 —— 上一輪只有被挑中的人收到 DM，"
             "訓練標籤已經被舊模型的選擇污染（對策：留 5–10% 隨機對照名單）")
        res["結果"] = "warning"
    else:
        ok(f"名單重疊率 {rate:.1%} ≥ {LIST_OVERLAP_MIN:.0%}")
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
#  動作階梯（12 §十）
# ══════════════════════════════════════════════════════════════
def action_ladder(blocks: list[dict[str, Any]]) -> str:
    steps = ["重做校準", "用最新資料重訓", "重做特徵與標籤定義", "回 M0 重新問問題"]
    by = {b["類別"]: b for b in blocks}
    pick = None
    perf = by.get("效能衰退", {})
    score = by.get("預測分布漂移", {})
    feat = by.get("特徵漂移", {})

    if perf.get("結果") == "error" or score.get("結果") == "error":
        pick = 1
    elif feat.get("結果") == "warning" or score.get("結果") == "warning":
        pick = 1
    elif perf.get("結果") == "warning":
        pick = 0
    lines = ["12 §十 的動作階梯（→ 標的是本次建議停在哪一階）："]
    for i, s in enumerate(steps):
        mark = "→ " if pick == i else "   "
        lines.append(f"  {mark}{i + 1}. {s}")
    if pick is None:
        lines.append("   本次四類檢查沒有觸發任何一階，維持現行模型與校準。")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
#  寫檔
# ══════════════════════════════════════════════════════════════
def write_outputs(p: Any, args: Any, spec: dict[str, Any],
                  blocks: list[dict[str, Any]], psi_tbl: pd.DataFrame,
                  psi_det: pd.DataFrame, perf_tbl: pd.DataFrame,
                  cur_perf: dict[str, Any] | None, cur_src: str,
                  exit_code: int) -> list[Path]:
    written: list[Path] = []
    tdir = p.tables / "預測模型"
    tdir.mkdir(parents=True, exist_ok=True)

    if len(psi_tbl):
        f = tdir / "監控_PSI.csv"
        psi_tbl.to_csv(f, index=False, encoding="utf-8-sig")
        written.append(f)
    if len(psi_det):
        f = tdir / "監控_PSI分箱明細.csv"
        psi_det.to_csv(f, index=False, encoding="utf-8-sig")
        written.append(f)
    if len(perf_tbl):
        f = tdir / "監控_效能對照.csv"
        perf_tbl.to_csv(f, index=False, encoding="utf-8-sig")
        written.append(f)

    p.models.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project": args.project,
        "current_source": cur_src,
        "baseline_source": spec.get("baseline_source"),
        "binning_fingerprint": spec.get("binning_fingerprint"),
        "分箱設定": spec.get("設定"),
        "blocks": blocks,
        "current_metrics": {k: _py(v) for k, v in (cur_perf or {}).items()},
        "baseline_metrics": spec.get("baseline_metrics"),
        "psi": psi_tbl.to_dict("records") if len(psi_tbl) else [],
        "errors": list(_errors),
        "warnings": list(_warnings),
        "exit_code": exit_code,
    }
    f = p.models / "model_monitor.json"
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                            default=_json_default), encoding="utf-8")
    written.append(f)

    # 交付物/預測追蹤.md —— 18-G15 指定落點，逐期追加不覆寫
    p.deliverables.mkdir(parents=True, exist_ok=True)
    md = p.deliverables / "預測追蹤.md"
    head = ("# 預測追蹤（18-G15）\n\n"
            "每期一節。**PSI 只在分箱指紋相同的期別之間可比** —— 指紋一換，"
            "下面的數字就要當成另一條序列重新起算。\n\n")
    if not md.exists():
        md.write_text(head, encoding="utf-8")
    sect = [f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} 監控紀錄\n",
            f"- 當期資料：`{cur_src}`",
            f"- 基準：`{spec.get('baseline_source')}`"
            f"（{spec.get('baseline_rows')} 列，建立於 {spec.get('generated_at')}）",
            f"- **分箱指紋：`{spec.get('binning_fingerprint')}`**"
            f"（{spec['設定']['method']}／{spec['設定']['n_bins']} 箱）",
            ""]
    for b in blocks:
        sect.append(f"- {b['類別']}：{b.get('結果')}")
    if len(psi_tbl):
        sect.append("\n| 特徵 | PSI | 判級 | 雜訊期望 PSI |")
        sect.append("|---|---:|---|---:|")
        for rec in psi_tbl.to_dict("records"):
            sect.append(f"| {rec['特徵']} | {rec['PSI']:.4f} | {rec['判級']} "
                        f"| {rec['雜訊期望PSI']:.4f} |")
    if _errors:
        sect.append("\n**error**")
        sect += [f"- {e}" for e in _errors]
    if _warnings:
        sect.append("\n**warning**")
        sect += [f"- {w}" for w in _warnings]
    sect.append("\n" + action_ladder(blocks) + "\n")
    with md.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(sect) + "\n")
    written.append(md)

    # 執行紀錄：逐次留痕，供跨期比對（12 §十「留痕」）
    p.log.mkdir(parents=True, exist_ok=True)
    runs = p.log / "monitor_runs.csv"
    row = pd.DataFrame([{
        "時間": datetime.now().isoformat(timespec="seconds"),
        "當期資料": cur_src,
        "當期n": int((cur_perf or {}).get("n", 0)) or (
            int(psi_tbl["當期n"].iloc[0]) if len(psi_tbl) else 0),
        "分箱指紋": spec.get("binning_fingerprint"),
        # 留痕檔一樣不留空白格（00 §四）：算不出來寫 N/A，不要讓下游讀成 0
        "最大PSI": _fmt_num(float(psi_tbl["PSI"].max()) if len(psi_tbl) else None),
        "分數PSI": _fmt_num(next((b.get("分數PSI") for b in blocks
                                 if b["類別"] == "預測分布漂移"), None)),
        "error數": len(_errors), "warning數": len(_warnings),
        "退出碼": exit_code,
    }])
    row.to_csv(runs, mode="a", header=not runs.exists(),
               index=False, encoding="utf-8-sig")
    written.append(runs)
    return written


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    spec_path: Path = args.spec or (p.models / "monitor_baseline.json")

    # ── 基準 spec：有就重用，沒有才建。這是「下次算的可比」的全部關鍵 ──
    spec: dict[str, Any] | None = None
    if spec_path.exists() and not args.rebaseline:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if args.baseline:
            err(f"已經有基準 {spec_path.name}（指紋 {spec.get('binning_fingerprint')}），"
                f"又給了 --baseline",
                "再建一次基準會產生另一組切點，兩期 PSI 就不可比了。"
                "要沿用舊基準就別給 --baseline；真的要換基準（換模型、換特徵定義）"
                "請明示 --rebaseline，腳本會在 預測追蹤.md 標出歷史斷點")
            return EX_ERROR
        bad = spec_incompatibilities(spec, n_bins=args.bins, method=args.binning)
        if bad:
            err("本次指定的分箱參數與既有基準不一致：" + "；".join(bad),
                "PSI 對分箱極度敏感，換一組切點算出來的數字與歷史不可比"
                "（--self-test 第 ⑤ 項會示範同一對資料換箱數 PSI 差多少）。"
                "要嘛拿掉這些旗標沿用基準的設定，要嘛 --rebaseline 重建基準"
                "並在 預測追蹤.md 標明從哪一期起換了尺")
            return EX_ERROR
    else:
        if not args.baseline:
            raise FileNotFoundError(
                f"還沒有基準檔（{spec_path}），也沒給 --baseline。\n"
                f"  第一次監控要先用上線那批資料建基準："
                f"model_monitor.py {args.project} --baseline <上線基準.parquet>\n"
                f"  分箱切點只從基準期算，之後每期重用 —— 每期各自分箱等於每期換一把尺。")
        base_df = load_table(args.baseline, "基準期資料")
        score_col = pick_col(base_df, args.score_col, SCORE_CANDIDATES, "分數")
        label_col = pick_col(base_df, args.label_col, LABEL_CANDIDATES, "實際結果")
        id_col = pick_col(base_df, args.id_col, ID_CANDIDATES, "id")
        feats = (args.features.split(",") if args.features
                 else default_features(base_df,
                                       {c for c in (score_col, label_col, id_col) if c}))
        miss = [c for c in feats if c not in base_df.columns]
        if miss:
            raise ValueError(f"--features 指定的欄位不在基準資料裡：{'、'.join(miss)}")
        spec = build_spec(base_df, feats,
                          n_bins=args.bins or DEFAULT_BINS,
                          method=args.binning or "quantile",
                          score_col=score_col, label_col=label_col, id_col=id_col,
                          threshold=args.threshold, top_pct=args.top_pct,
                          source=str(args.baseline))
        p.models.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2,
                                        default=_json_default), encoding="utf-8")
        print(f"✓ 基準與分箱規則已存：{spec_path}")
        print(f"  分箱指紋 {spec['binning_fingerprint']}"
              f"（{spec['設定']['method']}／{spec['設定']['n_bins']} 箱）"
              f" ← 之後每期都必須是這個指紋，PSI 才可比")
        if args.rebaseline:
            warn("已重建基準，歷史 PSI 與本期起的 PSI 不可比",
                 "在 交付物/預測追蹤.md 標明斷點：從本期起換了分箱規則，"
                 "之前的 PSI 序列不可與之後的直接比大小。"
                 "重建理由（換模型？換特徵定義？）也要寫進去")

    # ── 當期資料 ─────────────────────────────────────────
    cur_path = args.current or (p.models / "monitor_current.parquet")
    if not cur_path.exists():
        if args.baseline:
            print("\n本次只建立基準，沒有當期資料可比對。")
            print(f"下一期跑：model_monitor.py {args.project} --current <當期.parquet>")
            return EX_WARN if _warnings else EX_OK
        raise FileNotFoundError(
            f"找不到當期資料：{cur_path}\n  用 --current 指定，或放到 模型輸出/monitor_current.parquet")
    cur_df = load_table(cur_path, "當期資料")

    score_col = (spec.get("score") or {}).get("col")
    label_col = spec["欄位"].get("label")
    id_col = spec["欄位"].get("id")

    print("=" * 72)
    print("行銷數據分析 Skill — 模型上線後監控（12 §十，對應 18-G15）")
    print(f"專案：{args.project}")
    print(f"基準：{spec.get('baseline_source')}（{spec.get('baseline_rows'):,} 列）")
    print(f"當期：{cur_path.name}（{len(cur_df):,} 列）")
    print(f"分箱指紋：{spec.get('binning_fingerprint')}"
          f"｜{spec['設定']['method']}／{spec['設定']['n_bins']} 箱"
          f"｜切點取自基準期，本期重用")
    print("=" * 72)

    cur_perf = None
    if score_col in cur_df.columns and label_col and label_col in cur_df.columns:
        cur_perf = perf_metrics(cur_df[score_col].to_numpy(dtype=float),
                                cur_df[label_col].to_numpy(dtype=float),
                                threshold=spec["設定"].get("threshold"),
                                top_pct=spec["設定"].get("top_pct", DEFAULT_TOP_PCT))

    blocks: list[dict[str, Any]] = []
    b1, psi_tbl, psi_det = check_feature_drift(spec, cur_df)
    blocks.append(b1)
    if b1["結果"] == "error":
        # 欄位都對不上就不必往下算了 —— 後面每個數字都會是錯的對象
        print("\n" + "=" * 72)
        print("結果：⛔ 欄位對不上，後三類檢查不跑（比錯對象的數字比沒有數字更糟）")
        return EX_ERROR

    blocks.append(check_score_drift(spec, cur_df, cur_perf))
    b3, perf_tbl = check_performance(spec, cur_perf)
    blocks.append(b3)
    blocks.append(check_list_overlap(spec, cur_df,
                                     spec["設定"].get("top_pct", DEFAULT_TOP_PCT)))

    n_err = len(_errors)
    n_warn = len(_warnings)
    ran = sum(1 for b in blocks if b.get("結果") != "未驗")

    print("\n" + "=" * 72)
    print(f"跑了 {ran}／4 類檢查｜error {n_err}、warning {n_warn}")
    if ran < 4:
        skipped = [b["類別"] for b in blocks if b.get("結果") == "未驗"]
        print(f"      ⚠ 未驗到：{'、'.join(skipped)}。"
              f"報告不可寫「監控全部通過」，只能寫跑到的那幾類。")
    if n_err:
        print(f"結果：⛔ 有 {n_err} 條 error → 模型不可照原樣繼續用。")
    elif n_warn:
        print(f"結果：⚠ 有 {n_warn} 條 warning → 可往下，預測追蹤.md 要逐條寫明處置。")
    else:
        print(f"結果：✅ 跑到的 {ran} 類全過。")
    print("\n" + action_ladder(blocks))

    exit_code = EX_ERROR if n_err else (EX_WARN if n_warn else EX_OK)
    if not args.no_write:
        for f in write_outputs(p, args, spec, blocks, psi_tbl, psi_det,
                               perf_tbl, cur_perf, str(cur_path), exit_code):
            print(f"✓ {f}")
    return exit_code


# ══════════════════════════════════════════════════════════════
#  自我測試
# ══════════════════════════════════════════════════════════════
def _make_pop(rng: np.random.Generator, n: int, *, loc: float = 8.0,
              sigma: float = 0.8, cat_p: tuple[float, ...] = (0.4, 0.3, 0.2, 0.1),
              na_rate: float = 0.05, levels: tuple[str, ...] = ("北", "中", "南", "東")
              ) -> pd.DataFrame:
    """造一份顧客特徵表。改 loc/sigma/cat_p/na_rate 就是製造漂移。"""
    amt = rng.lognormal(loc, sigma, n)
    rec = rng.gamma(2.0, 30.0, n)
    freq = rng.poisson(3.0, n).astype(float)
    reg = rng.choice(list(levels), size=n, p=list(cat_p))
    if na_rate > 0:
        mask = rng.random(n) < na_rate
        rec = np.where(mask, np.nan, rec)
    return pd.DataFrame({"金額": amt, "最近購買間隔": rec, "頻率": freq, "地區": reg})


def _selftest() -> int:
    print("=" * 72)
    print("model_monitor.py 自我測試")
    print("=" * 72)
    rng = np.random.default_rng(20260728)
    failed: list[str] = []
    measured: list[str] = []

    def check(name: str, cond: bool, got: str = "") -> None:
        if cond:
            print(f"  ✓ {name}" + (f"（{got}）" if got else ""))
        else:
            print(f"  ✗ {name}" + (f"（{got}）" if got else ""))
            failed.append(name)

    # ① PSI 公式：與手算對照（雙路徑，00 §1.3）
    base = np.array([50.0, 50.0])
    cur = np.array([60.0, 40.0])
    手算 = (0.6 - 0.5) * np.log(0.6 / 0.5) + (0.4 - 0.5) * np.log(0.4 / 0.5)
    got = psi_from_counts(base, cur)["psi"]
    check("① PSI 公式與手算一致", abs(got - 手算) < 1e-12,
          f"腳本 {got:.9f} vs 手算 {手算:.9f}")

    # ② PSI 對稱性：互換基準與當期，值不變
    swp = psi_from_counts(cur, base)["psi"]
    check("② PSI 對稱（互換兩期值相同）", abs(got - swp) < 1e-12,
          f"{got:.9f} vs {swp:.9f}")

    # ③ 沒漂移：同一母體重抽，全部特徵 PSI < 0.10（不該叫的不准叫）
    n = 4000
    df_b = _make_pop(rng, n)
    df_same = _make_pop(rng, n)
    spec_same = build_spec(df_b, ["金額", "最近購買間隔", "頻率", "地區"],
                           n_bins=DEFAULT_BINS, method="quantile",
                           score_col=None, label_col=None, id_col=None,
                           threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    _reset_buckets()
    r_same, tbl_same, _ = check_feature_drift(spec_same, df_same)
    check("③ 無漂移資料：四個特徵 PSI 全 < 0.10 且判 pass",
          r_same["結果"] == "pass" and float(tbl_same["PSI"].max()) < PSI_WATCH,
          f"最大 PSI={tbl_same['PSI'].max():.4f}（{tbl_same.iloc[0]['特徵']}）")
    measured.append(f"無漂移（n={n}，等頻10箱）最大 PSI={tbl_same['PSI'].max():.4f}")

    # ④ 有漂移：金額整體上移 + 類別占比翻轉 → 必須抓到
    df_drift = _make_pop(rng, n, loc=8.5, sigma=1.0,
                         cat_p=(0.1, 0.2, 0.3, 0.4), na_rate=0.05)
    _reset_buckets()
    r_dr, tbl_dr, det_dr = check_feature_drift(spec_same, df_drift)
    amt_psi = float(tbl_dr.loc[tbl_dr["特徵"] == "金額", "PSI"].iloc[0])
    reg_psi = float(tbl_dr.loc[tbl_dr["特徵"] == "地區", "PSI"].iloc[0])
    check("④ 有漂移資料：金額與地區都被判「告警」",
          r_dr["結果"] == "warning" and amt_psi > PSI_ALERT and reg_psi > PSI_ALERT,
          f"金額 PSI={amt_psi:.4f}、地區 PSI={reg_psi:.4f}")
    check("④b 有漂移時沒有誤判沒動的特徵（頻率）",
          float(tbl_dr.loc[tbl_dr["特徵"] == "頻率", "PSI"].iloc[0]) < PSI_ALERT,
          f"頻率 PSI={float(tbl_dr.loc[tbl_dr['特徵'] == '頻率', 'PSI'].iloc[0]):.4f}")
    measured.append(f"有漂移 金額 PSI={amt_psi:.4f}、地區 PSI={reg_psi:.4f}")

    # ⑤ 分箱敏感度：同一對資料，換箱數 PSI 就變 —— 這是本腳本存分箱規則的理由
    psis = {}
    for b in (5, 10, 20):
        sp = build_spec(df_b, ["金額"], n_bins=b, method="quantile",
                        score_col=None, label_col=None, id_col=None,
                        threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
        psis[b] = psi_for_feature("金額", sp["features"]["金額"], df_drift["金額"])["PSI"]
    sp_ew = build_spec(df_b, ["金額"], n_bins=10, method="equal_width",
                       score_col=None, label_col=None, id_col=None,
                       threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    psi_ew = psi_for_feature("金額", sp_ew["features"]["金額"], df_drift["金額"])["PSI"]
    spread = max(psis.values()) / max(min(psis.values()), 1e-12)
    check("⑤ PSI 對分箱敏感（換箱數／換方法數字就變）",
          spread > 1.2 and abs(psi_ew - psis[10]) > 0.01,
          f"5箱={psis[5]:.4f}／10箱={psis[10]:.4f}／20箱={psis[20]:.4f}"
          f"／等寬10箱={psi_ew:.4f}")
    measured.append(f"同一對資料 金額 PSI：等頻5箱={psis[5]:.4f}、10箱={psis[10]:.4f}、"
                    f"20箱={psis[20]:.4f}、等寬10箱={psi_ew:.4f}")

    # ⑥ 分箱指紋：同設定同指紋，換箱數換指紋
    sp10a = build_spec(df_b, ["金額"], n_bins=10, method="quantile",
                       score_col=None, label_col=None, id_col=None,
                       threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    sp10b = build_spec(df_b, ["金額"], n_bins=10, method="quantile",
                       score_col=None, label_col=None, id_col=None,
                       threshold=None, top_pct=DEFAULT_TOP_PCT, source="別的路徑")
    sp20 = build_spec(df_b, ["金額"], n_bins=20, method="quantile",
                      score_col=None, label_col=None, id_col=None,
                      threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    check("⑥ 指紋：同切點同指紋、換箱數換指紋",
          sp10a["binning_fingerprint"] == sp10b["binning_fingerprint"]
          and sp10a["binning_fingerprint"] != sp20["binning_fingerprint"],
          f"{sp10a['binning_fingerprint']} vs {sp20['binning_fingerprint']}")

    # ⑦ 相容性：基準 10 箱、本次指定 20 箱 → 必須擋（不可比）
    bad = spec_incompatibilities(sp10a, n_bins=20, method=None)
    good = spec_incompatibilities(sp10a, n_bins=None, method=None)
    good2 = spec_incompatibilities(sp10a, n_bins=10, method="quantile")
    check("⑦ 分箱參數不一致會被判不可比，一致或未指定則放行",
          len(bad) == 1 and good == [] and good2 == [], f"不相容原因={bad}")

    # ⑧ 端箱：當期出現比基準更極端的值 → 落進端箱，占比總和仍為 1
    fs_amt = sp10a["features"]["金額"]
    extreme = pd.Series(np.concatenate([df_b["金額"].to_numpy(),
                                        np.array([1e12, -1e12])]))
    cnt, _ = bin_counts(extreme, fs_amt)
    check("⑧ 超出基準範圍的極端值不會被丟掉（端箱 ±inf 開放）",
          int(cnt.sum()) == len(extreme),
          f"樣本 {len(extreme)}、落箱 {int(cnt.sum())}")

    # ⑨ 未見類別：當期出現新水準 → 歸 __未見類別__ 箱並被點名
    spec_cat = build_spec(df_b, ["地區"], n_bins=DEFAULT_BINS, method="quantile",
                          score_col=None, label_col=None, id_col=None,
                          threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    df_newlv = _make_pop(rng, 1500, levels=("北", "中", "南", "離島"))
    _reset_buckets()
    r_lv, tbl_lv, _ = check_feature_drift(spec_cat, df_newlv[["地區"]])
    check("⑨ 未見類別被歸箱、被點名、且觸發 warning",
          int(tbl_lv["當期未見類別數"].iloc[0]) > 0 and r_lv["結果"] == "warning",
          f"未見類別 {int(tbl_lv['當期未見類別數'].iloc[0])} 筆")

    # ⑩ 缺值：缺值率暴增要抓到；缺值率沒動不准叫
    spec_na = build_spec(df_b, ["最近購買間隔"], n_bins=DEFAULT_BINS,
                         method="quantile", score_col=None, label_col=None,
                         id_col=None, threshold=None, top_pct=DEFAULT_TOP_PCT,
                         source="selftest")
    df_na = _make_pop(rng, n, na_rate=0.45)
    psi_na = psi_for_feature("最近購買間隔", spec_na["features"]["最近購買間隔"],
                             df_na["最近購買間隔"])
    psi_na0 = psi_for_feature("最近購買間隔", spec_na["features"]["最近購買間隔"],
                              _make_pop(rng, n, na_rate=0.05)["最近購買間隔"])
    check("⑩ 缺值率 5%→45% 被 PSI 抓到，缺值率沒動則不叫",
          psi_na["PSI"] > PSI_ALERT and psi_na0["PSI"] < PSI_WATCH,
          f"缺值暴增 PSI={psi_na['PSI']:.4f}、未變 PSI={psi_na0['PSI']:.4f}")
    measured.append(f"缺值率 5%→45% 的 PSI={psi_na['PSI']:.4f}")

    # ⑪ 空箱平滑：當期整箱沒人 → PSI 有限、被標記，而不是 inf
    r_zero = psi_from_counts(np.array([100.0, 100.0, 100.0]),
                             np.array([150.0, 150.0, 0.0]))
    check("⑪ 空箱不讓 PSI 變成 inf，且被標記為已平滑",
          np.isfinite(r_zero["psi"]) and r_zero["n_smoothed"] == 1,
          f"PSI={r_zero['psi']:.4f}、平滑箱 {r_zero['n_smoothed']}")

    # ⑫ 雜訊期望 PSI 的公式 vs 模擬（雙路徑；n 小的時候 PSI 天生就高）
    n_small, B, reps = 200, 10, 300
    sim = []
    for _ in range(reps):
        a = rng.normal(0, 1, n_small)
        c = rng.normal(0, 1, n_small)
        edges = np.unique(np.quantile(a, np.linspace(0, 1, B + 1)[1:-1]))
        fs = {"type": "numeric", "method": "quantile", "levels": [],
              "edges": [float(e) for e in edges],
              "labels": _numeric_labels([float(e) for e in edges]) + [MISSING_BIN]}
        cb, _ = bin_counts(pd.Series(a), fs)
        cc, _ = bin_counts(pd.Series(c), fs)
        sim.append(psi_from_counts(cb, cc)["psi"])
    sim_mean = float(np.mean(sim))
    pred = expected_noise_psi(n_small, n_small, B + 1)   # +1 = 缺值箱
    check("⑫ 雜訊期望 PSI 公式與模擬相符（誤差 < 25%）",
          abs(sim_mean - pred) / pred < 0.25,
          f"模擬均值 {sim_mean:.4f} vs 公式 {pred:.4f}（n={n_small}、B={B}）")
    measured.append(f"同母體、n=200、等頻10箱：模擬 PSI 均值={sim_mean:.4f}"
                    f"（公式預測 {pred:.4f}）")

    # ⑬ 小樣本 guard：n 小 → 明說 PSI 不可信；n 大 → 不叫
    df_tiny_b, df_tiny_c = _make_pop(rng, 150), _make_pop(rng, 150)
    sp_tiny = build_spec(df_tiny_b, ["金額"], n_bins=DEFAULT_BINS, method="quantile",
                         score_col=None, label_col=None, id_col=None,
                         threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    _reset_buckets()
    r_tiny, _, _ = check_feature_drift(sp_tiny, df_tiny_c)
    tiny_warned = any("雜訊期望" in w for w in _warnings)
    _reset_buckets()
    check_feature_drift(spec_same, df_same)
    big_warned = any("雜訊期望" in w for w in _warnings)
    check("⑬ 小樣本會警告 PSI 不可信，大樣本不亂叫",
          tiny_warned and not big_warned, f"n=150 警告={tiny_warned}、n=4000 警告={big_warned}")

    # ⑭ 效能：P/R 跌 >5pp → error；持平 → 不叫
    def _scored(n_: int, strength: float, rate: float = 0.05) -> pd.DataFrame:
        z = rng.normal(0, 1, n_)
        lin = np.log(rate / (1 - rate)) + strength * z
        pr = 1 / (1 + np.exp(-lin))
        y = (rng.random(n_) < pr).astype(float)
        return pd.DataFrame({"客戶編號": [f"C{i:05d}" for i in range(n_)],
                             "score": pr, "label": y, "z": z})

    b_perf = _scored(6000, 1.6)
    c_good = _scored(6000, 1.6)
    c_bad = _scored(6000, 0.0)          # 分數與結果脫鉤 → 名單品質垮掉
    sp_perf = build_spec(b_perf, ["z"], n_bins=DEFAULT_BINS, method="quantile",
                         score_col="score", label_col="label", id_col="客戶編號",
                         threshold=None, top_pct=DEFAULT_TOP_PCT, source="selftest")
    m_good = perf_metrics(c_good["score"].to_numpy(), c_good["label"].to_numpy(),
                          threshold=None, top_pct=DEFAULT_TOP_PCT)
    m_bad = perf_metrics(c_bad["score"].to_numpy(), c_bad["label"].to_numpy(),
                         threshold=None, top_pct=DEFAULT_TOP_PCT)
    _reset_buckets()
    r_pg, _ = check_performance(sp_perf, m_good)
    _reset_buckets()
    r_pb, _ = check_performance(sp_perf, m_bad)
    check("⑭ 效能持平不叫、效能垮掉判 error",
          r_pg["結果"] == "pass" and r_pb["結果"] == "error",
          f"基準 P={sp_perf['baseline_metrics']['precision@門檻']:.4f}／"
          f"持平 P={m_good['precision@門檻']:.4f}／垮掉 P={m_bad['precision@門檻']:.4f}")
    measured.append(f"效能情境：基準 P={sp_perf['baseline_metrics']['precision@門檻']:.4f}、"
                    f"lift={sp_perf['baseline_metrics']['top_decile_lift']:.2f}；"
                    f"脫鉤後 P={m_bad['precision@門檻']:.4f}、"
                    f"lift={m_bad['top_decile_lift']:.2f}")

    # ⑮ top_decile_lift：好模型不叫、脫鉤模型叫
    check("⑮ lift 判定：好模型 ≥2 不叫、脫鉤模型 <2 叫",
          m_good["top_decile_lift"] >= LIFT_FLOOR
          and m_bad["top_decile_lift"] < LIFT_FLOOR,
          f"好 {m_good['top_decile_lift']:.2f}／脫鉤 {m_bad['top_decile_lift']:.2f}")

    # ⑯ calib_slope：校準良好 ≈1；系統性高估 → 偏離 >0.15 被抓到
    s_ok, _ = calib_slope(c_good["score"].to_numpy(), c_good["label"].to_numpy())
    infl = np.clip(c_good["score"].to_numpy() * 2.2, 0, 0.999)
    s_bad, _ = calib_slope(infl, c_good["label"].to_numpy())
    check("⑯ calib_slope：良好校準 ≈1，機率灌水後偏離被抓到",
          abs(s_ok - 1.0) <= CALIB_SLOPE_TOL and abs(s_bad - 1.0) > CALIB_SLOPE_TOL,
          f"良好 {s_ok:.3f}／灌水 {s_bad:.3f}")
    measured.append(f"calib_slope：校準良好={s_ok:.3f}、機率×2.2 後={s_bad:.3f}")

    # ⑰ 正類發生率相對變化 >30% → error；小幅變化不叫
    df_rate_hi = c_good.copy()
    df_rate_hi["label"] = (rng.random(len(df_rate_hi))
                           < c_good["score"].to_numpy() * 2.0).astype(float)
    m_hi = perf_metrics(df_rate_hi["score"].to_numpy(), df_rate_hi["label"].to_numpy(),
                        threshold=None, top_pct=DEFAULT_TOP_PCT)
    _reset_buckets()
    r_rate_hi = check_score_drift(sp_perf, df_rate_hi, m_hi)
    _reset_buckets()
    r_rate_ok = check_score_drift(sp_perf, c_good, m_good)
    check("⑰ 正類發生率暴增判 error、持平不叫",
          r_rate_hi["結果"] == "error" and r_rate_ok["結果"] == "pass",
          f"相對變化 暴增={r_rate_hi['正類率相對變化']:+.1%}、"
          f"持平={r_rate_ok['正類率相對變化']:+.1%}")

    # ⑱ 名單重疊率：同一份資料 = 100%；分數打亂 → 掉到門檻以下
    _reset_buckets()
    r_ov_same = check_list_overlap(sp_perf, b_perf, DEFAULT_TOP_PCT)
    shuffled = b_perf.copy()
    shuffled["score"] = rng.permutation(shuffled["score"].to_numpy())
    _reset_buckets()
    r_ov_diff = check_list_overlap(sp_perf, shuffled, DEFAULT_TOP_PCT)
    check("⑱ 名單重疊率：同名單 100% 不叫、打亂後 <50% 叫",
          r_ov_same["結果"] == "pass" and r_ov_diff["結果"] == "warning",
          f"同 {r_ov_same['重疊率']:.1%}／打亂 {r_ov_diff['重疊率']:.1%}")

    # ⑲ 沒有標籤時，效能區塊要標「未驗」，不准報 pass
    _reset_buckets()
    r_nolab, _ = check_performance(sp_perf, None)
    check("⑲ 沒有實際結果時效能標「未驗」而非 pass", r_nolab["結果"] == "未驗",
          f"結果={r_nolab['結果']}")

    # ⑳ 欄位對不上要擋（03 W5：欄位改名會靜默拆欄，全程零報錯）
    _reset_buckets()
    r_missing, _, _ = check_feature_drift(spec_same, df_same.drop(columns=["地區"]))
    check("⑳ 當期缺了基準的特徵欄 → error", r_missing["結果"] == "error",
          f"結果={r_missing['結果']}")

    # ㉑ 結果要能寫成 JSON（numpy 純量不外洩）
    try:
        json.dumps({"blocks": [r_dr, r_pb, r_ov_diff],
                    "psi": tbl_dr.to_dict("records"),
                    "detail": det_dr.head(20).to_dict("records"),
                    "spec": sp_perf},
                   ensure_ascii=False, default=_json_default)
        ser_ok, ser_msg = True, "含分箱次數與占比仍可序列化"
    except TypeError as e:
        ser_ok, ser_msg = False, str(e)
    check("㉑ 監控結果可寫成 JSON", ser_ok, ser_msg)

    # ㉒ 動作階梯：垮掉的情境要指到「重訓」而不是停在「重做校準」
    ladder_bad = action_ladder([r_dr, r_rate_hi, r_pb, r_ov_diff])
    ladder_ok = action_ladder([r_same, r_rate_ok, r_pg, r_ov_same])
    check("㉒ 動作階梯：有 error 指向重訓、全過時不指任何一階",
          "→ 2. 用最新資料重訓" in ladder_bad
          and "沒有觸發任何一階" in ladder_ok)

    # ㉓ 效能對照表不准有 NaN／空白格（00 §四；verify_outputs 的 CELL_RULES）
    #    m_bad 的 calib_slope 算不出來 —— 早期版本讓它掉進 pandas 變成 nan，
    #    印出來是「當期 nan」、寫進 CSV 是空白格，兩種讀法都會被誤讀成 0
    _reset_buckets()
    _, tbl_na = check_performance(sp_perf, m_bad)
    flat = [str(v) for rec in tbl_na.to_dict("records") for v in rec.values()]
    check("㉓ 算不出來的指標寫 N/A，表裡沒有 nan／空白格",
          "N/A" in flat and not any(v.strip() == "" or v.lower() in ("nan", "none")
                                    for v in flat),
          f"calib_slope 當期="
          f"{tbl_na.loc[tbl_na['指標'] == 'calib_slope', '當期'].iloc[0]}")

    print("\n" + "-" * 72)
    print("本次實測到的數字（都是這一輪真的跑出來的）：")
    for m in measured:
        print(f"  · {m}")

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過（23 項）")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="模型上線後監控（12 §十）：PSI／特徵漂移／預測分布漂移／效能衰退。"
                    "分箱規則只從基準期算一次並存檔，之後每期重用 —— 換規則 PSI 就不可比。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--baseline", type=Path,
                    help="基準期資料（上線那批）。只在建立／重建基準時給")
    ap.add_argument("--current", type=Path,
                    help="當期資料（預設 模型輸出/monitor_current.parquet）")
    ap.add_argument("--spec", type=Path,
                    help="基準與分箱規則 JSON（預設 模型輸出/monitor_baseline.json）")
    ap.add_argument("--rebaseline", action="store_true",
                    help="重建基準（會換分箱指紋，歷史 PSI 從此不可比）")
    ap.add_argument("--features", help="要監控的特徵欄，逗號分隔（預設除 id／分數／標籤外全部）")
    ap.add_argument("--score-col", help="預測分數欄名")
    ap.add_argument("--label-col", help="實際結果欄名（沒回填就先不給，效能項會標未驗）")
    ap.add_argument("--id-col", help="顧客 id 欄名（算名單重疊率要用）")
    ap.add_argument("--bins", type=int,
                    help=f"分箱數（建立基準時預設 {DEFAULT_BINS}；已有基準時給了會做相容性檢查）")
    ap.add_argument("--binning", choices=BIN_METHODS,
                    help="分箱方法（建立基準時預設 quantile 等頻）")
    ap.add_argument("--threshold", type=float,
                    help="precision/recall 用的機率門檻（不給就用 top-pct 的分位點）")
    ap.add_argument("--top-pct", type=float, default=DEFAULT_TOP_PCT,
                    help=f"名單比例%%，用於門檻與名單重疊率（預設 {DEFAULT_TOP_PCT:.0f}）")
    ap.add_argument("--no-write", action="store_true", help="只檢查，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")
    # 參數值不合法在 argparse 層擋掉 → 64（腳本根本沒跑），不要掉到執行期變成 1
    if args.bins is not None and not (2 <= args.bins <= 100):
        ap.error(f"--bins 要在 2–100 之間，拿到 {args.bins}"
                 f"（箱數太少看不出形狀、太多每箱樣本不足，PSI 全是雜訊）")
    if not (0 < args.top_pct <= 100):
        ap.error(f"--top-pct 要在 (0, 100] 之間，拿到 {args.top_pct}")
    if args.threshold is not None and not (0.0 <= args.threshold <= 1.0):
        ap.error(f"--threshold 是機率門檻，要在 [0, 1] 之間，拿到 {args.threshold}")

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
        print(f"⛔ model_monitor.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
