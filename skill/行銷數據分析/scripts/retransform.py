#!/usr/bin/env python3
"""
反轉換工具 —— 取 log 建模之後，怎麼把預測值變回「金額」而不低估。

為什麼需要它（references/06_前處理與轉換.md §二）：
    E[Y] = E[exp(log Y)] ≠ exp(E[log Y])
    exp 是凸函數，Jensen 不等式保證 E[exp(Z)] ≥ exp(E[Z])，等號只在 Z 沒有變異時成立。
    所以 `exp(平均的 log)` 拿到的是**幾何平均**，不是算術平均；右偏資料的幾何平均
    恆小於算術平均 —— 這個偏誤**必然是低估**，偏度越大低估越多。

    低估倍數是 exp(σ²/2)，只跟殘差變異有關，**跟模型配得好不好完全無關**。
    這是它最陰險的地方：R² 高、殘差圖漂亮、Q-Q plot 直，偏誤照樣在那裡，
    沒有任何一個診斷會亮紅燈。課程資料集的交易金額實測（7,764 筆）：
    算術平均 1,909.73，exp(平均的 log) = 455.60，**少算 76.1%**。
    年度促銷預算按營收 3% 編列，就是 44.5 萬編成 10.6 萬。

    三個解法（§2.3）：
      ① Gamma GLM + log link —— 建模的是 log(E[Y])，exp(Xb) 直接就是 E[Y]，
         沒有偏誤要修。**只要交付物含「預測金額／營收／客單價」，一律走這條。**
      ② Duan smearing —— 已經配了 log-OLS、不想重配 GLM 時的補救。
      ③ 只要排序（分群、Top-N、Spearman、效果量比較）就不用管。

用法：
    python retransform.py <專案代號>
        掃描 顧客特徵表/transform_spec.json，檢查每個轉換欄位的反轉換風險。

    python retransform.py <專案代號> --self-test
        內建自我測試：造一組右偏資料，把「直接 exp」「Duan smearing」「真實算術平均」
        三個數字並排印出來，證明直接 exp 系統性低估。找得到素材庫時一併用
        課程資料集（7,764 筆真實交易）實跑一次。

退出碼（全庫統一，權威定義見 00 §八）：
    0  = 全通過
    1  = 有 error，不准交付
    2  = 只有 warning，可往下但報告要寫明口徑
    64 = 用法錯誤（旗標打錯、缺專案代號）
    70 = 腳本自身異常

當函式庫用：
    from retransform import duan_smearing, safe_inverse, check_retransform_risk

    m = sm.OLS(np.log(y), X).fit()
    check_retransform_risk(m).print_report()      # 有人要直接 exp 就會被抓到
    e_y = duan_smearing(m, X_new)                 # 這才是 E[Y]

實作判斷（reference 沒規定，這裡自己定的，見各處〔實作判斷〕標記）：
    · transform_spec.json 的欄位 entry 允許多一個 "retransform" 鍵，記載這一欄
      要用哪條路線回原尺度（glm_log / duan_smearing / rank_only / median_only）。
      §4.4 的 schema 沒有這個鍵，但沒有它就無法在交付前自動判斷「這一欄的金額
      到底修了沒有」—— 掃描器只能靠它放行。
    · 一般化 smearing 的殘差取樣上限（2,000 個分位點）。
    · endog 是否已取 log 的自動判定啟發式。
"""

from __future__ import annotations

import json
import sys
import unicodedata
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)
from paths import archive_root, project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# ══════════════════════════════════════════════════════════════════
# 例外與警告
# ══════════════════════════════════════════════════════════════════

class RetransformBiasError(ValueError):
    """要求回到原尺度的算術平均，但沒有給修正依據 —— 擋下，不給錯的數字。"""


class RetransformWarning(UserWarning):
    """可以放行，但報告口徑必須寫清楚。"""


# ══════════════════════════════════════════════════════════════════
# 一、轉換方法表：每個方法的反轉換函式與偏誤性質
# ══════════════════════════════════════════════════════════════════
# bias 欄的三種值：
#   "log"    —— 反轉換是 exp 型，E[Y] 可用**乘法** smearing factor 修正（§2.3 ②）
#   "curve"  —— 非線性但不是 exp 型，沒有乘法捷徑，只能走一般化 smearing 或改 GLM
#   "linear" —— 線性或恆等，期望值可交換，沒有偏誤

@dataclass(frozen=True)
class Method:
    key: str
    bias: str
    inverse: Callable[[np.ndarray, dict], np.ndarray]
    desc: str
    needs: tuple[str, ...] = ()


def _need(params: dict, *names: str) -> float:
    """從 params 取參數，缺了就給「事實 — 該怎麼辦」的錯誤。"""
    for n in names:
        if n in params and params[n] is not None:
            return float(params[n])
    raise RetransformBiasError(
        f"轉換規格缺少參數 {names[0]}，無法反轉換。\n"
        f"  該怎麼辦：到 顧客特徵表/transform_spec.json 把該欄的 params.{names[0]} 補上。"
        f"參數只能是當初 fit 在訓練集上的那一個值（§4.1），不可以拿現在這批資料重估。"
    )


def _inv_log(z: np.ndarray, p: dict) -> np.ndarray:
    return np.exp(z)


def _inv_log_c(z: np.ndarray, p: dict) -> np.ndarray:
    return np.exp(z) - _need(p, "c", "shift", "offset")


def _inv_arcsinh(z: np.ndarray, p: dict) -> np.ndarray:
    return _need(p, "theta") * np.sinh(z)


def _inv_box_cox(z: np.ndarray, p: dict) -> np.ndarray:
    lam = _need(p, "lambda", "lmbda")
    if lam == 0.0:
        return np.exp(z)
    base = lam * z + 1.0
    if np.any(base <= 0):
        raise RetransformBiasError(
            f"Box-Cox 反轉換遇到 λ·z+1 ≤ 0（λ={lam:g}，共 {int((base <= 0).sum())} 筆），"
            f"數學上無解。\n"
            f"  該怎麼辦：這代表模型預測值跑出了 Box-Cox 的值域。改走 Gamma GLM + log link"
            f"（§2.3 ①，值域天生為正），或在 transform_spec 加 clip_on_apply 並在報告寫明"
            f"被 clip 的列數。"
        )
    return np.power(base, 1.0 / lam)


def _inv_yeo_johnson(z: np.ndarray, p: dict) -> np.ndarray:
    lam = _need(p, "lambda", "lmbda")
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    if lam == 0.0:
        out[pos] = np.expm1(z[pos])
    else:
        out[pos] = np.power(lam * z[pos] + 1.0, 1.0 / lam) - 1.0
    if lam == 2.0:
        out[~pos] = 1.0 - np.exp(-z[~pos])
    else:
        out[~pos] = 1.0 - np.power(-(2.0 - lam) * z[~pos] + 1.0, 1.0 / (2.0 - lam))
    return out


def _inv_logit(z: np.ndarray, p: dict) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))


def _inv_arcsine_sqrt(z: np.ndarray, p: dict) -> np.ndarray:
    return np.square(np.sin(np.asarray(z, dtype=float)))


