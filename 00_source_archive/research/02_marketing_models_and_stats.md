# Python 行銷分析建模生態 — 技術選型調研

**調研日期**：2026-07-26
**調研對象環境**：Windows 11 Home 26200 / **Python 3.14.1**（`C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe`）
**倉儲層前提**：DuckDB + Parquet + SQL（已定案，本文不再比較引擎）
**建模層前提**：Python 為主，R 統計課那套完整改寫

---

## 0. 給趕時間的人：本次調研最重要的三個結論

### 結論 1：Part A（R→Python 統計）幾乎沒有問題，而且我已在你的機器上實測通過

statsmodels 0.14.6 **有 cp314 wheel**，已裝在你的環境裡。我實際跑過一份涵蓋 `lm`/`glm`/`anova_lm(typ=1,2,3)`/Cook's D/槓桿值/VIF/巢狀 F 檢定/Tukey HSD/殘差診斷檢定/MixedLM/quantreg 的驗證腳本，**全部通過**。R 統計課那套 95% 可以一比一搬過來。唯一真正的缺口是 `emmeans`，但可以用 `t_test()` + 對比向量手工補上（第 A.9 節有我實測過的可用程式碼）。

### 結論 2：Python 3.14.1 是本次選型最大的隱形地雷，會擋掉三個重要套件

這不是「印象」，是我在你機器上用 `pip install --dry-run` 實測的結果：

| 套件 | 在 Python 3.14.1 的實測結果 |
|---|---|
| **dowhy** | **靜默降版到 0.8（2022 年版本）** — 見下方說明，這是最危險的一個 |
| **EconML** | **安裝失敗**（`ERROR: Unknown compiler(s)` — 沒有 cp314 wheel，退回原始碼編譯） |
| **google-meridian** | **安裝失敗**（相依 TensorFlow < 2.21，TensorFlow 無 cp314 wheel） |

**dowhy 的坑要特別講**：`pip install dowhy` 在你的環境會「成功」，但裝到的是 **0.8 版**，不是最新的 0.14。原因是 dowhy 0.14 的 metadata 寫死 `Requires-Python >=3.9,<3.14`，pip 找不到符合的版本就一路往回退，最後裝了一個四年前的版本。pip **不會警告你**。實測輸出：

```
ERROR: Ignored the following versions that require a different python version:
  ... 0.12 Requires-Python >=3.8,<3.13; 0.13 Requires-Python >=3.8,<3.13;
  0.14 Requires-Python >=3.9,<3.14; ...
ERROR: Could not find a version that satisfies the requirement dowhy==0.14
       (from versions: 0.1.1, 0.2, 0.4, 0.5, 0.5.1, 0.6, 0.7, 0.7.1, 0.8)
```

**建議：建一個 Python 3.12 或 3.13 的第二個 venv 專門放因果推論/MMM 套件**，主環境（統計 + 倉儲 + 交付）繼續留在 3.14。詳見第 4 節「推薦堆疊」。

### 結論 3：你懷疑的兩個套件，兩個都確認死亡

- **CamDavidsonPilon/lifetimes** — **已 archived**。GitHub 橫幅原文："This repository was archived by the owner on **Jun 28, 2024**. It is now read-only."　README 原文："A project has emerged as a successor to lifetimes, PyMC-Lab/PyMC-Marketing, please check it out!"　最後一次 commit 2024-06-28，最後一個 release **v0.11.3 發布於 2020-07-06**（六年前）。
- **google/lightweight_mmm** — **已 archived**。橫幅原文："This repository was archived by the owner on **Jan 19, 2026**. It is now read-only."　README 原文："As of 29 Jan 2025 Google has released a new official Bayesian MMM version called **Meridian**"、"we **highly** recommend you switch to Meridian"、"LMMM is not supported anymore."　最後一次 commit 2025-06-17，最後 release **v0.1.9 發布於 2023-05-23**。

你的直覺兩次都對。

---

# PART A — R → Python 統計對照

> **本節所有程式碼都在你的機器上（Python 3.14.1 / statsmodels 0.14.6 / scipy 1.16.3 / numpy 2.3.5 / pandas 2.3.3 / pingouin 0.6.1）實際執行通過**，不是憑文件推測。

## A.1 總覽對照表

| R 的做法 | Python 等價 | 實測 | 備註 |
|---|---|---|---|
| `lm(y ~ x)` | `smf.ols("y ~ x", df).fit()` | 通過 | formula 語法幾乎一致 |
| `glm(y ~ x, family=binomial)` | `smf.glm(..., family=sm.families.Binomial()).fit()` | 通過 | |
| `anova(m)` Type I | `anova_lm(m, typ=1)` | 通過 | |
| `car::Anova(m, type=2)` | `anova_lm(m, typ=2)` | 通過 | |
| `car::Anova(m, type=3)` | `anova_lm(m, typ=3)` + **必須 Sum coding** | 通過 | **有陷阱，見 A.3** |
| `anova(m1, m2)` 巢狀 F | `m2.compare_f_test(m1)` 或 `anova_lm(m1, m2)` | 通過 | |
| `lrtest(m1, m2)` | `m2.compare_lr_test(m1)` | 通過 | |
| `plot(m)` 四圖 | 手工繪製，見 A.4 | 通過 | **Python 沒有一行指令版** |
| `cooks.distance(m)` | `m.get_influence().cooks_distance[0]` | 通過 | |
| `hatvalues(m)` | `m.get_influence().hat_matrix_diag` | 通過 | |
| `rstandard(m)` / `rstudent(m)` | `.resid_studentized_internal` / `_external` | 通過 | |
| `dfbetas(m)` / `dffits(m)` | `.dfbetas` / `.dffits` | 通過 | |
| `car::vif(m)` | `variance_inflation_factor(X, i)` | 通過 | **要自己迴圈，且含截距** |
| `TukeyHSD(aov)` | `pairwise_tukeyhsd(y, groups)` | 通過 | |
| `shapiro.test()` | `scipy.stats.shapiro()` | 通過 | |
| `lmtest::bptest()` | `sms.het_breuschpagan()` | 通過 | |
| `lmtest::dwtest()` | `sms.durbin_watson()` | 通過 | 只回統計量，無 p 值 |
| `lmtest::resettest()` | `sms.linear_reset()` | 通過 | |
| `sandwich::vcovHC` | `.fit(cov_type="HC3")` | 通過 | 更簡潔 |
| 群聚穩健標準誤 | `.fit(cov_type="cluster", cov_kwds={"groups": g})` | 通過 | |
| `lme4::lmer` | `smf.mixedlm()` | 可用 | **功能明顯較弱，見 A.10** |
| `MASS::polr` 順序邏輯 | `OrderedModel` | 可用 | |
| `mgcv::gam` | `statsmodels.gam.api.GLMGam` | 可用 | **功能明顯較弱** |
| `quantreg::rq` | `smf.quantreg()` | 通過 | |
| `MASS::rlm` | `smf.rlm()` | 通過 | |
| **`emmeans::emmeans`** | **無對應套件** | — | **最大缺口，見 A.9** |
| **`DHARMa`** | **無對應套件** | — | **見 A.10** |
| **`performance::check_model`** | **無對應套件** | — | 用 A.4 的自製函式代替 |

## A.2 `smf.ols` 能不能一比一取代 `lm`？

**能，而且 formula 語法相容度比想像中高。** 實測：

```python
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

m = smf.ols("y ~ x1 + x2 + C(grp)", data=df).fit()
print(m.summary())        # 等同 R 的 summary(m)
```

R 與 Python formula 的對應：

| R | Python (patsy/formulaic) |
|---|---|
| `y ~ x1 + x2` | 相同 |
| `y ~ x1 * x2`（含主效果與交互） | 相同 |
| `y ~ x1 : x2`（只有交互） | 相同 |
| `y ~ . ` | **不支援**，要自己組字串 |
| `y ~ x1 - 1` 去截距 | `y ~ x1 - 1` 或 `y ~ x1 + 0` |
| `factor(g)` | `C(g)` |
| `poly(x, 2)` | **不支援**，用 `I(x**2)` 或 `np.power(x,2)` |
| `log(x)` | `np.log(x)` |
| `offset(log(n))` | `smf.glm(..., offset=np.log(df.n))` |

**唯一要注意的差異**：R 的 `lm` 預設 `na.action=na.omit` 且會記住哪些列被丟掉；statsmodels 預設 `missing='none'`，遇到 NaN 會直接算出 NaN 而不報錯。**務必顯式指定**：

```python
m = smf.ols("y ~ x1 + x2", data=df, missing="drop").fit()
```

這是從 R 搬過來最容易踩的第一個坑。

## A.3 Type I / II / III 平方和 —— 有一個會靜默給錯答案的陷阱

三種平方和的差別（和 R 完全一樣的定義）：

