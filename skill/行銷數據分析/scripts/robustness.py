#!/usr/bin/env python3
"""
穩健性檢定 R1–R4（16 §五）——「換了什麼 → 結論有沒有變」的對照表。

這支腳本只回答一個問題：**換一批資料、換個做法，這個結論還在嗎。**
$p<0.001$ 只說「在虛無假設下這麼極端的資料很罕見」，主管真正要問的是前面那句
（16 §5.1）。一份寫得出「四項穩健性檢定，結論在三項下維持不變，在時間切點下
方向不變但幅度從 +1,850 元降到 +1,100 元」的報告，說服力遠高於一份只有 p 值的
報告，**而且它讓自己可被反駁**。

═══ 核心規則（放在最前面，因為它比任何門檻都重要）═══
**結論翻轉就必須寫進報告，不准只報對自己有利的那一版。**
本腳本的三個機械保證：
  · 跑過的每一個設定都會出現在輸出表裡，**包含把主結論打掉的那幾列**；
    沒有「只輸出通過的變體」的旗標，也沒有「挑一版當代表」的介面。
  · 有翻轉時退出碼是 2 而不是 0 —— 讓驅動腳本擋得住「全綠了就照抄結論」。
  · 主控台與 JSON 各印一份「必須寫進報告」的翻轉清單，逐條點名是哪個設定、
    翻的是方向還是顯著性、幅度多少。

四個軸（16 §5.2）。§九 維護條款寫死「只能在這四個軸上細分，**不要開第五個軸**」：

  R1 離群敏感度   動「樣本中的少數個體」  移除 Cook's D 最高 1% / 5% 各重估一次
  R2 子樣本穩定度 動「抽到的是誰」        cluster bootstrap（以顧客重抽）B=1,000
  R3 模型設定     動「你做的建模選擇」    至少四組對照（標準誤／共變量／轉換／檢定）
  R4 時間切點     動「你選的那個日期」    as_of ±1、±3 個月；觀察窗 6／12／24 個月

R3 為什麼把「換一種檢定」與「多重比較校正前後」也收進來：
  16 §5.2 的 R3 原文列的是「連結函數／共變量／轉換／標準誤」四組，沒有明列
  參數 vs 無母數、也沒有明列 BH 校正前後。但這兩者動的都是「你做的建模選擇」，
  §九 又禁止開第五個軸 —— 所以放在 R3 底下細分，不另立 R5／R6。

為什麼「換標準誤」那一組要單獨拉出來講（16 §七 P7）：
  100 位顧客 × 24 個月 = 2,400 列，預設 SE 得係數 1,850 元、$p=0.002$，據此把
  促銷檔期從 4 檔加到 8 檔、新增成本 480 萬；改 cluster-robust（cluster=cust_id）
  後 $p=0.11$ —— **根本不顯著**。有效樣本數接近 100 而非 2,400。
  16 §七 P7 是硬規則：**任何「一列不是一位顧客」的迴歸禁用預設 SE**，與 18-T3
  同級（兩者都是不報錯只給錯數字）。本腳本偵測到「一列不是一個 cluster」卻拿不到
  cluster 欄時**直接退 error**，不是印個警告讓人自己決定要不要理。

  【實測】ntu_creditcard 樣本（7,764 筆交易 / 100 位顧客，平均 77.6 列一人）：
  刷卡金額 ~ 刷卡地點（國外=1），naive SE 1,059.9、p = 0.0000497（顯著）；
  改 cluster-robust（cluster=客戶ID）後 SE 2,411.4、p = 0.0868（不顯著）。
  SE 放大 2.28 倍，**顯著性翻轉**，而係數 4,199.6 元一個字都沒動。
  出處：00_source_archive/local/資料集剖析/samples/ntu_creditcard__transactions.parquet，
  用本腳本 --self-test 之外的實跑量到（2026-07-28）。

穩健 ≠ 因果。四項全過只代表「這個關聯不是某個建模選擇撐出來的」，
證據等級仍由 00 §1.5 的識別條件決定，穩健性檢定**永遠不會升級證據等級**。

用法：
    python robustness.py 2026Q3_電商 \
        --data 分析資料表/月消費面板.parquet \
        --outcome 月消費 --treatment 促銷月 \
        --covariates 客層,tenure_days \
        --cluster-col 客戶編號 --date-col 月份 --as-of 2026-06-30

    # 只有兩組比較（沒有共變量）也可以，treatment 給二元欄即可
    python robustness.py 2026Q3_電商 --data ... --outcome 客單價 --treatment 群別

    python robustness.py --self-test

輸出：
    模型輸出/robustness_<model>.csv        16 §5.3 的固定 schema
        check_id / variant / coef / se / p / delta_pct / verdict / note
        verdict ∈ {stable, stable_with_caveat, unstable, not_run}
    統計表/迴歸與診斷/穩健性對照表_<model>.csv   人看的「換了什麼→結論有沒有變」
    模型輸出/robustness_<model>.json       機器可讀，供 build_report 引用
    主控台另印 16 §5.3 的固定四段句型與結論句，可直接貼進報告

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 四項全 stable
    1  = 有 error 擋住（panel 結構卻沒有 cluster 欄 = P7 禁行；資料不足以估計）
    2  = 有 unstable／stable_with_caveat／not_run —— 可往下，但報告要逐條寫明
    64 = 用法錯誤
    70 = 腳本自身異常
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import project_dir  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 門檻。有出處的標出處，本腳本補訂的標【補訂】並在 --help 尾巴說明 ──────
ALPHA = 0.05                    # 16 §一：顯著水準；放寬要照 §8.4 附加規則 2 聲明
COOKS_TOP_PCTS = (1.0, 5.0)     # 16 §5.2 R1：移除 Cook's D 最高 1% 與 5%
COEF_CHANGE_UNSTABLE = 50.0     # 16 §5.2 R1：|β̂| 變動 > 50% 判不穩健
COEF_CHANGE_CAVEAT = 25.0       # 【補訂】25–50% 這一段判 stable_with_caveat。
                                # reference 只給 50% 一條線，但 40% 的變動寫成
                                # 「穩健」會誤導讀者，落到 07 §7.3 那種「可用但
                                # 正文要標註」的帶子最貼近原意
CROSS_ZERO_MAX = 5.0            # 16 §5.2 R2：bootstrap 係數跨 0 比例 > 5% 判不穩健
CROSS_ZERO_CAVEAT = 2.0         # 【補訂】2–5% 這一段標註，同上理由
DIRECTION_CONSISTENT_MIN = 80.0  # 16 §5.2 R3：方向一致的設定 < 80% 判不穩健
JACCARD_MIN = 0.6               # 16 §5.2 R4：名單重疊 < 0.6 判不穩健【推導，待驗證】
BOOT_B = 1000                   # 16 §5.2 R2：cluster bootstrap B = 1,000
BOOT_B_MIN = 200                # 【補訂】低於此連 5% 的跨 0 比例都量不準
                                # （B=200 時 5% 是 10 個複本，MC 標準誤 1.5pp）
R3_MIN_VARIANTS = 4             # 16 §5.2 R3：「至少四組對照」
SMALL_N = 30                    # 16 §4.1：任一組 n < 30 必須附 MDE
LIST_PCT = 10.0                 # 【補訂】R4 名單 Jaccard 的名單定義見 r4_time()

VERDICTS = ("stable", "stable_with_caveat", "unstable", "not_run")

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


def _py(v: Any) -> Any:
    """numpy 純量 → 原生 Python 型別。

    bootstrap 的分位數、Cook's D 的索引、group 標籤全是 numpy 型別，它們會一路
    帶進結果 dict，json.dumps 到那裡才丟 TypeError —— 而且是在四項全跑完、CSV
    都寫好之後才炸，退出碼 70 蓋掉前面的結論。在來源轉掉。
    """
    if v is None:
        return None
    if isinstance(v, float) and not math.isfinite(v):
        return None            # NaN/inf 不是合法 JSON，寫出去會變 Infinity
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy 型別時，讓它寫得出去而不是整支腳本掛掉。"""
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    return str(o)


# ══════════════════════════════════════════════════════════════
#  一、設計矩陣與估計核心
# ══════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Spec:
    """主結論長什麼樣子。treatment 的係數就是「主結論的那個數字」。"""
    outcome: str
    treatment: str
    covariates: tuple[str, ...] = ()
    cluster_col: str | None = None
    date_col: str | None = None
    id_col: str | None = None


@dataclass
class Design:
    y: np.ndarray
    X: np.ndarray
    names: list[str]
    j: int                                  # treatment 在 X 裡的欄位序號
    clusters: np.ndarray | None = None
    ids: np.ndarray | None = None
    dates: np.ndarray | None = None
    treat_desc: str = ""
    binary_treat: bool = False
    n_dropped: int = 0
    covariate_cols: list[int] = field(default_factory=list)


def _as_numeric_treatment(s: pd.Series, name: str) -> tuple[np.ndarray, str, bool]:
    """把 treatment 轉成一欄數字。

    非數值且剛好兩個水準 → 排序後的第二個水準編為 1（誰是 1 一定要寫進報告，
    否則係數的符號沒有意義）。三個以上水準不接受：主結論的「那一個數字」
    在多水準下不存在，那是 ANOVA + 事後檢定的問題（16 §八），不是本腳本的。
    """
    if pd.api.types.is_bool_dtype(s):
        return s.astype(float).to_numpy(), f"{name}（True=1）", True
    if pd.api.types.is_numeric_dtype(s):
        vals = pd.unique(s.dropna())
        binary = len(vals) == 2
        return s.astype(float).to_numpy(), name, binary
    levels = sorted(pd.unique(s.dropna()).tolist(), key=str)
    if len(levels) != 2:
        raise ValueError(
            f"treatment 欄「{name}」有 {len(levels)} 個水準，本腳本只處理數值或二元變數。\n"
            f"  為什麼：穩健性檢定追蹤的是「主結論的那一個係數」，多水準下那個係數不存在。\n"
            f"  怎麼辦：① 先用 stats_utils.posthoc() 依 16 §8.4 決定要比哪兩個水準，"
            f"再把資料篩成兩組丟進來；② 或自己造一個二元旗標欄（例如 高價值群=1）。"
        )
    x = (s.astype(str) == str(levels[1])).astype(float).to_numpy()
    return x, f"{name}（{levels[1]}=1、{levels[0]}=0）", True


