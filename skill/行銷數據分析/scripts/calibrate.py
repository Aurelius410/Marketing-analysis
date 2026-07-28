#!/usr/bin/env python3
"""
機率校準（12 §三）—— Platt scaling／Isotonic regression、校準曲線、Brier／ECE。

這一節是 M9 與 M11（決策轉譯）之間的橋。12 §三 開宗明義：**不做它，M11 的所有
sizing 都是錯的**。XGBoost 吐的 0.7 不是「這位顧客有 70% 會買」，拿去乘客單價
算期望營收會系統性高估，而且高估的方向剛好落在你最捨得花錢的那批人身上
（§三 的示意：最高分箱輸出 0.70、實際 0.42，一檔活動高估 168,000 元）。
**AUC 管排序，校準管刻度，兩者互相看不見對方的錯**（§三 原話）。

本腳本大半的價值在第一部分，不在第二部分
─────────────────────────────────────────────
12 §三：「**校準必須在獨立的校準集上做。** 用訓練集校準等於用模型已經記住的
樣本去修正模型的自信 —— 修完看起來完美，上線照樣高估。」

這句話如果只寫在文件裡，它會被違反 —— 因為違反它的成本是零、而且**跑出來的
數字更好看**（在訓練集上校準，Brier 與 ECE 都會漂亮得多）。所以本腳本把它變成
七道會擋人的關（S1–S7），任何一道判 error 就**完全不做校準、不寫校準後分數**，
退 1。不是印個警告然後照樣把校準後的分數交出去 —— 那個檔案會被 M11 拿去乘金額。

  S1 三份切分齊全      缺 calib → error；缺 test → error（見下）；缺 train → 這道沒驗到
  S2 校準集 ∩ 訓練集   有交集 → error（§三：用訓練集校準等於沒校準）
  S3 校準集 ∩ 測試集   有交集 → error（校準前後對照會變成自己評自己）
  S4 訓練集 ∩ 測試集   有交集 → error（§二：out-of-time 評估失效）
  S5 時間順序          §三：「有時間結構時，三份必須依時間先後排列」→ 亂序 error
  S6 分布未被動過      §四：「校準集與測試集保持原始分布」，重抽樣只能在訓練集做
  S7 校準集規模        §三 的樣本量表：<1,000 傾向 Platt；每箱 <30 標 N/A

**為什麼「缺 test」也是 error**：校準前後的對照如果落在校準集自己身上，那是
「用同一批資料學映射、再用同一批資料證明映射有效」—— 恆定變好，證明不了任何
事。這與 07 §8.2 的 S1 循環推論是同一個病。所以三份缺一不可，本腳本不提供
繞過的旗標。

第二部分：校準（§三 的判準，沒有一條是本腳本自己發明的）
─────────────────────────────────────────────
  · Platt（sigmoid）與 Isotonic（保序）**兩種都跑**，比 Brier 與校準斜率，
    選贏的那個並記錄理由（§三 註：這是 00 §1.4「參數必附理由」的要求）
  · 校準曲線用**等頻分箱**（§三 程式碼 `np.quantile`，不是等寬），10 箱
  · 每箱樣本 <30 → 標 `N/A`，不畫也不進斜率迴歸（§三 表最後一列 + 00 §四）
  · 校準斜率＝分箱點對 45 度線的迴歸係數，理想 1.0；|斜率−1| > 0.15 →
    §十 的告警規則：「只重做校準，不必重訓全模型」
  · 曲線長相照 §三 的表判讀（系統性高估／低估／S 形／反 S／中段反轉）

Platt 套在 logit 上，不是套在 p 上
─────────────────────────────────────────────
§三 表格寫的是「對 **logit** 套一條兩參數 sigmoid」，本腳本照這個做
（`--platt-input logit`，預設）。要注意 sklearn 的 `CalibratedClassifierCV`
實際上是把 sigmoid 套在 `_get_response_values` 拿到的東西上：base 有
`decision_function`（LogisticRegression、SVM）時那就是 logit，兩者一致；
但 base 只有 `predict_proba`（XGBoost、RandomForest —— 也就是 §一 的主力）時，
sklearn 是**直接對 p 擬合**，與 §三 的文字不同。差別在能修的形狀族不同，
不是誰對誰錯。要複製 sklearn 在樹模型上的行為就給 `--platt-input raw`。
自我測試第 ⑫ 項用 LogisticRegression 當 base，把本腳本的 logit 版與
`CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid")` 對跑，
確認兩條路徑吐出同一組機率（00 §1.3 雙路徑驗算）。

用法：
    # 預測結果表要有：分數欄、標籤欄、切分欄（train/calib/test）
    python calibrate.py 2026Q3_電商
    python calibrate.py 2026Q3_電商 --pred 模型輸出/predictions.parquet \\
        --score-col 預測機率 --label-col 實際標籤 --split-col 切分 \\
        --id-col 客戶編號 --time-col as_of --pop-rate 0.04 --title 流失模型
    python calibrate.py --self-test

輸入表的最小長相（一列一個受評對象）：
    客戶編號 | 預測機率 | 實際標籤 | 切分  | as_of
    A0871   | 0.83     | 1        | calib | 2012-06-30

輸出：
    統計表/預測模型/表11.1_校準前後.csv     餵 ref 19 表 11.1 的 Brier／校準斜率兩欄
    統計表/預測模型/校準曲線_分箱.csv       逐方法逐箱（<30 筆標 N/A）
    統計表/預測模型/校準_切分獨立性.csv     S1–S7 逐關結果
    圖表/預測模型/M9_<主題>_calibration.png ref 19 §1.7 八圖之一（10 分箱＋45 度線）
    模型輸出/calibrated_scores.parquet      校準後分數，M11 要用的就是這個
    模型輸出/calibrate.json                 含校準器參數，可重放

三桶 + 退出碼（全庫統一，權威定義見 references/00_通則與紀律.md §八）：
    0  = 切分乾淨、校準後 |斜率−1| ≤ 0.15 且 ECE 有下降 → M11 可以拿去乘金額
    1  = 有 error 擋住（切分不獨立／缺切分／分數不是機率）—— 不產出校準後分數
    2  = 只有 warning，可往下但報告要逐條寫明（§五 Step 4：只排序就不必校準）
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
from paths import cfg, project_dir  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 門檻。出處逐條標在後面，不要在這裡調 ──────────────────────
DEFAULT_BINS = 10        # 12 §三 程式碼 n_bins=10；ref 19 §1.7「10 分箱＋45 度線」
MIN_BIN_N = 30           # 12 §三 表末列：每箱 <30「點在跳」→ 標 N/A（00 §四）
ISO_MIN_N = 1000         # 12 §三 表：isotonic 建議 ≥1,000（【推導，待驗證】）
RARE_POS_RATE = 0.05     # 12 §三 表：正類稀有 <5% 選 Platt
SLOPE_TOL = 0.15         # 12 §十 告警：|calib_slope − 1| > 0.15 → 重做校準
POP_RATE_TOL = 0.005     # 12 §四 的 assert：|y_test.mean() − 母體率| < 0.005
HIGH_SCORE_EDGE = 0.6    # 12 §三 表：「0.6 以上完全沒有點」→ 該區只准排序
NEAR_UNIQUE_RATIO = 0.5  # 12 §七：nunique/n > 0.5 視為接近唯一（此處借來判「重複列是巧合還是複製」）

# 分箱點是否「顯著」偏離 45 度線：用二項標準誤的 ±2 倍。
# 為什麼不是一個固定的百分點：小箱的抖動本來就大，用固定值會把 30 人的箱
# 一律判成偏離。se 用「若已校準」的預測值算（虛無假設下的變異）。
SE_K = 2.0
# S6 母體率比對：§四 那句 assert 的 0.005 是給大測試集寫的。n=500、母體率 4%
# 時，純抽樣造成 |x̄−p|>0.005 的機率就有 ~57%（本檔自我測試 ⑬ 實跑量到 0.5686），
# 直接照抄會把乾淨的切分判成 error。所以：超過 0.005 **且**超過 3 個標準誤才判
# error，只超過 0.005 判 warning 並講明是抽樣誤差可解釋的範圍。
POP_RATE_SE_K = 3.0

_errors: list[str] = []
_warnings: list[str] = []
_infos: list[str] = []

TRAIN_ALIASES = {"train", "training", "tr", "訓練", "訓練集"}
CALIB_ALIASES = {"calib", "calibration", "cal", "校準", "校準集", "校正", "校正集"}
TEST_ALIASES = {"test", "testing", "oot", "out_of_time", "holdout",
                "測試", "測試集", "保留集"}

SCORE_CANDIDATES = ["預測機率", "預測分數", "score", "y_score", "prob",
                    "probability", "p_hat", "pred", "prediction"]
LABEL_CANDIDATES = ["實際標籤", "標籤", "實際", "y", "y_true", "label",
                    "target", "actual"]
SPLIT_CANDIDATES = ["切分", "split", "set", "dataset", "資料集", "分割"]
ID_CANDIDATES = ["客戶編號", "客戶ID", "customer_id", "cust_id", "id"]
TIME_CANDIDATES = ["as_of", "as_of_date", "資料截止日", "觀測日", "日期"]


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
    _errors.clear()
    _warnings.clear()
    _infos.clear()


def _py(v: Any) -> Any:
    """numpy 純量 → 原生 Python 型別。

    分箱人數、正類數這些都來自 numpy（int64），一路帶進結果 dict 之後
    json.dumps 才丟 TypeError —— 而且是在校準全跑完、CSV 都寫好之後才炸，
    退出碼 70 會蓋掉前面全綠的結論。在來源轉掉。
    """
    return v.item() if hasattr(v, "item") else v


def _json_default(o: Any) -> Any:
    """兜底：日後新增欄位又漏了 numpy 型別時，讓它存成而不是讓整支腳本掛掉。"""
    if hasattr(o, "item"):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Series)):
        return [_json_default(x) for x in o.tolist()]
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    return str(o)


def fmt(v: Any, nd: int = 4) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float) and not np.isfinite(v):
        return "N/A"
    return f"{v:.{nd}f}"


# ══════════════════════════════════════════════════════════════
#  基本量
# ══════════════════════════════════════════════════════════════
def expit(z: np.ndarray) -> np.ndarray:
    """數值穩定的 sigmoid。z 很負時 exp(-z) 會 overflow，分兩支寫。"""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def logit(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """log(p/(1-p))。夾在 [eps, 1-eps]：模型吐 0 或 1 是常態（樹模型的葉子），
    不夾就會得到 ±inf，整條校準線報廢。eps 取 1e-12 讓 logit 範圍到 ±27.6，
    足以容納任何真實模型的自信程度，又不會把有限值改動到看得出來。"""
    p = np.clip(np.asarray(p, dtype=float), eps, 1.0 - eps)
    return np.log(p / (1.0 - p))


def brier_score(y: np.ndarray, p: np.ndarray) -> float:
    """Brier = mean((p − y)^2)。ref 19 表 11.1 的「Brier」欄就是這個。"""
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def roc_auc(y: np.ndarray, p: np.ndarray) -> float | None:
    """單類別時 AUC 無定義 —— 回 None 讓上層標 N/A，不要回 0.5 假裝算得出來。"""
    y = np.asarray(y)
    if len(np.unique(y)) < 2:
        return None
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p))


# ══════════════════════════════════════════════════════════════
#  校準曲線：等頻分箱（12 §三）
# ══════════════════════════════════════════════════════════════
def calibration_table(y: np.ndarray, p: np.ndarray,
                      n_bins: int = DEFAULT_BINS,
                      min_bin_n: int = MIN_BIN_N) -> pd.DataFrame:
    """等頻分箱的校準曲線表。12 §三：「等頻分箱，不用等寬」。

    與 §三 的示範程式碼有一處刻意不同：它每個箱都用 `(p >= lo) & (p <= hi)`，
    兩端都閉 —— 剛好落在內部邊界上的樣本會**同時屬於相鄰兩箱**，被計算兩次。
    分數有大量重複值時（樹模型的葉子機率、NTILE 分數）這不是理論問題而是常態。
    本函式改用 [lo, hi) 逐箱、最後一箱閉右端，總人數保證等於 n。
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    n = p.size

    edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
    if edges.size < 2:
        # 所有分數都一樣（常數預測）。仍要給一列，否則後面判不出「沒有鑑別度」。
        edges = np.array([p[0], p[0] + 1e-12])
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, edges.size - 2)

    rows: list[dict[str, Any]] = []
    for b in range(edges.size - 1):
        m = idx == b
        cnt = int(m.sum())
        row: dict[str, Any] = {
            "箱": b + 1,
            "下界": round(float(edges[b]), 6),
            "上界": round(float(edges[b + 1]), 6),
            "人數": cnt,
        }
        if cnt == 0:
            row.update({"預測均值": None, "實際發生率": None, "差": None,
                        "標準誤": None, "結論": "N/A（空箱）"})
            rows.append(row)
            continue
        pm = float(p[m].mean())
        om = float(y[m].mean())
        se = float(np.sqrt(max(pm * (1 - pm), 0.0) / cnt))
        if cnt < min_bin_n:
            # 12 §三 表末列 + 00 §四：有樣本但算不出可信值 → N/A，不是 0
            row.update({"預測均值": round(pm, 6), "實際發生率": None,
                        "差": None, "標準誤": round(se, 6),
                        "結論": f"N/A（人數 {cnt} < {min_bin_n}）"})
        else:
            d = om - pm
            row.update({"預測均值": round(pm, 6), "實際發生率": round(om, 6),
                        "差": round(d, 6), "標準誤": round(se, 6),
                        "結論": "在 45 度線上" if abs(d) <= SE_K * se
                        else ("實際高於預測（低估）" if d > 0 else "實際低於預測（高估）")})
        rows.append(row)
    return pd.DataFrame(rows)