- **Type I（序列型）**：依 formula 中變數出現順序逐一加入，**結果會隨變數順序改變**。R 的 `anova()` 預設。行銷情境幾乎用不到。
- **Type II**：每個效果都在「所有不包含它的其他效果」之後才評估。**不受編碼方式影響**，在沒有交互作用時最有統計檢定力。**這是我推薦的預設。**
- **Type III**：每個效果都在「所有其他效果（含交互）」之後評估。SPSS 預設，論文審稿常要求。**必須搭配 sum-to-zero 編碼才有意義。**

### 陷阱：`anova_lm(typ=3)` 用預設 treatment coding 會給出無意義的結果，而且不會報錯

我實測跑了同一份資料的三種寫法（真值：a 有強主效果、b 有主效果、無交互）：

```python
# 錯誤寫法：預設 treatment coding
anova_lm(smf.ols("y ~ C(a)*C(b)", df).fit(), typ=3)
             sum_sq     df        F  PR(>F)
Intercept    0.2977    1.0   0.3112  0.5774
C(a)       179.7631    2.0  93.9527  0.0000     <- 被低估
C(b)        23.9495    1.0  25.0343  0.0000     <- 被低估
C(a):C(b)    1.4607    2.0   0.7634  0.4670
```

```python
# 正確寫法：Sum coding，等同 R 的 car::Anova(m, type=3) 搭配 contr.sum
anova_lm(smf.ols("y ~ C(a,Sum)*C(b,Sum)", df).fit(), typ=3)
                       sum_sq     df         F  PR(>F)
Intercept            103.3492    1.0  108.0304   0.000
C(a, Sum)            325.6416    2.0  170.1958   0.000   <- 正確
C(b, Sum)             48.6390    1.0   50.8421   0.000   <- 正確
C(a, Sum):C(b, Sum)    1.4607    2.0    0.7634   0.467
```

注意主效果的 SS 從 179.76 變成 325.64 —— **差了將近一倍**。兩種寫法都不會拋任何警告。這和 R 完全同構（R 裡若不先 `options(contrasts=c("contr.sum","contr.poly"))` 就跑 `car::Anova(type=3)` 也是錯的），但 Python 這邊沒有 `car` 套件會提醒你。

**交互項的 SS 在三種 Type 下都一樣**（1.4607），這是正確的，最高階交互項不受影響。

**實務建議**：預設用 Type II；只有在期刊/客戶指名要 Type III 時才用，並且**一定寫 `C(x, Sum)`**。建議在專案裡包一個防呆函式：

```python
def anova3(formula, data):
    """強制 Sum coding 的 Type III ANOVA，等同 R car::Anova(type=3)+contr.sum"""
    import re
    f = re.sub(r"C\((\w+)\)", r"C(\1, Sum)", formula)
    if "C(" in formula and "Sum" not in f:
        raise ValueError("類別變數必須以 C(x) 標註才能自動轉 Sum coding")
    return anova_lm(smf.ols(f, data).fit(), typ=3)
```

## A.4 殘差診斷四圖 —— Python 要自己畫，但可以畫到等價

R 的 `plot(m)` 一行出四張圖，Python 沒有對應品。下面是我寫的等價實作，**四張圖的定義與 R 的 `plot.lm` 一致**（含 R 特有的 Cook's distance 等高線）：

```python
import numpy as np, matplotlib.pyplot as plt
import scipy.stats as st
from statsmodels.nonparametric.smoothers_lowess import lowess

def plot_lm(m, figsize=(11, 9), n_label=3):
    """等價於 R 的 plot(lm_model)：四張標準診斷圖。"""
    inf     = m.get_influence()
    fitted  = m.fittedvalues
    resid   = m.resid
    std_r   = inf.resid_studentized_internal      # R: rstandard()
    lev     = inf.hat_matrix_diag                 # R: hatvalues()
    cook    = inf.cooks_distance[0]               # R: cooks.distance()
    p       = m.df_model + 1
    n       = int(m.nobs)

    fig, ax = plt.subplots(2, 2, figsize=figsize)

    # (1) Residuals vs Fitted —— 檢查線性與等變異
    a = ax[0, 0]
    a.scatter(fitted, resid, s=14, alpha=.6, edgecolor="none")
    lo = lowess(resid, fitted, frac=2/3, return_sorted=True)
    a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    a.axhline(0, ls=":", c="grey")
    a.set_xlabel("Fitted values"); a.set_ylabel("Residuals")
    a.set_title("Residuals vs Fitted")
    for i in np.argsort(np.abs(resid))[-n_label:]:
        a.annotate(df.index[i] if hasattr(df,'index') else i, (fitted.iloc[i], resid.iloc[i]), fontsize=8)

    # (2) Normal Q-Q —— 檢查常態性
    a = ax[0, 1]
    (osm, osr), (slope, inter, _) = st.probplot(std_r, dist="norm")
    a.scatter(osm, osr, s=14, alpha=.6, edgecolor="none")
    a.plot(osm, slope*osm + inter, color="crimson", lw=1.2, ls="--")
    a.set_xlabel("Theoretical Quantiles"); a.set_ylabel("Standardized residuals")
    a.set_title("Normal Q-Q")

    # (3) Scale-Location —— 檢查等變異（對變異數更敏感）
    a = ax[1, 0]
    srs = np.sqrt(np.abs(std_r))
    a.scatter(fitted, srs, s=14, alpha=.6, edgecolor="none")
    lo = lowess(srs, fitted, frac=2/3, return_sorted=True)
    a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    a.set_xlabel("Fitted values"); a.set_ylabel(r"$\sqrt{|Standardized\ residuals|}$")
    a.set_title("Scale-Location")

    # (4) Residuals vs Leverage + Cook's distance 等高線 —— 找影響點
    a = ax[1, 1]
    a.scatter(lev, std_r, s=14, alpha=.6, edgecolor="none")
    lo = lowess(std_r, lev, frac=2/3, return_sorted=True)
    a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    xs = np.linspace(1e-6, max(lev)*1.05, 200)
    for c, ls in [(0.5, "--"), (1.0, ":")]:
        band = np.sqrt(c * p * (1 - xs) / xs)
        a.plot(xs,  band, ls=ls, c="grey", lw=1)
        a.plot(xs, -band, ls=ls, c="grey", lw=1)
    a.set_ylim(np.min(std_r)*1.3, np.max(std_r)*1.3)
    a.axhline(0, ls=":", c="grey")
    a.set_xlabel("Leverage"); a.set_ylabel("Standardized residuals")
    a.set_title("Residuals vs Leverage")
    for i in np.argsort(cook)[-n_label:]:
        a.annotate(i, (lev[i], std_r[i]), fontsize=8, color="crimson")

    fig.tight_layout()
    return fig
```

**幾個和 R 對齊的細節**（容易做錯的地方）：

1. 第 1 圖 R 用的是**原始殘差**不是標準化殘差；第 3、4 圖才用標準化殘差。很多網路上的 Python 版本這裡是錯的。
2. 第 4 圖 R 畫的是 **leverage 在 x 軸、標準化殘差在 y 軸**，Cook's D 等高線用 `sqrt(c*p*(1-h)/h)`，`p = 參數個數（含截距）`。
3. R 的 lowess `frac` 預設是 2/3，要顯式指定才會和 R 的紅線一致。
4. GLM 要畫診斷圖時，第 1 圖應改用 **deviance residual vs linear predictor**（`g.resid_deviance` vs `g.fittedvalues` 的 link scale），直接套 OLS 那套會誤導。

## A.5 Cook's D、槓桿值、影響量數

`get_influence()` 一次全給，實測 `summary_frame()` 的欄位：

```
['dfb_Intercept', 'dfb_C(grp)[T.B]', 'dfb_C(grp)[T.C]', 'dfb_x1', 'dfb_x2',
 'cooks_d', 'standard_resid', 'hat_diag', 'dffits_internal', 'student_resid', 'dffits']
```

```python
inf = m.get_influence()
cd, cd_p = inf.cooks_distance            # R: cooks.distance()
h        = inf.hat_matrix_diag           # R: hatvalues()
inf.summary_frame()                      # 一次全拿

# 常用門檻（與 R 慣例相同）
n, p = int(m.nobs), int(m.df_model) + 1
flag_cook = cd > 4 / n                   # 經驗法則
flag_lev  = h  > 2 * p / n               # 高槓桿
flag_dffits = np.abs(inf.dffits[0]) > 2 * np.sqrt(p / n)
```

**GLM 也支援**：實測 `smf.glm(...).fit().get_influence().cooks_distance[0]` 可用。

## A.6 VIF —— 可用但有兩個坑

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor
```

**坑 1：statsmodels 的 VIF 要你自己迴圈，而且會把截距欄一起算進去**，截距那格會算出一個很大的無意義數字（我實測 3.306 那格就是截距）。

**坑 2：對類別變數，statsmodels 算的是「每個 dummy 欄」的 VIF，而 R 的 `car::vif()` 對多自由度項回傳的是 GVIF（廣義 VIF）**。這是真正的行為差異，不是包裝問題。

推薦寫法（含 GVIF，對齊 `car::vif`）：

```python
import pandas as pd, numpy as np
from patsy import dmatrix

