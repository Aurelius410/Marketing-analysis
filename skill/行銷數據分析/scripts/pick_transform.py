#!/usr/bin/env python3
"""
M3 轉換方法選用 —— 給一個數值欄，依 `references/06_前處理與轉換.md` §一 的
七情境順位表判斷「第一順位該做什麼、為什麼不做第二順位」。

為什麼需要這支（不寫理由的腳本沒人會用）：
  · **選錯轉換不會報錯，只會安靜地錯掉。** 右偏金額取 log 建模再 exp 回去，
    平均客單價 1,909.73 會被報成 688（少算 64%），而 R²、殘差圖、Q-Q plot
    全部正常 —— 沒有任何診斷會跳出來（06 §二）。這支在**選方法的當下**就擋。
  · **順序也會錯。** 先 winsorize 再轉換，會砍掉客戶 5425 一個人 25.8 萬的
    真實消費，讓他掉出 VIP 名單。06 §三 的鐵則是「先轉換 → 再看還有沒有
    離群 → 才 winsorize」，這支把那棵決策樹寫成程式。
  · **理由要寫在紀錄裡。** 06 §六 的六欄格式第 4 欄（為什麼是它：第幾順位、
    前面的為什麼不行）是整份轉換紀錄存在的理由。人手寫會漏，這支自動產。

這支只「建議」不「執行」（06 §一 程式碼區塊的原話）。輸出要進
`顧客特徵表/transform_log.csv` 之前由人確認，實際寫檔是 write_transform_log.py。

三桶輸出 + 退出碼（沿用 setup_check.py 的形式）：
    0 = 通過，可以照建議做
    1 = 有 error，擋住（零膨脹要改模型／天花板效應／反轉換偏誤／比率或時間欄取 log）
    2 = 只有 warning，可以做但要補動作（灰帶零佔比、arcsinh 敏感度、分支 C 條件）

用法：
    # 從 parquet 讀一個欄，用途是預測
    python pick_transform.py 2026Q3_電商 --parquet 原始資料/txn.parquet \\
        --col 刷卡金額 --purpose predict

    # 用途只是分群輸入／畫圖
    python pick_transform.py 2026Q3_電商 --parquet txn.parquet --col 刷卡金額 \\
        --purpose cluster

    # 從專案資料庫的表讀，並宣告你打算用什麼（--want 會被驗證）
    python pick_transform.py 2026Q3_電商 --table mart.fact_transaction \\
        --col line_amount_net --want log --purpose predict     # → ⛔ 反轉換偏誤

    # 尺度檢查（情境 7）：把同一批要進距離模型的欄一起給
    python pick_transform.py 2026Q3_電商 --parquet rfm.parquet --col M \\
        --peer-cols R,F

    # 反轉換偏誤單獨檢查（不需要資料）
    python pick_transform.py 2026Q3_電商 --check-exp \\
        --deliverable pred_amount --action exp

    # 用課程資料集樣本跑完整自我測試
    python pick_transform.py 自我測試 --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import archive_root, project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════
# 門檻（出處全部可追）
# ═══════════════════════════════════════════════════════════════════
SKEW_OK = 1.0        # M4 三門檻之一，|skew| < 1（SKILL.md → 06 §1.1）
SPEARMAN_MIN = 0.95  # M4 三門檻之一，排序相關 > 0.95（06 §6.1）
ZERO_HEAVY = 0.30    # 零佔比 ≥ 30% → 情境 3〔06 §1.1 標為判斷〕
ZERO_GREY = 0.10     # 10%–30% 灰帶，改看零的性質
CEILING_TIE = 0.15   # 最大值重複佔比 > 15% → 天花板〔06 §1.3 標為判斷〕
Z_EXTREME = 5.0      # 轉換後仍有 |z| > 5 → 06 §3.2 分支 B Step 3
SCALE_GAP = 1e3      # 各欄量級差 ≥ 10³ → 情境 7
BETA_LINEAR_MAX = 0.1  # |β| > 0.1 不准用線性近似（06 §4.3）

# 06 §4.2 的欄名後綴表。表上沒有的（平移 log、平方、立方、arcsine）是本檔
# 自訂，**此處為實作判斷**，一律沿用「原欄名 + 雙底線 + 轉換代號 + 參數」的規則。
SUFFIX_IS_SPEC = {"__log", "__log_c", "__yj", "__bc", "__ihs_t", "__logit", "__w"}

# 06 §4.5：時間型欄位不要當一般數值轉。欄名樣式（17 §7.3 規定帶 _days 後綴）
TIME_COL_PAT = re.compile(
    r"(_days$|_days__|recency|interval|間隔|回購|last_sale|since_last)", re.I
)
TENURE_COL_PAT = re.compile(r"(tenure|帳齡|入會|acquisition_age|_age_days)", re.I)

LOG_FAMILY = {"log", "log_c", "bc", "shift_log"}  # 取 log 之後 exp 回去會有偏誤的

# ═══════════════════════════════════════════════════════════════════
# 三桶
# ═══════════════════════════════════════════════════════════════════
errors: list[str] = []
warnings: list[str] = []
infos: list[str] = []


def ok(msg: str) -> None:
    infos.append(msg)


def warn(msg: str, why: str) -> None:
    warnings.append(f"{msg} — {why}")


def err(msg: str, why: str) -> None:
    errors.append(f"{msg} — {why}")


def detail(bucket: list[str], msg: str) -> None:
    bucket.append(f"    · {msg}")


# ═══════════════════════════════════════════════════════════════════
# 欄位剖析
# ═══════════════════════════════════════════════════════════════════
@dataclass
class Profile:
    """一個數值欄的分布特性 —— 對應 06 §六 六欄格式的第 2 欄 src_profile。"""
    col: str
    n_raw: int
    n: int
    n_nan: int
    vmin: float
    vmax: float
    p1: float
    p25: float
    p50: float
    p75: float
    p99: float
    mean: float
    std: float
    skew: float
    zero_ratio: float
    neg_ratio: float
    tie_top_ratio: float
    min_positive: float | None

    def as_text(self) -> str:
        return (f"n={self.n}, min={self.vmin:,.4g}, max={self.vmax:,.4g}, "
                f"p50={self.p50:,.4g}, skew={self.skew:.4f}, "
                f"zero={self.zero_ratio:.2%}, neg={self.neg_ratio:.2%}")

    def as_dict(self) -> dict[str, Any]:
        return {"n": self.n, "n_nan": self.n_nan, "min": self.vmin,
                "max": self.vmax, "p1": self.p1, "p50": self.p50,
                "p99": self.p99, "mean": self.mean, "std": self.std,
                "skew": self.skew, "zero_ratio": self.zero_ratio,
                "neg_ratio": self.neg_ratio, "tie_top_ratio": self.tie_top_ratio}


def profile_column(x_raw: np.ndarray, col: str) -> Profile:
    """算分布特性。NaN 一律先剔除，零佔比的分母是「非空列數」（06 §1.1）。"""
    x_raw = np.asarray(x_raw, dtype=float)
    n_raw = int(x_raw.size)
    x = x_raw[np.isfinite(x_raw)]
    if x.size == 0:
        raise ValueError(f"欄 {col} 沒有任何有限值 —— 先回 M1 查這一欄是不是全空")
    pos = x[x > 0]
    return Profile(
        col=col, n_raw=n_raw, n=int(x.size), n_nan=n_raw - int(x.size),
        vmin=float(x.min()), vmax=float(x.max()),
        p1=float(np.percentile(x, 1)), p25=float(np.percentile(x, 25)),
        p50=float(np.percentile(x, 50)), p75=float(np.percentile(x, 75)),
        p99=float(np.percentile(x, 99)),
        mean=float(x.mean()), std=float(x.std(ddof=1)) if x.size > 1 else 0.0,
        # 與 06 §一 的參考程式一致，用 scipy 預設（bias=True）的偏度
        skew=float(stats.skew(x)),
        zero_ratio=float((x == 0).mean()),
        neg_ratio=float((x < 0).mean()),
        tie_top_ratio=float((x == x.max()).mean()),
        min_positive=float(pos.min()) if pos.size else None,
    )


# ═══════════════════════════════════════════════════════════════════
# 轉換函式（每個都回 (轉換後的值, 參數, 欄名後綴)）
# ═══════════════════════════════════════════════════════════════════
def t_log(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.log(x), {}, "__log"


def t_log_c(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    """c 取「最小正值的一半」（06 §1.3 明訂的兩個合法選項之一）。
    絕不用 1e-6 —— 那會在金額欄製造 log(1e-6) = −13.8 的假離群值。"""
    c = (pf.min_positive / 2.0) if pf.min_positive else 1.0
    with np.errstate(divide="ignore", invalid="ignore"):
        y = np.log(x + c)
    tag = f"{c:g}".replace(".", "p")
    return y, {"c": c, "c_source": "min_positive/2",
               "c_alternative_p1": pf.p1}, f"__log_c{tag}"


def t_yj(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    y, lam = stats.yeojohnson(x)
    return np.asarray(y), {"lambda": float(lam)}, "__yj"


def t_bc(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    y, lam = stats.boxcox(x)
    return np.asarray(y), {"lambda": float(lam)}, "__bc"


def t_ihs(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    """arcsinh(x/θ)。θ 預設取 train p50，並在外層做 p25/p50/p75 敏感度。"""
    theta = pf.p50 if pf.p50 > 0 else (pf.p75 if pf.p75 > 0 else 1.0)
    tag = f"{theta:g}".replace(".", "p")
    return (np.arcsinh(x / theta),
            {"theta": theta, "theta_source": "train p50"}, f"__ihs_t{tag}")


def t_shift_log(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    """水平平移後 log。平移量從這批資料的 min 學來 —— 新資料出現更小的值就會
    產生負數進 log，所以要存進 transform_spec.json 並定義 clip 規則（06 §1.3）。"""
    c = abs(pf.vmin) * 0.01 if pf.vmin != 0 else 1.0
    shift = -pf.vmin + c
    with np.errstate(divide="ignore", invalid="ignore"):
        y = np.log(x + shift)
    tag = f"{shift:g}".replace(".", "p").replace("-", "m")
    # 後綴不在 06 §4.2 表上 —— 此處為實作判斷
    return y, {"shift": shift, "c": c, "clip_on_apply": [-1e9, 1e9],
               "suffix_is_impl_judgement": True}, f"__shiftlog_s{tag}"


def t_logit(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    """端點用 Smithson–Verkuilen 壓縮 (y(n-1)+0.5)/n（06 §1.3 情境 5）。"""
    n = x.size
    y = (x * (n - 1) + 0.5) / n
    return np.log(y / (1 - y)), {"endpoint_adjust": "smithson_verkuilen",
                                 "n": int(n)}, "__logit"


def t_asin(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    # 後綴不在 06 §4.2 表上 —— 此處為實作判斷
    return (np.arcsin(np.sqrt(np.clip(x, 0, 1))),
            {"suffix_is_impl_judgement": True}, "__asin")


def t_square(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    # 後綴不在 06 §4.2 表上 —— 此處為實作判斷
    return x ** 2, {"suffix_is_impl_judgement": True}, "__sq"


def t_cube(x: np.ndarray, pf: Profile) -> tuple[np.ndarray, dict, str]:
    # 後綴不在 06 §4.2 表上 —— 此處為實作判斷
    return x ** 3, {"suffix_is_impl_judgement": True}, "__cube"


# ═══════════════════════════════════════════════════════════════════
# 候選方法
# ═══════════════════════════════════════════════════════════════════
@dataclass
class Candidate:
    rank: int
    method: str
    label: str
    kind: str               # column | model | binning | downstream
    fn: Callable | None = None
    params: dict = field(default_factory=dict)
    suffix: str = ""
    post_skew: float | None = None
    spearman: float | None = None
    n_bad: int = 0          # 轉換後產生的 NaN / inf 數
    eligible: bool = True
    reject: str = ""        # 為什麼這一順位不行（→ 六欄格式第 4 欄）
    note: str = ""


# 順位表（06 §1.2）。model = 換模型不產生欄位；column = 產生新欄位。
def build_candidates(sit: int, pf: Profile, purpose: str,
                     zero_kind: str) -> list[Candidate]:
    if sit == 1:
        return [
            Candidate(1, "gamma_glm_log", "Gamma GLM + log link", "model",
                      params={"family": "Gamma", "link": "log"},
                      note="Var 隨 Mean 超線性上升 → Gamma；exp(Xb) 直接是 E[Y]，不需修正"),
            Candidate(2, "log", "ln(x)", "column", t_log),
            Candidate(3, "bc", "Box-Cox（λ 從訓練集學）", "column", t_bc),
        ]
    if sit == 2:
        return [
            Candidate(1, "yj", "Yeo-Johnson（自動選 λ、原生支援 0）", "column", t_yj),
            Candidate(2, "ihs", "arcsinh(x/θ)", "column", t_ihs,
                      note="θ 必須報，且要做 p25/p50/p75 敏感度"),
            Candidate(3, "log_c", "log(x+c)，c = 最小正值的一半", "column", t_log_c,
                      note="c 不可用 1e-6 或隨手的 1"),
        ]
    if sit == 3:
        return [
            Candidate(1, "hurdle", "Hurdle 兩段（logit + 截斷 Gamma/lognormal）",
                      "model", note="第一段建模買不買、第二段建模買了買多少；"
                                    "兩段係數可以方向相反，這正是它的價值"),
            Candidate(2, "zinb", "ZINB（計數型）", "model"),
            Candidate(3, "tweedie", "Tweedie（1<p<2，總金額型）", "model",
                      note="只適用隨機零；結構性零那些列不該進第二段"),
        ]
    if sit == 4:
        return [
            Candidate(1, "yj", "Yeo-Johnson", "column", t_yj),
            Candidate(2, "ihs", "arcsinh(x/θ)", "column", t_ihs),
            Candidate(3, "shift_log", "水平平移後 log（平移量必須報告）",
                      "column", t_shift_log),
        ]
    if sit == 5:
        return [
            Candidate(1, "beta_reg", "Beta regression", "model",
                      params={"endpoint": "smithson_verkuilen 或 zero-one-inflated beta"}),
            Candidate(2, "logit", "logit(p)", "column", t_logit),
            Candidate(3, "asin", "arcsin(√p)", "column", t_asin),
        ]
    if sit == 6:
        return [
            Candidate(1, "square", "x²", "column", t_square),
            Candidate(2, "cube", "x³", "column", t_cube),
            Candidate(3, "yj", "Yeo-Johnson（λ>1 自動處理）", "column", t_yj),
        ]
    if sit == 7:
        return [
            Candidate(1, "zscore", "z-score（在各方法族內做，見 06 §五）",
                      "downstream"),
            Candidate(2, "robust_scaler", "RobustScaler（中位數 + IQR）",
                      "downstream", note="已走完 06 §三 仍有離群時用"),
        ]
    return []


SITUATION_NAME = {
    0: "整數分子分母的比例（不屬於七情境）",
    1: "右偏全正值",
    2: "右偏含 0",
    3: "零膨脹",
    4: "含負值",
    5: "比率 [0,1]",
    6: "左偏",
    7: "尺度差異大",
    -1: "|skew| ≤ 1，不轉換",
    -2: "時間型欄位（06 §4.5）",
    -3: "tenure／帳齡（18-G3）",
}

NEVER_DO = {
    1: "取 log 建模後 exp 回去報平均（06 §二）",
    2: "隨手用 log(x+1) 或 log(x+1e-6)",
    3: "用任何 log(x+c) 把零推到一根柱子上",
    4: "把負值當缺失刪掉（那是退貨，見 18-G2）",
    5: "對比率取 log（06 §4.4）",
    6: "忽略天花板效應硬轉",
    7: "用 log 當作「壓量級」的手段就以為解決了",
}


# ═══════════════════════════════════════════════════════════════════
# 情境路由（06 §1.1 決策樹：先看值域 → 再看零佔比 → 最後才看偏度）
# ═══════════════════════════════════════════════════════════════════
def route(pf: Profile, is_ratio: bool = False, has_int_denominator: bool = False,
          zero_kind: str = "unknown", treat_as_time: bool = True) -> tuple[int, str]:
    """回 (情境編號, 判定依據的文字)。順序不可調 —— 搞反會選錯整條路徑。"""
    # 欄名層級的前置攔截（06 §4.5、18-G3）
    if treat_as_time and TENURE_COL_PAT.search(pf.col):
        return -3, f"欄名 `{pf.col}` 命中 tenure／帳齡樣式"
    if treat_as_time and TIME_COL_PAT.search(pf.col):
        return -2, f"欄名 `{pf.col}` 命中時間型樣式（recency／間隔／_days）"

    if has_int_denominator:
        return 0, "宣告了整數分子/分母（點擊/曝光這類）"
    if is_ratio and pf.vmin >= 0 and pf.vmax <= 1:
        return 5, f"宣告為連續型比例且值域 [{pf.vmin:.4g}, {pf.vmax:.4g}] ⊆ [0,1]"
    if pf.vmin < 0:
        return 4, f"min = {pf.vmin:,.4g} < 0（負值佔 {pf.neg_ratio:.2%}）"

    if pf.zero_ratio >= ZERO_HEAVY:
        return 3, f"零佔比 {pf.zero_ratio:.2%} ≥ 30%"
    if pf.zero_ratio >= ZERO_GREY:
        if zero_kind == "structural":
            return 3, f"零佔比 {pf.zero_ratio:.2%} 落在 10–30% 灰帶，且宣告為結構性零"
        if zero_kind == "random":
            return 2, f"零佔比 {pf.zero_ratio:.2%} 落在 10–30% 灰帶，且宣告為隨機零"
        return 3, (f"零佔比 {pf.zero_ratio:.2%} 落在 10–30% 灰帶，"
                   f"零的性質未宣告 → 保守走情境 3")
    if pf.zero_ratio > 0:
        return 2, f"min = 0、零佔比 {pf.zero_ratio:.2%} < 10%"
    if pf.skew > SKEW_OK:
        return 1, f"min = {pf.vmin:,.4g} > 0、skew = {pf.skew:.4f} > 1"
    if pf.skew < -SKEW_OK:
        return 6, f"skew = {pf.skew:.4f} < −1"
    return -1, f"|skew| = {abs(pf.skew):.4f} ≤ 1"


# ═══════════════════════════════════════════════════════════════════
# 候選評估：算轉換後偏度與排序相關，決定哪一順位可用
# ═══════════════════════════════════════════════════════════════════
def ihs_sensitivity(x: np.ndarray, pf: Profile) -> dict[str, Any]:
    """θ 取 p25 / p50 / p75 各跑一次（06 §1.3 情境 2 明訂的敏感度做法）。

    改 θ 不只是改截距，會改係數的大小，所以彈性解讀會跟著變。這裡只能做
    **偏度**的敏感度 —— 係數的正負號與量級要等 M7 配完模型才比得出來，
    那一步腳本代勞不了，只能把它標成待辦〔此處為實作判斷〕。
    """
    out: dict[str, Any] = {"thetas": [], "post_skew": [],
                           "coef_sign_stable": None,
                           "todo": "M7 配完模型後，用同樣三個 θ 把係數並排；"
                                   "正負號或量級改變 → arcsinh 不能用，"
                                   "降級回 Yeo-Johnson 或改走 Hurdle"}
    for theta in (pf.p25, pf.p50, pf.p75):
        if theta <= 0:
            continue
        with np.errstate(all="ignore"):
            sk = float(stats.skew(np.arcsinh(x / theta)))
        out["thetas"].append(float(theta))
        out["post_skew"].append(sk)
    sks = out["post_skew"]
    out["skew_sign_stable"] = bool(sks) and len({s > 0 for s in sks}) == 1
    out["skew_range"] = (max(sks) - min(sks)) if sks else None
    return out


def measure(cands: list[Candidate], x: np.ndarray, pf: Profile) -> None:
    """把**三個順位全部**算一次，填 post_skew / spearman / 參數。

    不是只算選中的那個 —— 06 §六 第 4 欄要寫「前面的為什麼不行」，
    沒有數字就只能寫「有時候不好用」，那條紀錄就沒有價值。
    """
    for c in cands:
        if c.kind != "column" or c.fn is None:
            continue
        try:
            with np.errstate(all="ignore"):
                y, params, suffix = c.fn(x, pf)
        except Exception as e:  # noqa: BLE001
            c.eligible = False
            c.reject = f"轉換計算失敗：{e!r}"
            continue
        y = np.asarray(y, dtype=float)
        c.params, c.suffix = params, suffix
        c.n_bad = int((~np.isfinite(y)).sum())
        if c.n_bad:
            c.eligible = False
            c.reject = (f"轉換產生 {c.n_bad} 個 NaN/inf（log 吃到 0 或負值）"
                        f"—— 06 §6.1：這是 Bug 不是統計問題，回去修情境判定")
            continue
        c.post_skew = float(stats.skew(y))
        if c.method == "ihs":
            c.params["sensitivity"] = ihs_sensitivity(x, pf)
        rho = stats.spearmanr(x, y).statistic
        c.spearman = float(rho) if np.isfinite(rho) else None
        if c.spearman is not None and c.spearman < SPEARMAN_MIN:
            c.eligible = False
            c.reject = (f"排序相關 {c.spearman:.4f} < 0.95，M4 門檻不過"
                        f"（非單調轉換或 clip 範圍設錯，06 §6.1）")
        elif abs(c.post_skew) >= SKEW_OK:
            c.eligible = False
            c.reject = f"轉換後偏度 {c.post_skew:+.4f}，未過 |skew| < 1 門檻"


def evaluate(cands: list[Candidate], x: np.ndarray, pf: Profile,
             purpose: str, zero_kind: str, sit: int) -> Candidate | None:
    """依順位往下挑第一個可用的。被跳過的順位一律寫下 reject 理由。"""
    measure(cands, x, pf)
    for c in cands:
        if c.kind == "model":
            if sit in (1, 5) and c.rank == 1 and purpose != "predict":
                c.eligible = False
                c.reject = (f"① 是建模路線、不產生欄位；本次用途是 "
                            f"{PURPOSE_LABEL[purpose]}，不需要預測值（06 §1.3）")
                continue
            if sit == 3 and c.rank == 2:
                c.eligible = False
                c.reject = "本欄不是計數型（ZINB 針對計數）"
                continue
            if sit == 3 and c.rank == 3 and zero_kind == "structural":
                c.eligible = False
                c.reject = "結構性零的列不該進第二段，Tweedie 不適用（06 §1.3）"
                continue
            return c
        if c.kind == "downstream":
            return c
        if c.kind == "column" and c.eligible and c.post_skew is not None:
            return c
    return None


PURPOSE_LABEL = {
    "predict": "預測（交付物含金額）",
    "describe": "描述／EDA 直方圖",
    "cluster": "分群輸入",
    "rank": "排序／Top-N",
}


# ═══════════════════════════════════════════════════════════════════
# §二 反轉換偏誤防呆
# ═══════════════════════════════════════════════════════════════════
# 06 §2.3 的交付物對照表
DELIVERABLES: dict[str, tuple[bool, str, str]] = {
    # key: (需不需要處理, 中文說明, 走哪條)
    "pred_amount": (True, "預測營收／客單價／CLV 金額", "① GLM + log link"),
    "log_ols_amount": (True, "已配好 log-OLS，要出金額", "② Duan smearing"),
    "bayes_shrunk_amount": (True, "貝氏收縮平均後回報金額",
                            "在 log(M) 尺度收縮，回報時註明幾何平均意義"),
    "median_report": (False, "報「中位數客單價」",
                      "exp 合法，但必須在報告寫明這是中位數不是平均"),
    "cluster_topn": (False, "分群、Top-N 名單、排序", "③ 直接用"),
    "correlation": (False, "相關係數、Spearman", "③ 直接用"),
    "effect_relative": (False, "效果量的相對比較（誰比誰大）", "③ 直接用"),
}

ACTIONS = {"exp": "對 log 模型的預測值直接 exp",
           "glm_log": "GLM + log link",
           "duan": "Duan smearing",
           "none": "不做反轉換"}


def guard_exp_retransform(deliverable: str, action: str,
                          sigma2: float | None = None) -> str:
    """偵測「對 log 模型的預測值直接 exp」。回傳 'error' / 'warn' / 'ok'。

    這是 06 §二 的實作。它最陰險的地方：R² 高、殘差圖漂亮、Q-Q plot 直，
    偏誤照樣在那裡 —— 低估倍數是 exp(σ²/2)，跟模型配得好不好完全無關。
    """
    if deliverable not in DELIVERABLES:
        err(f"不認得的交付物代碼 `{deliverable}`",
            f"可用：{', '.join(DELIVERABLES)}（見 06 §2.3 對照表）")
        return "error"
    need, label, route_to = DELIVERABLES[deliverable]
    act = ACTIONS.get(action, action)

    if need and action == "exp":
        factor = (f"，以 lognormal 近似推估本欄低估倍數 exp(σ²/2) = "
                  f"{np.exp(sigma2 / 2):.3f}（即少算 "
                  f"{1 - np.exp(-sigma2 / 2):.1%}）") if sigma2 else ""
        err(f"⛔ 反轉換偏誤：交付物「{label}」不可以「{act}」{factor}",
            "exp 是凸函數，Jensen 不等式保證你拿到的是幾何平均不是算術平均，"
            "右偏資料必然低估，且偏度越大低估越多")
        detail(errors, "課程資料集（06 §2.2，以 lognormal 近似）：算術平均 1,909.73、"
                       "幾何平均 ≈ 中位數 688 → 7,764 筆總額少算 9,485,544（−64.0%）")
        detail(errors, "年度促銷預算按營收 3% 編列：正確 44.5 萬 vs 錯誤 16.0 萬，差 28.5 萬")
        detail(errors, f"該怎麼辦：走 {route_to}；"
                       f"或已配好 log-OLS 就用 Duan smearing "
                       f"（smear = mean(exp(resid))，見 scripts/retransform.py）")
        detail(errors, "交付前硬檢查：abs(pred.mean() / y.mean() - 1) < 0.05")
        return "error"

    if need and action in ("glm_log", "duan"):
        ok(f"交付物「{label}」用「{act}」—— 正確路線（06 §2.3）")
        if action == "duan":
            warn("Duan smearing 的前提是殘差同質變異",
                 "有異質變異時要按預測值分位分 5 組各算一個 smearing factor，"
                 "否則低估只是從整體搬到某幾段")
            detail(warnings, "交付前硬檢查：abs(pred_mean_duan.mean() / y.mean() - 1) < 0.05")
        if action == "glm_log":
            detail(infos, "GLM 的信賴區間要在 link scale 算好再轉換，不能轉換上下界的中點")
            detail(infos, "GLM 的診斷圖第 1 張要改用 deviance residual vs linear predictor")
        return "ok"

    if not need and action == "exp":
        if deliverable == "median_report":
            warn(f"交付物「{label}」用 exp 合法", f"{route_to}")
            return "warn"
        ok(f"交付物「{label}」不受反轉換偏誤影響（單調轉換不改排序）")
        return "ok"

    ok(f"交付物「{label}」+「{act}」→ {route_to}")
    return "ok"


def duan_smearing_factor(resid: np.ndarray) -> float:
    """Duan smearing factor = mean(exp(殘差))。殘差近似常態時會收斂到 exp(σ²/2)。"""
    return float(np.mean(np.exp(np.asarray(resid, dtype=float))))


# ═══════════════════════════════════════════════════════════════════
# §三 winsorize 順序決策樹
# ═══════════════════════════════════════════════════════════════════
@dataclass
class WinsorizeDecision:
    branch: str                  # A | B | C
    applied: bool | str
    reason: str
    steps: list[str] = field(default_factory=list)
    preview: dict[str, Any] = field(default_factory=dict)
    conditions: list[tuple[bool | None, str]] = field(default_factory=list)
    # 選中的是「換模型」時，這份決策只是參考（沒有轉換欄就沒有 winsorize 這件事）
    advisory: bool = False


def winsorize_preview(x: np.ndarray, ids: np.ndarray | None,
                      lower_q: float = 0.01, upper_q: float = 0.99) -> dict:
    """先算清楚「會影響幾列、佔營收多少 %、哪些 ID」（06 §3.2 分支 C 條件 3）。"""
    lo, hi = float(np.quantile(x, lower_q)), float(np.quantile(x, upper_q))
    mask = (x < lo) | (x > hi)
    total = float(np.abs(x).sum())
    clipped = np.where(x < lo, lo, np.where(x > hi, hi, x))
    lost = float(np.abs(x - clipped).sum())
    out = {
        "lower_q": lower_q, "upper_q": upper_q,
        "lower_value": lo, "upper_value": hi,
        "n_rows_clipped": int(mask.sum()),
        "pct_of_rows": float(mask.mean()),
        "pct_of_total_amount": (lost / total) if total else None,
    }
    if ids is not None:
        aff = np.asarray(ids)[mask]
        uniq = [str(v) for v in dict.fromkeys(aff.tolist())]
        out["affected_ids"] = uniq[:20]
        out["n_affected_ids"] = len(uniq)
    return out


def decide_winsorize(x_raw: np.ndarray, y_trans: np.ndarray | None,
                     tried: list[str], is_data_error: bool = False,
                     ids: np.ndarray | None = None,
                     step1_label: str = "") -> WinsorizeDecision:
    """06 §3.2 的完整決策樹。鐵則：先轉換 → 再看還有沒有離群 → 才 winsorize。"""
    if is_data_error:
        return WinsorizeDecision(
            branch="A", applied=False,
            reason="宣告為明確的資料錯誤（可回溯來源／量級錯 10^n／邏輯矛盾／"
                   "哨兵值／測試交易）",
            steps=["回 M1 處理，寫清理日誌 + SQL 檔",
                   "不進 M3 轉換流程",
                   "樣本數變化依 18-E22 在報告交代"])

    if y_trans is None:
        return WinsorizeDecision(
            branch="B", applied=False,
            reason="這個情境的三個順位都是「換模型」，不產生轉換欄",
            steps=["Step 1 的轉換不存在 → winsorize 決策不適用",
                   "模型端的極端值處理走 08_迴歸建模.md 的影響點診斷"
                   "（Cook's D），不是在 M3 winsorize"])

    y = np.asarray(y_trans, dtype=float)
    y = y[np.isfinite(y)]
    sk = float(stats.skew(y))
    sd = y.std(ddof=1) if y.size > 1 else 0.0
    z = (y - y.mean()) / sd if sd > 0 else np.zeros_like(y)
    n_ext = int((np.abs(z) > Z_EXTREME).sum())
    prev = winsorize_preview(np.asarray(x_raw, dtype=float), ids)

    lbl = f"（用 {step1_label}）" if step1_label else ""
    step1 = f"Step 1 先做轉換{lbl}（依 06 §一 順位，鐵則：轉換在前）"
    step2 = (f"Step 2 轉換後重算：skew = {sk:+.4f}、|z| > {Z_EXTREME:g} 有 "
             f"{n_ext} 筆")

    if abs(sk) < SKEW_OK and n_ext == 0:
        return WinsorizeDecision(
            branch="B", applied=False,
            reason=f"轉換後 |skew| = {abs(sk):.4f} < 1 且無 |z| > {Z_EXTREME:g}",
            steps=[step1, step2,
                   "Step 2 判定：收工，不 winsorize",
                   f"（若順序反過來先 winsorize p1/p99：會壓掉 "
                   f"{prev['n_rows_clipped']} 列、佔量值 "
                   f"{(prev['pct_of_total_amount'] or 0):.2%}，全是真實長尾）"],
            preview=prev)

    if abs(sk) < SKEW_OK and n_ext > 0:
        return WinsorizeDecision(
            branch="B", applied=False,
            reason=f"偏度已過關（{sk:+.4f}）但仍有 {n_ext} 筆 |z| > {Z_EXTREME:g}",
            steps=[step1, step2,
                   "Step 3 敏感度分析：含/不含並排係數表（**不是可選項**）",
                   "Step 4 結論不變 → 保留全部；結論翻盤 → 正文註明",
                   "實證：刪 3 位大戶後 CAI 係數 1,240(p=.03) → 380(p=.41)，顯著性翻盤"],
            preview=prev)

    conds: list[tuple[bool | None, str]] = [
        (len(tried) >= 2, f"1. 已試過至少兩種轉換並記錄 —— 目前記錄到 "
                          f"{len(tried)} 種：{', '.join(tried) or '（無）'}"),
        (True, f"2. 分位點寫死 p{prev['lower_q']*100:g}/p{prev['upper_q']*100:g} "
               f"= {prev['lower_value']:,.4g} / {prev['upper_value']:,.4g}，"
               f"理由要寫進報告"),
        (None, f"3. 報告明列：影響 {prev['n_rows_clipped']} 列（"
               f"{prev['pct_of_rows']:.2%}）、佔量值 "
               f"{(prev['pct_of_total_amount'] or 0):.2%}、"
               f"顧客 ID {prev.get('affected_ids', '（未提供 --id-col）')}"),
        (None, "4. 附 winsorize 前後結論對照 —— 人工，腳本無法代勞"),
    ]
    return WinsorizeDecision(
        branch="C", applied="待人工確認（例外，不是預設）",
        reason=f"轉換完全無效：轉換後 skew = {sk:+.4f}"
               + (f"、仍有 {n_ext} 筆 |z| > {Z_EXTREME:g}" if n_ext else ""),
        steps=[step1, step2,
               "Step 1–2 走完仍未過關 → 落到分支 C（例外，允許先 winsorize）",
               "★ 這是例外，不是預設。報告不寫 = 這條分支不成立"],
        preview=prev, conditions=conds)


# ═══════════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════════
@dataclass
class Suggestion:
    col: str
    profile: Profile
    situation: int
    situation_why: str
    candidates: list[Candidate]
    chosen: Candidate | None
    rationale: str
    winsorize: WinsorizeDecision | None
    never_do: str

    def to_json(self) -> dict[str, Any]:
        return {
            "col_name": self.col + (self.chosen.suffix if self.chosen else ""),
            "src_col": self.col,
            "src_profile": self.profile.as_dict(),
            "src_profile_text": self.profile.as_text(),
            "situation": self.situation,
            "situation_name": SITUATION_NAME.get(self.situation, "?"),
            "situation_why": self.situation_why,
            "method": self.chosen.method if self.chosen else None,
            "rank": self.chosen.rank if self.chosen else None,
            "kind": self.chosen.kind if self.chosen else None,
            "params": self.chosen.params if self.chosen else {},
            "rationale": self.rationale,
            "post_skew": self.chosen.post_skew if self.chosen else None,
            "spearman_vs_src": self.chosen.spearman if self.chosen else None,
            "never_do": self.never_do,
            "candidates": [
                {"rank": c.rank, "method": c.method, "label": c.label,
                 "kind": c.kind, "eligible": c.eligible, "reject": c.reject,
                 "post_skew": c.post_skew, "spearman": c.spearman,
                 "params": c.params, "suffix": c.suffix}
                for c in self.candidates
            ],
            "winsorize": None if self.winsorize is None else {
                "branch": self.winsorize.branch,
                "applied": self.winsorize.applied,
                "reason": self.winsorize.reason,
                "steps": self.winsorize.steps,
                "preview": self.winsorize.preview,
            },
        }


def analyse(x_raw: np.ndarray, col: str, purpose: str = "predict",
            is_ratio: bool = False, has_int_denominator: bool = False,
            zero_kind: str = "unknown", treat_as_time: bool = True,
            is_data_error: bool = False, ids: np.ndarray | None = None,
            peer: dict[str, np.ndarray] | None = None,
            want: str | None = None, fit_on: str = "train") -> Suggestion:
    pf = profile_column(x_raw, col)
    x = np.asarray(x_raw, dtype=float)
    x = x[np.isfinite(x)]
    if ids is not None:
        ids = np.asarray(ids)[np.isfinite(np.asarray(x_raw, dtype=float))]

    if pf.n_nan:
        warn(f"`{col}` 有 {pf.n_nan} 個空值（{pf.n_nan / pf.n_raw:.2%}）已排除",
             "M3 不補值。缺失機制與補值策略是 M1 的事，見 04_資料體檢.md")

    sit, why = route(pf, is_ratio, has_int_denominator, zero_kind, treat_as_time)
    ok(f"`{col}` → 情境 {sit if sit > 0 else '—'}"
       f"（{SITUATION_NAME.get(sit, '?')}）：{why}")

    # ── 不進順位表的三種前置攔截 ──────────────────────────
    if sit == 0:
        err(f"⛔ `{col}` 是整數分子/分母的比例，不屬於七情境任何一個",
            "直接用 binomial GLM 的分組形式 cbind(成功, 失敗)")
        detail(errors, "先除成比率再轉換：1,000 次曝光的 5% 和 20 次曝光的 5% "
                       "會變成同一筆資料，權重全部丟掉（06 §1.3 情境 5）")
        return Suggestion(col, pf, sit, why, [], None,
                          "不套用順位表：改 binomial GLM（cbind）", None,
                          "先算成比率")

    if sit == -3:
        err(f"⛔ `{col}` 看起來是 tenure／帳齡", "不要轉換（06 §4.5、18-G3）")
        detail(errors, "cohort 比較要的是絕對時間；轉換完就沒辦法比了")
        detail(errors, "若欄名誤判，加 --not-time 關閉欄名層級攔截")
        return Suggestion(col, pf, sit, why, [], None,
                          "tenure/帳齡不轉換（18-G3）", None, "拿去做 log")

    if sit == -2:
        cut = [float(np.quantile(x, q)) for q in (0.2, 0.4, 0.6, 0.8)]
        c = Candidate(1, "ntile5", "NTILE(5) 分位分箱", "binning",
                      params={"cutpoints": cut, "fit_on": fit_on})
        err(f"⛔ `{col}` 是時間型欄位，不要做 log", "改分位數分箱（06 §4.5）")
        detail(errors, "log 讓「30 天 vs 60 天」和「300 天 vs 600 天」變成同樣差距"
                       "（都是 ln2 = 0.693），但前者是該發喚回券、後者是兩個都死了")
        detail(errors, f"等寬分箱會把 90% 的客戶塞進第一箱（std={pf.std:,.1f} > "
                       f"mean={pf.mean:,.1f}）；五分位切點："
                       f"{' / '.join(f'{v:,.4g}' for v in cut)}")
        detail(errors, "要連續尺度就走存活分析的 P(alive)，見 09_行銷_顧客價值.md")
        detail(errors, "若欄名誤判，加 --not-time 關閉欄名層級攔截")
        return Suggestion(col, pf, sit, why, [c], c,
                          "時間型欄位（06 §4.5）：不做 log，改 NTILE(5) 分位分箱。"
                          "log 會壓平「近期 vs 很久以前」的實質差異", None,
                          "對 Recency 取 log")

    if sit == -1:
        ok(f"`{col}` 偏度 {pf.skew:+.4f}，|skew| ≤ 1 → 不轉換（06 §1.1 門檻）")
        return Suggestion(col, pf, sit, why, [], None,
                          f"不轉換。|skew| = {abs(pf.skew):.4f} ≤ 1，已達 M4 門檻，"
                          f"轉換只會增加解讀成本", None, "沒事找事轉換")

    # ── 情境 6 的天花板前檢（06 §1.3）──────────────────────
    if sit == 6 and pf.tie_top_ratio > CEILING_TIE:
        err(f"⛔ `{col}` 最大值 {pf.vmax:,.4g} 重複佔比 {pf.tie_top_ratio:.2%} "
            f"> 15%，是天花板效應",
            "轉換無效 —— 平方、立方只會把中段拉開，不會把天花板那根柱子拆掉")
        detail(errors, "改 ordinal logistic 或 censored（Tobit）模型")
        detail(errors, "行銷資料的左偏幾乎都來自上界：滿意度多數打 9/10、"
                       "高滲透品類購買率、折扣後價格佔原價比例")
        return Suggestion(col, pf, sit, why, [], None,
                          f"情境 6 但命中天花板（重複佔比 {pf.tie_top_ratio:.2%} > 15%）："
                          f"三個順位全部無效，改 ordinal/Tobit", None, NEVER_DO[6])

    # ── 情境 5 的端點質量（Beta regression 要求開區間 (0,1)）──
    if sit == 5:
        at0 = float((x == 0).mean())
        at1 = float((x == 1).mean())
        if at0 + at1 > CEILING_TIE:
            warn(f"`{col}` 有 {at0 + at1:.2%} 的觀測堆在端點"
                 f"（0 佔 {at0:.2%}、1 佔 {at1:.2%}）",
                 "Beta regression 要求開區間 (0,1)，這個比例的點質量不能只靠"
                 "端點壓縮 → 改 zero-one-inflated beta")
            detail(warnings, "這同時是天花板/地板效應：logit 與 arcsin(√p) 只會把"
                             "中段拉開，拆不掉端點那根柱子（06 §1.3 情境 6 同理）")
        elif at0 + at1 > 0:
            warn(f"`{col}` 有 {at0 + at1:.2%} 的觀測落在端點 0 或 1",
                 "Beta regression 要求開區間，端點用 (y(n−1)+0.5)/n 壓縮，"
                 "並在轉換紀錄寫明")

    # ── 走順位表 ──────────────────────────────────────────
    cands = build_candidates(sit, pf, purpose, zero_kind)
    chosen = evaluate(cands, x, pf, purpose, zero_kind, sit)

    if sit == 3:
        err(f"⛔ `{col}` 零膨脹（零佔比 {pf.zero_ratio:.2%}），不要轉換",
            "轉換不能改變機率品質點，只有模型可以（06 §1.3 情境 3）")
        detail(errors, f"該怎麼辦：{chosen.label if chosen else 'Hurdle 兩段模型'}"
                       f"；見 08_迴歸建模.md")
        detail(errors, f"用 log(x+c)：{pf.zero_ratio:.0%} 的列會堆到 log(c) 一根柱子上，"
                       f"迴歸係數量的是「有沒有被觸及」而不是「觸及後買多少」")
        if zero_kind == "unknown" and pf.zero_ratio < ZERO_HEAVY:
            warn("零的性質未宣告", "10–30% 灰帶已保守走情境 3；"
                 "確認是隨機零就加 --zero-kind random 改走情境 2")

    # ── 各順位的說明文字 ──────────────────────────────────
    rejected = [c for c in cands if c.rank < (chosen.rank if chosen else 99)
                and c.reject]
    if chosen is None:
        rationale = (f"情境 {sit}（{SITUATION_NAME[sit]}）三個順位全部不可用："
                     + "；".join(f"{'①②③'[c.rank - 1]} {c.label} — {c.reject}"
                                 for c in cands if c.reject))
        err(f"⛔ `{col}` 三個順位全部不可用", "落到 06 §3.2 分支 C 判定")
    else:
        head = f"情境 {sit} 第 {'①②③'[chosen.rank - 1]} 順位。"
        prevtxt = ("".join(f"{'①②③'[c.rank - 1]} {c.label} 不行："
                           f"{c.reject}。" for c in rejected))
        rationale = head + prevtxt + (chosen.note or "")
        if chosen.kind == "column":
            rationale += (f" 轉換後偏度 {chosen.post_skew:+.4f}"
                          f"（門檻 |skew| < 1）、Spearman(原,轉) = "
                          f"{chosen.spearman:.4f}（門檻 > 0.95）。")
        rationale += f" 參數 fit_on = {fit_on}（06 §4.1，重跑不重新 fit）。"

    # ── §三 winsorize 決策 ────────────────────────────────
    # 鐵則是「先轉換 → 再看還有沒有離群 → 才 winsorize」，所以 Step 1 一定要有一個
    # 轉換結果。選中的是換模型（不產生欄位）時，改拿順位最前面、算得出來的
    # column 轉換來評估「轉換完之後還構不構成離群」〔此處為實作判斷〕。
    tried: list[str] = [
        c.method + (f"(λ={c.params['lambda']:.4f})" if "lambda" in c.params else "")
        for c in cands
        if c.kind == "column" and c.fn is not None and c.post_skew is not None
    ]
    step1_c: Candidate | None = None
    if chosen is not None and chosen.kind == "column":
        step1_c = chosen
    else:
        step1_c = next((c for c in cands
                        if c.kind == "column" and c.eligible
                        and c.post_skew is not None), None)
        if step1_c is None:  # 三個順位都不過關 → 拿 ① 的結果去判分支 C
            step1_c = next((c for c in cands if c.kind == "column"
                            and c.post_skew is not None), None)
    y_trans = None
    if step1_c is not None and step1_c.fn is not None:
        with np.errstate(all="ignore"):
            y_trans = np.asarray(step1_c.fn(x, pf)[0], dtype=float)
    lbl = "" if (step1_c is None or step1_c is chosen) else \
        f"第 {'①②③'[step1_c.rank - 1]} 順位的 {step1_c.label}"
    wd = decide_winsorize(x, y_trans, tried, is_data_error, ids, lbl)
    wd.advisory = chosen is not None and chosen.kind != "column"
    if wd.advisory and y_trans is not None:
        wd.steps.append("（選中的是換模型路線，不產生轉換欄 → 這份 winsorize "
                        "判定只是參考；模型端的極端值走影響點診斷）")

    if wd.branch == "A":
        err(f"⛔ `{col}` 宣告為資料錯誤", "回 M1 處理，不進 M3 轉換流程")
    elif wd.branch == "C" and not wd.advisory:
        warn(f"`{col}` 落到分支 C（例外允許先 winsorize）",
             "四項條件全滿足才准，且報告不寫這條分支就不成立")
        for satisfied, text in wd.conditions:
            mark = "✅" if satisfied else ("⚠" if satisfied is None else "⛔")
            detail(warnings, f"{mark} {text}")
    elif wd.branch == "C" and wd.advisory:
        ok(f"`{col}` 若改走轉換路線會落到分支 C（{wd.reason}）—— "
           f"這也是為什麼第一順位是換模型")
    elif (wd.branch == "B" and not wd.advisory and wd.applied is False
          and any("Step 3" in s for s in wd.steps)):
        warn(f"`{col}` 轉換後仍有極端點", "Step 3 敏感度分析不是可選項")

    # ── arcsinh 的 θ 敏感度（06 §1.3 情境 2）────────────────
    if chosen is not None and chosen.method == "ihs":
        sen = chosen.params.get("sensitivity", {})
        ts = "、".join(f"θ={t:,.4g} → skew {s:+.4f}"
                       for t, s in zip(sen.get("thetas", []),
                                       sen.get("post_skew", [])))
        if not sen.get("skew_sign_stable", True) or \
                (sen.get("skew_range") or 0) > SKEW_OK:
            warn(f"`{col}` 的 arcsinh θ 敏感度不穩：{ts}",
                 "θ 換一個值結論就變 → 降級回 Yeo-Johnson，"
                 "或承認這是情境 3 改走 Hurdle")
        else:
            warn(f"`{col}` 用了 arcsinh，θ = {chosen.params['theta']:,.4g}"
                 f"（{chosen.params['theta_source']}）必須寫進報告",
                 f"偏度敏感度：{ts}；係數敏感度要在 M7 配完模型後把三個 θ 的"
                 f"係數並排，正負號或量級改變就不能用 arcsinh")

    # ── §二 反轉換偏誤：用了 log 家族又要拿去預測就擋 ────────
    log_pick = None
    if chosen is not None and chosen.method in LOG_FAMILY:
        log_pick = f"順位表選中的 {chosen.method}"
    if want in LOG_FAMILY:
        log_pick = f"你宣告的 --want {want}"
    if log_pick and purpose == "predict":
        guard_exp_retransform("pred_amount", "exp", _lognormal_sigma2(pf))
        detail(errors, f"觸發來源：`{col}` 用了{log_pick}，且 --purpose predict"
                       f"（= 要出金額預測值）")

    # ── --want 驗證 ───────────────────────────────────────
    if want:
        _check_want(want, col, sit, chosen, pf, purpose)

    # ── 情境 7 尺度檢查（要有 peer 欄才判得出來）──────────
    if peer:
        _check_scale(col, x, peer)

    if fit_on == "full" and purpose == "predict":
        err(f"⛔ `{col}` 的 fit_on = full 但用途是預測",
            "轉換參數（λ／θ／分位點／mean-sd）全部會洩漏，這是 18-G4 的入口")
        detail(errors, "監督式路線把轉換放進 sklearn.Pipeline，讓 CV 在每個 fold 內 fit")

    return Suggestion(col, pf, sit, why, cands, chosen, rationale, wd,
                      NEVER_DO.get(sit, ""))


def _lognormal_sigma2(pf: Profile) -> float | None:
    """以 lognormal 近似回推 σ²：幾何平均 ≈ 中位數，σ² = 2·ln(mean / p50)。
    這是 06 §2.2 用的推法（1,909.73 / 688 = 2.776 → σ² = 2.042）。"""
    if pf.p50 > 0 and pf.mean > pf.p50:
        return float(2 * np.log(pf.mean / pf.p50))
    return None


def _check_want(want: str, col: str, sit: int, chosen: Candidate | None,
                pf: Profile, purpose: str) -> None:
    """驗證使用者宣告要用的方法。這是「擋住」的另一個入口。"""
    if sit == 5 and want in LOG_FAMILY:
        err(f"⛔ `{col}` 是比率欄，不准取 log", "改 logit（06 §4.4）")
        detail(errors, "log 假設沒有上界，比率有。CTR 3%→6% 與 45%→90% 在 log 尺度"
                       "都是 +0.693，logit 才反映「越接近天花板越難再提升」（+0.712 vs +2.001）")
        detail(errors, "比率欄的離群判定也不要用 log 尺度的 z 分數")
        return
    if want == "winsorize":
        err(f"⛔ `{col}` 宣告要先 winsorize", "06 §三 鐵則：先轉換 → 再看還有沒有離群 → 才 winsorize")
        detail(errors, "先 winsorize 等於在壓縮之前砍掉真實長尾，而行銷資料的長尾就是大客戶")
        return
    if sit == -2 and want in LOG_FAMILY:
        err(f"⛔ `{col}` 是時間型欄位，宣告要用 {want}", "改分位數分箱（06 §4.5）")
        return
    if chosen is None:
        return
    if want != chosen.method:
        warn(f"`{col}` 你宣告要用 {want}，但順位表建議 {chosen.method}",
             f"要用 {want} 就必須在 transform_log.csv 的 rationale 欄寫出"
             f"「為什麼跳過 {chosen.method}」（06 §六 第 4 欄）")
    else:
        ok(f"`{col}` 宣告的 {want} 與順位表建議一致")


def _check_scale(col: str, x: np.ndarray, peer: dict[str, np.ndarray]) -> None:
    """情境 7：各欄量級差 ≥ 10³ 就是尺度問題，不是分布問題。"""
    mags: dict[str, float] = {}
    for name, v in {col: x, **peer}.items():
        v = np.asarray(v, dtype=float)
        v = np.abs(v[np.isfinite(v)])
        v = v[v > 0]
        mags[name] = float(np.median(v)) if v.size else float("nan")
    vals = [v for v in mags.values() if np.isfinite(v) and v > 0]
    if len(vals) < 2:
        return
    gap = max(vals) / min(vals)
    txt = "、".join(f"{k} 中位量級 {v:,.4g}" for k, v in mags.items())
    if gap >= SCALE_GAP:
        warn(f"情境 7 尺度差異大：量級差 {gap:,.0f} 倍 ≥ 10³（{txt}）",
             "這是尺度問題不是分布問題，不要用 log 去「解決」它")
        detail(warnings, "① z-score（在各方法族內做，見 06 §五）；"
                         "② 有離群 → RobustScaler（中位數 + IQR）")
        detail(warnings, "M3 不產出「標準化後的矩陣」—— 那是四份不同的矩陣，不是一份")
        detail(warnings, "實測：取 log 之後 M 與 F 的量級仍差 2.03 倍，"
                         "而且支配權會轉到 R（log 後三維變異數佔比 R45%/F24%/M31%）")
    else:
        ok(f"各欄量級差 {gap:,.1f} 倍 < 10³，不觸發情境 7（{txt}）")


# ═══════════════════════════════════════════════════════════════════
# 輸出
# ═══════════════════════════════════════════════════════════════════
def print_suggestion(s: Suggestion) -> None:
    print("─" * 70)
    print(f"欄位：{s.col}")
    print(f"原分布：{s.profile.as_text()}")
    print(f"情境 {s.situation if s.situation > 0 else '—'}"
          f"（{SITUATION_NAME.get(s.situation, '?')}）：{s.situation_why}")
    if s.never_do:
        print(f"絕對不要：{s.never_do}")
    print()
    if s.candidates:
        print(f"  {'順位':<4}{'方法':<34}{'類型':<10}{'轉換後偏度':>10}  {'Spearman':>8}")
        for c in s.candidates:
            mark = "◀ 選這個" if (s.chosen and c is s.chosen) else ""
            ps = f"{c.post_skew:+.4f}" if c.post_skew is not None else "—"
            sp = f"{c.spearman:.4f}" if c.spearman is not None else "—"
            print(f"  {'①②③'[c.rank - 1]:<5}{c.label:<34}{c.kind:<10}"
                  f"{ps:>10}  {sp:>8}  {mark}")
            if c.reject:
                print(f"       ↳ 不行：{c.reject}")
        print()
    if s.chosen:
        newcol = s.col + s.chosen.suffix
        print(f"選了：{s.chosen.label}"
              + (f"  → 新欄名 `{newcol}`" if s.chosen.suffix else "  （不產生新欄位）"))
        if s.chosen.params:
            print(f"參數：{json.dumps(s.chosen.params, ensure_ascii=False, default=str)}")
    else:
        print("選了：（無可用順位）")
    print(f"為什麼是它：{s.rationale}")
    if s.winsorize:
        w = s.winsorize
        print()
        print(f"winsorize 決策（06 §三）：分支 {w.branch}｜"
              f"applied = {w.applied}｜{w.reason}")
        for st in w.steps:
            print(f"    · {st}")
    print("─" * 70)


def flush_buckets(verbose: bool = False) -> int:
    if verbose and infos:
        print("\n通過")
        print("-" * 70)
        for m in infos:
            print(f"  ✅ {m}" if not m.startswith("  ") else m)
    if warnings:
        print("\n⚠ 可以做，但這些要補動作")
        print("-" * 70)
        for m in warnings:
            print(f"  {m}" if m.startswith("    ") else f"  ⚠ {m}")
    if errors:
        print("\n⛔ 擋住，必須先處理")
        print("-" * 70)
        for m in errors:
            print(f"  {m}" if m.startswith("    ") else f"  {m}")
    # 縮排的是上一條的明細行，不另計為一項（沿用 setup_check.py）
    n_err = sum(1 for m in errors if not m.startswith("    "))
    n_warn = sum(1 for m in warnings if not m.startswith("    "))
    print("\n" + "=" * 70)
    if errors:
        print(f"結果：{n_err} 個 error、{n_warn} 個 warning → 擋住，不要照建議動手")
        return 1
    if warnings:
        print(f"結果：{n_warn} 個 warning → 可以做，但上面那幾件要補")
        return 2
    print(f"結果：全部通過（{len(infos)} 項）→ 照建議做，理由寫進 transform_log.csv")
    return 0


# ═══════════════════════════════════════════════════════════════════
# 讀資料
# ═══════════════════════════════════════════════════════════════════
def load_frame(project: str, parquet: str | None, table: str | None):
    import pandas as pd
    if parquet:
        p = Path(parquet)
        if not p.exists():
            pp = project_dir(project, create=False)
            for base in (pp.raw, pp.staging, pp.mart, pp.features, pp.root):
                cand = base / parquet
                if cand.exists():
                    p = cand
                    break
        if not p.exists():
            raise FileNotFoundError(
                f"找不到 {parquet}\n"
                f"  試過：目前目錄、專案的 原始資料/清理後資料/分析資料表/顧客特徵表。\n"
                f"  給絕對路徑，或確認專案代號打對了。")
        if p.suffix.lower() in (".csv", ".txt"):
            return pd.read_csv(p)
        return pd.read_parquet(p)
    if table:
        from db import connect  # 唯一合法的連線介面（03 §7.1）
        with connect(project, read_only=True) as con:
            return con.execute(f"SELECT * FROM {table}").df()
    raise ValueError("要嘛給 --parquet，要嘛給 --table")


# ═══════════════════════════════════════════════════════════════════
# 自我測試（用課程資料集樣本，全部是真實數字）
# ═══════════════════════════════════════════════════════════════════
def self_test() -> int:
    import pandas as pd
    ar = archive_root()
    if ar is None:
        err("找不到素材庫 00_source_archive", "自我測試需要 samples/ 下的樣本檔")
        return flush_buckets(verbose=True)
    sd = ar / "local" / "資料集剖析" / "samples"
    txn = pd.read_parquet(sd / "ntu_creditcard__transactions.parquet")
    cai = pd.read_parquet(sd / "ntu_creditcard__step5_cai.parquet")
    smk = pd.read_parquet(sd / "ntu_supermarket__transactions.parquet")

    print("=" * 70)
    print("pick_transform.py 自我測試 —— 課程資料集樣本")
    print(f"樣本目錄：{sd}")
    print(f"交易 {len(txn):,} 筆／CAI {len(cai)} 位／超市 {len(smk):,} 筆")
    print("=" * 70)

    amt = txn["刷卡金額"].to_numpy(float)
    cust = txn["客戶ID"].to_numpy()

    cases: list[tuple[str, dict]] = []

    # ① 情境 1：右偏全正的金額，用途是預測 → Gamma GLM
    cases.append(("① 情境 1 右偏全正（要預測）",
                  dict(x_raw=amt, col="刷卡金額", purpose="predict", ids=cust)))
    # ② 同一欄，用途只是分群輸入 → 降到 ② log
    cases.append(("② 情境 1 右偏全正（只做分群輸入）",
                  dict(x_raw=amt, col="刷卡金額", purpose="cluster", ids=cust)))
    # ③ 同一欄，宣告要用 log 又要拿去預測 → 反轉換偏誤擋下
    cases.append(("③ 情境 1 + 宣告 --want log --purpose predict（應被擋）",
                  dict(x_raw=amt, col="刷卡金額", purpose="predict",
                       want="log", ids=cust)))
    # ④ 情境 4：CAI 可正可負
    cases.append(("④ 情境 4 含負值（CAI）",
                  dict(x_raw=cai["CAI"].to_numpy(float), col="cai_score",
                       purpose="cluster")))
    # ⑤ 情境 4：超市數量，值域含退貨
    cases.append(("⑤ 情境 4 含負值（超市數量，負值是退貨）",
                  dict(x_raw=smk["數量"].to_numpy(float), col="qty_units",
                       purpose="cluster")))

    # ⑥ 情境 3：顧客 × 品類金額（零膨脹，結構性零）
    piv = smk.pivot_table(index="會員卡號", columns="中類代碼",
                          values="總金額", aggfunc="sum").fillna(0.0)
    zr = {c: float((piv[c] == 0).mean()) for c in piv.columns}
    heavy = sorted((r, c) for c, r in zr.items() if r >= ZERO_HEAVY)
    zcol = heavy[0][1]
    cases.append((f"⑥ 情境 3 零膨脹（顧客×中類 {zcol} 金額，零佔比 "
                  f"{zr[zcol]:.1%}，宣告結構性零）",
                  dict(x_raw=piv[zcol].to_numpy(float),
                       col=f"cat_amt_{zcol}", purpose="predict",
                       zero_kind="structural",
                       ids=piv.index.to_numpy())))

    # ⑦ 情境 2：右偏含 0 —— 剔除退貨列後的單品金額（零來自空瓶回收，金額歸零）
    net = smk.loc[smk["數量"] >= 0, "金額"].to_numpy(float)
    cases.append((f"⑦ 情境 2 右偏含 0（非退貨列的單品金額，零佔比 "
                  f"{(net == 0).mean():.2%}）",
                  dict(x_raw=net, col="line_amt_net", purpose="cluster")))

    # ⑧ 10–30% 灰帶：同一欄跑兩次，零的性質未宣告 vs 宣告隨機零
    grey = sorted((r, c) for c, r in zr.items() if ZERO_GREY <= r < ZERO_HEAVY)
    if grey:
        gr, gcol = grey[0]
        cases.append((f"⑧a 10–30% 灰帶（顧客×中類 {gcol}，零佔比 {gr:.1%}，"
                      f"未宣告零的性質）",
                      dict(x_raw=piv[gcol].to_numpy(float),
                           col=f"cat_amt_{gcol}", purpose="cluster",
                           ids=piv.index.to_numpy())))
        cases.append((f"⑧b 同一欄宣告 --zero-kind random → 改走情境 2",
                      dict(x_raw=piv[gcol].to_numpy(float),
                           col=f"cat_amt_{gcol}", purpose="cluster",
                           zero_kind="random", ids=piv.index.to_numpy())))

    # ⑨ 情境 5：滲透率 100% 的中類佔顧客總消費的比重（連續比例，開區間內）
    full = [c for c, r in zr.items() if r == 0]
    scol = full[0]
    share = (piv[scol] / piv.sum(axis=1)).to_numpy(float)
    cases.append((f"⑨a 情境 5 比率 [0,1]（中類 {scol} 佔顧客總消費比重，"
                  f"宣告 --ratio、要預測）",
                  dict(x_raw=share, col=f"share_{scol}_ratio",
                       purpose="predict", is_ratio=True,
                       ids=piv.index.to_numpy())))
    cases.append((f"⑨b 情境 5 同一欄，用途是分群 → ① 不適用、②③ 也不過關，"
                  f"落到分支 C",
                  dict(x_raw=share, col=f"share_{scol}_ratio",
                       purpose="cluster", is_ratio=True,
                       ids=piv.index.to_numpy())))
    cases.append((f"⑨c 情境 5 同一欄，宣告 --want log（應被擋，06 §4.4）",
                  dict(x_raw=share, col=f"share_{scol}_ratio",
                       purpose="cluster", is_ratio=True, want="log",
                       ids=piv.index.to_numpy())))
    cases.append((f"⑨d 情境 0 整數分子分母（點擊/曝光型，應被擋）",
                  dict(x_raw=share, col=f"share_{scol}_ratio",
                       purpose="predict", is_ratio=True,
                       has_int_denominator=True)))

    # ⑨e/f 天花板：客戶的國內交易佔比，78 位客戶 100% 國內
    dom = (txn.assign(_d=(txn["刷卡地點"] == "國內").astype(float))
              .groupby("客戶ID")["_d"].mean())
    cases.append(("⑨e 情境 6 左偏 + 天花板（客戶國內交易佔比，應被擋）",
                  dict(x_raw=dom.to_numpy(float), col="domestic_share",
                       purpose="cluster")))
    cases.append(("⑨f 同一欄宣告 --ratio → 情境 5，但端點質量要改 "
                  "zero-one-inflated beta",
                  dict(x_raw=dom.to_numpy(float), col="domestic_share_ratio",
                       purpose="predict", is_ratio=True,
                       ids=dom.index.to_numpy())))

    # ⑩ 情境 7：RFM 三欄量級差
    asof = np.datetime64("2012-12-01")
    g = txn.groupby("客戶ID").agg(last=("刷卡日期", "max"),
                                  F=("交易序號", "count"),
                                  M=("刷卡金額", "sum"))
    R = (asof - g["last"].to_numpy("datetime64[D]")).astype("timedelta64[D]").astype(float)
    cases.append(("⑩ 情境 7 尺度差異（M 對上 R/F）",
                  dict(x_raw=g["M"].to_numpy(float), col="m_net_twd",
                       purpose="cluster",
                       peer={"r_days": R, "f_txn_cnt": g["F"].to_numpy(float)},
                       ids=g.index.to_numpy())))

    # ⑪ 時間型欄位：Recency
    cases.append(("⑪ 時間型欄位（r_days_since_last_sale，應被擋）",
                  dict(x_raw=R, col="r_days_since_last_sale", purpose="cluster")))

    # ⑫ 明確資料錯誤 → 分支 A
    cases.append(("⑫ 分支 A：宣告為明確資料錯誤",
                  dict(x_raw=amt, col="刷卡金額", purpose="cluster",
                       is_data_error=True, ids=cust)))
    # ⑬ 宣告要先 winsorize → 06 §三 鐵則擋下
    cases.append(("⑬ 宣告 --want winsorize（應被擋，06 §三 鐵則）",
                  dict(x_raw=amt, col="刷卡金額", purpose="cluster",
                       want="winsorize", ids=cust)))
    # ⑭ fit_on = full 又要拿去預測 → 18-G4 洩漏
    cases.append(("⑭ --fit-on full + --purpose predict（應被擋，18-G4）",
                  dict(x_raw=cai["CAI"].to_numpy(float), col="cai_score",
                       purpose="predict", fit_on="full")))

    results: list[tuple[str, int]] = []
    for title, kw in cases:
        errors.clear(); warnings.clear(); infos.clear()
        print(f"\n\n{'█' * 70}\n{title}\n{'█' * 70}")
        s = analyse(**kw)
        print_suggestion(s)
        rc = flush_buckets(verbose=True)
        results.append((title, rc))

    # 反轉換偏誤守門員：七種交付物 × exp
    print(f"\n\n{'█' * 70}\n⑮ 反轉換偏誤守門員（06 §2.3 對照表逐列）\n{'█' * 70}")
    lg = np.log(amt)
    sigma2 = float(np.var(lg, ddof=1))
    geo, ari, med = float(np.exp(lg.mean())), float(amt.mean()), float(np.median(amt))
    print(f"直接算：算術平均 {ari:,.2f}／exp(mean(ln x)) = {geo:,.2f}／"
          f"比值 {ari / geo:.4f}／ln x 的 σ² = {sigma2:.4f}／"
          f"exp(σ²/2) = {np.exp(sigma2 / 2):.4f}")
    print(f"  7,764 筆總額：實際 {ari * len(amt):,.0f} vs exp 口徑 "
          f"{geo * len(amt):,.0f} → 少算 {ari * len(amt) - geo * len(amt):,.0f}"
          f"（{geo / ari - 1:+.1%}）")
    print(f"06 §2.2 的 lognormal 近似（幾何平均 ≈ 中位數 {med:,.0f}）："
          f"比值 {ari / med:.3f}、σ² = {2 * np.log(ari / med):.3f}、"
          f"總額少算 {(ari - med) * len(amt):,.0f}（{med / ari - 1:+.1%}）")
    print("  兩個口徑都指向同一件事：低估。直接算的低估更重"
          "（真實分布比 lognormal 更右偏），文件用的是保守的近似值。")
    for dl in DELIVERABLES:
        errors.clear(); warnings.clear(); infos.clear()
        st = guard_exp_retransform(dl, "exp", sigma2)
        need, label, route_to = DELIVERABLES[dl]
        print(f"  {dl:<22} 需處理={str(need):<6} exp → {st}")
        results.append((f"⑮ {dl} + exp", 1 if st == "error" else
                        (2 if st == "warn" else 0)))
    for act in ("glm_log", "duan"):
        errors.clear(); warnings.clear(); infos.clear()
        st = guard_exp_retransform("pred_amount", act)
        print(f"  {'pred_amount':<22} 需處理=True   {act} → {st}")
        results.append((f"⑮ pred_amount + {act}",
                        0 if st == "ok" and not warnings else
                        (2 if st == "ok" else 1)))
    errors.clear(); warnings.clear(); infos.clear()

    # Duan smearing：對得上 exp(σ²/2) 嗎
    resid = lg - lg.mean()
    smear = duan_smearing_factor(resid)
    print(f"\n  Duan smearing factor = mean(exp(resid)) = {smear:.4f}"
          f"（殘差常態時的理論值 exp(σ²/2) = {np.exp(sigma2 / 2):.4f}）")
    print(f"  修正後平均 = {geo * smear:,.2f}（樣本算術平均 {ari:,.2f}，"
          f"相對誤差 {abs(geo * smear / ari - 1):.2%}）→ 通過"
          f" assert abs(pred.mean()/y.mean()-1) < 0.05")
    print("  註：兩者差 1.4 倍 —— ln(刷卡金額) 並非常態，所以只能用經驗殘差算 "
          "smearing，不能套 exp(σ²/2)。這正是 Duan 不假設常態的價值。")

    # arcsinh 的 θ 敏感度（樣本裡 arcsinh 都不是第一順位，單獨驗這支函式）
    print(f"\n\n{'█' * 70}\n⑯ arcsinh θ 敏感度（06 §1.3 情境 2）\n{'█' * 70}")
    for name, arr in (("刷卡金額", amt), ("line_amt_net", net)):
        pf_ = profile_column(arr, name)
        sen = ihs_sensitivity(arr[np.isfinite(arr)], pf_)
        pairs = "、".join(f"θ={t:,.4g}→skew {s:+.4f}"
                          for t, s in zip(sen["thetas"], sen["post_skew"]))
        print(f"  {name}: {pairs}")
        print(f"    偏度正負號一致={sen['skew_sign_stable']}、"
              f"偏度全距={sen['skew_range']:.4f}")
    print("  註：這裡只驗得了偏度敏感度。係數敏感度要 M7 配完模型才做得出來，"
          "腳本把它寫成 params.sensitivity.todo。")

    # 已知事實回歸測試
    print(f"\n\n{'█' * 70}\n⑰ 已知事實斷言\n{'█' * 70}")
    checks = [
        ("交易筆數 = 7,764", len(txn) == 7764),
        ("客戶數 = 100", txn["客戶ID"].nunique() == 100),
        ("CAI 人數 = 99", len(cai) == 99),
        ("CAI 值域 −43.665943 ~ +54.590571",
         abs(cai["CAI"].min() + 43.665943) < 1e-6
         and abs(cai["CAI"].max() - 54.590571) < 1e-6),
        ("客戶 89 的 MLE = 10.279412",
         abs(float(cai.loc[cai["Custom ID"] == 89, "MLE"].iloc[0]) - 10.279412) < 1e-6),
        ("客戶 89 的 WMLE = 11.570759",
         abs(float(cai.loc[cai["Custom ID"] == 89, "WMLE"].iloc[0]) - 11.570759) < 1e-6),
        ("客戶 89 的 CAI = −12.562460",
         abs(float(cai.loc[cai["Custom ID"] == 89, "CAI"].iloc[0]) + 12.562460) < 1e-6),
        ("客戶 89 的 f_txn_cnt = 85", int(g.loc[89, "F"]) == 85),
        ("客戶 89 的 M = 150,681", int(g.loc[89, "M"]) == 150681),
        ("客戶 89 的 R = 19（基準日 2012-12-01）",
         int(R[list(g.index).index(89)]) == 19),
    ]
    allok = True
    for name, good in checks:
        print(f"  {'✅' if good else '⛔'} {name}")
        allok &= good

    print(f"\n\n{'=' * 70}\n自我測試總表\n{'=' * 70}")
    for title, rc in results:
        tag = {0: "0 通過", 1: "1 擋住", 2: "2 有警告"}[rc]
        print(f"  [{tag}] {title}")
    print(f"\n已知事實斷言：{'全部通過' if allok else '有失敗'}")
    return 0 if allok else 1


# ═══════════════════════════════════════════════════════════════════
def main() -> int:
    ap = argparse.ArgumentParser(
        description="M3 轉換方法選用（06 §一 七情境順位表 + §二 反轉換防呆 + "
                    "§三 winsorize 順序）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("用法：")[-1])
    ap.add_argument("專案代號", help="paths.project_dir 用它決定資料庫與輸出位置")
    ap.add_argument("--parquet", help="資料檔（絕對路徑，或相對於專案子目錄）")
    ap.add_argument("--table", help="從專案 DuckDB 讀（走 db.connect，唯讀）")
    ap.add_argument("--col", help="要判定的數值欄名")
    ap.add_argument("--id-col", help="顧客 ID 欄名（分支 C 條件 3 要列出受影響 ID）")
    ap.add_argument("--purpose", default="predict",
                    choices=list(PURPOSE_LABEL), help="交付物用途（決定第一順位）")
    ap.add_argument("--ratio", action="store_true", help="宣告這是連續型比例 [0,1]")
    ap.add_argument("--int-denominator", action="store_true",
                    help="宣告有整數分子/分母（點擊/曝光）→ 走 binomial GLM")
    ap.add_argument("--zero-kind", default="unknown",
                    choices=["structural", "random", "unknown"],
                    help="10–30%% 灰帶時，零是結構性還是隨機")
    ap.add_argument("--peer-cols", help="一起進距離模型的其他欄，逗號分隔（情境 7）")
    ap.add_argument("--want", help="你打算用的方法（會被驗證）：log/log_c/yj/bc/"
                                   "ihs/logit/asin/square/cube/winsorize…")
    ap.add_argument("--fit-on", default="train", choices=["train", "full"],
                    help="轉換參數從哪學（06 §4.1，full 只允許非監督/描述用途）")
    ap.add_argument("--data-error", action="store_true",
                    help="宣告這欄的可疑值是明確資料錯誤 → 06 §3.2 分支 A")
    ap.add_argument("--not-time", action="store_true",
                    help="關閉欄名層級的時間型/tenure 攔截")
    ap.add_argument("--check-exp", action="store_true",
                    help="只做反轉換偏誤檢查，不需要資料")
    ap.add_argument("--deliverable", choices=list(DELIVERABLES),
                    help="交付物代碼（06 §2.3）")
    ap.add_argument("--action", default="exp", choices=list(ACTIONS),
                    help="你打算怎麼回到原尺度")
    ap.add_argument("--json", help="把建議寫成 JSON 檔（給 write_transform_log.py 吃）")
    ap.add_argument("--save", action="store_true",
                    help="寫到 <專案>/顧客特徵表/transform_suggestion__<欄名>.json")
    ap.add_argument("--self-test", action="store_true",
                    help="用課程資料集樣本跑完整自我測試")
    ap.add_argument("--verbose", action="store_true", help="連通過項也列出")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    print("=" * 70)
    print(f"M3 轉換方法選用｜專案：{args.專案代號}")
    print("規格：references/06_前處理與轉換.md §一 順位表／§二 反轉換／§三 winsorize")
    print("=" * 70)

    if args.check_exp:
        if not args.deliverable:
            print("⛔ --check-exp 要一起給 --deliverable —— "
                  f"可用：{', '.join(DELIVERABLES)}")
            return 1
        guard_exp_retransform(args.deliverable, args.action)
        return flush_buckets(args.verbose)

    if not args.col:
        print("⛔ 沒給 --col —— 這支一次判一個數值欄，欄名是必要的")
        return 1

    try:
        df = load_frame(args.專案代號, args.parquet, args.table)
    except Exception as e:  # noqa: BLE001
        print(f"⛔ 讀資料失敗：{e}")
        return 1

    if args.col not in df.columns:
        print(f"⛔ 找不到欄位 `{args.col}` —— 這張表的欄位是："
              f"{', '.join(map(str, df.columns[:40]))}")
        return 1

    peer = None
    if args.peer_cols:
        names = [c.strip() for c in args.peer_cols.split(",") if c.strip()]
        miss = [c for c in names if c not in df.columns]
        if miss:
            print(f"⛔ --peer-cols 有欄位不存在：{', '.join(miss)}")
            return 1
        peer = {c: df[c].to_numpy(dtype=float, na_value=np.nan) for c in names}

    ids = df[args.id_col].to_numpy() if args.id_col and args.id_col in df.columns \
        else None

    s = analyse(
        x_raw=df[args.col].to_numpy(dtype=float, na_value=np.nan),
        col=args.col, purpose=args.purpose, is_ratio=args.ratio,
        has_int_denominator=args.int_denominator, zero_kind=args.zero_kind,
        treat_as_time=not args.not_time, is_data_error=args.data_error,
        ids=ids, peer=peer, want=args.want, fit_on=args.fit_on)

    print_suggestion(s)

    out_path: Path | None = None
    if args.json:
        out_path = Path(args.json)
    elif args.save:
        pp = project_dir(args.專案代號)
        out_path = pp.features / f"transform_suggestion__{args.col}.json"
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = s.to_json()
        payload["fit_on"] = args.fit_on
        payload["purpose"] = args.purpose
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        print(f"\n建議已寫出：{out_path}")
        print("  ⚠ 這只是建議。實際寫進 transform_log.csv 之前要人確認"
              "（06 §一：這支只「建議」不「執行」）")

    return flush_buckets(args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
