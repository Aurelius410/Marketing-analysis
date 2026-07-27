#!/usr/bin/env python3
"""
M6 分群矩陣前處理 —— build_features 之後、任何分群之前的**必經**關卡。

為什麼需要它（沒有這一支，M6 的結論會是假的）：
  · **尺度**：課程資料集 M 的樣本變異數約為 F 的 10^6 倍。未標準化的歐氏
    K-Means，WGSS 的 99.99% 以上來自 M —— 分群結果實質上只是 M 的四分位
    切法，卻會被寫成「高頻低額客」。3C 資料的 Amount/Quantity 尺度比 6,112，
    ΔM² 對 ΔF² 的貢獻比約 3,700 萬比 1（07 §3.3）。
  · **順序**：尺度與轉換決策必須排在 k 之前（18-G7 前置條款）。沒定尺度就
    算 bootstrap ARI，只是在量「M 支配」這件事的穩定度 —— 而它會非常穩定。
  · **白名單**：分群輸入只能是行為指標（18-E2）。人口變數進矩陣的報告拿
    B+；教材原話是「行銷要從行為本質的基礎做策略發展，不是以成員結構的
    描述去發展」（IB5082 第一講 P26）。
  · **CRI 血緣**：CRI 的分母含「該顧客所屬先驗群的群內變異數」。先驗群若用
    人口變數分，交易紀錄完全相同的兩人也會拿到不同 CRI —— 等於把人口變數
    以非線性編碼偷渡進矩陣（07 §3.1）。這一關**讀資料**：血緣由
    build_features.py 寫進特徵表，不是靠 spec 填一個字串自我宣告。

做六件事（對應 07 §3.1／§3.3／§四）：
  1. 白名單檢查 —— 只准 R / F / M / RFM Score / CAI / CRI / 因素分數 /
     LN_F / LN_M。人口變數一律擋下（18-E2）→ error
  2. CRI 血緣檢查 —— **以特徵表裡的血緣欄位為準**（build_features.py 落的
     prior_group_type / prior_group_cols / prior_group_demographic_cols）。
     先驗群欄位會用 demographic_vars.py 的人口變數清單重判，不是 behavioral
     就擋下。cluster_spec.json 的 cri_prior_type 降級成交叉檢查，
     與資料不一致（或沒填）→ error（07 §3.1）
  3. 偏度檢查 —— |skew| > 1 依欄位性質轉換（見下方轉換政策），轉換後複檢
     偏度與 Spearman 排序相關 > 0.95（07 §四 關卡 2、06 §6.1）
  4. 標準化 —— z-score，fit 在**整個分析集**（非監督沒有 train/test，
     06 §5.2）；參數寫進 模型輸出/scaler.json，換批資料重跑用同一組
  5. 尺度比檢查 —— max(sd)/min(sd) > 10 必須標準化（07 §四 關卡 1）。
     有做標準化 → warning；spec 的 scaler 為 none → error（禁行，不是警告）
  6. WGSS 貢獻表 —— 每個輸入變數對 WGSS 下降（＝BGSS）的貢獻百分比，
     任一變數 > 70% → warning（07 §3.3 Step 3、§四 關卡 3）
  另加 07 §3.3 Step 4：標準化前 vs 標準化後的群成員 ARI 對照。

轉換政策（07 §3.1 白名單「用哪個版本進矩陣」那欄 + 06 §六 的裁定）：
  | 欄位性質            | |skew| > 1 時          | 為什麼 |
  |---------------------|------------------------|--------|
  | F（次數）、M（金額）| log1p → `__log1p`      | 白名單指定 LN_F / LN_M |
  | R（時間型）         | NTILE(5) → `__bin5`    | 時間型不宜 log：30↔60 與 300↔600
  |                     |                        | 會被壓成同樣差距（06 §4.5）。
  |                     |                        | 06 §六 對 r_days_since_last_sale
  |                     |                        | 的裁定就是分位分箱 |
  | CAI / CRI（可負）   | NTILE(5) → `__bin5`    | 可正可負，不可 log（07 §3.1）|
  | RFM Score           | 不轉換                 | 已是 1–5 的分數 |
  | 因素分數            | 不轉換、也不 z-score   | 因素分析輸出本身即為標準分數 |
  log1p 後仍 |skew| > 1 → 再退回 NTILE(5)。

三桶 + 退出碼（全庫統一，權威定義見 00 §八）：
    0  = 全通過，矩陣已寫出
    1  = 有 error，**不產出矩陣**，M6 不准往下走
    2  = 只有 warning，矩陣已寫出但報告必須寫理由
    64 = 用法錯誤（旗標打錯、缺專案代號）—— 矩陣根本沒開始算
    70 = 腳本自身異常

用法：
    python prep_cluster_matrix.py <專案代號> --input <顧客特徵表.parquet>
    python prep_cluster_matrix.py <專案代號> --table feature_customer
    python prep_cluster_matrix.py 2026Q3_電商 --input feat.parquet \\
        --spec spec.json --id-col cust --k 4
    python prep_cluster_matrix.py 2026Q3_電商 --input 新一批.parquet \\
        --reuse-scaler 模型輸出/scaler.json      # 換批資料，沿用同一組參數

產出（只有在沒有 error 時才寫）：
    模型輸出/cluster_matrix.parquet          標準化後的矩陣（含 id）
    模型輸出/scaler.json                     轉換 + 標準化參數（07 §3.3 Step 2）
    模型輸出/cluster_spec.json               回填 preflight gate1–3
    統計表/分群輪廓/wgss_contribution.csv     WGSS 貢獻表（gate3 的資料來源）
    統計表/轉換前後對照/cluster_matrix_transform.csv   偏度與排序相關對照
    隔離區/cluster_matrix_dropped.csv         被剔除的列（18-E22 樣本流失）
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)
from demographic_vars import (  # noqa: E402
    PRIOR_BEHAVIORAL, PRIOR_NONE, PRIOR_TYPES, classify_blacklist,
    classify_prior_cols, describe_prior_cols)
from paths import SKILL_ROOT, project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 三桶 ─────────────────────────────────────────────────
errors: list[str] = []
warnings: list[str] = []
infos: list[str] = []
DRY_RUN = False          # --dry-run 時結尾不要宣稱「矩陣已產出」


def ok(msg: str) -> None:
    infos.append(msg)


def detail(bucket: list[str], msg: str) -> None:
    """明細行，前面留四格縮排，不另計為一項。"""
    bucket.append(f"    · {msg}")


def warn(fact: str, todo: str) -> None:
    warnings.append(f"{fact} — {todo}")


def err(fact: str, todo: str) -> None:
    errors.append(f"{fact} — {todo}")


# ── 白名單（07 §3.1）。多一個都不行 ──────────────────────
# 每項是 (類別, 正規式, 轉換族)。轉換族決定 |skew|>1 時走哪條路。
#   log   = 可 log1p（全正的次數／金額）
#   bin   = 只能分位分箱（時間型、可負值）
#   none  = 不轉換
#   nozs  = 不轉換也不 z-score（因素分數已是標準分數）
WHITELIST: list[tuple[str, re.Pattern[str], str]] = [
    ("因素分數", re.compile(r"^(fa|fs|factor)_.+$|^factor\d+$"), "nozs"),
    # RFM Score 與它在 build_features.py 裡的兩套計分變體（bs_ / bsc_）
    ("RFM Score", re.compile(
        r"^(rfm_score|rfm|[rfm]_score|score_[rfm])$"
        r"|^(bs|bsc)_([rfm]_score(_variant)?|total)$"), "none"),
    ("CAI", re.compile(r"^cai(_.+)?$"), "bin"),
    ("CRI", re.compile(r"^cri(_.+)?$"), "bin"),
    ("R", re.compile(r"^r$|^r_.+$|^recency.*$"), "bin"),
    ("F", re.compile(r"^f$|^ln_f$|^log_f$|^f_.+$|^frequency.*$"), "log"),
    ("M", re.compile(r"^m$|^ln_m$|^log_m$|^m_.+$|^monetary.*$"), "log"),
]

# 07 §3.1「明確禁止」那一行 → scripts/demographic_vars.py。
# 清單刻意不寫在這裡：18-E2 的白名單檢查與 07 §3.1 的 CRI 血緣判定必須用
# 同一份人口變數清單，各寫一份就是給人繞過的破口（見該檔開頭的理由）。

# 分位分箱的分位點。06 §六 對 r_days_since_last_sale 的裁定是 NTILE(5)
NTILE_QUANTILES = (0.2, 0.4, 0.6, 0.8)

SKEW_THRESHOLD = 1.0        # M4 三門檻之一（07 §四 關卡 2）
SCALE_RATIO_THRESHOLD = 10.0    # 07 §四 關卡 1
WGSS_DOMINANCE_PCT = 70.0       # 07 §3.3 Step 3、§四 關卡 3
SPEARMAN_THRESHOLD = 0.95       # 06 §6.1
ARI_THRESHOLD = 0.60            # 07 §3.3 Step 4；門檻沿用 §7.3 的 ARI 可用線
CAI_MIN_INTERVALS = 5           # 07 §3.1 CAI 列

# build_features.py 產出的表叫 feat_customer，主鍵是 person_key / cust_id
ID_CANDIDATES = ["person_key", "cust_id", "customer_id", "cust", "custom_id",
                 "cid", "客戶ID", "Custom ID"]
DEFAULT_TABLE = "feat_customer"


# ── 規格檔 ───────────────────────────────────────────────
def load_spec(spec_path: Path, override_vars: list[str] | None) -> dict[str, Any] | None:
    """讀 cluster_spec.json。讀不到就是 error —— input_vars 是白名單檢查與
    §八 S1 gate 的唯一資料來源，沒有它整條紀律鏈是斷的（07 §3.3）。"""
    spec: dict[str, Any] = {}
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(f"cluster_spec.json 解析失敗（{e}）",
                f"修正 JSON 格式：{spec_path}")
            return None
    elif override_vars is None:
        tpl = SKILL_ROOT / "templates" / "cluster_spec.json"
        err(f"找不到規格檔：{spec_path}",
            f"07 §3.3 明訂四項決策強制記錄。先複製範本再填："
            f"cp \"{tpl}\" \"{spec_path}\"")
        return None

    if override_vars:
        spec["input_vars"] = override_vars
        infos.append(f"  └ input_vars 由 --vars 覆蓋：{', '.join(override_vars)}")

    if not spec.get("input_vars"):
        err("cluster_spec.json 的 input_vars 是空的",
            "填入分群輸入變數。它同時是 07 §8.2 S1 gate 的資料來源")
        return None
    return spec


# ── (1) 白名單檢查（18-E2）────────────────────────────────
# 已經取過對數的欄（LN_F / LN_M）不能再 log 一次；偏度若仍超標只能走分位分箱
_ALREADY_LOGGED = re.compile(r"^(ln|log)_|__log1?p?$")


def classify_var(name: str) -> tuple[str, str] | None:
    low = name.strip().lower()
    for cat, pat, family in WHITELIST:
        if pat.match(low):
            if family == "log" and _ALREADY_LOGGED.search(low):
                family = "bin"
            return cat, family
    return None


def blacklist_hit(name: str) -> str | None:
    return classify_blacklist(name)


def check_whitelist(input_vars: list[str]) -> dict[str, tuple[str, str]]:
    """回傳 {欄名: (白名單類別, 轉換族)}。違規者進 errors。"""
    classified: dict[str, tuple[str, str]] = {}
    bad_demo: list[str] = []
    bad_other: list[str] = []

    for v in input_vars:
        hit = blacklist_hit(v)
        if hit:
            bad_demo.append(f"{v}（{hit}）")
            continue
        cls = classify_var(v)
        if cls is None:
            bad_other.append(v)
            continue
        classified[v] = cls

    if bad_demo:
        err(f"人口統計／M5 標籤變數進了分群矩陣：{', '.join(bad_demo)}",
            "18-E2 明確禁止。把它們從 input_vars 拿掉；"
            "人口變數的合法位置是 07 §8.4 的卡方獨立性檢定（先分群、再看人口組成）")
    if bad_other:
        err(f"不在白名單的變數：{', '.join(bad_other)}",
            "07 §3.1 白名單只有 R / F / M / RFM Score / CAI / CRI / 因素分數 /"
            " LN_F / LN_M，多一個都不行。要新增請先改 07 §3.1 並寫理由")
    if classified:
        ok(f"白名單通過（{len(classified)} 個輸入變數）")
        for v, (cat, fam) in classified.items():
            detail(infos, f"{v:<26} → {cat}（轉換族 {fam}）")
    return classified


# ── (2) CRI 血緣檢查（07 §3.1）────────────────────────────
LINEAGE_COLS = ("prior_group_type", "prior_group_cols",
                "prior_group_demographic_cols")


def read_data_lineage(df: pd.DataFrame) -> dict[str, str] | None:
    """從特徵表讀 build_features 落下的血緣欄位。沒有這幾欄就回 None。

    這三欄是常數欄（每列相同）。出現多個值代表這張表是兩批不同先驗群的
    特徵表拼起來的 —— 那本身就是要擋的狀況，交給呼叫端報 error。
    """
    if not all(c in df.columns for c in LINEAGE_COLS):
        return None
    out: dict[str, str] = {}
    for c in LINEAGE_COLS:
        vals = {("" if pd.isna(v) else str(v)) for v in df[c].unique()}
        out[c] = ("＜多值＞" + "／".join(sorted(vals))) if len(vals) > 1 else (
            vals.pop() if vals else "")
    return out


def check_cri_lineage(classified: dict[str, tuple[str, str]], spec: dict[str, Any],
                      df: pd.DataFrame) -> None:
    """CRI 能不能進矩陣，**以資料裡的血緣為準**（07 §3.1）。

    舊版只看 cluster_spec.json 的 cri_prior_type，那是自我宣告 ——
    先驗群明明用性別分，spec 打 "behavioral" 就能過關。現在的順序是：
      1. 讀特徵表的 prior_group_cols，用共用清單（demographic_vars.py）**重新判定**；
      2. spec 的 cri_prior_type 只當交叉檢查，不一致 → error 並列出兩邊各說什麼；
      3. 資料判定不是 behavioral → error，不管 spec 寫什麼。
    """
    cri_vars = [v for v, (cat, _) in classified.items() if cat == "CRI"]
    if not cri_vars:
        ok("input_vars 不含 CRI，血緣檢查不適用")
        return

    cri_txt = ", ".join(cri_vars)
    spec_prior = spec.get("cri_prior_type")
    spec_txt = str(spec_prior).strip().lower() if spec_prior is not None else None

    data = read_data_lineage(df)
    if data is None:
        # 舊版 build_features 產的表。只剩自我宣告可用 —— 照舊擋 demographic，
        # 但必須講明白這一關現在是沒有牙齒的。
        warn(f"輸入資料沒有血緣欄位（{', '.join(LINEAGE_COLS)}），"
             f"CRI 血緣只能採信 cluster_spec.json 的自我宣告",
             "這張特徵表是舊版 build_features 產的。自我宣告攔不到填錯或亂填 —— "
             "用現在的 build_features.py 重跑一次特徵表，血緣才會跟著資料走（07 §3.1）")
        if spec_txt is None:
            err(f"input_vars 含 CRI（{cri_txt}）但 cluster_spec.json 的 "
                f"cri_prior_type 沒填（缺這個鍵，或值是 null）",
                "CRI 的分母含先驗群的群內變異數 τ²_g，先驗群用什麼分會直接決定 CRI 的值。"
                "把 spec 的 cri_prior_type 填成 \"behavioral\"（行為分層，如 F 三分位／"
                "品類廣度）或 \"demographic\"（人口變數）—— 看你跑 build_features.py 時 "
                "--prior-group-cols 給的是哪一種欄位，誠實填")
        elif spec_txt != PRIOR_BEHAVIORAL:
            err(f"CRI 的先驗群是 {spec_prior}（spec 自我宣告），不得進分群矩陣",
                "07 §3.1：先驗群用人口變數時，交易紀錄完全相同的兩人也會因人口欄不同"
                "拿到不同 CRI（同一個 s²/n 下 CRI 差到 21.4 vs 79.1）。"
                "把 CRI 從 input_vars 拿掉，或先驗群改用行為分層重算")
        else:
            ok(f"CRI 血緣（僅自我宣告）：cri_prior_type = behavioral（{cri_txt}）")
        return

    recorded = data["prior_group_type"]
    cols_raw = data["prior_group_cols"]

    if recorded.startswith("＜多值＞") or cols_raw.startswith("＜多值＞"):
        err(f"輸入資料的血緣欄位有多個值（prior_group_type = {recorded}，"
            f"prior_group_cols = {cols_raw}）",
            "同一張特徵表裡混了兩批不同先驗群算出來的 CRI，它們不在同一個尺度上。"
            "分開跑 build_features.py，不要把兩批 concat 起來再分群")
        return

    cols = [c for c in cols_raw.split(",") if c]
    if cols:
        effective, _demo = classify_prior_cols(cols)
    else:
        effective = recorded if recorded in PRIOR_TYPES else PRIOR_NONE

    ok(f"CRI 血緣來源：特徵表的 {'／'.join(LINEAGE_COLS)} 欄（不是 spec 的自我宣告）")
    detail(infos, f"先驗群欄位：{describe_prior_cols(cols)}"
                  f"｜特徵表記錄 {recorded}｜本次重判 {effective}"
                  f"｜spec 宣告 {spec_prior if spec_prior is not None else '（未填）'}")

    if cols and effective != recorded:
        warn(f"血緣重判與特徵表記錄不同：記錄 {recorded}、重判 {effective}",
             "多半是 demographic_vars.py 的人口變數清單在特徵表產出之後更新過。"
             "以重判為準（比較嚴），並重跑 build_features.py 讓兩邊一致")

    # 根本沒有先驗分群層：CRI 整欄是 N/A，先講這件事，不要叫人去把 spec 改成 "none"
    if effective == PRIOR_NONE:
        err(f"input_vars 含 CRI（{cri_txt}），但**資料說這批特徵沒有先驗分群層**"
            f"（prior_group_type = none）"
            + (f"，而 cluster_spec.json 說 {spec_prior}" if spec_txt is not None else ""),
            "沒有先驗群就沒有 τ²_g，CRI 全部是 N/A，整欄會在缺值那一步被剔光。"
            "把 CRI 從 input_vars 拿掉，或用 build_features.py 的 --dim 與 "
            "--prior-group-cols 給一組行為分層先驗群重跑 —— 改 spec 的字串不會生出 CRI")
        return

    # ── 交叉檢查：資料說什麼 vs spec 說什麼 ──
    # 07 §3.1 原文是「僅當 cluster_spec.json 的 cri_prior_type == behavioral 時
    # CRI 才可進分群輸入」，所以 spec 沒填一樣是 error —— 資料的血緣是**加上去的**
    # 一道關卡，不是拿來免除規格檔那一道。
    if spec_txt is None:
        err(f"input_vars 含 CRI（{cri_txt}）但 cluster_spec.json 的 cri_prior_type "
            f"沒填（缺這個鍵，或值是 null）；**資料說 {effective}**"
            f"（先驗群欄位 {cols_raw or '（無）'}）",
            f"07 §3.1 要求規格檔明寫 cri_prior_type，07 §3.3 要求四項決策入檔。"
            f"照資料把它填成 \"{effective}\"")
    elif spec_txt != effective:
        err(f"CRI 血緣不一致：**資料說 {effective}**（先驗群欄位 {cols_raw or '（無）'}"
            + (f"，命中人口變數清單的是 {data['prior_group_demographic_cols']}"
               if data["prior_group_demographic_cols"] else "")
            + f"）、**cluster_spec.json 說 {spec_prior}**",
            f"以資料為準 —— spec 的 cri_prior_type 是自我宣告，填錯或亂填都不該能放行，"
            f"這一關就是為了攔它。把 spec 的 cri_prior_type 改成 \"{effective}\"，"
            f"或用真正的行為分層先驗群重跑 build_features.py 再進來。"
            f"（判定依據：scripts/demographic_vars.py 的人口變數清單）")

    # ── 判決：只有 behavioral 放行 ──
    if effective == PRIOR_BEHAVIORAL:
        if spec_txt == PRIOR_BEHAVIORAL:
            ok(f"CRI 血緣通過：資料與 spec 都是 behavioral（{cri_txt}）")
        detail(infos, "07 §8.4 排除條款仍要人工確認：先驗群用到的欄位不得進卡方表")
        detail(infos, "behavioral 的判定是「先驗欄位沒有命中人口變數清單」，"
                      "不等於已證明是行為量 —— 清單見 scripts/demographic_vars.py")
        return

    err(f"CRI 的先驗群是{'人口變數' if effective == 'demographic' else '人口變數與其他欄位混用'}"
        f"（{data['prior_group_demographic_cols'] or cols_raw}），不得進分群矩陣",
        "07 §3.1：先驗群用人口變數時，交易紀錄完全相同的兩人也會因人口欄不同"
        "拿到不同 CRI（同一個 s²/n 下 CRI 差到 21.4 vs 79.1），等於把人口變數"
        "以非線性編碼送進矩陣。做法二選一：(a) 把 CRI 從 input_vars 拿掉；"
        "(b) 先驗群改用行為分層（如 F 三分位、品類廣度）重跑 build_features.py —— "
        "特徵表的 prior_group_type 變成 behavioral 才會放行，改 spec 的字串沒有用。"
        "另外，07 §8.4 排除條款：那批先驗人口變數也不得進卡方表")


# ── 資料讀取 ─────────────────────────────────────────────
def load_input(project: str, input_path: Path | None, table: str | None) -> pd.DataFrame | None:
    if input_path is not None:
        if not input_path.exists():
            err(f"找不到輸入檔：{input_path}", "確認路徑，或改用 --table 從專案資料庫讀")
            return None
        try:
            if input_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(input_path)
            elif input_path.suffix.lower() in (".csv", ".txt"):
                df = pd.read_csv(input_path)
            else:
                err(f"不支援的副檔名：{input_path.suffix}", "請給 .parquet 或 .csv")
                return None
        except Exception as e:  # noqa: BLE001
            err(f"讀取失敗：{input_path}（{e}）", "檢查檔案是否完整或被鎖住")
            return None
        ok(f"輸入：{input_path.name}（{len(df):,} 列 × {len(df.columns)} 欄）")
        return df

    if table:
        try:
            from db import connect  # 唯一合法的連線介面（03 §7.1）
            with connect(project, read_only=True) as con:
                df = con.execute(f'SELECT * FROM "{table}"').df()
        except Exception as e:  # noqa: BLE001
            err(f"從專案資料庫讀 {table} 失敗（{e}）",
                "確認表名，或先跑 build_features.py 產生顧客特徵表")
            return None
        ok(f"輸入：資料庫表 {table}（{len(df):,} 列 × {len(df.columns)} 欄）")
        return df

    err("沒有指定輸入來源",
        f"用 --input <parquet/csv> 或 --table <表名> 二選一。"
        f"build_features.py 產出的表是 {DEFAULT_TABLE}，"
        f"檔案在 顧客特徵表/feat_customer_asof<日期>.parquet")
    return None


def pick_id_col(df: pd.DataFrame, explicit: str | None) -> str | None:
    if explicit:
        if explicit not in df.columns:
            err(f"找不到 id 欄：{explicit}", f"現有欄位：{', '.join(map(str, df.columns[:15]))}")
            return None
        return explicit
    for c in ID_CANDIDATES:
        if c in df.columns:
            return c
    warn("找不到客戶 id 欄", f"矩陣會用列序當 id。要指定請加 --id-col。"
                            f"（找過 {', '.join(ID_CANDIDATES[:5])}）")
    return None


# ── (3) 偏度與轉換 ───────────────────────────────────────
def skewness(x: np.ndarray) -> float:
    """樣本偏度（scipy 的 bias=False，與 M4 門檻同口徑）。"""
    from scipy import stats
    return float(stats.skew(x, bias=False))


def ntile5_edges(x: np.ndarray) -> list[float]:
    return [float(np.quantile(x, q)) for q in NTILE_QUANTILES]


def apply_ntile5(x: np.ndarray, edges: list[float]) -> np.ndarray:
    """回傳 0–4 的箱號。等同 SQL 的 NTILE(5)，但並列值不會被拆到兩箱。"""
    return np.searchsorted(np.asarray(edges), x, side="right").astype(float)


def transform_one(
    name: str, family: str, x: np.ndarray, forced: dict[str, Any] | None
) -> tuple[str, np.ndarray, dict[str, Any], float, float]:
    """回傳 (新欄名, 轉換後的值, 參數, 轉換前偏度, 轉換後偏度)。"""
    sk0 = skewness(x)

    if forced is not None:                     # --reuse-scaler：沿用舊決策
        method = forced.get("method", "none")
        if method == "log1p":
            y = np.log1p(x)
            return f"{name}__log1p", y, {"method": "log1p"}, sk0, skewness(y)
        if method == "ntile5":
            edges = list(forced.get("edges", []))
            y = apply_ntile5(x, edges)
            return f"{name}__bin5", y, {"method": "ntile5", "edges": edges}, sk0, skewness(y)
        return name, x, {"method": "none"}, sk0, sk0

    if family in ("none", "nozs") or abs(sk0) <= SKEW_THRESHOLD:
        return name, x, {"method": "none"}, sk0, sk0

    if family == "log":
        if float(np.min(x)) <= -1.0:
            warn(f"{name} 偏度 {sk0:.2f} 但含 ≤ −1 的值，log1p 會產生 NaN",
                 "改走 NTILE(5) 分位分箱")
        else:
            y = np.log1p(x)
            sk1 = skewness(y)
            if abs(sk1) <= SKEW_THRESHOLD:
                return f"{name}__log1p", y, {"method": "log1p"}, sk0, sk1
            warn(f"{name} log1p 後偏度仍為 {sk1:.2f}（> {SKEW_THRESHOLD}）",
                 "退回 NTILE(5) 分位分箱，並在轉換紀錄第四欄寫明「log 為什麼不行」")

    edges = ntile5_edges(x)
    y = apply_ntile5(x, edges)
    n_bins = len(np.unique(y))
    if n_bins < 5:
        warn(f"{name} 分位分箱只切出 {n_bins} 箱（目標 5 箱）",
             "並列值太多。確認這個欄位是不是本來就該當類別變數處理")
    return f"{name}__bin5", y, {"method": "ntile5", "edges": edges}, sk0, skewness(y)


# ── (6) WGSS 貢獻表 + (Step 4) ARI ───────────────────────
def wgss_decompose(X: np.ndarray, labels: np.ndarray, cols: list[str]) -> pd.DataFrame:
    """逐變數拆解 TSS / WGSS / BGSS。

    「對 WGSS 下降的貢獻」＝ 從 k=1 的 TSS 降到 WGSS(k) 的降幅，也就是 BGSS_j
    （此處為實作判斷：07 §3.3 只寫「貢獻百分比」，沒給公式）。
    """
    rows = []
    for j, c in enumerate(cols):
        xj = X[:, j]
        tss = float(((xj - xj.mean()) ** 2).sum())
        wgss = 0.0
        for g in np.unique(labels):
            m = labels == g
            wgss += float(((xj[m] - xj[m].mean()) ** 2).sum())
        rows.append({"變數": c, "TSS": tss, "WGSS": wgss, "BGSS_WGSS下降量": tss - wgss})
    out = pd.DataFrame(rows)
    total = out["BGSS_WGSS下降量"].sum()
    out["貢獻百分比"] = out["BGSS_WGSS下降量"] / total * 100 if total > 0 else np.nan
    return out.sort_values("貢獻百分比", ascending=False).reset_index(drop=True)


def fit_labels(X: np.ndarray, k: int, seed: int, n_init: int) -> np.ndarray:
    from sklearn.cluster import KMeans
    return KMeans(n_clusters=k, random_state=seed, n_init=n_init).fit_predict(X)


# ── 主流程 ───────────────────────────────────────────────
def main() -> int:
    ap = GateArgumentParser(
        description="M6 分群矩陣前處理（白名單／CRI 血緣／偏度／標準化／WGSS 貢獻）")
    ap.add_argument("project", help="專案代號")
    ap.add_argument("--input", type=Path, help="顧客特徵表 .parquet / .csv")
    ap.add_argument("--table", nargs="?", const=DEFAULT_TABLE,
                    help=f"改從專案資料庫讀這張表（不給值時用 {DEFAULT_TABLE}）")
    ap.add_argument("--spec", type=Path, help="cluster_spec.json（預設 模型輸出/cluster_spec.json）")
    ap.add_argument("--vars", help="逗號分隔，覆蓋 spec 的 input_vars（臨時試算用）")
    ap.add_argument("--id-col", help="客戶 id 欄名")
    ap.add_argument("--k", type=int, help="暫定 k，只用來算 WGSS 貢獻與 ARI（預設取 spec）")
    ap.add_argument("--reuse-scaler", type=Path, help="沿用既有 scaler.json 的轉換與標準化參數")
    ap.add_argument("--no-spec-update", action="store_true", help="不回填 spec 的 preflight 欄位")
    ap.add_argument("--dry-run", action="store_true", help="只檢查，不寫任何檔案")
    ap.add_argument("--verbose", action="store_true", help="連通過項也列出")
    args = ap.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run
    p = project_dir(args.project, create=not args.dry_run)
    spec_path = args.spec or (p.models / "cluster_spec.json")

    print("=" * 68)
    print("行銷數據分析 Skill — M6 分群矩陣前處理")
    print(f"專案：{args.project}")
    print(f"規格：{spec_path}")
    print("=" * 68)

    override = [v.strip() for v in args.vars.split(",")] if args.vars else None
    spec = load_spec(spec_path, override)
    df = load_input(args.project, args.input, args.table)
    if spec is None or df is None:
        return report(args.verbose)

    input_vars: list[str] = list(spec["input_vars"])

    # (1) 白名單
    classified = check_whitelist(input_vars)
    # (2) CRI 血緣 —— 以資料裡的血緣欄位為準，spec 只做交叉檢查
    check_cri_lineage(classified, spec, df)
    if errors:
        return report(args.verbose)

    # 欄位存在性
    missing = [v for v in input_vars if v not in df.columns]
    if missing:
        err(f"輸入資料缺少 input_vars 的欄位：{', '.join(missing)}",
            f"確認 build_features 有產出這些欄，或修正 spec。"
            f"現有欄位前 20 個：{', '.join(map(str, df.columns[:20]))}")
        return report(args.verbose)

    id_col = pick_id_col(df, args.id_col)

    # CAI 的 n_intervals 條款（07 §3.1）
    has_cai = any(cat == "CAI" for cat, _ in classified.values())
    if has_cai:
        ncol = next((c for c in ("n_intervals", "n_interval", "interval_cnt") if c in df.columns), None)
        if ncol is None:
            warn("input_vars 含 CAI 但輸入資料沒有 n_intervals 欄",
                 f"07 §3.1：n_intervals < {CAI_MIN_INTERVALS} 的 CAI 一律 N/A，"
                 f"無法驗證就有把雜訊當節奏的風險。請在 build_features 補上這一欄")
        else:
            cai_cols = [v for v, (cat, _) in classified.items() if cat == "CAI"]
            bad = df[ncol] < CAI_MIN_INTERVALS
            if bad.any():
                df.loc[bad, cai_cols] = np.nan
                warn(f"{int(bad.sum())} 位客戶的 n_intervals < {CAI_MIN_INTERVALS}，"
                     f"其 CAI 已置為 N/A",
                     "07 §3.1 明訂。這些人會在下一步因缺值被剔出矩陣，"
                     "樣本流失要寫進報告（18-E22）")
            else:
                ok(f"CAI 的 n_intervals 全部 ≥ {CAI_MIN_INTERVALS}")

    # 缺值處理 —— 分群不能有 NaN，剔除並記錄（18-E22）
    work = df[([id_col] if id_col else []) + input_vars].copy()
    for v in input_vars:
        work[v] = pd.to_numeric(work[v], errors="coerce")
    n_before = len(work)
    bad_mask = work[input_vars].isna().any(axis=1)
    dropped = work[bad_mask].copy()
    work = work[~bad_mask].reset_index(drop=True)
    n_after = len(work)
    if n_before != n_after:
        warn(f"樣本流失：{n_before:,} → {n_after:,} 列（剔除 {n_before - n_after:,} 列含缺值）",
             "18-E22：樣本數變化必須在報告交代。明細見 隔離區/cluster_matrix_dropped.csv")
    else:
        ok(f"樣本無流失：{n_after:,} 列全部進矩陣")

    if n_after < 30:
        err(f"可用樣本只剩 {n_after} 列", "分群沒有意義。先查缺值來源，不要直接往下跑")
        return report(args.verbose)

    # (3) 偏度與轉換
    reuse: dict[str, Any] = {}
    if args.reuse_scaler:
        rp = args.reuse_scaler if args.reuse_scaler.is_absolute() else (p.root / args.reuse_scaler)
        if not rp.exists():
            err(f"找不到 scaler：{rp}", "確認路徑，或拿掉 --reuse-scaler 重新 fit")
            return report(args.verbose)
        reuse = json.loads(rp.read_text(encoding="utf-8")).get("vars", {})
        ok(f"沿用既有 scaler：{rp}（{len(reuse)} 個變數）")

    tr_rows: list[dict[str, Any]] = []
    mat: dict[str, np.ndarray] = {}
    var_params: dict[str, dict[str, Any]] = {}
    no_scale: set[str] = set()

    from scipy import stats as _st
    for v in input_vars:
        cat, family = classified[v]
        x = work[v].to_numpy(dtype=float)
        newname, y, prm, sk0, sk1 = transform_one(v, family, x, reuse.get(v))
        rho = float(_st.spearmanr(x, y).statistic) if prm["method"] != "none" else 1.0
        if prm["method"] != "none" and abs(rho) < SPEARMAN_THRESHOLD:
            warn(f"{v} 轉換後排序相關 Spearman = {rho:.3f}（< {SPEARMAN_THRESHOLD}）",
                 "06 §6.1：這是實作錯誤的訊號，不是統計訊號。回頭檢查分箱切點")
        if prm["method"] == "none" and abs(sk0) > SKEW_THRESHOLD and family == "none":
            warn(f"{v} 偏度 {sk0:.2f} 超過門檻但依白名單不轉換（{cat}）",
                 "07 §3.1 指定此類別用原值。若確實偏斜嚴重，在報告寫明")
        if family == "nozs":
            no_scale.add(newname)
        mat[newname] = y
        var_params[v] = {"category": cat, "out_col": newname,
                         "skew_before": sk0, "skew_after": sk1, "spearman": rho, **prm}
        tr_rows.append({
            "原欄名": v, "白名單類別": cat, "產出欄名": newname,
            "轉換方法": prm["method"],
            "參數": json.dumps(prm.get("edges"), ensure_ascii=False) if "edges" in prm else "",
            "轉換前偏度": round(sk0, 4), "轉換後偏度": round(sk1, 4),
            "Spearman(原,轉)": round(rho, 4),
            "結論": ("通過" if abs(sk1) <= SKEW_THRESHOLD else "偏度仍超標，報告須寫明"),
        })

    n_transformed = sum(1 for r in tr_rows if r["轉換方法"] != "none")
    max_skew_after = max(abs(r["轉換後偏度"]) for r in tr_rows)
    if max_skew_after <= SKEW_THRESHOLD:
        ok(f"偏度關卡通過：轉換 {n_transformed} 欄，轉換後最大 |skew| = {max_skew_after:.2f}")
    else:
        warn(f"轉換後仍有欄位 |skew| = {max_skew_after:.2f} > {SKEW_THRESHOLD}",
             "07 §四 關卡 2 未過。報告要寫明這一欄用了什麼、為什麼還是偏")
    for r in tr_rows:
        detail(infos, f"{r['原欄名']:<24} skew {r['轉換前偏度']:>7.3f} → "
                      f"{r['轉換後偏度']:>7.3f}（{r['轉換方法']}）")

    cols = list(mat.keys())
    X_raw = np.column_stack([mat[c] for c in cols])

    # (5) 尺度比檢查（07 §四 關卡 1）
    sd = X_raw.std(axis=0, ddof=1)
    rng = X_raw.max(axis=0) - X_raw.min(axis=0)
    zero_sd = [c for c, s in zip(cols, sd) if s == 0]
    if zero_sd:
        err(f"常數欄（sd = 0）：{', '.join(zero_sd)}",
            "無法 z-score，對距離也沒有任何貢獻。從 input_vars 拿掉")
        return report(args.verbose)

    sd_ratio = float(sd.max() / sd.min())
    rng_ratio = float(rng.max() / rng.min()) if rng.min() > 0 else float("inf")
    scaler_kind = str(spec.get("scaler", "zscore")).lower()

    if sd_ratio > SCALE_RATIO_THRESHOLD:
        msg = (f"標準化前尺度比 max(sd)/min(sd) = {sd_ratio:,.1f}（極差比 {rng_ratio:,.1f}）"
               f"，超過門檻 {SCALE_RATIO_THRESHOLD:.0f}")
        if scaler_kind == "none":
            err(msg, "07 §四 關卡 1：> 10 沒做標準化就是**禁行，不是警告**。"
                     "把 spec 的 scaler 改成 zscore（或有離群時改 robust）再重跑")
            return report(args.verbose)
        warn(msg, f"已用 {scaler_kind} 標準化解決。但報告的尺度決策段要寫這個數字 —— "
                  f"它就是「未標準化的話 WGSS 幾乎全部來自最大尺度那一欄」的證據")
    else:
        ok(f"標準化前尺度比 = {sd_ratio:,.2f}（≤ {SCALE_RATIO_THRESHOLD:.0f}），"
           f"極差比 {rng_ratio:,.2f}")
    detail(infos, "各欄 sd：" + "、".join(f"{c}={s:,.4g}" for c, s in zip(cols, sd)))

    # (4) 標準化 —— 非監督在整個分析集 fit（06 §5.2）
    if scaler_kind not in ("zscore", "none", "robust"):
        warn(f"spec 的 scaler = {scaler_kind}，本腳本只實作 zscore",
             "改成 zscore，或自行擴充本腳本並在 06 §5.2 補規則")
    center = X_raw.mean(axis=0)
    scale = X_raw.std(axis=0, ddof=0)          # 與 sklearn StandardScaler 同口徑
    if scaler_kind == "robust":
        center = np.median(X_raw, axis=0)
        iqr = np.percentile(X_raw, 75, axis=0) - np.percentile(X_raw, 25, axis=0)
        scale = np.where(iqr > 0, iqr, X_raw.std(axis=0, ddof=0))
        ok("標準化：RobustScaler（中位數／IQR），fit 在整個分析集")
    for i, c in enumerate(cols):
        if c in no_scale:                       # 因素分數已是標準分數
            center[i], scale[i] = 0.0, 1.0

    if reuse:
        reused = []
        for i, c in enumerate(cols):
            src = next((d for d in reuse.values() if d.get("out_col") == c), None)
            if src and "center" in src:
                center[i], scale[i] = float(src["center"]), float(src["scale"])
                reused.append(c)
            else:
                warn(f"{c} 在舊 scaler.json 裡沒有 center/scale，改用本批資料重新 fit",
                     "換批資料用不同參數，群定義會漂移。確認舊檔是不是同一組 input_vars")
        detail(infos, f"沿用舊 center/scale 的欄位：{', '.join(reused) or '（無）'}")
    X_std = (X_raw - center) / scale
    sd_ratio_std = float(X_std.std(axis=0, ddof=1).max() / X_std.std(axis=0, ddof=1).min())
    if scaler_kind != "robust":
        ok(f"標準化：z-score，fit 在整個分析集（{n_after:,} 列，非監督沒有 train/test）")
    if no_scale:
        detail(infos, f"不再 z-score（因素分數已是標準分數）：{', '.join(sorted(no_scale))}")
    detail(infos, f"標準化後尺度比 = {sd_ratio_std:.4f}")

    # (6) WGSS 貢獻表 + Step 4 ARI
    k = args.k or spec.get("k") or 4
    seed = int(spec.get("seed", 42))
    n_init = int(spec.get("n_init", 10))
    if not args.k and not spec.get("k"):
        detail(infos, "spec 沒有 k，暫定 k=4 只為了算 WGSS 貢獻與 ARI；"
                      "正式的 k 由 07 §五 決定（此處為實作判斷）")
    wgss_tbl, ari = None, None
    try:
        lab_std = fit_labels(X_std, int(k), seed, n_init)
        wgss_tbl = wgss_decompose(X_std, lab_std, cols)
        top = wgss_tbl.iloc[0]
        if float(top["貢獻百分比"]) > WGSS_DOMINANCE_PCT:
            warn(f"WGSS 下降有 {top['貢獻百分比']:.1f}% 來自單一變數 {top['變數']}"
                 f"（> {WGSS_DOMINANCE_PCT:.0f}%）",
                 "07 §四 關卡 3：這個分群實質上就是那一個變數的切法。"
                 "先分辨是單點離群還是次族群（< 1% 無結構 = 單點查輸入錯誤；"
                 "≥ 5% 或密度雙峰 = 次族群，不准刪，分開建模），"
                 "報告必須寫理由。絕不先 winsorize")
        else:
            ok(f"WGSS 貢獻關卡通過：最大單一變數 {top['變數']} 佔 "
               f"{top['貢獻百分比']:.1f}%（≤ {WGSS_DOMINANCE_PCT:.0f}%）")
        for _, r in wgss_tbl.iterrows():
            detail(infos, f"{r['變數']:<28} {r['貢獻百分比']:>6.2f}%")

        # Step 4：標準化前 vs 標準化後的群成員 ARI
        from sklearn.metrics import adjusted_rand_score
        lab_raw = fit_labels(X_raw, int(k), seed, n_init)
        ari = float(adjusted_rand_score(lab_raw, lab_std))
        if ari < ARI_THRESHOLD:
            warn(f"標準化前後群成員 ARI = {ari:.3f}（< {ARI_THRESHOLD}，k={k}）",
                 "07 §3.3 Step 4：尺度決策改變了整個分群。這不是錯誤，是必須寫進"
                 "報告的證據 —— 說明為什麼選 z-score 而不是原尺度")
        else:
            ok(f"標準化前後群成員 ARI = {ari:.3f}（k={k}，尺度決策對群成員影響有限）")
    except Exception as e:  # noqa: BLE001
        warn(f"WGSS 貢獻表／ARI 算不出來（{e}）",
             "gate3 與 §3.3 Step 4 缺證據。確認 sklearn 可用後重跑")

    if errors:
        return report(args.verbose)

    # ── 寫檔 ─────────────────────────────────────────────
    if args.dry_run:
        infos.append("  └ --dry-run：以下檔案都沒有實際寫出")
    else:
        out = pd.DataFrame(X_std, columns=cols)
        if id_col:
            out.insert(0, id_col, work[id_col].to_numpy())
        p.models.mkdir(parents=True, exist_ok=True)
        (p.tables / "分群輪廓").mkdir(parents=True, exist_ok=True)
        (p.tables / "轉換前後對照").mkdir(parents=True, exist_ok=True)
        p.quarantine.mkdir(parents=True, exist_ok=True)

        mpath = p.models / "cluster_matrix.parquet"
        out.to_parquet(mpath, index=False)
        ok(f"矩陣已寫出：{mpath}（{len(out):,} × {len(cols)}）")

        for i, c in enumerate(cols):
            src = next(d for d in var_params.values() if d["out_col"] == c)
            src["center"], src["scale"] = float(center[i]), float(scale[i])
        spath = p.models / "scaler.json"
        spath.write_text(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project": args.project,
            "source": str(args.input or f"table:{args.table}"),
            "n_rows_fit": n_after,
            "fit_on": "整個分析集（非監督沒有 train/test，06 §5.2）",
            "scaler": scaler_kind,
            "sd_ddof": 0,
            "vars": var_params,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        ok(f"scaler 參數已寫出：{spath}（換批資料重跑用 --reuse-scaler 指這個檔）")

        tpath = p.tables / "轉換前後對照" / "cluster_matrix_transform.csv"
        pd.DataFrame(tr_rows).to_csv(tpath, index=False, encoding="utf-8-sig")
        ok(f"轉換對照表：{tpath}")

        if wgss_tbl is not None:
            wpath = p.tables / "分群輪廓" / "wgss_contribution.csv"
            w = wgss_tbl.copy()
            w["結論"] = np.where(w["貢獻百分比"] > WGSS_DOMINANCE_PCT,
                                 f"超過 {WGSS_DOMINANCE_PCT:.0f}%，報告須寫理由", "通過")
            w.to_csv(wpath, index=False, encoding="utf-8-sig")
            ok(f"WGSS 貢獻表：{wpath}")

        if len(dropped):
            dpath = p.quarantine / "cluster_matrix_dropped.csv"
            dropped.to_csv(dpath, index=False, encoding="utf-8-sig")
            ok(f"被剔除的列：{dpath}（{len(dropped):,} 列）")

        if not args.no_spec_update and spec_path.exists():
            spec.setdefault("preflight", {})
            spec["preflight"].update({
                # gate1_scale_ratio 記的是**產出矩陣本身**的尺度比（kmeans_preflight.py
                # 拿到的就是這張矩陣）；標準化之前的比值另存 _raw，它是報告要引用的數字
                "gate1_scale_ratio": round(sd_ratio_std, 4),
                "gate1_scale_ratio_raw": round(sd_ratio, 4),
                "gate1_pass": bool(sd_ratio_std <= SCALE_RATIO_THRESHOLD),
                "gate2_skew_max_abs": round(float(max_skew_after), 4),
                "gate2_pass": bool(max_skew_after <= SKEW_THRESHOLD),
                "gate3_max_wgss_contribution_pct":
                    (round(float(wgss_tbl.iloc[0]["貢獻百分比"]), 4) if wgss_tbl is not None else None),
                "gate3_pass": (bool(float(wgss_tbl.iloc[0]["貢獻百分比"]) <= WGSS_DOMINANCE_PCT)
                               if wgss_tbl is not None else None),
            })
            spec["matrix_cols"] = cols
            spec["scale_vs_raw_ari"] = (round(ari, 4) if ari is not None else None)
            spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
            ok(f"spec 的 preflight gate1–3 已回填：{spec_path}")

    return report(args.verbose)


def report(verbose: bool = False) -> int:
    if verbose and infos:
        print("\n通過")
        print("-" * 68)
        for m in infos:
            print(m if m.startswith("    ") or m.startswith("  ") else f"  ✅ {m}")

    if warnings:
        print("\n⚠ 可以往下走，但報告必須寫明")
        print("-" * 68)
        for m in warnings:
            print(m if m.startswith("    ") else f"  ⚠ {m}")

    if errors:
        print("\n⛔ 不准進分群，必須先處理")
        print("-" * 68)
        for m in errors:
            print(m if m.startswith("    ") else f"  ⛔ {m}")

    n_err = sum(1 for m in errors if not m.startswith("    "))
    n_warn = sum(1 for m in warnings if not m.startswith("    "))
    made = "（--dry-run，未寫檔）" if DRY_RUN else "矩陣已產出，"
    print("\n" + "=" * 68)
    if errors:
        print(f"結果：{n_err} 個 error、{n_warn} 個 warning → 矩陣未產出，M6 不准往下走")
        return EX_ERROR
    if warnings:
        print(f"結果：{n_warn} 個 warning → {made}報告要逐條回應上面的警告")
        return EX_WARN
    print(f"結果：全部通過 → {made}可以進 kmeans_preflight.py")
    return EX_OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"⛔ prep_cluster_matrix.py 本身失敗：{type(exc).__name__}: {exc}\n"
              f"   → 退出碼 {EX_SOFTWARE}（腳本自身異常）。修腳本（00 §八）。",
              file=sys.stderr)
        raise SystemExit(EX_SOFTWARE) from exc