def build_design(df: pd.DataFrame, spec: Spec) -> Design:
    """組設計矩陣。缺值列直接剔除並回報數量 —— 不在這裡補值（18-E22）。"""
    need = [spec.outcome, spec.treatment, *spec.covariates]
    for extra in (spec.cluster_col, spec.date_col, spec.id_col):
        if extra:
            need.append(extra)
    missing = [c for c in dict.fromkeys(need) if c not in df.columns]
    if missing:
        raise ValueError(
            f"資料裡找不到這些欄位：{'、'.join(missing)}\n"
            f"  現有欄位：{'、'.join(map(str, df.columns[:30]))}"
            f"{'…' if len(df.columns) > 30 else ''}\n"
            f"  怎麼辦：確認 --outcome／--treatment／--covariates 的欄名拼寫，"
            f"欄名含空白或括號時整串用引號包起來。"
        )

    core = [spec.outcome, spec.treatment, *spec.covariates]
    if spec.cluster_col:
        core.append(spec.cluster_col)
    sub = df[list(dict.fromkeys(need))].copy()
    keep = sub[list(dict.fromkeys(core))].notna().all(axis=1)
    n_dropped = int((~keep).sum())
    sub = sub[keep].reset_index(drop=True)
    if len(sub) < 10:
        raise ValueError(
            f"剔除缺值後只剩 {len(sub)} 列（原 {len(df)} 列）。\n"
            f"  16 §4.1：n < 10 時任何漸近近似都不可信，穩健性檢定本身也失去意義。\n"
            f"  怎麼辦：回上游查缺值來源（check_data_quality.py），不要在這裡補值。"
        )

    y = pd.to_numeric(sub[spec.outcome], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise ValueError(
            f"結果變數「{spec.outcome}」有非數值或無限大的值。\n"
            f"  怎麼辦：先跑 check_data_quality.py 找出那幾列，"
            f"確認是輸入錯誤還是真的極端值（18 的處置順序：先轉換再看離群）。"
        )
    t, treat_desc, binary = _as_numeric_treatment(sub[spec.treatment], spec.treatment)

    cols = [np.ones(len(sub)), t]
    names = ["截距", spec.treatment]
    cov_idx: list[int] = []
    for c in spec.covariates:
        s = sub[c]
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
            cols.append(s.astype(float).to_numpy())
            names.append(str(c))
            cov_idx.append(len(cols) - 1)
        else:
            d = pd.get_dummies(s.astype(str), prefix=str(c), drop_first=True)
            for cc in d.columns:
                cols.append(d[cc].to_numpy(dtype=float))
                names.append(str(cc))
                cov_idx.append(len(cols) - 1)

    X = np.column_stack(cols)
    rank = int(np.linalg.matrix_rank(X))
    if rank < X.shape[1]:
        raise ValueError(
            f"設計矩陣降秩（{X.shape[1]} 欄但秩只有 {rank}）—— 共變量之間完全共線。\n"
            f"  為什麼要擋：降秩時係數不唯一，穩健性檢定會在「同一組資料的不同解」"
            f"之間跳動，量到的不是穩健性（同 18-T3 的病理：不報錯只給錯數字）。\n"
            f"  怎麼辦：用 stats_utils.vif_table() 找出共線的那幾欄，擇一保留。"
        )

    clusters = sub[spec.cluster_col].to_numpy() if spec.cluster_col else None
    id_col = spec.id_col or spec.cluster_col
    ids = sub[id_col].to_numpy() if id_col else None
    dates = (pd.to_datetime(sub[spec.date_col], errors="coerce").to_numpy()
             if spec.date_col else None)

    return Design(y=y, X=X, names=names, j=1, clusters=clusters, ids=ids,
                  dates=dates, treat_desc=treat_desc, binary_treat=binary,
                  n_dropped=n_dropped, covariate_cols=cov_idx)


def ols_fit(y: np.ndarray, X: np.ndarray, j: int = 1, *,
            cov_type: str = "naive",
            clusters: np.ndarray | None = None) -> dict[str, Any]:
    """OLS + 三種標準誤。回傳第 j 個係數的 coef / se / t / p / df。

    自己寫而不直接呼叫 statsmodels 的理由：bootstrap 要重估 1,000 次，而且
    cluster-robust 的自由度（G−1，不是 n−k）必須看得見 —— 那正是 P7 的重點。
    正確性靠自我測試對 statsmodels 逐項比對（見 _selftest 的 ①②③）。

    cov_type：
      naive    古典 OLS：σ²(X'X)⁻¹，df = n−k
      hc1      異質變異穩健（White/HC1），df = n−k
      cluster  以 cluster 為單位的三明治估計，df = **G−1**
               修正項 c = G/(G−1) · (n−1)/(n−k)，與 statsmodels 的
               use_correction=True 一致（不一致的話兩邊的數字對不起來，
               而讀者多半是拿 statsmodels 復核的）
    """
    n, k = X.shape
    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta

    if cov_type == "naive":
        if n <= k:
            raise ValueError(f"樣本數 {n} 不大於參數數 {k}，估不出殘差變異")
        s2 = float(e @ e) / (n - k)
        V = s2 * XtX_inv
        df = float(n - k)
        n_g = None
    elif cov_type == "hc1":
        meat = (X * (e ** 2)[:, None]).T @ X
        V = XtX_inv @ meat @ XtX_inv * (n / (n - k))
        df = float(n - k)
        n_g = None
    elif cov_type == "cluster":
        if clusters is None:
            raise ValueError("cluster-robust 標準誤需要 cluster 欄")
        uniq, inv = np.unique(clusters, return_inverse=True)
        G = len(uniq)
        if G < 2:
            raise ValueError(f"只有 {G} 個 cluster，算不出 cluster-robust 標準誤")
        meat = np.zeros((k, k))
        Xe = X * e[:, None]
        for g in range(G):
            sg = Xe[inv == g].sum(axis=0)
            meat += np.outer(sg, sg)
        c = (G / (G - 1)) * ((n - 1) / (n - k))
        V = c * (XtX_inv @ meat @ XtX_inv)
        df = float(G - 1)
        n_g = G
    else:
        raise ValueError(f"未知的 cov_type：{cov_type!r}")

    se = float(np.sqrt(max(V[j, j], 0.0)))
    coef = float(beta[j])
    t_stat = coef / se if se > 0 else float("nan")
    p = float(2 * st.t.sf(abs(t_stat), df)) if np.isfinite(t_stat) and df > 0 else float("nan")
    return {"coef": coef, "se": se, "t": float(t_stat), "p": p,
            "df": df, "n": int(n), "k": int(k), "cov_type": cov_type,
            "n_clusters": n_g, "beta": beta, "resid": e}


def cooks_distance(y: np.ndarray, X: np.ndarray, j: int = 1
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """回傳 (Cook's D, 該點對第 j 個係數的 DFBETA, 槓桿值 h)。

    D_i = e_i² / (k·s²) · h_i/(1−h_i)²  —— 門檻 1.0 / 0.5 / 4n 見 05 §7.3，
    本腳本不重寫門檻，只用 D 排序取前 1% / 5%（16 §5.2 R1 的做法）。
    DFBETA_i = (X'X)⁻¹x_i e_i /(1−h_i) 是**精確的** leave-one-out 差值，
    不必真的重跑 n 次迴歸 —— 用它找「拿掉哪一點結論會翻」最快。
    """
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    H = X @ XtX_inv
    h = np.einsum("ij,ij->i", H, X)
    beta = XtX_inv @ (X.T @ y)
    e = y - X @ beta
    s2 = float(e @ e) / max(n - k, 1)
    denom = np.clip(1 - h, 1e-12, None)
    D = (e ** 2) / (k * s2) * h / denom ** 2 if s2 > 0 else np.zeros(n)
    dfbeta = (XtX_inv[j] @ X.T) * e / denom
    return D, dfbeta, h


# ══════════════════════════════════════════════════════════════
#  二、判定：什麼叫「結論變了」
# ══════════════════════════════════════════════════════════════
def classify(base: dict[str, Any], var: dict[str, Any], *,
             scale_comparable: bool = True,
             alpha: float = ALPHA) -> dict[str, Any]:
    """比對一個變體與基準，回傳 {verdict, 結論有沒有變, delta_pct, 說明}。

    三條判「不穩健」的線全部照 16 §5.2 R1 的原文：
      · 主係數**符號翻轉**
      · 顯著性在 α 兩側跨越
      · |β̂| 變動 > 50%
    前兩條在任何變體都適用；第三條只在「幅度可比」時適用 —— 換轉換（ln／sqrt）
    或改用秩檢定之後，係數的單位已經不一樣，拿去算變動百分比是拿蘋果比橘子，
    那個數字比不報還糟。這種變體的 delta_pct 一律留 None 並在 note 寫明。
    """
    b, v = base["coef"], var["coef"]
    pb, pv = base["p"], var["p"]
    sig_b = bool(np.isfinite(pb) and pb < alpha)
    sig_v = bool(np.isfinite(pv) and pv < alpha)

    flips: list[str] = []
    if np.isfinite(b) and np.isfinite(v) and b != 0 and v != 0 and np.sign(b) != np.sign(v):
        flips.append(f"方向翻轉（{b:+.4g} → {v:+.4g}）")
    if sig_b != sig_v:
        flips.append(f"顯著性翻轉（p {pb:.4g} → {pv:.4g}，α={alpha}）")

    delta = None
    if scale_comparable and np.isfinite(b) and b != 0 and np.isfinite(v):
        delta = (v - b) / abs(b) * 100.0

    verdict = "stable"
    why = "方向、顯著性、幅度都沒變"
    if flips:
        verdict = "unstable"
        why = "；".join(flips)
    elif delta is not None and abs(delta) > COEF_CHANGE_UNSTABLE:
        verdict = "unstable"
        why = f"幅度變動 {delta:+.1f}%，超過 16 §5.2 R1 的 ±{COEF_CHANGE_UNSTABLE:.0f}%"
    elif delta is not None and abs(delta) > COEF_CHANGE_CAVEAT:
        verdict = "stable_with_caveat"
        why = (f"幅度變動 {delta:+.1f}%（{COEF_CHANGE_CAVEAT:.0f}–"
               f"{COEF_CHANGE_UNSTABLE:.0f}% 帶，本腳本補訂）")
    elif not scale_comparable:
        why = "方向與顯著性都沒變（尺度已變，幅度不可比）"

    return {"verdict": verdict, "結論有沒有變": "、".join(flips) if flips else "沒變",
            "delta_pct": delta, "說明": why,
            "方向": "正" if v > 0 else ("負" if v < 0 else "零"),
            "是否顯著": "顯著" if sig_v else "n.s."}


def worst_verdict(vs: list[str]) -> str:
    """一項檢定內部有多個變體時，取最壞的那一個當該項判定。

    為什麼不取多數決：核心規則是「結論翻轉就必須寫進報告」。四個變體裡有一個
    翻掉，該項就不是穩健的 —— 用多數決會讓那一個翻轉被投票投掉，正好是本腳本
    要防的事。
    """
    for level in ("unstable", "stable_with_caveat", "not_run", "stable"):
        if level in vs:
            return level
    return "not_run"


# ══════════════════════════════════════════════════════════════
#  三、R1 離群敏感度
# ══════════════════════════════════════════════════════════════
def r1_influence(d: Design, base: dict[str, Any], *, alpha: float = ALPHA,
                 verbose: bool = True) -> dict[str, Any]:
    """移除 Cook's D 最高的 1% 與 5% 各重估一次（16 §5.2 R1）。

    另加一個「最具影響力的單一點」變體：n 小的時候 1% 也只有 1 個點，兩者會重疊；
    n 大的時候 1% 是好幾十個點，個別的翻轉點會被平均掉。這是同一個軸（個體）上的
    細分，不是第五個軸。它同時回答 R1 最實用的問題：**有沒有哪一個人，拿掉他
    結論就不成立了。**
    """
    n = len(d.y)
    D, dfbeta, _ = cooks_distance(d.y, d.X, d.j)
    order = np.argsort(-D)
    rows: list[dict[str, Any]] = []

    for pct in COOKS_TOP_PCTS:
        # 至少移一個點：n=200 時 1% = 2 個點，n=50 時四捨五入是 0 個 ——
        # 「移除 0 個點」等於沒做這道檢定，卻會在報告裡看起來像做過了
        m = max(1, int(round(n * pct / 100.0)))
        drop = order[:m]
        keep = np.setdiff1d(np.arange(n), drop, assume_unique=False)
        try:
            f = ols_fit(d.y[keep], d.X[keep], d.j, cov_type=base["cov_type"],
                        clusters=d.clusters[keep] if d.clusters is not None else None)
        except (ValueError, np.linalg.LinAlgError) as e:
            rows.append({"variant": f"移除 Cook's D 最高 {pct:.0f}%（{m} 列）",
                         "coef": None, "se": None, "p": None, "delta_pct": None,
                         "verdict": "not_run", "note": f"重估失敗：{e}",
                         "結論有沒有變": "算不出來", "scale_comparable": True})
            continue
        c = classify(base, f, alpha=alpha)
        rows.append({
            "variant": f"移除 Cook's D 最高 {pct:.0f}%（{m} 列）",
            "coef": f["coef"], "se": f["se"], "p": f["p"],
            "delta_pct": c["delta_pct"], "verdict": c["verdict"],
            "note": (f"最大 Cook's D = {D[order[0]]:.4g}；{c['說明']}"),
            "結論有沒有變": c["結論有沒有變"], "方向": c["方向"],
            "是否顯著": c["是否顯著"], "scale_comparable": True,
        })
        if verbose:
            detail(f"移除最高 {pct:.0f}%（{m} 列）→ 係數 {base['coef']:+.4g} → "
                   f"{f['coef']:+.4g}，p {base['p']:.4g} → {f['p']:.4g}｜{c['verdict']}")

    # 最壞單點：先用 DFBETA 挑候選（精確 LOO 差值，不必重跑 n 次），再實際重估驗證
    worst_i = int(np.argmax(np.abs(dfbeta)))
    keep = np.delete(np.arange(n), worst_i)
    try:
        f1 = ols_fit(d.y[keep], d.X[keep], d.j, cov_type=base["cov_type"],
                     clusters=d.clusters[keep] if d.clusters is not None else None)
        c1 = classify(base, f1, alpha=alpha)
        who = ""
        if d.ids is not None:
            who = f"（id={d.ids[worst_i]}）"
        rows.append({
            "variant": f"移除最具影響力的單一列 #{worst_i}{who}",
            "coef": f1["coef"], "se": f1["se"], "p": f1["p"],
            "delta_pct": c1["delta_pct"], "verdict": c1["verdict"],
            "note": (f"該列 Cook's D = {D[worst_i]:.4g}、DFBETA = {dfbeta[worst_i]:+.4g}；"
                     f"{c1['說明']}"),
            "結論有沒有變": c1["結論有沒有變"], "方向": c1["方向"],
            "是否顯著": c1["是否顯著"], "scale_comparable": True,
        })
        if verbose:
            detail(f"移除最壞單點 #{worst_i}{who} → 係數 {f1['coef']:+.4g}、"
                   f"p {f1['p']:.4g}｜{c1['verdict']}")
    except (ValueError, np.linalg.LinAlgError) as e:
        rows.append({"variant": "移除最具影響力的單一列", "coef": None, "se": None,
                     "p": None, "delta_pct": None, "verdict": "not_run",
                     "note": f"重估失敗：{e}", "結論有沒有變": "算不出來",
                     "scale_comparable": True})

    v = worst_verdict([r["verdict"] for r in rows])
    summary = {
        "check_id": "R1", "動什麼": "樣本中的少數個體", "verdict": v,
        "note": _r1_note(rows, v),
        "最大CookD": _py(float(D.max())), "n": n,
        "最壞單點索引": worst_i,
        "最壞單點id": _py(d.ids[worst_i]) if d.ids is not None else None,
    }
    return {"summary": summary, "rows": rows}


def _r1_note(rows: list[dict[str, Any]], v: str) -> str:
    flipped = [r for r in rows if r["verdict"] == "unstable"]
    if not flipped:
        return "移除高影響點後方向、顯著性與幅度皆未變"
    parts = [f"{r['variant']}：{r['結論有沒有變']}" for r in flipped]
    return ("結論對少數個體敏感 —— " + "；".join(parts)
            + "。先分辨那幾列是輸入錯誤還是真實的次族群（18：占比 < 1% 且無結構"
              "＝單點，查輸入錯誤；≥ 5% 或密度圖雙峰＝次族群，不准刪，分開建模），"
              "兩種處置寫進報告，不要只報留著它們的那一版")


# ══════════════════════════════════════════════════════════════
#  四、R2 子樣本穩定度（cluster bootstrap）
# ══════════════════════════════════════════════════════════════
def r2_bootstrap(d: Design, base: dict[str, Any], *, B: int = BOOT_B,
                 seed: int = 42, alpha: float = ALPHA,
                 verbose: bool = True) -> dict[str, Any]:
    """cluster bootstrap，以 cluster（顧客）為重抽單位（16 §5.2 R2）。

    **cluster bootstrap 不是可選項。** 交易列資料直接對「列」重抽會低估變異 ——
    同一位顧客的 10 筆交易不是 10 個獨立觀測（ICC 判準見 05 §1.3）。重抽單位
    必須是分析想推論的單位，也就是顧客。沒給 cluster 欄時本函式退回列重抽，
    並在 note 明講「這次量到的變異偏小」——不是靜默照做。

    分群的 bootstrap ARI 不在這裡：流程（有放回抽樣 n 位、B=200）與門檻
    （ARI 中位數 0.60／0.75）是 07 §7.2／§7.3 的權責，16 §5.2 的 ⚠ 註記明訂
    「一律交叉引用，不重寫」—— 重寫就會分岔，同一份報告兩章互打。
    """
    rng = np.random.default_rng(seed)
    n = len(d.y)
    if d.clusters is not None:
        uniq, inv = np.unique(d.clusters, return_inverse=True)
        idx_by_g = [np.flatnonzero(inv == g) for g in range(len(uniq))]
        unit = f"cluster={len(uniq)} 個"
        row_level = False
    else:
        idx_by_g = [np.array([i]) for i in range(n)]
        unit = "列（無 cluster 欄）"
        row_level = True

    G = len(idx_by_g)
    coefs: list[float] = []
    n_fail = 0
    for _ in range(B):
        pick = rng.integers(0, G, size=G)
        idx = np.concatenate([idx_by_g[g] for g in pick])
        try:
            f = ols_fit(d.y[idx], d.X[idx], d.j, cov_type="naive")
            coefs.append(f["coef"])
        except (ValueError, np.linalg.LinAlgError):
            n_fail += 1

    if len(coefs) < max(20, B // 10):
        return {"summary": {"check_id": "R2", "動什麼": "抽到的是誰",
                            "verdict": "not_run",
                            "note": f"{B} 次重抽有 {n_fail} 次估不出來（多半是某些"
                                    f"複本裡 treatment 只剩一個水準），樣本結構不"
                                    f"支援 cluster bootstrap。怎麼辦：確認每個 "
                                    f"cluster 內是否都只有單一 treatment 值 —— "
                                    f"若是，重抽單位要改成分層重抽"},
                "rows": [{"variant": f"cluster bootstrap（{unit}，B={B}）",
                          "coef": None, "se": None, "p": None, "delta_pct": None,
                          "verdict": "not_run", "note": f"有效複本僅 {len(coefs)}／{B}",
                          "結論有沒有變": "算不出來", "scale_comparable": True}]}

    arr = np.asarray(coefs, dtype=float)
    b = base["coef"]
    # 「跨 0 比例」= 與點估計異號（含正好為 0）的複本占比。這比「CI 有沒有含 0」
    # 更嚴：CI 是兩個分位點，跨 0 比例看的是整個分布有多少質量跑到對面去。
    cross = float(np.mean((np.sign(arr) != np.sign(b)) | (arr == 0)) * 100)
    lo, hi = (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))
    boot_se = float(arr.std(ddof=1))

    if cross > CROSS_ZERO_MAX:
        v = "unstable"
    elif cross > CROSS_ZERO_CAVEAT:
        v = "stable_with_caveat"
    else:
        v = "stable"

    note = (f"{unit}，B={B}；95% 分位區間 [{lo:.4g}, {hi:.4g}]，"
            f"跨 0 比例 {cross:.2f}%（門檻 {CROSS_ZERO_MAX:.0f}%）；"
            f"bootstrap SE {boot_se:.4g} vs 基準 SE {base['se']:.4g}")
    if row_level:
        note += ("。⚠ 沒有 cluster 欄，這次是列重抽 —— 若一列不是一位顧客，"
                 "量到的變異偏小（16 §5.2：cluster bootstrap 不是可選項）")
    note += ("。分群的 bootstrap ARI 不在本腳本，流程與門檻見 07 §7.2／§7.3，"
             "不重寫（16 §5.2 ⚠）")
    if n_fail:
        note += f"；另有 {n_fail} 次重抽估不出來已剔除"

    if verbose:
        detail(f"{unit}，B={B} → 95% 分位區間 [{lo:.4g}, {hi:.4g}]，"
               f"跨 0 比例 {cross:.2f}%｜{v}")

    rows = [{
        "variant": f"cluster bootstrap（{unit}，B={B}）",
        "coef": float(np.median(arr)), "se": boot_se, "p": None,
        "delta_pct": ((float(np.median(arr)) - b) / abs(b) * 100) if b != 0 else None,
        "verdict": v, "note": note, "結論有沒有變":
            (f"跨 0 比例 {cross:.2f}% > {CROSS_ZERO_MAX:.0f}%" if v == "unstable" else "沒變"),
        "方向": "正" if np.median(arr) > 0 else "負",
        "是否顯著": "區間不含 0" if lo * hi > 0 else "區間含 0",
        "scale_comparable": True,
    }]
    return {"summary": {"check_id": "R2", "動什麼": "抽到的是誰", "verdict": v,
                        "note": note, "跨0比例": cross, "分位區間": [lo, hi],
                        "bootstrap_se": boot_se, "B有效": len(coefs),
                        "重抽單位": unit},
            "rows": rows}


# ══════════════════════════════════════════════════════════════
#  五、R3 模型設定敏感度
# ══════════════════════════════════════════════════════════════
def r3_specification(d: Design, base: dict[str, Any], spec: Spec, *,
                     family_p: list[float] | None = None,
                     family_name: str | None = None,
                     boot: dict[str, Any] | None = None,
                     alpha: float = ALPHA,
                     verbose: bool = True) -> dict[str, Any]:
    """至少四組對照（16 §5.2 R3）：標準誤／共變量／轉換／檢定。

    每一組動的都是「你做的建模選擇」。判不穩健的兩條線照原文：
      · 係數方向在 < 80% 的設定下一致
      · 顯著性只在單一設定下成立   ← 這條就是「只報對自己有利的那一版」的定義
    """
    rows: list[dict[str, Any]] = []

    def add(variant: str, f: dict[str, Any] | None, *, scale_comparable: bool = True,
            note_extra: str = "", not_run: str = "") -> None:
        if not_run or f is None:
            rows.append({"variant": variant, "coef": None, "se": None, "p": None,
                         "delta_pct": None, "verdict": "not_run",
                         "note": not_run or "未執行", "結論有沒有變": "未執行",
                         "scale_comparable": scale_comparable})
            return
        c = classify(base, f, scale_comparable=scale_comparable, alpha=alpha)
        note = c["說明"]
        if not scale_comparable:
            note += "；係數尺度已變，delta_pct 留空（拿去比幅度是拿蘋果比橘子）"
        if note_extra:
            note += "；" + note_extra
        rows.append({"variant": variant, "coef": f["coef"], "se": f["se"],
                     "p": f["p"], "delta_pct": c["delta_pct"],
                     "verdict": c["verdict"], "note": note,
                     "結論有沒有變": c["結論有沒有變"], "方向": c["方向"],
                     "是否顯著": c["是否顯著"], "scale_comparable": scale_comparable})
        if verbose:
            dp = "—" if c["delta_pct"] is None else f"{c['delta_pct']:+.1f}%"
            detail(f"{variant} → 係數 {f['coef']:+.4g}（{dp}）、SE {f['se']:.4g}、"
                   f"p {f['p']:.4g}｜{c['verdict']}")

    # ① 換標準誤 —— 16 §七 P7，本腳本最重要的一組
    add("換標準誤：HC1 異質變異穩健",
        ols_fit(d.y, d.X, d.j, cov_type="hc1"),
        note_extra="係數不動，只有 SE 與 p 會動")
    if d.clusters is not None:
        try:
            fc = ols_fit(d.y, d.X, d.j, cov_type="cluster", clusters=d.clusters)
            add(f"換標準誤：cluster-robust（cluster={spec.cluster_col}）", fc,
                note_extra=(f"有效樣本數接近 {fc['n_clusters']} 個 cluster 而非 "
                            f"{fc['n']} 列，自由度 {fc['df']:.0f}（16 §七 P7）"))
        except ValueError as e:
            add(f"換標準誤：cluster-robust（cluster={spec.cluster_col}）", None,
                not_run=f"算不出來：{e}")
    else:
        add("換標準誤：cluster-robust", None,
            not_run=("沒有 cluster 欄。一列是一位顧客時本來就不需要；"
                     "一列不是一位顧客時這是硬規則（16 §七 P7），"
                     "用 --cluster-col 指定顧客欄後重跑"))

    if boot and boot.get("bootstrap_se"):
        # bootstrap SE 借用 R2 的複本，不重跑 —— 兩者用同一批複本才對得起來
        bse = boot["bootstrap_se"]
        tb = base["coef"] / bse if bse > 0 else float("nan")
        pb = float(2 * st.norm.sf(abs(tb))) if np.isfinite(tb) else float("nan")
        add("換標準誤：bootstrap（沿用 R2 的複本）",
            {"coef": base["coef"], "se": bse, "p": pb},
            note_extra=f"p 用常態近似（{boot.get('B有效')} 個有效複本）")
    else:
        add("換標準誤：bootstrap", None, not_run="R2 未產生有效複本，無 bootstrap SE")

    # ② 加減共變量（18-G3：tenure 進不進模型）
    if d.covariate_cols:
        keep = [c for c in range(d.X.shape[1]) if c not in d.covariate_cols]
        add("移除全部共變量（只留 treatment）",
            ols_fit(d.y, d.X[:, keep], keep.index(d.j), cov_type=base["cov_type"],
                    clusters=d.clusters),
            note_extra=f"原模型共變量：{'、'.join(spec.covariates)}")
    else:
        add("加減共變量", None,
            not_run=("沒有給共變量（--covariates）。18-G3：tenure_days 至少要試一次"
                     "進出模型 —— cohort 沒對齊時「新客不忠誠」是假結論"))

    # ③ 換轉換（原始 vs ln vs sqrt）—— 只比方向與顯著性，幅度不可比
    ymin = float(d.y.min())
    if ymin > 0:
        add("結果變數取 ln", ols_fit(np.log(d.y), d.X, d.j,
                                     cov_type=base["cov_type"], clusters=d.clusters),
            scale_comparable=False,
            note_extra="ln 後的係數是幾何平均的差，不是「平均差 X 元」（16 §4.2）")
    elif ymin >= 0:
        add("結果變數取 log1p", ols_fit(np.log1p(d.y), d.X, d.j,
                                        cov_type=base["cov_type"], clusters=d.clusters),
            scale_comparable=False,
            note_extra="含 0 所以用 log1p；要報「平均差 X 元」請改 Gamma GLM + log link")
    else:
        add("結果變數取 ln", None,
            not_run=(f"結果變數有負值（最小 {ymin:.4g}），ln 無定義。"
                     f"右偏含 0／負值走 Yeo-Johnson（06 §1.2 順位表）"))
    if ymin >= 0:
        add("結果變數取 sqrt", ols_fit(np.sqrt(d.y), d.X, d.j,
                                       cov_type=base["cov_type"], clusters=d.clusters),
            scale_comparable=False)
    else:
        add("結果變數取 sqrt", None, not_run=f"結果變數有負值（最小 {ymin:.4g}）")

    # ④ 換檢定：參數 vs 無母數。只有二元 treatment 且無共變量時可比
    if d.binary_treat and not d.covariate_cols:
        a = d.y[d.X[:, d.j] == 1]
        b = d.y[d.X[:, d.j] == 0]
        if len(a) >= 2 and len(b) >= 2:
            tw, pw = st.ttest_ind(a, b, equal_var=False)
            add("換檢定：Welch's t（不假設等變異）",
                {"coef": float(a.mean() - b.mean()),
                 "se": float(math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))),
                 "p": float(pw)},
                note_extra="16 §4.3：兩組比較預設 Welch，不先跑 Levene（那是資料窺探）")
            u, pu = st.mannwhitneyu(a, b, alternative="two-sided")
            add("換檢定：Mann-Whitney U（無母數）",
                {"coef": float(np.median(a) - np.median(b)), "se": float("nan"),
                 "p": float(pu)},
                scale_comparable=False,
                note_extra=(f"係數欄是中位數差（n1={len(a)}、n2={len(b)}）；"
                            f"右偏資料的 t 與 U 結論不同是常態假設出問題的訊號"))
        else:
            add("換檢定：無母數", None, not_run=f"某一組只有 {min(len(a), len(b))} 列")
    else:
        add("換檢定：無母數", None,
            not_run=("treatment 非二元或模型含共變量 —— 秩檢定沒有對應的「控制共變量後」"
                     "版本。要比就先把共變量殘差化，或改用 16 §4.2 的 Gamma GLM"))

    # ⑤ 多重比較校正前後（16 §三）
    if family_p:
        try:
            from stats_utils import bh_correct  # 只有真的要校正時才載入
            allp = [base["p"], *family_p]
            tbl = bh_correct(allp, alpha=alpha,
                             family=family_name or "（未命名 —— 16 §3.4 要求寫出族的名字）",
                             labels=["主結論", *[f"同族{i + 1}" for i in range(len(family_p))]])
            p_bh = float(tbl.loc[tbl["label"] == "主結論", "p_bh"].iloc[0])
            add(f"多重比較校正後（BH，m={len(allp)}）",
                {"coef": base["coef"], "se": base["se"], "p": p_bh},
                note_extra=(f"族＝{family_name or '未命名'}；原始 p 與校正後 p 並報是"
                            f"硬規則（16 §3.4）。族的邊界跟著**行動**走，不跟著章節走"))
        except (ImportError, ValueError) as e:
            add("多重比較校正後（BH）", None, not_run=f"校正失敗：{e}")
    else:
        add("多重比較校正後（BH）", None,
            not_run=("沒給同族的其他 p 值（--family-p）。分群後的標準套組是 43 個檢定，"
                     "不校正時 89% 機率至少一個假顯著（16 §3.1）。"
                     "已用 Tukey／Games-Howell／Dunnett 的成對比較則**不可再套 BH**"))

    ran = [r for r in rows if r["verdict"] != "not_run"]
    n_ran = len(ran)
    signs = [1 if r["coef"] > 0 else (-1 if r["coef"] < 0 else 0)
             for r in ran if r["coef"] is not None and np.isfinite(r["coef"])]
    base_sign = 1 if base["coef"] > 0 else (-1 if base["coef"] < 0 else 0)
    agree = (sum(1 for s in signs if s == base_sign) / len(signs) * 100) if signs else float("nan")
    sig_flags = [r["是否顯著"] == "顯著" for r in ran if "是否顯著" in r]
    n_sig = sum(sig_flags)
    base_sig = base["p"] < alpha

    reasons: list[str] = []
    if np.isfinite(agree) and agree < DIRECTION_CONSISTENT_MIN:
        reasons.append(f"方向一致率 {agree:.0f}% < {DIRECTION_CONSISTENT_MIN:.0f}%")
    # 「顯著性只在單一設定下成立」：基準顯著、但所有替代設定都不顯著
    if base_sig and len(sig_flags) >= 2 and n_sig == 0:
        reasons.append("顯著性只在基準設定下成立，換任何一組設定都掉了")
    if any(r["verdict"] == "unstable" for r in ran):
        flipped = [r["variant"] for r in ran if r["verdict"] == "unstable"]
        reasons.append("有設定翻轉：" + "、".join(flipped))

    if n_ran < R3_MIN_VARIANTS:
        v = "not_run" if n_ran == 0 else worst_verdict([r["verdict"] for r in ran])
        note = (f"只跑得出 {n_ran} 組對照，未達 16 §5.2 R3 要求的 {R3_MIN_VARIANTS} 組 —— "
                f"報告不可寫「已做模型設定敏感度分析」。缺的組別見各列 note")
    elif reasons:
        v = "unstable"
        note = "；".join(reasons)
    else:
        v = worst_verdict([r["verdict"] for r in ran])
        note = (f"{n_ran} 組對照，方向一致率 {agree:.0f}%，"
                f"顯著的有 {n_sig}／{len(sig_flags)} 組")

    coefs_cmp = [r["coef"] for r in ran
                 if r["scale_comparable"] and r["coef"] is not None
                 and np.isfinite(r["coef"])]
    rng_txt = (f"[{min(coefs_cmp):.4g}, {max(coefs_cmp):.4g}]" if coefs_cmp else "—")
    return {"summary": {"check_id": "R3", "動什麼": "你做的建模選擇", "verdict": v,
                        "note": note, "對照組數": n_ran, "方向一致率": _py(agree),
                        "可比係數範圍": rng_txt},
            "rows": rows}