def _inv_square(z: np.ndarray, p: dict) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    if np.any(z < 0):
        raise RetransformBiasError(
            "平方轉換的反轉換遇到負值，開根號無解。\n"
            "  該怎麼辦：平方對含負值的欄是非單調轉換（§6.1 最後一列），"
            "回 §一 重新分流，含負值請走 Yeo-Johnson。"
        )
    return np.sqrt(z)


def _inv_cube(z: np.ndarray, p: dict) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    return np.sign(z) * np.power(np.abs(z), 1.0 / 3.0)


def _inv_identity(z: np.ndarray, p: dict) -> np.ndarray:
    return np.asarray(z, dtype=float)


def _inv_zscore(z: np.ndarray, p: dict) -> np.ndarray:
    return np.asarray(z, dtype=float) * _need(p, "scale", "sd", "std") + _need(p, "center", "mean")


METHODS: dict[str, Method] = {
    "log": Method("log", "log", _inv_log, "自然對數 ln(x)"),
    "log_c": Method("log_c", "log", _inv_log_c, "log(x+c)", ("c",)),
    "arcsinh": Method("arcsinh", "log", _inv_arcsinh, "arcsinh(x/θ)", ("theta",)),
    "box_cox": Method("box_cox", "curve", _inv_box_cox, "Box-Cox", ("lambda",)),
    "yeo_johnson": Method("yeo_johnson", "curve", _inv_yeo_johnson, "Yeo-Johnson", ("lambda",)),
    "logit": Method("logit", "curve", _inv_logit, "logit(p)"),
    "arcsine_sqrt": Method("arcsine_sqrt", "curve", _inv_arcsine_sqrt, "arcsin(√p)"),
    "square": Method("square", "curve", _inv_square, "x²（情境 6 左偏）"),
    "cube": Method("cube", "curve", _inv_cube, "x³（情境 6 左偏）"),
    "zscore": Method("zscore", "linear", _inv_zscore, "z-score", ("center", "scale")),
    "none": Method("none", "linear", _inv_identity, "不轉換"),
}

# 別名：transform_spec.json 可能用簡寫或欄名後綴的寫法
_ALIAS = {
    "ln": "log", "log10": "log", "log_x_plus_c": "log_c", "logc": "log_c",
    "ihs": "arcsinh", "asinh": "arcsinh", "bc": "box_cox", "yj": "yeo_johnson",
    "power_transform": "yeo_johnson", "robust_scaler": "zscore",
    "standardize": "zscore", "": "none", "identity": "none",
}

# 這些不是「轉換」而是「換模型」或「換尺度型態」，沒有欄位可以反轉換
_MODEL_ROUTES = {
    "gamma_glm_log": "Gamma GLM + log link —— predict() 出來已經是 E[Y]",
    "glm_log": "GLM + log link —— predict() 出來已經是 E[Y]",
    "tweedie": "Tweedie —— predict() 出來已經是 E[Y]",
    "hurdle": "Hurdle 兩段模型 —— E[Y] = P(買) × E[Y|買]，兩段各自預測後相乘",
    "zinb": "ZINB —— 由模型自己給期望值",
    "beta_reg": "Beta regression —— predict() 出來已經是 E[p]",
    "binomial_glm": "Binomial GLM —— predict() 出來已經是 E[p]",
}
_BIN_ROUTES = {"ntile", "quantile_bin", "bin", "qcut"}


def resolve_method(name: str | None) -> str:
    key = (name or "none").strip().lower()
    return _ALIAS.get(key, key)


# ══════════════════════════════════════════════════════════════════
# 二、Duan smearing estimator（§2.3 ②）
# ══════════════════════════════════════════════════════════════════
#   E[Y_i] = exp(X_i·b) · (1/n)Σ_j exp(ε̂_j)
# 它不假設殘差常態，只用經驗殘差。殘差近似常態時 smearing factor 會收斂到
# exp(σ̂²/2)。前提是**殘差同質變異**；有異質變異時要分組算，否則低估只是
# 從整體搬到某幾段。

# 一般化 smearing 的殘差取樣上限〔實作判斷〕：n_pred × n_resid 的矩陣會爆記憶體，
# 7,764 筆預測 × 7,764 個殘差已經是 6,000 萬格。取殘差經驗分布的等距分位點，
# 既保留分布形狀又固定成本，且結果可重現（不是隨機抽樣）。
_MAX_RESID = 2000

_HETERO_ALPHA = 0.05   # Breusch-Pagan 的顯著水準，沿用 16 的慣例
_N_SMEAR_GROUPS = 5    # §2.3「按預測值分位分成 5 組各算一個」


def _resid_of(model: Any) -> np.ndarray:
    r = np.asarray(getattr(model, "resid", None), dtype=float)
    if r.ndim != 1 or r.size == 0:
        raise RetransformBiasError(
            "模型物件取不到殘差（model.resid）。\n"
            "  該怎麼辦：Duan smearing 需要經驗殘差。請傳入 statsmodels 的已配適結果"
            "（sm.OLS(np.log(y), X).fit()），或改走 Gamma GLM + log link（§2.3 ①）。"
        )
    return r


def _predict_z(model: Any, X: Any) -> np.ndarray:
    """回傳轉換尺度上的預測值（log scale）。X 為 None 時用模型自己的配適值。"""
    if X is None:
        return np.asarray(model.fittedvalues, dtype=float)
    return np.asarray(model.predict(X), dtype=float)


def hetero_pvalue(model: Any) -> float | None:
    """Breusch-Pagan 異質變異檢定的 p 值。算不出來回 None（不阻擋流程）。"""
    try:
        from statsmodels.stats.diagnostic import het_breuschpagan  # noqa: PLC0415
        exog = np.asarray(model.model.exog, dtype=float)
        if exog.ndim != 2 or exog.shape[1] < 2:
            return None      # 只有截距，沒有可檢定的異質性
        _lm, p_lm, _f, _pf = het_breuschpagan(_resid_of(model), exog)
        return float(p_lm)
    except Exception:  # noqa: BLE001
        return None


def smearing_factors(
    model: Any,
    groups: int | None = None,
) -> dict[str, Any]:
    """算 smearing factor，順便把「該不該分組」的證據一起回傳。

    groups=None → 單一 factor；groups=k → 依配適值分位切 k 組各算一個。
    回傳的 dict 可直接存進 模型輸出/smearing.json，交付時要能追回（18-E7）。
    """
    resid = _resid_of(model)
    fitted = np.asarray(model.fittedvalues, dtype=float)
    out: dict[str, Any] = {
        "n": int(resid.size),
        "pooled": float(np.mean(np.exp(resid))),
        "hetero_p": hetero_pvalue(model),
    }
    sigma2 = getattr(model, "mse_resid", None)
    if sigma2 is not None and np.isfinite(sigma2):
        out["sigma2"] = float(sigma2)
        out["lognormal_factor"] = float(np.exp(float(sigma2) / 2.0))

    if groups:
        qs = np.linspace(0, 1, groups + 1)[1:-1]
        cuts = np.quantile(fitted, qs)
        gidx = np.digitize(fitted, cuts)
        out["cuts"] = [float(c) for c in cuts]
        out["by_group"] = {
            int(g): float(np.mean(np.exp(resid[gidx == g])))
            for g in range(groups) if np.any(gidx == g)
        }
    return out