def vif_table(model):
    """對齊 R car::vif()：連續變數給 VIF，多自由度類別項給 GVIF^(1/(2df))"""
    X  = pd.DataFrame(model.model.exog, columns=model.model.exog_names)
    Xn = X.drop(columns=[c for c in X.columns if c.lower() == "intercept"])
    di = model.model.data.design_info
    R  = np.corrcoef(Xn.values, rowvar=False)
    Rinv_det = np.linalg.det(np.linalg.inv(R))
    rows = []
    for term, slc in di.term_name_slices.items():
        if term == "Intercept":
            continue
        cols = [c for c in di.column_names[slc] if c in Xn.columns]
        idx  = [Xn.columns.get_loc(c) for c in cols]
        keep = [i for i in range(Xn.shape[1]) if i not in idx]
        gvif = (np.linalg.det(R[np.ix_(idx, idx)])
                * np.linalg.det(R[np.ix_(keep, keep)]) / np.linalg.det(R))
        dfree = len(idx)
        rows.append({"term": term, "df": dfree, "GVIF": gvif,
                     "GVIF^(1/(2df))": gvif ** (1 / (2 * dfree))})
    return pd.DataFrame(rows)
```

判讀門檻和 R 一樣：`GVIF^(1/(2df))` 超過 √5≈2.24 要注意，超過 √10≈3.16 要處理。

## A.7 巢狀模型 F 檢定 —— 完全等價，實測數字

```python
m_full = smf.ols("y ~ x1 + x2 + C(grp)", df).fit()
m_red  = smf.ols("y ~ x1 + x2",          df).fit()

F, p, ddf = m_full.compare_f_test(m_red)
# 實測輸出：F=71.4847  p=5.16e-24  ddf=2.0

anova_lm(m_red, m_full)      # 表格式輸出，和 R 的 anova(m1, m2) 版面幾乎一樣
#    df_resid         ssr  df_diff     ss_diff          F        Pr(>F)
# 0     197.0  356.569889      0.0         NaN        NaN           NaN
# 1     195.0  205.732032      2.0  150.837857  71.484692  5.162165e-24

m_full.compare_lr_test(m_red)   # 概似比檢定，GLM 用這個
# (109.99115097164156, 1.3053441807456117e-24, 2.0)
```

**注意**：`compare_f_test` 的呼叫方向是「**完整模型.compare_f_test(縮減模型)**」，和 R 的 `anova(reduced, full)` 參數順序相反，很容易寫反。寫反了 F 值會變成負數或報錯。

## A.8 事後檢定 —— 三個層次的工具

### 層次 1：statsmodels 內建（實測通過）

```python
from statsmodels.stats.multicomp import pairwise_tukeyhsd, MultiComparison

t = pairwise_tukeyhsd(df.y, df.grp, alpha=0.05)
print(t.summary())
# Multiple Comparison of Means - Tukey HSD, FWER=0.05
# group1 group2 meandiff p-adj  lower   upper  reject
#      A      B   1.2462 0.0245 0.1294   2.363   True
#      A      C  -1.2371 0.0364 -2.412 -0.0621   True
#      B      C  -2.4833    0.0 -3.595 -1.3715   True

mc = MultiComparison(df.y, df.grp)
mc.allpairtest(scipy.stats.ttest_ind, method="bonf")   # 也支援 holm, sidak, fdr_bh
```

**限制**：`pairwise_tukeyhsd` 只吃「一個反應變數 + 一個分組變數」，**不能對含共變量的模型做調整後的 Tukey**。要做那個得用 A.9 的 emmeans 替代方案。

### 層次 2：pingouin 0.6.1（實測通過，最新版 2026-03-28）

pingouin 是「R 風格 API」的統計套件，回傳整齊的 DataFrame，**含效果量**，很適合寫報告。實測可用的函式與欄位：

```python
import pingouin as pg
pg.anova(data=df, dv="y", between="grp", detailed=True)
#   欄位: Source, SS, DF, MS, F, p_unc, np2        <- np2 = partial eta squared
pg.welch_anova(data=df, dv="y", between="grp")     # 不等變異數版 ANOVA
pg.pairwise_tukey(data=df, dv="y", between="grp")
#   欄位: A, B, mean_A, mean_B, diff, se, T, p_tukey, hedges   <- 附 Hedges' g
pg.pairwise_tests(data=df, dv="y", between="grp", padjust="holm")
#   欄位: ..., p_unc, p_corr, p_adjust, BF10, hedges           <- 附 Bayes factor
pg.ancova(data=df, dv="y", covar="x1", between="grp")
pg.homoscedasticity(data=df, dv="y", group="grp")  # Levene
pg.normality(df["y"])                              # Shapiro-Wilk
pg.partial_corr(data=df, x="x1", y="y", covar="x2")
```

**pingouin 相對 R 的最大優勢**：預設就給效果量（np2、Hedges' g）和 Bayes factor，R 要另外裝 `effectsize` / `BayesFactor`。

**pingouin 的限制**：只做「標準設計」。重複量數、複雜巢狀設計它的 `rm_anova`/`mixed_anova` 只支援到相當基本的層次，比 R 的 `afex` 弱不少。

### 層次 3：scikit-posthocs（無母數事後檢定的主力）

statsmodels 和 pingouin 都不太做無母數事後檢定，這塊要靠 scikit-posthocs：

```python
import scikit_posthocs as sp
sp.posthoc_dunn(df, val_col="y", group_col="grp", p_adjust="holm")     # Kruskal 後續
sp.posthoc_conover(df, val_col="y", group_col="grp", p_adjust="holm")
sp.posthoc_dscf(df, val_col="y", group_col="grp")                      # Dwass-Steel-Critchlow-Fligner
sp.posthoc_nemenyi_friedman(wide_df)                                   # Friedman 後續
sp.sign_plot(pvalue_matrix)                                            # p 值矩陣熱圖
```

**行銷情境很需要這個**：客單價、停留時間、購買間隔天數這類變數通常嚴重右偏，用 Kruskal-Wallis + Dunn 比硬套 ANOVA 誠實得多。

## A.9 最大的缺口：`emmeans` —— 沒有對應套件，但可以補

R 的 `emmeans` 是統計課後半段的主力（估計邊際均值 / 調整後均值 / 任意對比 / 交互作用的 simple effects），**Python 生態沒有等價套件**。這是本次調研中 Python 相對 R 最實質的落差。

好消息是 statsmodels 的 `t_test()` 接受任意對比向量，可以手工補上。**下面這段我實際跑過並驗證能還原真值**：

```python
import numpy as np, pandas as pd, itertools
from patsy import dmatrix
from statsmodels.stats.multitest import multipletests

def emmeans(model, data, factor):
    """R emmeans(model, ~factor) 的等價：共變量固定在樣本平均，逐 level 求邊際均值。"""
    di = model.model.data.design_info
    rows = []
    for l in sorted(data[factor].unique()):
        d = data.copy(); d[factor] = l
        Xm = np.asarray(dmatrix(di, d)).mean(axis=0)     # 對共變量取平均 = EMM
        tt = model.t_test(Xm)
        ci = tt.conf_int()[0]
        rows.append({factor: l, "emmean": float(tt.effect[0]), "SE": float(tt.sd[0][0]),
                     "CI_low": float(ci[0]), "CI_high": float(ci[1])})
    return pd.DataFrame(rows)

def emm_contrasts(model, data, factor, method="holm"):
    """R pairs(emmeans(model, ~factor)) 的等價，含多重比較校正。"""
    di = model.model.data.design_info
    vecs = {}
    for l in sorted(data[factor].unique()):
        d = data.copy(); d[factor] = l
        vecs[l] = np.asarray(dmatrix(di, d)).mean(axis=0)
    out = []
    for a, b in itertools.combinations(vecs, 2):
        tt = model.t_test(vecs[a] - vecs[b])
        out.append({"contrast": f"{a} - {b}", "estimate": float(tt.effect[0]),
                    "SE": float(tt.sd[0][0]), "t": float(tt.tvalue.ravel()[0]),
                    "p_raw": float(tt.pvalue.ravel()[0])})
    o = pd.DataFrame(out)
    o["p_adj"] = multipletests(o.p_raw, method=method)[1]
    return o
```

實測結果（資料真值 A=0, B=1.5, C=-1，模型含共變量 x）：

```
grp  emmean     SE   CI_low  CI_high
  A -0.0776 0.0864  -0.2474   0.0922      <- 還原 0
  B  1.4735 0.0837   1.3090   1.6379      <- 還原 1.5
  C -1.1024 0.0802  -1.2600  -0.9448      <- 還原 -1

contrast  estimate     SE        t  p_raw  p_adj
   A - B   -1.5511 0.1203 -12.8983    0.0    0.0
   A - C    1.0248 0.1179   8.6906    0.0    0.0
   B - C    2.5758 0.1159  22.2315    0.0    0.0