# ══════════════════════════════════════════════════════════════
#  六、R4 時間切點敏感度
# ══════════════════════════════════════════════════════════════
def _name_list(ids: np.ndarray, y: np.ndarray, mask: np.ndarray,
               pct: float) -> set[Any]:
    """名單定義：窗內把 outcome 加總到 id，取前 pct% 的人。

    【補訂】16 §5.2 R4 的判準是「名單的 Jaccard 重疊率 < 0.6」，但沒有定義名單
    怎麼產。本腳本用最常見的那一種（依結果變數排序取前 X%），並把 pct 寫進輸出，
    讓讀者知道 Jaccard 是對哪一份名單算的。有自己的名單規則就用那個，
    不要沿用這裡的預設值當結論。
    """
    if ids is None or not mask.any():
        return set()
    s = pd.Series(y[mask]).groupby(pd.Series(ids[mask])).sum().sort_values(ascending=False)
    m = max(1, int(round(len(s) * pct / 100.0)))
    return set(s.index[:m].tolist())


def r4_time(d: Design, base: dict[str, Any], spec: Spec, *,
            as_of: pd.Timestamp | None = None, window_months: int = 12,
            list_pct: float = LIST_PCT, alpha: float = ALPHA,
            verbose: bool = True) -> dict[str, Any]:
    """換 as_of（±1、±3 個月）與觀察窗長度（6／12／24 個月）（16 §5.2 R4）。

    16 §5.2 的降級順序寫得很清楚：**時間不夠時先跑 R1 與 R4** —— R1 最便宜，
    R4 最常翻盤（行銷資料的季節結構強）。

    標籤 horizon（3／6 個月）那一支本腳本沒做：horizon 要有「標籤怎麼定義」
    才算得出來，而那是 M9 的事（12）。這一項在輸出裡是 not_run 並附原因，
    不會靜默消失（00 §1.6 降級不留空）。
    """
    if d.dates is None:
        return {"summary": {"check_id": "R4", "動什麼": "你選的那個日期",
                            "verdict": "not_run",
                            "note": ("沒有給時間欄（--date-col）。16 §5.2：R4 最常翻盤，"
                                     "時間不夠時也要跑 R1 與 R4 兩項。"
                                     "報告不准把「沒跑」默寫成「已做穩健性檢定」")},
                "rows": [{"variant": "as_of／觀察窗", "coef": None, "se": None,
                          "p": None, "delta_pct": None, "verdict": "not_run",
                          "note": "無時間欄", "結論有沒有變": "未執行",
                          "scale_comparable": True}]}

    dates = pd.to_datetime(pd.Series(d.dates))
    base_as_of = pd.Timestamp(as_of) if as_of is not None else dates.max()
    rows: list[dict[str, Any]] = []

    def window_mask(end: pd.Timestamp, months: int) -> np.ndarray:
        start = end - pd.DateOffset(months=months)
        return ((dates > start) & (dates <= end)).to_numpy()

    base_mask = window_mask(base_as_of, window_months)
    base_list = _name_list(d.ids, d.y, base_mask, list_pct)

    variants: list[tuple[str, pd.Timestamp, int]] = []
    for shift in (-3, -1, 1, 3):
        end = base_as_of + pd.DateOffset(months=shift)
        if end > dates.max() + pd.Timedelta(days=1) or end <= dates.min():
            continue          # 超出資料涵蓋範圍的切點不是「敏感度」，是「沒有資料」
        variants.append((f"as_of {shift:+d} 個月（{end.date()}）", end, window_months))
    for w in (6, 12, 24):
        if w == window_months:
            continue
        variants.append((f"觀察窗改 {w} 個月", base_as_of, w))

    for label, end, w in variants:
        mask = window_mask(end, w)
        n_in = int(mask.sum())
        if n_in < max(SMALL_N, d.X.shape[1] * 3):
            rows.append({"variant": label, "coef": None, "se": None, "p": None,
                         "delta_pct": None, "verdict": "not_run",
                         "note": f"窗內只有 {n_in} 列，不足以估計（16 §4.1）",
                         "結論有沒有變": "未執行", "scale_comparable": True})
            continue
        try:
            f = ols_fit(d.y[mask], d.X[mask], d.j, cov_type=base["cov_type"],
                        clusters=d.clusters[mask] if d.clusters is not None else None)
        except (ValueError, np.linalg.LinAlgError) as e:
            rows.append({"variant": label, "coef": None, "se": None, "p": None,
                         "delta_pct": None, "verdict": "not_run",
                         "note": f"重估失敗：{e}", "結論有沒有變": "未執行",
                         "scale_comparable": True})
            continue
        c = classify(base, f, alpha=alpha)
        lst = _name_list(d.ids, d.y, mask, list_pct)
        jac = (len(base_list & lst) / len(base_list | lst)) if (base_list | lst) else float("nan")
        v = c["verdict"]
        extra = ""
        if np.isfinite(jac):
            extra = f"；名單 Jaccard {jac:.3f}（前 {list_pct:.0f}%，門檻 {JACCARD_MIN}）"
            if jac < JACCARD_MIN:
                v = "unstable"
                extra += " ← 低於門檻，名單換掉一大半"
        rows.append({"variant": label, "coef": f["coef"], "se": f["se"], "p": f["p"],
                     "delta_pct": c["delta_pct"], "verdict": v,
                     "note": f"窗內 {n_in} 列；{c['說明']}{extra}",
                     "結論有沒有變": c["結論有沒有變"], "方向": c["方向"],
                     "是否顯著": c["是否顯著"], "Jaccard": _py(jac),
                     "scale_comparable": True})
        if verbose:
            jt = "—" if not np.isfinite(jac) else f"{jac:.3f}"
            detail(f"{label} → 係數 {f['coef']:+.4g}、p {f['p']:.4g}、"
                   f"Jaccard {jt}｜{v}")

    rows.append({"variant": "換標籤 horizon（3／6 個月）", "coef": None, "se": None,
                 "p": None, "delta_pct": None, "verdict": "not_run",
                 "note": ("需要「標籤怎麼定義」才算得出來，那是 M9 的事（12）。"
                          "本腳本不猜標籤定義 —— 猜錯會產生一個看起來做過的空檢定"),
                 "結論有沒有變": "未執行", "scale_comparable": True})

    ran = [r for r in rows if r["verdict"] != "not_run"]
    v = worst_verdict([r["verdict"] for r in ran]) if ran else "not_run"
    jacs = [r["Jaccard"] for r in ran if r.get("Jaccard") is not None]
    note = (f"{len(ran)} 組時間切點；"
            + (f"名單 Jaccard 最低 {min(jacs):.3f}（門檻 {JACCARD_MIN}）"
               if jacs else "無 id 欄，未算名單 Jaccard")
            + f"；基準 as_of={base_as_of.date()}、觀察窗 {window_months} 個月")
    if not ran:
        note = "所有時間切點都估不出來（窗內樣本不足），R4 這次沒有驗到"
    return {"summary": {"check_id": "R4", "動什麼": "你選的那個日期", "verdict": v,
                        "note": note, "as_of": str(base_as_of.date()),
                        "觀察窗月數": window_months,
                        "名單前百分比": list_pct,
                        "Jaccard最低": _py(min(jacs)) if jacs else None},
            "rows": rows}


