#!/usr/bin/env python3
"""
統計推論的唯一合法介面 —— type-III ANOVA、事後檢定、效果量、迴歸診斷。

為什麼需要它（四個「不報錯但給錯數字」的地方，靠人記是記不住的）：

  1. **`anova_lm(typ=3)` 配 patsy 預設的 treatment coding 會靜默算錯主效果平方和**
     （18-T3）。實測同一份資料，主效果 SS 從 325.64 掉到 179.76，**少算 45%，
     不拋任何警告**。R 那邊有 `car` 會提醒你，Python 什麼都沒有。所以
     `anova3()` 強制把 `C(x)` 改寫成 `C(x, Sum)`，遇到明寫 treatment 就擋下來。

  1b. **設計降秩（交叉表有空 cell）時 type-III 整張表都是垃圾，一樣不報錯。**
     實測信用卡樣本：刷卡產品產業分類 15 類 × 刷卡地點 2 類，其中 3 類沒有國外列
     → 設計矩陣 30 欄但秩只有 27，`anova_lm(typ=3)` 回傳的表
     **Intercept／兩個主效果／交互作用的 F 全部等於 1.122059、p 全部 0.289509**，
     主效果 SS 與交互作用 SS 一模一樣（22.130189）。statsmodels 只在內部丟一個
     預設會被吞掉的 `ValueWarning`。所以 `anova3()` **事前**驗秩與空 cell、
     **事後**驗平方和分解，任一關沒過就 raise（`RankDeficientDesignError` /
     `SSDoubleCheckError`），不是印個警告讓你自己決定要不要理。要放行必須顯式傳
     `allow_rank_deficient=True`，而且回傳表會被強制加上可見的「警告」欄。
     降級走 `anova_degrade()`（00 §1.6 降級不留空）。

  2. **事後檢定選錯方法會讓型一錯誤失控**（16 §8.4）。常態與變異數同質是兩個
     獨立維度，必須分兩層問；變異數比 ≥ 4 時退 Kruskal-Wallis 是**往假設更強
     的方向橫移**（05 §1.2 實測：ANOVA 實際 α=0.223、KW=0.116、Welch=0.049）。
     `posthoc()` 把整棵決策樹寫死，並回傳 `method_chosen` 與 `why`，讓人事後
     查得到「為什麼是這個方法」。

  3. **只報 p 值是違規**（16 §一）。大樣本端 42 萬列時差 13 元也能 p<0.001，
     小樣本端 n=47 時差 900 元也檢定不出來。`effect_sizes()` 與
     `compare_two_groups()` 一律把 p / 效果量 / 信賴區間三者綁在同一個回傳值裡，
     **不提供只回 p 值的介面**；min(n) < 30 時強制附 MDE。

用法：

    import sys; sys.path.insert(0, "<skill>/scripts")
    from stats_utils import (
        anova3, anova_degrade, design_check, posthoc, effect_sizes,
        compare_two_groups, chi2_safe, plot_lm, vif_table, nested_f,
        emmeans, emm_contrasts, bh_correct,
    )

    tbl = anova3("CAI ~ C(教育程度) * C(性別)", df)     # 自動改寫成 C(x, Sum)
    design_check("CAI ~ C(產業) * C(地點)", df)         # 先看設計矩陣秩與空 cell
    deg = anova_degrade("CAI ~ C(產業) * C(地點)", df)  # 降秩時照 00 §1.6 階梯降級
    ph  = posthoc(df, dv="CAI", group="教育程度")        # 依 16 §8.4 自動選
    es  = effect_sizes(df, dv="CAI", group="性別")       # p + 效果量 + CI 三者並回
    fig = plot_lm(m, project="2026Q3_電商", name="迴歸診斷四圖.png")

自我檢查（三桶 + 退出碼，全庫統一，權威定義見 00 §八）：
    0  = 全通過
    1  = 有 error，不可使用
    2  = 只有 warning，可用但部分路徑要留意
    64 = 用法錯誤（旗標打錯）
    70 = 腳本自身異常

    python stats_utils.py --self-test
    python stats_utils.py --self-test --verbose

實作判斷（reference 沒講到、由本檔決定的部分，逐條標記在對應函式的 docstring）：
  · 本檔是純函式庫，不讀專案資料，**CLI 沒有「專案代號」位置參數**，只有
    `--self-test`。唯一會用到 `paths` 的是 `plot_lm(project=..., name=...)`
    的存檔路徑與中文字型設定。
  · 08 §二 提到的循環相依（`stats_utils` ⇄ `templates/迴歸建模_程式範本.py`）
    在此的解法是：**本檔完全不 import 範本檔**。`influence_flags` /
    `sensitivity` 留在範本檔，不搬過來也不複寫一份（08 §十「兩邊不可分岔」）。
"""

from __future__ import annotations

import itertools
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)
from paths import cfg, project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

__all__ = [
    "RankDeficientDesignError",
    "SSDoubleCheckError",
    "anova3",
    "anova_degrade",
    "bh_correct",
    "chi2_safe",
    "compare_two_groups",
    "design_check",
    "effect_sizes",
    "emm_contrasts",
    "emmeans",
    "mde",
    "nested_f",
    "plot_lm",
    "posthoc",
    "vif_table",
]


class RankDeficientDesignError(ValueError):
    """設計矩陣降秩（多半是交叉表有空 cell）—— type-III 平方和在此無意義。

    繼承 `ValueError` 是為了不打斷既有 `except ValueError` 的呼叫端；
    要精準攔截就直接 except 這個類別。
    """


class SSDoubleCheckError(ValueError):
    """平方和雙路徑驗算未通過（08 §三 硬規則 3）。回傳的表不可採信。"""

# ── 門檻常數（全部有出處，改動要同步改 reference）────────────────
SKEW_LIMIT = 1.0          # 05 §1.1：|skew| >= 1 判高度偏態
LEVENE_ALPHA = 0.05       # 05 §1.2：Levene p > 0.05 為同質
VAR_RATIO_LIMIT = 4.0     # 05 §1.2：最大/最小組變異數比 >= 4 禁行標準 ANOVA
SMALL_N = 30              # 16 §4.1：任一組 n < 30 必須附 MDE
MIN_GROUP_N = 5           # 16 §8.4：某群 n < 5 走降級階梯
GVIF_WATCH = math.sqrt(5)     # 08 §六：GVIF^(1/(2df)) > 2.24 注意
GVIF_ACT = math.sqrt(10)      # 08 §六：> 3.16 要處理
COHEN_D = (0.2, 0.5, 0.8)         # 16 §2.1，Cohen (1988)
COHEN_ETA2 = (0.01, 0.06, 0.14)   # 16 §2.1，Cohen (1988)
CRAMER_V = (0.1, 0.3)             # 16 §2.1，IB5082 §4.8
SS_TOL = 1e-6             # 08 §三：平方和雙路徑驗算容差


# ══════════════════════════════════════════════════════════════
#  一、formula 解析：Sum coding 防呆的核心
# ══════════════════════════════════════════════════════════════
_SAFE_NAMES = {
    "C", "Sum", "Treatment", "Poly", "Diff", "Helmert", "Q", "I",
    "np", "log", "log1p", "log10", "sqrt", "exp", "abs", "center",
    "standardize", "scale", "bs", "cr", "cc", "te", "level", "levels",
    "reference", "True", "False", "None",
}


def _match_paren(s: str, open_idx: int) -> int:
    """回傳與 s[open_idx]（必為 '('）配對的右括號位置。找不到丟 ValueError。"""
    depth = 0
    in_str: str | None = None
    for i in range(open_idx, len(s)):
        ch = s[i]
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in "\"'":
            in_str = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"formula 括號不成對，從第 {open_idx} 個字元起：{s[open_idx:]}")


def _split_top_level(s: str, sep: str = ",") -> list[str]:
    """在深度 0 的位置切開，字串常值內的分隔符不算。"""
    out: list[str] = []
    depth = 0
    in_str: str | None = None
    buf: list[str] = []
    for ch in s:
        if in_str:
            buf.append(ch)
            if ch == in_str:
                in_str = None
            continue
        if ch in "\"'":
            in_str = ch
            buf.append(ch)
        elif ch in "([":
            depth += 1
            buf.append(ch)
        elif ch in ")]":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf))
    return [x.strip() for x in out]


def _find_c_calls(formula: str) -> list[tuple[int, int, str]]:
    """找出所有 C(...) 呼叫，回傳 (起, 迄含右括號的下一位, 括號內文字)。"""
    calls: list[tuple[int, int, str]] = []
    i = 0
    n = len(formula)
    while i < n:
        if formula[i] == "C":
            # 前一個字元不能是識別字元（避免抓到 ABC(...) 這種）
            prev_ok = i == 0 or not (formula[i - 1].isalnum() or formula[i - 1] == "_")
            j = i + 1
            while j < n and formula[j] == " ":
                j += 1
            if prev_ok and j < n and formula[j] == "(":
                close = _match_paren(formula, j)
                calls.append((i, close + 1, formula[j + 1:close]))
                i = close + 1
                continue
        i += 1
    return calls


def _identifiers_outside(formula: str, spans: list[tuple[int, int]]) -> set[str]:
    """回傳不落在 spans（C(...) 區段）內的識別字。用來抓沒包 C() 的類別欄。"""
    import re

    out: set[str] = set()
    for m in re.finditer(r"[A-Za-z_一-鿿][A-Za-z0-9_一-鿿.]*", formula):
        a, b = m.span()
        if any(s <= a and b <= e for s, e in spans):
            continue
        name = m.group(0)
        if name in _SAFE_NAMES or "." in name:
            continue
        out.add(name)
    return out


def force_sum_coding(
    formula: str,
    data: pd.DataFrame | None = None,
    *,
    strict: bool = True,
) -> tuple[str, list[str]]:
    """把 formula 裡的類別項改寫成 sum-to-zero 編碼，回傳 (新 formula, 說明).

    · `C(x)`                    → `C(x, Sum)`
    · `C(x, Sum)`               → 原樣保留
    · `C(x, Treatment(...))` 等 → strict=True 擋下來；strict=False 改寫成 Sum
    · 裸露的字串／類別欄        → 一律擋下來（patsy 會偷偷用 treatment coding）

    這是 `anova3()` 的內臟，單獨開放是為了讓分析腳本能先「看一下會被改成什麼」。
    """
    notes: list[str] = []
    calls = _find_c_calls(formula)
    new = formula
    # 由右往左改寫，才不會動到還沒處理的位移
    for start, end, inner in reversed(calls):
        args = _split_top_level(inner)
        var = args[0].strip()
        if len(args) == 1:
            new = new[:start] + f"C({var}, Sum)" + new[end:]
            notes.append(f"C({var}) → C({var}, Sum)")
            continue
        contrast = args[1].strip()
        if contrast.startswith("Sum"):
            continue
        if strict:
            raise ValueError(
                f"formula 明寫了非 sum-to-zero 的對比編碼：C({var}, {contrast}) —— "
                f"type-III 平方和在 treatment coding 下沒有意義，會靜默算錯"
                f"（18-T3，實測主效果 SS 少算 45%）。\n"
                f"  怎麼辦：改成 C({var}, Sum)；若你真的要 treatment coding，"
                f"那就不要用 type-III，改用 anova_lm(model, typ=2)（08 §三 硬規則 1）；"
                f"確定要讓本函式代為改寫，傳 strict=False。"
            )
        new = new[:start] + f"C({var}, Sum)" + new[end:]
        notes.append(f"C({var}, {contrast}) → C({var}, Sum)（strict=False 代改）")

    if data is not None:
        spans = [(s, e) for s, e, _ in _find_c_calls(new)]
        bare = _identifiers_outside(new, spans)
        offenders = []
        for name in sorted(bare):
            if name not in data.columns:
                continue
            s = data[name]
            if s.dtype == object or isinstance(s.dtype, pd.CategoricalDtype) or s.dtype == bool:
                offenders.append(name)
        if offenders:
            fix = "、".join(f"C({o}, Sum)" for o in offenders)
            raise ValueError(
                f"這些欄是類別型但沒有用 C() 標註：{'、'.join(offenders)} —— "
                f"patsy 會自動當成類別變數並套用 treatment coding，"
                f"type-III 的主效果平方和會靜默算錯（18-T3）。\n"
                f"  怎麼辦：把它們寫成 {fix} 再呼叫一次。"
            )
    return new, notes


def _c_var(factor_name: str) -> str | None:
    """從 patsy 的 factor 名稱（如 `C(a, Sum)`）取回底層欄名 `a`；非 C() 回 None。"""
    calls = _find_c_calls(factor_name)
    if not calls:
        return None
    start, end, inner = calls[0]
    if start != 0 or end != len(factor_name):
        return None
    return _split_top_level(inner)[0].strip()