def valid_bins(tbl: pd.DataFrame) -> pd.DataFrame:
    """只留下人數 ≥ MIN_BIN_N 的箱 —— N/A 箱不進斜率迴歸也不進形狀判讀。"""
    return tbl[tbl["實際發生率"].notna()].copy()


def ece(y: np.ndarray, p: np.ndarray, tbl: pd.DataFrame) -> tuple[float, float | None]:
    """Expected Calibration Error＝Σ (n_i/n)·|實際_i − 預測_i|，等頻分箱。

    **12 沒有定義 ECE**（§三 只點名 Brier 與校準斜率），這是本腳本補的。
    補它的理由：Brier 同時含鑑別度與校準度，模型變準（AUC 上升）Brier 也會下降，
    單看它分不出「校準有沒有改善」；ECE 只量刻度。分箱方式沿用 §三 的等頻 10 箱，
    不另立一套。

    回兩個數：
      · 全箱加權（headline）—— 小箱雖然標 N/A 不畫，但把它們的樣本丟掉會讓
        ECE 系統性偏低（丟掉的往往正是最抖的那一端）。
      · 有效箱加權（人數 ≥30，權重重新歸一）—— 與圖上畫得出來的點一致。
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    n = p.size
    if n == 0:
        return float("nan"), None

    # 全箱：用與 tbl 相同的邊界重算（tbl 對小箱的 實際發生率 是 None）
    edges = np.unique(np.quantile(p, np.linspace(0, 1, len(tbl) + 1)))
    if edges.size < 2:
        return float(abs(y.mean() - p.mean())), None
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, edges.size - 2)
    total = 0.0
    for b in range(edges.size - 1):
        m = idx == b
        c = int(m.sum())
        if c == 0:
            continue
        total += (c / n) * abs(float(y[m].mean()) - float(p[m].mean()))

    vb = valid_bins(tbl)
    if vb.empty:
        return float(total), None
    w = vb["人數"].to_numpy(dtype=float)
    d = (vb["實際發生率"].to_numpy(dtype=float)
         - vb["預測均值"].to_numpy(dtype=float))
    return float(total), float(np.sum(w * np.abs(d)) / w.sum())


def calib_slope_intercept(tbl: pd.DataFrame) -> tuple[float | None, float | None]:
    """校準斜率／截距：分箱點對 45 度線做迴歸，理想 (1, 0)。

    照 12 §三 的示範程式碼：`LinearRegression().fit(pred, obs).coef_[0]`，
    **未加權**、只用有效箱。加權會更有效率，但那就不是 §三 定義的那個數字了，
    而表 11.1 是要跨專案比的欄位 —— 定義先於精緻。
    """
    vb = valid_bins(tbl)
    if len(vb) < 2:
        return None, None
    from sklearn.linear_model import LinearRegression
    x = vb["預測均值"].to_numpy(dtype=float).reshape(-1, 1)
    yv = vb["實際發生率"].to_numpy(dtype=float)
    if np.allclose(x, x[0]):
        return None, None          # 所有箱的預測值一樣 → 斜率無定義
    lr = LinearRegression().fit(x, yv)
    return float(lr.coef_[0]), float(lr.intercept_)


def diagnose_shape(tbl: pd.DataFrame) -> tuple[str, str]:
    """照 12 §三「校準曲線怎麼讀」那張表判長相，回 (長相, 該做什麼)。

    判準是逐箱的顯著性，不是肉眼：d_i = 實際 − 預測，超過 ±2·SE 才算偏離
    （SE 用虛無假設「已校準」下的二項標準誤）。這樣 30 人的小箱不會因為抖動
    被判成系統性偏差。

    §三 那張表的「S 形（低機率端偏低、高機率端偏高）」描述的是**預測值**被推向
    兩端（過度自信），不是曲線的位置 —— 從下一列「反 S（往中間縮，兩端都被拉回
    0.5）＝過度保守、RF 的典型長相」可以反推：RF 因為多樹平均把機率往中間縮，
    低分端預測偏高、高分端預測偏低，曲線因此是「左低右高」。所以：
      · 曲線左端在對角線上方、右端在下方（斜率 <1）＝ 預測被推向兩端 ＝ 過度自信 ＝ S 形
      · 曲線左端在下方、右端在上方（斜率 >1）＝ 預測被縮向 0.5 ＝ 過度保守 ＝ 反 S
    """
    vb = valid_bins(tbl)
    if len(vb) < 3:
        return "判不出來", (f"有效箱只有 {len(vb)} 個（人數 ≥{MIN_BIN_N} 的箱），"
                            "形狀判讀需要至少 3 個。加大校準／測試集，"
                            "或把箱數調小（--bins）")

    d = vb["差"].to_numpy(dtype=float)
    se = vb["標準誤"].to_numpy(dtype=float)
    sig = np.where(d > SE_K * se, 1, np.where(d < -SE_K * se, -1, 0))
    nz = sig[sig != 0]

    if nz.size == 0:
        return "貼著 45 度線", "已校準。可以拿去乘金額算期望值（12 §三：M11 放行）"
    if np.all(sig >= 0):
        return "整條在對角線上方", ("系統性低估。校準；名單會比預期好，"
                                    "但預算會編不足（12 §三）")
    if np.all(sig <= 0):
        return "整條在對角線下方", ("系統性**高估** —— 最貴的錯誤。必須校準，"
                                    "同時檢查訓練集是否做過重抽樣（12 §四）")

    changes = int(np.sum(nz[1:] != nz[:-1]))
    if changes == 1 and nz[0] > 0:
        return "S 形（預測被推向兩端）", ("過度自信。Platt 通常修得動（12 §三）；"
                                          "常見於 early stopping／正則化／"
                                          "scale_pos_weight 之後")
    if changes == 1 and nz[0] < 0:
        return "反 S（預測被縮向 0.5）", ("過度保守，RF 的典型長相。"
                                          "Platt 或 Isotonic 都可，比 Brier 決定（12 §三）")
    return "中段反轉、上上下下", ("非單調扭曲。Platt 修不動，改 Isotonic；"
                                  "若仍不動，特徵或切分有問題，回 12 §二")


# ══════════════════════════════════════════════════════════════
#  校準器：Platt / Isotonic
# ══════════════════════════════════════════════════════════════
def fit_platt(p_cal: np.ndarray, y_cal: np.ndarray,
              mode: str = "logit") -> dict[str, Any]:
    """Platt scaling：q = sigmoid(A·x + B)，x = logit(p)（§三）或 p（sklearn 樹模型版）。

    目標值用 Platt(1999) 的先驗修正 t⁺=(N⁺+1)/(N⁺+2)、t⁻=1/(N⁻+2)，
    與 sklearn `_SigmoidCalibration` 同式。為什麼要修正而不是直接用 0/1：
    校準集裡若有一段全是正類（稀有事件常見），未修正的 MLE 會把 A 推到無限大，
    校準後的機率變成 0 或 1 —— 那正是我們要修掉的病，不能自己再製造一次。

    目標函數對 (A,B) 是凸的，梯度是 Σ(q−t)·x 與 Σ(q−t)，所以給 L-BFGS-B
    解析梯度就會收斂到唯一解，不需要隨機初始值也就沒有 seed 的問題。
    """
    p_cal = np.asarray(p_cal, dtype=float)
    y_cal = np.asarray(y_cal, dtype=float)
    x = logit(p_cal) if mode == "logit" else p_cal

    n_pos = float((y_cal == 1).sum())
    n_neg = float((y_cal == 0).sum())
    t = np.where(y_cal == 1, (n_pos + 1.0) / (n_pos + 2.0), 1.0 / (n_neg + 2.0))

    def nll_and_grad(theta: np.ndarray) -> tuple[float, np.ndarray]:
        a, b = float(theta[0]), float(theta[1])
        z = a * x + b
        q = expit(z)
        eps = 1e-12
        nll = -float(np.sum(t * np.log(q + eps) + (1 - t) * np.log(1 - q + eps)))
        r = q - t
        return nll, np.array([float(np.sum(r * x)), float(np.sum(r))])

    # 起點取「什麼都不做」：logit 模式的恆等是 (1,0)；raw 模式的近似恆等是 (4,-2)
    x0 = np.array([1.0, 0.0]) if mode == "logit" else np.array([4.0, -2.0])
    method = "L-BFGS-B"
    try:
        from scipy.optimize import minimize
        res = minimize(nll_and_grad, x0, jac=True, method=method)
        a, b = float(res.x[0]), float(res.x[1])
    except ImportError:  # pragma: no cover - scipy 是 sklearn 的硬相依，正常裝得到
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(C=1e6).fit(x.reshape(-1, 1), y_cal.astype(int))
        a, b = float(lr.coef_[0][0]), float(lr.intercept_[0])
        method = "LogisticRegression（scipy 不在，改用硬標籤，無先驗修正）"
    return {"method": "platt", "input": mode, "A": a, "B": b,
            "solver": method, "n_calib": int(p_cal.size)}


def apply_platt(model: dict[str, Any], p: np.ndarray) -> np.ndarray:
    x = logit(p) if model["input"] == "logit" else np.asarray(p, dtype=float)
    return expit(model["A"] * x + model["B"])


def fit_isotonic(p_cal: np.ndarray, y_cal: np.ndarray) -> dict[str, Any]:
    """Isotonic regression（保序）：非參數階梯，只假設單調。

    `out_of_bounds="clip"` 對應 §三 表的「修不了什麼：校準集外的區間（會外推成
    常數）」—— 這不是缺陷而是明講的行為，clip 讓它明確地變成常數而不是亂外推。
    直接擬合在 p 上（不是 logit 上）：§一 的主力是樹模型，樹模型沒有
    decision_function，sklearn 在這種情況下也是擬合在 p 上。
    """
    from sklearn.isotonic import IsotonicRegression
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(np.asarray(p_cal, dtype=float), np.asarray(y_cal, dtype=float))
    return {"method": "isotonic", "input": "raw",
            "x": [float(v) for v in np.asarray(iso.X_thresholds_).ravel()],
            "y": [float(v) for v in np.asarray(iso.y_thresholds_).ravel()],
            "_model": iso, "n_calib": int(np.asarray(p_cal).size)}


def apply_isotonic(model: dict[str, Any], p: np.ndarray) -> np.ndarray:
    iso = model.get("_model")
    if iso is not None:
        return np.asarray(iso.predict(np.asarray(p, dtype=float)), dtype=float)
    # 從 JSON 重放時沒有 sklearn 物件，用階梯的節點做線性內插 + 兩端 clip
    xs = np.asarray(model["x"], dtype=float)
    ys = np.asarray(model["y"], dtype=float)
    return np.interp(np.asarray(p, dtype=float), xs, ys, left=ys[0], right=ys[-1])


# ══════════════════════════════════════════════════════════════
#  評估一組分數
# ══════════════════════════════════════════════════════════════
def evaluate(name: str, dataset: str, y: np.ndarray, p: np.ndarray,
             n_bins: int = DEFAULT_BINS) -> dict[str, Any]:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    tbl = calibration_table(y, p, n_bins=n_bins)
    e_all, e_valid = ece(y, p, tbl)
    slope, intercept = calib_slope_intercept(tbl)
    shape, todo = diagnose_shape(tbl)
    return {
        "方法": name,
        "評估集": dataset,
        "n": int(p.size),
        "正類數": int((y == 1).sum()),
        "正類率": round(float(y.mean()), 6) if p.size else None,
        "Brier": round(brier_score(y, p), 6),
        "ECE": round(e_all, 6),
        "ECE_有效箱": round(e_valid, 6) if e_valid is not None else None,
        "校準斜率": round(slope, 4) if slope is not None else None,
        "校準截距": round(intercept, 4) if intercept is not None else None,
        "AUC": (lambda a: round(a, 6) if a is not None else None)(roc_auc(y, p)),
        "有效箱數": int(len(valid_bins(tbl))),
        "曲線長相": shape,
        "該做什麼": todo,
        "_table": tbl,
    }


# ══════════════════════════════════════════════════════════════
#  載入與切分
# ══════════════════════════════════════════════════════════════
def load_predictions(p: Any, explicit: Path | None) -> tuple[pd.DataFrame, Path]:
    path = explicit or (p.models / "predictions.parquet")
    if not path.exists():
        alt = path.with_suffix(".csv")
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(
                f"找不到預測結果表：{path}\n"
                f"  這支腳本吃的是「一列一個受評對象」的表，至少要有：\n"
                f"    分數欄（模型輸出的機率）、標籤欄（0/1 實際結果）、"
                f"切分欄（train/calib/test）\n"
                f"  訓練腳本跑完把這三欄存成 {p.models / 'predictions.parquet'}，"
                f"或用 --pred 指定路徑。")
    df = (pd.read_parquet(path) if path.suffix.lower() == ".parquet"
          else pd.read_csv(path, encoding="utf-8-sig"))
    return df, path


def pick_col(df: pd.DataFrame, explicit: str | None,
             candidates: list[str], what: str, required: bool = True) -> str | None:
    if explicit:
        if explicit not in df.columns:
            raise ValueError(
                f"表裡沒有 {what} 欄「{explicit}」。現有欄位：{list(df.columns)}")
        return explicit
    lower = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise ValueError(
            f"找不到 {what} 欄（試過 {candidates}）。現有欄位：{list(df.columns)}\n"
            f"  用對應的旗標明講欄名。")
    return None


def normalize_split(s: pd.Series, train_v: str | None, calib_v: str | None,
                    test_v: str | None) -> pd.Series:
    """把切分欄壓成 train／calib／test／其他。明確指定的值優先於別名表。"""
    raw = s.astype(str).str.strip()
    out = pd.Series("其他", index=s.index, dtype=object)
    if train_v or calib_v or test_v:
        if train_v:
            out[raw.str.lower() == train_v.strip().lower()] = "train"
        if calib_v:
            out[raw.str.lower() == calib_v.strip().lower()] = "calib"
        if test_v:
            out[raw.str.lower() == test_v.strip().lower()] = "test"
        return out
    low = raw.str.lower()
    out[low.isin({a.lower() for a in TRAIN_ALIASES}) | raw.isin(TRAIN_ALIASES)] = "train"
    out[low.isin({a.lower() for a in CALIB_ALIASES}) | raw.isin(CALIB_ALIASES)] = "calib"
    out[low.isin({a.lower() for a in TEST_ALIASES}) | raw.isin(TEST_ALIASES)] = "test"
    return out


def row_keys(df: pd.DataFrame, mask: pd.Series, id_col: str | None,
             drop_cols: list[str]) -> set:
    """一個切分裡的「身分集合」。有 id 就用 id（顧客層），沒有就用整列指紋。"""
    if id_col:
        return set(df.loc[mask, id_col].tolist())
    sub = df.loc[mask].drop(columns=[c for c in drop_cols if c in df.columns])
    return set(pd.util.hash_pandas_object(sub, index=False).tolist())


# ══════════════════════════════════════════════════════════════
#  第一部分：S1–S7 切分獨立性
# ══════════════════════════════════════════════════════════════
def gate_split(df: pd.DataFrame, *, split_col: str, score_col: str,
               label_col: str, id_col: str | None = None,
               time_col: str | None = None, pop_rate: float | None = None,
               n_bins: int = DEFAULT_BINS) -> list[dict[str, Any]]:
    """七道切分關。任何一道 error → 上層不做校準、不寫校準後分數。"""
    res: list[dict[str, Any]] = []
    sp = df[split_col]
    n_tr = int((sp == "train").sum())
    n_ca = int((sp == "calib").sum())
    n_te = int((sp == "test").sum())
    n_ot = int((sp == "其他").sum())

    # ── S1 三份齊全 ────────────────────────────────────────
    print("\nS1／三份切分齊全（12 §三：train 訓練、calib 只校準、test 只評估）")
    detail(f"train {n_tr:,} 列｜calib {n_ca:,} 列｜test {n_te:,} 列"
           + (f"｜其他 {n_ot:,} 列（不使用）" if n_ot else ""))
    r: dict[str, Any] = {"關卡": "S1", "名稱": "三份切分齊全",
                         "數值": f"train={n_tr}/calib={n_ca}/test={n_te}",
                         "門檻": "calib 與 test 必須都有列"}
    if n_ca == 0:
        err("校準集是空的（沒有任何列被判為 calib）",
            "本腳本無事可做。切分欄的值要能被認出來 —— 用 --calib-value 明講，"
            "或把值改成 calib／校準集。12 §二 ④：切分要切出 train/calib/test 三份")
        r["結果"] = "error"
    elif n_te == 0:
        err("測試集是空的（沒有任何列被判為 test）",
            "校準前後的對照會落在校準集自己身上 —— 用同一批資料學映射、"
            "再用同一批資料證明映射有效，恆定變好，證明不了任何事"
            "（同 07 §8.2 的 S1 循環推論）。切出 test 再來，本腳本不提供繞過的旗標")
        r["結果"] = "error"
    elif n_tr == 0:
        warn("表裡沒有 train 的列 —— S2（校準集 ∩ 訓練集）這次沒有真的驗到",
             "12 §三 最重要的那條規則就是「校準集不可與訓練集重疊」。"
             "把訓練集的列也寫進這張表（標 split=train），本腳本才驗得了。"
             "報告不可寫「校準集獨立性已驗證」")
        r["結果"] = "warning"
    else:
        ok("train／calib／test 三份都有列")
        r["結果"] = "pass"
    res.append(r)
    if r["結果"] == "error":
        return res     # 連切分都不成立，後面幾道沒有意義

    drop = [split_col]
    m_tr, m_ca, m_te = sp == "train", sp == "calib", sp == "test"
    k_tr = row_keys(df, m_tr, id_col, drop) if n_tr else set()
    k_ca = row_keys(df, m_ca, id_col, drop)
    k_te = row_keys(df, m_te, id_col, drop)

    # 沒有 id 欄時，重疊是靠「整列完全相同」判的。分數若接近唯一（連續型），
    # 兩列完全相同幾乎不可能是巧合 → 判 error；分數若大量重複（分箱分數），
    # 巧合是可能的 → 只能判 warning 並要求補 --id-col。
    uniq_ratio = float(df[score_col].nunique() / max(len(df), 1))
    by = (f"id 欄「{id_col}」" if id_col
          else f"整列指紋（分數唯一比 {uniq_ratio:.2f}）")
    hard = bool(id_col) or uniq_ratio > NEAR_UNIQUE_RATIO

    def overlap_gate(code: str, name: str, a: set, b: set, a_n: str, b_n: str,
                     why: str, todo: str) -> dict[str, Any]:
        print(f"\n{code}／{name}（比對依據：{by}）")
        inter = a & b
        rr: dict[str, Any] = {"關卡": code, "名稱": name, "數值": len(inter),
                              "門檻": "交集 = 0", "依據": by}
        if not a or not b:
            warn(f"{a_n} 或 {b_n} 沒有列，這道關沒有驗到", "補齊切分後重跑")
            rr["結果"] = "warning"
            return rr
        if not inter:
            ok(f"{a_n}（{len(a):,}）與 {b_n}（{len(b):,}）完全不重疊")
            rr["結果"] = "pass"
            return rr
        pct = len(inter) / len(a) * 100
        sample = list(inter)[:5]
        if hard:
            err(f"{a_n} 與 {b_n} 有 {len(inter):,} 個重疊（占 {a_n} 的 {pct:.1f}%）"
                f"；例：{sample}", todo)
            rr["結果"] = "error"
        else:
            warn(f"{a_n} 與 {b_n} 有 {len(inter):,} 列完全相同（占 {pct:.1f}%），"
                 f"但沒有 id 欄、分數重複值又多，分不出是複製還是巧合",
                 f"{todo}。先給 --id-col 讓這道關判得準 —— 目前它判不了")
            rr["結果"] = "warning"
        detail(why)
        return rr

    res.append(overlap_gate(
        "S2", "校準集 ∩ 訓練集", k_ca, k_tr, "校準集", "訓練集",
        "12 §三：用訓練集校準等於用模型已經記住的樣本去修正模型的自信 —— "
        "修完看起來完美，上線照樣高估",
        "重切：calib 的樣本一列都不能出現在 train。同一顧客有多筆時要按顧客切"
        "（12 §二 GroupKFold），不能按列切"))
    res.append(overlap_gate(
        "S3", "校準集 ∩ 測試集", k_ca, k_te, "校準集", "測試集",
        "校準器是在 calib 上學的，再拿 calib 的樣本去評估＝自己評自己，"
        "Brier 與 ECE 一定變好，那個「變好」不是證據",
        "重切：test 只做評估，一列都不能參與校準"))
    if n_tr:
        res.append(overlap_gate(
            "S4", "訓練集 ∩ 測試集", k_tr, k_te, "訓練集", "測試集",
            "12 §二：同一人的兩筆分別落進訓練與測試，模型等於考過的題目再考一次；"
            "驗證分數系統性樂觀（18-G4）",
            "重切。有時間結構就用時間切，同顧客多筆就用 GroupKFold"))

    # ── S5 時間順序 ────────────────────────────────────────
    print("\nS5／三份的時間順序（12 §三：train 最早、calib 次之、test 最晚）")
    r5: dict[str, Any] = {"關卡": "S5", "名稱": "時間順序",
                          "門檻": "max(train) ≤ min(calib) ≤ max(calib) ≤ min(test)"}
    if not time_col:
        warn("沒給 --time-col，時間順序這道沒有驗到",
             "目標與時間有關時（流失、下期購買、下季 CLV）這是硬規定："
             "12 §二 判準表第一列「必須時間切分」。給 --time-col <日期欄> 讓它驗；"
             "目標與時間無關（顧客屬性分類、評論情感）才可以略過，"
             "但報告要寫明是哪一種")
        r5.update({"數值": None, "結果": "warning", "依據": "未提供時間欄 —— 未實際驗證"})
    else:
        t = pd.to_datetime(df[time_col], errors="coerce")
        if t.isna().all():
            warn(f"時間欄「{time_col}」全部轉不成日期，這道關沒有驗到",
                 "確認欄位型別；字串日期請用 ISO 格式（YYYY-MM-DD）")
            r5.update({"數值": None, "結果": "warning", "依據": "時間欄無法解析"})
        else:
            bad = []
            spans = {}
            for nm, m in (("train", m_tr), ("calib", m_ca), ("test", m_te)):
                if m.sum():
                    spans[nm] = (t[m].min(), t[m].max())
                    detail(f"{nm}：{t[m].min()} → {t[m].max()}")
            if "train" in spans and "calib" in spans and spans["train"][1] > spans["calib"][0]:
                bad.append(f"train 的最晚（{spans['train'][1]}）晚於 "
                           f"calib 的最早（{spans['calib'][0]}）")
            if "calib" in spans and "test" in spans and spans["calib"][1] > spans["test"][0]:
                bad.append(f"calib 的最晚（{spans['calib'][1]}）晚於 "
                           f"test 的最早（{spans['test'][0]}）")
            if "train" in spans and "test" in spans and spans["train"][1] > spans["test"][0]:
                bad.append(f"train 的最晚（{spans['train'][1]}）晚於 "
                           f"test 的最早（{spans['test'][0]}）")
            r5["數值"] = "；".join(bad) if bad else "順序正確"
            if bad:
                err("三份的時間區間有交錯：" + "；".join(bad),
                    "12 §三：有時間結構時三份必須依時間先後排列。現在的切法讓模型"
                    "看過未來（18-G4），校準與評估都不成立。回 12 §二 重切，"
                    "並確認特徵窗與標籤窗之間留了 gap")
                r5["結果"] = "error"
            else:
                ok("train ≤ calib ≤ test，時間順序正確")
                r5["結果"] = "pass"
    res.append(r5)

    # ── S6 分布未被動過 ────────────────────────────────────
    print("\nS6／校準集與測試集維持母體分布（12 §四：重抽樣只能在訓練集做）")
    y = df[label_col].to_numpy(dtype=float)
    r_ca = float(y[m_ca.to_numpy()].mean()) if n_ca else float("nan")
    r_te = float(y[m_te.to_numpy()].mean()) if n_te else float("nan")
    r_tr = float(y[m_tr.to_numpy()].mean()) if n_tr else float("nan")
    detail(f"正類率：train {r_tr:.4f}｜calib {r_ca:.4f}｜test {r_te:.4f}")
    r6: dict[str, Any] = {"關卡": "S6", "名稱": "校準／測試集維持母體分布",
                          "數值": f"calib={r_ca:.4f}, test={r_te:.4f}",
                          "門檻": f"|正類率 − 母體率| < {POP_RATE_TOL}"}
    if pop_rate is None:
        # 沒有母體率就只能兩者互比。這抓不到「兩邊被同樣動過」，要講清楚。
        se = float(np.sqrt(max(
            ((n_ca * r_ca + n_te * r_te) / (n_ca + n_te))
            * (1 - (n_ca * r_ca + n_te * r_te) / (n_ca + n_te))
            * (1 / max(n_ca, 1) + 1 / max(n_te, 1)), 1e-18)))
        z = (r_ca - r_te) / se if se > 0 else 0.0
        if abs(z) > POP_RATE_SE_K:
            warn(f"校準集正類率 {r_ca:.4f} 與測試集 {r_te:.4f} 差距顯著"
                 f"（z = {z:+.2f}，超過 ±{POP_RATE_SE_K:.0f} 個標準誤）",
                 "兩種可能：① 其中一邊被重抽樣動過（12 §四：SMOTE／undersampling "
                 "絕不能碰 calib 與 test）② 母體真的漂移了（12 §十 concept drift）。"
                 "查訓練管線有沒有在切分之前做重抽樣；沒有的話這是漂移訊號，"
                 "校準器可能撐不到下個月。給 --pop-rate <母體實際發生率> 可以判得更準")
            r6["結果"] = "warning"
        else:
            warn("沒給 --pop-rate，只比了校準集與測試集彼此，"
                 "這道關沒有真的驗到母體分布",
                 f"兩者彼此一致（z = {z:+.2f}）只能排除「單邊被動過」，"
                 f"排除不了「兩邊被同樣動過」。給 --pop-rate <母體實際發生率> "
                 f"（例如全庫的回應率）才驗得到 12 §四 那條 assert")
            r6["結果"] = "warning"
        r6["依據"] = f"僅互比，z={z:+.3f}"
    else:
        bad, soft = [], []
        for nm, rate, nn in (("校準集", r_ca, n_ca), ("測試集", r_te, n_te)):
            if nn == 0:
                continue
            se = float(np.sqrt(max(pop_rate * (1 - pop_rate) / nn, 1e-18)))
            dv = abs(rate - pop_rate)
            if dv >= POP_RATE_TOL and dv > POP_RATE_SE_K * se:
                bad.append(f"{nm} {rate:.4f} 偏離母體 {pop_rate:.4f} 達 {dv:.4f}"
                           f"（{dv / se:.1f} 個標準誤）")
            elif dv >= POP_RATE_TOL:
                soft.append(f"{nm} {rate:.4f} 偏離 {dv:.4f}"
                            f"（僅 {dv / se:.1f} 個標準誤，抽樣誤差可解釋）")
        r6["依據"] = f"母體率 {pop_rate}"
        if bad:
            err("；".join(bad),
                "12 §四：測試集與校準集必須維持原始分布，任何重抽樣只能在訓練集上做，"
                "否則就是 data leakage、評估數字虛高。把 SMOTE／undersampling 移進 "
                "imblearn Pipeline，讓它只在訓練折內執行")
            r6["結果"] = "error"
        elif soft:
            warn("；".join(soft),
                 f"12 §四 的 assert 寫的是絕對值 {POP_RATE_TOL}，但那是給大測試集寫的 —— "
                 f"這裡的偏離量在抽樣誤差內，先不擋。若測試集會再放大，重跑一次確認")
            r6["結果"] = "warning"
        else:
            ok(f"校準集與測試集的正類率都與母體 {pop_rate:.4f} 相符")
            r6["結果"] = "pass"
    res.append(r6)

    # ── S7 校準集規模（§三 樣本量表） ──────────────────────
    print(f"\nS7／校準集規模（12 §三 樣本量表；每箱 ≥{MIN_BIN_N}、isotonic ≥{ISO_MIN_N}）")
    n_pos_ca = int((y[m_ca.to_numpy()] == 1).sum())
    r7: dict[str, Any] = {"關卡": "S7", "名稱": "校準集規模",
                          "數值": f"n={n_ca}, 正類={n_pos_ca}",
                          "門檻": f"n ≥ {n_bins * MIN_BIN_N}（{n_bins} 箱 × {MIN_BIN_N}）"}
    msgs = []
    if n_ca < n_bins * MIN_BIN_N:
        msgs.append(f"校準集只有 {n_ca:,} 列，{n_bins} 箱等頻分箱平均每箱 "
                    f"{n_ca / n_bins:.0f} 人，撐不到 {MIN_BIN_N} 人")
    if n_ca < ISO_MIN_N:
        msgs.append(f"校準集 {n_ca:,} < {ISO_MIN_N}，isotonic 會過擬合成鋸齒")
    if n_ca and r_ca < RARE_POS_RATE:
        msgs.append(f"正類率 {r_ca:.2%} < {RARE_POS_RATE:.0%}（稀有正類）")
    if n_pos_ca < MIN_BIN_N:
        msgs.append(f"校準集正類只有 {n_pos_ca} 筆，連一個可信的箱都湊不出來")
    if msgs:
        warn("；".join(msgs),
             "12 §三 表：這幾種情況一律優先用 Platt（參數只有 2 個，數百筆即可）。"
             f"人數不足 {MIN_BIN_N} 的箱會標 N/A 不畫（00 §四），圖下要註明。"
             "兩種還是都會跑，但選擇理由要寫進表 11.1")
        r7["結果"] = "warning"
    else:
        ok(f"校準集 {n_ca:,} 列、正類 {n_pos_ca:,} 筆，兩種方法都撐得住")
        r7["結果"] = "pass"
    res.append(r7)
    return res


# ══════════════════════════════════════════════════════════════
#  選擇 Platt 還是 Isotonic（12 §三）
# ══════════════════════════════════════════════════════════════
def choose_method(rows: list[dict[str, Any]], n_calib: int,
                  pos_rate_calib: float) -> tuple[str, str]:
    """回 (選誰, 理由)。§三：兩種都跑，比 Brier 與校準斜率，選贏的並記錄理由。"""
    cand = {r["方法"]: r for r in rows if r["方法"] in ("Platt", "Isotonic")}
    if len(cand) < 2:
        only = next(iter(cand)) if cand else "未校準"
        return only, "只跑了一種方法"

    by_brier = min(cand.values(), key=lambda r: r["Brier"])["方法"]
    # 斜率離 1 越近越好；算不出來（有效箱 <2）的視為最差
    def slope_gap(r: dict[str, Any]) -> float:
        return abs(r["校準斜率"] - 1.0) if r["校準斜率"] is not None else float("inf")
    by_slope = min(cand.values(), key=slope_gap)["方法"]

    rule = "Platt" if (n_calib < ISO_MIN_N or pos_rate_calib < RARE_POS_RATE) else None
    why = [f"測試集 Brier 較低者＝{by_brier}"
           f"（Platt {cand['Platt']['Brier']:.6f}／Isotonic {cand['Isotonic']['Brier']:.6f}）",
           f"校準斜率較接近 1 者＝{by_slope}"
           f"（Platt {fmt(cand['Platt']['校準斜率'])}／"
           f"Isotonic {fmt(cand['Isotonic']['校準斜率'])}）"]
    if rule:
        why.append(f"§三 樣本量規則指向 Platt"
                   f"（校準集 {n_calib:,} < {ISO_MIN_N} 或正類率 "
                   f"{pos_rate_calib:.2%} < {RARE_POS_RATE:.0%}）")
        if by_brier != "Platt":
            return "Platt", ("；".join(why)
                             + "。規則與數字不一致：規則指向 Platt、Brier 指向 "
                             f"{by_brier}。本腳本從規則（isotonic 在小校準集上的優勢"
                             "常是過擬合出來的），但 §三 要求記錄理由 —— "
                             "兩組數字都已寫進表 11.1，最終由人決定")
        return "Platt", "；".join(why) + "。規則與數字一致"
    return by_brier, "；".join(why) + "。§三 樣本量規則沒有偏好，依 Brier"


# ══════════════════════════════════════════════════════════════
#  圖（ref 19 §1.7：10 分箱＋45 度線，檔名 M9_<主題>_calibration.png）
# ══════════════════════════════════════════════════════════════
def make_figure(evals: list[dict[str, Any]], scores: dict[str, np.ndarray],
                out_path: Path, title: str) -> Path | None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    zh = str(cfg("字型.中文", "Microsoft JhengHei"))
    matplotlib.rcParams["font.sans-serif"] = [zh, "Microsoft JhengHei",
                                              "Noto Sans TC", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False   # 中文字型多半沒有 U+2212
    matplotlib.rcParams["font.size"] = max(int(cfg("字型.最小字級", 12) or 12), 10)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(7.2, 8.2), height_ratios=[3, 1.4],
        constrained_layout=True)
    ax.plot([0, 1], [0, 1], ls="--", lw=1, color="0.4", label="45 度線（完美校準）")

    na_note = []
    for e in evals:
        vb = valid_bins(e["_table"])
        n_na = int(len(e["_table"]) - len(vb))
        if n_na:
            na_note.append(f"{e['方法']} {n_na} 箱")
        if vb.empty:
            continue
        ax.plot(vb["預測均值"], vb["實際發生率"], marker="o", ms=5, lw=1.6,
                label=f"{e['方法']}（Brier {e['Brier']:.4f}／ECE {e['ECE']:.4f}／"
                      f"斜率 {fmt(e['校準斜率'], 2)}）")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("預測機率（該箱平均）")
    ax.set_ylabel("實際發生率")
    ax.set_title(f"校準曲線｜{title}（測試集，等頻 {DEFAULT_BINS} 分箱）")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.25)

    for nm, s in scores.items():
        ax2.hist(s, bins=30, range=(0, 1), histtype="step", lw=1.5, label=nm)
    ax2.set_xlim(0, 1)
    ax2.set_xlabel("預測機率")
    ax2.set_ylabel("人數")
    ax2.set_title("分數分布（校準把刻度搬到哪裡去了）", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(alpha=0.25)

    foot = (f"等頻分箱；每箱人數 <{MIN_BIN_N} 標 N/A 不繪（12 §三、00 §四）"
            + (f"；本圖略去 {'、'.join(na_note)}" if na_note else ""))
    fig.text(0.01, 0.005, foot, fontsize=8.5, color="0.35")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ══════════════════════════════════════════════════════════════
def run(args: Any) -> int:
    p = project_dir(args.project, create=True)
    df, path = load_predictions(p, args.pred)
    if df.empty:
        raise ValueError(f"預測結果表 {path.name} 是空的")

    score_col = pick_col(df, args.score_col, SCORE_CANDIDATES, "分數")
    label_col = pick_col(df, args.label_col, LABEL_CANDIDATES, "標籤")
    split_col = pick_col(df, args.split_col, SPLIT_CANDIDATES, "切分")
    id_col = pick_col(df, args.id_col, ID_CANDIDATES, "id", required=False)
    time_col = pick_col(df, args.time_col, TIME_CANDIDATES, "時間", required=False)

    # ── 分數與標籤的基本合法性。這裡不擋住的話，後面每個數字都是垃圾 ──
    s_raw = pd.to_numeric(df[score_col], errors="coerce")
    if s_raw.isna().any():
        raise ValueError(
            f"分數欄「{score_col}」有 {int(s_raw.isna().sum())} 列不是數字或缺值。"
            f"缺值不可以補 0（那等於斷言「這人一定不會回應」），"
            f"先回頭查預測管線為什麼漏了這些列")
    if args.score_is_logit:
        s = expit(s_raw.to_numpy(dtype=float))
    else:
        s = s_raw.to_numpy(dtype=float)
        if s.min() < 0 or s.max() > 1:
            raise ValueError(
                f"分數欄「{score_col}」的範圍是 [{s.min():.4g}, {s.max():.4g}]，"
                f"不在 [0,1] —— 這不是機率。\n"
                f"  若那是 log-odds／decision_function，加 --score-is-logit；\n"
                f"  若那是分數卡分數，先自己壓到 [0,1] 再進來。\n"
                f"  12 §三 校準的對象是機率，餵 log-odds 進來 Brier 與 ECE 全部無意義")

    y_raw = pd.to_numeric(df[label_col], errors="coerce")
    uniq = set(pd.unique(y_raw.dropna()))
    if y_raw.isna().any() or not uniq <= {0, 1, 0.0, 1.0}:
        raise ValueError(
            f"標籤欄「{label_col}」必須是 0/1，目前的值：{sorted(uniq)[:8]}"
            f"{'（另有缺值）' if y_raw.isna().any() else ''}。\n"
            f"  多類別問題不適用本腳本（12 §三 校準講的是二元機率）；"
            f"標籤缺值代表這批人的結果還沒發生，應該排除而不是當成 0")
    y = y_raw.to_numpy(dtype=float)

    work = df.copy()
    work["_score"] = s
    work["_label"] = y
    work["_split"] = normalize_split(work[split_col], args.train_value,
                                     args.calib_value, args.test_value)

    print("=" * 74)
    print("行銷數據分析 Skill — 機率校準（12 §三）")
    print(f"專案：{args.project}｜預測表：{path.name}（{len(work):,} 列）")
    print(f"分數欄：{score_col}｜標籤欄：{label_col}｜切分欄：{split_col}"
          f"｜id 欄：{id_col or '（無）'}｜時間欄：{time_col or '（無）'}")
    print(f"整體正類率：{y.mean():.4f}（{int(y.sum()):,} / {len(y):,}）")
    print("=" * 74)
    print("\n【第一部分】切分獨立性 —— 12 §三：「校準必須在獨立的校準集上做」")

    gates = gate_split(work, split_col="_split", score_col="_score",
                       label_col="_label", id_col=id_col, time_col=time_col,
                       pop_rate=args.pop_rate, n_bins=args.bins)

    n_gate_err = sum(1 for g in gates if g["結果"] == "error")
    out_tbl = p.tables / "預測模型"
    out_tbl.mkdir(parents=True, exist_ok=True)
    gate_csv = out_tbl / "校準_切分獨立性.csv"

    if n_gate_err:
        print("\n" + "=" * 74)
        print(f"結果：⛔ 切分獨立性有 {n_gate_err} 條 error。")
        print("      **本腳本到此為止 —— 不做校準、不寫校準後分數。**")
        print("      理由：校準後的分數會被 M11 拿去乘金額算預算。切分不乾淨時，")
        print("      校準前後的對照會漂亮得離譜，而那個漂亮完全是循環推論造出來的，")
        print("      交出去比不校準更危險（12 §三）。")
        if not args.no_write:
            pd.DataFrame(gates).to_csv(gate_csv, index=False, encoding="utf-8-sig")
            print(f"\n✓ 切分關結果：{gate_csv}")
        return EX_ERROR

    m_ca = (work["_split"] == "calib").to_numpy()
    m_te = (work["_split"] == "test").to_numpy()
    p_ca, y_ca = s[m_ca], y[m_ca]
    p_te, y_te = s[m_te], y[m_te]

    if len(np.unique(y_ca)) < 2:
        raise ValueError(
            f"校準集只有單一類別（正類 {int(y_ca.sum())} / {len(y_ca)}）。"
            f"校準映射學不出來 —— Platt 會退化成常數。"
            f"12 §九：正類 < 200 筆就不該建模，先看標籤定義與 horizon")

    # ── 第二部分：校準 ────────────────────────────────────
    print("\n" + "=" * 74)
    print("【第二部分】校準（12 §三）—— 兩種都跑，比 Brier 與校準斜率")
    print("=" * 74)

    models: dict[str, dict[str, Any]] = {}
    scores_te: dict[str, np.ndarray] = {"未校準": p_te}
    if args.method in ("both", "platt"):
        models["Platt"] = fit_platt(p_ca, y_ca, mode=args.platt_input)
        scores_te["Platt"] = apply_platt(models["Platt"], p_te)
        mp = models["Platt"]
        print(f"\nPlatt scaling：q = sigmoid({mp['A']:.4f}·{mp['input']}(p) "
              f"{mp['B']:+.4f})，在 {mp['n_calib']:,} 列校準集上擬合")
        if mp["A"] <= 0:
            warn(f"Platt 的斜率 A = {mp['A']:.4f} ≤ 0 —— 校準映射是遞減的",
                 "這代表在校準集上「分數越高、實際發生率越低」。不是校準的問題，"
                 "是標籤或切分反了：回 12 §二 檢查標籤定義（是不是把 0/1 寫反）"
                 "與特徵窗／標籤窗有沒有重疊")
    if args.method in ("both", "isotonic"):
        models["Isotonic"] = fit_isotonic(p_ca, y_ca)
        scores_te["Isotonic"] = apply_isotonic(models["Isotonic"], p_te)
        print(f"Isotonic regression：{len(models['Isotonic']['x'])} 個節點的階梯，"
              f"校準集外的區間 clip 成常數（12 §三 表：「修不了校準集外的區間」）")

    evals: list[dict[str, Any]] = [evaluate("未校準", "test", y_te, p_te, args.bins)]
    for nm in ("Platt", "Isotonic"):
        if nm in scores_te:
            evals.append(evaluate(nm, "test", y_te, scores_te[nm], args.bins))
    # 校準集上的數字也算一份，但要明著標「不可當成效證據」
    evals_ca = [evaluate("未校準", "calib(不可當成效證據)", y_ca, p_ca, args.bins)]
    for nm in ("Platt", "Isotonic"):
        if nm in scores_te:
            fn = apply_platt if nm == "Platt" else apply_isotonic
            evals_ca.append(evaluate(nm, "calib(不可當成效證據)", y_ca,
                                     fn(models[nm], p_ca), args.bins))

    print("\n校準前後對照（**測試集**，n = {:,}；校準集的數字在 CSV 裡，標了不可引用）"
          .format(len(y_te)))
    print("-" * 74)
    print(f"{'方法':<10}{'Brier':>11}{'ECE':>10}{'校準斜率':>11}"
          f"{'校準截距':>11}{'AUC':>9}{'有效箱':>7}")
    print("-" * 74)
    for e in evals:
        print(f"{e['方法']:<10}{e['Brier']:>11.6f}{e['ECE']:>10.4f}"
              f"{fmt(e['校準斜率'], 3):>11}{fmt(e['校準截距'], 3):>11}"
              f"{fmt(e['AUC'], 4):>9}{e['有效箱數']:>7}")
    print("-" * 74)
    base = evals[0]
    for e in evals[1:]:
        d_ece = e["ECE"] - base["ECE"]
        d_bri = e["Brier"] - base["Brier"]
        detail(f"{e['方法']}：ECE {d_ece:+.4f}（{d_ece / base['ECE'] * 100:+.1f}%）、"
               f"Brier {d_bri:+.6f}")

    print("\n曲線長相（12 §三「校準曲線怎麼讀」）：")
    for e in evals:
        detail(f"{e['方法']}：{e['曲線長相']} → {e['該做什麼']}")

    # 12 §三 表：「0.6 以上完全沒有點」
    if float(p_te.max()) < HIGH_SCORE_EDGE:
        warn(f"測試集最高分只有 {p_te.max():.3f}，{HIGH_SCORE_EDGE} 以上完全沒有點",
             f"高分區沒有樣本，那一段的校準是外推出來的。該區機率標 N/A，"
             f"**只准用排序不准用機率**，並在圖下標註（12 §三）")

    # ── 選誰 ────────────────────────────────────────────
    pick, why = choose_method(evals, len(y_ca), float(y_ca.mean()))
    print(f"\n選用：{pick}")
    detail(why)
    if "不一致" in why:
        warn("§三 的樣本量規則與 Brier 的贏家不一致",
             "兩組數字都已寫進表 11.1。00 §1.4：參數必附理由 —— "
             "報告要寫「選 X，因為 Y」，不可以只寫結果")

    chosen = evals[[e["方法"] for e in evals].index(pick)] if pick in [
        e["方法"] for e in evals] else base

    # ── M11 放行判準 ────────────────────────────────────
    print("\nM11 放行判準（12 §五 Step 4：要拿去乘金額就必須先過校準）")
    slope = chosen["校準斜率"]
    verdict_ok = True
    if slope is None:
        warn("校準斜率算不出來（有效箱不足 2 個）",
             f"人數 ≥{MIN_BIN_N} 的箱太少。加大測試集，或把 --bins 調小到讓每箱撐得住")
        verdict_ok = False
    elif abs(slope - 1.0) > SLOPE_TOL:
        warn(f"校準後斜率 {slope:.3f}，偏離 1.0 達 {abs(slope - 1):.3f} "
             f"> {SLOPE_TOL}",
             "12 §十 的告警規則就是這一條：「只重做校準，不必重訓全模型」。"
             "先換另一種方法（Platt ↔ Isotonic）；兩種都過不了代表校準集太小或"
             "曲線非單調，回 12 §三 的長相表對照。在修好之前，"
             "**M11 只能用排序不能用機率**")
        verdict_ok = False
    else:
        ok(f"校準後斜率 {slope:.3f}，落在 1.0 ± {SLOPE_TOL} 內（12 §十）")

    if chosen["ECE"] >= base["ECE"]:
        warn(f"{pick} 的 ECE（{chosen['ECE']:.4f}）沒有低於未校準"
             f"（{base['ECE']:.4f}）—— 校準沒有幫上忙",
             "三種可能：① 模型本來就校準得不錯（看未校準的斜率是不是已經 ≈1，"
             "是的話這是好消息，照原分數用即可）② 校準集太小，學到的是雜訊 "
             "③ 校準集與測試集的母體不同（12 §十 concept drift）。"
             "不要因為「有跑校準」就宣稱校準過了")
        verdict_ok = False
    else:
        ok(f"{pick} 把 ECE 從 {base['ECE']:.4f} 降到 {chosen['ECE']:.4f}"
           f"（−{(base['ECE'] - chosen['ECE']) / base['ECE'] * 100:.1f}%）")

    if verdict_ok:
        print("\n  ✅ M11 可以拿校準後的機率去乘金額算期望值。")
    else:
        print("\n  ⚠ M11 目前只能用排序，不可以乘金額（12 §五 Step 4）。")

    # ── 寫檔 ────────────────────────────────────────────
    written: list[str] = []
    if not args.no_write:
        pd.DataFrame(gates).to_csv(gate_csv, index=False, encoding="utf-8-sig")
        written.append(str(gate_csv))

        cmp_rows = []
        for e in evals + evals_ca:
            row = {k: v for k, v in e.items() if not k.startswith("_")}
            row["選用"] = "★" if (e["方法"] == pick and e["評估集"] == "test") else ""
            cmp_rows.append(row)
        cmp_csv = out_tbl / "表11.1_校準前後.csv"
        pd.DataFrame(cmp_rows).to_csv(cmp_csv, index=False, encoding="utf-8-sig")
        written.append(str(cmp_csv))

        bins_rows = []
        for e in evals + evals_ca:
            t = e["_table"].copy()
            t.insert(0, "方法", e["方法"])
            t.insert(1, "評估集", e["評估集"])
            bins_rows.append(t)
        bin_csv = out_tbl / "校準曲線_分箱.csv"
        pd.concat(bins_rows, ignore_index=True).to_csv(
            bin_csv, index=False, encoding="utf-8-sig")
        written.append(str(bin_csv))

        # 校準後分數：M11 要用的就是這一份
        p.models.mkdir(parents=True, exist_ok=True)
        out = work.loc[:, [c for c in ([id_col] if id_col else []) + [split_col]]].copy()
        out["原始分數"] = s
        for nm in ("Platt", "Isotonic"):
            if nm in models:
                fn = apply_platt if nm == "Platt" else apply_isotonic
                out[f"校準後分數_{nm}"] = fn(models[nm], s)
        out["採用"] = (out[f"校準後分數_{pick}"] if f"校準後分數_{pick}" in out
                       else out["原始分數"])
        sp_path = p.models / "calibrated_scores.parquet"
        try:
            out.to_parquet(sp_path, index=False)
        except (ImportError, ValueError) as e:   # 沒有 pyarrow／型別存不進 parquet
            sp_path = sp_path.with_suffix(".csv")
            out.to_csv(sp_path, index=False, encoding="utf-8-sig")
            info(f"parquet 寫不出來（{type(e).__name__}），改存 CSV：{sp_path.name}")
        written.append(str(sp_path))

        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "predictions": str(path),
            "columns": {"score": score_col, "label": label_col,
                        "split": split_col, "id": id_col, "time": time_col},
            "n_train": int((work["_split"] == "train").sum()),
            "n_calib": int(m_ca.sum()),
            "n_test": int(m_te.sum()),
            "split_gates": gates,
            "selected": pick,
            "selection_reason": why,
            "m11_放行": bool(verdict_ok),
            "calibrators": {k: {kk: vv for kk, vv in v.items()
                                if not kk.startswith("_")}
                            for k, v in models.items()},
            "metrics_test": [{k: v for k, v in e.items() if not k.startswith("_")}
                             for e in evals],
            "metrics_calib_不可引用": [{k: v for k, v in e.items()
                                        if not k.startswith("_")}
                                       for e in evals_ca],
            "errors": _errors,
            "warnings": _warnings,
        }
        jp = p.models / "calibrate.json"
        jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                                 default=_json_default), encoding="utf-8")
        written.append(str(jp))

        if not args.no_figure:
            fig_path = p.figure("預測模型", f"M9_{args.title}_calibration.png")
            try:
                make_figure(evals, {k: v for k, v in scores_te.items()
                                    if k in ("未校準", pick)},
                            fig_path, args.title)
                written.append(str(fig_path))
            except Exception as e:  # noqa: BLE001 - 缺字型／缺 matplotlib 不該讓整支掛掉
                warn(f"校準曲線圖沒畫出來：{type(e).__name__}: {e}",
                     "ref 19 §1.7 把校準曲線列為 M9 八張圖之一，缺一張報告即不完整。"
                     "先跑 python scripts/check_fonts.py 確認中文字型；"
                     "數字都在 統計表/預測模型/校準曲線_分箱.csv，可以自己畫")

    for w in written:
        print(f"✓ {w}")

    print("\n" + "=" * 74)
    n_err = len(_errors)
    n_warn = len(_warnings)
    if n_err:
        print(f"結果：⛔ 有 {n_err} 條 error。")
        return EX_ERROR
    if n_warn:
        print(f"結果：⚠ 有 {n_warn} 條 warning → 可往下，但報告要逐條寫明處置。")
        return EX_WARN
    print("結果：✅ 切分乾淨、校準有效、斜率在 ±0.15 內。")
    return EX_OK


# ══════════════════════════════════════════════════════════════
#  自我測試
# ══════════════════════════════════════════════════════════════
def _make_case(rng: np.random.Generator, n: int, distort: float
               ) -> tuple[np.ndarray, np.ndarray]:
    """造一批真實機率 p_true，再把分數用 logit 放大／縮小 distort 倍。

    distort > 1 → 預測被推向 0/1（過度自信）
    distort = 1 → 本來就校準良好
    distort < 1 → 預測被縮向 0.5（過度保守，RF 的長相）
    y 一律由 p_true 生成，所以「正確答案」是已知的：校準器應該把分數還原成 p_true，
    也就是 Platt 的 A 應該收斂到 1/distort。
    """
    p_true = rng.beta(2.0, 5.0, n)
    y = (rng.random(n) < p_true).astype(float)
    score = expit(logit(p_true) * distort)
    return y, score


def _selftest() -> int:
    print("=" * 74)
    print("calibrate.py 自我測試")
    print("=" * 74)
    rng = np.random.default_rng(20260728)
    failed: list[str] = []
    measured: list[str] = []

    def check(name: str, cond: bool, got: str = "") -> None:
        if cond:
            print(f"  ✓ {name}" + (f"（{got}）" if got else ""))
        else:
            print(f"  ✗ {name}" + (f"（{got}）" if got else ""))
            failed.append(name)

    # ── ① ECE 實作本身要能量到東西（否則後面全是假的） ──────
    # 常數預測 0.5、實際發生率 0.2 → ECE 必須 ≈ 0.30，不是「差不多小」
    y_c = np.zeros(2000)
    y_c[:400] = 1.0
    p_c = np.full(2000, 0.5)
    t_c = calibration_table(y_c, p_c)
    e_c, _ = ece(y_c, p_c, t_c)
    check("ECE 對常數預測給得出正確的已知值 0.30", abs(e_c - 0.30) < 1e-9,
          f"ECE={e_c:.6f}")
    check("Brier 與手算公式一致",
          abs(brier_score(np.array([1.0, 0.0]), np.array([0.8, 0.3]))
              - ((0.8 - 1) ** 2 + (0.3 - 0) ** 2) / 2) < 1e-12)

    # ── ② 過度自信：校準後 ECE 必須真的下降 ────────────────
    n = 12000
    y_all, s_all = _make_case(rng, n, distort=2.5)
    half = n // 2
    y_ca, p_ca = y_all[:half], s_all[:half]
    y_te, p_te = y_all[half:], s_all[half:]

    e_un = evaluate("未校準", "test", y_te, p_te)
    mp = fit_platt(p_ca, y_ca, mode="logit")
    e_pl = evaluate("Platt", "test", y_te, apply_platt(mp, p_te))
    mi = fit_isotonic(p_ca, y_ca)
    e_is = evaluate("Isotonic", "test", y_te, apply_isotonic(mi, p_te))
    measured.append(f"過度自信(distort=2.5, n_calib={half}): ECE 未校準 "
                    f"{e_un['ECE']:.4f} → Platt {e_pl['ECE']:.4f} → "
                    f"Isotonic {e_is['ECE']:.4f}")
    measured.append(f"同上斜率：未校準 {e_un['校準斜率']:.3f} → "
                    f"Platt {e_pl['校準斜率']:.3f} → Isotonic {e_is['校準斜率']:.3f}"
                    f"；Brier {e_un['Brier']:.5f} → {e_pl['Brier']:.5f} → "
                    f"{e_is['Brier']:.5f}")

    check("過度自信的預測，未校準 ECE 明顯偏高", e_un["ECE"] > 0.05,
          f"ECE={e_un['ECE']:.4f}")
    check("Platt 把 ECE 降到未校準的一半以下",
          e_pl["ECE"] < 0.5 * e_un["ECE"], f"{e_un['ECE']:.4f} → {e_pl['ECE']:.4f}")
    check("Isotonic 把 ECE 降到未校準的一半以下",
          e_is["ECE"] < 0.5 * e_un["ECE"], f"{e_un['ECE']:.4f} → {e_is['ECE']:.4f}")
    check("Platt 的 A 收斂到 1/distort = 0.400（已知正解）",
          abs(mp["A"] - 1 / 2.5) < 0.06, f"A={mp['A']:.4f}, B={mp['B']:+.4f}")
    check("未校準的斜率顯著 < 1（過度自信的定義）", e_un["校準斜率"] < 0.85,
          f"斜率={e_un['校準斜率']:.3f}")
    check("Platt 後斜率回到 1.0 ± 0.15（12 §十 放行門檻）",
          abs(e_pl["校準斜率"] - 1.0) <= SLOPE_TOL, f"斜率={e_pl['校準斜率']:.3f}")
    check("曲線長相判成「S 形（預測被推向兩端）」", "S 形" in e_un["曲線長相"],
          e_un["曲線長相"])
    check("Platt 是單調變換，AUC 一分不差",
          abs(e_pl["AUC"] - e_un["AUC"]) < 1e-12,
          f"{e_un['AUC']:.6f} vs {e_pl['AUC']:.6f}")

    # ── ③ 本來就校準良好的預測，不可以被弄壞 ────────────────
    y_g, s_g = _make_case(rng, n, distort=1.0)
    y_gca, p_gca = y_g[:half], s_g[:half]
    y_gte, p_gte = y_g[half:], s_g[half:]
    g_un = evaluate("未校準", "test", y_gte, p_gte)
    g_mp = fit_platt(p_gca, y_gca, mode="logit")
    g_pl = evaluate("Platt", "test", y_gte, apply_platt(g_mp, p_gte))
    g_mi = fit_isotonic(p_gca, y_gca)
    g_is = evaluate("Isotonic", "test", y_gte, apply_isotonic(g_mi, p_gte))
    measured.append(f"已校準良好(distort=1.0): ECE 未校準 {g_un['ECE']:.4f} → "
                    f"Platt {g_pl['ECE']:.4f} → Isotonic {g_is['ECE']:.4f}"
                    f"；Platt A={g_mp['A']:.4f} B={g_mp['B']:+.4f}")

    check("已校準良好時未校準 ECE 本來就低", g_un["ECE"] < 0.02,
          f"ECE={g_un['ECE']:.4f}")
    check("Platt 沒有把已校準的預測弄壞（ECE 惡化 ≤ 0.01）",
          g_pl["ECE"] <= g_un["ECE"] + 0.01,
          f"{g_un['ECE']:.4f} → {g_pl['ECE']:.4f}")
    check("Platt 在已校準資料上收斂到近似恆等（A≈1、B≈0）",
          abs(g_mp["A"] - 1.0) < 0.15 and abs(g_mp["B"]) < 0.15,
          f"A={g_mp['A']:.4f}, B={g_mp['B']:+.4f}")
    check("Isotonic 沒有把已校準的預測弄壞（ECE 惡化 ≤ 0.02）",
          g_is["ECE"] <= g_un["ECE"] + 0.02,
          f"{g_un['ECE']:.4f} → {g_is['ECE']:.4f}")
    check("已校準良好時斜率本來就在 1.0 ± 0.15 內，校準後仍在",
          abs(g_un["校準斜率"] - 1) <= SLOPE_TOL
          and abs(g_pl["校準斜率"] - 1) <= SLOPE_TOL,
          f"{g_un['校準斜率']:.3f} → {g_pl['校準斜率']:.3f}")
    check("已校準良好時不可被判成系統性高估／低估",
          "45 度線" in g_un["曲線長相"] or "判不出來" in g_un["曲線長相"],
          g_un["曲線長相"])

    # ── ④ 過度保守（RF 的長相）：反 S、斜率 > 1 ─────────────
    y_r, s_r = _make_case(rng, n, distort=0.4)
    r_un = evaluate("未校準", "test", y_r[half:], s_r[half:])
    r_mp = fit_platt(s_r[:half], y_r[:half], mode="logit")
    r_pl = evaluate("Platt", "test", y_r[half:], apply_platt(r_mp, s_r[half:]))
    measured.append(f"過度保守(distort=0.4): 斜率 {r_un['校準斜率']:.3f} → "
                    f"{r_pl['校準斜率']:.3f}；ECE {r_un['ECE']:.4f} → "
                    f"{r_pl['ECE']:.4f}；Platt A={r_mp['A']:.4f}")
    check("過度保守的預測，未校準斜率 > 1", r_un["校準斜率"] > 1.15,
          f"斜率={r_un['校準斜率']:.3f}")
    check("曲線長相判成「反 S（預測被縮向 0.5）」", "反 S" in r_un["曲線長相"],
          r_un["曲線長相"])
    check("Platt 的 A 收斂到 1/0.4 = 2.50", abs(r_mp["A"] - 2.5) < 0.35,
          f"A={r_mp['A']:.4f}")

    # ── ⑤ 「什麼都不做」的假校準器必須被判成沒過 ─────────────
    # 只驗「校準後有變好」的檢查器會被一支回傳原分數的假校準器騙過去。
    fake = evaluate("假校準（原封不動）", "test", y_te, p_te)
    check("假校準器（原分數不動）在過度自信資料上仍被判超出 ±0.15",
          abs(fake["校準斜率"] - 1.0) > SLOPE_TOL,
          f"斜率={fake['校準斜率']:.3f}")

    # ── ⑥ 分箱：<30 人的箱要標 N/A，不可以給數字 ─────────────
    y_s = (rng.random(120) < 0.3).astype(float)
    p_s = rng.random(120)
    t_s = calibration_table(y_s, p_s, n_bins=10)      # 每箱 12 人
    check("人數 <30 的箱標 N/A 而非給實際發生率",
          t_s["實際發生率"].isna().all() and t_s["結論"].str.contains("N/A").all(),
          f"{len(t_s)} 箱、每箱約 {int(t_s['人數'].mean())} 人")
    check("分箱人數加總等於樣本數（邊界不重複計算）",
          int(t_s["人數"].sum()) == 120, f"合計 {int(t_s['人數'].sum())}")
    # 大量重複分數：ref 的 (p>=lo)&(p<=hi) 兩端都閉會重複計數，這裡驗不會
    p_tie = np.repeat(np.array([0.1, 0.2, 0.3, 0.4, 0.5]), 400)
    y_tie = (rng.random(2000) < p_tie).astype(float)
    t_tie = calibration_table(y_tie, p_tie, n_bins=10)
    check("分數大量重複時人數仍不重複計算",
          int(t_tie["人數"].sum()) == 2000, f"合計 {int(t_tie['人數'].sum())}")
    check("有效箱過濾只留人數 ≥30 的箱",
          len(valid_bins(t_s)) == 0 and len(valid_bins(t_tie)) == len(t_tie),
          f"小樣本 {len(valid_bins(t_s))} 箱、重複值 {len(valid_bins(t_tie))} 箱")

    # ── ⑦ 切分關：該抓的要抓到 ──────────────────────────
    def mk_df(n_tr=800, n_ca=600, n_te=600, leak=0, ca_eq_te=False,
              shuffle_time=False, ids=True) -> pd.DataFrame:
        tot = n_tr + n_ca + n_te
        yy = (rng.random(tot) < 0.25).astype(float)
        ss = np.clip(rng.beta(2, 5, tot), 1e-6, 1 - 1e-6)
        idv = [f"C{i:06d}" for i in range(tot)]
        sp = ["train"] * n_tr + ["calib"] * n_ca + ["test"] * n_te
        d = pd.DataFrame({"客戶編號": idv, "預測機率": ss, "實際標籤": yy,
                          "_split": sp})
        if leak:
            # 把訓練集的前 leak 個 id 蓋到校準集頭上 = 典型的重複使用
            d.loc[n_tr:n_tr + leak - 1, "客戶編號"] = idv[:leak]
        if ca_eq_te:
            d.loc[n_tr + n_ca:, "客戶編號"] = d.loc[
                n_tr:n_tr + n_ca - 1, "客戶編號"].to_numpy()[:n_te]
        days = ([0] * n_tr + [400] * n_ca + [800] * n_te if not shuffle_time
                else [800] * n_tr + [400] * n_ca + [0] * n_te)
        d["as_of"] = pd.Timestamp("2026-01-01") + pd.to_timedelta(days, unit="D")
        if not ids:
            d = d.drop(columns=["客戶編號"])
        return d

    def run_gates(d, **kw):
        _reset_buckets()
        g = gate_split(d, split_col="_split", score_col="預測機率",
                       label_col="實際標籤",
                       id_col="客戶編號" if "客戶編號" in d.columns else None, **kw)
        return {x["關卡"]: x for x in g}

    print("\n--- 切分關：乾淨的三份 ---")
    g_clean = run_gates(mk_df(), time_col="as_of")
    check("乾淨切分：S2/S3/S4 全 pass（不該叫的沒亂叫）",
          all(g_clean[k]["結果"] == "pass" for k in ("S2", "S3", "S4")),
          "、".join(f"{k}={g_clean[k]['結果']}" for k in ("S2", "S3", "S4")))
    check("乾淨切分：時間順序 S5 pass", g_clean["S5"]["結果"] == "pass")

    print("\n--- 切分關：校準集混進 120 個訓練集 id ---")
    g_leak = run_gates(mk_df(leak=120), time_col="as_of")
    check("校準集 ∩ 訓練集有交集 → S2 判 error",
          g_leak["S2"]["結果"] == "error" and g_leak["S2"]["數值"] == 120,
          f"交集 {g_leak['S2']['數值']}")
    check("洩漏時 S3（校準∩測試）不被連坐誤判",
          g_leak["S3"]["結果"] == "pass", g_leak["S3"]["結果"])

    print("\n--- 切分關：校準集與測試集是同一批人 ---")
    g_same = run_gates(mk_df(ca_eq_te=True), time_col="as_of")
    check("校準集 ∩ 測試集重疊 → S3 判 error",
          g_same["S3"]["結果"] == "error", f"交集 {g_same['S3']['數值']}")

    print("\n--- 切分關：時間順序倒過來 ---")
    g_time = run_gates(mk_df(shuffle_time=True), time_col="as_of")
    check("train 晚於 calib／test → S5 判 error",
          g_time["S5"]["結果"] == "error", str(g_time["S5"]["數值"])[:60])

    print("\n--- 切分關：缺 test ---")
    g_note = run_gates(mk_df(n_te=0), time_col="as_of")
    check("沒有測試集 → S1 判 error（校準前後對照會變成循環推論）",
          g_note["S1"]["結果"] == "error" and len(g_note) == 1,
          f"只跑了 {len(g_note)} 道就停")

    print("\n--- 切分關：缺 train（驗不到就要說驗不到） ---")
    g_notr = run_gates(mk_df(n_tr=0), time_col="as_of")
    check("沒有訓練集 → S1 判 warning 並明講 S2 沒驗到，不可判 pass",
          g_notr["S1"]["結果"] == "warning", g_notr["S1"]["結果"])

    print("\n--- 切分關：沒有時間欄 ---")
    g_notime = run_gates(mk_df())
    check("沒給時間欄 → S5 判 warning（未實際驗證），不是 pass",
          g_notime["S5"]["結果"] == "warning"
          and "未實際驗證" in str(g_notime["S5"].get("依據", "")),
          g_notime["S5"].get("依據", ""))

    print("\n--- 切分關：母體率 ---")
    d_pop = mk_df(n_ca=4000, n_te=4000)
    g_pop_ok = run_gates(d_pop, time_col="as_of",
                         pop_rate=float(d_pop["實際標籤"].mean()))
    check("母體率相符 → S6 pass", g_pop_ok["S6"]["結果"] == "pass",
          str(g_pop_ok["S6"]["數值"]))
    g_pop_bad = run_gates(d_pop, time_col="as_of", pop_rate=0.05)
    check("正類率遠離母體率（重抽樣痕跡）→ S6 判 error",
          g_pop_bad["S6"]["結果"] == "error", str(g_pop_bad["S6"]["數值"]))

    print("\n--- 切分關：沒有 id 欄時的指紋比對 ---")
    d_noid = mk_df(ids=False)
    d_noid.loc[800:919, ["預測機率", "實際標籤"]] = \
        d_noid.loc[0:119, ["預測機率", "實際標籤"]].to_numpy()
    g_noid = run_gates(d_noid, time_col="as_of")
    check("沒有 id 欄但分數連續 → 整列完全相同仍判 error",
          g_noid["S2"]["結果"] == "error", f"交集 {g_noid['S2']['數值']}")

    print("\n--- 切分關：校準集規模 ---")
    g_small = run_gates(mk_df(n_ca=150), time_col="as_of")
    check("校準集 <1,000 且每箱不足 30 → S7 判 warning 並建議 Platt",
          g_small["S7"]["結果"] == "warning", str(g_small["S7"]["數值"]))
    g_big = run_gates(mk_df(n_ca=5000), time_col="as_of")
    check("校準集夠大且正類不稀有 → S7 pass（不該叫的沒亂叫）",
          g_big["S7"]["結果"] == "pass", str(g_big["S7"]["數值"]))
    _reset_buckets()

    # ── ⑧ choose_method：規則與數字衝突時要講出來 ─────────────
    rows_small = [
        {"方法": "未校準", "Brier": 0.20, "校準斜率": 0.5},
        {"方法": "Platt", "Brier": 0.150, "校準斜率": 0.98},
        {"方法": "Isotonic", "Brier": 0.149, "校準斜率": 0.99},
    ]
    pick_s, why_s = choose_method(rows_small, n_calib=300, pos_rate_calib=0.20)
    check("小校準集時：Brier 贏家是 Isotonic，仍依 §三 規則選 Platt 並說明衝突",
          pick_s == "Platt" and "不一致" in why_s, pick_s)
    pick_b, why_b = choose_method(rows_small, n_calib=20000, pos_rate_calib=0.20)
    check("大校準集時：沒有規則偏好 → 依 Brier 選 Isotonic",
          pick_b == "Isotonic", pick_b)

    # ── ⑨ 分數合法性：logit 進來要能還原 ────────────────────
    z = np.array([-4.0, -1.0, 0.0, 2.0, 5.0])
    check("expit/logit 互為反函數", np.allclose(logit(expit(z)), z, atol=1e-8))
    check("expit 對極端負值不 overflow",
          np.isfinite(expit(np.array([-800.0, 800.0]))).all())

    # ── ⑩ Isotonic 的輸出必須單調不遞減 ────────────────────
    grid = np.linspace(0, 1, 501)
    iso_out = apply_isotonic(mi, grid)
    check("Isotonic 輸出對輸入單調不遞減", bool(np.all(np.diff(iso_out) >= -1e-12)))
    iso_json = {k: v for k, v in mi.items() if not k.startswith("_")}
    check("Isotonic 從 JSON 節點重放的結果與 sklearn 物件一致",
          float(np.max(np.abs(apply_isotonic(iso_json, grid) - iso_out))) < 1e-9,
          f"最大差 {float(np.max(np.abs(apply_isotonic(iso_json, grid) - iso_out))):.2e}")

    # ── ⑪ 結果要能寫成 JSON（numpy 純量不外洩） ──────────────
    try:
        payload = {"metrics": [{k: v for k, v in e.items() if not k.startswith("_")}
                               for e in (e_un, e_pl, e_is)],
                   "gates": list(g_clean.values()),
                   "bins": t_s.to_dict(orient="records")}
        json.dumps(payload, ensure_ascii=False, default=_json_default)
        ser_ok, ser_msg = True, "含分箱人數等 numpy 整數仍可序列化"
    except TypeError as exc:
        ser_ok, ser_msg = False, str(exc)
    check("結果可寫成 JSON", ser_ok, ser_msg)

    # ── ⑫ 雙路徑：與 sklearn 的 CalibratedClassifierCV 對跑（00 §1.3） ──
    # 12 §三 的範例用 CalibratedClassifierCV(FrozenEstimator(base), "sigmoid")。
    # base 是 LogisticRegression（有 decision_function＝logit），sklearn 會把
    # sigmoid 擬合在 logit 上 —— 正是本腳本 --platt-input logit 做的事。
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.frozen import FrozenEstimator
        Xa = rng.normal(0, 1, (3000, 3))
        ya = (rng.random(3000) < expit(Xa @ np.array([1.2, -0.8, 0.5]) - 0.5)
              ).astype(int)
        Xtr, ytr = Xa[:1500], ya[:1500]
        Xcal, ycal = Xa[1500:2400], ya[1500:2400]
        Xte = Xa[2400:]
        base = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
        sk = CalibratedClassifierCV(FrozenEstimator(base),
                                    method="sigmoid").fit(Xcal, ycal)
        p_sk = sk.predict_proba(Xte)[:, 1]
        mine_m = fit_platt(base.predict_proba(Xcal)[:, 1], ycal.astype(float),
                           mode="logit")
        p_mine = apply_platt(mine_m, base.predict_proba(Xte)[:, 1])
        dmax = float(np.max(np.abs(p_sk - p_mine)))
        measured.append(f"雙路徑：本腳本 Platt(logit) vs sklearn "
                        f"CalibratedClassifierCV+FrozenEstimator 最大機率差 {dmax:.3e}")
        check("本腳本的 Platt 與 sklearn CalibratedClassifierCV 吐出同一組機率",
              dmax < 1e-4, f"最大差 {dmax:.3e}")
        cross_ok = True
    except Exception as exc:  # noqa: BLE001
        check("本腳本的 Platt 與 sklearn CalibratedClassifierCV 吐出同一組機率",
              False, f"{type(exc).__name__}: {exc}")
        cross_ok = False
    if cross_ok:
        check("12 §三 註記的 cv='prefit' 確實已被移除（改用 FrozenEstimator）",
              True, "FrozenEstimator 路徑可用")

    # ── ⑬ S6 的門檻放寬有沒有必要：實測純抽樣的誤判率 ──────────
    n_sim, n_s, p_s0 = 4000, 500, 0.04
    draws = rng.binomial(n_s, p_s0, n_sim) / n_s
    fp = float(np.mean(np.abs(draws - p_s0) >= POP_RATE_TOL))
    measured.append(f"12 §四 那條 assert 若照抄（|率−母體|<0.005）："
                    f"n=500、母體率 4% 時純抽樣就會誤判 {fp:.4f}"
                    f"（{n_sim} 次模擬）")
    check("照抄 §四 的絕對門檻在小測試集上誤判率極高，本腳本加 3σ 條件是必要的",
          fp > 0.3, f"誤判率 {fp:.4f}")

    print("\n" + "-" * 74)
    print("實測數字（供 12 §十一 維護條款把【推導，待驗證】換成【實測】用）：")
    for m in measured:
        print(f"  · {m}")

    print("\n" + "=" * 74)
    if failed:
        print(f"⛔ {len(failed)} 項未通過：{'、'.join(failed)}")
        return EX_ERROR
    print("✅ 自我測試全部通過")
    return EX_OK


# ══════════════════════════════════════════════════════════════
def main() -> int:
    ap = GateArgumentParser(
        description="機率校準（12 §三）：Platt／Isotonic、校準曲線、Brier／ECE。"
                    "校準集不獨立就擋住，不產出校準後分數。")
    ap.add_argument("project", nargs="?", help="專案代號")
    ap.add_argument("--pred", type=Path,
                    help="預測結果表（預設 模型輸出/predictions.parquet）")
    ap.add_argument("--score-col", help="模型輸出的機率欄")
    ap.add_argument("--label-col", help="0/1 實際結果欄")
    ap.add_argument("--split-col", help="切分欄（train／calib／test）")
    ap.add_argument("--id-col", help="顧客 id 欄。有它才驗得到顧客層的切分重疊")
    ap.add_argument("--time-col", help="時間欄。有它才驗得到 train≤calib≤test")
    ap.add_argument("--train-value", help="切分欄裡代表訓練集的值")
    ap.add_argument("--calib-value", help="切分欄裡代表校準集的值")
    ap.add_argument("--test-value", help="切分欄裡代表測試集的值")
    ap.add_argument("--score-is-logit", action="store_true",
                    help="分數欄是 log-odds／decision_function，先過 sigmoid")
    ap.add_argument("--bins", type=int, default=DEFAULT_BINS,
                    help=f"校準曲線的等頻箱數（預設 {DEFAULT_BINS}，ref 19 §1.7）")
    ap.add_argument("--pop-rate", type=float,
                    help="母體實際發生率。給了才驗得到 12 §四「分布未被重抽樣動過」")
    ap.add_argument("--method", choices=["both", "platt", "isotonic"],
                    default="both",
                    help="12 §三 要求兩種都跑再比，預設 both")
    ap.add_argument("--platt-input", choices=["logit", "raw"], default="logit",
                    help="Platt 擬合在 logit(p)（§三 文字，預設）或 p 上"
                         "（sklearn 對只有 predict_proba 的樹模型的行為）")
    ap.add_argument("--title", default="預測機率",
                    help="圖檔名的 {主題}：M9_<主題>_calibration.png（ref 19 §九）")
    ap.add_argument("--no-write", action="store_true", help="只檢查，不寫檔")
    ap.add_argument("--no-figure", action="store_true", help="不畫校準曲線圖")
    ap.add_argument("--self-test", action="store_true", help="不需專案，自我測試")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()
    if not args.project:
        ap.error("要給專案代號（或用 --self-test）")

    # 值不合法在 argparse 層擋掉 → 退 64「腳本根本沒跑」，不要掉到執行期變成 1
    if args.bins < 2 or args.bins > 100:
        ap.error(f"--bins 要在 2–100 之間（給的是 {args.bins}）。"
                 f"ref 19 §1.7 的規格是 10 分箱")
    if args.pop_rate is not None and not (0.0 < args.pop_rate < 1.0):
        ap.error(f"--pop-rate 要在 (0,1) 之間（給的是 {args.pop_rate}）")
    vals = [("--train-value", args.train_value), ("--calib-value", args.calib_value),
            ("--test-value", args.test_value)]
    given = [(n, v) for n, v in vals if v is not None]
    for i in range(len(given)):
        for j in range(i + 1, len(given)):
            if given[i][1].strip().lower() == given[j][1].strip().lower():
                ap.error(f"{given[i][0]} 與 {given[j][0]} 給了同一個值 "
                         f"「{given[i][1]}」—— 那就不是三份獨立的切分。"
                         f"12 §三：calib 只做校準、test 只評估，兩者都不參與訓練")

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
        print(f"⛔ calibrate.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