# ══════════════════════════════════════════════════════════════
#  七、彙總、對照表、16 §5.3 的報告句型
# ══════════════════════════════════════════════════════════════
def schema_rows(checks: list[dict[str, Any]]) -> pd.DataFrame:
    """16 §5.3 的固定 schema。

    每一項先出一列「（本項判定）」再出各變體 —— verify_outputs 的
    「R1..R4 四列齊全；未執行者 verdict 填 not_run 且 note 非空」靠這一列成立，
    未執行的檢定也一定有一列，不會整項消失。
    """
    out: list[dict[str, Any]] = []
    for ck in checks:
        s = ck["summary"]
        out.append({"check_id": s["check_id"], "variant": "（本項判定）",
                    "coef": None, "se": None, "p": None, "delta_pct": None,
                    "verdict": s["verdict"], "note": s["note"]})
        for r in ck["rows"]:
            out.append({"check_id": s["check_id"], "variant": r["variant"],
                        "coef": _py(r["coef"]), "se": _py(r["se"]),
                        "p": _py(r["p"]),
                        "delta_pct": (None if r["delta_pct"] is None
                                      else round(float(r["delta_pct"]), 3)),
                        "verdict": r["verdict"], "note": r["note"]})
    return pd.DataFrame(out, columns=["check_id", "variant", "coef", "se", "p",
                                      "delta_pct", "verdict", "note"])