def _smear_general(
    z: np.ndarray,
    resid: np.ndarray,
    inverse: Callable[[np.ndarray, dict], np.ndarray],
    params: dict,
) -> np.ndarray:
    """一般化 smearing：E[Y_i] = (1/n)Σ_j g⁻¹(z_i + ε̂_j)。

    Duan (1983) 的原始形式就是這一條，log 只是它可以因式分解的特例。
    Yeo-Johnson / Box-Cox / arcsinh 這種沒有乘法捷徑的轉換要用這條。
    """
    if resid.size > _MAX_RESID:
        resid = np.quantile(resid, np.linspace(0.0, 1.0, _MAX_RESID))
    z = np.asarray(z, dtype=float).ravel()
    out = np.empty(z.size, dtype=float)
    chunk = max(1, int(4_000_000 / max(resid.size, 1)))
    for i in range(0, z.size, chunk):
        blk = z[i:i + chunk][:, None] + resid[None, :]
        out[i:i + chunk] = inverse(blk, params).mean(axis=1)
    return out


def duan_smearing(
    model: Any,
    X: Any = None,
    *,
    inverse: Callable[[np.ndarray, dict], np.ndarray] | None = None,
    params: dict | None = None,
    groups: int | str | None = "auto",
    hetero_alpha: float = _HETERO_ALPHA,
) -> np.ndarray:
    """把 log-OLS 的預測值變回 E[Y]（原尺度的**算術平均**）。

    model     statsmodels 的已配適結果，endog 必須是 log(y)
    X         要預測的設計矩陣；None 表示用訓練資料自己的配適值
    inverse   反轉換函式，預設 exp（log-OLS）。傳別的（如 Yeo-Johnson 的反函式）
              會自動改走一般化 smearing
    groups    "auto"（預設）= 先跑 Breusch-Pagan，異質變異就自動分 5 組並發警告；
              None = 強制單一 factor；int = 強制分該組數
    """
    params = params or {}
    resid = _resid_of(model)
    z = _predict_z(model, X)

    # 決定分組數
    if groups == "auto":
        p = hetero_pvalue(model)
        if p is not None and p < hetero_alpha:
            groups = _N_SMEAR_GROUPS
            warnings.warn(
                f"Breusch-Pagan p = {p:.4g} < {hetero_alpha} —— 殘差異質變異，"
                f"已自動改用分 {_N_SMEAR_GROUPS} 組的 smearing factor。"
                f"單一 factor 會讓低估從整體搬到某幾段（§2.3 ②）。"
                f"報告要寫明用了分組 smearing。",
                RetransformWarning, stacklevel=2,
            )
        else:
            groups = None

    is_exp = inverse is None or inverse is _inv_log

    if not groups:
        if is_exp:
            return np.exp(z) * float(np.mean(np.exp(resid)))
        return _smear_general(z, resid, inverse, params)

    fitted = np.asarray(model.fittedvalues, dtype=float)
    qs = np.linspace(0, 1, int(groups) + 1)[1:-1]
    cuts = np.quantile(fitted, qs)
    g_train = np.digitize(fitted, cuts)
    g_pred = np.digitize(z, cuts)

    out = np.empty(z.size, dtype=float)
    for g in np.unique(g_pred):
        mask_p = g_pred == g
        r_g = resid[g_train == g]
        if r_g.size == 0:                      # 預測落到訓練沒有的區段 → 退回全體殘差
            r_g = resid
        if is_exp:
            out[mask_p] = np.exp(z[mask_p]) * float(np.mean(np.exp(r_g)))
        else:
            out[mask_p] = _smear_general(z[mask_p], r_g, inverse, params)
    return out


# ══════════════════════════════════════════════════════════════════
# 三、safe_inverse —— 依轉換規格正確反轉
# ══════════════════════════════════════════════════════════════════

_TARGETS = ("mean", "median", "rank")