def design_check(
    formula: str,
    data: pd.DataFrame,
    *,
    strict: bool = True,
    min_cell: int = MIN_GROUP_N,
) -> dict[str, Any]:
    """**跑 ANOVA 之前**先驗設計矩陣：秩夠不夠、交叉表有沒有空 cell。

    為什麼要事前擋：空 cell 讓 type-III 的對比矩陣降秩，`anova_lm(typ=3)` 不會
    報錯，只會回一張**每一列 F 與 p 都相同、主效果 SS 等於交互作用 SS** 的表
    （實測：信用卡 15 類 × 2 地點，3 個空 cell，全表 F=1.122059、p=0.289509）。
    statsmodels 只在 `wald_test` 內部丟一個 `ValueWarning`，預設會被吞掉。

    回傳 dict：
      formula_used   改寫成 Sum coding 後的 formula
      n_cols/rank    設計矩陣欄數與實際秩
      deficiency     n_cols - rank（0 代表滿秩）
      rank_deficient bool
      empty_cells    [{"term":…, "factors":[…], "cells":[(水準…)…], "n_empty":…}]
      thin_cells     同上，但是 0 < n < min_cell 的細瘦 cell（只警告，不擋）
      cross_tabs     {term: 交叉表 DataFrame}，給降級時挑要合併的水準用
      reason         人看的一句話

    實作判斷（reference 未規定）：秩用 `np.linalg.matrix_rank(exog)` 算，
    因為 `smf.ols(...)` 未 `.fit()` 前 `mod.rank` 是 None。
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data 必須是 pandas.DataFrame —— 先把資料讀成 DataFrame 再進來。")

    used, _ = force_sum_coding(formula, data, strict=strict)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mod = smf.ols(used, data=data, missing="drop")

    X = np.asarray(mod.exog, dtype=float)
    n_cols = int(X.shape[1])
    rank = int(np.linalg.matrix_rank(X)) if X.size else 0

    try:
        used_rows = data.loc[mod.data.row_labels]
    except Exception:  # noqa: BLE001
        used_rows = data

    empty_cells: list[dict[str, Any]] = []
    thin_cells: list[dict[str, Any]] = []
    cross_tabs: dict[str, pd.DataFrame] = {}
    try:
        terms = list(mod.data.design_info.terms)
    except Exception:  # noqa: BLE001
        terms = []
    for term in terms:
        names = [_c_var(f.name()) for f in term.factors]
        if len(names) < 2 or any(v is None or v not in used_rows.columns for v in names):
            continue
        cols = [used_rows[v] for v in names]  # type: ignore[index]
        ct = pd.crosstab(cols[0], cols[1:] if len(cols) > 2 else cols[1])
        cross_tabs[term.name()] = ct
        arr = ct.to_numpy()
        empt: list[tuple] = []
        thin: list[tuple] = []
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                combo = (ct.index[i], ct.columns[j])
                if arr[i, j] == 0:
                    empt.append(combo)
                elif arr[i, j] < min_cell:
                    thin.append(combo)
        if empt:
            empty_cells.append({"term": term.name(), "factors": names,
                                "cells": empt, "n_empty": len(empt)})
        if thin:
            thin_cells.append({"term": term.name(), "factors": names,
                               "cells": thin, "n_thin": len(thin)})

    deficiency = n_cols - rank
    bits = []
    if deficiency:
        bits.append(f"設計矩陣降秩：{n_cols} 欄但秩只有 {rank}（少 {deficiency}）")
    if empty_cells:
        tot = sum(e["n_empty"] for e in empty_cells)
        bits.append(f"交叉表有 {tot} 個空 cell")
    return {
        "formula_in": formula,
        "formula_used": used,
        "n_cols": n_cols,
        "rank": rank,
        "deficiency": deficiency,
        "rank_deficient": bool(deficiency > 0 or empty_cells),
        "empty_cells": empty_cells,
        "thin_cells": thin_cells,
        "cross_tabs": cross_tabs,
        "min_cell": min_cell,
        "n": int(X.shape[0]),
        "reason": "；".join(bits) if bits else "滿秩、無空 cell",
    }


def _fmt_cells(empty_cells: list[dict[str, Any]], limit: int = 12) -> str:
    """把空 cell 列表排成人看得懂的多行字串。"""
    lines = []
    for e in empty_cells:
        head = " × ".join(str(f) for f in e["factors"])
        lines.append(f"    · {e['term']}（{head}）缺 {e['n_empty']} 格：")
        for combo in e["cells"][:limit]:
            lines.append("        - " + " × ".join(str(c) for c in combo))
        if e["n_empty"] > limit:
            lines.append(f"        - …其餘 {e['n_empty'] - limit} 格省略")
    return "\n".join(lines)


def _rank_deficient_message(diag: dict[str, Any], check: dict[str, Any] | None = None) -> str:
    """統一的錯誤訊息：哪個設計降秩、差多少、該怎麼辦。"""
    msg = [
        f"設計降秩，type-III 平方和不可用 —— formula={diag['formula_used']!r}，n={diag['n']}。",
        f"  症狀：{diag['reason']}。",
    ]
    if diag["empty_cells"]:
        msg.append("  空 cell（這些組合完全沒有觀測值）：")
        msg.append(_fmt_cells(diag["empty_cells"]))
    if check is not None and check.get("passed") is False:
        msg.append(
            f"  平方和雙路徑驗算未通過：Type I 逐項和 {check.get('ss_model_plus_resid'):.6f} "
            f"vs 總平方和 {check.get('ss_total'):.6f}，{check.get('reason')}"
            f"（08 §三 硬規則 3，容差 {SS_TOL}）。"
        )
    msg.append(
        "  為什麼一定要擋：對比矩陣降秩時 anova_lm(typ=3) 不會報錯，只會回一張"
        "每一列 F 與 p 都相同、主效果 SS 等於交互作用 SS 的表 —— 那是垃圾，不是結果。"
    )
    msg.append(
        "  怎麼辦（00 §1.6 降級不留空，階梯由前提多到少）：\n"
        "    ① 合併稀有水準讓每個 cell 都有觀測 → 保住全因子 type-III\n"
        "    ② 拿掉交互項，改用可估的主效果模型 + Type II（08 §三 硬規則 1 本來就要你優先用 Type II）\n"
        "    ③ 退成單因子 ANOVA + 事後檢定，交互作用不主張\n"
        "    ④ 退到底就報 cell 平均數對照表，並明說「本節無法主張交互作用」\n"
        "    一行做完：anova_degrade(formula, data) 會照這個階梯往下試並回傳降級紀錄；\n"
        "    真的要看那張不可信的表，顯式傳 allow_rank_deficient=True（回傳表會帶「警告」欄）。"
    )
    return "\n".join(msg)


def _ss_double_check(model: Any) -> dict[str, Any]:
    """雙路徑驗算：Type I 平方和逐項相加 + 殘差 SS 應等於總 SS（08 §三 硬規則 3）。

    type-III 的平方和本身不會加總成 SS_total（那是設計使然，不是錯），
    所以驗算改跑同一個模型的序列型分解 —— 它是恆等式，不成立就是資料或程式錯了。
    """
    out: dict[str, Any] = {"passed": None, "reason": ""}
    try:
        # 有沒有「顯式」的 Intercept 項決定 anova_lm(typ=1) 加總到哪個總平方和。
        # 不能只看 k_constant：`y ~ 0 + C(g, Sum)` 展開成滿格 dummy 時，欄空間本身
        # 就含常數，statsmodels 會把 k_constant 判成 1，但 Type I 逐項和加總到的是
        # **未置中**的總平方和（實測 830.664664 vs centered_tss 733.558331）。
        # 舊版在這裡誤判成驗算失敗，只是印個 stderr 所以沒人發現；現在會 raise，
        # 所以必須挑對比較對象。
        try:
            has_intercept = any(t.name() == "Intercept"
                                for t in model.model.data.design_info.terms)
        except Exception:  # noqa: BLE001
            has_intercept = bool(getattr(model.model, "k_constant", 0))
        t1 = anova_lm(model, typ=1)
        ss_sum = float(t1["sum_sq"].sum())          # 已含 Residual 列
        ss_total = (float(model.centered_tss) if has_intercept
                    else float(np.sum(np.asarray(model.model.endog) ** 2)))
        out["ss_total_kind"] = "centered_tss" if has_intercept else "uncentered_tss（無顯式截距）"
        gap = abs(ss_sum - ss_total)
        tol = SS_TOL * max(1.0, abs(ss_total))
        out.update(
            passed=bool(gap <= tol),
            ss_model_plus_resid=ss_sum,
            ss_total=ss_total,
            abs_gap=gap,
            tol=tol,
            reason="" if gap <= tol else f"差 {gap:.6g} > 容差 {tol:.6g}",
        )
    except Exception as e:  # noqa: BLE001
        out["reason"] = f"驗算過程異常：{e!r}"
    return out


def anova3(
    formula: str,
    data: pd.DataFrame,
    *,
    strict: bool = True,
    verbose: bool = True,
    cov_type: str | None = None,
    cov_kwds: dict | None = None,
    allow_rank_deficient: bool = False,
    min_cell: int = MIN_GROUP_N,
) -> pd.DataFrame:
    """強制 sum-to-zero 編碼的 Type III ANOVA，等同 R 的 `car::Anova(m, type=3)` + `contr.sum`。

    **直接呼叫 `anova_lm(typ=3)` 會靜默算錯主效果平方和**（18-T3；實測 a 的 SS
    179.76 vs 325.64，少算 45%，不報錯），所以專案內一律走這支，不准繞過。

    **第二個靜默錯誤：設計降秩。** 交叉表只要有一格沒觀測值，type-III 的對比矩陣
    就降秩，`anova_lm(typ=3)` 照樣回一張表 —— 每一列 F 與 p 都相同、主效果 SS
    等於交互作用 SS（實測：信用卡 15 類 × 2 地點、3 個空 cell，全表
    F=1.122059、p=0.289509）。本函式**事前**驗設計矩陣的秩與空 cell，
    **事後**驗平方和分解，任一關沒過就 raise，不是印個警告讓你自己決定要不要理。

    參數
      formula   patsy formula。類別項寫 `C(x)` 即可，本函式會改寫成 `C(x, Sum)`
      data      DataFrame
      strict    True（預設）遇到明寫 treatment/poly 編碼就擋下來；False 代為改寫
      verbose   改寫或細瘦 cell 等非致命狀況時印訊息到 stderr
      cov_type  傳給 `.fit()` 的穩健標準誤（如 "HC3"）。注意：**anova_lm 的
                type-III 表在穩健共變異數下仍以平方和呈現**，要報穩健檢定請看
                回傳表 attrs 裡的 model 自行 `wald_test_terms()`（實作判斷）
      allow_rank_deficient
                預設 False：降秩或平方和驗算失敗一律 raise。傳 True 才放行，
                此時回傳表**強制帶一個可見的「警告」欄**，且 attrs["可信"]=False
      min_cell  cell 樣本數低於此值只警告不擋（預設 16 §8.4 的 MIN_GROUP_N=5）

    例外
      RankDeficientDesignError  設計降秩（含空 cell）且未顯式放行
      SSDoubleCheckError        平方和雙路徑驗算未通過且未顯式放行
      ValueError                formula 用了非 sum-to-zero 編碼／裸露類別欄

    回傳
      DataFrame（sum_sq / df / F / PR(>F) / eta_sq / partial_eta_sq；
      放行降秩時另加「警告」欄），並在 `.attrs` 帶：
        formula_in、formula_used、rewrites、model、ss_check、n、
        rank_check、可信、warnings

    效果量欄是本檔加的（16 §一：只報 p 是違規）：
      eta_sq         = SS_effect / SS_total（SS_total 用 model.centered_tss）
      partial_eta_sq = SS_effect / (SS_effect + SS_residual)   ← 16 §2.2(a)：
                       多因子時兩者不相等，且 partial 加總可以超過 1，報告只寫一種
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("data 必須是 pandas.DataFrame —— 先把資料讀成 DataFrame 再進來。")

    used, notes = force_sum_coding(formula, data, strict=strict)
    if notes and verbose:
        print(f"⚠ anova3 已改寫 formula（18-T3 防呆）：{'；'.join(notes)}", file=sys.stderr)

    # ① 事前：設計矩陣的秩與空 cell —— 降秩就不要跑，跑了也只會拿到垃圾
    diag = design_check(formula, data, strict=strict, min_cell=min_cell)
    warn_msgs: list[str] = []
    if diag["rank_deficient"]:
        if not allow_rank_deficient:
            raise RankDeficientDesignError(_rank_deficient_message(diag))
        warn_msgs.append(
            f"設計降秩（{diag['reason']}）；type-III 主效果與交互作用 SS 不可解讀，"
            f"由 allow_rank_deficient=True 顯式放行"
        )
    if diag["thin_cells"] and verbose:
        tot = sum(t["n_thin"] for t in diag["thin_cells"])
        print(f"⚠ anova3：有 {tot} 個 cell 的 n < {min_cell}（16 §8.4），"
              f"主效果估計不穩，考慮先合併稀有水準。", file=sys.stderr)

    fit_kw: dict[str, Any] = {}
    if cov_type:
        fit_kw["cov_type"] = cov_type
        if cov_kwds:
            fit_kw["cov_kwds"] = cov_kwds
    model = smf.ols(used, data=data, missing="drop").fit(**fit_kw)

    tbl = anova_lm(model, typ=3)
    ss_resid = float(tbl.loc["Residual", "sum_sq"])
    ss_total = float(model.centered_tss) if getattr(model.model, "k_constant", 0) else float(
        np.sum(np.asarray(model.model.endog) ** 2)
    )
    tbl = tbl.copy()
    tbl["eta_sq"] = tbl["sum_sq"] / ss_total
    tbl["partial_eta_sq"] = tbl["sum_sq"] / (tbl["sum_sq"] + ss_resid)
    for col in ("eta_sq", "partial_eta_sq"):
        tbl.loc["Residual", col] = np.nan
        if "Intercept" in tbl.index:
            tbl.loc["Intercept", col] = np.nan

    # ② 事後：平方和雙路徑驗算（08 §三 硬規則 3）—— 失敗一律 raise，不是印警告
    check = _ss_double_check(model)
    if check.get("passed") is False:
        if not allow_rank_deficient:
            if diag["rank_deficient"]:
                raise RankDeficientDesignError(_rank_deficient_message(diag, check))
            raise SSDoubleCheckError(
                f"平方和雙路徑驗算未通過 —— formula={used!r}，n={int(model.nobs)}。\n"
                f"  Type I 逐項和 {check.get('ss_model_plus_resid'):.6f} "
                f"vs 總平方和 {check.get('ss_total'):.6f}，{check.get('reason')}"
                f"（08 §三 硬規則 3 要求在 {SS_TOL} 相對容差內相等）。\n"
                f"  設計矩陣本身是滿秩的（{diag['n_cols']} 欄／秩 {diag['rank']}），"
                f"所以不是空 cell 造成的。\n"
                f"  怎麼辦：檢查資料是否有 NaN 被部分丟棄（本函式用 missing=\"drop\"）、"
                f"formula 是否含權重或穩健設定、y 是否有 inf。\n"
                f"  確定要看這張不可信的表，顯式傳 allow_rank_deficient=True。"
            )
        warn_msgs.append(f"平方和雙路徑驗算未通過（{check['reason']}），SS 分解不成立")

    if warn_msgs:
        text = "；".join(warn_msgs)
        tbl["警告"] = text          # 可見欄，不是只有 attrs 裡的暗號
        if verbose:
            print(f"⚠ anova3 放行了不可信的結果：{text}", file=sys.stderr)

    tbl.attrs.update(
        formula_in=formula,
        formula_used=used,
        rewrites=notes,
        model=model,
        ss_check=check,
        rank_check={k: v for k, v in diag.items() if k != "cross_tabs"},
        n=int(model.nobs),
        警告=warn_msgs,
        可信=not warn_msgs,
    )
    return tbl