def comparison_table(base: dict[str, Any], d: Design, spec: Spec,
                     checks: list[dict[str, Any]], alpha: float = ALPHA) -> pd.DataFrame:
    """人看的「換了什麼 → 結論有沒有變」對照表。第一列是基準設定。"""
    rows = [{
        "檢定": "基準", "換了什麼": f"（原始設定：{d.treat_desc}）",
        "係數": round(base["coef"], 6), "標準誤": round(base["se"], 6),
        "p": base["p"], "相對基準變動%": 0.0,
        "方向": "正" if base["coef"] > 0 else "負",
        "是否顯著": "顯著" if base["p"] < alpha else "n.s.",
        "結論有沒有變": "—", "判定": "—",
        "說明": (f"n={base['n']}、參數 {base['k']} 個、"
                 f"標準誤 {base['cov_type']}、自由度 {base['df']:.0f}"),
    }]
    for ck in checks:
        cid = ck["summary"]["check_id"]
        for r in ck["rows"]:
            rows.append({
                "檢定": cid, "換了什麼": r["variant"],
                "係數": None if r["coef"] is None else round(float(r["coef"]), 6),
                "標準誤": None if r["se"] is None or not np.isfinite(r["se"])
                          else round(float(r["se"]), 6),
                "p": _py(r["p"]),
                "相對基準變動%": (None if r["delta_pct"] is None
                                  else round(float(r["delta_pct"]), 2)),
                "方向": r.get("方向", "—"), "是否顯著": r.get("是否顯著", "—"),
                "結論有沒有變": r["結論有沒有變"], "判定": r["verdict"],
                "說明": r["note"],
            })
    return pd.DataFrame(rows)


def collect_flips(checks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """所有「結論變了」的變體。這份清單就是「必須寫進報告」的東西。"""
    out = []
    for ck in checks:
        cid = ck["summary"]["check_id"]
        for r in ck["rows"]:
            if r["verdict"] in ("unstable", "stable_with_caveat"):
                out.append({"check_id": cid, "variant": r["variant"],
                            "verdict": r["verdict"],
                            "結論有沒有變": r["結論有沒有變"], "note": r["note"]})
    return out


def report_block(base: dict[str, Any], d: Design, spec: Spec,
                 checks: list[dict[str, Any]], conclusion: str,
                 alpha: float = ALPHA) -> str:
    """16 §5.3 包子指定的固定四段句型 —— 每一項都要給幅度，不只給「維持不變」。"""
    by = {ck["summary"]["check_id"]: ck for ck in checks}
    L = ["【穩健性檢定】"]
    titles = {"R1": "離群敏感度", "R2": "子樣本穩定度",
              "R3": "模型設定", "R4": "時間切點"}
    for cid in ("R1", "R2", "R3", "R4"):
        ck = by.get(cid)
        head = f"  {cid} {titles[cid]}："
        if ck is None:
            L.append(head + "未執行。")
            continue
        s = ck["summary"]
        if s["verdict"] == "not_run":
            L.append(head + f"**未執行** —— {s['note']}")
            continue
        pieces = []
        for r in ck["rows"]:
            if r["verdict"] == "not_run" or r["coef"] is None:
                continue
            dp = "" if r["delta_pct"] is None else f"（{r['delta_pct']:+.1f}%）"
            pv = "" if r["p"] is None or not np.isfinite(r["p"]) else f"、p {r['p']:.4g}"
            pieces.append(f"{r['variant']} 係數 {base['coef']:.4g} → "
                          f"{r['coef']:.4g}{dp}{pv}")
        L.append(head + "；".join(pieces) if pieces else head + s["note"])
        L.append(f"      → {s['verdict']}：{s['note']}")

    stable = [c for c in ("R1", "R2", "R3", "R4")
              if by.get(c) and by[c]["summary"]["verdict"] == "stable"]
    shaky = [c for c in ("R1", "R2", "R3", "R4")
             if by.get(c) and by[c]["summary"]["verdict"] in
             ("unstable", "stable_with_caveat")]
    notrun = [c for c in ("R1", "R2", "R3", "R4")
              if not by.get(c) or by[c]["summary"]["verdict"] == "not_run"]

    tail = [f"  結論句：以上{len([c for c in ('R1', 'R2', 'R3', 'R4') if by.get(c)])}"
            f"項穩健性檢定，主結論（{conclusion}）"]
    if stable:
        tail[-1] += f"在 {'／'.join(stable)} 下維持不變"
    if shaky:
        detail_txt = "；".join(f"{c} {by[c]['summary']['note']}" for c in shaky)
        tail[-1] += ("，" if stable else "") + f"在 {'／'.join(shaky)} 下改變：{detail_txt}"
    tail[-1] += "。"
    if notrun:
        tail.append(f"         {'／'.join(notrun)} 未執行，"
                    f"報告不准默寫成「已做穩健性檢定」（16 §5.2）。")
    if shaky:
        tail.append("         因此本節的證據等級**不升級**，正文必須逐條寫出上述幅度"
                    "變化；建議走 M12 取得增量估計（15）。")
    else:
        tail.append("         穩健性檢定通過不等於因果 —— 證據等級仍由 00 §1.5 的"
                    "識別條件決定，穩健性**永遠不會升級證據等級**。")
    return "\n".join(L + tail)


# ══════════════════════════════════════════════════════════════
#  八、主流程（純函式，可直接被自我測試呼叫，不碰檔案系統）
# ══════════════════════════════════════════════════════════════
def analyze(df: pd.DataFrame, spec: Spec, *, B: int = BOOT_B, seed: int = 42,
            alpha: float = ALPHA, as_of: str | None = None,
            window_months: int = 12, list_pct: float = LIST_PCT,
            family_p: list[float] | None = None, family_name: str | None = None,
            conclusion: str | None = None,
            verbose: bool = True) -> dict[str, Any]:
    """跑完 R1–R4，回傳結構化結果。不寫檔、不呼叫 warn/err（那是 run() 的事）。"""
    d = build_design(df, spec)

    # 基準設定的標準誤：有 cluster 欄且「一列不是一個 cluster」時，預設就走
    # cluster-robust —— 16 §七 P7 是硬規則，不是可選項
    panel = False
    if d.clusters is not None:
        G = len(np.unique(d.clusters))
        panel = G < len(d.y)
    base_cov = "cluster" if (panel and d.clusters is not None) else "naive"
    base = ols_fit(d.y, d.X, d.j, cov_type=base_cov, clusters=d.clusters)

    if verbose:
        print(f"\n基準設定：{d.treat_desc}｜n={base['n']}、參數 {base['k']} 個"
              f"｜標準誤 {base['cov_type']}"
              + (f"（{base['n_clusters']} 個 cluster、df={base['df']:.0f}）"
                 if base["n_clusters"] else f"（df={base['df']:.0f}）"))
        print(f"          係數 {base['coef']:+.6g}、SE {base['se']:.6g}、"
              f"p {base['p']:.6g}")

    if verbose:
        print("\nR1 離群敏感度（16 §5.2；動樣本中的少數個體）")
    r1 = r1_influence(d, base, alpha=alpha, verbose=verbose)
    if verbose:
        print("\nR2 子樣本穩定度（16 §5.2；動抽到的是誰）")
    r2 = r2_bootstrap(d, base, B=B, seed=seed, alpha=alpha, verbose=verbose)
    if verbose:
        print("\nR3 模型設定敏感度（16 §5.2；動你做的建模選擇）")
    r3 = r3_specification(d, base, spec, family_p=family_p, family_name=family_name,
                          boot=r2["summary"], alpha=alpha, verbose=verbose)
    if verbose:
        print("\nR4 時間切點敏感度（16 §5.2；動你選的那個日期）")
    r4 = r4_time(d, base, spec, as_of=pd.Timestamp(as_of) if as_of else None,
                 window_months=window_months, list_pct=list_pct, alpha=alpha,
                 verbose=verbose)

    checks = [r1, r2, r3, r4]
    conc = conclusion or (
        f"{spec.outcome} 隨 {d.treat_desc} "
        f"{'較高' if base['coef'] > 0 else '較低'}"
        f"（{base['coef']:+.4g}）")
    return {
        "design": d, "base": base, "checks": checks, "panel": panel,
        "schema": schema_rows(checks),
        "對照表": comparison_table(base, d, spec, checks, alpha=alpha),
        "flips": collect_flips(checks),
        "report": report_block(base, d, spec, checks, conc, alpha=alpha),
        "conclusion": conc,
    }


def load_data(p: Any, explicit: Path | None) -> tuple[pd.DataFrame, Path]:
    """吃 --data。相對路徑相對於專案根目錄解讀（03 的目錄命名是中文的）。"""
    if explicit is None:
        raise FileNotFoundError(
            "要用 --data 指定分析資料表（.parquet／.csv）。\n"
            "  慣例落點是 分析資料表/ 或 顧客特徵表/（03 §倉儲與檔案結構）。")
    path = explicit if explicit.is_absolute() else (p.root / explicit)
    if not path.exists():
        raise FileNotFoundError(
            f"找不到資料檔：{path}\n"
            f"  相對路徑是相對專案根目錄（{p.root}）解讀的，"
            f"要用絕對路徑也可以。")
    df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
          else pd.read_csv(path, encoding="utf-8-sig"))
    return df, path