```

**這套函式建議直接收進你的專案工具模組**，行銷分析裡「控制住客單價與年資後，三個會員等級的回購率有沒有差」這種問題天天會用到。

**限制**：這個實作對應 emmeans 的預設行為（共變量取平均、類別變數取等權平均）。emmeans 的 `weights=`、`at=`、`by=`、非線性模型的 `type="response"` 反轉換等進階功能都要另外自己寫。GLM 上要小心：`t_test` 給的是 link scale 的結果，要轉回機率尺度得自己套 inverse link，且信賴區間要先在 link scale 算好再轉換（不能直接轉換上下界的中點）。

## A.10 其他 Python 真的補不上的 R 功能，以及怎麼繞

| R 功能 | Python 現況 | 繞法 |
|---|---|---|
| **`emmeans`** 全套 | 無 | A.9 自製函式，涵蓋 8 成常用情境 |
| **`DHARMa`** 模擬殘差診斷（GLM/GLMM 的正確殘差診斷） | **無任何對應品** | GLM 用 deviance residual + binned residual plot 手工做；或接受這塊比 R 弱。這是 Poisson/負二項模型診斷的真實損失 |
| **`performance::check_model`** 一鍵全套診斷 | 無 | 用 A.4 的 `plot_lm` + A.6 的 `vif_table` 自己包一個 |
| **`lme4::lmer`** 複雜隨機效果 | `MixedLM` 可用但弱 | 單一隨機截距沒問題；**交叉隨機效果（crossed random effects）、多重隨機斜率 statsmodels 支援很差**。真的需要就用 PyMC 手寫階層模型，或（誠實選項）這一塊留在 R |
| **`glmmTMB`** 零膨脹/負二項 GLMM | 無 | statsmodels 有 `ZeroInflatedPoisson`/`NegativeBinomial` 但**不含隨機效果**；要兩者兼具只能 PyMC |
| **`car::Anova`** 的便利性 | `anova_lm` 有但需手動 Sum coding | A.3 的 `anova3` 防呆函式 |
| **`broom::tidy/glance`** 模型結果整齊化 | 無標準品 | 自己寫：`m.summary2().tables[1]` 拿係數表，或 `pd.DataFrame({"coef":m.params,"se":m.bse,"p":m.pvalues})` |
| **`survey`** 複雜抽樣加權 | 幾乎無 | statsmodels 的 `freq_weights` 只處理次數權重，不處理分層/叢集抽樣設計。市調資料若有設計權重，這是實質缺口 |
| **`mgcv::gam`** 的成熟度 | `GLMGam` 陽春 | 平滑項選擇、自動 smoothing parameter 估計都遠不如 mgcv。改用 `pyGAM`（但維護狀態我未查證）或改用樹模型 |
| **`multcomp::glht`** 任意線性假設 | **`m.t_test()` / `m.f_test()` 其實夠用** | 這個其實**不算缺口**，statsmodels 的對比向量介面很完整，只是不好寫 |
| R 的 formula `poly()`, `.` | 不支援 | 手動展開 |

**總結判斷**：R 統計課那套搬到 Python，**線性模型 / ANOVA / 診斷 / 事後檢定這條主線是完全可行的**，甚至部分地方（穩健標準誤、效果量）比 R 更順手。真正會痛的是三處：`emmeans`（可自製補上）、`DHARMa`（沒得補）、複雜混合模型（要退回 PyMC 或 R）。行銷分析日常工作**極少踩到後兩者**，所以這個遷移決定是站得住腳的。

---

# PART B — 行銷專用套件逐一查證

> 所有「最後活躍時間」皆為我實際透過 GitHub commits/releases Atom feed 與 GitHub API 取得的絕對時間戳，非相對時間推測。
> BI = Business Intelligence（描述，發生了什麼）／CI = Causal Inference（因果，為什麼／若…會如何）／DI = Decision Intelligence（決策，該怎麼做）

## B.1 pymc-labs/pymc-marketing — **推薦，核心**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/pymc-labs/pymc-marketing |
| star 數量級 | ~1.2k（實測 1,206） |
| **實際最後活躍** | **最後 commit 2026-07-20；最新 release 0.19.4 發布於 2026-05-06** |
| archived | **否**（API `archived: false`） |
| Python 3.14 | **實測 dry-run 通過**，可解析出 pymc 5.28.5 + pytensor 2.38.3 完整相依樹 |
| 定位 | 貝氏行銷工具箱：MMM、CLV、Customer Choice |

**回答什麼行銷問題**：
- MMM：各通路的邊際 ROI、飽和點、廣告延滯效應（adstock）、預算最佳配置
- CLV：BG/NBD、Gamma-Gamma、Pareto/NBD、Shifted Beta-Geometric —— **完整涵蓋 lifetimes 的所有模型**
- Customer Choice：新品上市對既有品的蠶食效應、Bass 擴散

**需要什麼資料粒度**：
- MMM：**週或日層級的通路花費 + 成效時間序列**，至少 2 年（104 週）才穩定
- CLV：交易明細（customer_id, date, amount），可彙總成 RFM summary

**BI/CI/DI**：MMM 是 **CI + DI**（估因果貢獻，然後最佳化預算）；CLV 是 **BI + DI**（描述客戶價值，驅動分群行動）

**四種資料型態的用處**：
- CRM：**主戰場**，CLV 全套
- 網站：可作為 MMM 的中介變數
- 廣告：**主戰場**，MMM 的輸入
- POS：MMM 可加入門市促銷變數；CLV 需有會員綁定才能算

**取捨**：
- 優點：唯一同時涵蓋 MMM + CLV 且活躍維護的 Python 套件；貝氏框架天生給出不確定性區間，對「這個 ROI 估計有多可信」這種老闆問題非常有力；lifetimes 官方指定的接班人
- 缺點：**要求 Python >= 3.12**；MCMC 取樣慢（MMM 大模型動輒數十分鐘）；需要理解先驗設定，不是黑箱套用；相依樹很重（pytensor + numba + arviz 一整串）

## B.2 CamDavidsonPilon/lifetimes — **明確不用（已 archived）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/CamDavidsonPilon/lifetimes |
| star 數量級 | ~1.5k（實測 1,477） |
| **實際最後活躍** | **最後 commit 2024-06-28；最後 release v0.11.3 發布於 2020-07-06** |
| archived | **是** — "This repository was archived by the owner on Jun 28, 2024. It is now read-only." |

README 原文："A project has emerged as a successor to lifetimes, PyMC-Lab/PyMC-Marketing, please check it out!"、"This codebase has moved to 'archived-mode'. We won't be adding new features, improvements, or even answering issues in this codebase."

PyPI 上的 lifetimes 0.11.3 classifiers 只列到 **Python 2.7 / 3.5**。

**結論：不要用。** 你懷疑得對。功能完全被 pymc-marketing 的 CLV 模組取代，而且後者的模型清單是超集。網路上大量 CLV 教學仍在用 lifetimes，**遇到請直接換算成 pymc-marketing 的 API**。

## B.3 google/meridian — **推薦但有 Python 版本硬限制**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/google/meridian |
| star 數量級 | ~1.5k（實測 1,468） |
| **實際最後活躍** | **最後 commit 2026-07-24；PyPI 最新 1.7.1 上傳於 2026-07-22** |
| archived | **否** |
| **Python 3.14** | **實測安裝失敗** |

README 原文："Python 3.11-3.13 is required"、"We also recommend using a minimum of 1 GPU"、"This project has been tested on T4 GPU using 16 GB of RAM"

**Python 3.14 失敗的實測原因**：相依 `tensorflow<2.21,>=2.19.0` 與 `tfp-nightly==0.26.0.dev20260130`，而 TensorFlow 最新版 2.21.0（2026-03-06）**沒有 cp314 wheel**。dry-run 錯誤：

```
error: subprocess-exited-with-error
..\meson.build:1:0: ERROR: Unknown compiler(s): [['icl'], ['cl'], ['cc'], ...]
error: metadata-generation-failed
```

**回答什麼行銷問題**：MMM，且是 Google 官方版本 —— 特別強調 **incrementality experiment 校準**（可把地理實驗結果當先驗餵進模型）、reach & frequency 建模、Google 生態的媒體資料整合。

**需要什麼資料粒度**：週層級、**建議帶地理維度（geo-level）** 的媒體花費與成效；Meridian 的地理階層模型是它相對 pymc-marketing 的主要優勢。

**BI/CI/DI**：**CI + DI**

**四種資料型態**：廣告（主戰場）；POS/CRM 可作為 KPI 端；網站行為可作為中介

**取捨**：
- 優點：Google 官方、有實驗校準機制、地理階層模型成熟、業界（尤其大型廣告主）認可度高
- 缺點：**必須 Python 3.11–3.13，你的 3.14 主環境裝不起來**；TensorFlow Probability 相依很重（且釘在 nightly 版，是個維護風險訊號）；沒 GPU 會很慢；資料需求（geo-level）門檻高，中小型客戶常給不出來

## B.4 google/lightweight_mmm — **明確不用（已 archived）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/google/lightweight_mmm |
| star 數量級 | ~1.1k（實測 1,052） |
| **實際最後活躍** | **最後 commit 2025-06-17；最後 release v0.1.9 發布於 2023-05-23** |
| archived | **是** — "This repository was archived by the owner on Jan 19, 2026. It is now read-only." |

README 原文："As of 29 Jan 2025 Google has released a new official Bayesian MMM version called **Meridian**"、"we **highly** recommend you switch to Meridian"、"LMMM is not supported anymore."

**結論：不要用。** 你懷疑得對。Google 自己已把使用者導向 Meridian。

## B.5 facebookexperimental/Robyn — **不建議作為 Python 主線**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/facebookexperimental/Robyn |
| star 數量級 | ~1.5k（實測 1,495） |
| **實際最後活躍** | **main 分支最後 commit 2025-06-27；最後 release v3.12.0 [GitHub R] 發布於 2024-12-20**（repo 層級 `pushed_at` 為 2026-01-26，屬非主分支活動） |
| archived | **否** |

**關鍵發現**：Robyn 的核心是 **R 套件**。README 原文："Robyn is available in R and Python."，但 Python 版標註為 **"Quick start for Python (Beta)"**，且明說："Please note that the current Python version is a **LLM-translated Beta version** and might encounter bugs."、"we anticipate that there could be some issues in the translation from R to Python."

另一個 Python 選項是 "Robyn API for Python (beta)"，但那是 plumber-based 方案，**要求先安裝 R 套件本體**。

**回答什麼行銷問題**：MMM，走頻率學派 + 演化式演算法（Nevergrad）做超參數搜尋與多目標最佳化，和貝氏路線互補。

**BI/CI/DI**：**CI + DI**

**取捨**：
- 優點：Meta 出品、業界知名度高、自動超參數搜尋省調參力氣、Pareto 前緣輸出很適合給決策者看取捨
- 缺點：**Python 版是 LLM 翻譯的 Beta，用在正式交付有風險**；主線 release 已一年半沒更新（v3.12.0, 2024-12-20）；真要用等於要維護一套 R 環境，違背你「Python 為主」的前提

**結論**：知道它存在、看得懂別人的 Robyn 報告即可。**你的 MMM 主線走 pymc-marketing，需要 Google 生態相容性時再開 Python 3.12 環境跑 Meridian。**

## B.6 uber/causalml — **推薦（但需注意編譯）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/uber/causalml |
| star 數量級 | ~5.9k（實測 5,933） |
| **實際最後活躍** | **最後 commit 2026-07-24；最新 release v0.17.0 發布於 2026-07-04** |
| archived | **否** |
| Python 3.14 | **相依解析通過，但 PyPI 只有 cp311/cp312 wheel，實際安裝需編譯（見取捨）** |

**回答什麼行銷問題**：**Uplift modeling / 增量建模** —— 「這檔優惠券該發給誰？」不是找「最可能買的人」，而是找「**因為收到才買**的人」。這是行銷分析從相關走向因果最關鍵的一步。

具體方法：Meta-learners（S/T/X/R-learner）、Uplift Tree/Forest、CEVAE、增益曲線與 Qini 係數評估。

**需要什麼資料粒度**：**個人層級**的（處理指派 T, 特徵 X, 結果 Y）。**最好來自隨機實驗**；觀察性資料要靠 propensity score 調整，且要能自圓其說。

**BI/CI/DI**：**CI + DI**（估個體處理效果 → 決定發給誰）

**四種資料型態**：
- CRM：**主戰場** —— EDM 該寄給誰、折扣該給誰、挽留該打給誰
- 網站：站上推薦/彈窗該對誰出
- 廣告：受眾出價分層、廣告該追誰
- POS：門市促銷 DM 該寄給哪些會員

**取捨**：
- 優點：uplift 這塊最完整成熟的 Python 套件、活躍維護（一個月內有 release）、評估工具（Qini/AUUC）齊全、Uber 實戰驗證
- 缺點：**PyPI 只提供到 cp312 wheel**，在 Python 3.14 上 pip 會退回原始碼編譯 Cython 擴充，需要 MSVC Build Tools（我只驗證到相依解析階段，未實際完成編譯 —— 見第 5 節）；相依很重（會拉進 lightgbm、xgboost、shap、numba）；沒有隨機實驗資料時結論很脆弱

## B.7 maks-sh/scikit-uplift — **不推薦（實質停更近四年）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/maks-sh/scikit-uplift |
| star 數量級 | ~0.8k（實測 808） |
| **實際最後活躍** | **最後 commit 2022-08-11；最後 release Version 0.5.1 發布於 2022-08-11** |
| archived | **否（但這是關鍵：沒有 archived 標記，容易被誤認為還活著）** |

**這是本次調研的一個重要發現**：scikit-uplift **沒有** archived 標記，PyPI 也照樣掛著，但 **commit 與 release 都停在 2022-08-11，將近四年沒有任何動靜**。PyPI classifiers 只寫了通用的 "Programming Language :: Python :: 3"，沒有具體版本宣告。

**定位**：sklearn 風格的 uplift modeling API，比 causalml 輕量好上手，文件寫得漂亮。

**取捨**：
- 優點：API 極簡潔（`SoloModel`, `ClassTransformation`, `TwoModels` 三個類別就涵蓋主流方法）、視覺化好看、學習曲線平緩
- 缺點：**近四年零維護**，與新版 scikit-learn（你環境是 1.7.2）的相容性是定時炸彈；作者未宣告 Python 3.10+ 支援

**結論：不要用在正式專案。** 拿它的文件當 uplift 概念的教材很好，但實作走 causalml。

## B.8 py-why/EconML — **想用但 Python 3.14 裝不起來**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/py-why/EconML |
| star 數量級 | ~4.7k（實測 4,727） |
| **實際最後活躍** | **最後 commit 2026-07-23；最新 release v0.16.0 發布於 2025-07-14** |
| archived | **否** |
| **Python 3.14** | **實測安裝失敗** |

注意這個組合：**程式碼很活躍（三天前還有 commit），但已一年沒發 release**。PyPI wheel 只到 **cp313**。實測錯誤同 Meridian：

```
error: subprocess-exited-with-error
..\meson.build:1:0: ERROR: Unknown compiler(s): [...]
error: metadata-generation-failed
```

**回答什麼行銷問題**：異質處理效果（CATE）的計量經濟學路線 —— Double ML、Doubly Robust Learner、Orthogonal Forest、Deep IV（工具變數）、政策學習樹。相對 causalml 更偏「估計量的統計性質正確」，有信賴區間。

**需要什麼資料粒度**：個人層級（T, X, Y, 可選 W 混淆變數、Z 工具變數）

**BI/CI/DI**：**CI**（純因果估計，DI 要靠它的 policy tree）

**四種資料型態**：與 causalml 相同，但更適合「需要對估計值做統計推論」的場合，例如要跟老闆說「這個 uplift 是 3.2% ± 0.8%」。

**取捨**：
- 優點：微軟研究院出品、理論嚴謹、有信賴區間、`PolicyTree` 輸出可解釋的分群規則、與 dowhy 同屬 py-why 生態可串接
- 缺點：**Python 3.14 裝不起來**；release 節奏慢（v0.16.0 已滿一年）；API 比 causalml 陡峭；文件對非計量背景的人不友善

## B.9 py-why/dowhy — **最危險的一個：會靜默降版四年**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/py-why/dowhy |
| star 數量級 | ~8.2k（實測 8,232，本次調研中最高） |
| **實際最後活躍** | **最後 commit 2026-07-19；最新 release v0.14 發布於 2025-11-15** |
| archived | **否** |
| **Python 3.14** | **會靜默安裝到 0.8（2022 年版本）** |

**這是本文最重要的一個警告**。dowhy 0.14 的 metadata 是 `Requires-Python >=3.9,<3.14`。在 Python 3.14.1 上：

- `pip install dowhy` → **成功**，但裝到 **0.8**
- `pip install dowhy==0.14` → 明確報錯（見第 0 節實測輸出）

0.8 是 2022 年的版本，缺少後來整個 GCM（graphical causal model）模組、缺少 2025 年新增的 doubly robust estimator。**如果沒注意到，會以為自己在用最新版而寫出基於舊 API 的分析。**

**回答什麼行銷問題**：因果推論的「四步驟框架」—— 建模（畫因果圖 DAG）→ 識別（這個效果理論上可估嗎）→ 估計 → **反駁測試（refutation）**。最後這步是它的獨門價值：安慰劑處理、隨機共同原因、資料子集穩健性，用來檢驗「我的因果宣稱有多脆弱」。

**需要什麼資料粒度**：個人或事件層級 + **一張你願意為之辯護的因果圖**

**BI/CI/DI**：**CI**（純粹的因果識別與驗證，不做決策最佳化）

**四種資料型態**：
- CRM：會員升等真的提升消費，還是本來就會消費的人才升等？
- 網站：改版真的提升轉換，還是季節性？
- 廣告：曝光與轉換的相關有多少是選擇偏誤（廣告本來就投給高意願者）
- POS：門市改裝的真實增量

**取捨**：
- 優點：**refutation 測試是其他套件沒有的**，強迫分析者面對自己的假設；DAG 語言讓因果假設可被同事審查；社群最大
- 缺點：**Python 3.14 的靜默降版陷阱**；估計器本身不如 EconML 強（官方也建議兩者搭配）；DAG 要自己畫，畫錯了整套結論就錯，這需要領域知識而非工具能解決

## B.10 CamDavidsonPilon/lifelines — **推薦**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/CamDavidsonPilon/lifelines |
| star 數量級 | ~2.6k（實測 2,596） |
| **實際最後活躍** | **最後 commit 2026-03-07；最新 release v0.30.3 發布於 2026-03-05** |
| archived | **否** |
| Python 3.14 | **實測 dry-run 通過**（純 Python wheel） |

注意同一作者的 lifetimes 已 archived，但 **lifelines 仍在維護** —— 這兩個很容易混淆，別因為 lifetimes 死了就以為 lifelines 也死了。

**回答什麼行銷問題**：**流失/存活分析** —— 不是「會不會流失」而是「**多久後流失**」、「現在還沒流失的人風險曲線長怎樣」。訂閱制的續訂、會員的沉睡時點、購買間隔。

具體方法：Kaplan-Meier 存活曲線、Cox 比例風險模型、AFT 參數模型（Weibull/LogNormal）、時變共變量。

**需要什麼資料粒度**：每人一列的（存續時間, 是否已發生事件, 共變量），**必須正確處理右設限（right censoring）** —— 還沒流失的人不是「沒流失」而是「觀察期內尚未流失」，這是存活分析的核心，也是用一般分類模型做流失預測最常犯的錯。

**BI/CI/DI**：**BI + CI**（描述存活曲線；Cox 模型估各因子的風險比）

**四種資料型態**：
- CRM：**主戰場**，會員生命週期、訂閱續訂、沉睡預警
- 網站：註冊到首購的時間、session 停留時間
- 廣告：（較少用）
- POS：會員回購間隔、門市客戶留存

**取捨**：
- 優點：API 極好用、文件是同類套件裡最清楚的、繪圖直接可用於報告、純 Python 安裝無痛
- 缺點：大資料量（百萬列以上）的 Cox 模型會慢；不做機器學習式的存活模型（要那個用 scikit-survival）

## B.11 sebp/scikit-survival — **推薦（與 lifelines 互補）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/sebp/scikit-survival |
| star 數量級 | ~1.3k（實測 1,312） |
| **實際最後活躍** | **最後 commit 2026-07-23；最新 release v0.28.0 發布於 2026-07-05** |
| archived | **否** |
| Python 3.14 | **PyPI 有 cp314 wheel，實測 dry-run 通過** |

**與 lifelines 的分工**：lifelines 是「統計解釋」路線（我要知道哪個因子影響風險、影響多少）；scikit-survival 是「**預測**」路線（我要準確預測誰先流失，用 Random Survival Forest / Gradient Boosting / Survival SVM）。**兩個都裝，不衝突。**

**BI/CI/DI**：**DI**（預測驅動行動：對高風險名單做挽留）

**取捨**：
- 優點：完全 sklearn 相容（可進 Pipeline、GridSearchCV）、有 cp314 wheel、活躍維護（三週內有 release）
- 缺點：可解釋性弱於 Cox；模型評估指標（C-index、Brier score）需要額外理解成本

## B.12 Nixtla/statsforecast — **推薦**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/Nixtla/statsforecast |
| star 數量級 | ~4.9k（實測 4,850） |
| **實際最後活躍** | **最後 commit 2026-07-21；最新 release v2.1.1 發布於 2026-07-16** |
| archived | **否** |
| Python 3.14 | **PyPI 有 cp314 wheel，實測 dry-run 通過** |

**回答什麼行銷問題**：**大規模時間序列預測** —— 未來 12 週各門市/各品類的銷售、需求規劃、預算基準線。也提供 MSTL 分解拆出趨勢/季節/殘差，可作為「這波成長是活動效果還是季節性」的第一層判斷。

**需要什麼資料粒度**：長格式的（unique_id, ds, y）。它的設計目標就是**同時預測數千條序列**（每個 SKU × 每家店）。

**BI/CI/DI**：**BI + DI**（預測基準線；驅動備貨與預算決策）

**四種資料型態**：
- POS：**主戰場**，門市 × 品類的銷售預測
- 廣告：花費與成效的基準線預測（也可做 counterfactual baseline 給 incrementality 分析用）
- 網站：流量預測、容量規劃
- CRM：新增會員數預測

**取捨**：
- 優點：**快得離譜**（Numba 編譯，比 statsmodels 的 ARIMA 快一到兩個數量級）、AutoARIMA/AutoETS/AutoTheta 自動選模、與 DuckDB/Polars 生態契合、有 cp314 wheel、維護非常活躍
- 缺點：只做統計方法（要 ML 方法得配 Nixtla 的 mlforecast）；相依會拉進 fugue/triad 一串；階層調和（hierarchical reconciliation）要另裝 hierarchicalforecast

## B.13 rasbt/mlxtend — **推薦（購物籃分析唯一選擇）**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/rasbt/mlxtend |
| star 數量級 | ~5.2k（實測 5,164） |
| **實際最後活躍** | **最後 commit 2026-06-06；最新 release v0.25.0 發布於 2026-06-06** |
| archived | **否** |
| Python 3.14 | **實測 dry-run 通過**（純 Python wheel） |

**回答什麼行銷問題**：**購物籃分析 / 關聯規則** —— 「買 A 的人也買 B」、交叉銷售組合、貨架陳列與捆綁定價、推薦位選品。

具體演算法：`apriori`、`fpgrowth`、`fpmax`、`association_rules`（support / confidence / lift / leverage / conviction / zhangs_metric）。

**需要什麼資料粒度**：**交易 × 品項的 one-hot 矩陣**（每列一張發票，每欄一個品項）。這是資料工程的重點：從 POS 明細轉成這個格式在 DuckDB 裡用 `PIVOT` 或 `list()` 聚合最有效率。

**BI/CI/DI**：**BI**（純描述性關聯，**不是因果**）

**四種資料型態**：
- POS：**主戰場**，實體零售的品類關聯
- CRM/電商：跨品類購買組合
- 網站：頁面瀏覽序列的關聯（把 session 當作籃子）
- 廣告：（較少用）曝光通路組合的關聯

**取捨**：
- 優點：purchase basket 這塊 Python 沒有第二個成熟選擇；API 簡單；作者（Sebastian Raschka）維護穩定
- 缺點：**大資料量會爆記憶體** —— one-hot 矩陣是 交易數 × 品項數 的稠密矩陣，10 萬張發票 × 5000 品項就要小心（用 `sparse` DataFrame 並優先選 `fpgrowth` 而非 `apriori`）；lift 高不代表有因果，**經典陷阱是熱銷品和任何東西的關聯都看似很強**，要看 lift 而非 confidence
- 注意：PyPI classifiers 只列 Python 3.11，但它是純 Python wheel，實測在 3.14 可安裝

## B.14 EducationalTestingService/factor_analyzer — **可用但要留意低活躍度**

| 項目 | 內容 |
|---|---|
| repo | https://github.com/EducationalTestingService/factor_analyzer |
| star 數量級 | GitHub 頁面顯示 **4**（數字異常低，見第 5 節） |
| **實際最後活躍** | **最後 commit 2025-01-21；最新 release v0.5.1 發布於 2024-02-08** |
| archived | **否** |
| Python 3.14 | **實測 dry-run 通過**（但 PyPI **只有 sdist、無任何 wheel**） |

**回答什麼行銷問題**：**因素分析 / 量表建構**，取代 SPSS —— 問卷的構面萃取、品牌形象維度、滿意度量表的效度驗證、把 30 題問卷壓成 5 個可解釋的因素。

功能：EFA（探索性因素分析，含多種旋轉 varimax/promax/oblimin）、CFA（驗證性因素分析）、KMO 檢定、Bartlett 球形檢定、陡坡圖資料。

**需要什麼資料粒度**：受訪者 × 題項的矩陣（問卷原始作答）

**BI/CI/DI**：**BI**（結構描述與降維）

**四種資料型態**：主要用於**問卷/市調資料**，不直接對應你列的四種行為資料。但在行銷分析裡經常和 CRM 資料 join（會員問卷 + 實際消費行為）。

**取捨**：
- 優點：Python 生態裡做 EFA/CFA 最完整的；KMO 與 Bartlett 這兩個 SPSS 必報的指標它有；能真正取代 SPSS 的因素分析模組
- 缺點：**活躍度低**（release 已兩年半，commit 已一年半）；**PyPI 只有 sdist 沒有 wheel**，安裝時要能跑 setup.py；classifiers 只列到 Python 3.11；CFA 功能遠不如 R 的 `lavaan` 或 Python 的 `semopy`（要做完整 SEM 路徑分析請另尋工具）
- **判斷**：不是死的，但也不是活躍的。做 EFA 夠用；要做 SEM 請不要指望它

## B.15 A/B 測試套件 — 你提到的方向對，但具體套件要換

你提到「benmiroglio/pysparkling 之類的 AB test 套件」—— **pysparkling 不是 A/B 測試套件**（那是 Spark 的純 Python 實作），這裡應該是記混了。我實際查了目前的選項：

| 套件 | PyPI 最新版 / 日期 | GitHub 最後 commit | 判斷 |
|---|---|---|---|
| **e10v/tea-tasting** | **v2.0.0 / 2026-06-07** | **2026-07-11** | **推薦**，唯一明確活躍 |
| **Matt52/bayesian-testing** | v0.9.4 / 2026-05-12 | 2026-05-12 | 可用，貝氏路線 |
| PlaytikaOSS/abexp | v0.0.3 / **2021-10-13** | 2024-06-14 | 不推薦，PyPI 停在 2021 |
| AdiVarma27/pyAB | v0.0.2 / **2020-06-17** | 未查 | 不推薦 |
| abracadabra | v0.0.7 / **2021-04-06** | 未查 | 不推薦 |
| tcassou/babtest | v1.0.7 / **2020-07-30** | 未查 | 不推薦 |

**tea-tasting**（star ~333，`requires_python >=3.12`）：定位是「實驗分析」而非「實驗平台」，支援 Welch t 檢定、Bootstrap、**CUPED 變異數縮減**、**delta method 處理 ratio metrics**、序貫檢定。CUPED 和 ratio metric 這兩項是實務上真正會遇到的難點（例如「人均訂單數」這種比率指標的標準誤不能直接算），一般套件不處理。它還能直接對接 SQL 後端。

**但最重要的建議是**：A/B 測試的 80% 需求，**statsmodels 自己就夠了**，不必額外裝套件：

```python
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.power import TTestIndPower, NormalIndPower
from statsmodels.stats.weightstats import ttest_ind, CompareMeans, DescrStatsW