def _drop_interactions(formula: str) -> str:
    """把 `y ~ C(a)*C(b) + x` 化成只剩主效果的加法式。找不到類別項就原樣回傳。"""
    if "~" not in formula:
        return formula
    lhs, rhs = formula.split("~", 1)
    spans = _find_c_calls(rhs)
    masked = list(rhs)
    for s, e, _ in spans:                      # 先把 C(...) 內部遮掉，避免切到括號裡的逗號
        for i in range(s, e):
            masked[i] = "\x00"
    masked_s = "".join(masked)

    spans_top: list[tuple[int, int]] = []      # 頂層以 '+' 切開的項，記位移不記字串
    depth = 0
    cur = 0
    for i, ch in enumerate(masked_s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "+" and depth == 0:
            spans_top.append((cur, i))
            cur = i + 1
    spans_top.append((cur, len(masked_s)))

    out: list[str] = []
    for a, b in spans_top:
        raw, mask = rhs[a:b], masked_s[a:b]
        if "*" in mask:                        # a*b → 拆成 a + b（保住主效果）
            cuts, d, c0 = [], 0, 0
            for i, ch in enumerate(mask):
                if ch == "(":
                    d += 1
                elif ch == ")":
                    d -= 1
                elif ch in "*:" and d == 0:
                    cuts.append(raw[c0:i])
                    c0 = i + 1
            cuts.append(raw[c0:])
            out.extend(s.strip() for s in cuts if s.strip())
            continue
        if ":" in mask:                        # 純交互項沒有主效果可留，整項丟掉
            continue
        if raw.strip():
            out.append(raw.strip())
    seen: list[str] = []
    for t in out:
        if t not in seen:
            seen.append(t)
    return f"{lhs.strip()} ~ " + " + ".join(seen) if seen else formula


def anova_degrade(
    formula: str,
    data: pd.DataFrame,
    *,
    strict: bool = True,
    min_cell: int = MIN_GROUP_N,
    verbose: bool = True,
) -> dict[str, Any]:
    """設計降秩時的降級階梯（00 §1.6「降級不留空」）—— 一路往下試，回傳降級紀錄。

    階梯（左 → 右＝前提由多到少，只准退一格）：

        ① 全因子 Type III（原方法）
        ② 合併稀有水準（造成 cell n < min_cell 的水準併成「其他(合併)」）後
           重跑全因子 Type III —— 保住交互作用，但水準意義變粗
        ③ 拿掉交互項，主效果模型 + **Type II**
           （08 §三 硬規則 1 本來就說無交互時預設用 Type II，且不受編碼影響）
        ④ 退成單因子 ANOVA + 事後檢定（16 §8.4 的 posthoc），交互作用不主張
        ⑤ 退到底：cell 平均數對照表，明說「本節無法主張任何組間差異」

    ⚠ 為什麼階梯 ③ 不是「同一個降秩模型改跑 Type II」：實測那樣會回**負的平方和**
    （C(a) SS = −0.003035、C(b) SS = −0.009980），一樣是垃圾。必須先把交互項拿掉
    讓設計回到滿秩，Type II 才有意義。

    回傳 dict，欄位對齊 00 §1.6 的 `執行紀錄/degradation_log.md` 表：
      階梯、原方法、失效證據、降級路徑、實際採用、結論弱在哪、
      table（結果表或 None）、posthoc（階梯④才有）、data_used（階梯②才有）、
      rank_check、ladder_log（每一格試了什麼、為什麼失敗）

    實作判斷（reference 只給階梯精神，沒指定合併規則）：階梯②合併的是
    **交互項裡水準數最多的那個因子**，把所有參與 n < min_cell 之 cell 的水準
    併成單一「其他(合併)」；合併後仍降秩就往 ③ 走。
    """
    log: list[str] = []
    diag = design_check(formula, data, strict=strict, min_cell=min_cell)
    base = {
        "原方法": f"全因子 Type III ANOVA（{diag['formula_used']}）",
        "失效證據": diag["reason"],
        "rank_check": {k: v for k, v in diag.items() if k != "cross_tabs"},
    }

    # ── 階梯①：本來就沒問題就直接跑，不叫降級 ───────────────────
    if not diag["rank_deficient"]:
        tbl = anova3(formula, data, strict=strict, verbose=verbose, min_cell=min_cell)
        return {**base, "階梯": 1, "降級路徑": "（未降級）", "實際採用": "全因子 Type III",
                "結論弱在哪": "無", "table": tbl, "posthoc": None, "data_used": None,
                "ladder_log": ["① 設計滿秩、無空 cell，照原方法跑"]}

    log.append(f"① 全因子 Type III：擋下 —— {diag['reason']}")
    if diag["empty_cells"]:
        log.append("   空 cell：\n" + _fmt_cells(diag["empty_cells"]))

    # ── 階梯②：合併稀有水準 ────────────────────────────────────
    merged: pd.DataFrame | None = None
    merge_note = ""
    for term_name, ct in diag["cross_tabs"].items():
        arr = ct.to_numpy()
        rows_bad = [ct.index[i] for i in range(arr.shape[0]) if (arr[i] < min_cell).any()]
        cols_bad = [ct.columns[j] for j in range(arr.shape[1]) if (arr[:, j] < min_cell).any()]
        ent = next((e for e in diag["empty_cells"] if e["term"] == term_name), None)
        if ent is None:
            continue
        f_row, f_col = ent["factors"][0], ent["factors"][1]
        # 併水準數多的那一邊，才不會把二分類因子整個併掉
        if len(ct.index) >= len(ct.columns):
            col, bad = f_row, rows_bad
        else:
            col, bad = f_col, cols_bad
        if len(bad) < 2:
            log.append(f"② 合併稀有水準：跳過 —— {col} 只有 {len(bad)} 個水準要併，併不出東西")
            continue
        merged = (merged if merged is not None else data).copy()
        merged[col] = merged[col].astype(object).where(~merged[col].isin(bad), "其他(合併)")
        merge_note = (f"{col}：把 {len(bad)} 個水準（{'、'.join(map(str, bad[:6]))}"
                      f"{'…' if len(bad) > 6 else ''}）併成「其他(合併)」")
        log.append(f"② 合併稀有水準 → {merge_note}")

    if merged is not None:
        d2 = design_check(formula, merged, strict=strict, min_cell=min_cell)
        if not d2["rank_deficient"]:
            tbl = anova3(formula, merged, strict=strict, verbose=verbose, min_cell=min_cell)
            log.append(f"② 合併後滿秩（{d2['n_cols']} 欄／秩 {d2['rank']}），全因子 Type III 通過")
            weak = "被併掉的水準只能整團解讀，不能再對個別水準下結論"
            if d2["thin_cells"]:
                thin = "、".join(" × ".join(map(str, c))
                                 for t in d2["thin_cells"] for c in t["cells"])
                weak += f"；且仍有 n < {min_cell} 的 cell（{thin}），該格的交互作用估計不穩"
            if verbose:
                print("\n".join(log), file=sys.stderr)
            return {**base, "階梯": 2,
                    "降級路徑": "全因子 Type III →（合併稀有水準）→ 全因子 Type III",
                    "實際採用": f"合併稀有水準後的全因子 Type III；{merge_note}",
                    "結論弱在哪": weak,
                    "table": tbl, "posthoc": None, "data_used": merged,
                    "ladder_log": log}
        log.append(f"② 合併後仍降秩（{d2['reason']}），繼續往下退")

    # ── 階梯③：拿掉交互項 + Type II ────────────────────────────
    add_formula = _drop_interactions(formula)
    if add_formula != formula:
        add_used, _ = force_sum_coding(add_formula, data, strict=strict)
        d3 = design_check(add_formula, data, strict=strict, min_cell=min_cell)
        if not d3["rank_deficient"]:
            model = smf.ols(add_used, data=data, missing="drop").fit()
            chk = _ss_double_check(model)
            if chk.get("passed") is not False:
                tbl = anova_lm(model, typ=2).copy()
                ss_resid = float(tbl.loc["Residual", "sum_sq"])
                ss_total = float(model.centered_tss)
                tbl["eta_sq"] = tbl["sum_sq"] / ss_total
                tbl["partial_eta_sq"] = tbl["sum_sq"] / (tbl["sum_sq"] + ss_resid)
                for c in ("eta_sq", "partial_eta_sq"):
                    tbl.loc["Residual", c] = np.nan
                tbl.attrs.update(formula_in=formula, formula_used=add_used, model=model,
                                 ss_check=chk, n=int(model.nobs), typ=2,
                                 rank_check={k: v for k, v in d3.items() if k != "cross_tabs"},
                                 可信=True)
                log.append(f"③ 拿掉交互項 → {add_used}，滿秩（{d3['n_cols']} 欄／秩 {d3['rank']}），"
                           f"Type II 通過（SS 驗算差 {chk.get('abs_gap', 0):.3g}）")
                if verbose:
                    print("\n".join(log), file=sys.stderr)
                return {**base, "階梯": 3,
                        "降級路徑": "全因子 Type III → 主效果模型 + Type II",
                        "實際採用": f"anova_lm(typ=2) on {add_used}",
                        "結論弱在哪": "只能主張主效果，**不能主張交互作用**"
                                    "（空 cell 讓交互項不可估，不是「檢定不顯著」）",
                        "table": tbl, "posthoc": None, "data_used": None,
                        "ladder_log": log}
            log.append(f"③ 主效果模型的 SS 驗算沒過（{chk.get('reason')}），繼續往下退")
        else:
            log.append(f"③ 主效果模型仍降秩（{d3['reason']}），繼續往下退")

    # ── 階梯④：單因子 ANOVA + 事後檢定 ──────────────────────────
    dv = formula.split("~", 1)[0].strip()
    factors = [v for v in (_c_var(f"C({inner})") for _, _, inner in _find_c_calls(formula))
               if v and v in data.columns]
    seen_f: list[str] = []
    for f in factors:
        if f not in seen_f:
            seen_f.append(f)
    one: dict[str, Any] = {}
    for f in seen_f:
        try:
            sub = data[[dv, f]].dropna()
            one[f] = {
                "anova": anova3(f"{dv} ~ C({f})", sub, strict=strict,
                                verbose=False, min_cell=min_cell),
                "posthoc": posthoc(sub, dv=dv, group=f),
            }
        except Exception as e:  # noqa: BLE001
            one[f] = {"error": repr(e)}
    ok = [f for f, r in one.items() if "error" not in r]
    if ok:
        log.append(f"④ 退成單因子 ANOVA + 事後檢定：{'、'.join(ok)} 各跑一次，交互作用不主張")
        if verbose:
            print("\n".join(log), file=sys.stderr)
        return {**base, "階梯": 4,
                "降級路徑": "全因子 Type III → 主效果模型 + Type II → 單因子 ANOVA + 事後檢定",
                "實際採用": f"對 {'、'.join(ok)} 各跑一次單因子 ANOVA，事後檢定依 16 §8.4 自動選",
                "結論弱在哪": "各因子各自解讀，不能主張任一因子的效果在另一因子的水準間不同",
                "table": {f: one[f]["anova"] for f in ok},
                "posthoc": {f: one[f]["posthoc"] for f in ok},
                "data_used": None, "ladder_log": log}

    # ── 階梯⑤：敘述統計對照表，章節保留（18-E11 不准刪章）────────
    cells = list(diag["cross_tabs"].values())
    desc = None
    if seen_f:
        try:
            desc = data.groupby(seen_f, dropna=False)[dv].agg(["count", "mean", "median", "std"])
        except Exception:  # noqa: BLE001
            desc = None
    log.append("⑤ 退到底：只報 cell 平均數對照表，本節無法主張任何組間差異")
    if verbose:
        print("\n".join(log), file=sys.stderr)
    return {**base, "階梯": 5,
            "降級路徑": "全因子 Type III → Type II → 單因子 ANOVA → 敘述統計對照表",
            "實際採用": "cell 平均數／中位數／n 對照表",
            "結論弱在哪": "完全不能做推論；章節保留但要明說「本節無法主張組間差異」（18-E11）",
            "table": desc if desc is not None else (cells[0] if cells else None),
            "posthoc": None, "data_used": None, "ladder_log": log}


# ══════════════════════════════════════════════════════════════
#  二、迴歸診斷：plot_lm / vif_table / nested_f
# ══════════════════════════════════════════════════════════════
def _apply_cjk_font() -> None:
    """讓中文標籤不變豆腐字。字型名稱從 config.yml 讀，不寫死。"""
    try:
        import matplotlib as mpl

        want = [str(cfg("字型.中文", "Microsoft JhengHei")),
                str(cfg("字型.對外散布備援", "Noto Sans TC"))]
        cur = list(mpl.rcParams.get("font.sans-serif", []))
        mpl.rcParams["font.sans-serif"] = want + [c for c in cur if c not in want]
        mpl.rcParams["axes.unicode_minus"] = False
    except Exception:  # noqa: BLE001
        pass


def plot_lm(
    model: Any,
    *,
    figsize: tuple[float, float] = (11.0, 9.0),
    n_label: int = 3,
    project: str | None = None,
    name: str | None = None,
    save_to: str | Path | None = None,
    dpi: int = 150,
):
    """等價於 R 的 `plot(lm)`：四張標準診斷圖。Python 沒有一行指令版，只能自己畫。

    四張圖與 R 的對齊細節（抄錯這三處就不是 R 的圖了，08 §4.1）：
      (1) Residuals vs Fitted 用**原始殘差**，不是標準化殘差
      (2) Residuals vs Leverage 的 x 軸是 leverage、y 軸是標準化殘差，
          Cook 等高線 = sqrt(c·p·(1−h)/h)，**p 含截距**
      (3) lowess 的 frac 要顯式寫 2/3 才會和 R 的紅線一致

    參數
      project/name  兩者都給時存到 `<專案>/圖表/迴歸診斷/<name>`（路徑走 paths，不寫死）
      save_to       直接指定完整路徑，優先於 project/name

    回傳 matplotlib Figure。GLM 不要直接套這四張圖 —— 第 1 圖要改成
    deviance residual vs linear predictor（08 §五；`DHARMa` 無 Python 對應品）。
    """
    import matplotlib
    if matplotlib.get_backend().lower() not in ("agg",) and (save_to or project):
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from statsmodels.nonparametric.smoothers_lowess import lowess

    _apply_cjk_font()

    inf = model.get_influence()
    fitted = np.asarray(model.fittedvalues, dtype=float)
    resid = np.asarray(model.resid, dtype=float)
    std_r = np.asarray(inf.resid_studentized_internal, dtype=float)
    lev = np.asarray(inf.hat_matrix_diag, dtype=float)
    cook = np.asarray(inf.cooks_distance[0], dtype=float)
    p = int(model.df_model) + 1
    labels = list(getattr(model.model.data, "row_labels", range(len(resid))))

    fig, ax = plt.subplots(2, 2, figsize=figsize)

    # (1) Residuals vs Fitted —— 線性與等變異
    a = ax[0, 0]
    a.scatter(fitted, resid, s=14, alpha=0.6, edgecolor="none")
    lo = lowess(resid, fitted, frac=2 / 3, return_sorted=True)
    a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    a.axhline(0, ls=":", c="grey")
    a.set_xlabel("Fitted values")
    a.set_ylabel("Residuals")
    a.set_title("Residuals vs Fitted")
    for i in np.argsort(np.abs(resid))[-n_label:]:
        a.annotate(str(labels[i]), (fitted[i], resid[i]), fontsize=8)

    # (2) Normal Q-Q —— 常態性
    a = ax[0, 1]
    (osm, osr), (slope, inter, _) = st.probplot(std_r, dist="norm")
    a.scatter(osm, osr, s=14, alpha=0.6, edgecolor="none")
    a.plot(osm, slope * osm + inter, color="crimson", lw=1.2, ls="--")
    a.set_xlabel("Theoretical Quantiles")
    a.set_ylabel("Standardized residuals")
    a.set_title("Normal Q-Q")

    # (3) Scale-Location —— 對變異數更敏感
    a = ax[1, 0]
    srs = np.sqrt(np.abs(std_r))
    a.scatter(fitted, srs, s=14, alpha=0.6, edgecolor="none")
    lo = lowess(srs, fitted, frac=2 / 3, return_sorted=True)
    a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    a.set_xlabel("Fitted values")
    a.set_ylabel(r"$\sqrt{|Standardized\ residuals|}$")
    a.set_title("Scale-Location")

    # (4) Residuals vs Leverage + Cook's D 等高線
    a = ax[1, 1]
    a.scatter(lev, std_r, s=14, alpha=0.6, edgecolor="none")
    if np.ptp(lev) > 0:
        lo = lowess(std_r, lev, frac=2 / 3, return_sorted=True)
        a.plot(lo[:, 0], lo[:, 1], color="crimson", lw=1.4)
    xs = np.linspace(1e-6, float(np.max(lev)) * 1.05, 200)
    for c, ls in ((0.5, "--"), (1.0, ":")):
        band = np.sqrt(np.clip(c * p * (1 - xs) / xs, 0, None))
        a.plot(xs, band, ls=ls, c="grey", lw=1)
        a.plot(xs, -band, ls=ls, c="grey", lw=1)
        a.annotate(f"Cook's D = {c}", (xs[-1], band[-1]), fontsize=7, color="grey",
                   ha="right", va="bottom")
    a.set_ylim(float(np.min(std_r)) * 1.3 - 0.5, float(np.max(std_r)) * 1.3 + 0.5)
    a.axhline(0, ls=":", c="grey")
    a.set_xlabel("Leverage")
    a.set_ylabel("Standardized residuals")
    a.set_title("Residuals vs Leverage")
    for i in np.argsort(cook)[-n_label:]:
        a.annotate(str(labels[i]), (lev[i], std_r[i]), fontsize=8, color="crimson")

    fig.tight_layout()

    out: Path | None = None
    if save_to:
        out = Path(save_to)
    elif project and name:
        out = project_dir(project).figure("迴歸診斷", name)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        fig.saved_path = out  # type: ignore[attr-defined]
    return fig


def vif_table(model: Any) -> pd.DataFrame:
    """GVIF 表，對齊 R 的 `car::vif()`。連續變數給 VIF，多自由度類別項給 GVIF。

    statsmodels 的 `variance_inflation_factor` 有兩個坑（08 §六）：
      坑 1 要自己迴圈，而且會把截距欄一起算（那格的數字沒有意義）
      坑 2 對類別變數算的是「每個 dummy 欄」的 VIF，R 給的是整項的 GVIF

    判讀門檻與 R 一致：`GVIF^(1/(2df))` > √5≈2.24 注意、> √10≈3.16 要處理。
    欄位：term / df / GVIF / GVIF^(1/(2df)) / 判定
    """
    X = pd.DataFrame(model.model.exog, columns=list(model.model.exog_names))
    Xn = X.drop(columns=[c for c in X.columns if c.lower() == "intercept"])
    if Xn.shape[1] == 0:
        raise ValueError(
            "模型只有截距，沒有可算 VIF 的項 —— 共線性是「解釋變數之間」的事。"
            "怎麼辦：至少放一個解釋變數再算。"
        )
    if Xn.shape[1] == 1:
        return pd.DataFrame([{
            "term": Xn.columns[0], "df": 1, "GVIF": 1.0,
            "GVIF^(1/(2df))": 1.0, "判定": "✅ 單一解釋變數，無共線性可言",
        }])

    di = model.model.data.design_info
    R = np.corrcoef(Xn.values, rowvar=False)
    detR = float(np.linalg.det(R))
    if not np.isfinite(detR) or abs(detR) < 1e-300:
        raise ValueError(
            "設計矩陣的相關矩陣是奇異的（行列式≈0）—— 這通常不是共線性，"
            "是欄位重複或 dummy trap（08 §六：VIF=∞ 那一格）。\n"
            "  怎麼辦：回 M1 檢查是否有兩欄內容相同、或類別變數被同時放進 dummy 與原欄。"
        )

    rows = []
    for term, slc in di.term_name_slices.items():
        if term == "Intercept":
            continue
        cols = [c for c in di.column_names[slc] if c in Xn.columns]
        if not cols:
            continue
        idx = [Xn.columns.get_loc(c) for c in cols]
        keep = [i for i in range(Xn.shape[1]) if i not in idx]
        if not keep:
            gvif = 1.0
        else:
            gvif = float(
                np.linalg.det(R[np.ix_(idx, idx)])
                * np.linalg.det(R[np.ix_(keep, keep)])
                / detR
            )
        dfree = len(idx)
        scaled = gvif ** (1 / (2 * dfree)) if gvif > 0 else float("nan")
        if not np.isfinite(scaled):
            verdict = "⛔ 算不出來（GVIF ≤ 0），檢查欄位是否重複"
        elif scaled > GVIF_ACT:
            verdict = "⛔ > 3.16，禁止解讀個別係數，走 08 §六 共線性階梯"
        elif scaled > GVIF_WATCH:
            verdict = "⚠ > 2.24，標準誤已膨脹，報告須註明"
        else:
            verdict = "✅ 通過"
        rows.append({
            "term": term, "df": dfree, "GVIF": gvif,
            "GVIF^(1/(2df))": scaled, "判定": verdict,
        })
    out = pd.DataFrame(rows)
    out.attrs["thresholds"] = {"watch": GVIF_WATCH, "act": GVIF_ACT}
    return out


def nested_f(m_reduced: Any, m_full: Any) -> dict[str, Any]:
    """巢狀模型的 Partial F 檢定。參數順序刻意與 R 的 `anova(reduced, full)` 相同。

    statsmodels 的原生呼叫方向和 R **相反**（`完整.compare_f_test(縮減)`），
    寫反 F 會變負或報錯（08 §二）。這支把方向固定死，順便把 08 §七 的
    三個前置條件與「三角驗證」一起檢查掉：

      前置條件（缺一不可做）：同一個 Y、同一筆資料、縮減模型是完整模型的特例
      三角驗證：Partial F 顯著 ⟺ Adjusted R² ↑ 且 σ̂ ↓，三者一致才下結論

    回傳 dict：F、p、df_diff、df_resid_full、sse_reduced、sse_full、
              adj_r2_*、sigma_hat_*、triangulation、verdict、note
    """
    n_r, n_f = int(m_reduced.nobs), int(m_full.nobs)
    if n_r != n_f:
        raise ValueError(
            f"兩個模型的樣本數不同（縮減 {n_r} vs 完整 {n_f}）—— "
            f"巢狀 F 檢定要求同一筆資料（08 §七 前置條件 2）。\n"
            f"  怎麼辦：多半是 missing='drop' 丟掉的列不同。先把兩個模型要用的欄"
            f"一起 dropna，再用同一個子集配適。"
        )
    y_r = np.asarray(m_reduced.model.endog, dtype=float)
    y_f = np.asarray(m_full.model.endog, dtype=float)
    if not np.allclose(y_r, y_f, equal_nan=True):
        raise ValueError(
            "兩個模型的應變數不同 —— 巢狀 F 檢定要求同一個 Y（08 §七 前置條件 2）。\n"
            "  怎麼辦：檢查是不是一邊用了 log(Y)、一邊用原始 Y。轉換過的 Y 不可互比，"
            "要比就用 AIC 且兩邊都轉。"
        )

    sse_r = float(m_reduced.ssr)
    sse_f = float(m_full.ssr)
    if sse_r < sse_f - 1e-8 * max(1.0, sse_f):
        raise ValueError(
            f"縮減模型的 SSE（{sse_r:.6g}）小於完整模型（{sse_f:.6g}）—— "
            f"這在數學上不可能，代表兩個模型不是巢狀關係，或參數傳反了"
            f"（08 §七 前置條件 3）。\n"
            f"  怎麼辦：確認呼叫是 nested_f(縮減, 完整)；並確認縮減模型的變數集合"
            f"確實是完整模型的子集。"
        )

    cols_r = set(getattr(m_reduced.model, "exog_names", []) or [])
    cols_f = set(getattr(m_full.model, "exog_names", []) or [])
    note = ""
    if cols_r and not cols_r.issubset(cols_f):
        note = (
            f"縮減模型有完整模型沒有的欄：{sorted(cols_r - cols_f)} —— "
            f"SSE 大小雖然過關，但這不是嚴格巢狀，F 的分布只是近似的。"
        )

    F, p, ddf = m_full.compare_f_test(m_reduced)
    F, p, ddf = float(F), float(p), float(ddf)

    adj_r, adj_f = float(m_reduced.rsquared_adj), float(m_full.rsquared_adj)
    sig_r = float(np.sqrt(m_reduced.mse_resid))
    sig_f = float(np.sqrt(m_full.mse_resid))
    sig = p < 0.05
    consistent = (adj_f > adj_r and sig_f < sig_r) if sig else (adj_f <= adj_r or sig_f >= sig_r)

    return {
        "F": F,
        "p": p,
        "df_diff": ddf,
        "df_resid_full": float(m_full.df_resid),
        "sse_reduced": sse_r,
        "sse_full": sse_f,
        "adj_r2_reduced": adj_r,
        "adj_r2_full": adj_f,
        "sigma_hat_reduced": sig_r,
        "sigma_hat_full": sig_f,
        "triangulation": "一致" if consistent else "不一致（三個指標沒同向，先別下結論）",
        "verdict": ("保留該批變數（完整模型）" if sig else "移除該批變數（縮減模型）"),
        "note": note,
    }


# ══════════════════════════════════════════════════════════════
#  三、emmeans 替代品
# ══════════════════════════════════════════════════════════════
def _design_row_means(model: Any, data: pd.DataFrame, factor: str, level: Any) -> np.ndarray:
    """把 factor 全部設成 level，其餘共變量維持原樣後取設計矩陣列平均 = EMM 的對比向量。"""
    from patsy import dmatrix

    di = model.model.data.design_info
    d = data.copy()
    d[factor] = level
    return np.asarray(dmatrix(di, d)).mean(axis=0)


def emmeans(model: Any, data: pd.DataFrame, factor: str) -> pd.DataFrame:
    """R `emmeans(model, ~factor)` 的等價：共變量固定在樣本平均，逐 level 求邊際均值。

    Python 生態沒有 emmeans 對應套件（08 §二：最大缺口）。這裡靠 statsmodels 的
    `t_test()` 接受任意對比向量補上。`pairwise_tukeyhsd` 只吃「一個 Y + 一個分組」，
    **含共變量的調整後均值只能用這支**。

    限制（照抄 A.9 的原始限制，本檔沒有擴充）：
      · 只對應 emmeans 的預設行為（共變量取平均、類別取等權平均）；
        `weights=` / `at=` / `by=` 都沒實作
      · GLM 上 `t_test` 給的是 link scale，要轉回機率尺度得自己套 inverse link，
        且 CI 必須先在 link scale 算完再轉換，不可轉換上下界的中點
    """
    if factor not in data.columns:
        raise KeyError(
            f"資料裡沒有欄位 {factor!r} —— emmeans 需要用它重設每一個 level。\n"
            f"  怎麼辦：確認欄名（現有欄位：{list(data.columns)[:12]}…）。"
        )
    rows = []
    for lv in sorted(pd.Series(data[factor]).dropna().unique()):
        Xm = _design_row_means(model, data, factor, lv)
        tt = model.t_test(Xm)
        ci = np.asarray(tt.conf_int()).ravel()
        rows.append({
            factor: lv,
            "emmean": float(np.ravel(tt.effect)[0]),
            "SE": float(np.ravel(tt.sd)[0]),
            "CI_low": float(ci[0]),
            "CI_high": float(ci[1]),
        })
    return pd.DataFrame(rows)


def emm_contrasts(
    model: Any,
    data: pd.DataFrame,
    factor: str,
    method: str = "fdr_bh",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """R `pairs(emmeans(model, ~factor))` 的等價，含多重比較校正。

    實作判斷：素材原始碼預設 `holm`，本檔改成 **BH（fdr_bh）**，與 16 §3.3
    「預設 BH」一致。要押大預算的單一確認性結論再切 `method="bonferroni"`。

    欄位：contrast / estimate / SE / t / df / p_raw / p_adj / CI_low / CI_high
    """
    vecs: dict[Any, np.ndarray] = {}
    for lv in sorted(pd.Series(data[factor]).dropna().unique()):
        vecs[lv] = _design_row_means(model, data, factor, lv)

    out = []
    for a, b in itertools.combinations(vecs, 2):
        tt = model.t_test(vecs[a] - vecs[b])
        ci = np.asarray(tt.conf_int()).ravel()
        out.append({
            "contrast": f"{a} - {b}",
            "estimate": float(np.ravel(tt.effect)[0]),
            "SE": float(np.ravel(tt.sd)[0]),
            "t": float(np.ravel(tt.tvalue)[0]),
            "df": float(getattr(tt, "df_denom", np.nan) or np.nan),
            "p_raw": float(np.ravel(tt.pvalue)[0]),
            "CI_low": float(ci[0]),
            "CI_high": float(ci[1]),
        })
    o = pd.DataFrame(out)
    if len(o):
        o["p_adj"] = multipletests(o["p_raw"].to_numpy(), alpha=alpha, method=method)[1]
        o["p_adjust_method"] = method
    return o


# ══════════════════════════════════════════════════════════════
#  四、效果量：p / 效果量 / CI 三者並報
# ══════════════════════════════════════════════════════════════
def _label(value: float, cuts: Sequence[float], names: Sequence[str]) -> str:
    v = abs(value)
    for c, nm in zip(cuts, names):
        if v < c:
            return nm
    return names[-1]


def _solve_ncp(
    cdf,
    stat: float,
    target: float,
    *,
    allow_negative: bool = False,
    hi: float = 1e5,
) -> float:
    """解出使 cdf(stat; λ) = target 的非中心參數 λ（cdf 對 λ 遞減）。

    allow_negative：非中心 t 的 λ 可以是負的（d 的 CI 要能跨 0），非中心 F 與
    非中心卡方的 λ 必須 ≥ 0，兩者不可混用 —— 對 F／χ² 硬解負 λ 會得到假的下界。
    """
    from scipy.optimize import brentq

    try:
        floor = -hi if allow_negative else 0.0
        if cdf(stat, floor) <= target:
            return floor if allow_negative else 0.0
        lo, up = floor, max(floor + 1.0, 1.0)
        while cdf(stat, up) > target:
            up = up * 2 if up > 0 else 1.0
            if up > hi:
                return float("nan")
        return float(brentq(lambda lam: cdf(stat, lam) - target, lo, up, xtol=1e-8))
    except Exception:  # noqa: BLE001
        return float("nan")


def _d_ci(d: float, n1: int, n2: int, alpha: float) -> tuple[float, float, str]:
    """Cohen's d 的 CI。優先用非中心 t（λ 可為負，CI 才跨得過 0），失敗退常態近似。"""
    df = n1 + n2 - 2
    a = math.sqrt(1 / n1 + 1 / n2)
    t_obs = d / a if a > 0 else float("nan")
    lo = _solve_ncp(lambda s, lam: st.nct.cdf(s, df, lam), t_obs, 1 - alpha / 2,
                    allow_negative=True)
    hi_ = _solve_ncp(lambda s, lam: st.nct.cdf(s, df, lam), t_obs, alpha / 2,
                     allow_negative=True)
    if np.isfinite(lo) and np.isfinite(hi_) and abs(lo) < 1e4 and abs(hi_) < 1e4:
        vals = sorted([lo * a, hi_ * a])
        return vals[0], vals[1], "非中心 t"
    se = math.sqrt((n1 + n2) / (n1 * n2) + d * d / (2 * (n1 + n2)))
    z = st.norm.ppf(1 - alpha / 2)
    return d - z * se, d + z * se, "Hedges-Olkin 常態近似"


def mde(n1: int, n2: int, sd: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """最小可偵測差異（16 §1.3）：MDE = (z_{1-α/2} + z_{power}) · s · sqrt(1/n1 + 1/n2)。

    `n.s.` 的同一列必須附這個數字，否則「看不出來」會被讀成「沒差異」（00 §四）。
    """
    if n1 <= 0 or n2 <= 0:
        return float("nan")
    z = st.norm.ppf(1 - alpha / 2) + st.norm.ppf(power)
    return float(z * sd * math.sqrt(1 / n1 + 1 / n2))


def compare_two_groups(
    x1: Iterable[float],
    x2: Iterable[float],
    alpha: float = 0.05,
    power: float = 0.80,
) -> dict[str, Any]:
    """兩組比較的唯一出口 —— 三者並報（16 §1.4），不提供只回 p 值的介面。

    · 檢定用 **Welch's t**（16 §4.3：不先跑 Levene，那是一次額外的資料窺探）
    · 效果量用 Cohen's d（合併標準差）；min(n) < 20 另附 Hedges' g
    · min(n1, n2) < 30 時 `mde` 必為非 None（本檔一律計算，呼叫端不得丟棄）

    回傳 dict（欄位固定，`verify_outputs.py` 依賴這組欄名）：
      diff, ci_low, ci_high, p, effect_size, effect_label, mde, n1, n2,
      另附 mean1/mean2/sd_pooled/t/df/hedges_g/effect_ci_low/effect_ci_high/
      effect_ci_method/test/mde_required
    """
    a = pd.Series(list(x1), dtype="float64").dropna().to_numpy()
    b = pd.Series(list(x2), dtype="float64").dropna().to_numpy()
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        raise ValueError(
            f"兩組各需至少 2 筆非缺值觀測（現在是 {n1} 與 {n2}）—— 少於 2 筆算不出變異數。\n"
            f"  怎麼辦：n < 10 時本來就該走精確法或重抽法（16 §4.2），"
            f"且結論不得單獨支撐一條建議。"
        )

    m1, m2 = float(a.mean()), float(b.mean())
    v1, v2 = float(a.var(ddof=1)), float(b.var(ddof=1))
    diff = m1 - m2

    t_stat, p = st.ttest_ind(a, b, equal_var=False)          # Welch
    se_w = math.sqrt(v1 / n1 + v2 / n2)
    df_w = (
        (v1 / n1 + v2 / n2) ** 2
        / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    ) if se_w > 0 else float("nan")
    tcrit = st.t.ppf(1 - alpha / 2, df_w) if np.isfinite(df_w) else float("nan")
    ci_low, ci_high = diff - tcrit * se_w, diff + tcrit * se_w

    sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)) if n1 + n2 > 2 else float("nan")
    d = diff / sp if sp and np.isfinite(sp) and sp > 0 else float("nan")
    g = d * (1 - 3 / (4 * (n1 + n2) - 9)) if np.isfinite(d) and (4 * (n1 + n2) - 9) != 0 else float("nan")
    d_lo, d_hi, d_method = _d_ci(d, n1, n2, alpha) if np.isfinite(d) else (float("nan"), float("nan"), "N/A")

    m = mde(n1, n2, sp if np.isfinite(sp) else float("nan"), alpha, power)
    return {
        "diff": diff,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "p": float(p),
        "effect_size": float(d),
        "effect_label": f"Cohen's d {_label(d, COHEN_D, ('可忽略', '小', '中', '大'))}"
        if np.isfinite(d) else "N/A",
        "mde": float(m),
        "n1": n1,
        "n2": n2,
        "mean1": m1,
        "mean2": m2,
        "sd_pooled": float(sp),
        "t": float(t_stat),
        "df": float(df_w),
        "hedges_g": float(g),
        "effect_ci_low": float(d_lo),
        "effect_ci_high": float(d_hi),
        "effect_ci_method": d_method,
        "test": "Welch's t（16 §4.3 預設）",
        "mde_required": bool(min(n1, n2) < SMALL_N),
    }


def _eta_sq_ci(f_stat: float, df1: int, df2: int, n: int, alpha: float) -> tuple[float, float]:
    """η² 的 CI：解非中心 F 的 λ 區間再換算 η² = λ/(λ+N)。"""
    lo = _solve_ncp(lambda s, lam: st.ncf.cdf(s, df1, df2, lam), f_stat, 1 - alpha / 2)
    hi = _solve_ncp(lambda s, lam: st.ncf.cdf(s, df1, df2, lam), f_stat, alpha / 2)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return float("nan"), float("nan")
    return lo / (lo + n), hi / (hi + n)


def _cramers_v_ci(chi2: float, dof: int, n: int, k: int, alpha: float) -> tuple[float, float]:
    """Cramér's V 的 CI：解非中心卡方的 λ 區間再換算 V = sqrt(λ/(n·k))。"""
    lo = _solve_ncp(lambda s, lam: st.ncx2.cdf(s, dof, lam), chi2, 1 - alpha / 2)
    hi = _solve_ncp(lambda s, lam: st.ncx2.cdf(s, dof, lam), chi2, alpha / 2)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return float("nan"), float("nan")
    return math.sqrt(max(lo, 0) / (n * k)), math.sqrt(max(hi, 0) / (n * k))


def effect_sizes(
    data: pd.DataFrame | None = None,
    dv: str | None = None,
    group: str | None = None,
    *,
    x1: Iterable[float] | None = None,
    x2: Iterable[float] | None = None,
    table: pd.DataFrame | np.ndarray | None = None,
    alpha: float = 0.05,
    power: float = 0.80,
) -> dict[str, Any]:
    """效果量 + p 值 + 信賴區間，**三者一起回傳**（16 §一：只報 p 是違規）。

    三種呼叫方式，依傳進來的東西自動分派：
      兩組均值   effect_sizes(df, dv="CAI", group="性別")  或  effect_sizes(x1=a, x2=b)
                 → Cohen's d（+ Hedges' g）、Welch t、差異 CI、d 的 CI、MDE
      多組均值   effect_sizes(df, dv="CAI", group="教育程度")   （k ≥ 3）
                 → one-way ANOVA 的 F/p、η²（= one-way 的 partial η²）、η² 的 CI
      列聯表     effect_sizes(table=pd.crosstab(a, b))
                 → 卡方（走 chi2_safe 的期望次數 gate）、Cramér's V、V 的 CI

    回傳 dict 一律含：kind、effect_name、effect、effect_ci_low、effect_ci_high、
    effect_label、p、statistic、n、interpretation；兩組時另含 compare_two_groups
    的全部欄位（含 mde）。

    判讀門檻（16 §2.1）：d 0.2/0.5/0.8｜η² 0.01/0.06/0.14｜V <0.1 弱 /0.1–0.3 中 />0.3 強。
    **Cohen 的門檻只回答「統計上算不算大」；該不該花錢要另外算 MWE（16 §2.3）。**
    """
    if table is not None:
        res = chi2_safe(table, alpha=alpha)
        return {
            "kind": "contingency",
            "effect_name": "Cramér's V",
            "effect": res["cramers_v"],
            "effect_ci_low": res["v_ci_low"],
            "effect_ci_high": res["v_ci_high"],
            "effect_label": _label(res["cramers_v"], CRAMER_V, ("弱", "中", "強")),
            "p": res["p"],
            "statistic": res["chi2"],
            "dof": res["dof"],
            "n": res["n"],
            "method": res["method"],
            "expected_min": res["expected_min"],
            "pct_cells_lt5": res["pct_cells_lt5"],
            "interpretation": (
                f"χ²={res['chi2']:.4f}（df={res['dof']}）、p={res['p']:.4g}、"
                f"V={res['cramers_v']:.4f}"
                f"（{_label(res['cramers_v'], CRAMER_V, ('弱', '中', '強'))}，"
                f"95% CI [{res['v_ci_low']:.4f}, {res['v_ci_high']:.4f}]，n={res['n']}）"
            ),
        }

    if x1 is not None and x2 is not None:
        out = compare_two_groups(x1, x2, alpha=alpha, power=power)
        out.update(
            kind="two_groups",
            effect_name="Cohen's d",
            effect=out["effect_size"],
            statistic=out["t"],
            n=out["n1"] + out["n2"],
            interpretation=(
                f"差異 {out['diff']:.4f}（95% CI [{out['ci_low']:.4f}, {out['ci_high']:.4f}]）、"
                f"p={out['p']:.4g}、d={out['effect_size']:.4f}"
                f"（{out['effect_label']}，CI [{out['effect_ci_low']:.4f}, "
                f"{out['effect_ci_high']:.4f}]）、MDE={out['mde']:.4f}"
            ),
        )
        return out

    if data is None or dv is None or group is None:
        raise ValueError(
            "沒有給足夠的輸入 —— effect_sizes 需要 (data, dv, group)、(x1, x2) 或 table 三者之一。\n"
            "  怎麼辦：兩組比較用 effect_sizes(df, dv=..., group=...)；"
            "列聯表用 effect_sizes(table=pd.crosstab(a, b))。"
        )

    d = data[[dv, group]].dropna()
    levels = list(pd.Series(d[group]).unique())
    groups = [d.loc[d[group] == lv, dv].astype(float).to_numpy() for lv in levels]
    if len(levels) < 2:
        raise ValueError(
            f"{group!r} 只有 {len(levels)} 個有效組別 —— 少於兩組沒有「組間差異」可談。\n"
            f"  怎麼辦：檢查是不是篩選條件太嚴，或該欄在 dropna 後只剩一種值。"
        )
    if len(levels) == 2:
        return effect_sizes(x1=groups[0], x2=groups[1], alpha=alpha, power=power)

    n = int(sum(len(g) for g in groups))
    k = len(groups)
    f_stat, p = st.f_oneway(*groups)
    grand = float(np.concatenate(groups).mean())
    ss_b = float(sum(len(g) * (g.mean() - grand) ** 2 for g in groups))
    ss_w = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
    ss_t = ss_b + ss_w
    eta2 = ss_b / ss_t if ss_t > 0 else float("nan")
    lo, hi = _eta_sq_ci(float(f_stat), k - 1, n - k, n, alpha)
    sizes = {str(lv): int(len(g)) for lv, g in zip(levels, groups)}
    sd_pooled = math.sqrt(ss_w / (n - k)) if n > k else float("nan")
    min_n = min(sizes.values())
    two_smallest = sorted(sizes.values())[:2]
    m = mde(two_smallest[0], two_smallest[1], sd_pooled, alpha, power) if len(two_smallest) == 2 else float("nan")
    return {
        "kind": "k_groups",
        "effect_name": "eta squared",
        "effect": eta2,
        "effect_ci_low": lo,
        "effect_ci_high": hi,
        "effect_label": _label(eta2, COHEN_ETA2, ("可忽略", "小", "中", "大")),
        "p": float(p),
        "statistic": float(f_stat),
        "df_between": k - 1,
        "df_within": n - k,
        "ss_between": ss_b,
        "ss_within": ss_w,
        "ss_total": ss_t,
        "ss_check_passed": bool(abs(ss_b + ss_w - ss_t) <= SS_TOL * max(1.0, ss_t)),
        "n": n,
        "group_sizes": sizes,
        "sd_pooled": sd_pooled,
        "mde": float(m),
        "mde_required": bool(min_n < SMALL_N),
        "interpretation": (
            f"F({k - 1}, {n - k})={f_stat:.4f}、p={p:.4g}、η²={eta2:.4f}"
            f"（{_label(eta2, COHEN_ETA2, ('可忽略', '小', '中', '大'))}，"
            f"95% CI [{lo:.4f}, {hi:.4f}]）"
            + (f"；最小兩組的 MDE={m:.4f}" if min_n < SMALL_N else "")
        ),
    }


def chi2_safe(
    table: pd.DataFrame | np.ndarray,
    *,
    alpha: float = 0.05,
    correction: bool = False,
    B: int = 10_000,
    seed: int = 42,
) -> dict[str, Any]:
    """帶期望次數 gate 的卡方檢定。**禁止直接呼叫 `scipy.stats.chi2_contingency`**（16 §4.5）。

    理由和 18-T3 同級：期望次數不足時卡方近似會失準，而 scipy 不會擋你。規則（16 §4.2）：
      · 所有 $E_{ij} \\ge 5$              → 一般卡方
      · 2×2 且任一 $E_{ij} < 5$          → Fisher 精確檢定
      · r×c 且期望 <5 的格超過 20%       → Monte-Carlo 排列卡方（B=10,000）

    回傳一律含 Cramér's V 與其 CI（16 §2.2(b)：**沒有 V 欄的卡方表不得交付**），
    以及 `expected_min` / `pct_cells_lt5` 兩個 verify_outputs 會檢查的欄位。
    """
    tab = pd.DataFrame(table)
    obs = tab.to_numpy(dtype=float)
    if obs.ndim != 2 or min(obs.shape) < 2:
        raise ValueError(
            f"列聯表的形狀是 {obs.shape} —— 卡方需要至少 2×2。\n"
            f"  怎麼辦：確認 pd.crosstab 的兩個變數在篩選後都還有 2 個以上的類別。"
        )
    n = float(obs.sum())
    chi2, p_chi, dof, exp = st.chi2_contingency(obs, correction=correction)
    exp_min = float(exp.min())
    pct_lt5 = float((exp < 5).mean() * 100)

    rng = np.random.default_rng(seed)
    if obs.shape == (2, 2) and exp_min < 5:
        _, p = st.fisher_exact(obs.astype(int))
        method = "Fisher 精確檢定（2×2 且期望次數 < 5）"
    elif pct_lt5 > 20:
        stat0 = chi2
        rows = obs.sum(axis=1).astype(int)
        cols = obs.sum(axis=0).astype(int)
        labels = np.repeat(np.arange(len(rows)), rows)
        colvec = np.repeat(np.arange(len(cols)), cols)
        hits = 0
        for _ in range(B):
            perm = rng.permutation(colvec)
            ct = np.zeros_like(obs)
            np.add.at(ct, (labels, perm), 1)
            try:
                s, _, _, _ = st.chi2_contingency(ct, correction=False)
            except ValueError:
                continue
            hits += int(s >= stat0 - 1e-12)
        p = (hits + 1) / (B + 1)
        method = f"Monte-Carlo 排列卡方（期望 <5 的格佔 {pct_lt5:.1f}% > 20%，B={B}）"
    else:
        p = float(p_chi)
        method = "一般卡方" + ("（Yates 連續性校正）" if correction and obs.shape == (2, 2) else "")

    k = min(obs.shape) - 1
    v = math.sqrt(chi2 / (n * k)) if n > 0 and k > 0 else float("nan")
    v_lo, v_hi = _cramers_v_ci(float(chi2), int(dof), int(n), k, alpha)
    return {
        "chi2": float(chi2),
        "dof": int(dof),
        "p": float(p),
        "p_chi2_asymptotic": float(p_chi),
        "method": method,
        "n": int(n),
        "expected_min": exp_min,
        "pct_cells_lt5": pct_lt5,
        "cramers_v": float(v),
        "v_ci_low": float(v_lo),
        "v_ci_high": float(v_hi),
        "v_label": _label(v, CRAMER_V, ("弱", "中", "強")),
        "approximation": (
            "exact" if method.startswith("Fisher")
            else "permutation" if method.startswith("Monte")
            else "asymptotic"
        ),
    }


# ══════════════════════════════════════════════════════════════
#  五、事後檢定：16 §8.4 的兩層決策樹
# ══════════════════════════════════════════════════════════════
def _hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float("nan")
    sp = math.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    if sp <= 0:
        return float("nan")
    d = (a.mean() - b.mean()) / sp
    return float(d * (1 - 3 / (4 * (n1 + n2) - 9)))


def _rank_biserial(a: np.ndarray, b: np.ndarray) -> float:
    """Mann-Whitney 的秩雙序相關 —— 無母數路徑的效果量（16 §一：不能只報 p）。"""
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return float("nan")
    u, _ = st.mannwhitneyu(a, b, alternative="two-sided")
    return float(2 * u / (n1 * n2) - 1)


def _bca_diff_ci(
    a: np.ndarray, b: np.ndarray, alpha: float, B: int, rng: np.random.Generator
) -> tuple[float, float]:
    """兩組均值差的 bootstrap BCa CI（16 §8.4 變異數比 ≥ 4 的備援路徑）。"""
    theta = a.mean() - b.mean()
    boots = np.empty(B)
    for i in range(B):
        boots[i] = rng.choice(a, len(a), replace=True).mean() - rng.choice(b, len(b), replace=True).mean()
    prop = float((boots < theta).mean())
    prop = min(max(prop, 1 / (2 * B)), 1 - 1 / (2 * B))
    z0 = st.norm.ppf(prop)
    pooled = np.concatenate([a, b])
    n1, n2 = len(a), len(b)
    jack = []
    for i in range(len(pooled)):
        if i < n1:
            aa = np.delete(a, i)
            jack.append(aa.mean() - b.mean())
        else:
            bb = np.delete(b, i - n1)
            jack.append(a.mean() - bb.mean())
    jack = np.asarray(jack)
    jm = jack.mean()
    denom = 6 * ((((jm - jack) ** 2).sum()) ** 1.5)
    acc = (((jm - jack) ** 3).sum()) / denom if denom > 0 else 0.0
    out = []
    for q in (alpha / 2, 1 - alpha / 2):
        z = st.norm.ppf(q)
        adj = z0 + (z0 + z) / (1 - acc * (z0 + z))
        out.append(float(np.percentile(boots, 100 * st.norm.cdf(adj))))
    return out[0], out[1]


def posthoc(
    data: pd.DataFrame,
    dv: str,
    group: str,
    *,
    method: str = "auto",
    control: Any = None,
    alpha: float = 0.05,
    declared: str | None = None,
    transformed: bool = False,
    B: int = 2000,
    seed: int = 42,
    verbose: bool = False,
) -> dict[str, Any]:
    """依 16 §8.4 的**兩層決策樹**自動選事後檢定，並回傳 `method_chosen` 與 `why`。

    決策樹（常態與變異數同質是兩個獨立維度，必須分兩層問；排成同一層會讓
    「偏態 + 等變異」的資料被錯誤攔走）：

        比較結構是「各組 vs 單一對照組」？ → Dunnett（傳 control=）
        否則 —— 第 1 層：常態站得住嗎？（各組 |skew| < 1，或轉換後 < 1）
            ├ 是 → 第 2 層：Levene p > 0.05 且 變異數比 < 4？
            │        ├ 是 → Tukey HSD（n 不等自動走 Tukey–Kramer）
            │        └ 否 → Welch ANOVA + Games-Howell
            └ 否 → 變異數比 < 4 → Kruskal-Wallis + Dunn(BH)
                   變異數比 ≥ 4 → Games-Howell 或 bootstrap BCa
                                  （**KW 在異方差下型一錯誤失控，不可當萬用退路**；
                                    05 §1.2 實測 α：ANOVA 0.223／KW 0.116／Welch 0.049）

    任一組 n < 5 或變異數為 0 → 走降級階梯（手動 Welch t + BH），`degraded=True`。

    參數
      method     "auto"（預設）走決策樹；也可指定 tukey / games_howell /
                 kruskal_dunn / dunnett / bootstrap_bca 強制覆寫（會記在 why 裡）
      declared   `params.yml` 事前宣告的方法。與實際選出的不符就擋下來 ——
                 這條擋的是「看到 p 值再挑方法」（16 §8.3）
      transformed 已經做過轉換仍偏態時傳 True，會寫進 why

    回傳 dict：method_chosen、why、table（DataFrame）、omnibus、assumptions、
              group_sizes、degraded、fwer_controlled、notes
      **fwer_controlled=True 時不得再套 BH**（16 §3.2：Tukey/GH/Dunnett 已控制
      FWER，二次校正是重複校正）。`bh_correct()` 會擋。
    """
    d = data[[dv, group]].dropna()
    d = d.assign(**{dv: pd.to_numeric(d[dv], errors="coerce")}).dropna()
    levels = sorted(pd.Series(d[group]).unique(), key=str)
    if len(levels) < 3 and control is None and method == "auto":
        if len(levels) < 2:
            raise ValueError(
                f"{group!r} 在去除缺值後只剩 {len(levels)} 組 —— 沒有成對比較可做。\n"
                f"  怎麼辦：檢查篩選條件；兩組比較請改用 compare_two_groups()。"
            )
    groups = {lv: d.loc[d[group] == lv, dv].to_numpy(dtype=float) for lv in levels}
    sizes = {str(k): int(len(v)) for k, v in groups.items()}
    rng = np.random.default_rng(seed)
    notes: list[str] = []

    # ── 前提診斷 ──────────────────────────────────────────
    skews = {str(k): float(st.skew(v, bias=True)) if len(v) > 2 else float("nan")
             for k, v in groups.items()}
    max_skew = float(np.nanmax([abs(s) for s in skews.values()])) if skews else float("nan")
    shapiro: dict[str, float] = {}
    for k, v in groups.items():
        if 3 <= len(v) <= 5000:
            try:
                shapiro[str(k)] = float(st.shapiro(v).pvalue)
            except Exception:  # noqa: BLE001
                shapiro[str(k)] = float("nan")
    variances = {str(k): float(v.var(ddof=1)) if len(v) > 1 else float("nan")
                 for k, v in groups.items()}
    vv = [x for x in variances.values() if np.isfinite(x) and x > 0]
    var_ratio = float(max(vv) / min(vv)) if len(vv) >= 2 else float("nan")
    try:
        lev_stat, lev_p = st.levene(*[v for v in groups.values() if len(v) > 1], center="median")
    except Exception:  # noqa: BLE001
        lev_stat, lev_p = float("nan"), float("nan")

    normal_ok = bool(np.isfinite(max_skew) and max_skew < SKEW_LIMIT)
    homog_ok = bool(np.isfinite(lev_p) and lev_p > LEVENE_ALPHA
                    and np.isfinite(var_ratio) and var_ratio < VAR_RATIO_LIMIT)
    tiny = [k for k, n in sizes.items() if n < MIN_GROUP_N]
    zero_var = [k for k, v in variances.items() if not np.isfinite(v) or v == 0]

    assumptions = {
        "skew_by_group": skews,
        "max_abs_skew": max_skew,
        "skew_limit": SKEW_LIMIT,
        "normality_ok": normal_ok,
        "shapiro_p_by_group": shapiro,
        "levene_stat": float(lev_stat),
        "levene_p": float(lev_p),
        "levene_center": "median（Modified Levene，05 §1.2 實務首選）",
        "variance_by_group": variances,
        "variance_ratio": var_ratio,
        "homogeneity_ok": homog_ok,
        "groups_below_min_n": tiny,
        "groups_zero_variance": zero_var,
    }

    # ── 選方法 ────────────────────────────────────────────
    degraded = False
    if method != "auto":
        chosen = method
        why = f"呼叫端以 method={method!r} 強制指定，未走 16 §8.4 決策樹。"
    elif tiny or zero_var:
        chosen, degraded = "manual_t_bh", True
        why = (
            f"降級階梯：{'某群 n < 5（' + '、'.join(tiny) + '）' if tiny else ''}"
            f"{'；' if tiny and zero_var else ''}"
            f"{'某群變異數為 0（' + '、'.join(zero_var) + '）' if zero_var else ''}"
            f" —— 標準事後檢定跑不出來，退到手動 Welch t + BH（16 §8.4 降級階梯）。"
        )
    elif control is not None:
        chosen = "dunnett"
        why = f"比較結構是「各組 vs 單一對照組 {control!r}」→ Dunnett（比較數少、檢定力較高）。"
    elif normal_ok and homog_ok:
        chosen = "tukey"
        why = (
            f"第 1 層常態站得住（max|skew|={max_skew:.3f} < {SKEW_LIMIT}）；"
            f"第 2 層 Levene p={lev_p:.4f} > {LEVENE_ALPHA} 且變異數比={var_ratio:.2f} "
            f"< {VAR_RATIO_LIMIT} → Tukey HSD（預設；n 不等自動走 Tukey–Kramer）。"
        )
    elif normal_ok:
        chosen = "games_howell"
        why = (
            f"第 1 層常態站得住（max|skew|={max_skew:.3f} < {SKEW_LIMIT}）；"
            f"第 2 層變異數不齊（Levene p={lev_p:.4f}、變異數比={var_ratio:.2f}）"
            f"→ Welch ANOVA + Games-Howell（05 §1.2 通行證）。"
        )
    elif np.isfinite(var_ratio) and var_ratio < VAR_RATIO_LIMIT:
        chosen = "kruskal_dunn"
        why = (
            f"常態不成立（max|skew|={max_skew:.3f} ≥ {SKEW_LIMIT}"
            f"{'，且轉換後仍偏態' if transformed else '，尚未嘗試轉換'}）"
            f"且變異數比={var_ratio:.2f} < {VAR_RATIO_LIMIT} → Kruskal-Wallis + Dunn(BH)。"
        )
        notes.append(
            "用了 KW 就必須附並排箱型圖確認各組形狀相近，否則結論只能寫「各組分布有差異」，"
            "不可寫成中位數排序（05 §1.2）。"
        )
    else:
        chosen = "games_howell"
        why = (
            f"常態不成立（max|skew|={max_skew:.3f} ≥ {SKEW_LIMIT}）**且變異數比"
            f"={var_ratio:.2f} ≥ {VAR_RATIO_LIMIT}** → 不可退 Kruskal-Wallis"
            f"（異方差下型一錯誤失控，05 §1.2 實測 α：ANOVA 0.223／KW 0.116／Welch 0.049），"
            f"改走 Games-Howell；要無母數區間請改 method='bootstrap_bca'。"
        )

    if declared and declared != chosen:
        raise ValueError(
            f"事前宣告的事後檢定是 {declared!r}，但依 16 §8.4 決策樹算出來應該是 {chosen!r} —— "
            f"「用哪個事後檢定」必須事前決定並寫進 params.yml，不能看到 p 值再挑（16 §8.3；"
            f"同一組資料三種方法的 p 差一個數量級）。\n"
            f"  怎麼辦：(1) 若前提診斷才是對的，更新 params.yml 的宣告並在報告寫明改動理由；"
            f"(2) 若真要沿用宣告的方法，傳 method={declared!r} 強制指定，"
            f"why 欄會記下「未走決策樹」。診斷結果：{why}"
        )

    # ── 執行 ──────────────────────────────────────────────
    omnibus: dict[str, Any] = {}
    fwer = True
    rows: list[dict[str, Any]] = []
    arrs = [groups[lv] for lv in levels]

    if chosen == "tukey":
        f_stat, p_om = st.f_oneway(*arrs)
        es = effect_sizes(d, dv=dv, group=group, alpha=alpha)
        omnibus = {"test": "one-way ANOVA", "statistic": float(f_stat), "p": float(p_om),
                   "eta_sq": es["effect"], "eta_sq_ci": (es["effect_ci_low"], es["effect_ci_high"])}
        res = pairwise_tukeyhsd(d[dv].to_numpy(float), d[group].astype(str).to_numpy(), alpha=alpha)
        gu = list(res.groupsunique)
        # statsmodels 的 meandiff 是「後者 − 前者」，這裡把欄名對調過來，
        # 讓整份表的 diff 一律等於 group1 − group2（與 Dunnett／Games-Howell 一致）
        for (a, b), md, lo, hi, pv, rj in zip(
            itertools.combinations(gu, 2), res.meandiffs,
            res.confint[:, 0], res.confint[:, 1], res.pvalues, res.reject
        ):
            ga, gb = groups[_match_level(levels, a)], groups[_match_level(levels, b)]
            rows.append({"group1": b, "group2": a, "diff": float(md),
                         "ci_low": float(lo), "ci_high": float(hi), "p": float(pv),
                         "hedges_g": _hedges_g(gb, ga), "reject": bool(rj),
                         "diff_direction": f"{b} − {a}"})

    elif chosen == "games_howell":
        try:
            import pingouin as pg
        except ImportError as e:
            raise RuntimeError(
                "Games-Howell 需要 pingouin，但它沒裝 —— 這條路徑是變異數不齊時唯一"
                "合法的成對比較（不可退 Kruskal-Wallis）。\n"
                "  怎麼辦：pip install pingouin；真的裝不了就改 method='bootstrap_bca' "
                "走無母數區間，並在報告寫明降級。"
            ) from e
        try:
            wa = pg.welch_anova(data=d, dv=dv, between=group)
            # pingouin 的 p 值欄名在版本間改過（p-unc / p_unc），不要寫死
            pcol = next((c for c in wa.columns if c.lower().replace("-", "_") == "p_unc"), None)
            if pcol is None:
                raise KeyError(f"pingouin.welch_anova 沒有 p 值欄，實際欄位：{list(wa.columns)}")
            omnibus = {"test": "Welch ANOVA", "statistic": float(wa["F"].iloc[0]),
                       "p": float(wa[pcol].iloc[0]),
                       "np2": float(wa["np2"].iloc[0]) if "np2" in wa.columns else float("nan")}
        except Exception as e:  # noqa: BLE001
            omnibus = {"test": "Welch ANOVA", "error": repr(e),
                       "note": "整體檢定失敗不影響成對比較，但報告要說明 omnibus 缺席"}
        gh = pg.pairwise_gameshowell(data=d, dv=dv, between=group)
        for _, r in gh.iterrows():
            ga, gb = groups[_match_level(levels, r["A"])], groups[_match_level(levels, r["B"])]
            se = float(r.get("se", np.nan))
            dfr = float(r.get("df", np.nan))
            diff = float(r["diff"])
            tcrit = st.t.ppf(1 - alpha / 2, dfr) if np.isfinite(dfr) else float("nan")
            rows.append({
                "group1": r["A"], "group2": r["B"], "diff": diff,
                "ci_low": diff - tcrit * se if np.isfinite(tcrit) else float("nan"),
                "ci_high": diff + tcrit * se if np.isfinite(tcrit) else float("nan"),
                "p": float(r["pval"]),
                "hedges_g": float(r["hedges"]) if "hedges" in gh.columns else _hedges_g(ga, gb),
                "reject": bool(float(r["pval"]) < alpha),
                "diff_direction": f"{r['A']} − {r['B']}",
            })

    elif chosen == "kruskal_dunn":
        h, p_om = st.kruskal(*arrs)
        n_tot = sum(len(a) for a in arrs)
        eps2 = (float(h) - len(arrs) + 1) / (n_tot - len(arrs)) if n_tot > len(arrs) else float("nan")
        omnibus = {"test": "Kruskal-Wallis", "statistic": float(h), "p": float(p_om),
                   "epsilon_sq": float(eps2)}
        try:
            import scikit_posthocs as sp
        except ImportError as e:
            raise RuntimeError(
                "Kruskal-Wallis 的事後檢定需要 scikit-posthocs（Dunn），但它沒裝 —— "
                "ANOVA → 事後檢定不可分離（18-E1）。\n"
                "  怎麼辦：pip install scikit-posthocs；裝不了就走降級階梯"
                "（method='manual_t_bh'）並在 degradation_log.md 記一列。"
            ) from e
        mat = sp.posthoc_dunn(d, val_col=dv, group_col=group, p_adjust="fdr_bh")
        for a, b in itertools.combinations(list(mat.index), 2):
            ga, gb = groups[_match_level(levels, a)], groups[_match_level(levels, b)]
            pv = float(mat.loc[a, b])
            rows.append({
                "group1": a, "group2": b,
                "diff": float(np.median(ga) - np.median(gb)),
                "ci_low": float("nan"), "ci_high": float("nan"),
                "p": pv, "rank_biserial": _rank_biserial(ga, gb),
                "reject": bool(pv < alpha),
                "diff_direction": f"中位數 {a} − {b}",
            })
        fwer = True  # Dunn 已內含 BH，不得再校正一次
        notes.append("Dunn 的 p 已用 BH 校正過，不可再套 bh_correct()。")

    elif chosen == "dunnett":
        if control is None:
            raise ValueError(
                "method='dunnett' 但沒有指定 control —— Dunnett 檢定的定義就是「各組 vs 對照組」。\n"
                "  怎麼辦：傳 control='<對照組的 level>'，例如現行主打方案。"
            )
        ctrl_key = _match_level(levels, control)
        others = [lv for lv in levels if lv != ctrl_key]
        res = st.dunnett(*[groups[lv] for lv in others], control=groups[ctrl_key])
        ci = res.confidence_interval(confidence_level=1 - alpha)
        f_stat, p_om = st.f_oneway(*arrs)
        omnibus = {"test": "one-way ANOVA", "statistic": float(f_stat), "p": float(p_om)}
        for lv, stat, pv, lo, hi in zip(others, res.statistic, res.pvalue, ci.low, ci.high):
            rows.append({
                "group1": lv, "group2": ctrl_key,
                "diff": float(groups[lv].mean() - groups[ctrl_key].mean()),
                "ci_low": float(lo), "ci_high": float(hi), "p": float(pv),
                "statistic": float(stat),
                "hedges_g": _hedges_g(groups[lv], groups[ctrl_key]),
                "reject": bool(float(pv) < alpha),
                "diff_direction": f"{lv} − {ctrl_key}",
            })

    elif chosen == "bootstrap_bca":
        h, p_om = st.kruskal(*arrs)
        omnibus = {"test": "Kruskal-Wallis（僅供整體參考）", "statistic": float(h), "p": float(p_om)}
        fwer = False
        for a, b in itertools.combinations(levels, 2):
            lo, hi = _bca_diff_ci(groups[a], groups[b], alpha, B, rng)
            _, pv = st.ttest_ind(groups[a], groups[b], equal_var=False)
            rows.append({
                "group1": a, "group2": b,
                "diff": float(groups[a].mean() - groups[b].mean()),
                "ci_low": lo, "ci_high": hi, "p": float(pv),
                "hedges_g": _hedges_g(groups[a], groups[b]),
                "reject": bool(not (lo <= 0 <= hi)),
                "diff_direction": f"{a} − {b}",
            })
        notes.append(f"bootstrap BCa（B={B}）給的是區間，p 欄是未校正的 Welch t，僅供參考。")

    elif chosen == "manual_t_bh":
        fwer = False
        f_stat, p_om = st.f_oneway(*arrs) if all(len(a) > 1 for a in arrs) else (float("nan"), float("nan"))
        omnibus = {"test": "one-way ANOVA（降級路徑，僅供參考）",
                   "statistic": float(f_stat), "p": float(p_om)}
        raw = []
        for a, b in itertools.combinations(levels, 2):
            ga, gb = groups[a], groups[b]
            if len(ga) < 2 or len(gb) < 2:
                raw.append({"group1": a, "group2": b, "diff": float("nan"),
                            "ci_low": float("nan"), "ci_high": float("nan"),
                            "p": float("nan"), "hedges_g": float("nan"),
                            "diff_direction": f"{a} − {b}"})
                continue
            c = compare_two_groups(ga, gb, alpha=alpha)
            raw.append({"group1": a, "group2": b, "diff": c["diff"],
                        "ci_low": c["ci_low"], "ci_high": c["ci_high"], "p": c["p"],
                        "hedges_g": c["hedges_g"], "mde": c["mde"],
                        "diff_direction": f"{a} − {b}"})
        rows = raw
        ps = np.array([r["p"] for r in rows], dtype=float)
        ok = np.isfinite(ps)
        adj = np.full_like(ps, np.nan)
        if ok.any():
            adj[ok] = multipletests(ps[ok], alpha=alpha, method="fdr_bh")[1]
        for r, pa in zip(rows, adj):
            r["p_bh"] = float(pa)
            r["reject"] = bool(np.isfinite(pa) and pa < alpha)
        notes.append("降級路徑：手動 Welch t 的 p 已套 BH（16 §8.4 附加規則 1）。")

    else:
        raise ValueError(
            f"不認得的 method={chosen!r}。\n"
            f"  怎麼辦：可用值為 auto / tukey / games_howell / kruskal_dunn / "
            f"dunnett / bootstrap_bca / manual_t_bh。"
        )

    tbl = pd.DataFrame(rows)
    out = {
        "method_chosen": chosen,
        "why": why,
        "table": tbl,
        "omnibus": omnibus,
        "assumptions": assumptions,
        "group_sizes": sizes,
        "n_groups": len(levels),
        "alpha": alpha,
        "degraded": degraded,
        # 兩個欄位刻意分開：Tukey/GH/Dunnett 控制的是 FWER，Dunn 用的是 BH（FDR）。
        # 「不得再套一次校正」對四者都成立，但寫成同一個欄位會讓 16 §3.2 的兩件事混淆。
        "fwer_controlled": bool(fwer and chosen in {"tukey", "games_howell", "dunnett"}),
        "already_corrected": bool(fwer and chosen in
                                  {"tukey", "games_howell", "dunnett", "kruskal_dunn"}),
        "notes": notes,
        "dv": dv,
        "group": group,
    }
    if any(n < SMALL_N for n in sizes.values()):
        out["notes"].append(
            f"有組別 n < {SMALL_N}（{ {k: v for k, v in sizes.items() if v < SMALL_N} }）—— "
            f"16 §4.1 硬規則：不顯著的列必須同時報 MDE，不可寫成「兩群一樣」。"
        )
    if verbose:
        print(f"✅ posthoc → {chosen}\n · {why}", file=sys.stderr)
    return out


def _match_level(levels: list[Any], name: Any) -> Any:
    """把 statsmodels/pingouin 回傳的（字串化）組名對回原始 level。"""
    for lv in levels:
        if lv == name or str(lv) == str(name):
            return lv
    raise KeyError(
        f"對不回原始組別 {name!r} —— 這通常是組名裡有前後空白或型別混雜。\n"
        f"  怎麼辦：先把分組欄 astype(str).str.strip() 再進來。現有 level：{levels}"
    )


# ══════════════════════════════════════════════════════════════
#  六、多重比較校正
# ══════════════════════════════════════════════════════════════
def bh_correct(
    pvals: Iterable[float],
    *,
    alpha: float = 0.05,
    family: str | None = None,
    labels: Sequence[Any] | None = None,
    method: str = "fdr_bh",
    already_fwer_controlled: bool = False,
) -> pd.DataFrame:
    """Benjamini-Hochberg FDR 校正（18-G8：全 skill 統一用 BH）。

    程序：把 m 個 p 值排序，找**最大**的 k 使 $p_{(k)} \\le \\frac{k}{m} q$，拒絕前 k 個。

    硬規則：
      · **原始 p 與校正後 p 必須並排出現在報表**（16 §3.4），所以本函式回傳
        兩欄都在的表，不回傳單一陣列
      · Tukey / Games-Howell / Dunnett 之後**不得再套 BH**（16 §3.2 重複校正）。
        傳 already_fwer_controlled=True 會直接擋下來
      · `family` 要填 —— 讀者得知道 m 是多少（16 §3.4 的 verify CHECK）

    切 Bonferroni 的唯一情境是「單一確認性結論、要押七位數預算」（16 §3.3），
    傳 method="bonferroni"。**不要因為 m 小就切 Bonferroni**：m=5 時兩者臨界值差 5 倍。
    """
    if already_fwer_controlled:
        raise ValueError(
            "這批 p 值已由 Tukey／Games-Howell／Dunnett 控制 FWER，再套 BH 是重複校正 —— "
            "會讓真效果被殺光（16 §3.2）。\n"
            "  怎麼辦：直接用事後檢定回傳的 p 欄；只有「手動 t 檢定」的降級路徑才需要 BH。"
        )
    p = np.asarray(list(pvals), dtype=float)
    if p.size == 0:
        raise ValueError("沒有 p 值可以校正 —— 傳進來的是空的。怎麼辦：確認上游檢定真的有跑出結果。")
    bad = ~np.isfinite(p) | (p < 0) | (p > 1)
    if bad.any():
        raise ValueError(
            f"有 {int(bad.sum())} 個 p 值不在 [0, 1] 或是 NaN（位置 {np.flatnonzero(bad).tolist()}）—— "
            f"多重比較校正不能靠丟掉算不出來的檢定來湊，那會讓 m 偏小、校正過寬"
            f"（16 §3.4 的 verify CHECK 就是在防這個）。\n"
            f"  怎麼辦：把算不出來的那幾列填 `N/A` 保留在報表裡，並在 family 的 m 說明中"
            f"寫清楚有幾個檢定未能執行。"
        )
    rej, p_adj, _, _ = multipletests(p, alpha=alpha, method=method)
    m = p.size
    order = np.argsort(p, kind="mergesort")
    rank = np.empty(m, dtype=int)
    rank[order] = np.arange(1, m + 1)
    col = "p_bh" if method.startswith("fdr") else "p_bonf" if method == "bonferroni" else "p_adj"
    out = pd.DataFrame({
        "label": list(labels) if labels is not None else list(range(m)),
        "p_raw": p,
        col: p_adj,
        "rank": rank,
        "bh_threshold": rank / m * alpha,
        "rejected": rej,
    })
    out["family"] = family if family else "（未命名 —— 16 §3.4 要求寫出族的名字）"
    out["m"] = m
    out["method"] = method
    out.attrs.update(alpha=alpha, m=m, method=method, family=family)
    return out


# ══════════════════════════════════════════════════════════════
#  七、自我檢查
# ══════════════════════════════════════════════════════════════
errors: list[str] = []
warnings_: list[str] = []
infos: list[str] = []


def _ok(msg: str) -> None:
    infos.append(msg)


def _warn(msg: str, why: str) -> None:
    warnings_.append(f"{msg} — {why}")


def _err(msg: str, why: str) -> None:
    errors.append(f"{msg} — {why}")


def _selftest_anova3() -> None:
    """核心斷言：anova3 與 anova_lm(typ=3) 的差異真的存在（用 statsmodels 內建資料）。"""
    try:
        fair = sm.datasets.fair.load_pandas().data
    except Exception as e:  # noqa: BLE001
        _err("讀不到 statsmodels 內建資料 fair", f"{e!r}。怎麼辦：確認 statsmodels 安裝完整")
        return

    df = fair.assign(
        rm=fair["rate_marriage"].astype(int).astype(str),
        rel=fair["religious"].astype(int).astype(str),
    )
    wrong = anova_lm(smf.ols("affairs ~ C(rm)*C(rel)", df, missing="drop").fit(), typ=3)
    right = anova3("affairs ~ C(rm) * C(rel)", df, verbose=False)

    ss_w_a = float(wrong.loc["C(rm)", "sum_sq"])
    ss_r_a = float(right.loc["C(rm, Sum)", "sum_sq"])
    ss_w_b = float(wrong.loc["C(rel)", "sum_sq"])
    ss_r_b = float(right.loc["C(rel, Sum)", "sum_sq"])
    ix_w = float(wrong.loc["C(rm):C(rel)", "sum_sq"])
    ix_r = float(right.loc["C(rm, Sum):C(rel, Sum)", "sum_sq"])

    infos.append(f"  · statsmodels.datasets.fair，n={int(right.attrs['n'])}，"
                 f"rm 5 個 level × rel 4 個 level（不平衡設計）")
    infos.append(f"  · 主效果 rm  ：treatment {ss_w_a:12.4f} vs Sum {ss_r_a:12.4f}"
                 f"  → 差 {abs(ss_r_a - ss_w_a) / ss_r_a * 100:5.1f}%")
    infos.append(f"  · 主效果 rel ：treatment {ss_w_b:12.4f} vs Sum {ss_r_b:12.4f}"
                 f"  → 差 {abs(ss_r_b - ss_w_b) / ss_r_b * 100:5.1f}%")
    infos.append(f"  · 交互項     ：treatment {ix_w:12.4f} vs Sum {ix_r:12.4f}"
                 f"  → 差 {abs(ix_r - ix_w):.2e}（最高階交互項三種 Type 相同）")

    if abs(ss_r_a - ss_w_a) / max(ss_r_a, 1e-12) < 0.01:
        _err("anova3 與 anova_lm(typ=3) 的主效果 SS 幾乎相同",
             "18-T3 的靜默錯誤在這批資料上沒重現，防呆函式失去驗證依據。"
             "怎麼辦：換一個更不平衡的設計重測，或確認 statsmodels 是否改了預設編碼")
    else:
        _ok("anova3 vs anova_lm(typ=3)：主效果 SS 差異存在，18-T3 的靜默錯誤重現")

    if abs(ix_r - ix_w) > 1e-6 * max(abs(ix_r), 1.0):
        _warn("交互項 SS 兩種寫法不同", f"理論上應相同（差 {abs(ix_r - ix_w):.3e}）")
    else:
        _ok("交互項 SS 兩種寫法相同（符合「最高階交互項不受編碼影響」）")

    if right.attrs["ss_check"].get("passed"):
        _ok("平方和雙路徑驗算通過（Type I 分解 + 殘差 = 總平方和，容差 1e-6）")
    else:
        _err("平方和雙路徑驗算未通過", str(right.attrs["ss_check"]))

    # 防呆本身要真的擋得住
    for bad, what in [
        ("affairs ~ C(rm, Treatment)", "明寫 treatment coding"),
        ("affairs ~ rm", "裸露的字串類別欄"),
    ]:
        try:
            anova3(bad, df, verbose=False)
            _err(f"anova3 沒擋住「{what}」", f"formula={bad!r} 應該要 raise ValueError")
        except ValueError:
            _ok(f"anova3 擋下「{what}」")
        except Exception as e:  # noqa: BLE001
            _err(f"anova3 對「{what}」丟出非預期例外", repr(e))


def _selftest_anova3_balanced() -> None:
    """18-T3 在**平衡設計**上一樣成立 —— 差異的來源是交互作用，不是不平衡。

    完全平衡的 2×2，a 的效果在 b1 是 +2.0、在 b2 是 −1.6634（近乎交叉），
    平均下來主效果只剩 0.168。treatment coding 的 type-III 測的是「b 參照水準上的
    單純效果」，所以 SS 會大到跟真主效果差兩個數量級。
    """
    rng = np.random.default_rng(20260727)
    n = 2088
    cells = {("a1", "b1"): 0.0, ("a2", "b1"): 2.0,
             ("a1", "b2"): 0.0, ("a2", "b2"): -1.6634}
    df = pd.concat(
        [pd.DataFrame({"a": A, "b": B, "y": rng.normal(m, 1.275, n)})
         for (A, B), m in cells.items()],
        ignore_index=True,
    )
    ct = pd.crosstab(df["a"], df["b"]).to_numpy()
    if ct.min() != ct.max():
        _err("平衡設計 fixture 不平衡", f"cell 次數 {ct.tolist()}")
        return

    try:
        bare = anova_lm(smf.ols("y ~ C(a)*C(b)", df, missing="drop").fit(), typ=3)
        right = anova3("y ~ C(a)*C(b)", df, verbose=False)
    except Exception as e:  # noqa: BLE001
        _err("平衡設計上的 18-T3 對照跑失敗", repr(e))
        return

    sb, fb = float(bare.loc["C(a)", "sum_sq"]), float(bare.loc["C(a)", "F"])
    sr, fr = float(right.loc["C(a, Sum)", "sum_sq"]), float(right.loc["C(a, Sum)", "F"])
    ratio = sb / sr if sr else float("inf")
    infos.append(f"  · 平衡 2×2（每 cell n={n}，交叉型交互作用）")
    infos.append(f"  · 裸 anova_lm(typ=3) C(a)：SS={sb:10.2f}  F={fb:9.2f}")
    infos.append(f"  · anova3          C(a, Sum)：SS={sr:10.2f}  F={fr:9.2f}  → 差 {ratio:.1f} 倍")

    if ratio < 10:
        _err("平衡設計上 anova3 與裸 anova_lm(typ=3) 差不到 10 倍",
             f"實際 {ratio:.2f} 倍。防呆失去驗證依據；"
             "怎麼辦：確認 force_sum_coding 還有沒有真的改寫，或 statsmodels 換了預設編碼")
    else:
        _ok(f"平衡設計上 18-T3 仍抓得到差異（C(a) SS 差 {ratio:.1f} 倍）")

    if right.attrs["可信"] and "警告" not in right.columns:
        _ok("滿秩平衡設計不會被降秩防呆誤擋（無「警告」欄、可信=True）")
    else:
        _err("滿秩平衡設計被降秩防呆誤擋", str(right.attrs.get("警告")))


def _mk_rank_deficient() -> pd.DataFrame:
    """仿實測案例：15 類 × 2 類，其中 3 類完全沒有第二種水準 → 3 個空 cell。"""
    rng = np.random.default_rng(20260727)
    lv_a = [f"{i:02d}_類{i}" for i in range(1, 16)]
    missing = {lv_a[4], lv_a[12], lv_a[14]}      # 對應 05／13／X2 三類沒有國外列
    rows = []
    for i, A in enumerate(lv_a):
        rows.append(pd.DataFrame({"a": A, "b": "國內",
                                  "y": rng.normal(7 + 0.1 * i, 1.2, 400)}))
        if A not in missing:
            rows.append(pd.DataFrame({"a": A, "b": "國外",
                                      "y": rng.normal(7.4 + 0.1 * i, 1.2, 30)}))
    return pd.concat(rows, ignore_index=True)


def _selftest_rank_guard() -> None:
    """降秩設計必須被擋下來，而且要擋在「回傳垃圾」之前（實測 18-T3 的第二個坑）。"""
    df = _mk_rank_deficient()

    # 1) 事前偵測：秩與空 cell 都要點名
    try:
        d = design_check("y ~ C(a)*C(b)", df)
    except Exception as e:  # noqa: BLE001
        _err("design_check 跑失敗", repr(e))
        return
    combos = [c for e in d["empty_cells"] for c in e["cells"]]
    infos.append(f"  · 降秩 fixture：設計矩陣 {d['n_cols']} 欄／秩 {d['rank']}，"
                 f"空 cell {len(combos)} 格 → {'、'.join(' × '.join(map(str, c)) for c in combos)}")
    if d["rank_deficient"] and d["deficiency"] == 3 and len(combos) == 3:
        _ok("design_check 事前抓到降秩與 3 個空 cell，並列出是哪些組合")
    else:
        _err("design_check 沒抓到降秩",
             f"deficiency={d['deficiency']}、空 cell={combos}。"
             "怎麼辦：確認 np.linalg.matrix_rank 是否被 exog 的 NaN 干擾")

    # 2) 預設一定要 raise —— 不是印 stderr
    try:
        tbl = anova3("y ~ C(a)*C(b)", df, verbose=False)
        bad = tbl.loc["C(a, Sum)", "F"] == tbl.loc["C(a, Sum):C(b, Sum)", "F"]
        _err("anova3 沒擋住降秩設計",
             f"回傳了表（主效果 F 與交互作用 F 相同={bool(bad)}），"
             "這正是實測回報的靜默垃圾；怎麼辦：檢查 anova3 的事前 design_check 分支")
    except RankDeficientDesignError as e:
        must = ["空 cell", "anova_degrade", "allow_rank_deficient", "Type II"]
        miss = [m for m in must if m not in str(e)]
        if miss:
            _warn("RankDeficientDesignError 訊息缺少關鍵字", f"缺 {miss}")
        else:
            _ok("anova3 對降秩設計 raise RankDeficientDesignError（訊息含空 cell 清單與降級路徑）")
    except Exception as e:  # noqa: BLE001
        _err("anova3 對降秩設計丟出非預期例外", repr(e))

    # 3) 顯式放行時，回傳表必須帶可見的警告欄
    try:
        t = anova3("y ~ C(a)*C(b)", df, verbose=False, allow_rank_deficient=True)
        if "警告" in t.columns and t.attrs["可信"] is False and t.attrs["警告"]:
            _ok("allow_rank_deficient=True 放行，但回傳表帶可見「警告」欄且 attrs['可信']=False")
        else:
            _err("放行時沒有把失敗寫進可見欄位",
                 f"columns={list(t.columns)}、可信={t.attrs.get('可信')}")
    except Exception as e:  # noqa: BLE001
        _err("allow_rank_deficient=True 仍然擋下來", repr(e))

    # 4) 降級路徑要真的跑得出可信的東西（00 §1.6 降級不留空）
    for mc, want in ((MIN_GROUP_N, (2, 3)), (1, (3, 4))):
        try:
            r = anova_degrade("y ~ C(a)*C(b)", df, min_cell=mc, verbose=False)
        except Exception as e:  # noqa: BLE001
            _err(f"anova_degrade（min_cell={mc}）跑失敗", repr(e))
            continue
        t = r["table"]
        trust = isinstance(t, pd.DataFrame) and t.attrs.get("可信") is True
        infos.append(f"  · anova_degrade(min_cell={mc}) → 階梯 {r['階梯']}：{r['實際採用']}")
        if r["階梯"] in want and trust and r["結論弱在哪"] and r["失效證據"]:
            _ok(f"anova_degrade（min_cell={mc}）退到階梯 {r['階梯']}，"
                f"結果可信且四件事（原方法／失效證據／實際採用／結論弱在哪）齊全")
        else:
            _err(f"anova_degrade（min_cell={mc}）降級結果不合格",
                 f"階梯={r['階梯']}（預期 {want}）、可信={trust}、"
                 f"結論弱在哪={r['結論弱在哪']!r}")

    # 5) 無顯式截距不可被誤判成驗算失敗（驗算失敗改成 raise 之後才會咬人）
    rng = np.random.default_rng(7)
    d0 = pd.DataFrame({"g": rng.choice(list("ABC"), 400)})
    d0["y"] = (d0["g"] == "A") * 2.0 + rng.normal(0, 1, 400)
    try:
        t0 = anova3("y ~ 0 + C(g)", d0, verbose=False)
        kind = t0.attrs["ss_check"].get("ss_total_kind", "")
        if t0.attrs["ss_check"]["passed"] and "uncentered" in kind:
            _ok("無顯式截距的模型改用未置中總平方和比對，不再誤判為驗算失敗")
        else:
            _err("無顯式截距的 SS 驗算判斷不對",
                 f"passed={t0.attrs['ss_check']['passed']}、比對對象={kind!r}")
    except SSDoubleCheckError as e:
        _err("無顯式截距的模型被誤判成驗算失敗", str(e).splitlines()[0])
    except Exception as e:  # noqa: BLE001
        _err("無顯式截距的模型丟出非預期例外", repr(e))


def _selftest_rest() -> None:
    rng = np.random.default_rng(20260727)

    # 1) posthoc 決策樹的四條路徑
    n = 60
    same = pd.DataFrame({
        "g": np.repeat(["A", "B", "C"], n),
        "y": np.concatenate([rng.normal(0, 1, n), rng.normal(0.8, 1, n), rng.normal(1.6, 1, n)]),
    })
    hetero = pd.DataFrame({
        "g": np.repeat(["A", "B", "C"], n),
        "y": np.concatenate([rng.normal(0, 1, n), rng.normal(0.5, 1, n), rng.normal(1.0, 6, n)]),
    })
    skewed = pd.DataFrame({
        "g": np.repeat(["A", "B", "C"], n),
        "y": np.concatenate([rng.gamma(1.2, 2, n), rng.gamma(1.2, 2.6, n), rng.gamma(1.2, 3.2, n)]),
    })
    cases = [(same, "tukey"), (hetero, "games_howell"), (skewed, "kruskal_dunn")]
    for d, want in cases:
        try:
            r = posthoc(d, "y", "g")
            if r["method_chosen"] == want:
                _ok(f"posthoc 決策樹 → {want}（{len(r['table'])} 組成對比較）")
            else:
                _warn(f"posthoc 選了 {r['method_chosen']}，預期 {want}",
                      f"模擬資料的前提診斷落在邊界：{r['why']}")
        except Exception as e:  # noqa: BLE001
            _err(f"posthoc（預期 {want}）跑失敗", repr(e))

    try:
        r = posthoc(same, "y", "g", control="A")
        _ok(f"posthoc → dunnett（對照組 A，{len(r['table'])} 個比較）")
    except Exception as e:  # noqa: BLE001
        _err("posthoc dunnett 跑失敗", repr(e))

    try:
        posthoc(same, "y", "g", declared="games_howell")
        _err("declared 不符時沒有擋下來", "16 §8.3：不能看到 p 值再挑方法")
    except ValueError:
        _ok("declared 與決策樹不符時擋下來（防止事後換方法）")
    except Exception as e:  # noqa: BLE001
        _err("declared 檢查丟出非預期例外", repr(e))

    # 2) 效果量三者並報
    try:
        es = effect_sizes(same, dv="y", group="g")
        need = {"effect", "effect_ci_low", "effect_ci_high", "p"}
        if need <= set(es) and all(np.isfinite(es[k]) for k in need):
            _ok(f"effect_sizes（k 組）：{es['interpretation']}")
        else:
            _err("effect_sizes（k 組）缺欄或有 NaN", str({k: es.get(k) for k in need}))
        two = effect_sizes(x1=rng.normal(0, 1, 20), x2=rng.normal(0.5, 1, 18))
        if two["mde"] and np.isfinite(two["mde"]) and two["mde_required"]:
            _ok(f"effect_sizes（兩組, n<30）強制附 MDE：{two['mde']:.4f}")
        else:
            _err("min(n) < 30 但沒有算出 MDE", "16 §4.1 硬規則")
    except Exception as e:  # noqa: BLE001
        _err("effect_sizes 跑失敗", repr(e))

    # 3) chi2_safe / Cramér's V
    try:
        tab = pd.crosstab(
            rng.choice(["男", "女"], 200),
            rng.choice(["高", "中", "低"], 200, p=[0.2, 0.3, 0.5]),
        )
        c = chi2_safe(tab)
        if np.isfinite(c["cramers_v"]) and np.isfinite(c["v_ci_high"]):
            _ok(f"chi2_safe：{c['method']}、V={c['cramers_v']:.4f}"
                f" CI [{c['v_ci_low']:.4f}, {c['v_ci_high']:.4f}]")
        else:
            _err("chi2_safe 沒給出 Cramér's V 或其 CI", str(c))
    except Exception as e:  # noqa: BLE001
        _err("chi2_safe 跑失敗", repr(e))

    # 4) bh_correct 與重複校正防呆
    try:
        t = bh_correct([0.011, 0.012, 0.013, 0.014, 0.015], family="自我檢查")
        b = bh_correct([0.011, 0.012, 0.013, 0.014, 0.015], family="自我檢查", method="bonferroni")
        if int(t["rejected"].sum()) == 5 and int(b["rejected"].sum()) == 0:
            _ok("bh_correct：16 §3.3 的算例重現（m=5 時 BH 全拒絕、Bonferroni 一個都不拒絕）")
        else:
            _err("bh_correct 與 16 §3.3 算例不符",
                 f"BH 拒絕 {int(t['rejected'].sum())}／Bonferroni 拒絕 {int(b['rejected'].sum())}")
        try:
            bh_correct([0.01, 0.02], already_fwer_controlled=True)
            _err("bh_correct 沒擋住重複校正", "16 §3.2")
        except ValueError:
            _ok("bh_correct 擋下 FWER 已控制後的二次校正")
    except Exception as e:  # noqa: BLE001
        _err("bh_correct 跑失敗", repr(e))

    # 5) 迴歸診斷三件套
    try:
        n2 = 200
        x1 = rng.normal(size=n2)
        x2 = 0.8 * x1 + rng.normal(scale=0.6, size=n2)
        g = rng.choice(["A", "B", "C"], n2)
        y = 1 + 2 * x1 - 0.5 * x2 + (g == "B") * 1.5 + rng.normal(size=n2)
        df = pd.DataFrame({"y": y, "x1": x1, "x2": x2, "g": g})
        m_full = smf.ols("y ~ x1 + x2 + C(g)", df, missing="drop").fit()
        m_red = smf.ols("y ~ x1 + x2", df, missing="drop").fit()
        vt = vif_table(m_full)
        _ok(f"vif_table：{len(vt)} 項，最大 GVIF^(1/(2df))={vt['GVIF^(1/(2df))'].max():.4f}")
        nf = nested_f(m_red, m_full)
        _ok(f"nested_f：F={nf['F']:.4f}、p={nf['p']:.4g}、df_diff={nf['df_diff']:.0f}"
            f"、三角驗證{nf['triangulation']}")
        try:
            nested_f(m_full, m_red)
            _err("nested_f 參數傳反時沒擋住", "08 §二：R 與 Python 的呼叫方向相反，最常見的錯")
        except ValueError:
            _ok("nested_f 擋下參數傳反（SSE_R < SSE_C 在數學上不可能）")
        em = emmeans(m_full, df, "g")
        ec = emm_contrasts(m_full, df, "g")
        _ok(f"emmeans：{len(em)} 個 level 的調整後均值；emm_contrasts：{len(ec)} 個對比（BH）")

        # 雙路徑驗算 1（00 §1.3）：連續變數的 GVIF 必須等於 1/(1-R²_j)
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        m_cont = smf.ols("y ~ x1 + x2", df, missing="drop").fit()
        vt2 = vif_table(m_cont).set_index("term")
        X = np.asarray(m_cont.model.exog)
        ref = {name: variance_inflation_factor(X, i)
               for i, name in enumerate(m_cont.model.exog_names) if name != "Intercept"}
        gaps = {k: abs(float(vt2.loc[k, "GVIF"]) - v) for k, v in ref.items()}
        if max(gaps.values()) < 1e-8:
            _ok(f"vif_table 雙路徑驗算：GVIF 與 variance_inflation_factor 一致"
                f"（最大差 {max(gaps.values()):.2e}，值 {ref}）")
        else:
            _err("vif_table 與 variance_inflation_factor 不一致", str(gaps))

        # 雙路徑驗算 2：無共變量時 EMM 必須等於各組樣本平均
        m_g = smf.ols("y ~ C(g)", df, missing="drop").fit()
        em2 = emmeans(m_g, df, "g").set_index("g")["emmean"]
        raw = df.groupby("g")["y"].mean()
        gap = float((em2 - raw).abs().max())
        if gap < 1e-8:
            _ok(f"emmeans 雙路徑驗算：無共變量時 EMM = 各組樣本平均（最大差 {gap:.2e}）")
        else:
            _err("emmeans 與各組樣本平均不符", f"最大差 {gap:.6g}")

        # 降級路徑也要真的跑得動
        for mth in ("bootstrap_bca", "manual_t_bh"):
            r2 = posthoc(df.rename(columns={"g": "grp"}), "y", "grp", method=mth, B=400)
            _ok(f"posthoc method={mth} 可跑（{len(r2['table'])} 列，"
                f"fwer_controlled={r2['fwer_controlled']}）")

        # chi2_safe 的 Fisher 分支
        small = pd.DataFrame([[8, 2], [1, 3]])
        cs = chi2_safe(small)
        if cs["approximation"] == "exact":
            _ok(f"chi2_safe 2×2 期望次數不足 → {cs['method']}，p={cs['p']:.4f}")
        else:
            _err("chi2_safe 沒切到 Fisher 精確檢定", str(cs))

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        tmp = Path(__file__).resolve().parent / "__selftest_plot_lm.png"
        fig = plot_lm(m_full, save_to=tmp)
        size = tmp.stat().st_size if tmp.exists() else 0
        plt.close(fig)
        if size > 0:
            _ok(f"plot_lm：四圖產出 {size:,} bytes")
            tmp.unlink()
        else:
            _err("plot_lm 存檔為 0 bytes", "怎麼辦：檢查 matplotlib backend 與字型設定")
    except Exception as e:  # noqa: BLE001
        _err("迴歸診斷自我檢查失敗", repr(e))


def _main() -> int:
    ap = GateArgumentParser(
        description="統計推論工具（type-III ANOVA／事後檢定／效果量）的自我檢查",
        epilog="本檔是純函式庫，不讀專案資料，所以沒有「專案代號」位置參數。",
    )
    ap.add_argument("--self-test", action="store_true",
                    help="跑內建斷言（含 anova3 vs anova_lm(typ=3) 的差異驗證）")
    ap.add_argument("--verbose", action="store_true", help="連通過項也列出")
    args = ap.parse_args()

    if not args.self_test:
        print(__doc__)
        print("要驗證安裝是否正確：python stats_utils.py --self-test --verbose")
        return EX_OK

    print("=" * 68)
    print("stats_utils —— 自我檢查")
    print("=" * 68)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for fn in (_selftest_anova3, _selftest_anova3_balanced,
                   _selftest_rank_guard, _selftest_rest):
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                _err(f"{fn.__name__} 異常中止", repr(e))

    if args.verbose and infos:
        print("\n通過")
        print("-" * 68)
        for m in infos:
            print(f"  ✅ {m}" if not m.startswith("  ") else m)

    if warnings_:
        print("\n⚠ 可用，但這幾項要留意")
        print("-" * 68)
        for m in warnings_:
            print(f"  ⚠ {m}")

    if errors:
        print("\n⛔ 不可使用，必須先處理")
        print("-" * 68)
        for m in errors:
            print(f"  ⛔ {m}")

    print("\n" + "=" * 68)
    n_ok = sum(1 for m in infos if not m.startswith("  "))
    if errors:
        print(f"結果：{len(errors)} 個 error、{len(warnings_)} 個 warning → 不可使用")
        return EX_ERROR
    if warnings_:
        print(f"結果：{len(warnings_)} 個 warning → 可用，部分路徑要留意（通過 {n_ok} 項）")
        return EX_WARN
    print(f"結果：全部通過（{n_ok} 項）→ 可用")
    return EX_OK


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ stats_utils.py 本身失敗：{type(exc).__name__}: {exc}",
              file=sys.stderr)
        print(f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