def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    df, dpath = load_data(p, args.data)
    covs = tuple(c.strip() for c in (args.covariates or "").split(",") if c.strip())
    spec = Spec(outcome=args.outcome, treatment=args.treatment, covariates=covs,
                cluster_col=args.cluster_col, date_col=args.date_col,
                id_col=args.id_col)

    print("=" * 72)
    print("行銷數據分析 Skill — 穩健性檢定 R1–R4（16 §五）")
    print(f"專案：{args.project}｜資料：{dpath.name}（{len(df):,} 列）")
    print(f"主結論：{spec.outcome} ~ {spec.treatment}"
          + (f" + {' + '.join(covs)}" if covs else ""))
    print("核心規則：結論翻轉就必須寫進報告，不准只報對自己有利的那一版。")
    print("=" * 72)

    fam_p = None
    if args.family_p:
        fam_p = [float(x) for x in args.family_p.split(",") if x.strip()]

    res = analyze(df, spec, B=args.B, seed=args.seed, alpha=args.alpha,
                  as_of=args.as_of, window_months=args.window_months,
                  list_pct=args.list_pct, family_p=fam_p,
                  family_name=args.family_name, conclusion=args.conclusion,
                  verbose=True)
    d: Design = res["design"]
    base = res["base"]

    if d.n_dropped:
        info(f"剔除 {d.n_dropped} 列缺值（原 {len(df):,} 列）—— "
             f"缺值列的處置見 18-E22，本腳本不補值")

    # ── P7 硬規則 ──────────────────────────────────────────────
    if res["panel"] is False and spec.cluster_col is None:
        dup = None
        for cand in ("客戶編號", "customer_id", "cust_id", "客戶ID"):
            if cand in df.columns and df[cand].duplicated().any():
                dup = cand
                break
        if dup:
            err(f"資料裡的「{dup}」有重複值（一列不是一位顧客），但沒有指定 --cluster-col",
                "16 §七 P7 硬規則：任何「一列不是一位顧客」的迴歸禁用預設標準誤。"
                "有效樣本數接近顧客數而非列數，預設 SE 會低估變異、p 值太樂觀"
                f"（與 18-T3 同級：不報錯只給錯數字）。加 --cluster-col {dup} 重跑")

    print("\n" + "=" * 72)
    print("對照表：換了什麼 → 結論有沒有變")
    print("=" * 72)
    tbl = res["對照表"]
    for _, r in tbl.iterrows():          # 用欄名取值，不用 itertuples（含 % 的欄名會被改名）
        c = "—" if pd.isna(r["係數"]) else f"{r['係數']:+.4g}"
        pv = "—" if r["p"] is None or pd.isna(r["p"]) else f"{r['p']:.4g}"
        dp = "—" if r["相對基準變動%"] is None or pd.isna(r["相對基準變動%"]) \
            else f"{r['相對基準變動%']:+.1f}%"
        print(f"  {r['檢定']:<4}{r['換了什麼'][:34]:<36}係數 {c:>12}｜"
              f"p {pv:>10}｜Δ {dp:>8}｜{r['判定']:<18}{r['結論有沒有變']}")

    flips = res["flips"]
    print("\n" + "-" * 72)
    if flips:
        print("必須寫進報告的翻轉（核心規則：不准只報對自己有利的那一版）")
        print("-" * 72)
        for f in flips:
            warn(f"{f['check_id']}｜{f['variant']}：{f['結論有沒有變']}",
                 "把這一列寫進報告正文，連同幅度一起 —— 16 §5.3 的四段句型要求"
                 "「每一項都要給幅度，不只給『維持不變』」。"
                 "刪掉這一列而只報基準版，就是本腳本要防的那件事")
    else:
        print("四項檢定沒有出現結論翻轉。")
        print("-" * 72)

    for ck in res["checks"]:
        s = ck["summary"]
        if s["verdict"] == "not_run":
            warn(f"{s['check_id']} 未執行：{s['note'][:60]}",
                 "16 §5.2：只跑兩項要在報告寫明哪兩項未執行，"
                 "不准默寫成「已做穩健性檢定」。降級順序是先 R1 再 R4")

    print("\n" + "-" * 72)
    print("可直接貼進報告（16 §5.3 的固定四段句型）：")
    print("-" * 72)
    print(res["report"])

    model = args.model_name or f"{spec.outcome}_{spec.treatment}"
    if not args.no_write:
        p.models.mkdir(parents=True, exist_ok=True)
        csv_path = p.models / f"robustness_{model}.csv"
        res["schema"].to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n✓ 固定 schema（16 §5.3）：{csv_path}")

        out_dir = p.tables / "迴歸與診斷"
        out_dir.mkdir(parents=True, exist_ok=True)
        cmp_path = out_dir / f"穩健性對照表_{model}.csv"
        tbl.to_csv(cmp_path, index=False, encoding="utf-8-sig")
        print(f"✓ 對照表：{cmp_path}")

        jp = p.models / f"robustness_{model}.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project, "data": str(dpath), "model": model,
            "spec": {"outcome": spec.outcome, "treatment": spec.treatment,
                     "covariates": list(spec.covariates),
                     "cluster_col": spec.cluster_col, "date_col": spec.date_col,
                     "id_col": spec.id_col, "treat_desc": d.treat_desc},
            "alpha": args.alpha, "B": args.B, "seed": args.seed,
            "baseline": {k: _py(v) for k, v in base.items()
                         if k not in ("beta", "resid")},
            "checks": [{**{k: _py(v) for k, v in ck["summary"].items()},
                        "rows": [{k: _py(v) for k, v in r.items()} for r in ck["rows"]]}
                       for ck in res["checks"]],
            "必須寫進報告": flips,
            "報告段落": res["report"],
            "errors": _errors, "warnings": _warnings, "infos": _infos,
        }, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        print(f"✓ 機器可讀結果：{jp}")

    n_err, n_warn = len(_errors), len(_warnings)
    verdicts = [ck["summary"]["verdict"] for ck in res["checks"]]
    print("\n" + "=" * 72)
    print("四項判定："
          + "、".join(f"{ck['summary']['check_id']}={ck['summary']['verdict']}"
                      for ck in res["checks"]))
    if n_err:
        print(f"結果：⛔ 有 {n_err} 條 error → 穩健性檢定的數字本身不可信，先修上游。")
        return EX_ERROR
    if all(v == "not_run" for v in verdicts):
        err("R1–R4 四項全部未執行",
            "等於沒做穩健性檢定。至少要跑 R1（最便宜）與 R4（最常翻盤），"
            "見 16 §5.2 的降級順序")
        return EX_ERROR
    if n_warn or any(v != "stable" for v in verdicts):
        print(f"結果：⚠ 有 {n_warn} 條 warning → 可往下，但報告要逐條寫明翻轉與幅度。")
        return EX_WARN
    print("結果：✅ 四項穩健性檢定全部 stable。")
    print("      提醒：穩健 ≠ 因果。證據等級仍由 00 §1.5 的識別條件決定。")
    return EX_OK