def safe_inverse(
    values: Sequence[float] | np.ndarray,
    transform_spec: dict | str,
    *,
    target: str = "mean",
    smearing_factor: float | None = None,
    residuals: Sequence[float] | np.ndarray | None = None,
) -> np.ndarray:
    """把轉換尺度上的值依規格反轉回原尺度。log 類一律走 smearing，否則擋下。

    values           轉換尺度上的值（模型預測值或轉換後欄位）
    transform_spec   transform_spec.json 裡該欄的 entry，或直接給方法名字串
    target           要回什麼口徑：
                       "mean"   —— 原尺度的算術平均（金額、營收、客單價）。
                                   log 類必須給 smearing_factor 或 residuals，否則擋下。
                       "median" —— 中位數／幾何平均。單調轉換直接 exp 合法，
                                   但會發警告：報告必須寫明「這是中位數不是平均」（§2.3 表）。
                       "rank"   —— 只要排序（分群、Top-N、Spearman）。單調轉換不影響排序。
    smearing_factor  log 類的乘法修正係數，來自 duan_smearing / smearing_factors
    residuals        經驗殘差；給了就走一般化 smearing（非 log 類唯一的正解）
    """
    if target not in _TARGETS:
        raise ValueError(f"target 只能是 {_TARGETS} 其中之一，收到 {target!r}")

    spec: dict = {"method": transform_spec} if isinstance(transform_spec, str) else dict(transform_spec)
    raw_method = str(spec.get("method", "none"))
    method = resolve_method(raw_method)
    params: dict = dict(spec.get("params") or {})
    z = np.asarray(values, dtype=float)

    # ── 換模型的路線：根本沒有轉換欄位可以反轉 ──────────────────
    if method in _MODEL_ROUTES:
        raise RetransformBiasError(
            f"method='{raw_method}' 不是尺度轉換，是換模型（{_MODEL_ROUTES[method]}）。\n"
            f"  該怎麼辦：不要對它呼叫 safe_inverse。這條路線的 predict() 已經是 E[Y]，"
            f"再乘任何 smearing factor 就是**高估**。"
        )
    if method in _BIN_ROUTES:
        raise RetransformBiasError(
            f"method='{raw_method}' 是分箱，不是可逆轉換（多對一）。\n"
            f"  該怎麼辦：分箱後只剩序數資訊，要回原尺度只能回去查原欄位。"
            f"Recency 用分位分箱是 §4.5 的規定，本來就不打算回原尺度。"
        )
    if method not in METHODS:
        raise RetransformBiasError(
            f"不認得的轉換方法 '{raw_method}'。\n"
            f"  該怎麼辦：transform_spec.json 的 method 只能是 "
            f"{sorted(set(METHODS) | set(_ALIAS))} 之一（見 §4.2 後綴表）。"
        )

    m = METHODS[method]

    # ── 只要排序 / 中位數：單調轉換不需要修正（§2.3 ③）────────────
    if target in ("rank", "median"):
        if method in ("square", "cube") and np.any(z < 0):
            warnings.warn(
                "平方／立方對含負值的資料是非單調轉換，排序會被翻掉（§6.1）。"
                "請回 §一 重新分流。", RetransformWarning, stacklevel=2,
            )
        if target == "median" and m.bias in ("log", "curve"):
            warnings.warn(
                f"target='median'：{m.desc} 的反轉換給的是中位數／幾何平均，不是算術平均。"
                f"報告寫這個數字時**必須寫明是中位數**（§2.3 表第 3 列），"
                f"否則就是 18-E7 的口徑錯誤。",
                RetransformWarning, stacklevel=2,
            )
        return m.inverse(z, params)

    # ── target='mean'：偏誤處理 ────────────────────────────────
    if m.bias == "linear":
        if method == "zscore":
            warnings.warn(
                "標準化不該出現在 transform_spec.json（§五）—— 它屬於各方法族自己的第一步，"
                "參數在 模型輸出/scaler.json 或 sklearn Pipeline 裡。這裡照樣反轉（線性轉換"
                "沒有 Jensen 偏誤），但請把它從 M3 的規格檔搬走。",
                RetransformWarning, stacklevel=2,
            )
        return m.inverse(z, params)

    if residuals is not None:
        r = np.asarray(residuals, dtype=float).ravel()
        if method == "log_c":                     # E[exp(z)] - c，先修再平移
            c = _need(params, "c", "shift", "offset")
            return _smear_general(z, r, _inv_log, {}) - c
        return _smear_general(z, r, m.inverse, params)

    if m.bias == "log":
        if smearing_factor is None:
            raise RetransformBiasError(
                f"擋下：method='{raw_method}' 是 log 類轉換，直接反轉會得到幾何平均，"
                f"對右偏資料**必然低估**（§二；課程資料集實測少算 76.1%）。\n"
                f"  該怎麼辦：三選一 ——\n"
                f"    ① 改配 Gamma GLM + log link，exp(Xb) 直接就是 E[Y]（預設走這條）；\n"
                f"    ② 傳 smearing_factor=duan_smearing 算出的係數，或 residuals=模型殘差；\n"
                f"    ③ 若交付物只要排序或中位數，改用 target='rank' / target='median'。"
            )
        s = float(smearing_factor)
        if method == "log_c":
            return np.exp(z) * s - _need(params, "c", "shift", "offset")
        if method == "arcsinh":
            raise RetransformBiasError(
                "擋下：arcsinh 的反轉換是 sinh，沒有乘法 smearing 這種捷徑，"
                "乘一個係數上去只是換一個錯的數字。\n"
                "  該怎麼辦：傳 residuals=模型殘差走一般化 smearing，"
                "或改走 Gamma GLM + log link（§2.3 ①）。"
            )
        return m.inverse(z, params) * s

    # curve：非線性但不是 exp 型
    raise RetransformBiasError(
        f"擋下：method='{raw_method}'（{m.desc}）的反轉換是非線性的，"
        f"g⁻¹(平均) ≠ 平均(g⁻¹)，乘法 smearing factor 在這裡不成立。\n"
        f"  該怎麼辦：傳 residuals=模型殘差走一般化 smearing "
        f"（E[Y_i] = mean_j g⁻¹(z_i + ε̂_j)），或改走 §2.3 ① 的 GLM 路線。"
        f"若只要排序或中位數，改 target='rank' / 'median'。"
    )


# ══════════════════════════════════════════════════════════════════
# 四、check_retransform_risk —— 偵測有沒有人要直接 exp
# ══════════════════════════════════════════════════════════════════

_LOG_NAME_HINTS = ("log", "ln(", "__log", "lg_")


@dataclass
class RiskReport:
    """一個模型的反轉換風險診斷。三桶 + 退出碼，沿用 setup_check.py 的形式。"""
    model_kind: str = "unknown"
    errors: list[str] = field(default_factory=list)
    warnings_: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    numbers: dict[str, Any] = field(default_factory=dict)

    @property
    def exit_code(self) -> int:
        if self.errors:
            return EX_ERROR
        return EX_WARN if self.warnings_ else EX_OK

    def print_report(self, out=None) -> None:
        out = out or sys.stdout
        print(f"模型型態：{self.model_kind}", file=out)
        for k, v in self.numbers.items():
            print(f"  · {k}：{v}", file=out)
        for m in self.errors:
            print(f"  ⛔ {m}", file=out)
        for m in self.warnings_:
            print(f"  ⚠ {m}", file=out)
        for m in self.infos:
            print(f"  ✅ {m}", file=out)


def _looks_logged(endog: np.ndarray) -> bool:
    """endog 疑似已取 log 的啟發式〔實作判斷〕。

    判準：值域窄（|x| < 30，exp 回去不會溢位）、本身接近對稱、但 exp 回去右偏。
    這是「疑似」不是「確定」，命中只會進 warning 桶。
    """
    e = endog[np.isfinite(endog)]
    if e.size < 20 or e.min() < -30 or e.max() > 30:
        return False
    try:
        from scipy import stats  # noqa: PLC0415
        return abs(float(stats.skew(e))) < 1.0 and float(stats.skew(np.exp(e))) > 1.0
    except Exception:  # noqa: BLE001
        return False