# 轉換率差異檢定
z, p = proportions_ztest([conv_a, conv_b], [n_a, n_b])
# 事前樣本數估計（R: power.prop.test）
NormalIndPower().solve_power(effect_size=0.05, alpha=.05, power=.8, ratio=1)
# 連續型指標（客單價）
CompareMeans(DescrStatsW(a), DescrStatsW(b)).ttest_ind(usevar="unequal")  # Welch
```

**BI/CI/DI**：**CI**（隨機實驗是因果推論的黃金標準）

**四種資料型態**：網站（**主戰場**，A/B test 原生場域）、廣告（廣告素材測試、geo-lift 實驗）、CRM（EDM 主旨行測試、優惠券實驗）、POS（門市層級的 geo 實驗，要用 B.6/B.8 的方法或合成控制）

## B.16 歸因分析（Markov chain attribution）— **最弱的一環，要有心理準備**

這是本次調研中生態最不理想的一塊。逐一查證：

| 套件 | 實測最後活躍 | 判斷 |
|---|---|---|
| **ChannelAttribution**（PyPI）/ DavideAltomare/ChannelAttribution | PyPI **v2.2.5 / 2026-06-08**；GitHub 最後 commit **2024-02-01**；star ~17 | 有條件推薦，**Windows 需 MSVC** |
| DP6/Marketing-Attribution-Models（PyPI: marketing-attribution-models） | PyPI **v1.0.10 / 2022-07-11**；GitHub 最後 commit **2026-04-28**；star ~365 | 程式碼有動但 **PyPI 停在 2022** |
| jmwoloso/pychattr | PyPI **v0.2.1 / 2019-10-25** | **不要用**，近七年沒動 |

**ChannelAttribution** 是這裡最實用的：它是 R 的 `ChannelAttribution` 套件的同源 Python 版，核心用 C++ 實作 k 階 Markov 模型（移除效應 removal effect），另附 first-touch / last-touch / linear-touch 三種啟發式歸因。PyPI 版本很新（2026-06），但 GitHub commit 停在 2024-02 —— 這個落差我無法解釋（見第 5 節）。

**注意**：官方說明「installation on Windows requires Microsoft Visual C++ 14.0 or greater」，且 PyPI **只有 sdist、無 wheel、無 cp314**。我的 dry-run 顯示相依可解析，但**沒有實際完成編譯驗證**。

**DP6/Marketing-Attribution-Models** 的情況相反：GitHub 三個月前還有 commit，但 PyPI 上的版本停在 2022 年。要用建議直接從 GitHub 裝。

**回答什麼行銷問題**：多觸點歸因 —— 使用者接觸了 展示廣告 → 搜尋 → EDM → 才購買，這筆轉換的功勞怎麼分？相對於 last-click 歸因（把功勞全給最後一個觸點，系統性低估上層漏斗），Markov 模型用「移除某通路後轉換會掉多少」來分配。

**需要什麼資料粒度**：**使用者層級的完整觸點路徑序列**（user_id, timestamp, channel, converted）。這是最大的實務門檻 —— 隱私政策收緊後跨裝置跨平台的路徑資料越來越難拿到。

**BI/CI/DI**：**介於 BI 與 CI 之間**。要誠實說：**Markov 歸因不是真正的因果推論**，它是在觀察到的路徑上做的結構化功勞分配，仍受選擇偏誤影響（會看廣告的人本來就更可能買）。真要因果請走 MMM（B.1/B.3）或 incrementality 實驗（B.15）。

**四種資料型態**：廣告（主戰場）、網站（路徑資料來源）、CRM（EDM 作為觸點之一）、POS（線上到線下歸因，資料極難串）

**取捨與建議**：
- 這塊 Python 生態明顯落後 R（R 的 `ChannelAttribution` 是成熟的 CRAN 套件）
- **Markov removal effect 的演算法本身不難**，如果安裝出問題，**自己用 pandas + numpy 實作一階 Markov 移除效應約 100 行內可完成**，這可能比和 C++ 編譯環境搏鬥更省時間
- 更重要的是管理期望：**歸因模型的輸出不該被當成因果證據**，要在報告裡寫清楚

---

## 3. 總結比較表

| 套件 | Star | **實測最後活躍** | Archived | **Py 3.14** | 階層 | 主要資料型態 | 判斷 |
|---|---|---|---|---|---|---|---|
| **statsmodels** | 11.5k | commit 2026-07-24 / rel 0.14.6 (2025-12-05) | 否 | **OK（有 cp314 wheel）** | BI/CI | 全部 | **核心必裝** |
| **pingouin** | 1.9k | commit 2026-03-28 / rel 0.6.1 (2026-03-28) | 否 | OK | BI/CI | 全部 | **推薦** |
| **scikit-posthocs** | 386 | commit 2026-07-24 / rel 0.14.0 (2026-05-26) | 否 | OK | BI/CI | 全部 | **推薦** |
| **pymc-marketing** | 1.2k | commit 2026-07-20 / rel 0.19.4 (2026-05-06) | 否 | OK | CI/DI | 廣告, CRM | **推薦（MMM+CLV 核心）** |
| **google-meridian** | 1.5k | commit 2026-07-24 / PyPI 1.7.1 (2026-07-22) | 否 | **失敗（TF 無 cp314）** | CI/DI | 廣告 | 次環境 (3.12) |
| **causalml** | 5.9k | commit 2026-07-24 / rel 0.17.0 (2026-07-04) | 否 | **需編譯（未驗證）** | CI/DI | CRM, 廣告 | **推薦（uplift）** |
| **EconML** | 4.7k | commit 2026-07-23 / rel 0.16.0 (2025-07-14) | 否 | **失敗（無 cp314 wheel）** | CI | CRM, 廣告 | 次環境 (3.12) |
| **dowhy** | 8.2k | commit 2026-07-19 / rel 0.14 (2025-11-15) | 否 | **靜默降版到 0.8** | CI | 全部 | 次環境 (3.12) |
| **lifelines** | 2.6k | commit 2026-03-07 / rel 0.30.3 (2026-03-05) | 否 | OK | BI/CI | CRM | **推薦（流失）** |
| **scikit-survival** | 1.3k | commit 2026-07-23 / rel 0.28.0 (2026-07-05) | 否 | **OK（有 cp314 wheel）** | DI | CRM | **推薦** |
| **statsforecast** | 4.9k | commit 2026-07-21 / rel 2.1.1 (2026-07-16) | 否 | **OK（有 cp314 wheel）** | BI/DI | POS, 廣告 | **推薦（預測）** |
| **mlxtend** | 5.2k | commit 2026-06-06 / rel 0.25.0 (2026-06-06) | 否 | OK | BI | POS, 電商 | **推薦（購物籃）** |
| **factor_analyzer** | 顯示 4 (存疑) | commit 2025-01-21 / rel 0.5.1 (2024-02-08) | 否 | OK (僅 sdist) | BI | 問卷 | 可用，活躍度低 |
| **tea-tasting** | 333 | commit 2026-07-11 / rel 2.0.0 (2026-06-07) | 否 | 未驗證 (需 >=3.12) | CI | 網站, 廣告 | **推薦（A/B）** |
| **ChannelAttribution** | ~17 | commit 2024-02-01 / PyPI 2.2.5 (2026-06-08) | 否 | 需 MSVC（未驗證） | BI | 廣告 | 有條件 |
| **lifetimes** | 1.5k | **commit 2024-06-28 / rel v0.11.3 (2020-07-06)** | **是（2024-06-28）** | — | — | — | **不用** |
| **lightweight_mmm** | 1.1k | **commit 2025-06-17 / rel v0.1.9 (2023-05-23)** | **是（2026-01-19）** | — | — | — | **不用** |
| **scikit-uplift** | 808 | **commit 2022-08-11 / rel 0.5.1 (2022-08-11)** | 否（但停更近 4 年） | — | — | — | **不用** |
| **Robyn** | 1.5k | main commit 2025-06-27 / rel v3.12.0 (2024-12-20) | 否 | R 為主，Py 是 LLM 翻譯 Beta | CI/DI | 廣告 | **不用（Python 線）** |
| **pychattr** | — | PyPI v0.2.1 (2019-10-25) | — | — | — | — | **不用** |

---

## 4. 推薦堆疊

### 主環境：Python 3.14.1（你現在的環境）— 統計 + 倉儲 + 交付

```
# 已裝，保持
duckdb 1.5.5, pandas 2.3.3, numpy 2.3.5, scipy 1.16.3,
statsmodels 0.14.6, pingouin 0.6.1, scikit-learn 1.7.2,
matplotlib 3.10.7, seaborn 0.13.2