# ══════════════════════════════════════════════════════════════
#  九、自我測試
# ══════════════════════════════════════════════════════════════
def _selftest() -> int:  # noqa: C901 - 測試項目多，拆開反而看不出對照關係
    print("=" * 72)
    print("robustness.py 自我測試")
    print("=" * 72)
    rng = np.random.default_rng(20260728)
    failed: list[str] = []

    def check(name: str, cond: bool, got: str = "") -> None:
        print(("  ✓ " if cond else "  ✗ ") + name + (f"（{got}）" if got else ""))
        if not cond:
            failed.append(name)

    # ── ① 估計核心對得上 statsmodels（三種標準誤逐一比）──────────
    n = 300
    g = np.repeat(np.arange(30), 10)             # 30 個 cluster × 10 列
    x = rng.normal(0, 1, n)
    z = rng.normal(0, 1, n)
    u = np.repeat(rng.normal(0, 2, 30), 10)      # 群層隨機效果 → 群內相關
    y = 1.0 + 0.5 * x + 0.3 * z + u + rng.normal(0, 1, n)
    X = np.column_stack([np.ones(n), x, z])
    try:
        import statsmodels.api as sm
        m = sm.OLS(y, X).fit()
        f_naive = ols_fit(y, X, 1, cov_type="naive")
        check("naive OLS 的係數對得上 statsmodels",
              abs(f_naive["coef"] - m.params[1]) < 1e-10,
              f"差 {abs(f_naive['coef'] - m.params[1]):.2e}")
        check("naive 標準誤對得上 statsmodels",
              abs(f_naive["se"] - m.bse[1]) < 1e-10,
              f"{f_naive['se']:.8f} vs {m.bse[1]:.8f}")
        mh = sm.OLS(y, X).fit(cov_type="HC1")
        f_hc = ols_fit(y, X, 1, cov_type="hc1")
        check("HC1 標準誤對得上 statsmodels",
              abs(f_hc["se"] - mh.bse[1]) < 1e-10,
              f"{f_hc['se']:.8f} vs {mh.bse[1]:.8f}")
        mc = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g})
        f_cl = ols_fit(y, X, 1, cov_type="cluster", clusters=g)
        check("cluster-robust 標準誤對得上 statsmodels",
              abs(f_cl["se"] - mc.bse[1]) < 1e-9,
              f"{f_cl['se']:.8f} vs {mc.bse[1]:.8f}")
        check("cluster-robust 的自由度是 G−1 不是 n−k",
              abs(f_cl["df"] - 29) < 1e-9, f"df={f_cl['df']:.0f}（G=30）")
        from statsmodels.stats.outliers_influence import OLSInfluence
        D_sm = OLSInfluence(m).cooks_distance[0]
        D, dfb, h = cooks_distance(y, X, 1)
        check("Cook's D 對得上 statsmodels 的 OLSInfluence",
              float(np.max(np.abs(D - D_sm))) < 1e-9,
              f"最大差 {float(np.max(np.abs(D - D_sm))):.2e}")
        # DFBETA 是精確 LOO 差值 —— 拿真的刪一列重估來驗
        i = int(np.argmax(np.abs(dfb)))
        keep = np.delete(np.arange(n), i)
        real = f_naive["coef"] - ols_fit(y[keep], X[keep], 1)["coef"]
        check("DFBETA 等於真的刪一列重估的差值",
              abs(real - dfb[i]) < 1e-9, f"{real:.10f} vs {dfb[i]:.10f}")
    except ImportError:
        check("statsmodels 可用（用來交叉驗算估計核心）", False, "未安裝")

    # ── ② R1：造一份「拿掉一個點結論就翻轉」的資料 ────────────────
    #    30 個點沒有關聯（真斜率 0），再加一個高槓桿點把斜率整個拉起來。
    #    這是 R1 存在的唯一理由：那一個點撐著整條結論。
    nb = 30
    xb = rng.normal(0, 1, nb)
    yb = rng.normal(0, 1, nb)
    df_flip = pd.DataFrame({"x": np.append(xb, 12.0), "y": np.append(yb, 40.0),
                            "id": np.arange(nb + 1)})
    d_flip = build_design(df_flip, Spec(outcome="y", treatment="x", id_col="id"))
    base_flip = ols_fit(d_flip.y, d_flip.X, d_flip.j)
    check("造出來的資料在含高影響點時顯著", base_flip["p"] < ALPHA,
          f"係數 {base_flip['coef']:+.4g}、p={base_flip['p']:.3g}")
    r1f = r1_influence(d_flip, base_flip, verbose=False)
    check("R1 抓到「拿掉一個點結論就翻轉」", r1f["summary"]["verdict"] == "unstable",
          f"判定={r1f['summary']['verdict']}")
    single = [r for r in r1f["rows"] if "單一列" in r["variant"]]
    check("R1 點名的是最後那一列（人造的高影響點）",
          bool(single) and str(nb) in single[0]["variant"],
          single[0]["variant"] if single else "沒有這一列")
    check("R1 的翻轉理由講的是顯著性或方向",
          bool(single) and ("翻轉" in single[0]["結論有沒有變"]
                            or "幅度" in single[0]["note"]),
          single[0]["結論有沒有變"] if single else "—")
    check("R1 的 note 講了該怎麼辦（不是只講哪裡錯）",
          "怎麼辦" in r1f["summary"]["note"] or "查輸入錯誤" in r1f["summary"]["note"],
          r1f["summary"]["note"][:40])

    # ── ③ R1 反例：乾淨資料不可以亂叫 ────────────────────────────
    nc = 400
    xc = rng.normal(0, 1, nc)
    yc = 2.0 * xc + rng.normal(0, 1, nc)
    d_ok = build_design(pd.DataFrame({"x": xc, "y": yc}),
                        Spec(outcome="y", treatment="x"))
    base_ok = ols_fit(d_ok.y, d_ok.X, d_ok.j)
    r1o = r1_influence(d_ok, base_ok, verbose=False)
    check("R1 對乾淨資料不亂叫", r1o["summary"]["verdict"] == "stable",
          f"判定={r1o['summary']['verdict']}")

    # ── ④ R2：真效果為 0 → 跨 0 比例應該遠大於 5% ────────────────
    d_null = build_design(pd.DataFrame({"x": rng.normal(0, 1, 200),
                                        "y": rng.normal(0, 1, 200)}),
                          Spec(outcome="y", treatment="x"))
    base_null = ols_fit(d_null.y, d_null.X, d_null.j)
    r2n = r2_bootstrap(d_null, base_null, B=300, seed=7, verbose=False)
    check("R2 對「真效果為 0」判 unstable",
          r2n["summary"]["verdict"] == "unstable",
          f"跨 0 比例 {r2n['summary']['跨0比例']:.1f}%")
    r2o = r2_bootstrap(d_ok, base_ok, B=300, seed=7, verbose=False)
    check("R2 對「效果很強」不亂叫", r2o["summary"]["verdict"] == "stable",
          f"跨 0 比例 {r2o['summary']['跨0比例']:.1f}%")
    check("R2 的 note 有交叉引用 07 §7.2（分群 ARI 不在這裡重寫）",
          "07 §7.2" in r2o["summary"]["note"])

    # ── ⑤ R3：panel 結構下 naive 顯著、cluster-robust 不顯著 ─────
    #    這是 16 §七 P7 的情境，全 skill 最貴的一條
    ng, per = 40, 25
    gid = np.repeat(np.arange(ng), per)
    treat = np.repeat(rng.integers(0, 2, ng), per).astype(float)   # 處理在群層指派
    ue = np.repeat(rng.normal(0, 3, ng), per)
    yp = 0.6 * treat + ue + rng.normal(0, 1, ng * per)
    Xp = np.column_stack([np.ones(ng * per), treat])
    fn = ols_fit(yp, Xp, 1, cov_type="naive")
    fc = ols_fit(yp, Xp, 1, cov_type="cluster", clusters=gid)
    check("panel 資料的 cluster-robust SE 明顯大於 naive SE",
          fc["se"] > fn["se"] * 1.5,
          f"naive {fn['se']:.4f} → cluster {fc['se']:.4f}"
          f"（{fc['se'] / fn['se']:.2f} 倍）")
    cflip = classify(fn, fc)
    check("換標準誤造成的顯著性翻轉被判 unstable",
          (fn["p"] < ALPHA) != (fc["p"] < ALPHA) and cflip["verdict"] == "unstable",
          f"p {fn['p']:.4g} → {fc['p']:.4g}")
    # 反例：真 iid 資料，兩種 SE 應該幾乎一樣，不可以判翻轉
    yi = 0.6 * treat + rng.normal(0, 1, ng * per)
    fni = ols_fit(yi, Xp, 1, cov_type="naive")
    fci = ols_fit(yi, Xp, 1, cov_type="cluster", clusters=gid)
    check("iid 資料換 cluster-robust 不亂叫",
          classify(fni, fci)["verdict"] == "stable",
          f"SE {fni['se']:.4f} → {fci['se']:.4f}")

    # ── ⑥ R3：分析單位不符時基準自動走 cluster-robust ────────────
    df_panel = pd.DataFrame({"y": yp, "t": treat, "cid": gid})
    resp = analyze(df_panel, Spec(outcome="y", treatment="t", cluster_col="cid"),
                   B=200, seed=11, verbose=False)
    check("一列不是一個 cluster 時，基準標準誤自動走 cluster-robust",
          resp["base"]["cov_type"] == "cluster" and resp["panel"] is True,
          f"cov_type={resp['base']['cov_type']}")

    # ── ⑦ R3：無母數與參數在對數常態資料上結論不同 ───────────────
    a = rng.lognormal(0, 1.5, 60)
    b = rng.lognormal(0, 1.5, 60) * 1.0
    b[:3] = b[:3] * 60                       # 三個大戶把平均拉高、中位數不動
    df_np = pd.DataFrame({"y": np.concatenate([a, b]),
                          "grp": np.array([0] * 60 + [1] * 60, dtype=float)})
    d_np = build_design(df_np, Spec(outcome="y", treatment="grp"))
    base_np = ols_fit(d_np.y, d_np.X, d_np.j)
    r3np = r3_specification(d_np, base_np, Spec(outcome="y", treatment="grp"),
                            verbose=False)
    mw = [r for r in r3np["rows"] if "Mann-Whitney" in r["variant"]]
    check("R3 有跑出無母數對照", bool(mw) and mw[0]["verdict"] != "not_run",
          mw[0]["variant"] if mw else "沒跑")
    check("無母數變體的 delta_pct 留空（尺度已變，幅度不可比）",
          bool(mw) and mw[0]["delta_pct"] is None,
          f"delta_pct={mw[0]['delta_pct'] if mw else '—'}")
    ln = [r for r in r3np["rows"] if "ln" in r["variant"]]
    check("取 ln 的變體 delta_pct 也留空",
          bool(ln) and ln[0]["delta_pct"] is None)
    check("R3 至少跑到 4 組對照（16 §5.2 R3 的下限）",
          r3np["summary"]["對照組數"] >= R3_MIN_VARIANTS,
          f"{r3np['summary']['對照組數']} 組")
    check("R3 未執行的變體 note 非空（00 §1.6 降級不留空）",
          all(r["note"].strip() for r in r3np["rows"] if r["verdict"] == "not_run"))

    # ── ⑧ 多重比較：校正前顯著、校正後不顯著 ─────────────────────
    #    16 §3.1：43 個檢定不校正時 89% 機率至少一個假顯著。這裡把一個「勉強
    #    顯著」的 p 值丟進一族大 p 值裡，看 BH 會不會把它壓下去。
    #    族的大小由基準 p 反推（要 m·p > α 才可能翻），不是隨手挑一個數字 ——
    #    挑錯大小會得到一個永遠通過的假測試。
    d_bh = build_design(pd.DataFrame({"x": xc[:120], "y": 0.28 * xc[:120]
                                      + rng.normal(0, 1, 120)}),
                        Spec(outcome="y", treatment="x"))
    base_bh = ols_fit(d_bh.y, d_bh.X, d_bh.j)
    m_need = int(math.ceil((ALPHA * 1.5) / max(base_bh["p"], 1e-12)))
    fam = [0.30 + 0.002 * i for i in range(max(12, min(m_need, 400)))]
    r3bh = r3_specification(d_bh, base_bh, Spec(outcome="y", treatment="x"),
                            family_p=fam, family_name="自我測試族", verbose=False)
    bh = [r for r in r3bh["rows"] if "BH" in r["variant"] and r["verdict"] != "not_run"]
    check("多重比較校正後顯著性翻轉被抓到",
          base_bh["p"] < ALPHA and bool(bh) and bh[0]["p"] > ALPHA
          and bh[0]["verdict"] == "unstable",
          f"m={len(fam) + 1}，p {base_bh['p']:.4g} → p_BH "
          + (f"{bh[0]['p']:.4g}" if bh else "—"))
    # 反例：極顯著的 p 值套同一族 BH 之後不該翻
    r3bh2 = r3_specification(d_ok, base_ok, Spec(outcome="y", treatment="x"),
                             family_p=fam, family_name="自我測試族2", verbose=False)
    bh2 = [r for r in r3bh2["rows"] if "BH" in r["variant"] and r["verdict"] != "not_run"]
    check("BH 校正對極顯著的結論不亂叫",
          bool(bh2) and bh2[0]["verdict"] == "stable",
          f"p_BH={bh2[0]['p']:.3g}" if bh2 else "沒跑")

    # ── ⑨ R4：造一份「換時間切點結論就翻」的資料 ──────────────────
    dates = pd.date_range("2024-01-31", periods=24, freq="ME")
    ids = np.arange(50)
    rows_t = []
    for k, dt in enumerate(dates):
        early = k < 12
        for i in ids:
            t = float(i % 2)
            eff = 3.0 if early else -3.0      # 前 12 個月正效果、後 12 個月負效果
            rows_t.append({"日期": dt, "id": i, "t": t,
                           "y": eff * t + rng.normal(0, 1)})
    df_t = pd.DataFrame(rows_t)
    d_t = build_design(df_t, Spec(outcome="y", treatment="t", date_col="日期",
                                  id_col="id"))
    base_t = ols_fit(d_t.y, d_t.X, d_t.j)
    r4f = r4_time(d_t, base_t, Spec(outcome="y", treatment="t", date_col="日期",
                                    id_col="id"),
                  as_of=pd.Timestamp("2025-12-31"), window_months=12, verbose=False)
    check("R4 抓到時間切點翻轉", r4f["summary"]["verdict"] == "unstable",
          f"判定={r4f['summary']['verdict']}")
    flipped_t = [r for r in r4f["rows"] if r["verdict"] == "unstable"]
    check("R4 點名了是哪一個切點翻的", bool(flipped_t),
          flipped_t[0]["variant"] if flipped_t else "—")
    # 反例：效果不隨時間變 → 不該叫
    rows_s = []
    for dt in dates:
        for i in ids:
            t = float(i % 2)
            rows_s.append({"日期": dt, "id": i, "t": t,
                           "y": 3.0 * t + rng.normal(0, 1)})
    df_s = pd.DataFrame(rows_s)
    d_s = build_design(df_s, Spec(outcome="y", treatment="t", date_col="日期",
                                  id_col="id"))
    base_s = ols_fit(d_s.y, d_s.X, d_s.j)
    r4s = r4_time(d_s, base_s, Spec(outcome="y", treatment="t", date_col="日期",
                                    id_col="id"),
                  as_of=pd.Timestamp("2025-12-31"), window_months=12, verbose=False)
    check("R4 對時間穩定的資料不亂叫", r4s["summary"]["verdict"] == "stable",
          f"判定={r4s['summary']['verdict']}")
    check("R4 沒有時間欄時是 not_run 而不是靜默跳過",
          r4_time(d_ok, base_ok, Spec(outcome="y", treatment="x"),
                  verbose=False)["summary"]["verdict"] == "not_run")

    # ── ⑩ classify 的四條線逐條驗 ────────────────────────────────
    b0 = {"coef": 100.0, "se": 10.0, "p": 0.001}
    check("classify：符號翻轉 → unstable",
          classify(b0, {"coef": -20.0, "se": 10.0, "p": 0.04})["verdict"] == "unstable")
    check("classify：顯著性跨越 α → unstable",
          classify(b0, {"coef": 98.0, "se": 60.0, "p": 0.11})["verdict"] == "unstable")
    check("classify：幅度變動 > 50% → unstable",
          classify(b0, {"coef": 40.0, "se": 10.0, "p": 0.001})["verdict"] == "unstable",
          f"Δ={classify(b0, {'coef': 40.0, 'se': 10.0, 'p': 0.001})['delta_pct']:+.0f}%")
    check("classify：幅度變動 25–50% → stable_with_caveat",
          classify(b0, {"coef": 65.0, "se": 10.0, "p": 0.001})["verdict"]
          == "stable_with_caveat")
    check("classify：都沒變 → stable",
          classify(b0, {"coef": 95.0, "se": 10.0, "p": 0.002})["verdict"] == "stable")
    check("classify：尺度不可比時不拿幅度判（只看方向與顯著性）",
          classify(b0, {"coef": 0.4, "se": 0.1, "p": 0.001},
                   scale_comparable=False)["verdict"] == "stable",
          "係數從 100 變 0.4 但不判 unstable")
    check("worst_verdict 取最壞而不是多數決",
          worst_verdict(["stable", "stable", "stable", "unstable"]) == "unstable")

    # ── ⑪ 核心規則的機械檢查：翻轉的那一版不准從輸出消失 ──────────
    res_flip = analyze(df_flip, Spec(outcome="y", treatment="x", id_col="id"),
                       B=200, seed=3, verbose=False)
    sch = res_flip["schema"]
    check("schema 的 R1..R4 四列齊全",
          set(sch["check_id"]) >= {"R1", "R2", "R3", "R4"},
          "、".join(sorted(set(sch["check_id"]))))
    check("schema 欄位就是 16 §5.3 指定的八欄",
          list(sch.columns) == ["check_id", "variant", "coef", "se", "p",
                                "delta_pct", "verdict", "note"],
          "、".join(sch.columns))
    check("schema 的 verdict 只用四個合法值",
          set(sch["verdict"]) <= set(VERDICTS), "、".join(sorted(set(sch["verdict"]))))
    nr = sch[sch["verdict"] == "not_run"]
    check("not_run 的列 note 一律非空（16 §5.3 的 verify CHECK）",
          bool(len(nr)) and nr["note"].astype(str).str.strip().ne("").all(),
          f"{len(nr)} 列 not_run")
    n_unstable = int((sch["verdict"] == "unstable").sum())
    check("翻轉的變體有留在輸出表裡（不准只報對自己有利的那一版）",
          n_unstable > 0 and len(res_flip["flips"]) > 0,
          f"unstable {n_unstable} 列、翻轉清單 {len(res_flip['flips'])} 條")
    check("對照表第一列是基準設定，翻轉列與基準列同時存在",
          res_flip["對照表"].iloc[0]["檢定"] == "基準"
          and (res_flip["對照表"]["判定"] == "unstable").any())
    check("報告段落點名了翻轉，不是只寫「維持不變」",
          "unstable" in res_flip["report"] and "維持不變" not in
          res_flip["report"].split("結論句")[0],
          res_flip["report"].splitlines()[-1][:50])
    check("報告段落有 16 §5.3 的四段標題",
          all(f"{c} " in res_flip["report"] for c in ("R1", "R2", "R3", "R4")))
    check("全 stable 時報告會講「穩健 ≠ 因果」",
          "永遠不會升級證據等級" in analyze(
              pd.DataFrame({"x": xc, "y": yc}), Spec(outcome="y", treatment="x"),
              B=200, seed=5, verbose=False)["report"])

    # ── ⑫ 序列化：numpy 純量不可外洩到 json.dumps ─────────────────
    try:
        payload = {"checks": [{**{k: _py(v) for k, v in ck["summary"].items()},
                               "rows": [{k: _py(v) for k, v in r.items()}
                                        for r in ck["rows"]]}
                              for ck in res_flip["checks"]],
                   "flips": res_flip["flips"]}
        json.dumps(payload, ensure_ascii=False, default=_json_default)
        ser, msg = True, "含 numpy 分位數與 id 仍可序列化"
    except TypeError as e:
        ser, msg = False, str(e)
    check("結果可寫成 JSON（numpy 純量不外洩）", ser, msg)
    check("NaN 已在 _py 轉成 None（Infinity/NaN 不是合法 JSON）",
          _py(float("nan")) is None and _py(np.float64("inf")) is None)

    # ── ⑬ 輸入把關：該擋的要擋（退出碼才會是 1 而不是 70）──────────
    for name, bad_df, bad_spec in (
        ("欄名不存在", pd.DataFrame({"a": [1.0, 2.0]}), Spec(outcome="y", treatment="x")),
        ("treatment 三個水準",
         pd.DataFrame({"y": rng.normal(0, 1, 30),
                       "g": ["甲", "乙", "丙"] * 10}), Spec(outcome="y", treatment="g")),
        ("共變量完全共線",
         pd.DataFrame({"y": rng.normal(0, 1, 40), "x": xc[:40],
                       "x2": xc[:40] * 2.0}),
         Spec(outcome="y", treatment="x", covariates=("x2",))),
    ):
        try:
            build_design(bad_df, bad_spec)
            got, hit = "沒有擋下來", False
        except ValueError as e:
            got, hit = str(e).splitlines()[0][:40], "怎麼辦" in str(e)
        check(f"build_design 擋下「{name}」並講怎麼辦", hit, got)

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print(f"✅ 自我測試全部通過（共 {len(_SELFTEST_COUNTER)} 項）"
          if _SELFTEST_COUNTER else "✅ 自我測試全部通過")
    return EX_OK