def check_retransform_risk(model: Any, *, is_log_endog: bool | None = None) -> RiskReport:
    """看一個已配適的模型，判斷它的預測值能不能直接 exp 回原尺度。

    is_log_endog=None 時自動判定：先看 endog 欄名，再看數值型態的啟發式。
    """
    rep = RiskReport()
    mdl = getattr(model, "model", None)

    # ⓪ 不是 statsmodels 的配適結果 → 不能靜默說「沒問題」
    if mdl is None or not hasattr(mdl, "endog"):
        rep.model_kind = type(model).__name__
        rep.warnings_.append(
            "這不是 statsmodels 的配適結果（取不到 model.endog），無法判定有沒有反轉換偏誤。\n"
            "      該怎麼辦：若這個模型是配在 log(y) 上（sklearn、XGBoost 都常這樣做），"
            "預測值 exp 回去一樣會低估。請自己算殘差後傳 residuals 給 safe_inverse，"
            "或改用目標為原尺度的模型（Gamma GLM／Tweedie／objective='reg:gamma'）。"
        )
        return rep

    # ① GLM + log link → 正解，exp(Xb) 就是 E[Y]
    fam = getattr(mdl, "family", None)
    if fam is not None:
        link = getattr(fam, "link", None)
        link_name = type(link).__name__.lower() if link is not None else "?"
        fam_name = type(fam).__name__
        rep.model_kind = f"GLM({fam_name}, link={link_name})"
        if link_name.startswith("log") and "logit" not in link_name:
            rep.infos.append(
                f"{fam_name} GLM + log link 建模的是 log(E[Y])，"
                f"predict() 出來已經是 E[Y] —— 不要再乘任何 smearing factor，乘了就變高估（§2.3 ①）。"
            )
            rep.infos.append(
                "提醒：信賴區間要在 link scale 算好再轉換，不能轉換上下界的中點；"
                "診斷圖第 1 張改用 deviance residual vs linear predictor。"
            )
        else:
            rep.infos.append(f"link={link_name}，不是 log link，沒有 exp 反轉換的問題。")
        return rep

    # ② OLS：endog 是不是 log
    endog = np.asarray(getattr(mdl, "endog", []), dtype=float).ravel()
    name = str(getattr(mdl, "endog_names", "") or "")
    guessed = False
    if is_log_endog is None:
        if any(h in name.lower() for h in _LOG_NAME_HINTS):
            is_log_endog = True
        else:
            is_log_endog = _looks_logged(endog)
            guessed = bool(is_log_endog)

    rep.model_kind = f"{type(mdl).__name__}(endog={name or '未命名'})"

    if not is_log_endog:
        rep.infos.append(
            "endog 看起來不是 log 尺度，沒有反轉換偏誤。"
            "（若其實有取 log，請傳 is_log_endog=True 重跑 —— 欄名沒帶 log 是 §4.2 的違規）"
        )
        return rep

    resid = _resid_of(model)
    sigma2 = float(getattr(model, "mse_resid", np.var(resid, ddof=1)))
    smear = float(np.mean(np.exp(resid)))
    lognorm = float(np.exp(sigma2 / 2.0))
    understate = 1.0 - 1.0 / smear

    rep.numbers = {
        "殘差變異 σ̂²": f"{sigma2:.4f}",
        "lognormal 理論倍數 exp(σ̂²/2)": f"{lognorm:.4f}",
        "Duan smearing factor": f"{smear:.4f}",
        "直接 exp 的低估幅度": f"{understate:.1%}",
    }

    head = "疑似（自動判定，請確認）" if guessed else ""
    rep.errors.append(
        f"{head}endog 是 log 尺度：直接 exp(Xb) 得到的是幾何平均，"
        f"會低估 E[Y] 約 {understate:.1%}（smearing factor = {smear:.4f}）。\n"
        f"      該怎麼辦：交付物含金額就走 ① Gamma GLM + log link 重配，"
        f"或 ② duan_smearing(model, X)。只要排序／中位數則不受影響（③）。"
    )

    p = hetero_pvalue(model)
    if p is not None:
        rep.numbers["Breusch-Pagan p"] = f"{p:.4g}"
        if p < _HETERO_ALPHA:
            rep.warnings_.append(
                f"殘差異質變異（BP p = {p:.4g} < {_HETERO_ALPHA}）：單一 smearing factor "
                f"只會把低估從整體搬到某幾段。要按預測值分位分 {_N_SMEAR_GROUPS} 組各算一個"
                f"（duan_smearing 的 groups='auto' 會自動處理）。"
            )

    # §二 的硬檢查：修正後的模型平均必須對得上樣本平均
    try:
        y = np.exp(endog)
        pred = np.exp(np.asarray(model.fittedvalues, dtype=float)) * smear
        ratio = float(pred.mean() / y.mean() - 1.0)
        rep.numbers["修正後 平均比 樣本平均 −1"] = f"{ratio:+.4%}"
        if abs(ratio) >= 0.05:
            rep.warnings_.append(
                f"smearing 修正後模型平均與樣本平均仍差 {ratio:+.2%}（門檻 5%）："
                f"殘差分布可能不同質，或 X 沒解釋到主要的量級變動。"
                f"要分組算 smearing factor，並在報告寫明。"
            )
    except Exception:  # noqa: BLE001
        pass

    return rep


# ══════════════════════════════════════════════════════════════════
# 五、CLI ①：掃描專案的 transform_spec.json
# ══════════════════════════════════════════════════════════════════

# 欄位 entry 的 "retransform" 鍵允許的值〔實作判斷，§4.4 schema 的擴充〕
_OK_ROUTES = {
    "glm_log": "改走 GLM + log link，不從轉換欄反推",
    "duan_smearing": "已記載 smearing factor",
    "rank_only": "只用於排序／分群，不回原尺度",
    "median_only": "只報中位數，報告已寫明口徑",
    "descriptive_only": "只用於 EDA／描述，不進預測模型",
}


def scan_spec(spec: dict) -> tuple[list[str], list[str], list[str]]:
    """掃一份 transform_spec.json，回 (errors, warnings, infos)。"""
    errors: list[str] = []
    warns: list[str] = []
    infos: list[str] = []

    cols = spec.get("columns") or {}
    if not cols:
        warns.append("transform_spec.json 沒有 columns 區塊 — M3 還沒產出任何轉換規格，"
                     "或檔案結構不符 §4.4")
        return errors, warns, infos

    fit_on = str(spec.get("fit_on", "")).lower()
    for col, ent in cols.items():
        if not isinstance(ent, dict):
            errors.append(f"{col} 的 entry 不是物件 — 對照 §4.4 的格式重寫")
            continue
        raw = str(ent.get("method", "none"))
        method = resolve_method(raw)
        purpose = str(ent.get("purpose", "") or "")
        route = str(ent.get("retransform", "") or "")

        if method in _MODEL_ROUTES:
            infos.append(f"{col}：{raw} — {_MODEL_ROUTES[method]}，沒有反轉換偏誤")
            continue
        if method in _BIN_ROUTES or method == "none":
            infos.append(f"{col}：{raw} — 不產生需要反轉換的欄位")
            continue

        m = METHODS.get(method)
        if m is None:
            errors.append(f"{col}：不認得的 method='{raw}' — 見 §4.2 的後綴與方法對照表")
            continue
        if m.bias == "linear":
            if method == "zscore":
                warns.append(
                    f"{col}：標準化不該進 transform_spec.json（§五）— "
                    f"它是各方法族自己的第一步，參數放 模型輸出/scaler.json 或 Pipeline"
                )
            else:
                infos.append(f"{col}：{raw} — 線性轉換，沒有 Jensen 偏誤")
            continue

        # 需要判斷有沒有交代反轉換路線
        cleared = route in _OK_ROUTES or purpose in ("descriptive_only", "ranking")
        tag = "log 類（exp 反轉，必然低估）" if m.bias == "log" else "非線性（沒有乘法捷徑）"
        if cleared:
            why = _OK_ROUTES.get(route) or "purpose 已標記僅供描述／排序"
            if route == "glm_log":
                tail = "金額一律從 GLM 的 predict() 取，不可以從這一欄反推（§2.3 ①）"
            elif route == "duan_smearing":
                tail = ("報告要附 smearing factor 的值與 fit_on，"
                        "並確認殘差同質；異質變異要分組（§2.3 ②）")
            else:
                tail = "報告若引用它的平均，必須寫明是幾何平均／中位數（§2.3 表）"
            warns.append(f"{col}：{raw}，{tag}，已標 {route or purpose} — {why}。{tail}")
        else:
            errors.append(
                f"{col}：{raw}，{tag}，但 entry 沒有 retransform 也沒有 purpose — "
                f"這一欄若被拿去出金額就是 §二 的低估。"
                f"該怎麼辦：補上 retransform 為 {sorted(_OK_ROUTES)} 之一"
            )

        if m.needs:
            miss = [k for k in m.needs if k not in (ent.get("params") or {})]
            if miss:
                errors.append(
                    f"{col}：params 缺 {miss} — 反轉換算不出來。"
                    f"該怎麼辦：把當初 fit 在訓練集的參數值補進去（§4.1，不可重估）"
                )

    if fit_on == "full":
        bad = [c for c, e in cols.items()
               if isinstance(e, dict)
               and str(e.get("purpose", "")) != "descriptive_only"
               and resolve_method(str(e.get("method", "none"))) in METHODS
               and METHODS[resolve_method(str(e.get("method", "none")))].bias != "linear"]
        if bad:
            errors.append(
                f"fit_on='full' 但這些欄不是 descriptive_only：{bad} — "
                f"轉換參數用了測試集資訊就是目標洩漏（§4.1、18-G4）。"
                f"該怎麼辦：改成 fit_on='train' 並用 train_row_filter 重跑"
            )
    return errors, warns, infos


