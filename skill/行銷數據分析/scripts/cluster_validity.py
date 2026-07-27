#!/usr/bin/env python3
"""
k 怎麼決定（07 §五）＋ 分群「是不是真的」（07 §7.4）。

包子自己的期末報告在這裡有一個明確缺口：K=4 **沒有選擇依據** —— 未做 elbow、
未做 silhouette、未比較不同 k。這支腳本就是為了讓那一格再也不會空著。

做四件事：

  ① 四個指標逐 k 算  Elbow(改善率) / CH / Silhouette(含剖面) / Gap
  ② §5.2 仲裁表      三者不一致是常態不是異常，規則是硬的，
                     不准挑一個看起來合理的用
  ③ §5.3 可執行性    最小群人數 >= max(0.05n, 30)。兩條取較嚴的，
                     n < 600 時恆由「30 人」那條綁定
  ④ §7.4 存在性      對「同尺度的參考資料」跑完全相同的 pipeline，
                     輸出 structure_pvalue

為什麼 ④ 必須獨立於 ①：
  bootstrap ARI 測的是**穩定性**，不是**存在性** —— 純隨機噪音也可能得到穩定的
  分群（因為切法本身穩定）。而 CH 與 K-Means 目標函數同源，它再高也不能證明
  「群是真的」。要主張這批資料真的有群結構，唯一合法的數字是 structure_pvalue；
  §八 的 ANOVA p 值不行（那是 S1 循環推論，見 07 §8.2 與 verify_outputs 的 T08）。

參考資料兩種都跑（07 §7.4 明訂）：
  (a) 各欄獨立 permutation 打亂 —— 保留邊際分布、破壞相關結構
  (b) uniform hypercube        —— 連邊際分布也不保留
  兩者的 p 值意義不同：(a) 問「這些群是不是只來自各欄的邊際分布」，
  (b) 問「這些群是不是只來自資料的外框」。(a) 比 (b) 嚴格，兩個都要報。

Gap 的參考分布產生方式會改結果，所以**寫進 cluster_spec.json**（07 §5.1）。
本腳本預設 uniform hypercube（Tibshirani 原文的方法 (a)），可用
--gap-reference pca 切成 PCA 對齊的外框（原文方法 (b)）。

用法：
    python cluster_validity.py 2026Q3_電商
    python cluster_validity.py 2026Q3_電商 --k-range 2-10 --B 200
    python cluster_validity.py 2026Q3_電商 --gap-reference pca
    python cluster_validity.py --self-test

輸出：
    統計表/分群輪廓/k選擇_四指標.csv
    統計表/分群輪廓/k選擇_silhouette剖面.csv
    統計表/分群輪廓/k選擇_可執行性.csv
    統計表/分群輪廓/分群存在性_structure_pvalue.csv
    模型輸出/cluster_validity.json

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 四指標收斂到可執行的 k
    1  = 有 error 擋住（§5.2 的兩個「停」：gap 最佳 k=1、silhouette 與 gap 差 ≥2）
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

# ── 門檻。全部出自 07 §5.1／§5.2／§5.3，不要在這裡調 ──────────
ELBOW_IMPROVE_PCT = 5.0        # 改善率首次跌破 5% 的前一點（教材投影片示例）
SIL_STRONG = 0.50              # >= 結構明確
SIL_WEAK = 0.25                # >= 結構弱但可用；< 無實質結構
SIL_NEG_FRAC_MAX = 0.20        # 任一群 > 20% 樣本 s(i)<0 → 該群邊界失效
MIN_GROUP_PCT = 0.05           # 可執行性 (a) 最小群佔比 >= 5%
MIN_GROUP_N = 30               # 可執行性 (b) 最小群人數 >= 30
GAP_B = 200                    # 素材建議：gap-statistical-inference.md S1 修補動作 2
N_BINDING_SWITCH = MIN_GROUP_N / MIN_GROUP_PCT   # = 600，低於此恆由 (b) 綁定

_errors: list[str] = []
_warnings: list[str] = []


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


def _py(v: Any) -> Any:
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    return str(o)


# ══════════════════════════════════════════════════════════════
#  基本量：WGSS / BGSS / CH
# ══════════════════════════════════════════════════════════════
def fit(X: np.ndarray, k: int, seed: int, n_init: int) -> np.ndarray:
    from sklearn.cluster import KMeans
    return KMeans(n_clusters=k, random_state=seed, n_init=n_init).fit_predict(X)


def wgss(X: np.ndarray, labels: np.ndarray) -> float:
    """群內平方和。k=1 時等於 TSS —— Tibshirani 的 W_1 就是這個。"""
    total = 0.0
    for g in np.unique(labels):
        pts = X[labels == g]
        total += float(((pts - pts.mean(axis=0)) ** 2).sum())
    return total


def ch_index(X: np.ndarray, labels: np.ndarray) -> float:
    """CH(k) = (BGSS/(k-1)) / (WGSS/(n-k))。教材唯一給公式且可自動最大化的指標。"""
    n = X.shape[0]
    k = len(np.unique(labels))
    if k < 2 or k >= n:
        return float("nan")
    tss = float(((X - X.mean(axis=0)) ** 2).sum())
    w = wgss(X, labels)
    bgss = tss - w
    if w <= 0:
        return float("inf")
    return float((bgss / (k - 1)) / (w / (n - k)))


# ══════════════════════════════════════════════════════════════
#  ① 四個指標
# ══════════════════════════════════════════════════════════════
def indicator_table(X: np.ndarray, ks: list[int], seed: int,
                    n_init: int) -> tuple[pd.DataFrame, pd.DataFrame,
                                          dict[int, np.ndarray]]:
    """回傳 (逐 k 指標表, silhouette 剖面表, 各 k 的 labels)。"""
    from sklearn.metrics import silhouette_samples

    rows, prof_rows = [], []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in ks:
        lab = fit(X, k, seed, n_init)
        labels_by_k[k] = lab
        w = wgss(X, lab)
        row: dict[str, Any] = {"k": k, "WGSS": round(w, 4),
                               "CH": round(ch_index(X, lab), 4)}
        if k >= 2 and len(np.unique(lab)) >= 2:
            s = silhouette_samples(X, lab)
            row["silhouette平均"] = round(float(s.mean()), 4)
            worst_frac = 0.0
            for g in np.unique(lab):
                m = lab == g
                frac = float((s[m] < 0).mean())
                worst_frac = max(worst_frac, frac)
                prof_rows.append({
                    "k": k, "群": _py(g), "n": int(m.sum()),
                    "群內silhouette平均": round(float(s[m].mean()), 4),
                    "s(i)<0比例": round(frac, 4),
                    "結論": "邊界失效" if frac > SIL_NEG_FRAC_MAX else "通過",
                })
            row["最差群負值比例"] = round(worst_frac, 4)
        else:
            row["silhouette平均"] = float("nan")
            row["最差群負值比例"] = float("nan")
        rows.append(row)

    tbl = pd.DataFrame(rows)
    # 改善率(k) = (WGSS(k-1) − WGSS(k)) / WGSS(k-1) × 100%
    imp = [float("nan")]
    for i in range(1, len(tbl)):
        prev, cur = tbl["WGSS"].iloc[i - 1], tbl["WGSS"].iloc[i]
        imp.append(round((prev - cur) / prev * 100, 3) if prev > 0 else float("nan"))
    tbl["改善率%"] = imp
    return tbl, pd.DataFrame(prof_rows), labels_by_k


def pick_elbow(tbl: pd.DataFrame) -> tuple[int | None, str]:
    """改善率首次跌破 5% 的前一點。無肘部或多個肘部 → 棄權（§5.2）。"""
    imp = tbl["改善率%"].to_numpy()
    ks = tbl["k"].to_numpy()
    below = [bool(np.isfinite(v) and v < ELBOW_IMPROVE_PCT) for v in imp[1:]]
    if not below:
        return None, "候選 k 太少，算不出改善率"
    crossings = [i for i, b in enumerate(below) if b and (i == 0 or not below[i - 1])]
    if not crossings:
        return None, (f"改善率從未跌破 {ELBOW_IMPROVE_PCT:.0f}%（無肘部）"
                      f"—— WGSS 對 k 單調遞減，不能拿 WGSS 本身當「愈低愈好」的準則")
    if len(crossings) > 1:
        at = "、".join(f"k={ks[1:][i]}" for i in crossings)
        return None, (f"改善率跌破 {ELBOW_IMPROVE_PCT:.0f}% 共 {len(crossings)} 次（{at}），"
                      f"有多個肘部")
    i = crossings[0]
    k_break = int(ks[1:][i])
    prev_k = int(ks[list(ks).index(k_break) - 1])
    return prev_k, f"改善率在 k={k_break} 首次跌破 {ELBOW_IMPROVE_PCT:.0f}%，取前一點"


def pick_ch(tbl: pd.DataFrame) -> tuple[int | None, str]:
    """argmax CH。單調上升到 k_max → CH 失效（§5.2）。"""
    v = tbl["CH"].to_numpy(dtype=float)
    ks = tbl["k"].to_numpy()
    valid = np.isfinite(v)
    if valid.sum() < 2:
        return None, "可用的 CH 值不足"
    vv, kk = v[valid], ks[valid]
    if int(np.argmax(vv)) == len(vv) - 1 and bool(np.all(np.diff(vv) > 0)):
        return None, (f"CH 單調上升到 k_max={kk[-1]}，CH 失效 —— "
                      f"同時檢查是否有極端值把 BGSS 撐大")
    return int(kk[int(np.argmax(vv))]), f"CH 最大值 {vv.max():.2f}"


def pick_silhouette(tbl: pd.DataFrame) -> tuple[int | None, str]:
    v = tbl["silhouette平均"].to_numpy(dtype=float)
    ks = tbl["k"].to_numpy()
    valid = np.isfinite(v)
    if not valid.any():
        return None, "算不出 silhouette"
    vv, kk = v[valid], ks[valid]
    best = int(kk[int(np.argmax(vv))])
    s = float(vv.max())
    if s >= SIL_STRONG:
        lvl = "結構明確"
    elif s >= SIL_WEAK:
        lvl = "結構弱但可用"
    else:
        lvl = "無實質結構"
    return best, f"平均 silhouette 最高 {s:.3f}（{lvl}）"


# ══════════════════════════════════════════════════════════════
#  Gap statistic（Tibshirani）
# ══════════════════════════════════════════════════════════════
def _reference_sample(X: np.ndarray, rng: np.random.Generator,
                      kind: str) -> np.ndarray:
    """產生一份參考資料。

    uniform  各欄獨立 uniform，範圍取原始欄的 [min, max]（Tibshirani 方法 (a)）
    pca      先轉到主成分座標、在那個外框裡 uniform、再轉回來（方法 (b)）
    permute  各欄獨立打亂 —— 保留邊際分布、破壞相關結構（07 §7.4 的 (a)）
    """
    n, d = X.shape
    if kind == "permute":
        out = np.empty_like(X)
        for j in range(d):
            out[:, j] = rng.permutation(X[:, j])
        return out
    if kind == "pca":
        mu = X.mean(axis=0)
        Xc = X - mu
        _, _, vt = np.linalg.svd(Xc, full_matrices=False)
        Z = Xc @ vt.T
        lo, hi = Z.min(axis=0), Z.max(axis=0)
        Zr = rng.uniform(lo, hi, size=(n, d))
        return Zr @ vt + mu
    lo, hi = X.min(axis=0), X.max(axis=0)
    return rng.uniform(lo, hi, size=(n, d))


def gap_statistic(X: np.ndarray, ks: list[int], B: int, seed: int,
                  n_init: int, kind: str) -> pd.DataFrame:
    """Gap(k) = E*_B[log W_k] − log W_k，s_k = sd_B(log W_k)·sqrt(1+1/B)。

    sd 用 ddof=0 —— Tibshirani 原文的 sd_k 是 sqrt((1/B)Σ(logW* − 平均)²)。
    """
    rng = np.random.default_rng(seed)
    logw_ref = {k: [] for k in ks}
    for _ in range(B):
        Xr = _reference_sample(X, rng, kind)
        for k in ks:
            lab = fit(Xr, k, seed, n_init) if k > 1 else np.zeros(len(Xr), dtype=int)
            logw_ref[k].append(np.log(max(wgss(Xr, lab), 1e-300)))

    rows = []
    for k in ks:
        lab = fit(X, k, seed, n_init) if k > 1 else np.zeros(len(X), dtype=int)
        lw = float(np.log(max(wgss(X, lab), 1e-300)))
        ref = np.asarray(logw_ref[k], dtype=float)
        gap = float(ref.mean() - lw)
        sk = float(ref.std(ddof=0) * np.sqrt(1 + 1.0 / B))
        rows.append({"k": k, "log_W": round(lw, 6),
                     "參考log_W平均": round(float(ref.mean()), 6),
                     "Gap": round(gap, 6), "s_k": round(sk, 6)})
    return pd.DataFrame(rows)


def pick_gap(gap_tbl: pd.DataFrame) -> tuple[int | None, str]:
    """Tibshirani 準則：取最小的 k 使 Gap(k) >= Gap(k+1) − s_{k+1}。"""
    g = gap_tbl.sort_values("k").reset_index(drop=True)
    for i in range(len(g) - 1):
        if g["Gap"].iloc[i] >= g["Gap"].iloc[i + 1] - g["s_k"].iloc[i + 1]:
            return int(g["k"].iloc[i]), (
                f"Gap({int(g['k'].iloc[i])})={g['Gap'].iloc[i]:.4f} ≥ "
                f"Gap({int(g['k'].iloc[i + 1])})−s={g['Gap'].iloc[i + 1]:.4f}"
                f"−{g['s_k'].iloc[i + 1]:.4f}")
    return None, (f"到 k_max={int(g['k'].iloc[-1])} 都沒有滿足 Tibshirani 準則的 k "
                  f"—— Gap 一路上升，k 的上界可能取太小")


# ══════════════════════════════════════════════════════════════
#  ④ §7.4 存在性：structure_pvalue
# ══════════════════════════════════════════════════════════════
def structure_pvalue(X: np.ndarray, k: int, B: int, seed: int, n_init: int,
                     kind: str) -> dict[str, Any]:
    """實際 CH 對參考分布的位置。

    p = (1 + #{CH_ref >= CH_actual}) / (B + 1)。分子分母各加 1 是標準的
    permutation p 值修正 —— 沒有它，p 有機會是 0，而「p=0」在有限次重抽下
    是不可能成立的宣稱。
    """
    rng = np.random.default_rng(seed + 977)
    actual = ch_index(X, fit(X, k, seed, n_init))
    ref = []
    for _ in range(B):
        Xr = _reference_sample(X, rng, kind)
        ref.append(ch_index(Xr, fit(Xr, k, seed, n_init)))
    ref = np.asarray([v for v in ref if np.isfinite(v)], dtype=float)
    ge = int((ref >= actual).sum())
    p = (1 + ge) / (len(ref) + 1)
    return {"參考類型": kind, "k": k, "實際CH": round(float(actual), 4),
            "參考CH平均": round(float(ref.mean()), 4),
            "參考CH第95百分位": round(float(np.percentile(ref, 95)), 4),
            "B": int(len(ref)), "structure_pvalue": round(float(p), 6),
            "結論": "有群結構證據" if p < 0.05 else "無法主張有群結構"}


# ══════════════════════════════════════════════════════════════
#  ③ §5.3 可執行性
# ══════════════════════════════════════════════════════════════
def executability(X: np.ndarray, ks: list[int], seed: int,
                  n_init: int) -> pd.DataFrame:
    n = X.shape[0]
    need_a = MIN_GROUP_PCT * n
    need = max(need_a, MIN_GROUP_N)
    binding = "(b) 最小群人數 ≥ 30" if need_a < MIN_GROUP_N else "(a) 最小群佔比 ≥ 5%"
    rows = []
    for k in ks:
        if k < 2:
            continue
        lab = fit(X, k, seed, n_init)
        sizes = pd.Series(lab).value_counts()
        mn = int(sizes.min())
        rows.append({
            "k": k, "最小群人數": mn, "最小群佔比%": round(mn / n * 100, 2),
            "門檻人數": round(need, 1), "綁定條件": binding,
            "結論": "通過" if mn >= need else "不通過",
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════
#  ② §5.2 仲裁表
# ══════════════════════════════════════════════════════════════
def arbitrate(elbow: int | None, ch: int | None, sil: int | None,
              gap: int | None) -> dict[str, Any]:
    """§5.2 的六條規則，順序是硬的。回傳 {判定, 動作, k候選, level}。"""
    # 「停」的兩條先判 —— 它們代表上游沒做好，後面的仲裁沒有意義
    if gap == 1:
        return {"判定": "gap 的最佳 k = 1：這批資料可能沒有群結構",
                "動作": "不要硬分。走 07 §六 的 HDBSCAN 交叉比對，"
                        "並準備誠實說明（§6.2 情況 B）",
                "k候選": [], "level": "error"}
    if sil is not None and gap is not None and abs(sil - gap) >= 2:
        return {"判定": f"silhouette(k={sil}) 與 gap(k={gap}) 相差 {abs(sil - gap)} ≥ 2",
                "動作": "停。這是尺度或轉換沒做好的訊號 —— 回 07 §3.3 檢查 "
                        "WGSS 貢獻表。單一變數 > 70% 時三指標必然打架",
                "k候選": [], "level": "error"}

    votes = {"Elbow": elbow, "CH": ch, "silhouette": sil, "gap": gap}
    live = {name: v for name, v in votes.items() if v is not None}
    notes = []
    if elbow is None:
        notes.append("Elbow 棄權，不算一票")
    if ch is None:
        notes.append("CH 失效，忽略")

    if len(set(live.values())) == 1 and len(live) >= 3:
        k = next(iter(live.values()))
        return {"判定": f"指標指向同一個 k={k}（罕見）",
                "動作": "直接採用，但仍要走 §5.3 的後三步",
                "k候選": [k], "level": "ok", "備註": notes}

    if sil is not None and gap is not None and abs(sil - gap) == 1:
        k = min(sil, gap)
        return {"判定": f"silhouette(k={sil}) 與 gap(k={gap}) 相差 1",
                "動作": f"取小的那個 k={k} —— 群少比群多安全，"
                        f"群多的代價是行銷團隊做不出這麼多套素材",
                "k候選": [k], "level": "ok", "備註": notes}

    cands = sorted(set(live.values()))
    return {"判定": "指標不一致且不落在 §5.2 的具名情況",
            "動作": "以 silhouette 與 gap 為主，把候選集合帶進 §5.3 第 ② 步"
                    "用產業知識收斂（教材：先驗知識是三種方法裡最好的一種，"
                    "且 K 要反映業務需求，不能純粹靠數學）",
            "k候選": cands, "level": "warning", "備註": notes}


# ══════════════════════════════════════════════════════════════
def load_matrix(p: Any, explicit: Path | None) -> tuple[pd.DataFrame, Path]:
    path = explicit or (p.models / "cluster_matrix.parquet")
    if not path.exists():
        raise FileNotFoundError(
            f"找不到分群矩陣：{path}\n"
            f"  先跑 prep_cluster_matrix.py <專案>，或用 --matrix 指定路徑。")
    df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
          else pd.read_csv(path))
    return df, path


def parse_k_range(s: str) -> list[int]:
    if "-" not in s:
        raise ValueError(f"--k-range 要寫成 2-8 這種形式，收到 {s!r}")
    a, b = s.split("-", 1)
    lo, hi = int(a), int(b)
    if lo < 2 or hi <= lo:
        raise ValueError(f"--k-range 下界要 ≥2 且上界要大於下界，收到 {s!r}")
    return list(range(lo, hi + 1))


def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    df, mpath = load_matrix(p, args.matrix)

    id_like = {"客戶編號", "customer_id", "cust_id", "id"}
    cols = [c for c in df.columns
            if pd.api.types.is_numeric_dtype(df[c])
            and str(c).lower() not in id_like and not str(c).lower().endswith("_id")]
    X = df[cols].astype(float).to_numpy()
    if np.isnan(X).any():
        raise ValueError(
            f"矩陣有缺值。K-Means 不吃 NaN —— prep_cluster_matrix.py 會把缺值列"
            f"移到 隔離區/ 並在報告交代（18-E22）。先跑它，不要在這裡補值。")

    n = X.shape[0]
    ks = parse_k_range(args.k_range)
    if max(ks) >= n:
        raise ValueError(f"k 上界 {max(ks)} 不小於樣本數 {n}")

    seed, n_init = args.seed, args.n_init
    spec_path = p.models / "cluster_spec.json"
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            seed = int(spec.get("seed", seed))
            n_init = int(spec.get("n_init", n_init))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass

    print("=" * 72)
    print("行銷數據分析 Skill — k 的選擇（07 §五）＋ 分群存在性（§7.4）")
    print(f"專案：{args.project}｜矩陣：{mpath.name}"
          f"（{n:,} 列 × {len(cols)} 欄）｜k 範圍 {ks[0]}–{ks[-1]}")
    print(f"seed={seed}、n_init={n_init}、gap B={args.B}、"
          f"gap 參考分布={args.gap_reference}")
    print("=" * 72)

    # ① 四指標
    print("\n① 四個指標（07 §5.1）")
    tbl, prof, _ = indicator_table(X, ks, seed, n_init)
    # 用欄名取值。itertuples 會把「改善率%」這種含符號的欄名改成位置代號
    # （_5 / _6），欄序一動就對到別欄 —— 那是靜默錯誤，不是報錯。
    for _, r in tbl.iterrows():
        imp = "—" if not np.isfinite(r["改善率%"]) else f"{r['改善率%']:+.2f}%"
        sv = r["silhouette平均"]
        sil = "—" if not np.isfinite(sv) else f"{sv:.3f}"
        detail(f"k={int(r['k'])}｜WGSS {r['WGSS']:>12,.2f}｜改善率 {imp:>8}｜"
               f"CH {r['CH']:8.2f}｜silhouette {sil}")

    elbow, elbow_why = pick_elbow(tbl)
    ch, ch_why = pick_ch(tbl)
    sil, sil_why = pick_silhouette(tbl)

    print("\n② Gap statistic（Tibshirani；k 從 1 起算才判得出「沒有群結構」）")
    gap_tbl = gap_statistic(X, [1] + ks, args.B, seed, n_init, args.gap_reference)
    for _, r in gap_tbl.iterrows():
        detail(f"k={int(r['k'])}｜Gap {r['Gap']:+.4f}｜s_k {r['s_k']:.4f}")
    gap, gap_why = pick_gap(gap_tbl)

    print("\n各指標的票：")
    for name, k, why in (("Elbow", elbow, elbow_why), ("CH", ch, ch_why),
                         ("silhouette", sil, sil_why), ("gap", gap, gap_why)):
        detail(f"{name:<11}{'棄權' if k is None else f'k={k}':<8}{why}")
    if elbow is None:
        warn(f"Elbow 棄權：{elbow_why}",
             "用 silhouette + gap 兩票。教材對此有先例：DBSCAN 的 k-distance 圖"
             "「曲線可能有多個較明顯的肘部，需要領域知識判斷」，同一個病理")
    if ch is None:
        warn(f"CH 失效：{ch_why}", "忽略 CH，用 silhouette + gap")

    # silhouette 剖面 —— 只看 s̄ 不看剖面圖等於沒看（07 §5.1）
    print("\n③ silhouette 剖面（只看平均值等於沒看）")
    if len(prof):
        bad = prof[prof["結論"] == "邊界失效"]
        if len(bad):
            for _, r in bad.iterrows():
                detail(f"k={int(r['k'])} 的群 {r['群']}（n={int(r['n'])}）"
                       f"有 {r['s(i)<0比例']:.1%} 的成員 s(i)<0")
            warn(f"{len(bad)} 個 (k, 群) 組合的邊界失效"
                 f"（> {SIL_NEG_FRAC_MAX:.0%} 的成員 s(i)<0）",
                 "平均值會被大群蓋過。這些群的成員比較接近隔壁群 —— "
                 "採用該 k 時，這幾群不可當成行銷名單直接發送")
        else:
            ok(f"各 (k, 群) 的負值比例皆 ≤ {SIL_NEG_FRAC_MAX:.0%}")
    if sil is not None:
        s_best = float(tbl.loc[tbl["k"] == sil, "silhouette平均"].iloc[0])
        if s_best < SIL_WEAK:
            warn(f"最佳 k 的平均 silhouette 僅 {s_best:.3f} < {SIL_WEAK}（無實質結構）",
                 "先看 §7.4 的 structure_pvalue 再決定要不要分群。"
                 "structure_pvalue 不顯著就不要硬分")

    # ④ 仲裁
    print("\n④ §5.2 仲裁（不一致是常態，規則是硬的）")
    verdict = arbitrate(elbow, ch, sil, gap)
    print(f"  判定：{verdict['判定']}")
    print(f"  動作：{verdict['動作']}")
    for nte in verdict.get("備註", []):
        detail(nte)
    if verdict["level"] == "error":
        err(verdict["判定"], verdict["動作"])
    elif verdict["level"] == "warning":
        warn(verdict["判定"], verdict["動作"])
    else:
        ok(f"候選 k = {verdict['k候選']}")

    # ⑤ 可執行性
    print("\n⑤ §5.3 第 ③ 步 可執行性檢驗")
    ex = executability(X, ks, seed, n_init)
    binding = ex["綁定條件"].iloc[0] if len(ex) else "—"
    detail(f"門檻 = max(0.05×{n}, {MIN_GROUP_N}) = {max(MIN_GROUP_PCT * n, MIN_GROUP_N):.1f} 人"
           f"，本次由 {binding} 綁定"
           + (f"（n < {N_BINDING_SWITCH:.0f} 時恆由 (b) 綁定，不要只驗 (a)）"
              if n < N_BINDING_SWITCH else ""))
    for _, r in ex.iterrows():
        detail(f"k={int(r['k'])}｜最小群 {int(r['最小群人數'])} 人"
               f"（{r['最小群佔比%']:.1f}%）｜{r['結論']}")
    cand = verdict["k候選"]
    failing = [int(r["k"]) for _, r in ex.iterrows()
               if r["結論"] == "不通過" and int(r["k"]) in cand]
    if failing:
        warn(f"候選 k={failing} 的最小群不足 {max(MIN_GROUP_PCT * n, MIN_GROUP_N):.0f} 人",
             "§5.3 第 ③ 步：與最近的群合併，k 減 1，回到第 ① 步。"
             "實證：期末報告 k=4 的最小群只有 5 人，年齡與地區的 F 值整格填「—」，"
             "決策建議從 3 條降為 2 條 —— 少掉的正是「某某檢定顯示 X，因此建議 Y」，"
             "而那一條是統計章存在的唯一理由")

    # ⑥ 存在性
    print("\n⑥ §7.4 分群存在性 —— 唯一可寫進報告當「分群有效性」的數字")
    k_for_sp = (cand[0] if cand else (sil or gap or ks[0]))
    sp_rows = [structure_pvalue(X, k_for_sp, args.B, seed, n_init, kind)
               for kind in ("permute", "uniform")]
    for r in sp_rows:
        lbl = ("各欄獨立打亂（保留邊際分布、破壞相關結構）" if r["參考類型"] == "permute"
               else "uniform hypercube（連邊際分布也不保留）")
        detail(f"{lbl}：實際 CH {r['實際CH']:.2f} vs 參考平均 {r['參考CH平均']:.2f}"
               f"（第95百分位 {r['參考CH第95百分位']:.2f}）"
               f"→ structure_pvalue = {r['structure_pvalue']:.4f}")
    strict = next(r for r in sp_rows if r["參考類型"] == "permute")
    if strict["structure_pvalue"] >= 0.05:
        warn(f"打亂參考下 structure_pvalue = {strict['structure_pvalue']:.4f} ≥ 0.05，"
             f"無法主張這批資料有群結構",
             "群可以照分、輪廓可以照描述，但報告**不准寫「分群結果具備統計效力」**。"
             "§八 的 ANOVA p 值不能拿來補這個洞（S1 循環推論，見 07 §8.2）。"
             "考慮走 §六 的 HDBSCAN 交叉比對")
    else:
        ok(f"打亂參考下 structure_pvalue = {strict['structure_pvalue']:.4f} < 0.05 → 有群結構證據")

    # 收斂
    print("\n" + "=" * 72)
    n_err, n_warn = len(_errors), len(_warnings)
    print(f"error {n_err}、warning {n_warn}")
    if n_err:
        print("結果：⛔ §5.2 判定要停 → 不要往下選 k，先回上游。")
    elif n_warn:
        print(f"結果：⚠ 候選 k = {cand or '（見上）'}，可往下但報告要逐條回應警告。")
    else:
        print(f"結果：✅ 候選 k = {cand}，四指標與可執行性皆無異狀。")
    print("      提醒：§5.3 還有第 ②（產業知識收斂）、④（命名四件套）、"
          "⑤（命名盲測）三步，那三步不是這支腳本能代勞的。")

    if not args.no_write:
        d = p.tables / "分群輪廓"
        d.mkdir(parents=True, exist_ok=True)
        tbl.to_csv(d / "k選擇_四指標.csv", index=False, encoding="utf-8-sig")
        prof.to_csv(d / "k選擇_silhouette剖面.csv", index=False, encoding="utf-8-sig")
        ex.to_csv(d / "k選擇_可執行性.csv", index=False, encoding="utf-8-sig")
        gap_tbl.to_csv(d / "k選擇_gap.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(sp_rows).to_csv(d / "分群存在性_structure_pvalue.csv",
                                     index=False, encoding="utf-8-sig")
        print(f"\n✓ 統計表已寫入：{d}")

        jp = p.models / "cluster_validity.json"
        jp.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project, "matrix": str(mpath),
            "n_rows": int(n), "input_vars": cols,
            "k_range": ks, "seed": seed, "n_init": n_init,
            "gap": {"B": args.B, "參考分布": args.gap_reference,
                    "說明": "參考分布的產生方式會改結果，必須記進 cluster_spec.json（07 §5.1）"},
            "votes": {"Elbow": elbow, "CH": ch, "silhouette": sil, "gap": gap},
            "vote_reasons": {"Elbow": elbow_why, "CH": ch_why,
                             "silhouette": sil_why, "gap": gap_why},
            "仲裁": verdict,
            "structure_pvalue": sp_rows,
            "可執行性": ex.to_dict("records"),
            "errors": _errors, "warnings": _warnings,
        }, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        print(f"✓ 機器可讀結果：{jp}")

        if spec_path.exists() and not args.no_spec_update:
            try:
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                spec["gap_reference"] = args.gap_reference
                spec["gap_B"] = args.B
                spec["k_selection"] = {"votes": {"Elbow": elbow, "CH": ch,
                                                 "silhouette": sil, "gap": gap},
                                       "仲裁": verdict["判定"],
                                       "候選": verdict["k候選"]}
                spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
                print(f"✓ 已回填 cluster_spec.json 的 gap_reference / k_selection")
            except (json.JSONDecodeError, OSError):
                warn("cluster_spec.json 回填失敗", "手動把 gap_reference 記進去（07 §5.1）")

    if n_err:
        return EX_ERROR
    return EX_WARN if n_warn else EX_OK


# ══════════════════════════════════════════════════════════════
def _selftest() -> int:
    print("=" * 72)
    print("cluster_validity.py 自我測試")
    print("=" * 72)
    rng = np.random.default_rng(20260727)
    failed = []

    def check(name: str, cond: bool, got: str = "") -> None:
        print(("  ✓ " if cond else "  ✗ ") + name + (f"（{got}）" if got else ""))
        if not cond:
            failed.append(name)

    ks = [2, 3, 4, 5, 6]

    # ① 三團明確分開的資料 → silhouette 應該指到 3
    centers = np.array([[0, 0], [12, 0], [6, 11]], dtype=float)
    X3 = np.vstack([c + rng.normal(0, 1.0, (120, 2)) for c in centers])
    tbl3, prof3, _ = indicator_table(X3, ks, 42, 10)
    s3, _ = pick_silhouette(tbl3)
    check("三團資料的 silhouette 指到 k=3", s3 == 3, f"k={s3}")
    ch3, _ = pick_ch(tbl3)
    check("三團資料的 CH 指到 k=3", ch3 == 3, f"k={ch3}")

    # ② 純噪音 → gap 的最佳 k 應該是 1（§5.2「不要硬分」那一列）
    Xn = rng.normal(0, 1, (200, 3))
    g_noise = gap_statistic(Xn, [1, 2, 3, 4], 40, 42, 5, "uniform")
    gk, _ = pick_gap(g_noise)
    check("純噪音的 gap 判到 k=1", gk == 1, f"k={gk}")
    v = arbitrate(None, 2, 2, 1)
    check("gap=1 觸發 error 而不是往下選 k",
          v["level"] == "error" and "沒有群結構" in v["判定"])

    # ③ structure_pvalue：純噪音不顯著、真有結構顯著
    sp_noise = structure_pvalue(Xn, 3, 60, 42, 5, "permute")
    check("純噪音的 structure_pvalue 不顯著",
          sp_noise["structure_pvalue"] >= 0.05,
          f"p={sp_noise['structure_pvalue']:.4f}")
    sp_real = structure_pvalue(X3, 3, 60, 42, 5, "permute")
    check("真有結構時 structure_pvalue 顯著",
          sp_real["structure_pvalue"] < 0.05, f"p={sp_real['structure_pvalue']:.4f}")
    check("structure_pvalue 永遠 > 0（有限重抽下 p=0 是不可能的宣稱）",
          sp_noise["structure_pvalue"] > 0 and sp_real["structure_pvalue"] > 0,
          f"最小 {min(sp_noise['structure_pvalue'], sp_real['structure_pvalue']):.6f}")

    # ④ 仲裁表逐條
    v = arbitrate(4, 4, 2, 5)
    check("silhouette 與 gap 差 ≥2 → 停",
          v["level"] == "error" and "尺度或轉換" in v["動作"], v["判定"])
    v = arbitrate(3, 3, 3, 4)
    check("silhouette 與 gap 差 1 → 取小的",
          v["k候選"] == [3], f"候選={v['k候選']}")
    v = arbitrate(4, 4, 4, 4)
    check("四者一致 → 直接採用", v["k候選"] == [4] and v["level"] == "ok")
    v = arbitrate(None, None, 3, 3)
    check("Elbow 棄權 + CH 失效仍可用 silhouette+gap 兩票",
          v["k候選"] == [3] and len(v.get("備註", [])) == 2, str(v.get("備註")))

    # ⑤ Elbow 棄權的兩種病理
    e, why = pick_elbow(pd.DataFrame({"k": ks, "WGSS": [100, 90, 81, 73, 66],
                                      "改善率%": [np.nan, 10.0, 10.0, 9.9, 9.6]}))
    check("改善率從未跌破 5% → 無肘部，棄權", e is None and "無肘部" in why, why)
    e, why = pick_elbow(pd.DataFrame({"k": ks, "WGSS": [100, 96, 80, 77, 60],
                                      "改善率%": [np.nan, 4.0, 16.7, 3.8, 22.1]}))
    check("跌破 5% 兩次 → 多個肘部，棄權", e is None and "多個肘部" in why, why)
    e, why = pick_elbow(pd.DataFrame({"k": ks, "WGSS": [100, 60, 40, 38.5, 37.5],
                                      "改善率%": [np.nan, 40.0, 33.3, 3.75, 2.6]}))
    check("單一肘部 → 取跌破那點的前一點 k=4", e == 4, f"k={e}")

    # ⑥ 可執行性：n<600 時必須由「30 人」綁定
    ex = executability(X3, [2, 3], 42, 10)
    check("n=360 < 600 → 由 (b) 30 人綁定",
          all("(b)" in b for b in ex["綁定條件"]), ex["綁定條件"].iloc[0])
    Xbig = np.vstack([c + rng.normal(0, 1.0, (300, 2)) for c in centers])
    exb = executability(Xbig, [3], 42, 10)
    check("n=900 ≥ 600 → 改由 (a) 5% 綁定",
          "(a)" in exb["綁定條件"].iloc[0], exb["綁定條件"].iloc[0])

    # ⑦ CH 單調上升 → 失效
    c_mono, why = pick_ch(pd.DataFrame({"k": ks, "CH": [10.0, 20.0, 30.0, 40.0, 50.0]}))
    check("CH 單調上升到 k_max → 失效", c_mono is None and "CH 失效" in why, why)

    # ⑧ 序列化
    try:
        json.dumps({"仲裁": arbitrate(3, 3, 3, 4), "sp": sp_real,
                    "ex": ex.to_dict("records")},
                   ensure_ascii=False, default=_json_default)
        ser = True
    except TypeError as e:
        ser = False
        print(f"      {e}")
    check("結果可寫成 JSON", ser)

    print("\n" + "=" * 72)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


def main() -> int:
    ap = GateArgumentParser(
        description="k 的選擇（07 §五）與分群存在性（§7.4）")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--matrix", type=Path,
                    help="分群矩陣（預設 模型輸出/cluster_matrix.parquet）")
    ap.add_argument("--k-range", default="2-8", help="k 的搜尋範圍，如 2-8")
    ap.add_argument("--B", type=int, default=GAP_B,
                    help=f"gap 與 structure_pvalue 的重抽次數（預設 {GAP_B}）")
    ap.add_argument("--gap-reference", choices=("uniform", "pca"), default="uniform",
                    help="gap 的參考分布產生方式。會改結果，所以寫進 cluster_spec.json")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-init", type=int, default=10)
    ap.add_argument("--no-write", action="store_true", help="只算，不寫檔")
    ap.add_argument("--no-spec-update", action="store_true",
                    help="不回填 cluster_spec.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")
    if args.B < 20:
        ap.error(f"--B 至少 20（收到 {args.B}）；素材建議值是 {GAP_B}")
    try:
        parse_k_range(args.k_range)
    except ValueError as e:
        # 值的格式不合法 = 命令列打錯 → 64。掉到 run() 裡會被判成 1
        #（資料側問題），而這裡根本還沒碰到資料。
        ap.error(str(e))

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
        print(f"⛔ cluster_validity.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