_SELFTEST_COUNTER: list[int] = []


def main() -> int:
    ap = GateArgumentParser(
        description="穩健性檢定 R1–R4（16 §五）——「換了什麼 → 結論有沒有變」對照表。"
                    "核心規則：結論翻轉就必須寫進報告，不准只報對自己有利的那一版。",
        epilog="門檻出處：50%／5%／80%／0.6 全部出自 16 §5.2；"
               "25–50% 與 2–5% 的 stable_with_caveat 帶、R4 的名單定義是本腳本補訂。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--data", type=Path,
                    help="分析資料表（.parquet／.csv）。相對路徑相對專案根目錄")
    ap.add_argument("--outcome", help="結果變數欄名")
    ap.add_argument("--treatment", help="主結論的那個變數（數值或二元）")
    ap.add_argument("--covariates", default="",
                    help="共變量，逗號分隔。18-G3：tenure_days 至少要試一次進出模型")
    ap.add_argument("--cluster-col",
                    help="cluster bootstrap 與 cluster-robust SE 的分群欄（通常是顧客編號）。"
                         "一列不是一位顧客時這是硬規則（16 §七 P7）")
    ap.add_argument("--date-col", help="時間欄，R4 需要")
    ap.add_argument("--id-col", help="名單 id 欄（R4 的 Jaccard 用），預設沿用 --cluster-col")
    ap.add_argument("--as-of", help="基準時間切點（YYYY-MM-DD），預設取資料最大日期")
    ap.add_argument("--window-months", type=int, default=12, help="基準觀察窗月數（預設 12）")
    ap.add_argument("--list-pct", type=float, default=LIST_PCT,
                    help=f"R4 名單取前百分之幾（預設 {LIST_PCT:.0f}）")
    ap.add_argument("--family-p",
                    help="同族其他檢定的原始 p 值，逗號分隔。給了才跑「BH 校正前後」對照")
    ap.add_argument("--family-name", help="族的名字（16 §3.4 要求寫出來，讀者才知道 m 是多少）")
    ap.add_argument("--conclusion", help="主結論的一句話，會寫進報告段落的結論句")
    ap.add_argument("--model-name", help="輸出檔名的 <model> 部分")
    ap.add_argument("--B", type=int, default=BOOT_B,
                    help=f"cluster bootstrap 重抽次數（16 §5.2 R2 訂 {BOOT_B}）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=ALPHA,
                    help=f"顯著水準（預設 {ALPHA}）。放寬要照 16 §8.4 附加規則 2 聲明")
    ap.add_argument("--no-write", action="store_true", help="只算，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案代號，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()

    # 參數值不合法一律在 argparse 層擋 → 64。掉到 run() 裡會被判成 1（資料側問題），
    # 而這時候根本還沒碰到資料。
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")
    for name, val in (("--outcome", args.outcome), ("--treatment", args.treatment)):
        if not val:
            ap.error(f"要給 {name}")
    if args.data is None:
        ap.error("要給 --data（分析資料表）")
    if args.B < BOOT_B_MIN:
        ap.error(f"--B 至少 {BOOT_B_MIN}（收到 {args.B}）；16 §5.2 R2 訂 {BOOT_B}。"
                 f"太小時連 5% 的跨 0 比例都量不準")
    if not 0 < args.alpha < 1:
        ap.error(f"--alpha 要在 (0, 1) 之間（收到 {args.alpha}）")
    if not 0 < args.list_pct < 100:
        ap.error(f"--list-pct 要在 (0, 100) 之間（收到 {args.list_pct}）")
    if args.window_months < 1:
        ap.error(f"--window-months 要 ≥ 1（收到 {args.window_months}）")
    if args.as_of:
        try:
            pd.Timestamp(args.as_of)
        except (ValueError, TypeError):
            ap.error(f"--as-of 要是可解析的日期（收到 {args.as_of!r}），例如 2026-06-30")
    if args.family_p:
        try:
            vals = [float(x) for x in args.family_p.split(",") if x.strip()]
        except ValueError:
            ap.error(f"--family-p 要是逗號分隔的數字（收到 {args.family_p!r}）")
        if any(not 0 <= v <= 1 for v in vals):
            ap.error("--family-p 的每個值都要在 [0, 1] 之間 —— 那是 p 值")

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
        print(f"⛔ robustness.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
