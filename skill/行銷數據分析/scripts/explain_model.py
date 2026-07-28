#!/usr/bin/env python3
"""
模型解釋：SHAP／特徵重要度／Lift-Gain（12 §五、§六、§九）

這支腳本回答的是**行銷部門真正會問的三件事**，不是「模型準不準」：

  ① 「這次只發 1 萬封，該發給誰、能撈到多少？」→ 十分位 Lift 表與 Gain 曲線（§五）
  ② 「為什麼是這些人？」                        → SHAP（§六），含個體層級貢獻
  ③ 「這模型值不值得上線？」                    → 與 naive baseline 對照（§九）

AUC 一句都回答不了上面三題。12 §五 講得很白：AUC 問的是「隨機抽一正一負，模型給
正類更高分的機率」，那是全域指標；而行銷的決策是局部的 —— 只發前 10%，命中率多少。

**這支腳本最重要的一句話，寫在每次輸出裡：SHAP 是「模型怎麼想」，不是「世界怎麼
運作」。** SHAP 值是模型內部的加法分解，它忠實反映的是這個模型的思路，不是資料
生成機制。把「R 的 SHAP 最大」讀成「把 R 壓下來就能降低流失」，等於拿一個只被訓練
來排序的東西去回答一個介入問題 —— 12 §六 警語表第一列、00 §1.5 措辭白名單（預測級
禁用任何 intervention 語句）、18-G6 都在擋這一句。

第二重要的是**特徵重要度在共線變數之間會被稀釋**。permutation importance 的定義是
「打亂它，分數掉多少」；兩個高度相關的特徵互相掩護，各自打亂都不掉分，兩個都會被
排到後面（12 §六 對照表原話）。SHAP 也不能免疫 —— TreeSHAP 的路徑相依讓貢獻在相關
特徵之間被分攤。所以本腳本一定會跑 VIF（門檻出自 05 §1.4），並把 SHAP 與 permutation
的排名落差當成共線性的徵狀報出來。

shap 沒裝就降級到 permutation importance ＋ 逐特徵 PDP，並**明講降級了**（12 §一
環境表的替代方案；報告必須註明「無個體層級解釋」）。降級不是靜默的。

用法：
    # 有模型檔與評估資料表
    python explain_model.py 2026Q3_電商 --model 模型輸出/model.joblib \
        --data 模型輸出/test_matrix.parquet --target 是否流失 --eval-split out_of_time

    # 只有分數欄（模型在另一個環境跑的）→ 只做 Lift/Gain
    python explain_model.py 2026Q3_電商 --data 模型輸出/scored.parquet \
        --target 是否流失 --score-col 流失機率 --baseline-col R天數倒序

    python explain_model.py --self-test

輸出：
    統計表/預測模型/表11.2_十分位Lift表.csv     ← ref 19 §1.7 表 11.2 本體
    統計表/預測模型/lift_gain_曲線資料.csv       ← 圖與表同一份計算結果（19 §6.2）
    統計表/預測模型/SHAP_特徵重要度.csv
    統計表/預測模型/特徵重要度_三法對照.csv      ← SHAP vs permutation vs tree
    統計表/預測模型/共線性_VIF.csv
    統計表/預測模型/PDP_逐特徵.csv               ← 只有降級時才產
    模型輸出/shap_個體貢獻_top3.parquet          ← 行銷話術素材（§六）
    模型輸出/explain_model.json                  ← 機器可讀，供 build_report 引用
    主控台另印可直接貼進報告的三句話與解讀警語

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全過
    1  = 有 error 擋住（標籤退化、欄位重複／dummy trap、特徵順序對不上模型…）
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

# ── 門檻。有出處的寫出處；本腳本自訂的一律標明，不要假裝是 reference 給的 ──
N_BINS_DEFAULT = 10          # 12 §五 表 11.2 是「十分位」Lift 表
MIN_BIN_N = 30               # 每箱 <30 標 N/A（12 §三 校準分箱同數；00 §四「有樣本但算不出可信值」）
MIN_POSITIVE_N = 200         # 12 §九「標籤太稀有：正類 < 200 筆 → 不建模」
TOP_DECILE_LIFT_ALERT = 2.0  # 12 §十 監控告警門檻（該處已標【推導，待驗證】）
AUC_GAIN_MIN = 0.03          # 12 §九／00 §1.5：相對 baseline 提升 < 0.03 AUC → 不建議上線
VIF_HIGH = 10.0              # 05 §1.4 高度共線
VIF_STRICT = 5.0             # 05 §1.4 嚴管產業（電力／通訊／金融）
VIF_DEGENERATE = 1000.0      # 05 §1.4：> 1000 不是共線，是欄位重複或 dummy trap

# 以下四個 reference 沒有給數字，是本腳本的判斷，全部標【推導，待驗證】。
# 改門檻要連同這裡的理由一起改，不要只改數字。
SHAP_DOMINANCE_SHARE = 0.50  # 單一特徵佔 mean|SHAP| 總和 > 50% → 洩漏嫌疑。
                             # 理由：d 個特徵均分時每個佔 1/d；單一特徵超過一半，
                             # 代表其餘全部加起來還不如它 —— 12 §六 說「先懷疑洩漏」
                             # 的那種長相（教材原例：用「已成交金額」預測「是否成交」）
RANK_GAP_ALERT = 3           # SHAP 與 permutation 排名差 ≥3 名 → 查共線（12 §六 只說「差很多」）
TIE_SHARE_ALERT = 0.10       # 單一分數值佔 >10% → 十分位邊界是任意切的，Lift 不可細讀
MONO_RHO = 0.5               # |Spearman(特徵值, SHAP值)| ≥ 0.5 才敢說方向單調

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

    這裡的 numpy 純量來源很多：value_counts 的索引、argsort 出來的位置、
    mean|SHAP| 的 float32。它們會一路帶進結果 dict，json.dumps 到最後才丟
    TypeError —— 而且是在 SHAP 都算完、CSV 都寫好之後才炸，退出碼 70 蓋掉
    前面全綠的結論。在來源轉掉。
    """
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy 型別時，讓它存成字串而不是讓整支腳本掛掉。"""
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    if isinstance(o, (Path, datetime)):
        return str(o)
    return str(o)


# ══════════════════════════════════════════════════════════════
#  小工具：排名、Spearman、AUC
# ══════════════════════════════════════════════════════════════
def _rankdata(a: np.ndarray) -> np.ndarray:
    """平均秩（同 scipy.stats.rankdata 的 'average'）。

    自己寫是為了讓 AUC 與 Spearman 兩處共用同一套並列處理 —— 兩邊用不同的
    並列規則會讓「AUC 0.5 但 Spearman 不是 0」這種對不上的結果出現。
    """
    a = np.asarray(a, dtype=float)
    order = np.argsort(a, kind="stable")
    ranks = np.empty(len(a), dtype=float)
    sorted_a = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _rankdata(x), _rankdata(y)
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def auc_score(y: np.ndarray, s: np.ndarray) -> float:
    """AUC = (Σ 正類的秩 − n₊(n₊+1)/2) / (n₊·n₋)，並列取平均秩。

    等價於 Mann-Whitney U / (n₊·n₋)，也就是 12 §五 講的「隨機抽一正一負，
    模型給正類更高分的機率」。並列算 0.5 分，這正是平均秩自動處理掉的部分。
    """
    y = np.asarray(y, dtype=float)
    n_pos = int((y == 1).sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = _rankdata(np.asarray(s, dtype=float))
    return float((r[y == 1].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


# ══════════════════════════════════════════════════════════════
#  ① Lift / Gain（12 §五；表 11.2）
# ══════════════════════════════════════════════════════════════
def tie_report(score: np.ndarray) -> dict[str, Any]:
    """分數的並列狀況。

    為什麼要看：十分位是「按分數排序後等人數切」。若模型只吐得出 6 個相異
    分數（淺樹、規則模型、或分數被四捨五入過），切出來的十分位邊界落在並列
    群內部，誰進 D1 誰進 D2 純看排序穩定性 —— Lift 表看起來照樣有數字，
    但那個數字不可細讀。
    """
    s = np.asarray(score, dtype=float)
    n = len(s)
    vals, cnts = np.unique(s, return_counts=True)
    top = int(cnts.max()) if len(cnts) else 0
    return {"相異分數數": int(len(vals)), "最大並列組人數": top,
            "最大並列組佔比": round(top / n, 4) if n else float("nan")}


def lift_gain_table(y: np.ndarray, score: np.ndarray,
                    bins: int = N_BINS_DEFAULT) -> pd.DataFrame:
    """十分位 Lift 表（ref 19 表 11.2 的欄位：十分位／人數／回應數／回應率／Lift／累積 Gain）。

    Lift_k = 該箱回應率 / 母體整體回應率；Gain_k = 前 k 箱抓到的回應者 / 全部回應者。
    公式出處：12 §五。
    """
    y = np.asarray(y, dtype=float)
    s = np.asarray(score, dtype=float)
    n = len(y)
    total_pos = float(y.sum())
    base = total_pos / n if n else float("nan")

    # 分數由高到低。kind="stable" 讓並列的相對順序等於原始列序 ——
    # 不指定的話 numpy 的內定排序對並列不保證穩定，兩次跑同一份資料
    # 可能得到不同的十分位成員，而報告的數字必須可重現。
    order = np.argsort(-s, kind="stable")
    ys = y[order]

    bounds = [int(round(n * i / bins)) for i in range(bins + 1)]
    rows: list[dict[str, Any]] = []
    cum = 0.0
    for i in range(bins):
        lo, hi = bounds[i], bounds[i + 1]
        seg = ys[lo:hi]
        n_k = int(len(seg))
        resp = float(seg.sum())
        cum += resp
        small = n_k < MIN_BIN_N
        rate = (resp / n_k) if n_k and not small else float("nan")
        lift = (rate / base) if (n_k and not small and base > 0) else float("nan")
        rows.append({
            "十分位": f"D{i + 1}",
            "人數": n_k,
            "回應數": int(resp),
            "該箱回應率": None if np.isnan(rate) else round(rate, 6),
            "Lift": None if np.isnan(lift) else round(lift, 4),
            "累積人數": int(hi),
            "累積回應數": int(cum),
            "累積Gain%": round(cum / total_pos * 100, 2) if total_pos > 0 else None,
            "累積回應率": round(cum / hi, 6) if hi else None,
            "結論": (f"N/A（該箱 n={n_k} < {MIN_BIN_N}，算不出可信值）" if small
                     else ("命中率高於亂發" if lift and lift > 1
                           else "比亂發還糟 —— 模型已明講他們不會回應")),
        })
    return pd.DataFrame(rows)


def gain_curve(y: np.ndarray, score: np.ndarray, step_pct: float = 1.0) -> pd.DataFrame:
    """Lift/Gain 曲線的資料點（圖與表用同一份計算結果 —— ref 19 §6.2 的硬規則）。

    圖不可以自己重算一次：資料更新過、排序穩定性不同、並列處理不同，
    任一項都會讓「同一張圖」與表對不上（18-E7 那個坑）。
    """
    y = np.asarray(y, dtype=float)
    s = np.asarray(score, dtype=float)
    n = len(y)
    total_pos = float(y.sum())
    order = np.argsort(-s, kind="stable")
    ys = y[order]
    cum = np.cumsum(ys)
    rows = []
    pct = step_pct
    while pct <= 100.0 + 1e-9:
        k = max(1, int(round(n * pct / 100.0)))
        g = cum[k - 1] / total_pos if total_pos > 0 else float("nan")
        rows.append({"名單比例%": round(pct, 2), "人數": k,
                     "累積回應數": int(cum[k - 1]),
                     "累積Gain%": round(g * 100, 4),
                     "累積Lift": round(g / (pct / 100.0), 4)})
        pct += step_pct
    return pd.DataFrame(rows)


def gate_label(y: np.ndarray) -> dict[str, Any]:
    """標籤本身站不站得住（12 §九「標籤太稀有」那一列）。"""
    print("\n① 標籤與分數的體檢")
    n = len(y)
    n_pos = int(np.asarray(y).sum())
    res: dict[str, Any] = {"n": n, "正類數": n_pos,
                           "正類佔比": round(n_pos / n, 6) if n else None}
    if n_pos == 0 or n_pos == n:
        err(f"標籤退化：{n} 列裡正類 {n_pos} 筆（另一類 {n - n_pos} 筆）",
            "Lift 的分母是母體回應率，單一類別時它是 0 或 1，整張表沒有意義。"
            "先確認 --target 指到的是標籤欄、--positive-label 指到的是正類的值")
        res["結果"] = "error"
        return res
    detail(f"n = {n:,}｜正類 {n_pos:,} 筆（{n_pos / n:.2%}）")
    if n_pos < MIN_POSITIVE_N:
        warn(f"正類只有 {n_pos} 筆 < {MIN_POSITIVE_N} 筆",
             "12 §九：正類 < 200 筆不建模，改用業務規則 + 敘述統計，"
             "並說明需要多少筆才值得建模。已經訓練好的模型可以照跑，"
             "但十分位表的每一格都只有個位數回應者，不要拿它下結論")
        res["結果"] = "warning"
    else:
        ok(f"正類 {n_pos} 筆 ≥ {MIN_POSITIVE_N} 筆（12 §九 的建模下限）")
        res["結果"] = "pass"
    if n_pos / n < 0.10:
        info(f"正類佔比 {n_pos / n:.2%} < 10% —— 12 §五：主指標改看 PR/AP，"
             f"ROC/AUC 只當模型間比較的輔助（FPR 的分母含大量 TN，AUC 會虛高）")
    return res


def gate_ties(score: np.ndarray, bins: int) -> dict[str, Any]:
    print("\n② 分數的並列狀況（決定十分位切不切得開）")
    rep = tie_report(score)
    res: dict[str, Any] = dict(rep)
    detail(f"相異分數 {rep['相異分數數']:,} 種｜最大並列組 {rep['最大並列組人數']:,} 人"
           f"（{rep['最大並列組佔比']:.2%}）")
    if rep["相異分數數"] < bins:
        err(f"相異分數只有 {rep['相異分數數']} 種，切不出 {bins} 個十分位",
            "模型輸出的解析度不足（淺樹或規則模型常見）。改用相異分數當分箱，"
            "或直接報「分數只有 N 級」而不要假裝有十分位")
        res["結果"] = "error"
        return res
    if rep["最大並列組佔比"] > TIE_SHARE_ALERT:
        warn(f"單一分數值佔了 {rep['最大並列組佔比']:.1%} 的人（門檻 {TIE_SHARE_ALERT:.0%}）",
             "十分位邊界落在並列群內部，誰進 D1 誰進 D2 是任意的。"
             "報告要寫明這件事，或改用「分數層級」而非十分位切名單")
        res["結果"] = "warning"
    else:
        ok(f"並列不影響十分位切分（最大並列組 {rep['最大並列組佔比']:.2%}）")
        res["結果"] = "pass"
    return res


def gate_lift(tbl: pd.DataFrame, y: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    """讀十分位表並發警告。回傳 top decile lift 等關鍵數字。"""
    print("\n③ 十分位 Lift 表（12 §五；ref 19 表 11.2）")
    # 用欄名取值。itertuples 對「累積Gain%」這種含 % 的欄名會改成位置代號 _N，
    # 欄序一動就對到別欄 —— 那是靜默錯誤，不會報錯。
    for _, r in tbl.iterrows():
        lift = "—" if r["Lift"] is None else f"{r['Lift']:.2f}"
        rate = "—" if r["該箱回應率"] is None else f"{r['該箱回應率']:.2%}"
        detail(f"{r['十分位']}｜{r['人數']:>6,} 人｜回應 {r['回應數']:>5,}｜"
               f"回應率 {rate:>7}｜Lift {lift:>6}｜累積 Gain {r['累積Gain%']}%")

    res: dict[str, Any] = {}
    top = tbl.iloc[0]
    tdl = top["Lift"]
    res["top_decile_lift"] = tdl
    res["每箱人數不足"] = int(sum(1 for _, r in tbl.iterrows() if r["Lift"] is None))

    if res["每箱人數不足"]:
        warn(f"{res['每箱人數不足']} 個十分位的人數 < {MIN_BIN_N}，該箱回應率與 Lift 標 N/A",
             "00 §四：有樣本但算不出可信值就標 N/A，不要填一個看起來合理的數。"
             "改用五分位（--bins 5）或先把評估集加大")

    if tdl is None:
        warn("算不出 top decile lift", "見上一條：D1 的人數不足")
    elif tdl < TOP_DECILE_LIFT_ALERT:
        warn(f"top decile lift = {tdl:.2f} < {TOP_DECILE_LIFT_ALERT}",
             f"12 §十 把這個數字當上線後的告警線（該處標【推導，待驗證】）。"
             f"前 10% 名單的命中率只有亂發的 {tdl:.2f} 倍，"
             f"先跟 naive baseline 比（§九）再決定要不要上線")
    else:
        ok(f"top decile lift = {tdl:.2f} ≥ {TOP_DECILE_LIFT_ALERT}"
           f"（前 10% 名單命中率是亂發的 {tdl:.2f} 倍）")

    # 雙路徑驗算（00 §1.3）：十分位表的累積回應數，必須等於直接從排序陣列數出來的。
    # 兩條路徑都很短，但它們會抓到「分箱邊界算錯一格」這種只差一點的錯 ——
    # 那種錯不會讓表看起來怪，只會讓 Gain 全部偏一點點。
    yv = np.asarray(y, dtype=float)
    order = np.argsort(-np.asarray(score, dtype=float), kind="stable")
    cum_direct = np.cumsum(yv[order])
    mismatch = []
    for _, r in tbl.iterrows():
        k = int(r["累積人數"])
        if k and int(cum_direct[k - 1]) != int(r["累積回應數"]):
            mismatch.append(f"{r['十分位']}（表 {r['累積回應數']} vs 直算 {int(cum_direct[k - 1])}）")
    total_pos = int(yv.sum())
    tail_ok = int(tbl["累積回應數"].iloc[-1]) == total_pos
    res["雙路徑驗算"] = "通過" if (not mismatch and tail_ok) else "不通過"
    if mismatch or not tail_ok:
        err(f"Lift 表的累積回應數與直接計算對不上：{'、'.join(mismatch) or '最後一格未收斂到總回應數'}",
            "這是腳本或分箱邊界的問題，不是資料的問題。先不要用這張表，回報這個訊息")
        res["結果"] = "error"
        return res
    ok(f"雙路徑驗算通過：累積回應數與直接計算逐格相同，最後一格 = 全部 {total_pos} 位回應者")
    res["結果"] = "warning" if (res["每箱人數不足"] or (tdl is not None and tdl < TOP_DECILE_LIFT_ALERT)) else "pass"
    return res


def report_sentences(tbl: pd.DataFrame, base_rate: float) -> str:
    """12 §五「這張表一眼可讀的三件事」—— 直接產成可貼進報告的句子。

    措辭照 00 §1.5 的預測級白名單：用「命中」「模型排序下前 N%」，
    不用「帶來」「驅動」。這三句 AUC 一句都寫不出來。
    """
    lines: list[str] = []
    top = tbl.iloc[0]
    if top["Lift"] is not None:
        lines.append(
            f"· 模型排序下前 10% 的名單命中率為 {top['該箱回應率']:.1%}，"
            f"是母體整體回應率 {base_rate:.1%} 的 {top['Lift']:.2f} 倍（top decile lift）。")
    # 前 k 分位抓到多少回應者：取累積 Gain 首次 ≥70% 的那一格
    hit = None
    for i, (_, r) in enumerate(tbl.iterrows()):
        if r["累積Gain%"] is not None and r["累積Gain%"] >= 70.0:
            hit = (i + 1, r["累積Gain%"])
            break
    if hit:
        pct = hit[0] / len(tbl) * 100
        lines.append(f"· 發前 {pct:.0f}% 就命中 {hit[1]:.1f}% 的回應者。")
    below = [r["十分位"] for _, r in tbl.iterrows()
             if r["Lift"] is not None and r["Lift"] < 1.0]
    if below:
        first = below[0]
        idx = int(first[1:])
        lines.append(f"· {first} 起 Lift < 1，發給後 {(len(tbl) - idx + 1) / len(tbl) * 100:.0f}% 的人"
                     f"比亂發還糟 —— 模型已經明確告訴你他們不會回應。")
    lines.append("· 以上三句的證據等級最高到「預測」，且必須同時具備 out-of-time 驗證與 "
                 "naive baseline 對照才成立（00 §1.5）。禁用「帶來」「驅動」「因此增加」。")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
#  ② baseline 對照（12 §九）
# ══════════════════════════════════════════════════════════════
def gate_baseline(y: np.ndarray, score: np.ndarray,
                  baseline: np.ndarray | None, baseline_name: str,
                  bins: int) -> dict[str, Any]:
    """沒有 baseline 對照的模型不是模型，是裝飾（12 開頭那句）。"""
    print("\n④ naive baseline 對照（12 §九；0.03 AUC 硬門檻）")
    auc_m = auc_score(y, score)
    res: dict[str, Any] = {"模型AUC": round(auc_m, 4) if np.isfinite(auc_m) else None}
    detail(f"候選模型 AUC = {auc_m:.4f}")
    if baseline is None:
        warn("這次沒有給 naive baseline（--baseline-col）",
             "12 開頭：沒有 baseline 對照的模型不是模型，是裝飾。實證：14 個特徵、"
             "跑完 backward elimination 的 logistic 拿到 AUC 0.89，而「只用 R 單變數排序」"
             "的 baseline 是 0.86 —— 整套工程只多 0.03，80 萬喚回預算花在一行 SQL "
             "就能做到的事情上。至少補一個 R 排序或 RFM Score 排序當對照欄再跑一次")
        res.update({"baseline": None, "結果": "warning"})
        return res

    auc_b = auc_score(y, baseline)
    delta = auc_m - auc_b
    tbl_b = lift_gain_table(y, baseline, bins)
    res.update({"baseline名稱": baseline_name,
                "baselineAUC": round(auc_b, 4) if np.isfinite(auc_b) else None,
                "AUC提升": round(delta, 4),
                "baseline_top_decile_lift": tbl_b["Lift"].iloc[0]})
    detail(f"baseline（{baseline_name}）AUC = {auc_b:.4f}｜"
           f"top decile lift = {tbl_b['Lift'].iloc[0]}")
    detail(f"相對 baseline 的 AUC 提升 = {delta:+.4f}")
    if delta < AUC_GAIN_MIN:
        warn(f"相對 baseline 只提升 {delta:+.4f} AUC < {AUC_GAIN_MIN}",
             "12 §九 硬門檻：強制寫「不建議上線，用 baseline 排序即可」。"
             "同一條也寫在 00 §1.5 的證據等級決策樹裡 —— 提升不足時證據等級"
             "升不到「預測」。表 11.1 至少三列（R 排序／RFM Score 排序／候選模型）")
        res["結果"] = "warning"
    else:
        ok(f"相對 baseline 提升 {delta:+.4f} ≥ {AUC_GAIN_MIN} → 證據等級可主張到「預測」"
           f"（前提是評估集確實是 out-of-time）")
        res["結果"] = "pass"
    return res


def gate_eval_split(kind: str) -> dict[str, Any]:
    """評估集是不是 out-of-time —— 腳本看不出來，只能要求分析者具名宣告。"""
    print("\n⑤ 評估集的性質（00 §1.5 證據等級決策樹）")
    res = {"評估切分": kind}
    if kind == "out_of_time":
        ok("已宣告為 out-of-time（用更晚的 as_of 重建特徵與標籤）")
        res["結果"] = "pass"
    elif kind == "random":
        warn("評估集是隨機切列",
             "00 §1.5：沒有 out-of-time 驗證就降回「相關」等級。12 §二：隨機切列在"
             "有時間結構或有顧客重複的資料上會讓分數系統性樂觀（實證：驗證集 AUC 0.95、"
             "上線崩盤，18-G4）。Lift 表照樣可以出，但不可寫成「上線後預期命中率」")
        res["結果"] = "warning"
    else:
        warn("沒有宣告評估集的切分方式（--eval-split unknown）",
             "本腳本看不出資料是怎麼切的。在確認是 out-of-time 之前，"
             "這張 Lift 表的證據等級只能標「相關」（00 §1.5）。"
             "確認後用 --eval-split out_of_time 重跑，讓宣告留在 JSON 裡")
        res["結果"] = "warning"
    return res


# ══════════════════════════════════════════════════════════════
#  ③ 共線性（05 §1.4）—— 特徵重要度會在這裡被稀釋
# ══════════════════════════════════════════════════════════════
def vif_table(X: pd.DataFrame) -> pd.DataFrame:
    """逐欄 VIF = 1/(1−R²_j)，R²_j 是「該欄對其餘欄」的線性迴歸。

    自己用最小平方解，不引 statsmodels：08 §六 已經記過 statsmodels 的
    variance_inflation_factor 兩個坑（要自己迴圈、會把截距也算一格）。
    """
    cols = list(X.columns)
    A = X.to_numpy(dtype=float)
    rows = []
    for j, c in enumerate(cols):
        yj = A[:, j]
        sst = float(((yj - yj.mean()) ** 2).sum())
        if sst == 0:
            rows.append({"特徵": c, "VIF": None, "R2": None,
                         "判定": "常數欄", "結論": "不帶資訊卻會污染重要度排序，先排除（12 §七）"})
            continue
        if len(cols) == 1:
            rows.append({"特徵": c, "VIF": 1.0, "R2": 0.0, "判定": "單一特徵",
                         "結論": "只有一個特徵，沒有共線性可言"})
            continue
        rest = np.delete(A, j, axis=1)
        design = np.column_stack([np.ones(len(A)), rest])
        beta, *_ = np.linalg.lstsq(design, yj, rcond=None)
        resid = yj - design @ beta
        r2 = 1.0 - float((resid ** 2).sum()) / sst
        r2 = min(max(r2, 0.0), 1.0)
        vif = float("inf") if r2 >= 1.0 - 1e-12 else 1.0 / (1.0 - r2)
        if vif > VIF_DEGENERATE:
            verdict, note = "欄位重複／dummy trap", (
                "05 §1.4：VIF = ∞ 或 > 1000 不是共線性，是欄位重複或 dummy trap，回 M1 查")
        elif vif > VIF_HIGH:
            verdict, note = "高度共線", "重要度會被相關特徵分攤，排序不可細讀"
        elif vif > VIF_STRICT:
            verdict, note = "嚴管產業門檻超標", "電力／通訊／金融的門檻是 5，其他產業可放行"
        else:
            verdict, note = "通過", "共線性不影響重要度排序"
        rows.append({"特徵": c, "VIF": round(vif, 4) if np.isfinite(vif) else None,
                     "R2": round(r2, 6), "判定": verdict, "結論": note})
    return pd.DataFrame(rows)


def gate_collinearity(X: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    print(f"\n⑥ 共線性（05 §1.4；VIF > {VIF_HIGH:.0f} 高度共線，嚴管產業 > {VIF_STRICT:.0f}）")
    tbl = vif_table(X)
    res: dict[str, Any] = {}
    dead = [r["特徵"] for _, r in tbl.iterrows()
            if r["判定"] in ("欄位重複／dummy trap", "常數欄")]
    high = [(r["特徵"], r["VIF"]) for _, r in tbl.iterrows() if r["判定"] == "高度共線"]
    mid = [r["特徵"] for _, r in tbl.iterrows() if r["判定"] == "嚴管產業門檻超標"]
    vals = [r["VIF"] for _, r in tbl.iterrows() if r["VIF"] is not None]
    res["最大VIF"] = round(max(vals), 4) if vals else None

    for _, r in tbl.sort_values("VIF", ascending=False, na_position="first").iterrows():
        v = "∞／常數" if r["VIF"] is None else f"{r['VIF']:.2f}"
        detail(f"{r['特徵']}：VIF = {v}｜{r['判定']}")

    if dead:
        err(f"{len(dead)} 個特徵是常數欄或與其他欄完全線性相依：{'、'.join(dead)}",
            "05 §1.4：這不是共線性，是欄位重複或 dummy trap，回 M1 查；"
            "12 §七 也要求建模前用 scan_columns.py 把常數與近常數欄踢掉。"
            "在這之前，SHAP 與 permutation 的排序都不可讀 —— "
            "重複欄會把同一份貢獻切成兩半，兩個都排到後面")
        res["結果"] = "error"
    elif high:
        warn(f"{len(high)} 個特徵 VIF > {VIF_HIGH:.0f}："
             + "、".join(f"{c}({v:.1f})" for c, v in high),
             "12 §六：permutation importance 對共線特徵會互相掩護（兩個高度相關的"
             "特徵各自打亂都不掉分，兩個都被排到後面）；SHAP 也受特徵相關性影響"
             "（TreeSHAP 的路徑相依）。**重要度排序在這幾個變數之間不可細讀**，"
             "報告要把它們當一組談，或照 05 §1.4 的階梯處理："
             "補資料 → 合成變數 → 轉換 → 移除其一")
        res["結果"] = "warning"
    else:
        ok(f"各特徵 VIF ≤ {VIF_HIGH:.0f}，重要度不會被共線稀釋"
           + (f"（{'、'.join(mid)} 超過嚴管產業的 {VIF_STRICT:.0f}）" if mid else ""))
        res["結果"] = "pass"
    if mid and res.get("結果") != "error":
        info(f"{'、'.join(mid)} 的 VIF 在 {VIF_STRICT:.0f}–{VIF_HIGH:.0f} 之間 —— "
             f"電力／通訊／金融屬嚴管產業，門檻是 5（05 §1.4）")
    return res, tbl


# ══════════════════════════════════════════════════════════════
#  ④ SHAP（12 §六）與降級
# ══════════════════════════════════════════════════════════════
def shap_available() -> tuple[bool, str]:
    try:
        import shap  # noqa: F401
        return True, getattr(shap, "__version__", "未知版本")
    except Exception as exc:  # noqa: BLE001 - ImportError 之外還可能是相依套件版本衝突
        return False, f"{type(exc).__name__}: {exc}"


def _normalize_shap(values: Any, base: Any, pos_idx: int) -> tuple[np.ndarray, np.ndarray]:
    """把 shap 的輸出統一成 (n, d) 的正類貢獻矩陣 + (n,) 的 base value。

    形狀是這裡最容易靜默出錯的地方，實測（shap 0.52.0 + sklearn 1.9.0）：
      · sklearn 的二元分類器 → Explanation.values 是 (n, d, 2)，要取正類那一片
      · xgboost 的二元分類器 → (n, d)，沒有類別維度
      · 舊 API shap_values() → list[array]，每個類別一個
    取錯片不會報錯，只會讓每個特徵的方向全部反過來 —— 所以下面一定要跑
    加法性驗算（sum(shap) + base ≈ 模型輸出）把取錯的情況攔下來。
    """
    vals = np.asarray(values)
    if isinstance(base, (list, tuple)):
        base = np.asarray(base)
    base = np.asarray(base, dtype=float)
    if vals.ndim == 3:
        vals = vals[:, :, pos_idx]
        if base.ndim == 2:
            base = base[:, pos_idx]
        elif base.ndim == 1 and base.size == vals.shape[1]:
            pass
    if base.ndim == 0:
        base = np.repeat(float(base), vals.shape[0])
    base = base.ravel()
    if base.size == 1:
        base = np.repeat(base[0], vals.shape[0])
    return np.asarray(vals, dtype=float), base


def additivity_error(shap_vals: np.ndarray, base: np.ndarray,
                     pred: np.ndarray) -> float:
    """SHAP 的加法性：base + Σ shap = 模型輸出。回傳最大絕對誤差。

    這是一條免費的雙路徑驗算（00 §1.3）：一條路徑是 explainer 給的分解，
    另一條是模型自己的 predict_proba。對不上就代表類別維度取錯、或 explainer
    的 model_output 設定與我們的假設不同 —— 兩者都會讓整張 SHAP 圖的方向錯。
    """
    if len(base) != len(shap_vals):
        return float("inf")
    recon = base + shap_vals.sum(axis=1)
    return float(np.max(np.abs(recon - np.asarray(pred, dtype=float))))


def shap_importance(model: Any, X: pd.DataFrame, pos_idx: int,
                    pred: np.ndarray) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    """TreeExplainer → mean|SHAP| 排序表 + 原始 (n, d) 矩陣。

    只用 TreeExplainer。非樹模型（例如 CalibratedClassifierCV 包過的模型、
    LogisticRegression）故意不退到 KernelExplainer —— 它是 O(n·2^d) 的取樣近似，
    在幾千列的行銷資料上會跑到讓人以為當掉，然後有人就把 n 砍到 100 列，
    得到一份雜訊很大的 beeswarm。寧可降級到 permutation importance 並說清楚。
    """
    import shap

    explainer = shap.TreeExplainer(model)
    sv = explainer(X)
    vals, base = _normalize_shap(sv.values, sv.base_values, pos_idx)
    meta: dict[str, Any] = {"explainer": "TreeExplainer",
                            "shap形狀": list(np.asarray(sv.values).shape)}
    meta["加法性最大誤差"] = additivity_error(vals, base, pred)
    tbl = _importance_from_shap(vals, X)
    return tbl, vals, meta


def _importance_from_shap(vals: np.ndarray, X: pd.DataFrame) -> pd.DataFrame:
    """mean|SHAP| 排序 + 方向。

    方向用 Spearman(特徵值, 該特徵的 SHAP 值)：|ρ| ≥ 0.5 才敢說單調，
    否則寫「非單調」—— 交互作用強的特徵硬給一個方向，比不給更糟。
    """
    rows = []
    total = float(np.abs(vals).mean(axis=0).sum())
    for j, c in enumerate(X.columns):
        m = float(np.abs(vals[:, j]).mean())
        rho = spearman(X[c].to_numpy(dtype=float), vals[:, j])
        if not np.isfinite(rho) or abs(rho) < MONO_RHO:
            direction = "非單調（有交互作用或分段效果，看 dependence 圖）"
        elif rho > 0:
            direction = "值越高，分數越高"
        else:
            direction = "值越高，分數越低"
        rows.append({"特徵": c, "mean|SHAP|": round(m, 6),
                     "佔比": round(m / total, 6) if total > 0 else None,
                     "與特徵值的Spearman": round(rho, 4) if np.isfinite(rho) else None,
                     "方向": direction})
    tbl = pd.DataFrame(rows).sort_values("mean|SHAP|", ascending=False)
    tbl.insert(0, "排名", range(1, len(tbl) + 1))
    tbl["結論"] = [f"第 {r} 名，佔全部歸因的 {s:.1%}"
                   if s is not None else f"第 {r} 名"
                   for r, s in zip(tbl["排名"], tbl["佔比"])]
    return tbl.reset_index(drop=True)


def permutation_table(model: Any, X: pd.DataFrame, y: np.ndarray,
                      n_repeats: int, seed: int,
                      scoring: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """permutation importance：打亂它，分數掉多少。

    一定要在**評估集**上做。在訓練集上做量到的是「模型記住了多少」，
    不是「這個特徵有多少預測力」。
    """
    from sklearn.inspection import permutation_importance

    r = permutation_importance(model, X, y, n_repeats=n_repeats,
                               random_state=seed, scoring=scoring)
    tbl = pd.DataFrame({
        "特徵": list(X.columns),
        "重要度": np.round(r.importances_mean, 6),
        "標準差": np.round(r.importances_std, 6),
    }).sort_values("重要度", ascending=False)
    tbl.insert(0, "排名", range(1, len(tbl) + 1))
    tbl["結論"] = [f"打亂它，{scoring} 掉 {v:.4f}" if v > 0
                   else f"打亂它反而沒掉分（{v:+.4f}）→ 無預測貢獻或被共線特徵掩護"
                   for v in tbl["重要度"]]
    return tbl.reset_index(drop=True), {"scoring": scoring, "n_repeats": n_repeats}


def tree_importance_table(model: Any, cols: list[str]) -> pd.DataFrame | None:
    """模型內建的 feature_importances_。

    **只當開發期的快速掃描，不進報告**（12 §六 硬規則）。留著它是為了做對照：
    tree importance 對高基數特徵有偏（教材講的是 ID3 的 Information Gain 版本 ——
    用顧客 ID 分裂會讓每個子集合純度 100%、IG 最高，但顧客 ID 對新顧客零預測力，
    §15.10），RF／GBDT 的 gain 與 split count 繼承同一個結構性偏誤。
    它與 SHAP 排序差很多的地方，通常就是高基數欄位。
    """
    imp = getattr(model, "feature_importances_", None)
    if imp is None or len(imp) != len(cols):
        return None
    tbl = pd.DataFrame({"特徵": cols, "tree_importance": np.round(np.asarray(imp, dtype=float), 6)})
    tbl = tbl.sort_values("tree_importance", ascending=False)
    tbl.insert(0, "排名", range(1, len(tbl) + 1))
    tbl["結論"] = "開發期掃描用，不進報告（12 §六）"
    return tbl.reset_index(drop=True)


def pdp_table(model: Any, X: pd.DataFrame, features: list[str],
              grid: int = 10) -> pd.DataFrame | None:
    """降級路徑的逐特徵 PDP（12 §一 環境表指定的 shap 替代方案）。

    PDP 給的是「特徵值變動時，模型平均輸出怎麼變」，補的是 permutation
    importance 沒有的方向資訊。它仍然**不是個體層級解釋** —— 報告要照 12 §一
    註明「無個體層級解釋」。
    """
    try:
        from sklearn.inspection import partial_dependence
    except ImportError:
        return None
    rows = []
    for f in features:
        try:
            pd_res = partial_dependence(model, X, [f], grid_resolution=grid,
                                        kind="average")
        except Exception as exc:  # noqa: BLE001 - PDP 對某些模型／欄位型別會拋錯，不該讓整支腳本停
            rows.append({"特徵": f, "格點": None, "平均預測": None,
                         "結論": f"算不出來：{type(exc).__name__}"})
            continue
        gv = np.asarray(pd_res["grid_values"][0], dtype=float)
        av = np.asarray(pd_res["average"][0], dtype=float)
        for g, a in zip(gv, av):
            rows.append({"特徵": f, "格點": round(float(g), 6),
                         "平均預測": round(float(a), 6),
                         "結論": "PDP 是全體平均，不是個體解釋（12 §一）"})
    return pd.DataFrame(rows) if rows else None


def gate_dominance(imp_tbl: pd.DataFrame, value_col: str,
                   source: str) -> dict[str, Any]:
    """單一特徵獨大 → 先懷疑洩漏，不要先高興（12 §六 警語表第二列）。"""
    print(f"\n⑧ 單一特徵獨大檢查（{source}；門檻 佔比 > {SHAP_DOMINANCE_SHARE:.0%}）")
    v = imp_tbl[value_col].to_numpy(dtype=float)
    v = np.where(np.isfinite(v), v, 0.0)
    pos = np.clip(v, 0, None)          # permutation 可能出現負值，負的不算貢獻
    total = float(pos.sum())
    res: dict[str, Any] = {"來源": source, "門檻": SHAP_DOMINANCE_SHARE}
    if total <= 0:
        warn("所有特徵的重要度都 ≤ 0，算不出佔比",
             "模型對這批資料沒有可量測的預測貢獻。先確認評估集與訓練集的欄位一致，"
             "再回 12 §九「訊號太弱」那一列")
        res.update({"最大佔比": None, "結果": "warning"})
        return res
    share = float(pos.max() / total)
    top_feat = str(imp_tbl.iloc[int(np.argmax(pos))]["特徵"])
    res.update({"最大佔比": round(share, 4), "獨大特徵": top_feat})
    detail(f"最大貢獻：{top_feat} 佔 {share:.1%}")
    if share > SHAP_DOMINANCE_SHARE:
        warn(f"{top_feat} 一個特徵就佔了 {share:.1%} 的歸因（門檻 {SHAP_DOMINANCE_SHARE:.0%}）",
             "12 §六：兩件事都要查，查完沒問題才寫進報告。"
             "① m_try／max_features 是不是設太大（太大時所有樹都選同一個強特徵）；"
             "② 這個變數是不是洩漏（教材原例：用「已成交金額」預測「是否成交」；"
             "12 §七 的『標籤衍生／事後欄位』那一類）。"
             "另一個徵狀對照：加入顧客層彙總特徵後 AUC 跳升 0.05 以上時先懷疑切分（12 §二）")
        res["結果"] = "warning"
    else:
        ok(f"沒有單一特徵獨大（最大 {share:.1%} ≤ {SHAP_DOMINANCE_SHARE:.0%}）")
        res["結果"] = "pass"
    return res


def gate_rank_gap(shap_tbl: pd.DataFrame | None, perm_tbl: pd.DataFrame,
                  vif_tbl: pd.DataFrame,
                  tree_tbl: pd.DataFrame | None) -> tuple[dict[str, Any], pd.DataFrame]:
    """SHAP 與 permutation 的排名落差 → 查共線（12 §六 對照表）。"""
    print(f"\n⑨ 三法排名對照（排名落差 ≥ {RANK_GAP_ALERT} 名就要查共線）")
    merged = perm_tbl[["特徵", "排名", "重要度"]].rename(
        columns={"排名": "permutation排名", "重要度": "permutation重要度"})
    if shap_tbl is not None:
        merged = merged.merge(
            shap_tbl[["特徵", "排名", "mean|SHAP|"]].rename(
                columns={"排名": "SHAP排名"}), on="特徵", how="outer")
    if tree_tbl is not None:
        merged = merged.merge(
            tree_tbl[["特徵", "排名", "tree_importance"]].rename(
                columns={"排名": "tree排名"}), on="特徵", how="outer")
    merged = merged.merge(vif_tbl[["特徵", "VIF"]], on="特徵", how="left")

    res: dict[str, Any] = {}
    if shap_tbl is None:
        merged["結論"] = "無 SHAP（已降級），只能看 permutation"
        info("沒有 SHAP 可對照（已降級）—— 排名落差這道檢查這次沒有驗到")
        res["結果"] = "warning"
        res["說明"] = "已降級，無 SHAP 排名可對照"
        return res, merged

    merged["排名落差"] = (merged["SHAP排名"] - merged["permutation排名"]).abs()
    rho = spearman(merged["SHAP排名"].to_numpy(dtype=float),
                   merged["permutation排名"].to_numpy(dtype=float))
    res["排名Spearman"] = round(rho, 4) if np.isfinite(rho) else None
    detail(f"SHAP 與 permutation 的排名 Spearman ρ = {rho:.3f}")

    topk = 5
    focus = merged[(merged["SHAP排名"] <= topk) | (merged["permutation排名"] <= topk)]
    bad = focus[focus["排名落差"] >= RANK_GAP_ALERT]
    merged["結論"] = [
        (f"排名落差 {int(g)} 名 ≥ {RANK_GAP_ALERT}，查共線" if np.isfinite(g) and g >= RANK_GAP_ALERT
         else "兩法排序一致") for g in merged["排名落差"]
    ]
    res["落差超標特徵"] = [str(x) for x in bad["特徵"].tolist()]
    if len(bad):
        for _, r in bad.iterrows():
            v = "—" if pd.isna(r.get("VIF")) else f"{r['VIF']:.2f}"
            detail(f"{r['特徵']}：SHAP 第 {int(r['SHAP排名'])} 名 vs "
                   f"permutation 第 {int(r['permutation排名'])} 名（VIF = {v}）")
        warn(f"{len(bad)} 個 Top-{topk} 特徵的兩法排名差 ≥ {RANK_GAP_ALERT} 名："
             + "、".join(str(x) for x in bad["特徵"]),
             "12 §六：兩者排序差很多時要查共線。permutation 的定義是「打亂它掉多少分」，"
             "相關特徵會互相掩護；SHAP 則把貢獻攤在相關特徵之間。"
             "先看上面那張 VIF 表，把這幾個變數當一組談，"
             "或照 05 §1.4 的階梯合成成單一指標再重跑")
        res["結果"] = "warning"
    else:
        ok(f"Top-{topk} 特徵的兩法排名落差都 < {RANK_GAP_ALERT} 名")
        res["結果"] = "pass"

    if tree_tbl is not None:
        info("tree importance 已算出但**不進報告**（12 §六 硬規則）—— "
             "它對高基數特徵有偏（§15.10 的 ID3 Information Gain 版本）。"
             "它與 SHAP 排名差很多的欄位，先看是不是高基數類別欄")
    return res, merged


def individual_contributions(vals: np.ndarray, X: pd.DataFrame,
                             ids: pd.Series | None, score: np.ndarray,
                             top_n: int = 3) -> pd.DataFrame:
    """每列取 |SHAP| 最大的前 N 個特徵 —— 這是 SHAP 相對 importance 的真正價值。

    12 §六 的用法：把這幾條直接寫成行銷話術的素材。措辭仍然是「在本模型中，
    X=96 使這位顧客的分數上升 0.21」，不是「因為 X 所以他會流失」。
    """
    rows = []
    order = np.argsort(-np.abs(vals), axis=1, kind="stable")[:, :top_n]
    cols = list(X.columns)
    xv = X.to_numpy()
    for i in range(vals.shape[0]):
        for rank, j in enumerate(order[i], start=1):
            rows.append({
                "列索引": int(i),
                "id": (_py(ids.iloc[i]) if ids is not None else None),
                "分數": round(float(score[i]), 6),
                "貢獻排名": rank,
                "特徵": cols[int(j)],
                "特徵值": _py(xv[i, int(j)]),
                "SHAP貢獻": round(float(vals[i, int(j)]), 6),
            })
    out = pd.DataFrame(rows)
    out["結論"] = ["在本模型中，該值使這位顧客的分數上升 "
                   f"{v:.4f}" if v >= 0 else
                   f"在本模型中，該值使這位顧客的分數下降 {abs(v):.4f}"
                   for v in out["SHAP貢獻"]]
    return out


# ══════════════════════════════════════════════════════════════
#  固定警語 —— 每次都印，因為每次都有人忘記
# ══════════════════════════════════════════════════════════════
INTERPRETATION_NOTES: list[str] = [
    "SHAP 是「模型怎麼想」，不是「世界怎麼運作」。它是模型輸出的加法分解，"
    "忠實反映的是這個模型的思路，不是資料的生成機制。"
    "✗「R 驅動流失，把 R 降下來就能降低流失」／"
    "✓「在本模型中，R=96 天使這位顧客的流失分數上升 0.21」。"
    "（12 §六 警語表；00 §1.5 措辭白名單：預測級禁用任何 intervention 語句；18-G6）",

    "要主張「改變 X 會改變 Y」只有一條路：M12 的實驗或準實驗設計。"
    "SHAP 排序再乾淨也不能升級證據等級 —— 模型只被訓練來排序，沒有被訓練來回答介入。",

    "特徵重要度在共線變數之間會被稀釋。permutation importance 的兩個高相關特徵"
    "會互相掩護（各自打亂都不掉分，兩個都排到後面）；SHAP 的 TreeSHAP 路徑相依"
    "則把貢獻攤在相關特徵之間。看到重要度低，先確認不是被隔壁的特徵吃掉了。"
    "（12 §六 對照表；VIF 門檻見 05 §1.4）",

    "tree importance（feature_importances_）不進報告。它對高基數特徵有偏 —— "
    "一個有 200 個水準的「來源活動代碼」會得到比二元的「是否曾退貨」更多的分裂機會，"
    "因此累積更多 gain，即使後者才是真正的訊號。（12 §六；教材 §15.10 的 ID3 版本）",

    "單一特徵獨大時先懷疑洩漏，不要先高興：① m_try 設太大？② 那個變數是不是"
    "事後才有值的欄位？查完沒問題才寫進報告。（12 §六 警語表第二列、§28.3 診斷順序、18-G4）",

    "Lift／Gain 是名單型交付的主指標，AUC 是配角。但兩者都只描述排序，"
    "不描述刻度 —— 要把分數乘上金額算期望營收，必須先過 12 §三 的機率校準。"
    "（12 §五 Step 4：沒校準不准算）",
]


def print_notes() -> None:
    print("\n" + "-" * 72)
    print("解讀警語（每次都印；這幾條是報告最常滑掉的地方）")
    print("-" * 72)
    for i, note in enumerate(INTERPRETATION_NOTES, start=1):
        print(f"  {i}. {note}")


# ══════════════════════════════════════════════════════════════
#  載入
# ══════════════════════════════════════════════════════════════
def load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"找不到資料表：{path}\n"
            f"  這支腳本吃的是「評估集 + 標籤」的表（split_time.py 的 test 那一份）。"
            f"  用 --data 指定路徑。")
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() in (".csv", ".txt"):
        return pd.read_csv(path)
    raise ValueError(f"不認得的副檔名：{path.suffix}（吃 .parquet／.csv）")


def load_model(path: Path) -> Any:
    """讀已訓練的模型。

    joblib 與 pickle 都會執行檔案裡的位元組碼，所以只讀自己專案 模型輸出/
    底下、自己跑出來的檔 —— 不要拿別人寄來的 .pkl 直接餵進來。
    """
    if not path.exists():
        raise FileNotFoundError(
            f"找不到模型檔：{path}\n"
            f"  用 --model 指定，或改用 --score-col 直接給已算好的分數欄"
            f"（那條路徑只做 Lift/Gain，沒有 SHAP）。")
    if path.suffix.lower() in (".pkl", ".pickle"):
        import pickle
        with open(path, "rb") as f:
            return pickle.load(f)
    try:
        import joblib
    except ImportError as exc:
        raise ValueError(
            f"要讀 {path.name} 需要 joblib（sklearn 的相依套件）。"
            f"pip install joblib，或把模型存成 .pkl") from exc
    return joblib.load(path)


def resolve_features(df: pd.DataFrame, model: Any, args: Any,
                     drop: set[str]) -> list[str]:
    """決定特徵欄與順序。

    順序是這裡的重點：sklearn 的模型吃的是位置，不是欄名。欄序一動，
    「年齡」的值會被當成「金額」餵進去，模型照樣吐得出機率，SHAP 照樣畫得出圖，
    只是每個結論都對到別的變數。所以有 feature_names_in_ 就以它為準。
    """
    if args.feature_cols:
        cols = [c.strip() for c in args.feature_cols.split(",") if c.strip()]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"--feature-cols 指定的欄位不在資料表裡：{'、'.join(missing)}")
        return cols

    names = getattr(model, "feature_names_in_", None) if model is not None else None
    if names is not None:
        cols = [str(c) for c in names]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"模型訓練時用的特徵在資料表裡找不到：{'、'.join(missing)}\n"
                f"  模型的 feature_names_in_ = {cols}\n"
                f"  資料表的欄位 = {list(df.columns)}\n"
                f"  這通常是評估集用了不同版本的特徵表。不要改欄名硬湊 —— "
                f"回去確認兩邊是不是同一次 build_features 的產物。")
        return cols

    return [c for c in df.columns
            if c not in drop and pd.api.types.is_numeric_dtype(df[c])]


def pick_id_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        low = str(c).lower()
        if low in ("客戶編號", "客戶id", "customer_id", "cust_id", "id"):
            return c
    return None


def resolve_target(df: pd.DataFrame, args: Any) -> np.ndarray:
    if args.target not in df.columns:
        raise ValueError(
            f"資料表裡沒有標籤欄 {args.target!r}。現有欄位：{list(df.columns)}\n"
            f"  用 --target 指定。")
    raw = df[args.target]
    uniq = pd.unique(raw.dropna())
    if len(uniq) > 2:
        raise ValueError(
            f"標籤欄 {args.target!r} 有 {len(uniq)} 種值，這支腳本只處理二元標籤。\n"
            f"  多類別的評估請照 12 §五：逐類 P/R/F1 + macro & micro 並報。")
    pos = args.positive_label
    if pos is None:
        # 沒指定就用「1／True」；都沒有才用排序後較大的那個值
        if raw.isin([1, True]).any():
            pos_val: Any = 1
        else:
            pos_val = sorted(uniq, key=str)[-1]
    else:
        pos_val = pos
        if not raw.astype(str).eq(str(pos_val)).any():
            raise ValueError(
                f"--positive-label {pos_val!r} 在標籤欄 {args.target!r} 裡找不到。"
                f"現有的值：{list(uniq)}")
    y = raw.astype(str).eq(str(pos_val)).to_numpy().astype(float)
    if raw.isna().any():
        raise ValueError(
            f"標籤欄 {args.target!r} 有 {int(raw.isna().sum())} 個缺值。"
            f"缺標籤的列不是「負類」—— 先決定它們該被排除還是補標，不要讓它們默默變成 0。")
    print(f"  · 正類 = {args.target} == {pos_val!r}")
    return y


def positive_class_index(model: Any) -> int:
    """predict_proba 的哪一欄是正類。

    sklearn 的 classes_ 是排序過的，二元 0/1 時正類在第 1 欄；但 classes_ 是
    ['否','是'] 這種字串時就不一定。取錯欄會讓整張 Lift 表反過來（top decile
    lift 變成 0.1 那種），所以照 classes_ 找，不要寫死 1。
    """
    classes = getattr(model, "classes_", None)
    if classes is None:
        return 1
    cl = list(classes)
    for cand in (1, True, "1", "是", "Y", "yes"):
        if cand in cl:
            return cl.index(cand)
    return len(cl) - 1


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)

    data_path = args.data or (p.models / "test_matrix.parquet")
    df = load_table(Path(data_path))

    print("=" * 72)
    print("行銷數據分析 Skill — 模型解釋：SHAP／特徵重要度／Lift-Gain（12 §五、§六、§九）")
    print(f"專案：{args.project}｜資料表：{Path(data_path).name}"
          f"（{len(df):,} 列 × {df.shape[1]} 欄）")
    print("=" * 72)

    y = resolve_target(df, args)

    model = None
    if args.score_col:
        if args.score_col not in df.columns:
            raise ValueError(f"資料表裡沒有 --score-col 指定的欄位：{args.score_col}")
        score = df[args.score_col].to_numpy(dtype=float)
        score_src = f"資料表的 {args.score_col} 欄"
    else:
        model_path = args.model or (p.models / "model.joblib")
        model = load_model(Path(model_path))
        drop = {args.target, args.score_col, args.baseline_col, pick_id_col(df)}
        cols = resolve_features(df, model, args, {c for c in drop if c})
        Xall = df[cols]
        pos_idx = positive_class_index(model)
        if hasattr(model, "predict_proba"):
            score = np.asarray(model.predict_proba(Xall))[:, pos_idx]
            score_src = f"{Path(model_path).name} 的 predict_proba[:, {pos_idx}]"
        elif hasattr(model, "decision_function"):
            score = np.asarray(model.decision_function(Xall), dtype=float)
            score_src = f"{Path(model_path).name} 的 decision_function"
            warn("模型沒有 predict_proba，只有 decision_function",
                 "這個分數只能排序，不是機率。Lift/Gain 照算（它只吃排序），"
                 "但**不准拿去乘金額算期望營收**（12 §三、§五 Step 4）")
        else:
            raise ValueError(
                f"模型 {type(model).__name__} 既沒有 predict_proba 也沒有 "
                f"decision_function，產不出分數。")

    if np.isnan(score).any():
        raise ValueError(
            f"分數有 {int(np.isnan(score).sum())} 個缺值。"
            f"缺分數的列不能當成最低分排到最後 —— 先確認特徵是不是有缺值，"
            f"或把這些列移到 隔離區/ 並在報告交代（18-E22）。")
    print(f"  · 分數來源：{score_src}")

    baseline = None
    if args.baseline_col:
        if args.baseline_col not in df.columns:
            raise ValueError(f"資料表裡沒有 --baseline-col 指定的欄位：{args.baseline_col}")
        baseline = df[args.baseline_col].to_numpy(dtype=float)

    results: dict[str, Any] = {}
    results["標籤"] = gate_label(y)
    if results["標籤"].get("結果") == "error":
        # 標籤退化時後面每一格都是假的，不要硬算下去產出一張看起來正常的表
        print("\n" + "=" * 72)
        print("結果：⛔ 標籤退化 → 後續全部不跑。")
        return EX_ERROR

    results["並列"] = gate_ties(score, args.bins)
    base_rate = float(y.sum() / len(y))
    lift_tbl = lift_gain_table(y, score, args.bins)
    results["Lift"] = gate_lift(lift_tbl, y, score)
    curve = gain_curve(y, score, args.curve_step)

    print("\n" + "-" * 72)
    print("可直接貼進報告的三句話（12 §五）：")
    print("-" * 72)
    sentences = report_sentences(lift_tbl, base_rate)
    print(sentences)

    results["baseline"] = gate_baseline(y, score, baseline,
                                        args.baseline_col or "—", args.bins)
    results["評估切分"] = gate_eval_split(args.eval_split)

    shap_tbl: pd.DataFrame | None = None
    perm_tbl: pd.DataFrame | None = None
    vif_tbl: pd.DataFrame | None = None
    tree_tbl: pd.DataFrame | None = None
    cmp_tbl: pd.DataFrame | None = None
    contrib: pd.DataFrame | None = None
    pdp: pd.DataFrame | None = None
    shap_meta: dict[str, Any] = {}

    if model is None:
        print("\n⑥–⑨ 特徵重要度與 SHAP —— 本次只有分數欄，沒有模型，全部未跑")
        info("要跑 SHAP 與重要度，給 --model（模型檔）與特徵欄")
        results["解釋"] = {"結果": "warning", "說明": "只有分數欄，未做任何特徵層級解釋"}
        warn("這次沒有做特徵層級解釋（只有 Lift/Gain）",
             "報告的 SHAP summary／dependence 兩張圖沒有來源（ref 19 §1.7 的八張圖缺兩張）。"
             "把模型檔放進 模型輸出/ 再跑一次")
    else:
        X = df[cols]
        n_nan = int(X.isna().any(axis=1).sum())
        if n_nan:
            warn(f"特徵表有 {n_nan} 列含缺值",
                 "permutation importance 與 PDP 對 NaN 的處理各家不同，"
                 "SHAP 的 base value 也會跟著漂。先確認模型本身吃得下 NaN"
                 "（HistGradientBoosting 可以，RandomForest 不行）")

        cv_res, vif_tbl = gate_collinearity(X.select_dtypes(include=[np.number]))
        results["共線性"] = cv_res

        # SHAP 或降級
        print("\n⑦ SHAP（12 §六：報告用 SHAP，不用 tree importance 條形圖）")
        Xs, idx_s = X, np.arange(len(X))
        if len(X) > args.sample:
            rng = np.random.default_rng(args.seed)
            idx_s = np.sort(rng.choice(len(X), size=args.sample, replace=False))
            Xs = X.iloc[idx_s]
            info(f"列數 {len(X):,} > --sample {args.sample:,}，SHAP 只在抽樣的 "
                 f"{args.sample:,} 列上算（seed={args.seed}）。"
                 f"mean|SHAP| 因此是估計值，報告要寫明抽樣列數")

        have_shap, shap_ver = shap_available()
        if args.no_shap:
            have_shap, shap_ver = False, "--no-shap（使用者強制降級）"
        if have_shap:
            try:
                shap_tbl, sv, shap_meta = shap_importance(
                    model, Xs, positive_class_index(model),
                    np.asarray(model.predict_proba(Xs))[:, positive_class_index(model)]
                    if hasattr(model, "predict_proba") else score[idx_s])
                shap_meta["版本"] = shap_ver
                ok(f"TreeExplainer 完成（shap {shap_ver}，{len(Xs):,} 列 × {X.shape[1]} 欄）")
                aerr = shap_meta.get("加法性最大誤差")
                if aerr is None or not np.isfinite(aerr) or aerr > 1e-3:
                    err(f"SHAP 加法性驗算不通過（base + Σshap 與模型輸出最大差 "
                        f"{aerr if aerr is not None else float('nan'):.3g}）",
                        "多半是類別維度取錯（sklearn 二元分類器的 values 是 "
                        "(n, d, 2)，要取正類那一片）或 explainer 的 model_output 與"
                        "這裡的假設不同。在修好之前，SHAP 的方向可能整個相反，不要用")
                    results.setdefault("SHAP", {})["加法性"] = "不通過"
                else:
                    ok(f"加法性驗算通過：base + Σshap 與 predict_proba 最大差 {aerr:.3g}"
                       f"（雙路徑驗算，00 §1.3）")
                for _, r in shap_tbl.head(args.top_n).iterrows():
                    detail(f"{r['排名']:>2}. {r['特徵']}｜mean|SHAP| {r['mean|SHAP|']:.6f}"
                           f"（{r['佔比']:.1%}）｜{r['方向']}")
                ids = df[pick_id_col(df)] if pick_id_col(df) else None
                contrib = individual_contributions(
                    sv, Xs, ids.iloc[idx_s] if ids is not None else None,
                    score[idx_s], top_n=3)
                results.setdefault("SHAP", {}).update(
                    {"結果": "pass", "來源": "shap.TreeExplainer", "版本": shap_ver})
            except Exception as exc:  # noqa: BLE001 - 非樹模型／版本不合都會在這裡拋
                shap_tbl = None
                warn(f"shap 裝得起來但 TreeExplainer 跑不動：{type(exc).__name__}: {exc}",
                     "常見原因：模型不是樹（CalibratedClassifierCV 包過的、"
                     "LogisticRegression）。校準後的模型要對 base 模型算 SHAP，"
                     "並在報告註明「解釋的是未校準的分數」。"
                     "本次已降級為 permutation importance，報告要註明「無個體層級解釋」（12 §一）")
                results.setdefault("SHAP", {}).update(
                    {"結果": "warning", "來源": "降級", "原因": f"{type(exc).__name__}: {exc}"})
        else:
            warn(f"沒有可用的 shap（{shap_ver}）→ **已降級為 permutation importance**",
                 "12 §一 環境表指定的替代方案：sklearn.inspection.permutation_importance "
                 "+ 逐特徵 PDP，並在報告註明「無個體層級解釋」。"
                 "ref 19 §1.7 的 SHAP summary 與 SHAP dependence 兩張圖這次交不出來，"
                 "要在《進度與異狀.md》寫明理由。要修：pip install shap")
            results.setdefault("SHAP", {}).update(
                {"結果": "warning", "來源": "降級", "原因": shap_ver})

        # permutation importance（不論有沒有 SHAP 都跑 —— 它是 SHAP 的對照組）
        print("\n⑦-b permutation importance（12 §六：SHAP 的對照組）")
        scoring = "roc_auc" if hasattr(model, "predict_proba") else "accuracy"
        if scoring == "accuracy":
            warn("模型沒有 predict_proba，permutation importance 只能用 accuracy 當分數",
                 "12 §五：類別不平衡下禁用 Accuracy 當主指標。這裡的 accuracy 只用來"
                 "排特徵順序，**不可寫進報告當模型表現**")
        perm_tbl, perm_meta = permutation_table(model, X, y, args.n_repeats,
                                                args.seed, scoring)
        info(f"在評估集上算（n_repeats={args.n_repeats}、scoring={scoring}）—— "
             f"在訓練集上算量到的是模型記住多少，不是預測力")
        for _, r in perm_tbl.head(args.top_n).iterrows():
            detail(f"{r['排名']:>2}. {r['特徵']}｜{r['重要度']:+.6f}"
                   f"（±{r['標準差']:.6f}）")

        tree_tbl = tree_importance_table(model, list(X.columns))

        # 降級路徑補 PDP（12 §一）
        if shap_tbl is None:
            print("\n⑦-c 逐特徵 PDP（降級路徑的方向資訊，12 §一）")
            feats = [str(c) for c in perm_tbl["特徵"].head(min(5, args.top_n))]
            pdp = pdp_table(model, X, feats)
            if pdp is None or pdp.empty:
                warn("PDP 也算不出來", "降級只剩排序，沒有方向。報告要寫明這一點")
            else:
                ok(f"PDP 已算出前 {len(feats)} 名特徵（{'、'.join(feats)}）")
                info("PDP 是全體平均的效果，仍然不是個體層級解釋（12 §一）")

        dom_src = ("SHAP", "mean|SHAP|", shap_tbl) if shap_tbl is not None \
            else ("permutation（已降級）", "重要度", perm_tbl)
        results["獨大"] = gate_dominance(dom_src[2], dom_src[1], dom_src[0])
        rg, cmp_tbl = gate_rank_gap(shap_tbl, perm_tbl,
                                    vif_tbl if vif_tbl is not None
                                    else pd.DataFrame({"特徵": list(X.columns),
                                                       "VIF": [None] * X.shape[1]}),
                                    tree_tbl)
        results["排名對照"] = rg

        if contrib is not None and len(contrib):
            print("\n⑩ 個體層級解釋範例（12 §六：這是 SHAP 相對 importance 的真正價值）")
            best = int(np.argmax(score[idx_s]))
            ex = contrib[contrib["列索引"] == best]
            who = ex["id"].iloc[0] if len(ex) and ex["id"].iloc[0] is not None else f"第 {best} 列"
            detail(f"分數最高的個體（{who}，分數 {score[idx_s][best]:.4f}）：")
            for _, r in ex.iterrows():
                detail(f"    {r['特徵']} = {r['特徵值']}  → {r['SHAP貢獻']:+.4f}")
            detail("話術措辭：「在本模型中，上列數值使這位顧客的分數上升／下降 X」——"
                   "不要寫成「因為 A 所以他會流失」")

    print_notes()

    # ── 收斂 ──
    print("\n" + "=" * 72)
    n_err, n_warn = len(_errors), len(_warnings)
    print(f"error {n_err}、warning {n_warn}")
    if n_err:
        print("結果：⛔ 有 error → 這份解釋不可進報告，先修上游。")
    elif n_warn:
        print("結果：⚠ 可往下，但報告要逐條回應上面的警告。")
    else:
        print("結果：✅ 全部通過。")
    print("      提醒：ref 19 §1.7 的 M9 八張圖裡，本腳本負責 Lift/Gain 與 SHAP "
          "兩類圖的**資料**；畫圖時直接讀這裡寫出的 CSV，不要重算（19 §6.2）。")

    if not args.no_write:
        d = p.tables / "預測模型"
        d.mkdir(parents=True, exist_ok=True)
        lift_tbl.to_csv(d / "表11.2_十分位Lift表.csv", index=False, encoding="utf-8-sig")
        curve.to_csv(d / "lift_gain_曲線資料.csv", index=False, encoding="utf-8-sig")
        if shap_tbl is not None:
            shap_tbl.to_csv(d / "SHAP_特徵重要度.csv", index=False, encoding="utf-8-sig")
        if perm_tbl is not None:
            perm_tbl.to_csv(d / "permutation_特徵重要度.csv", index=False,
                            encoding="utf-8-sig")
        if vif_tbl is not None:
            vif_tbl.to_csv(d / "共線性_VIF.csv", index=False, encoding="utf-8-sig")
        if cmp_tbl is not None:
            cmp_tbl.to_csv(d / "特徵重要度_三法對照.csv", index=False,
                           encoding="utf-8-sig")
        if tree_tbl is not None:
            # 單獨落一份是為了讓 verify_outputs 能檢查「報告有沒有偷用它」——
            # 12 §六 的硬規則是 tree importance 不進報告（19 §1.7 同）
            tree_tbl.to_csv(d / "tree_importance_不進報告.csv", index=False,
                            encoding="utf-8-sig")
        if pdp is not None and len(pdp):
            pdp.to_csv(d / "PDP_逐特徵.csv", index=False, encoding="utf-8-sig")
        print(f"\n✓ 統計表已寫入：{d}")

        p.models.mkdir(parents=True, exist_ok=True)
        if contrib is not None and len(contrib):
            cp = p.models / "shap_個體貢獻_top3.parquet"
            try:
                contrib.to_parquet(cp, index=False)
            except (ImportError, ValueError):
                cp = p.models / "shap_個體貢獻_top3.csv"
                contrib.to_csv(cp, index=False, encoding="utf-8-sig")
            print(f"✓ 個體層級貢獻：{cp}")

        jp = p.models / "explain_model.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "data": str(data_path),
            "model": str(args.model) if args.model else None,
            "n_rows": int(len(df)),
            "母體回應率": round(base_rate, 6),
            "分數來源": score_src,
            "bins": int(args.bins),
            "gates": results,
            "十分位Lift表": lift_tbl.to_dict("records"),
            "SHAP重要度": (shap_tbl.to_dict("records") if shap_tbl is not None else None),
            "permutation重要度": (perm_tbl.to_dict("records") if perm_tbl is not None else None),
            "tree_importance": (tree_tbl.to_dict("records") if tree_tbl is not None else None),
            "共線性VIF": (vif_tbl.to_dict("records") if vif_tbl is not None else None),
            "shap_meta": shap_meta,
            "報告三句": sentences,
            "解讀警語": INTERPRETATION_NOTES,
            "errors": _errors,
            "warnings": _warnings,
        }, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        print(f"✓ 機器可讀結果：{jp}")

    if n_err:
        return EX_ERROR
    return EX_WARN if n_warn else EX_OK


# ══════════════════════════════════════════════════════════════
#  自我測試
# ══════════════════════════════════════════════════════════════
def _reference_lift_case() -> tuple[np.ndarray, np.ndarray]:
    """重建 12 §五 表 11.2 的示意資料：10,000 人、400 位回應者。

    逐十分位的回應數 132/88/60/40/28/20/12/8/8/4 —— 直接拿 reference 印出來的
    數字當測試預期值。這樣測的不只是「程式有沒有跑」，是「我算出來的 Lift
    與 Gain 跟 reference 那張表逐格相同」。
    """
    resp = [132, 88, 60, 40, 28, 20, 12, 8, 8, 4]
    y, s = [], []
    for i, r in enumerate(resp):
        y.extend([1.0] * r + [0.0] * (1000 - r))
        s.extend([float(10 - i)] * 1000)
    return np.asarray(y), np.asarray(s)


def _selftest() -> int:  # noqa: C901 - 自我測試就是一長串斷言，拆開反而難讀
    print("=" * 72)
    print("explain_model.py 自我測試")
    print("=" * 72)
    rng = np.random.default_rng(20260728)
    failed: list[str] = []
    ran: list[str] = []

    def check(name: str, cond: bool, got: str = "") -> None:
        ran.append(name)
        print(("  ✓ " if cond else "  ✗ ") + name + (f"（{got}）" if got else ""))
        if not cond:
            failed.append(name)

    # ── ① Lift/Gain 對得上 reference 表 11.2 ──────────────────
    y_ref, s_ref = _reference_lift_case()
    t = lift_gain_table(y_ref, s_ref, 10)
    check("十分位 Lift 表重現 12 §五 的 top decile lift = 3.30",
          abs(t["Lift"].iloc[0] - 3.30) < 1e-9, f"Lift={t['Lift'].iloc[0]}")
    check("D3 累積 Gain = 70.0%", abs(t["累積Gain%"].iloc[2] - 70.0) < 1e-9,
          f"{t['累積Gain%'].iloc[2]}%")
    check("D4 的 Lift = 1.00（reference 那格）",
          abs(t["Lift"].iloc[3] - 1.00) < 1e-9, f"Lift={t['Lift'].iloc[3]}")
    check("D10 累積 Gain = 100%，累積回應數 = 400",
          t["累積Gain%"].iloc[-1] == 100.0 and t["累積回應數"].iloc[-1] == 400)
    check("逐箱回應數與 reference 逐格相同",
          list(t["回應數"]) == [132, 88, 60, 40, 28, 20, 12, 8, 8, 4],
          str(list(t["回應數"])))

    # Gain 曲線與十分位表必須互相對得上（圖表同源，19 §6.2）
    c = gain_curve(y_ref, s_ref, 10.0)
    check("Gain 曲線在 30% 處與十分位表的 D3 累積 Gain 一致",
          abs(c.loc[c["名單比例%"] == 30.0, "累積Gain%"].iloc[0] - 70.0) < 1e-9,
          f"{c.loc[c['名單比例%'] == 30.0, '累積Gain%'].iloc[0]}")

    # ── ② 無預測力的分數：Lift ≈ 1，且不該被說成有效 ─────────
    y_rand = (rng.random(5000) < 0.04).astype(float)
    s_rand = rng.random(5000)
    t_rand = lift_gain_table(y_rand, s_rand, 10)
    tdl_rand = t_rand["Lift"].iloc[0]
    check("隨機分數的 top decile lift 落在 1 附近", 0.6 <= tdl_rand <= 1.6,
          f"lift={tdl_rand}")
    before = len(_warnings)
    gate_lift(t_rand, y_rand, s_rand)
    check("隨機分數會觸發低 lift 警告", len(_warnings) > before,
          f"lift={tdl_rand} < {TOP_DECILE_LIFT_ALERT}")
    before = len(_warnings)
    gate_lift(t, y_ref, s_ref)
    check("強模型不會被誤報低 lift", len(_warnings) == before,
          f"lift={t['Lift'].iloc[0]}")

    # ── ③ 分箱人數不足要標 N/A，不可硬給數字 ─────────────────
    y_small = np.concatenate([np.ones(5), np.zeros(95)])
    s_small = np.linspace(1, 0, 100)
    t_small = lift_gain_table(y_small, s_small, 10)   # 每箱 10 人 < 30
    check("每箱 n<30 時該箱回應率與 Lift 標 N/A",
          all(v is None for v in t_small["Lift"]),
          f"{t_small['結論'].iloc[0]}")
    check("N/A 的箱仍算得出累積 Gain（累積數比逐箱率穩定）",
          t_small["累積Gain%"].iloc[-1] == 100.0)

    # ── ④ AUC：自算 vs sklearn（雙路徑）──────────────────────
    y_a = (rng.random(800) < 0.3).astype(float)
    s_a = y_a * 0.6 + rng.random(800)
    mine = auc_score(y_a, s_a)
    try:
        from sklearn.metrics import roc_auc_score
        theirs = float(roc_auc_score(y_a, s_a))
        check("AUC 與 sklearn 一致", abs(mine - theirs) < 1e-12,
              f"自算 {mine:.6f} vs sklearn {theirs:.6f}")
        s_tie = np.round(s_a, 1)                      # 製造大量並列
        check("並列分數下 AUC 仍與 sklearn 一致（平均秩）",
              abs(auc_score(y_a, s_tie) - float(roc_auc_score(y_a, s_tie))) < 1e-12,
              f"自算 {auc_score(y_a, s_tie):.6f}")
    except ImportError:
        check("AUC 與 sklearn 一致", False, "sklearn 缺席，這項驗不到")
    check("全部同分時 AUC = 0.5", abs(auc_score(y_a, np.ones(800)) - 0.5) < 1e-12)

    # ── ⑤ 標籤退化與並列 ────────────────────────────────────
    r = gate_label(np.ones(500))
    check("全部都是正類 → error", r["結果"] == "error")
    r = gate_label(np.concatenate([np.ones(50), np.zeros(950)]))
    check("正類 50 筆 < 200 → warning", r["結果"] == "warning", f"正類 {r['正類數']}")
    r = gate_label(np.concatenate([np.ones(400), np.zeros(9600)]))
    check("正類 400 筆 ≥ 200 且雙類別 → pass", r["結果"] == "pass")

    r = gate_ties(np.ones(1000), 10)
    check("分數全部相同 → 切不出十分位，error", r["結果"] == "error",
          f"相異分數 {r['相異分數數']}")
    r = gate_ties(np.concatenate([np.zeros(300), rng.random(700)]), 10)
    check("單一分數值佔 30% → warning", r["結果"] == "warning",
          f"最大並列組佔比 {r['最大並列組佔比']:.0%}")
    r = gate_ties(rng.random(1000), 10)
    check("分數各不相同 → 不誤報並列", r["結果"] == "pass")

    # ── ⑥ baseline 對照（12 §九 的 0.03 AUC 門檻）────────────
    y_b = (rng.random(4000) < 0.1).astype(float)
    strong = y_b * 1.5 + rng.normal(0, 1, 4000)
    weak = y_b * 1.44 + rng.normal(0, 1, 4000)     # 幾乎一樣強
    r = gate_baseline(y_b, strong, weak, "近似 baseline", 10)
    check("提升 < 0.03 AUC → 觸發「不建議上線」",
          r["結果"] == "warning" and r["AUC提升"] < AUC_GAIN_MIN,
          f"ΔAUC={r['AUC提升']}")
    dumb = rng.random(4000)
    r = gate_baseline(y_b, strong, dumb, "亂數 baseline", 10)
    check("提升 ≥ 0.03 AUC → 不誤報",
          r["結果"] == "pass" and r["AUC提升"] >= AUC_GAIN_MIN,
          f"ΔAUC={r['AUC提升']}")
    r = gate_baseline(y_b, strong, None, "—", 10)
    check("沒給 baseline → 一定要警告（沒有對照的模型是裝飾）",
          r["結果"] == "warning")

    # ── ⑦ 共線性：抓得到、也不亂叫 ──────────────────────────
    n = 800
    a = rng.normal(0, 1, n)
    Xc = pd.DataFrame({"a": a, "b": a * 2 + rng.normal(0, 0.05, n),
                       "c": rng.normal(0, 1, n)})
    r, vt = gate_collinearity(Xc)
    check("r≈0.999 的兩欄被判高度共線", r["結果"] == "warning",
          f"最大 VIF={r['最大VIF']}")
    check("獨立欄 c 沒有被誤判",
          vt.loc[vt["特徵"] == "c", "判定"].iloc[0] == "通過")
    Xi = pd.DataFrame(rng.normal(0, 1, (n, 3)), columns=list("xyz"))
    r, _ = gate_collinearity(Xi)
    check("三個獨立欄 → 不誤報共線", r["結果"] == "pass", f"最大 VIF={r['最大VIF']}")
    Xd = pd.DataFrame({"a": a, "a_copy": a, "c": rng.normal(0, 1, n)})
    r, vt = gate_collinearity(Xd)
    check("完全重複欄判成「欄位重複／dummy trap」而不是普通共線",
          r["結果"] == "error"
          and (vt["判定"] == "欄位重複／dummy trap").sum() >= 2,
          "、".join(vt["判定"]))
    Xk = pd.DataFrame({"a": a, "k": np.ones(n)})
    _, vt = gate_collinearity(Xk)
    check("常數欄被點名（12 §七 要求先排除）",
          "常數欄" in list(vt["判定"]))

    # ── ⑧ 單一特徵獨大 ──────────────────────────────────────
    dom = pd.DataFrame({"特徵": ["洩漏欄", "b", "c"], "mean|SHAP|": [0.80, 0.10, 0.10]})
    r = gate_dominance(dom, "mean|SHAP|", "SHAP")
    check("單一特徵佔 80% → 觸發洩漏懷疑", r["結果"] == "warning",
          f"佔比={r['最大佔比']}")
    even = pd.DataFrame({"特徵": ["a", "b", "c"], "mean|SHAP|": [0.4, 0.35, 0.25]})
    r = gate_dominance(even, "mean|SHAP|", "SHAP")
    check("重要度分散時不誤報洩漏", r["結果"] == "pass", f"佔比={r['最大佔比']}")

    # ── ⑨ 排名落差 ──────────────────────────────────────────
    feats = [f"f{i}" for i in range(6)]
    vt = pd.DataFrame({"特徵": feats, "VIF": [1.0] * 6})
    sh = pd.DataFrame({"特徵": feats, "排名": [1, 2, 3, 4, 5, 6],
                       "mean|SHAP|": [6, 5, 4, 3, 2, 1]})
    pm_same = pd.DataFrame({"特徵": feats, "排名": [1, 2, 3, 4, 5, 6],
                            "重要度": [6, 5, 4, 3, 2, 1]})
    r, _ = gate_rank_gap(sh, pm_same, vt, None)
    check("兩法排名一致 → 不誤報共線", r["結果"] == "pass",
          f"ρ={r['排名Spearman']}")
    pm_diff = pd.DataFrame({"特徵": feats, "排名": [5, 6, 3, 4, 1, 2],
                            "重要度": [2, 1, 4, 3, 6, 5]})
    r, cmp_tbl = gate_rank_gap(sh, pm_diff, vt, None)
    check("Top-5 特徵排名差 ≥3 名 → 要求查共線", r["結果"] == "warning",
          f"落差超標：{r['落差超標特徵']}")
    check("對照表帶得出 VIF 欄（要一起看才判得出是不是共線）",
          "VIF" in cmp_tbl.columns)
    r, _ = gate_rank_gap(None, pm_same, vt, None)
    check("沒有 SHAP 時明講「這道檢查沒有驗到」，不報 pass",
          r["結果"] == "warning" and "降級" in r["說明"])

    # ── ⑩ 模型層級：SHAP 與降級路徑 ─────────────────────────
    from sklearn.ensemble import RandomForestClassifier
    n_tr = 1200
    f_strong = rng.normal(0, 1, n_tr)
    f_noise = rng.normal(0, 1, n_tr)
    f_dup = f_strong + rng.normal(0, 0.02, n_tr)      # 與 f_strong 幾乎共線
    prob = 1 / (1 + np.exp(-(1.8 * f_strong - 0.6)))
    y_m = (rng.random(n_tr) < prob).astype(int)
    Xm = pd.DataFrame({"f_strong": f_strong, "f_noise": f_noise, "f_dup": f_dup})
    rf = RandomForestClassifier(n_estimators=60, random_state=0,
                                min_samples_leaf=5).fit(Xm, y_m)
    pos_idx = positive_class_index(rf)
    check("正類欄位索引照 classes_ 找得到", pos_idx == list(rf.classes_).index(1),
          f"pos_idx={pos_idx}、classes_={list(rf.classes_)}")

    pm, _ = permutation_table(rf, Xm, y_m, 5, 42, "roc_auc")
    check("permutation importance 把純噪音欄排在強特徵之後",
          list(pm["特徵"]).index("f_noise") > list(pm["特徵"]).index("f_strong"),
          "、".join(pm["特徵"]))

    tr = tree_importance_table(rf, list(Xm.columns))
    check("tree importance 算得出來（只當對照，不進報告）",
          tr is not None and len(tr) == 3)

    have_shap, ver = shap_available()
    if have_shap:
        proba = rf.predict_proba(Xm)[:, pos_idx]
        st, sv, meta = shap_importance(rf, Xm, pos_idx, proba)
        check(f"SHAP 可用（{ver}）且加法性驗算通過",
              meta["加法性最大誤差"] < 1e-3,
              f"最大誤差 {meta['加法性最大誤差']:.3g}")
        check("SHAP 把純噪音欄排在強特徵之後",
              list(st["特徵"]).index("f_noise") > list(st["特徵"]).index("f_strong"),
              "、".join(st["特徵"]))
        check("SHAP 方向抓得到（f_strong 值越高分數越高）",
              st.loc[st["特徵"] == "f_strong", "方向"].iloc[0] == "值越高，分數越高",
              st.loc[st["特徵"] == "f_strong", "方向"].iloc[0])
        # 反向驗證：故意取錯類別維度，加法性必須不通過
        import shap as _shap
        raw = _shap.TreeExplainer(rf)(Xm)
        if np.asarray(raw.values).ndim == 3:
            wrong, wbase = _normalize_shap(raw.values, raw.base_values,
                                           1 - pos_idx)
            check("類別維度取錯時，加法性驗算會擋下來（不是靜默通過）",
                  additivity_error(wrong, wbase, proba) > 1e-3,
                  f"誤差 {additivity_error(wrong, wbase, proba):.3g}")
        else:
            check("類別維度取錯時，加法性驗算會擋下來（不是靜默通過）",
                  True, "本模型的 shap 輸出沒有類別維度，跳過")
        con = individual_contributions(sv, Xm, None, proba, top_n=3)
        check("個體層級貢獻每列取 3 個特徵", len(con) == 3 * len(Xm),
              f"{len(con)} 列")
        check("個體貢獻的結論欄用「在本模型中…」措辭，沒有因果字眼",
              all("在本模型中" in s for s in con["結論"])
              and not any(("造成" in s or "驅動" in s) for s in con["結論"]))
    else:
        check("shap 缺席時，自我測試照樣跑得完（降級路徑）", True, ver)

    # 降級路徑：不論 shap 在不在，都要驗一次「沒有 SHAP 時的行為」
    pdp = pdp_table(rf, Xm, ["f_strong"], grid=5)
    check("降級路徑的 PDP 算得出來（12 §一 指定的替代方案）",
          pdp is not None and len(pdp) > 0, f"{0 if pdp is None else len(pdp)} 列")
    r = gate_dominance(pm, "重要度", "permutation（已降級）")
    check("降級後仍會做單一特徵獨大檢查", "結果" in r, f"佔比={r.get('最大佔比')}")

    # ── ⑪ 洩漏長相：把標籤本身當特徵，必須被獨大檢查抓到 ────
    Xl = Xm.copy()
    Xl["洩漏_標籤本身"] = y_m.astype(float)
    rf2 = RandomForestClassifier(n_estimators=60, random_state=0,
                                 min_samples_leaf=5).fit(Xl, y_m)
    pm2, _ = permutation_table(rf2, Xl, y_m, 5, 42, "roc_auc")
    r = gate_dominance(pm2, "重要度", "permutation")
    check("把標籤當特徵時，獨大檢查抓得到（12 §六 的洩漏長相）",
          r["結果"] == "warning" and r["獨大特徵"] == "洩漏_標籤本身",
          f"{r.get('獨大特徵')} 佔 {r.get('最大佔比')}")

    # ── ⑫ 報告三句與警語 ────────────────────────────────────
    sent = report_sentences(t, float(y_ref.mean()))
    check("報告三句寫得出 top decile lift 與「比亂發還糟」",
          "3.30" in sent and "比亂發還糟" in sent)
    check("報告三句不含禁用動詞（00 §1.5 預測級白名單）",
          not any(w in sent for w in ("造成", "帶動", "驅動", "導致")),
          sent.splitlines()[0][:40])
    check("解讀警語第一條就是「模型怎麼想 ≠ 世界怎麼運作」",
          "模型怎麼想" in INTERPRETATION_NOTES[0]
          and "世界怎麼運作" in INTERPRETATION_NOTES[0])
    check("解讀警語提到共線稀釋與 tree importance 偏誤",
          any("稀釋" in s for s in INTERPRETATION_NOTES)
          and any("高基數" in s for s in INTERPRETATION_NOTES))

    # ── ⑬ 序列化：numpy 純量不可外洩 ────────────────────────
    try:
        json.dumps({"lift": t.to_dict("records"),
                    "perm": pm.to_dict("records"),
                    "tree": (tr.to_dict("records") if tr is not None else None),
                    "gate": gate_dominance(pm, "重要度", "permutation")},
                   ensure_ascii=False, default=_json_default)
        ser, msg = True, "含 numpy 純量仍可序列化"
    except TypeError as exc:
        ser, msg = False, str(exc)
    check("結果可寫成 JSON（numpy 純量不外洩）", ser, msg)

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(ran)} 項裡有 {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print(f"✅ 自我測試全部通過（共 {len(ran)} 項）")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="模型解釋：SHAP／特徵重要度／Lift-Gain（12 §五、§六、§九）")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--data", type=Path,
                    help="評估集（含特徵與標籤），預設 模型輸出/test_matrix.parquet")
    ap.add_argument("--model", type=Path,
                    help="已訓練模型（.joblib／.pkl），預設 模型輸出/model.joblib")
    ap.add_argument("--target", default="label", help="標籤欄名（預設 label）")
    ap.add_argument("--positive-label", help="正類的值（預設 1／True）")
    ap.add_argument("--score-col", help="已有分數欄時直接用它（此路徑只做 Lift/Gain）")
    ap.add_argument("--baseline-col",
                    help="naive baseline 的分數欄（R 排序／RFM Score 排序）—— 12 §九 要求")
    ap.add_argument("--feature-cols", help="逗號分隔，限定特徵欄（預設照模型的 feature_names_in_）")
    ap.add_argument("--eval-split", choices=("out_of_time", "random", "unknown"),
                    default="unknown",
                    help="評估集怎麼切的。腳本看不出來，要你具名宣告（00 §1.5）")
    ap.add_argument("--bins", type=int, default=N_BINS_DEFAULT,
                    help=f"分位數（預設 {N_BINS_DEFAULT}，ref 19 表 11.2 是十分位）")
    ap.add_argument("--curve-step", type=float, default=1.0,
                    help="Gain 曲線的取樣間隔（%%，預設 1）")
    ap.add_argument("--top-n", type=int, default=15,
                    help="重要度印前幾名（預設 15，對齊 beeswarm 的 max_display）")
    ap.add_argument("--n-repeats", type=int, default=10,
                    help="permutation importance 的重複次數（預設 10）")
    ap.add_argument("--sample", type=int, default=5000,
                    help="SHAP 的最大列數，超過就抽樣（預設 5000）")
    ap.add_argument("--no-shap", action="store_true",
                    help="強制走降級路徑（測試降級用）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-write", action="store_true", help="只算，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")

    # 參數值不合法要在這裡擋（→64）。掉到 run() 裡會被判成 1，
    # 而 1 的語意是「資料／設定的問題」—— 旗標打錯不是資料的問題。
    if args.bins < 2 or args.bins > 100:
        ap.error(f"--bins 要在 2–100 之間（收到 {args.bins}）；ref 19 表 11.2 用 10")
    if args.curve_step <= 0 or args.curve_step > 50:
        ap.error(f"--curve-step 要在 (0, 50] 之間（收到 {args.curve_step}）")
    if args.top_n < 1:
        ap.error(f"--top-n 至少 1（收到 {args.top_n}）")
    if args.n_repeats < 1:
        ap.error(f"--n-repeats 至少 1（收到 {args.n_repeats}）")
    if args.sample < MIN_BIN_N:
        ap.error(f"--sample 至少 {MIN_BIN_N}（收到 {args.sample}）；"
                 f"再少下去 mean|SHAP| 只是雜訊")
    if args.score_col and args.model:
        ap.error("--score-col 與 --model 只能給一個："
                 "給了分數欄就不會再跑模型推論，兩者同時給會讓報告說不清分數哪來的")

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
        print(f"⛔ explain_model.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
