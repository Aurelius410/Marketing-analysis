#!/usr/bin/env python3
"""
K-Means 五道前提關卡（07 §四）——— 分群之前跑前三道，fit 完回頭跑後兩道。

為什麼要獨立一支（prep_cluster_matrix 已經做過一部分）：
  · prep_cluster_matrix 是**產矩陣**的，它順手驗了尺度與偏度，但它跑完就走了。
    關卡 4（球形簇）與關卡 5（等變異）**只能在 fit 之後算**——需要 labels_。
    07 §四 開宗明義：「前三道是事前可驗的，後兩道只能事後驗——這個區別要誠實
    寫在報告裡，不要假裝五道都在跑之前就過了。」
  · 所以本腳本有兩個階段。**只跑前三道時，輸出一律標「五道過三道」，
    不准印「全部通過」**。這不是措辭潔癖：K-Means 對非球形與不等變異的簇會
    給出看起來很漂亮的錯誤答案，而那兩道關恰恰是報告最愛跳過的。

五道關（門檻與處置全部照 07 §四 的表，沒有一條是本腳本自己發明的）：

  1. 尺度已標準化   max(sd)/min(sd) > 10 必須標準化
                    ——「沒做就是禁行，不是警告」（05 §1.5）→ **error**
  2. 右偏欄已轉換   |skew| <= 1（M4 三門檻之一）→ 沒過 warning，附 06 §1.2 順位
  3. 無極端值主導   單一變數對 WGSS 的貢獻 > 70% → warning
  4. 球形簇假設     每群共變異矩陣條件數 κ=sqrt(λmax/λmin) > 10 → warning
  5. 等變異         max_k d̄_k / min_k d̄_k >= 4 → warning

關卡 1 的陷阱（這支腳本大半的價值在這裡）：
  餵進來的若是 prep_cluster_matrix 產出的 cluster_matrix.parquet，它**已經
  標準化過了**，每欄 sd 都是 1，尺度比恆等於 1.00 —— 直接算就是一道穩過的
  假關卡。真正該問的是「**標準化之前**比值是多少」。本腳本因此去讀
  模型輸出/scaler.json 的 vars[].scale（那是各欄轉換後、標準化前的 sd），
  用它還原真實比值。讀不到 scaler.json 而矩陣看起來已標準化 → 明講
  「這道關這次沒有真的驗到」，退 warning，不是 pass。

用法：
    # 事前三道（矩陣剛產好，還沒 fit）
    python kmeans_preflight.py 2026Q3_電商

    # 事後全五道（給 labels，或給 --k 讓它自己 fit 一次來驗）
    python kmeans_preflight.py 2026Q3_電商 --k 4
    python kmeans_preflight.py 2026Q3_電商 --labels 模型輸出/labels_k4.parquet

    python kmeans_preflight.py --self-test

輸出：
    統計表/分群輪廓/kmeans_五道關.csv      逐關結果
    統計表/分群輪廓/kmeans_關卡4_5_明細.csv 後兩道的逐群數字（有跑才寫）
    模型輸出/kmeans_preflight.json          機器可讀，供 build_report 引用
    主控台另印 07 §四 的「誠實說明模板」，可直接貼進報告

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 全過（且已標明跑了幾道）
    1  = 有 error 擋住（關卡 1 未標準化 = 禁行）
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

# ── 門檻。全部出自 07 §四 的表，不要在這裡調 ────────────────
SCALE_RATIO_MAX = 10.0      # 關卡 1：> 10 必須標準化
SKEW_MAX = 1.0              # 關卡 2：|skew| <= 1
WGSS_DOMINANCE_PCT = 70.0   # 關卡 3：單一變數 > 70% → warning
KAPPA_MAX = 10.0            # 關卡 4：κ > 10 該群明顯拉長
DISP_RATIO_MAX = 4.0        # 關卡 5：max/min >= 4 → warning

# 已標準化的判定：各欄 sd 都落在 1 附近。用 ddof=0 與 prep_cluster_matrix 一致。
STANDARDIZED_SD_TOL = 0.02

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


# ══════════════════════════════════════════════════════════════
#  載入
# ══════════════════════════════════════════════════════════════
def load_matrix(p: Any, explicit: Path | None) -> tuple[pd.DataFrame, Path]:
    """讀分群矩陣。預設吃 prep_cluster_matrix 的落點。"""
    path = explicit or (p.models / "cluster_matrix.parquet")
    if not path.exists():
        raise FileNotFoundError(
            f"找不到分群矩陣：{path}\n"
            f"  先跑 prep_cluster_matrix.py <專案> —— 它會產出這個檔。"
            f"  或用 --matrix 指定路徑。"
        )
    df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
          else pd.read_csv(path))
    return df, path


def load_scaler(p: Any, explicit: Path | None) -> dict[str, Any] | None:
    """讀 scaler.json。關卡 1 要靠它還原標準化前的 sd。"""
    path = explicit or (p.models / "scaler.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def numeric_cols(df: pd.DataFrame, id_col: str | None,
                 label_col: str | None) -> list[str]:
    drop = {c for c in (id_col, label_col) if c}
    return [c for c in df.columns
            if c not in drop and pd.api.types.is_numeric_dtype(df[c])]


def pick_id_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        low = str(c).lower()
        if low in ("客戶編號", "customer_id", "cust_id", "id") or low.endswith("_id"):
            return c
    return None


def looks_standardized(X: pd.DataFrame) -> bool:
    sd = X.std(ddof=0)
    sd = sd[sd.notna()]
    if sd.empty:
        return False
    return bool(np.all(np.abs(sd.to_numpy() - 1.0) <= STANDARDIZED_SD_TOL))


def _py(v: Any) -> Any:
    """numpy 純量 → 原生 Python 型別。

    群標籤來自 pd.unique(labels)，是 numpy int32/int64。它會一路帶進
    結果 dict，json.dumps 到那裡才丟 TypeError —— 而且是在所有分析都跑完、
    CSV 都寫好之後才炸，退出碼 70 蓋掉前面全綠的結論。在來源轉掉。
    """
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    """兜底：萬一日後新增欄位又漏了 numpy 型別，讓它落地而不是讓整支腳本掛掉。"""
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    return str(o)


def skewness(x: np.ndarray) -> float:
    """與 prep_cluster_matrix.skewness 同式（Fisher-Pearson，g1）。"""
    x = x[np.isfinite(x)]
    n = x.size
    if n < 3:
        return 0.0
    m = x.mean()
    s = x.std(ddof=0)
    if s == 0:
        return 0.0
    return float(((x - m) ** 3).mean() / s ** 3)


# ══════════════════════════════════════════════════════════════
#  關卡 1：尺度
# ══════════════════════════════════════════════════════════════
def gate1_scale(X: pd.DataFrame, scaler: dict[str, Any] | None) -> dict[str, Any]:
    print("\n關卡 1／尺度已標準化（07 §四；門檻 max(sd)/min(sd) ≤ 10）")

    standardized = looks_standardized(X)
    res: dict[str, Any] = {"關卡": 1, "名稱": "尺度已標準化", "階段": "事前"}

    # 先看標準化「之前」的比值 —— 那才是這道關真正要問的
    pre_sd: dict[str, float] = {}
    if scaler and isinstance(scaler.get("vars"), dict):
        for _, v in scaler["vars"].items():
            col, sc = v.get("out_col"), v.get("scale")
            if col in X.columns and isinstance(sc, (int, float)) and sc > 0:
                pre_sd[col] = float(sc)

    if pre_sd and len(pre_sd) >= 2:
        ratio = max(pre_sd.values()) / min(pre_sd.values())
        hi = max(pre_sd, key=lambda k: pre_sd[k])
        lo = min(pre_sd, key=lambda k: pre_sd[k])
        res.update({"數值": round(ratio, 2), "門檻": f"≤ {SCALE_RATIO_MAX:.0f}",
                    "依據": "scaler.json 的標準化前 sd"})
        detail(f"標準化前尺度比 {ratio:.2f}（{hi} sd={pre_sd[hi]:.4g}／"
               f"{lo} sd={pre_sd[lo]:.4g}）")
        if ratio > SCALE_RATIO_MAX and not standardized:
            err(f"尺度比 {ratio:.2f} > {SCALE_RATIO_MAX:.0f} 且矩陣未標準化",
                "05 §1.5：沒做標準化就是禁行，不是警告。回頭跑 "
                "prep_cluster_matrix.py（spec 的 scaler 不可為 none）")
            res["結果"] = "error"
        elif standardized:
            ok(f"標準化前比值 {ratio:.2f}，矩陣已 z-score 標準化 → 通過")
            res["結果"] = "pass"
        else:
            ok(f"尺度比 {ratio:.2f} ≤ {SCALE_RATIO_MAX:.0f}，未標準化也可接受")
            res["結果"] = "pass"
        return res

    # 沒有 scaler.json：只能看手上這份矩陣
    sd = X.std(ddof=0)
    sd = sd[sd > 0]
    if len(sd) < 2:
        warn("可用欄位不足 2 欄，尺度比算不出來",
             "確認矩陣是不是只有一個變數 —— 單變數不需要分群")
        res.update({"數值": None, "門檻": f"≤ {SCALE_RATIO_MAX:.0f}", "結果": "warning",
                    "依據": "欄位不足"})
        return res

    ratio = float(sd.max() / sd.min())
    res.update({"數值": round(ratio, 2), "門檻": f"≤ {SCALE_RATIO_MAX:.0f}",
                "依據": "當前矩陣的 sd"})
    if standardized:
        # 這是最危險的情況：比值 1.00 看起來完美，其實什麼都沒驗到
        warn(f"矩陣已標準化（各欄 sd≈1，比值 {ratio:.2f}）但找不到 scaler.json，"
             f"**這道關這次沒有真的驗到**",
             f"標準化後算尺度比恆等於 1，是一道穩過的假關卡。"
             f"要真的驗它，跑 prep_cluster_matrix.py 產出 "
             f"{'模型輸出/scaler.json'}，或用 --scaler 指路徑")
        res["結果"] = "warning"
        res["依據"] = "已標準化但無 scaler.json —— 未實際驗證"
    elif ratio > SCALE_RATIO_MAX:
        err(f"尺度比 {ratio:.2f} > {SCALE_RATIO_MAX:.0f}（{sd.idxmax()} vs {sd.idxmin()}）",
            "05 §1.5：沒做標準化就是禁行。跑 prep_cluster_matrix.py 標準化後再來")
        res["結果"] = "error"
    else:
        ok(f"尺度比 {ratio:.2f} ≤ {SCALE_RATIO_MAX:.0f}")
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 2：偏度
# ══════════════════════════════════════════════════════════════
def gate2_skew(X: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    print(f"\n關卡 2／右偏欄已轉換（07 §四；門檻 |skew| ≤ {SKEW_MAX:.0f}）")
    rows = []
    for c in X.columns:
        sk = skewness(X[c].to_numpy(dtype=float))
        rows.append({"變數": c, "偏度": round(sk, 3),
                     "結論": "通過" if abs(sk) <= SKEW_MAX else "超標"})
    tbl = pd.DataFrame(rows)
    bad = tbl[tbl["結論"] == "超標"]

    res: dict[str, Any] = {"關卡": 2, "名稱": "右偏欄已轉換", "階段": "事前",
                           "門檻": f"|skew| ≤ {SKEW_MAX:.0f}",
                           "數值": round(float(tbl["偏度"].abs().max()), 3) if len(tbl) else None}
    if len(bad) == 0:
        ok(f"{len(tbl)} 欄偏度全部在 ±{SKEW_MAX:.0f} 內"
           f"（最大 |skew| = {tbl['偏度'].abs().max():.3f}）")
        res["結果"] = "pass"
    else:
        warn(f"{len(bad)} 欄偏度超標："
             + "、".join(f"{r.變數}={r.偏度:+.2f}" for r in bad.itertuples()),
             "依 06 §1.2 順位表：右偏全正 → log(x)（分群輸入屬「只做描述」，"
             "用第二順位即可）；右偏含 0 → Yeo-Johnson。轉換後複檢 Spearman "
             "排序相關 > 0.95。prep_cluster_matrix.py 會自動做這件事 —— "
             "若它做完仍超標，代表 log1p 後退回了 NTILE(5)，報告要寫明原因")
        res["結果"] = "warning"
    return res, tbl


# ══════════════════════════════════════════════════════════════
#  關卡 3：極端值主導（讀 prep_cluster_matrix 的 WGSS 貢獻表）
# ══════════════════════════════════════════════════════════════
def gate3_wgss(p: Any, X: pd.DataFrame, labels: np.ndarray | None) -> dict[str, Any]:
    print(f"\n關卡 3／無極端值主導（07 §四；門檻 單一變數 ≤ {WGSS_DOMINANCE_PCT:.0f}%）")
    res: dict[str, Any] = {"關卡": 3, "名稱": "無極端值主導", "階段": "事前",
                           "門檻": f"≤ {WGSS_DOMINANCE_PCT:.0f}%"}

    tbl = None
    src = p.tables / "分群輪廓" / "wgss_contribution.csv"
    if src.exists():
        try:
            tbl = pd.read_csv(src, encoding="utf-8-sig")
            res["依據"] = f"prep_cluster_matrix 的 {src.name}"
        except (OSError, pd.errors.ParserError):
            tbl = None

    if tbl is None and labels is not None:
        # 現場算一份。與 prep_cluster_matrix.wgss_decompose 同一套拆解。
        from prep_cluster_matrix import wgss_decompose
        tbl = wgss_decompose(X.to_numpy(dtype=float), labels, list(X.columns))
        res["依據"] = "本次以 labels 現算"

    if tbl is None or "貢獻百分比" not in tbl.columns:
        warn("找不到 WGSS 貢獻表，關卡 3 這次沒有驗到",
             f"先跑 prep_cluster_matrix.py（它會寫出 {src}），"
             f"或本腳本加 --k / --labels 讓它現算")
        res.update({"數值": None, "結果": "warning", "依據": "無資料 —— 未實際驗證"})
        return res

    worst = tbl.loc[tbl["貢獻百分比"].idxmax()]
    res["數值"] = round(float(worst["貢獻百分比"]), 2)
    for r in tbl.sort_values("貢獻百分比", ascending=False).itertuples():
        detail(f"{getattr(r, '變數', '?')}：{r.貢獻百分比:.2f}%")
    if float(worst["貢獻百分比"]) > WGSS_DOMINANCE_PCT:
        warn(f"{worst.get('變數', '?')} 對 WGSS 的貢獻 {worst['貢獻百分比']:.2f}%"
             f" > {WGSS_DOMINANCE_PCT:.0f}%",
             "先分辨「單點」還是「次族群」：占比 < 1% 且無結構 = 單點，查輸入錯誤；"
             "≥ 5% 或密度圖雙峰 = 次族群，**不准刪，分開建模**。"
             "先轉換再看還有沒有離群，絕不先 winsorize（SKILL.md 負面清單）")
        res["結果"] = "warning"
    else:
        ok(f"最大貢獻 {worst.get('變數', '?')} {worst['貢獻百分比']:.2f}%"
           f" ≤ {WGSS_DOMINANCE_PCT:.0f}%")
        res["結果"] = "pass"
    return res


# ══════════════════════════════════════════════════════════════
#  關卡 4／5：只能事後驗
# ══════════════════════════════════════════════════════════════
def gate4_sphericity(X: pd.DataFrame,
                     labels: np.ndarray) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    print(f"\n關卡 4／球形簇假設（07 §四；門檻 κ ≤ {KAPPA_MAX:.0f}）  ← 事後驗")
    A = X.to_numpy(dtype=float)
    d = A.shape[1]
    rows: list[dict[str, Any]] = []
    flagged, uncomputable = [], []

    for k in sorted(pd.unique(labels)):
        m = labels == k
        n_k = int(m.sum())
        row: dict[str, Any] = {"群": _py(k), "n": n_k}
        if n_k <= d:
            # 樣本數不大於維度 → 共變異矩陣必為奇異，κ 會是 inf。
            # 這不是「該群拉長」，是「算不出來」，兩者不可混為一談。
            row.update({"條件數": None, "結論": f"群太小（n={n_k} ≤ 維度 {d}），算不出來"})
            uncomputable.append(f"群 {k}(n={n_k})")
            rows.append(row)
            continue
        cov = np.cov(A[m], rowvar=False)
        ev = np.linalg.eigvalsh(np.atleast_2d(cov))
        ev = ev[ev > 0]
        if ev.size < d:
            row.update({"條件數": None,
                        "結論": f"共變異矩陣秩虧（正特徵值 {ev.size}/{d}），該群變數共線"})
            uncomputable.append(f"群 {k}(秩虧)")
            rows.append(row)
            continue
        kappa = float(np.sqrt(ev.max() / ev.min()))
        row.update({"條件數": round(kappa, 2),
                    "結論": "通過" if kappa <= KAPPA_MAX else "明顯拉長"})
        if kappa > KAPPA_MAX:
            flagged.append(f"群 {k}(κ={kappa:.1f})")
        rows.append(row)

    for r in rows:
        kv = f"{r['條件數']:.2f}" if r["條件數"] is not None else "—"
        detail(f"群 {r['群']}（n={r['n']}）κ = {kv}｜{r['結論']}")

    kappas = [r["條件數"] for r in rows if r["條件數"] is not None]
    res: dict[str, Any] = {"關卡": 4, "名稱": "球形簇假設", "階段": "事後",
                           "門檻": f"κ ≤ {KAPPA_MAX:.0f}",
                           "數值": round(max(kappas), 2) if kappas else None}
    if flagged:
        warn(f"{len(flagged)} 群不符球形假設：{'、'.join(flagged)}",
             "升級 L4 HDBSCAN，或改用 GMM 的 full covariance。"
             "教材原話：K-Means「假設簇呈球形，對非凸形狀效果差」。"
             "先跑 §六 的 HDBSCAN 交叉比對 —— 被判為噪音的成員不進行銷名單")
        res["結果"] = "warning"
    elif uncomputable and not kappas:
        warn(f"所有群都算不出條件數（{'、'.join(uncomputable)}）",
             "關卡 4 這次沒有驗到。群太小或群內變數共線 —— "
             "先確認 k 是不是切太細")
        res["結果"] = "warning"
    else:
        ok(f"各群條件數皆 ≤ {KAPPA_MAX:.0f}（最大 {max(kappas):.2f}）")
        res["結果"] = "pass"
    if uncomputable and kappas:
        info(f"另有 {len(uncomputable)} 群算不出條件數（{'、'.join(uncomputable)}）"
             f"—— 這幾群的球形假設未驗證，報告不可寫成通過")
    return res, rows


def gate5_equal_variance(X: pd.DataFrame,
                         labels: np.ndarray) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    print(f"\n關卡 5／等變異（07 §四；門檻 max/min < {DISP_RATIO_MAX:.0f}）  ← 事後驗")
    A = X.to_numpy(dtype=float)
    rows: list[dict[str, Any]] = []
    for k in sorted(pd.unique(labels)):
        m = labels == k
        pts = A[m]
        centroid = pts.mean(axis=0)
        dbar = float(np.linalg.norm(pts - centroid, axis=1).mean())
        rows.append({"群": _py(k), "n": int(m.sum()),
                     "群內平均距離": round(dbar, 4)})

    for r in rows:
        detail(f"群 {r['群']}（n={r['n']}）d̄ = {r['群內平均距離']:.4f}")

    ds = [r["群內平均距離"] for r in rows]
    res: dict[str, Any] = {"關卡": 5, "名稱": "等變異", "階段": "事後",
                           "門檻": f"< {DISP_RATIO_MAX:.0f}"}
    positive = [d for d in ds if d > 0]
    if not positive or len(ds) < 2:
        warn("群數不足 2 或所有群的群內距離為 0，比值算不出來",
             "確認 labels 是不是只有一群 —— 一群不需要比較等變異")
        res.update({"數值": None, "結果": "warning"})
        return res, rows
    if len(positive) < len(ds):
        # 單點群的 d̄=0，拿它當分母會得到 inf。剔除並明講。
        zeros = [r["群"] for r in rows if r["群內平均距離"] == 0]
        info(f"群 {zeros} 的群內平均距離為 0（單點群或成員完全重合），"
             f"不納入比值計算 —— 用 0 當分母會得到無限大")
    ratio = max(positive) / min(positive)
    res["數值"] = round(ratio, 2)
    hi = max(rows, key=lambda r: r["群內平均距離"])
    lo = min((r for r in rows if r["群內平均距離"] > 0),
             key=lambda r: r["群內平均距離"])
    if ratio >= DISP_RATIO_MAX:
        warn(f"群內離散比 {ratio:.2f} ≥ {DISP_RATIO_MAX:.0f}"
             f"（群 {hi['群']} d̄={hi['群內平均距離']:.4f} / "
             f"群 {lo['群']} d̄={lo['群內平均距離']:.4f}）",
             "K-Means 的 WGSS 目標函數對各群一視同仁，變異大的群會被切碎、"
             "變異小的群會被吞併。升級 GMM（各成分可有自己的共變異），"
             "或接受並在報告寫明")
        res["結果"] = "warning"
    else:
        ok(f"群內離散比 {ratio:.2f} < {DISP_RATIO_MAX:.0f}")
        res["結果"] = "pass"
    return res, rows


# ══════════════════════════════════════════════════════════════
#  07 §四 的誠實說明模板
# ══════════════════════════════════════════════════════════════
def honesty_template(g4: dict[str, Any], g4_rows: list[dict[str, Any]],
                     g5: dict[str, Any], g5_rows: list[dict[str, Any]]) -> str:
    def fmt4(r):
        return "算不出來" if r["條件數"] is None else f"{r['條件數']:.1f}"

    ks = "／".join(f"{fmt4(r)}" for r in g4_rows)
    bad4 = [r for r in g4_rows
            if r["條件數"] is not None and r["條件數"] > KAPPA_MAX]
    ds = "／".join(f"{r['群內平均距離']:.2f}" for r in g5_rows)

    lines = [
        "本節的 K-Means 有兩道前提只能事後檢查。實際結果：",
        f"  · 球形假設：群 {'/'.join(str(r['群']) for r in g4_rows)} 的共變異條件數 {ks}",
    ]
    if bad4:
        for r in bad4:
            lines.append(f"    群 {r['群']} 為 {r['條件數']:.1f}（未通過，該群明顯拉長）")
    else:
        lines.append("    （全部通過）")
    if g5["數值"] is not None:
        lines.append(f"  · 等變異：群內平均距離 {ds}，比值 {g5['數值']:.2f}"
                     f"（{'通過' if g5['結果'] == 'pass' else '未通過'}）")
    if bad4:
        gl = "、".join(str(r["群"]) for r in bad4)
        lines += [
            f"因此群 {gl} 的成員邊界不可信，§六 需用 HDBSCAN 對這批人做交叉比對。",
            "被 HDBSCAN 判為噪音的成員不進任何行銷名單。",
        ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
#  labels 來源
# ══════════════════════════════════════════════════════════════
def resolve_labels(df: pd.DataFrame, X: pd.DataFrame, args: Any,
                   p: Any) -> tuple[np.ndarray | None, str]:
    """回傳 (labels, 來源說明)。拿不到回 (None, 原因)。"""
    if args.label_col:
        if args.label_col not in df.columns:
            raise ValueError(f"矩陣裡沒有 --label-col 指定的欄位：{args.label_col}")
        return df[args.label_col].to_numpy(), f"矩陣的 {args.label_col} 欄"

    if args.labels:
        lp: Path = args.labels
        if not lp.exists():
            raise FileNotFoundError(f"找不到 labels 檔：{lp}")
        ldf = (pd.read_parquet(lp) if lp.suffix.lower() == ".parquet"
               else pd.read_csv(lp))
        cand = [c for c in ldf.columns
                if str(c).lower() in ("label", "labels", "cluster", "群", "群編號")]
        col = cand[0] if cand else ldf.columns[-1]
        if len(ldf) != len(X):
            raise ValueError(
                f"labels 列數 {len(ldf)} 與矩陣列數 {len(X)} 不一致 —— "
                f"兩者必須是同一次 fit 的產物，否則關卡 4/5 量到的是隨機配對")
        return ldf[col].to_numpy(), f"{lp.name} 的 {col} 欄"

    for c in ("label", "labels", "cluster", "群", "群編號"):
        if c in df.columns:
            return df[c].to_numpy(), f"矩陣既有的 {c} 欄"

    if args.k:
        from prep_cluster_matrix import fit_labels
        spec_path = p.models / "cluster_spec.json"
        seed, n_init = 42, 10
        if spec_path.exists():
            try:
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                seed = int(spec.get("seed", seed))
                n_init = int(spec.get("n_init", n_init))
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                pass
        lab = fit_labels(X.to_numpy(dtype=float), args.k, seed, n_init)
        return lab, f"本腳本現場 fit（k={args.k}、seed={seed}、n_init={n_init}）"

    return None, "沒給 --k／--labels／--label-col，且矩陣裡沒有群欄位"


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    df, mpath = load_matrix(p, args.matrix)
    scaler = load_scaler(p, args.scaler)

    id_col = args.id_col or pick_id_col(df)
    labels, lab_src = resolve_labels(df, df, args, p)
    label_col_name = args.label_col
    if label_col_name is None:
        for c in ("label", "labels", "cluster", "群", "群編號"):
            if c in df.columns:
                label_col_name = c
                break

    cols = numeric_cols(df, id_col, label_col_name)
    if not cols:
        raise ValueError(f"矩陣 {mpath.name} 裡找不到任何數值欄位")
    X = df[cols].astype(float)

    # 缺值：K-Means 不吃 NaN，這裡先講清楚而不是讓 sklearn 丟例外
    n_nan = int(X.isna().any(axis=1).sum())
    if n_nan:
        raise ValueError(
            f"矩陣有 {n_nan} 列含缺值（共 {len(X)} 列）。K-Means 不吃 NaN。\n"
            f"  prep_cluster_matrix.py 會把缺值列移到 隔離區/cluster_matrix_dropped.csv"
            f" 並在報告交代（18-E22）。先跑它，不要在這裡補值。")

    print("=" * 72)
    print("行銷數據分析 Skill — K-Means 五道前提關卡（07 §四）")
    print(f"專案：{args.project}｜矩陣：{mpath.name}（{len(X):,} 列 × {len(cols)} 欄）")
    print(f"輸入變數：{'、'.join(cols)}")
    print(f"labels：{lab_src}")
    print("=" * 72)

    results: list[dict[str, Any]] = []
    r1 = gate1_scale(X, scaler)
    results.append(r1)
    r2, skew_tbl = gate2_skew(X)
    results.append(r2)
    r3 = gate3_wgss(p, X, labels)
    results.append(r3)

    g4_rows: list[dict[str, Any]] = []
    g5_rows: list[dict[str, Any]] = []
    if labels is not None:
        if len(labels) != len(X):
            raise ValueError(f"labels 長度 {len(labels)} ≠ 矩陣列數 {len(X)}")
        r4, g4_rows = gate4_sphericity(X, labels)
        r5, g5_rows = gate5_equal_variance(X, labels)
        results += [r4, r5]
    else:
        print("\n關卡 4／5（球形簇、等變異）—— 事後才驗得到，本次未跑")
        info(f"原因：{lab_src}")
        detail("要跑：加 --k <群數> 讓本腳本現場 fit 一次，"
               "或 --labels <檔> 指向既有的分群結果")

    ran = len(results)
    n_err = sum(1 for r in results if r["結果"] == "error")
    n_warn = sum(1 for r in results if r["結果"] == "warning")
    n_pass = sum(1 for r in results if r["結果"] == "pass")

    print("\n" + "=" * 72)
    # 07 §四：「不要假裝五道都在跑之前就過了」。跑幾道就說幾道。
    print(f"跑了 {ran}／5 道關｜通過 {n_pass}、warning {n_warn}、error {n_err}")
    if ran < 5:
        print("      ⚠ 關卡 4／5 尚未驗證。報告不可寫「五道前提全部通過」，")
        print("        只能寫「事前三道通過，球形與等變異待 fit 後補驗」。")

    if n_err:
        print(f"結果：⛔ 有 {n_err} 條 error → 不准跑 K-Means。")
    elif n_warn:
        print(f"結果：⚠ 有 {n_warn} 條 warning → 可往下，但報告要逐條寫明處置。")
    else:
        print(f"結果：✅ 跑到的 {ran} 道關全過。")

    if g4_rows and g5_rows:
        print("\n" + "-" * 72)
        print("可直接貼進報告的誠實說明（07 §四 模板）：")
        print("-" * 72)
        r4 = next(r for r in results if r["關卡"] == 4)
        r5 = next(r for r in results if r["關卡"] == 5)
        print(honesty_template(r4, g4_rows, r5, g5_rows))

    if not args.no_write:
        out_dir = p.tables / "分群輪廓"
        out_dir.mkdir(parents=True, exist_ok=True)
        gate_csv = out_dir / "kmeans_五道關.csv"
        pd.DataFrame(results).to_csv(gate_csv, index=False, encoding="utf-8-sig")
        print(f"\n✓ 五道關結果：{gate_csv}")

        skew_csv = out_dir / "kmeans_關卡2_偏度.csv"
        skew_tbl.to_csv(skew_csv, index=False, encoding="utf-8-sig")

        if g4_rows:
            det = pd.merge(pd.DataFrame(g4_rows), pd.DataFrame(g5_rows),
                           on=["群", "n"], how="outer")
            dp = out_dir / "kmeans_關卡4_5_明細.csv"
            det.to_csv(dp, index=False, encoding="utf-8-sig")
            print(f"✓ 關卡 4／5 逐群明細：{dp}")

        p.models.mkdir(parents=True, exist_ok=True)
        jp = p.models / "kmeans_preflight.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "matrix": str(mpath),
            "n_rows": int(len(X)),
            "input_vars": cols,
            "labels_source": lab_src,
            "gates_run": ran,
            "gates_total": 5,
            "後兩道已驗": bool(g4_rows),
            "results": results,
            "gate4_detail": g4_rows,
            "gate5_detail": g5_rows,
            "errors": _errors,
            "warnings": _warnings,
        }, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8")
        print(f"✓ 機器可讀結果：{jp}")

    if n_err:
        return EX_ERROR
    if n_warn:
        return EX_WARN
    return EX_OK


# ══════════════════════════════════════════════════════════════
#  自我測試
# ══════════════════════════════════════════════════════════════
def _selftest() -> int:
    print("=" * 72)
    print("kmeans_preflight.py 自我測試")
    print("=" * 72)
    rng = np.random.default_rng(20260727)
    failed = []

    def check(name: str, cond: bool, got: str = "") -> None:
        if cond:
            print(f"  ✓ {name}" + (f"（{got}）" if got else ""))
        else:
            print(f"  ✗ {name}" + (f"（{got}）" if got else ""))
            failed.append(name)

    # ① 偏度：對數常態應遠大於 1，標準常態應接近 0
    X_sk = pd.DataFrame({"a": rng.lognormal(0, 1.2, 3000),
                         "b": rng.normal(0, 1, 3000)})
    r2, tbl = gate2_skew(X_sk)
    check("關卡 2 抓到對數常態的右偏", r2["結果"] == "warning",
          f"max|skew|={r2['數值']}")
    check("關卡 2 沒有誤判常態欄",
          tbl.loc[tbl["變數"] == "b", "結論"].iloc[0] == "通過")

    # ② 尺度：無 scaler.json 且矩陣已標準化 → 必須是 warning 而非 pass
    Z = pd.DataFrame({c: (X_sk[c] - X_sk[c].mean()) / X_sk[c].std(ddof=0)
                      for c in X_sk})
    r1 = gate1_scale(Z, None)
    check("已標準化但無 scaler.json → 不准報 pass", r1["結果"] == "warning",
          f"結果={r1['結果']}")

    # ③ 尺度：未標準化且比值 > 10 → error（05 §1.5 禁行）
    X_big = pd.DataFrame({"f": rng.normal(0, 1, 2000),
                          "m": rng.normal(0, 500, 2000)})
    r1b = gate1_scale(X_big, None)
    check("尺度比 > 10 且未標準化 → error", r1b["結果"] == "error",
          f"ratio={r1b['數值']}")

    # ④ 尺度：有 scaler.json 時用標準化前的 sd 還原真實比值
    fake_scaler = {"vars": {"f": {"out_col": "f", "scale": 1.0},
                            "m": {"out_col": "m", "scale": 500.0}}}
    Zb = pd.DataFrame({c: (X_big[c] - X_big[c].mean()) / X_big[c].std(ddof=0)
                       for c in X_big})
    r1c = gate1_scale(Zb, fake_scaler)
    check("有 scaler.json → 還原標準化前比值並判 pass",
          r1c["結果"] == "pass" and r1c["數值"] is not None and r1c["數值"] > 100,
          f"還原比值={r1c['數值']}")

    # ⑤ 關卡 4：刻意造一個拉長的群 + 一個球形群
    n = 400
    sph = rng.normal(0, 1, (n, 2))
    elong = np.column_stack([rng.normal(0, 8, n), rng.normal(0, 0.2, n)])
    X45 = pd.DataFrame(np.vstack([sph, elong + 40]), columns=["x", "y"])
    lab = np.array([0] * n + [1] * n)
    r4, rows4 = gate4_sphericity(X45, lab)
    k0 = next(r["條件數"] for r in rows4 if r["群"] == 0)
    k1 = next(r["條件數"] for r in rows4 if r["群"] == 1)
    check("關卡 4 判出拉長群", r4["結果"] == "warning" and k1 > KAPPA_MAX,
          f"球形群 κ={k0:.2f}、拉長群 κ={k1:.2f}")
    check("關卡 4 沒有誤判球形群", k0 <= KAPPA_MAX, f"κ={k0:.2f}")

    # ⑥ 關卡 4：n <= 維度 → 必須回「算不出來」，不能回 inf 當成拉長
    X_tiny = pd.DataFrame(rng.normal(0, 1, (6, 4)), columns=list("abcd"))
    lab_tiny = np.array([0, 0, 0, 1, 1, 1])   # 每群 n=3 ≤ 維度 4
    r4t, rows4t = gate4_sphericity(X_tiny, lab_tiny)
    check("關卡 4 對 n ≤ 維度 的群回「算不出來」而非 inf",
          all(r["條件數"] is None for r in rows4t),
          "；".join(r["結論"] for r in rows4t))

    # ⑦ 關卡 5：離散比
    tight = rng.normal(0, 0.2, (300, 2))
    loose = rng.normal(0, 3.0, (300, 2)) + 30
    X5 = pd.DataFrame(np.vstack([tight, loose]), columns=["x", "y"])
    lab5 = np.array([0] * 300 + [1] * 300)
    r5, rows5 = gate5_equal_variance(X5, lab5)
    check("關卡 5 判出不等變異", r5["結果"] == "warning", f"比值={r5['數值']}")
    X5e = pd.DataFrame(rng.normal(0, 1, (600, 2)), columns=["x", "y"])
    r5e, _ = gate5_equal_variance(X5e, lab5)
    check("關卡 5 沒有誤判等變異", r5e["結果"] == "pass", f"比值={r5e['數值']}")

    # ⑧ 關卡 5：單點群 d̄=0 不可當分母
    X5s = pd.DataFrame(np.vstack([tight, np.zeros((1, 2)) + 99]), columns=["x", "y"])
    lab5s = np.array([0] * 300 + [1])
    r5s, _ = gate5_equal_variance(X5s, lab5s)
    check("關卡 5 剔除 d̄=0 的單點群，不回 inf",
          r5s["數值"] is not None and np.isfinite(r5s["數值"]),
          f"比值={r5s['數值']}")

    # ⑨ 誠實說明模板產得出來且點名未通過的群
    tpl = honesty_template(r4, rows4, r5, rows5)
    check("誠實說明模板點名未通過的群", "未通過" in tpl and "群 1" in tpl)

    # ⑩ 結果必須 JSON 序列化得出來。
    #    群標籤來自 pd.unique()，是 numpy int32 —— 早期版本在這裡丟 TypeError，
    #    而且是在五道關全跑完、CSV 都寫好之後才炸，退出碼 70 蓋掉全綠的結論。
    #    這一項直接驗序列化，不要只驗各關的計算。
    try:
        payload = {"results": [r1, r2, r4, r5],
                   "gate4_detail": rows4, "gate5_detail": rows5}
        json.dumps(payload, ensure_ascii=False, default=_json_default)
        ser_ok, ser_msg = True, "含 numpy 群標籤仍可序列化"
    except TypeError as e:
        ser_ok, ser_msg = False, str(e)
    check("五道關結果可寫成 JSON（numpy 純量不外洩）", ser_ok, ser_msg)
    check("群標籤已轉成原生 int",
          all(type(r["群"]) is int for r in rows4 + rows5),
          "、".join(sorted({type(r["群"]).__name__ for r in rows4 + rows5})))

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="K-Means 五道前提關卡（07 §四）。前三道事前驗，後兩道 fit 後驗。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--matrix", type=Path,
                    help="分群矩陣（預設 模型輸出/cluster_matrix.parquet）")
    ap.add_argument("--scaler", type=Path,
                    help="scaler.json（預設 模型輸出/scaler.json）。關卡 1 靠它還原標準化前的 sd")
    ap.add_argument("--labels", type=Path, help="既有分群結果（.parquet／.csv）")
    ap.add_argument("--label-col", help="群標籤在矩陣裡的欄名")
    ap.add_argument("--k", type=int, help="沒有現成 labels 時，用這個 k 現場 fit 一次來驗關卡 4／5")
    ap.add_argument("--id-col", help="客戶 id 欄名（會被排除在輸入變數外）")
    ap.add_argument("--no-write", action="store_true", help="只檢查，不寫檔")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")

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
        print(f"⛔ kmeans_preflight.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