def cmd_scan(project: str) -> tuple[list[str], list[str], list[str]]:
    p = project_dir(project, create=False)
    spec_path = p.features / "transform_spec.json"
    print(f"專案：{project}")
    print(f"規格檔：{spec_path}")
    print("=" * 66)
    if not spec_path.exists():
        return ([], [f"找不到 {spec_path} — M3 還沒跑，或專案代號打錯。"
                     f"該怎麼辦：先跑 M3 前處理產出規格檔，再回來跑這支放行檢查"], [])
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return ([f"transform_spec.json 解析失敗（{e}） — "
                 f"該怎麼辦：檢查 JSON 語法（§4.4 的範例用了 jsonc 註解，實際檔案不能有註解）"],
                [], [])
    return scan_spec(spec)


# ══════════════════════════════════════════════════════════════════
# 六、CLI ②：--self-test 自我測試
# ══════════════════════════════════════════════════════════════════

def _line(title: str) -> None:
    print()
    print(title)
    print("-" * 66)


def _w(s: str) -> int:
    """字串在等寬主控台上佔幾格（中文兩格）。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _lpad(s: str, n: int) -> str:
    return " " * max(0, n - _w(s)) + s


def _rpad(s: str, n: int) -> str:
    return s + " " * max(0, n - _w(s))


def _three_numbers(truth: float, naive: float, duan: float, unit: str = "元") -> None:
    print("    " + _rpad("口徑", 26) + _lpad("數值", 14) + _lpad("相對真實算術平均", 20))
    print("    " + _rpad("真實算術平均 E[Y]", 26) + f"{truth:>14,.2f}" + _lpad("—", 20))
    print("    " + _rpad("直接 exp（幾何平均）", 26) + f"{naive:>14,.2f}"
          + f"{naive / truth - 1:>+20.1%}")
    print("    " + _rpad("Duan smearing", 26) + f"{duan:>14,.2f}"
          + f"{duan / truth - 1:>+20.1%}")
    print(f"    （單位：{unit}）")


def demo(errors: list[str], warns: list[str], infos: list[str]) -> None:
    try:
        import statsmodels.api as sm  # noqa: PLC0415
    except ImportError:
        errors.append("statsmodels 未安裝 — 該怎麼辦：pip install -r requirements.txt（第 2 層）")
        return

    rng = np.random.default_rng(20260727)

    # ── A. 合成右偏資料：三個數字並排 ────────────────────────────
    _line("A. 合成右偏資料（lognormal，σ = 1.43 取自 §2.2 由 1909.73/688 回推）")
    # n 取 5 萬不是為了好看：σ = 1.43 的 lognormal 尾巴很重，
    # 樣本算術平均自己的變異係數就是 sqrt(exp(σ²)−1)/√n，n = 5,000 時約 3.7%，
    # 拿它當「真值」去驗 5% 門檻等於在驗抽樣雜訊。n = 5 萬時降到 1.2%〔實作判斷〕。
    from scipy import stats  # noqa: PLC0415
    n = 50_000
    x = rng.normal(0.0, 1.0, n)
    sigma = 1.43
    log_y = 6.53 + 0.80 * x + rng.normal(0.0, sigma, n)
    y = np.exp(log_y)
    X = sm.add_constant(x)
    m = sm.OLS(np.log(y), X).fit()

    truth = float(y.mean())
    naive = float(np.exp(m.fittedvalues).mean())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RetransformWarning)
        duan = float(duan_smearing(m, X, groups=None).mean())

    theory = float(np.exp(6.53 + 0.5 * 0.80 ** 2 + sigma ** 2 / 2))
    print(f"    n = {n:,}｜偏度 = {float(stats.skew(y)):.2f}｜R² = {m.rsquared:.4f}"
          f"｜母體 E[Y] = {theory:,.2f}")
    print(f"    R² 高不高跟偏誤沒有關係：低估倍數是 exp(σ̂²/2)，只由殘差變異決定（§2.1）")
    _three_numbers(truth, naive, duan)
    sf = smearing_factors(m)
    print(f"    smearing factor = {sf['pooled']:.4f}"
          f"｜exp(σ̂²/2) = {sf['lognormal_factor']:.4f}"
          f"（殘差近似常態時兩者會收斂，§2.3 ②）")

    if naive >= truth:
        errors.append(f"A：直接 exp 沒有低估（{naive:,.2f} ≥ {truth:,.2f}）— §二 的論述在這組資料上不成立，回頭查")
    else:
        infos.append(f"A：直接 exp 低估 {1 - naive / truth:.1%}，方向與 §二 一致")
    if abs(duan / truth - 1) < 0.05:
        infos.append(f"A：Duan smearing 後偏差 {duan / truth - 1:+.2%}，通過 §二 的 5% 硬檢查")
    else:
        errors.append(f"A：Duan smearing 後偏差 {duan / truth - 1:+.2%} ≥ 5% — 修正無效，回頭查")

    # ── B. 課程資料集實跑 ────────────────────────────────────────
    _line("B. 課程資料集實跑（信用卡交易金額，已知 n = 7,764、算術平均 1,909.73）")
    ar = archive_root()
    fp = (ar / "local" / "資料集剖析" / "samples"
          / "ntu_creditcard__transactions.parquet") if ar else None
    if not fp or not fp.exists():
        warns.append("找不到素材庫的樣本檔 — 跳過真實資料驗證。"
                     "該怎麼辦：確認 00_source_archive 在 repo 內，或用 config.yml 指定 素材庫")
    else:
        import pandas as pd  # noqa: PLC0415
        df = pd.read_parquet(fp)
        amt = df["刷卡金額"].astype(float).to_numpy()
        cat = df["刷卡產品產業分類"].astype(str)
        print(f"    來源：{fp.name}｜n = {len(amt):,}")

        # B1：只有截距（等同「報一個平均數」這件事本身）
        X0 = np.ones((len(amt), 1))
        m0 = sm.OLS(np.log(amt), X0).fit()
        truth0 = float(amt.mean())
        naive0 = float(np.exp(m0.fittedvalues).mean())
        duan0 = float(duan_smearing(m0, X0, groups=None).mean())
        print("    B1 只有截距（就是「把 log 平均 exp 回去報平均客單價」）：")
        _three_numbers(truth0, naive0, duan0)
        print(f"    （§2.2 用 lognormal 近似把幾何平均寫成中位數 688；"
              f"實際 exp(mean(log)) = {naive0:,.2f}，比 688 更低，低估更嚴重）")

        # B2：加入產業分類當解釋變數
        D = pd.get_dummies(cat, drop_first=True).astype(float).to_numpy()
        X1 = sm.add_constant(D)
        m1 = sm.OLS(np.log(amt), X1).fit()
        naive1 = float(np.exp(m1.fittedvalues).mean())
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RetransformWarning)
            duan1 = float(duan_smearing(m1, X1).mean())
            switched = [str(w.message)[:60] for w in caught]
        print(f"    B2 金額 ~ 刷卡產品產業分類（{D.shape[1] + 1} 個係數，R² = {m1.rsquared:.4f}）：")
        _three_numbers(truth0, naive1, duan1)
        if switched:
            print(f"    （groups='auto' 自動改分組：{switched[0]}…）")

        rep = check_retransform_risk(m1)
        print("    check_retransform_risk(m1)：")
        rep.print_report()

        if naive0 < truth0 and naive1 < truth0:
            infos.append(f"B：真實資料上直接 exp 也低估（B1 {1 - naive0 / truth0:.1%}、"
                         f"B2 {1 - naive1 / truth0:.1%}）")
        else:
            errors.append("B：真實資料上直接 exp 沒有低估 — 回頭查")
        if abs(duan0 / truth0 - 1) < 1e-9:
            infos.append("B1：只有截距時 smearing 精確還原算術平均（數學恆等，可當回歸測試）")
        else:
            errors.append(f"B1：smearing 沒有還原算術平均，差 {duan0 - truth0:.6f}")
        if abs(duan1 / truth0 - 1) < 0.05:
            infos.append(f"B2：Duan smearing 後偏差 {duan1 / truth0 - 1:+.2%}，通過 5% 硬檢查")
        else:
            errors.append(f"B2：Duan smearing 後偏差 {duan1 / truth0 - 1:+.2%} ≥ 5%")
        if rep.exit_code == 0:
            errors.append("B2：check_retransform_risk 沒抓到 log-OLS 的反轉換風險 — 偵測器失效")
        else:
            infos.append("B2：check_retransform_risk 正確擋下 log-OLS 直接 exp")

    # ── C. 異質變異：單一 factor 不夠 ────────────────────────────
    _line("C. 異質變異時，單一 smearing factor 會把低估搬到某幾段（§2.3 ②）")
    n2 = 6000
    x2 = rng.uniform(-2, 2, n2)
    sd2 = 0.4 + 0.9 * (x2 + 2) / 4 * 2          # 殘差 sd 隨 x 上升
    y2 = np.exp(6.0 + 0.9 * x2 + rng.normal(0.0, 1.0, n2) * sd2)
    X2 = sm.add_constant(x2)
    m2 = sm.OLS(np.log(y2), X2).fit()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RetransformWarning)
        pooled = duan_smearing(m2, X2, groups=None)
        grouped = duan_smearing(m2, X2, groups=_N_SMEAR_GROUPS)
    q = np.quantile(m2.fittedvalues, [.2, .4, .6, .8])
    g = np.digitize(m2.fittedvalues, q)
    print(f"    Breusch-Pagan p = {hetero_pvalue(m2):.3g}（< 0.05 → 異質變異）")
    print("    " + _rpad("預測值分位組", 14) + _lpad("真實平均", 12)
          + _lpad("單一 factor", 22) + _lpad("分組 factor", 22))
    worst_pooled = 0.0
    worst_group = 0.0
    for k in range(_N_SMEAR_GROUPS):
        msk = g == k
        t, pl, gr = y2[msk].mean(), pooled[msk].mean(), grouped[msk].mean()
        worst_pooled = max(worst_pooled, abs(pl / t - 1))
        worst_group = max(worst_group, abs(gr / t - 1))
        print("    " + _rpad(f"第 {k + 1} 組", 14) + f"{t:>12,.0f}"
              + f"{pl:>14,.0f}{pl / t - 1:>+8.1%}"
              + f"{gr:>14,.0f}{gr / t - 1:>+8.1%}")
    print(f"    整體：單一 factor {pooled.mean() / y2.mean() - 1:+.2%}、"
          f"分組 {grouped.mean() / y2.mean() - 1:+.2%}（整體都對得上，錯在分段）")
    if worst_group < worst_pooled:
        infos.append(f"C：分組 smearing 把最差分段誤差從 {worst_pooled:.1%} 降到 {worst_group:.1%}")
    else:
        warns.append(f"C：分組沒有改善分段誤差（單一 {worst_pooled:.1%}、分組 {worst_group:.1%}）— "
                     f"這組模擬資料的異質性可能不夠強，不代表方法錯")

    # ── D. safe_inverse 的擋與放 ────────────────────────────────
    _line("D. safe_inverse：log 類沒有修正依據就擋下")
    z = np.asarray(m.fittedvalues, dtype=float)
    blocked = False
    try:
        safe_inverse(z, {"method": "log"}, target="mean")
    except RetransformBiasError as e:
        blocked = True
        print("    safe_inverse(z, {'method':'log'}, target='mean') →")
        for ln in str(e).splitlines():
            print(f"      {ln}")
    if blocked:
        infos.append("D：log 類無 smearing 時正確擋下")
    else:
        errors.append("D：log 類無 smearing 竟然放行 — 擋不住就沒意義")

    s = smearing_factors(m)["pooled"]
    fixed = safe_inverse(z, {"method": "log"}, target="mean", smearing_factor=s)
    print(f"    給 smearing_factor={s:.4f} 後放行，平均 = {fixed.mean():,.2f}"
          f"（真實 {truth:,.2f}）")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RetransformWarning)
        med = safe_inverse(z, {"method": "log"}, target="median")
        got_warn = any(issubclass(w.category, RetransformWarning) for w in caught)
    print(f"    target='median' 放行，平均 = {med.mean():,.2f}"
          f"，並發警告：{'有' if got_warn else '沒有'}")
    if got_warn:
        infos.append("D：target='median' 有發「必須寫明是中位數」的警告")
    else:
        errors.append("D：target='median' 沒發警告 — 報告會把幾何平均當平均寫出去")

    # Yeo-Johnson 來回一致性（反轉換函式本身寫對沒有）
    try:
        from sklearn.preprocessing import PowerTransformer  # noqa: PLC0415
        raw = np.concatenate([rng.normal(-500, 300, 400), rng.gamma(2, 900, 600)])
        pt = PowerTransformer(method="yeo-johnson", standardize=False).fit(raw.reshape(-1, 1))
        lam = float(pt.lambdas_[0])
        zz = pt.transform(raw.reshape(-1, 1)).ravel()
        back = safe_inverse(zz, {"method": "yeo_johnson", "params": {"lambda": lam}}, target="rank")
        err = float(np.max(np.abs(back - raw)))
        print(f"    Yeo-Johnson 來回誤差（λ={lam:.4f}，含負值 {int((raw < 0).sum())} 筆）：{err:.3e}")
        if err < 1e-6:
            infos.append(f"D：Yeo-Johnson 反轉換與 sklearn 來回一致（最大誤差 {err:.1e}）")
        else:
            errors.append(f"D：Yeo-Johnson 反轉換與 sklearn 對不上（最大誤差 {err:.3e}）")
        try:
            safe_inverse(zz, {"method": "yeo_johnson", "params": {"lambda": lam}}, target="mean")
            errors.append("D：Yeo-Johnson 沒給殘差竟然放行 target='mean'")
        except RetransformBiasError:
            infos.append("D：非 log 類（Yeo-Johnson）沒給殘差時正確擋下 target='mean'")
    except ImportError:
        warns.append("sklearn 未安裝 — 跳過 Yeo-Johnson 來回驗證")

    # ── D2. 每一條反轉換公式的來回一致性 ────────────────────────
    _line("D2. 每個方法的反轉換公式來回誤差（forward 自己算，inverse 走 safe_inverse）")
    pos = rng.gamma(2.0, 800.0, 500) + 1.0          # 全正金額
    anyv = np.concatenate([-pos[:150], pos[150:]])  # 含負值
    prob = rng.beta(2.0, 5.0, 500)                  # (0,1) 比率
    cases: list[tuple[str, dict, np.ndarray, np.ndarray]] = [
        ("log", {}, pos, np.log(pos)),
        ("log_c", {"c": 344.0}, pos, np.log(pos + 344.0)),
        ("arcsinh", {"theta": 688.0}, anyv, np.arcsinh(anyv / 688.0)),
        ("box_cox", {"lambda": 0.3}, pos, (np.power(pos, 0.3) - 1) / 0.3),
        ("logit", {}, prob, np.log(prob / (1 - prob))),
        ("arcsine_sqrt", {}, prob, np.arcsin(np.sqrt(prob))),
        ("square", {}, pos, np.square(pos)),
        ("cube", {}, anyv, np.power(anyv, 3.0)),
        ("zscore", {"center": 1500.0, "scale": 900.0}, anyv, (anyv - 1500.0) / 900.0),
    ]
    worst_name, worst_err = "", 0.0
    for name, prm, orig, fwd in cases:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RetransformWarning)
            back = safe_inverse(fwd, {"method": name, "params": prm}, target="rank")
        rel = float(np.max(np.abs(back - orig) / np.maximum(np.abs(orig), 1e-9)))
        print(f"    {_rpad(name, 16)}最大相對誤差 {rel:.3e}")
        if rel > worst_err:
            worst_name, worst_err = name, rel
    if worst_err < 1e-9:
        infos.append(f"D2：9 個反轉換公式全部來回一致（最差 {worst_name} {worst_err:.1e}）")
    else:
        errors.append(f"D2：{worst_name} 的反轉換公式來回對不上（相對誤差 {worst_err:.3e}）— 公式寫錯")

    # ── E. GLM + log link 不該被誤判 ────────────────────────────
    _line("E. Gamma GLM + log link：不能被判成有偏誤（否則會被多乘一次）")
    gm = sm.GLM(y, X, family=sm.families.Gamma(sm.families.links.Log())).fit()
    rep_g = check_retransform_risk(gm)
    rep_g.print_report()
    pred_g = float(gm.predict(X).mean())
    print(f"    GLM predict() 平均 = {pred_g:,.2f}（真實 {truth:,.2f}，"
          f"{pred_g / truth - 1:+.2%}）")
    if rep_g.exit_code == 0:
        infos.append("E：GLM + log link 被正確判為無偏誤")
    else:
        errors.append("E：GLM + log link 被誤判成有風險 — 會誘導使用者多乘一次 smearing")

    # 非 statsmodels 的物件不可以被靜默判成「沒問題」
    class _NotAModel:
        pass

    rep_x = check_retransform_risk(_NotAModel())
    print(f"    傳一個非 statsmodels 物件進去 → 退出碼 {rep_x.exit_code}（1 或 2 才對）")
    if rep_x.exit_code == 0:
        errors.append("E：非 statsmodels 物件被靜默判為無風險 — sklearn/XGBoost 配在 log(y) 上會漏抓")
    else:
        infos.append("E：非 statsmodels 物件正確回報「無法判定」而不是「沒問題」")


# ══════════════════════════════════════════════════════════════════
# 七、main
# ══════════════════════════════════════════════════════════════════

def main() -> int:
    ap = GateArgumentParser(
        description="反轉換工具：擋住 exp(E[log Y]) 被當成 E[Y] 報出去（06 §二）")
    # --self-test 不寫任何檔案，允許省略專案代號（自我測試旗標全庫統一，00 §八）
    ap.add_argument("project", metavar="專案代號", nargs="?",
                    help="專案代號，路徑由 paths.project_dir 解析。"
                         "--self-test 時可省略")
    ap.add_argument("--self-test", action="store_true",
                    help="跑內建自我測試：三個數字並排證明直接 exp 低估")
    args = ap.parse_args()

    print("=" * 66)
    print("反轉換偏誤檢查 — E[Y] ≠ exp(E[log Y])")
    print("=" * 66)

    errors: list[str] = []
    warns: list[str] = []
    infos: list[str] = []

    if args.self_test:
        print(f"（--self-test 自我測試；專案代號 {args.project or '(未給)'} "
              f"僅作紀錄，不寫入任何檔案）")
        try:
            demo(errors, warns, infos)
        except Exception as e:  # noqa: BLE001
            errors.append(f"自我測試中斷（{type(e).__name__}: {e}）— "
                          f"該怎麼辦：先跑 python setup_check.py 確認套件與素材庫")
    else:
        if not args.project:
            ap.error("要指定專案代號（只有 --self-test 可以省略）")
        e, w, i = cmd_scan(args.project)
        errors += e
        warns += w
        infos += i

    print()
    print("=" * 66)
    if infos:
        print("通過")
        print("-" * 66)
        for m in infos:
            print(f"  ✅ {m}")
    if warns:
        print("\n⚠ 可以往下走，但報告要交代")
        print("-" * 66)
        for m in warns:
            print(f"  ⚠ {m}")
    if errors:
        print("\n⛔ 擋下，不准交付")
        print("-" * 66)
        for m in errors:
            print(f"  ⛔ {m}")

    print()
    print("=" * 66)
    if errors:
        print(f"結果：{len(errors)} 個 error、{len(warns)} 個 warning → 擋下")
        return EX_ERROR
    if warns:
        print(f"結果：{len(warns)} 個 warning → 放行，但報告必須寫明口徑")
        return EX_WARN
    print(f"結果：全部通過（{len(infos)} 項）")
    return EX_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ retransform.py 本身失敗：{type(exc).__name__}: {exc}",
              file=sys.stderr)
        print(f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