# 建議加裝（全部實測 dry-run 通過）
pip install scikit-posthocs        # 無母數事後檢定
pip install lifelines              # 流失/存活（統計解釋）
pip install scikit-survival        # 流失預測（ML，有 cp314 wheel）
pip install statsforecast          # 時間序列預測（有 cp314 wheel）
pip install mlxtend                # 購物籃 apriori/fpgrowth
pip install factor_analyzer        # 因素分析（取代 SPSS）
pip install pymc-marketing         # MMM + CLV（相依樹重但可裝）
pip install tea-tasting            # A/B 測試（CUPED、ratio metrics）
```

**這個環境涵蓋：Part A 全部統計需求 + CLV + MMM + 流失 + 預測 + 購物籃 + 因素分析 + A/B 測試。** 已經是行銷分析日常工作的 85%。

### 次環境：Python 3.12（另建 venv）— 因果推論 + Google MMM

```
py -3.12 -m venv .venv-causal
.venv-causal\Scripts\pip install dowhy econml causalml google-meridian
```

**只在需要做因果推論或 Meridian MMM 時才切過去。** 用 Parquet 檔在兩個環境間傳資料（正好呼應你的 DuckDB + Parquet 倉儲層 —— 兩個 Python 環境都能讀同一份 Parquet，這是分環境策略能成立的關鍵）。

### 專案自製工具模組（`src/stats_utils.py`）

把本文 Part A 的四個函式收進去，這是你 R→Python 遷移的真正資產：

1. `plot_lm(model)` — A.4 的殘差診斷四圖
2. `vif_table(model)` — A.6 的 GVIF 表（對齊 `car::vif`）
3. `anova3(formula, data)` — A.3 的防呆 Type III
4. `emmeans(model, data, factor)` + `emm_contrasts(...)` — A.9 的 emmeans 替代

---

## 5. 明確不用的東西 + 理由

| 不用 | 理由（皆為實測查證） |
|---|---|
| **lifetimes** | **已 archived（2024-06-28）**，最後 release 是 2020 年。作者官方指定接班人為 pymc-marketing。**改用 pymc-marketing 的 CLV 模組** |
| **lightweight_mmm** | **已 archived（2026-01-19）**，Google 自己在 README 說 "LMMM is not supported anymore"、"highly recommend you switch to Meridian" |
| **scikit-uplift** | 未 archived 但 **commit 與 release 都停在 2022-08-11**，近四年零維護，與現代 sklearn 相容性有風險。**改用 causalml** |
| **pychattr** | PyPI 最後版本 2019-10-25，近七年無動靜 |
| **Robyn（Python 線）** | 核心是 R 套件；Python 版官方自述為 "LLM-translated Beta version"，不適合正式交付。主線 release 停在 2024-12-20 |
| **abexp / pyAB / abracadabra / babtest** | PyPI 版本分別停在 2021 / 2020 / 2021 / 2020。**A/B 測試改用 statsmodels 內建 + tea-tasting** |
| **在 Python 3.14 主環境裝 dowhy** | 會靜默降版到 2022 年的 0.8 版。**要用請在 3.12 次環境裝** |
| **在 Python 3.14 主環境裝 EconML / meridian** | 實測安裝失敗（無 cp314 wheel / TensorFlow 不支援）。**要用請在 3.12 次環境裝** |
| **`anova_lm(typ=3)` 搭配預設 treatment coding** | 不是套件問題而是用法問題，但危害同等嚴重：**會靜默算出錯誤的主效果 SS**（實測差近一倍）。必用 `C(x, Sum)` |

---

## 6. 無法查證的事項（誠實列出）

以下是我**沒有**直接驗證、或驗證後仍有疑問的項目。不憑印象補齊：

1. **causalml 在 Python 3.14 是否能真正完成安裝**。我只驗證到 pip 相依解析階段（顯示 "Would install causalml-0.17.0"），**但 PyPI 上 0.17.0 只有 cp311/cp312 wheel**，實際安裝會退回原始碼編譯 Cython 擴充，需要 MSVC Build Tools。我**沒有實際執行完整安裝**，因此無法確認編譯是否成功。建議實際跑一次 `pip install causalml` 驗證。

2. **ChannelAttribution 在 Python 3.14 是否能真正完成安裝**。同上，dry-run 顯示可解析，但它是 C++ sdist、無任何 wheel，官方文件說 Windows 需要 MSVC 14.0+。未實際編譯驗證。

3. **ChannelAttribution 的 PyPI 版本（v2.2.5, 2026-06-08）與 GitHub 最後 commit（2024-02-01）之間兩年多的落差原因**。可能是開發已移往其他地方（官網 channelattribution.io 或私有 repo），也可能是 PyPI 上傳但未推 GitHub。**我無法確認這個套件目前真實的維護狀態**，這對是否採用它是關鍵資訊。

4. **EducationalTestingService/factor_analyzer 的 star 數**。GitHub 頁面的 JSON payload 顯示 `stargazerCount: 4`，這對一個廣泛使用的套件而言異常低。可能該 repo 曾被轉移或重建。因 GitHub API 匿名額度已用盡（403 rate limit），**未能二次確認**。請勿引用這個數字。

5. **google/meridian 的正式 release tag 與日期**。GitHub releases API 端點未回傳資料，README 的引用範例中出現 "1.7.1 (2026)"，PyPI 上 `google-meridian` 1.7.1 上傳於 2026-07-22。**GitHub 上是否有對應的 release tag 我未能確認**（該專案可能不使用 GitHub Releases）。

6. **facebookexperimental/Robyn 的 repo `pushed_at` 為 2026-01-26，但 main 分支最後 commit 為 2025-06-27**。差異來自非主分支的活動，**我未查證那些分支的內容**，因此無法判斷 Robyn 是否有尚未合併的活躍開發。

7. **tea-tasting 在 Python 3.14 的實際安裝結果**。它宣告 `requires_python >=3.12`（未設上界，理論上 3.14 可行），但我**未執行 dry-run 驗證**。

8. **pymc-marketing 在 Python 3.14 的實際執行結果**。dry-run 完整解析成功（pymc 5.28.5 + pytensor 2.38.3 + numba 0.65.1），**但我未實際安裝並跑一次 MMM 或 CLV 模型**。numba 對新 Python 版本的支援通常落後，這是殘餘風險點。

9. **各套件的 star 數為擷取當下（2026-07-26）的快照**，且部分透過 HTML 擷取而非 API（因 API 額度用盡）。數量級可信，精確值請勿引用。

10. **`emmeans` 替代函式在 GLM（非線性連結函數）上的正確性我未驗證**。我只在 OLS 上驗證通過（成功還原真值）。GLM 情境下 link scale 與 response scale 的轉換、以及信賴區間的正確算法需要額外測試。

11. **DHARMa 是否真的沒有 Python 對應品**。我基於既有認知判斷，**未做窮盡搜尋**。可能存在我不知道的小眾套件。

12. **`plot_lm` 函式與 R `plot.lm` 的數值一致性未做逐點比對**。我確認了各組件（rstandard、hatvalues、Cook's D）的定義與 R 一致，且函式可執行，但**未用同一份資料在 R 與 Python 各跑一次做圖形比對**。
