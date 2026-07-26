"""M7 迴歸建模：可直接複製使用的程式範本。

規格書是 references/08_迴歸建模.md，本檔是它的可執行版本。
兩者不一致時**以 08 為準**，並立刻回頭修這個檔（不要讓兩邊分岔）。

環境：Python 3.14.1 主環境。statsmodels 0.14.6 / scipy 1.16.3 / numpy 2.3.5 / pandas 2.3.3
本檔的 `anova3` / `plot_lm` / `vif_table` / `emmeans` 正本在 scripts/stats_utils.py，
這裡只 import，**不要在這裡再寫一份**（08 §十 維護條款第 2 條）。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from scripts.stats_utils import anova3, emm_contrasts, emmeans, plot_lm, vif_table  # noqa: F401


# ---------------------------------------------------------------------------
# 08 §一：選模型族前的機械化前置。不要憑印象選族。
# ---------------------------------------------------------------------------
def y_profile(y: pd.Series) -> dict:
    """一次算出所有「該用哪個模型族」需要的判斷指標。

    判讀（門檻出處見 08 §一與 ref 05 §1.7 / §1.9）：
      zero_ratio > 0.30            → 走 08 §1.2，先判斷零的來源
      is_integer 且 var_mean >> 1  → Negative Binomial，不是 Poisson
      非整數且 zero_ratio > 0      → Tweedie
      skew > 1                     → 不要用 OLS
      n_distinct <= 2              → 二元；<= 10 且有序 → Ordinal
    """
    y = y.dropna()
    return {
        "n": len(y),
        "min": y.min(),
        "zero_ratio": float((y == 0).mean()),
        "is_integer": bool((y % 1 == 0).all()),
        "skew": float(y.skew()),
        "mean": float(y.mean()),
        "var": float(y.var(ddof=1)),
        "var_mean": float(y.var(ddof=1) / y.mean()) if y.mean() else np.nan,
        "n_distinct": int(y.nunique()),
    }


# ---------------------------------------------------------------------------
# 08 §四 Step 2-4 + Step 7：影響點旗標與敏感度分析
# ---------------------------------------------------------------------------
def influence_flags(m) -> tuple[pd.DataFrame, dict]:
    """回傳 (每列的診斷量與旗標, 門檻字典)。門檻出處：MBA5045 0923 §4.5-4.7。

    教材原則：殘差大 != 影響一定大；槓桿高 != 影響一定大。
    看到高槓桿就刪是新手動作 —— HOMES4a 實測移除三個高槓桿點後 R^2 僅 0.6808 → 0.6757。
    """
    inf = m.get_influence()
    n, k = int(m.nobs), int(m.df_model)
    thr = {
        "outlier": 3.0,                 # |studentized residual| > 3，兩尾機率 < 0.002
        "lev3": 3 * (k + 1) / n,        # 需進一步檢查
        "lev2": 2 * (k + 1) / n,        # 低於此代表該點很孤立，也要檢查
        "cook_hi": 1.0,                 # 強警訊（主判準）
        "cook_warn": 0.5,               # 留意（主判準）
        "cook_4n": 4 / n,               # 0930 實戰腳本的業界常用線，畫但不當主判準
    }
    d = pd.DataFrame(
        {
            "rstandard": inf.resid_studentized_internal,
            "leverage": inf.hat_matrix_diag,
            "cooks_d": inf.cooks_distance[0],
        },
        index=m.model.data.row_labels,
    )
    d["is_outlier"] = d.rstandard.abs() > thr["outlier"]
    d["is_leverage"] = d.leverage > thr["lev3"]
    d["is_isolated"] = d.leverage < thr["lev2"]
    d["is_influential"] = d.cooks_d >= thr["cook_warn"]
    return d, thr


def sensitivity(formula: str, data: pd.DataFrame, drop_idx) -> pd.DataFrame:
    """08 §四 Step 7：移除可疑點重估，看係數是否實質改變。

    「實質改變」教材未給門檻，本 skill 操作化為「係數變動 > 1 個原標準誤」
    【推導，待驗證】。結果要進報告 —— 就是給主管的那句
    「就算把異常客戶拿掉，結論還是一樣」。
    """
    m0 = smf.ols(formula, data, missing="drop").fit()
    m1 = smf.ols(formula, data.drop(index=drop_idx), missing="drop").fit()
    out = pd.DataFrame(
        {
            "coef_full": m0.params,
            "coef_drop": m1.params,
            "delta_in_se": (m1.params - m0.params) / m0.bse,
            "p_full": m0.pvalues,
            "p_drop": m1.pvalues,
        }
    )
    out["material_change"] = out.delta_in_se.abs() > 1.0
    return out


# ---------------------------------------------------------------------------
# 08 §七：變數選擇。R 的 step() 無 Python 內建。
# ---------------------------------------------------------------------------
def backward_aic(y: str, xs: list[str], data: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    """依 AIC 逐步剔除。回傳 (最終 formula, 逐步軌跡)。

    軌跡**必須留檔**：選變數後再看 p-value 會有「選後 p-value 偏樂觀」的問題
    （MBA5045 1118 §5.4 D7），讀者要看得到剔除順序才能自己打折。

    收尾一定要再跑一次 Partial F 對照（m_full.compare_f_test(m_red)）。
    兩者結論不一致時**以 Partial F 為準** —— 它有明確的 H0，AIC 沒有。
    """
    cur = list(xs)
    trace: list[dict] = []
    best = smf.ols(f"{y} ~ " + " + ".join(cur), data, missing="drop").fit()
    while len(cur) > 1:
        cands = {
            x: smf.ols(f"{y} ~ " + " + ".join([c for c in cur if c != x]), data, missing="drop").fit()
            for x in cur
        }
        drop, mdl = min(cands.items(), key=lambda kv: kv[1].aic)
        trace.append(
            {"dropped": drop, "aic_before": best.aic, "aic_after": mdl.aic, "delta_aic": mdl.aic - best.aic}
        )
        if mdl.aic >= best.aic:
            break
        cur.remove(drop)
        best = mdl
    return f"{y} ~ " + " + ".join(cur), pd.DataFrame(trace)


# ---------------------------------------------------------------------------
# 08 §八：分群後建迴歸。預設走 (B)，不要用 (A) 的兩個係數大小講故事。
# ---------------------------------------------------------------------------
def segment_slope_test(y: str, x: str, seg: str, data: pd.DataFrame, ref: str):
    """檢定「不同客群對 x 的敏感度是否真的不同」。

    ref = 參考組，選**人數最多的群或現行主打客群**，不是字母序第一個
    （基準組選錯會讓所有群看起來都沒差異，MBA5045 0923 §8.7）。

    p <  alpha → 各群斜率確實不同，主效果解讀必須條件化
    p >= alpha → 沒有證據支持「各群敏感度不同」。用平行斜率模型，並在報告寫明這句
    """
    c = f"C({seg}, Treatment(reference='{ref}'))"
    m_par = smf.ols(f"{y} ~ {x} + {c}", data, missing="drop").fit()   # 平行斜率
    m_int = smf.ols(f"{y} ~ {x} * {c}", data, missing="drop").fit()   # 各群斜率不同
    F, p, ddf = m_int.compare_f_test(m_par)                          # 完整在前！與 R 相反
    return {"F": F, "p": p, "df_diff": ddf, "m_parallel": m_par, "m_interact": m_int}


# ---------------------------------------------------------------------------
# 08 §九：降級。穩健標準誤三種寫法。
# ---------------------------------------------------------------------------
def robust_refit(formula: str, data: pd.DataFrame, kind: str, groups=None):
    """kind: 'hc3'（異質變異）/ 'cluster'（同顧客多筆）/ 'hac'（時間自相關）。

    保住：係數解讀、效果量、單位效果。
    放棄：找到正確的函數形式；預測區間仍不可信。
    降級要記進 _log/degradation_log.md（00 §1.6），並在該章小結複述前四欄。
    """
    m = smf.ols(formula, data, missing="drop")
    if kind == "hc3":
        return m.fit(cov_type="HC3")
    if kind == "cluster":
        return m.fit(cov_type="cluster", cov_kwds={"groups": groups})
    if kind == "hac":
        return m.fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    raise ValueError(f"unknown kind: {kind}")


# ---------------------------------------------------------------------------
# 08 §一：非高斯族的呼叫式速查（標 ⚠ 者本機未實測，用之前先自己跑一次）
# ---------------------------------------------------------------------------
FAMILY_CALLS = {
    "gamma_log":  "sm.GLM(y, X, family=sm.families.Gamma(sm.families.links.Log())).fit()",
    "binomial":   "smf.glm(f, df, family=sm.families.Binomial()).fit()",
    "poisson":    "smf.glm(f, df, family=sm.families.Poisson()).fit()   # 只在 psi_hat ~= 1 時",
    "negbin":     "sm.NegativeBinomialP(y, X, p=2).fit()                # ⚠ 未實測。預設族",
    "zinb":       "sm.ZeroInflatedNegativeBinomialP(y, X, exog_infl=Z).fit()   # ⚠ 未實測",
    "hurdle":     "from statsmodels.discrete.truncated_model import HurdleCountModel  # ⚠ 未實測",
    "tweedie":    "sm.GLM(y, X, family=sm.families.Tweedie(sm.families.links.Log(), var_power=1.5)).fit()",
    "ordinal":    "from statsmodels.miscmodels.ordinal_model import OrderedModel      # ⚠ 未逐項實測",
    "mixed":      "smf.mixedlm(f, df, groups=df['cust_id']).fit()       # ⚠ 隨機斜率支援很差",
    "cox":        "from lifelines import CoxPHFitter                    # ⚠ 未實測",
}


def psi_hat(glm_result) -> float:
    """過度離散係數。>1 代表 Poisson/Binomial 的 SE 被低估 sqrt(psi) 倍。

    順序鐵則不可顛倒（02_logistic_glm_categorical §3.8）：
      (1) 先查漏變數 / 非線性 → (2) 再查是否少數幾筆殘差撐大整體
      → (3) 都排除後才歸因 overdispersion
    """
    return float(glm_result.deviance / glm_result.df_resid)
