#!/usr/bin/env python3
"""
轉換紀錄落檔與驗收 —— M3 的六欄格式 `transform_log`（規格：06 §六）。

**為什麼需要它**：轉換做完當下每個人都記得「為什麼選 log 不選 Yeo-Johnson」，
兩週後沒有人記得。06 §六 把這件事寫成六欄硬格式，其中第四欄「為什麼是它」
是整份紀錄存在的理由 —— 它就是 00 §1.4「參數必附理由」在 M3 的實作。
包子自己的 HW2／HW5 盤點了 15 個參數，「有無理由」欄**全部是「無明文」**
（00 §1.4），這支腳本就是為了讓那件事不再發生：
沒寫理由的列**寫得進去但驗收不會過**，`--validate` 回退出碼 1。

它同時處理三件手寫容易出錯的事：
  · 第二欄（原分布特性）與第六欄（轉換後偏度、排序相關）從陣列自動算，
    不靠人抄數字 —— 抄錯就是 18-E8。
  · 六欄的欄名與**順序不可改**（06 §六 SCHEMA 明訂），寫入端統一產生。
  · CSV 用 **utf-8-sig**，Excel 直接點開不亂碼；同時產一份人眼看的 markdown。

檔案位置（**此處為實作判斷**）：
  06 §六 寫的是 `顧客特徵表/transform_log.csv`，本專案的落檔規範要求放
  `執行紀錄/`（00 §1.2：執行紀錄/ 放每一步的過程紀錄）。兩邊都要能對上，
  所以 **`執行紀錄/transform_log.csv` 是正本**，同時鏡射一份到
  `顧客特徵表/transform_log.csv` 給引用 06 §六 路徑的下游（verify_outputs）。
  兩份不一致時 `--validate` 出 warning，不會靜默挑一份用。

用法：
    # 1) 程式內（建議路線）：把原欄與轉換後欄丟進來，第 2、6 欄自動算
    from write_transform_log import row_from_arrays, write_log, validate_log

    rows = [row_from_arrays(
        col_name="m_net_twd__log", src=m, dst=np.log(m),
        method="ln(x)",
        rationale="情境 1 第 ② 順位。僅供分群輸入與 EDA；① Gamma GLM 是建模路線不產生欄位",
        params="—; fit_on=train")]
    write_log("2026Q3_電商", rows)
    validate_log("2026Q3_電商")

    # 2) 命令列
    python write_transform_log.py <專案代號> --from-json rows.json
    python write_transform_log.py <專案代號> --validate
    python write_transform_log.py <專案代號> --self-test   # 用素材庫樣本實跑一次

驗收（--validate）沿用 setup_check.py 的三桶 + 退出碼：
    0 = 全通過｜1 = 有 error（缺理由、缺欄、Spearman 破線）｜2 = 只有 warning
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 06 §六 的 SCHEMA：欄名與順序不可改 ──────────────────────
SCHEMA: list[str] = [
    "col_name",         # 1. 欄名（含轉換後綴，見 06 §4.2）
    "src_profile",      # 2. 原分布特性：n / min / max / p50 / skew / zero_ratio / neg_ratio
    "method",           # 3. 選了哪個轉換（或 "none + <模型族>"）
    "rationale",        # 4. ★ 為什麼是它：情境編號 + 第幾順位 + 前面順位為什麼不行
    "params",           # 5. 參數值 + fit_on（train / full）
    "post_skew",        # 6a. 轉換後偏度，門檻 |skew| < 1
    "spearman_vs_src",  # 6b. 排序相關，門檻 > 0.95
]

# markdown 表頭用 06 §六 表格的中文欄名，讓紀錄跟 reference 對得起來
SCHEMA_ZH: list[str] = [
    "欄名", "原分布特性", "選了哪個轉換",
    "為什麼是它（第幾順位、前面的為什麼不行）", "參數值", "轉換後偏度與排序相關",
]

CSV_NAME = "transform_log.csv"
MD_NAME = "transform_log.md"

# 「不適用」的統一寫法：不轉換的列（如情境 1 走 GLM、情境 3 走 Hurdle）沒有轉換後欄，
# 第六欄填這個，而不是留空 —— 00 §1.6「降級不留空」、00 §四 空值紀律。
NA = "—"

# 06 §6.1 的門檻
SKEW_MAX = 1.0          # |post_skew| < 1（M4 三門檻之一）
SPEARMAN_MIN = 0.95     # > 0.95；0.95~0.999 要能對上 n_rows_clipped
SPEARMAN_TIE = 0.999    # 低於這個值視為有並列，要查 winsorize/clip

# 第五欄一定要有數值的方法（參數是它的一部分，只寫方法名等於沒寫）
_METHOD_NEEDS_PARAM = re.compile(
    r"yeo[-_ ]?johnson|yj|box[-_ ]?cox|arcsinh|ihs|log\s*\(\s*x\s*\+|log_c"
    r"|winsor|clip|ntile|分位|分箱|quantile|shift|平移|logit|scale|z-?score",
    re.IGNORECASE,
)

# 第四欄要抓到的兩個東西：情境編號、順位（06 §六 CHECKS_M3 第 1 條）
_RE_SITUATION = re.compile(r"(情境|situation)\s*[:：]?\s*[0-7０-７]", re.IGNORECASE)
_RE_RANK = re.compile(
    r"(第\s*[①②③1-3一二三]\s*順位|順位\s*[①②③1-3]|rank\s*[=:]?\s*[1-3]|唯一順位)",
    re.IGNORECASE,
)

# 06 §3.3 的 winsorize 專用欄位。分支 C 才會有值；放在第五欄的 JSON 裡（實作判斷：
# CSV 攤不平巢狀結構，而 SCHEMA 的七個 key 不准增減，所以塞進 params 而不是加欄）。
WINSOR_REQUIRED = ["applied", "branch", "reason", "tried_before",
                   "lower_q", "upper_q", "n_rows_clipped", "pct_of_total_amount"]
WINSOR_NICE = ["lower_value", "upper_value", "pct_of_rows",
               "affected_cust_ids", "conclusion_flip"]


# ── 數字格式 ────────────────────────────────────────────────
def _num(v: float) -> str:
    """人看得懂的數字：整數加千分位，小數留 4 位。"""
    if v is None:
        return NA
    f = float(v)
    if f != f:  # NaN
        return "NaN"
    if abs(f) < 1e15 and float(f).is_integer():
        return f"{int(f):,}"
    return f"{f:,.4f}"


def _fmt_stat(v: float | None) -> str:
    """第六欄的統計量：固定 4 位小數，NaN 原樣寫出（NaN 是 bug 的證據，不可吞掉）。"""
    if v is None:
        return NA
    f = float(v)
    if f != f:
        return "NaN"
    return f"{f:.4f}"


def _as_float(s: str) -> float | None:
    """把第六欄字串轉回浮點；'—' 回 None，'NaN' 回 float('nan')。"""
    t = (s or "").strip()
    if t in ("", NA, "-", "不適用", "n/a", "N/A"):
        return None
    try:
        return float(t.replace(",", ""))
    except ValueError:
        return None


# ── 第二欄：原分布特性 ──────────────────────────────────────
def profile_series(x: Sequence[float]) -> str:
    """算第二欄。七項與 06 §六 SCHEMA 註解一致：n/min/max/p50/skew/zero/neg。

    偏度用 `scipy.stats.skew` 預設（bias=True），與 pick_transform.py 的
    情境路由同一個口徑 —— 兩支用不同口徑就會出現「路由說情境 1、紀錄說 skew<1」。
    有缺值時額外附 nan=（實作判斷：00 §四 要求缺漏顯性化，不可靜默 dropna）。
    """
    import numpy as np
    from scipy import stats

    a = np.asarray(x, dtype="float64")
    n_all = a.size
    a = a[~np.isnan(a)]
    n = a.size
    if n == 0:
        return "n=0（全為缺值）"
    parts = [
        f"n={n:,}",
        f"min={_num(a.min())}",
        f"max={_num(a.max())}",
        f"p50={_num(float(np.median(a)))}",
        f"skew={float(stats.skew(a)):.4f}",
        f"zero={float((a == 0).mean()):.1%}",
        f"neg={float((a < 0).mean()):.1%}",
    ]
    if n_all > n:
        parts.append(f"nan={n_all - n:,}")
    return ", ".join(parts)


def post_stats(src: Sequence[float], dst: Sequence[float]) -> tuple[float, float]:
    """算第六欄：(轉換後偏度, Spearman(原欄, 轉換後欄))。

    只用「兩邊都非缺」的列算 Spearman —— 若轉換自己製造了 NaN（log 吃到 0），
    偏度那一邊會是 NaN，06 §6.1 明訂那是 bug 不是統計問題，必須讓它浮出來，
    所以偏度**不** dropna。
    """
    import numpy as np
    from scipy import stats

    s = np.asarray(src, dtype="float64")
    d = np.asarray(dst, dtype="float64")
    if s.size != d.size:
        raise ValueError(
            f"原欄與轉換後欄長度不同（{s.size} vs {d.size}）—— "
            f"通常是轉換前先 dropna 了。請保留同一組列，缺值用 NaN 佔位再進來。"
        )
    post_skew = float(stats.skew(d)) if d.size else float("nan")
    both = ~(np.isnan(s) | np.isnan(d))
    if both.sum() < 3 or np.unique(d[both]).size < 2:
        rho = float("nan")
    else:
        rho = float(stats.spearmanr(s[both], d[both]).statistic)
    return post_skew, rho


# ── 一列紀錄 ────────────────────────────────────────────────
@dataclass
class TransformRow:
    """transform_log 的一列。六欄（第六欄拆成 6a/6b，共七個 key）。"""
    col_name: str
    src_profile: str
    method: str
    rationale: str
    params: str = NA
    post_skew: str = NA
    spearman_vs_src: str = NA
    winsorize: dict[str, Any] | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, str]:
        params = self.params or NA
        if self.winsorize is not None:
            blob = json.dumps(self.winsorize, ensure_ascii=False, sort_keys=True)
            params = f"{params}; winsorize={blob}" if params != NA else f"winsorize={blob}"
        return {
            "col_name": self.col_name,
            "src_profile": self.src_profile,
            "method": self.method,
            "rationale": self.rationale,
            "params": params,
            "post_skew": self.post_skew,
            "spearman_vs_src": self.spearman_vs_src,
        }


def row_from_arrays(
    col_name: str,
    method: str,
    rationale: str,
    src: Sequence[float],
    dst: Sequence[float] | None = None,
    params: str = NA,
    winsorize: dict[str, Any] | None = None,
) -> TransformRow:
    """建一列：第 2、6 欄自動算，第 3、4、5 欄由人給（那三欄是判斷不是計算）。

    dst=None 代表「不轉換，改模型」（情境 1 的 GLM、情境 3 的 Hurdle）——
    沒有轉換後欄，第六欄填 `—`，不是 0 也不是空白。
    """
    prof = profile_series(src)
    if dst is None:
        return TransformRow(col_name, prof, method, rationale, params,
                            NA, NA, winsorize)
    sk, rho = post_stats(src, dst)
    return TransformRow(col_name, prof, method, rationale, params,
                        _fmt_stat(sk), _fmt_stat(rho), winsorize)


def row_from_dict(d: dict[str, Any]) -> TransformRow:
    """從 JSON/dict 建列（pick_transform.py 的建議經人工確認後的進場口）。"""
    missing = [k for k in SCHEMA[:4] if not str(d.get(k, "")).strip()]
    if missing:
        who = str(d.get("col_name", "")).strip() or "(無欄名)"
        raise ValueError(
            f"「{who}」這一列缺欄：{', '.join(missing)} —— "
            f"六欄缺一不可（06 §六）。缺 rationale 更是直接違反 00 §1.4。\n"
            f"  該怎麼辦：補齊後再寫，或用 row_from_arrays() 讓第 2、6 欄自動算。"
        )
    return TransformRow(
        col_name=str(d["col_name"]).strip(),
        src_profile=str(d["src_profile"]).strip(),
        method=str(d["method"]).strip(),
        rationale=str(d["rationale"]).strip(),
        params=str(d.get("params") or NA).strip(),
        post_skew=str(d.get("post_skew") or NA).strip(),
        spearman_vs_src=str(d.get("spearman_vs_src") or NA).strip(),
        winsorize=d.get("winsorize"),
    )


# ── 落檔 ────────────────────────────────────────────────────
def log_paths(project: str, create: bool = False) -> tuple[Path, Path, Path]:
    """回 (正本 csv, markdown, 鏡射 csv)。"""
    p = project_dir(project, create=create)
    return p.log / CSV_NAME, p.log / MD_NAME, p.features / CSV_NAME


def _backup(path: Path) -> Path | None:
    """覆寫前先備份 —— 00 §1.2「一步一檔絕不覆寫」的精神：舊版本要查得到。"""
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_name(f"{path.stem}.{stamp}.bak{path.suffix}")
    bak.write_bytes(path.read_bytes())
    return bak


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_log(
    project: str,
    rows: Sequence[TransformRow | dict[str, Any]],
    merge: bool = True,
    mirror: bool = True,
) -> dict[str, Path]:
    """把列寫進 `執行紀錄/transform_log.csv`（utf-8-sig）與同名 markdown。

    merge=True（預設）：同 col_name 的舊列被新列取代，其餘保留 —— M3 是分批做的，
        每次只寫一欄不該把前面的洗掉。merge=False 則整份重寫。
    mirror=True：同步一份到 `顧客特徵表/transform_log.csv`（06 §六 的路徑）。
    覆寫前自動備份成 `transform_log.<時戳>.bak.csv`。
    """
    norm: list[TransformRow] = [
        r if isinstance(r, TransformRow) else row_from_dict(r) for r in rows
    ]
    csv_path, md_path, mirror_path = log_paths(project, create=True)

    out: list[dict[str, str]] = []
    if merge and csv_path.exists():
        new_names = {r.col_name for r in norm}
        out = [d for d in _read_rows(csv_path) if d.get("col_name") not in new_names]
    out.extend(r.to_dict() for r in norm)

    _backup(csv_path)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCHEMA, extrasaction="ignore")
        w.writeheader()
        for d in out:
            w.writerow({k: d.get(k, "") for k in SCHEMA})

    md_path.write_text(_render_md(project, out), encoding="utf-8")

    written = {"csv": csv_path, "md": md_path}
    if mirror:
        mirror_path.write_bytes(csv_path.read_bytes())
        written["mirror"] = mirror_path
    return written


def _md_cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", "<br>")


def _render_md(project: str, rows: list[dict[str, str]]) -> str:
    """人眼看的版本：六欄合併成 06 §六 表格的樣子，第六欄兩個數字併一格。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L = [
        f"# 轉換紀錄 — {project}",
        "",
        f"產生時間：{ts}　｜　列數：{len(rows)}　｜　格式：`06_前處理與轉換.md` §六（六欄）",
        "",
        "正本：`執行紀錄/transform_log.csv`（utf-8-sig）。這份 markdown 是唯讀的可讀版，",
        "改請改 CSV 或重跑 `write_transform_log.py`，不要手改這裡。",
        "",
        "| " + " | ".join(SCHEMA_ZH) + " |",
        "|" + "---|" * len(SCHEMA_ZH),
    ]
    for d in rows:
        sk, rho = d.get("post_skew", NA), d.get("spearman_vs_src", NA)
        six = NA if (sk in ("", NA) and rho in ("", NA)) else f"skew {sk}；Spearman {rho}"
        L.append("| " + " | ".join([
            f"`{_md_cell(d.get('col_name', ''))}`",
            _md_cell(d.get("src_profile", "")),
            _md_cell(d.get("method", "")),
            _md_cell(d.get("rationale", "")),
            _md_cell(d.get("params", "")),
            _md_cell(six),
        ]) + " |")
    L += [
        "",
        "## 門檻（06 §6.1）",
        "",
        f"- 轉換後偏度：`|skew| < {SKEW_MAX}`，抓的是「統計目的有沒有達成」（M4 三門檻之一）。",
        f"- 排序相關：Spearman(原欄, 轉換後欄) `> {SPEARMAN_MIN}`，抓的是「實作有沒有寫錯」。",
        "  單調轉換理論值是 1.000；0.95~0.999 代表 winsorize/clip 造成並列，",
        "  要與 `n_rows_clipped` 對得起來；出現 NaN 是 bug 不是統計問題。",
        f"- `{NA}` 代表不適用（不轉換、改模型的列），不是漏填。",
        "",
        "## 驗收",
        "",
        "```",
        "python scripts/write_transform_log.py <專案代號> --validate",
        "```",
        "",
        "退出碼 0 = 全通過｜1 = 有 error（缺理由、缺欄、Spearman 破線）｜2 = 只有 warning。",
        "",
    ]
    return "\n".join(L)


# ── 驗收 ────────────────────────────────────────────────────
@dataclass
class ValidateResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        n_err = sum(1 for m in self.errors if not m.startswith("    "))
        n_warn = sum(1 for m in self.warnings if not m.startswith("    "))
        if n_err:
            return 1
        return 2 if n_warn else 0

    def ok(self) -> bool:
        return not self.errors


def _check_winsorize(tag: str, params: str, res: ValidateResult) -> None:
    """第五欄若帶 winsorize JSON，檢查 06 §3.3 的必填欄位。"""
    m = re.search(r"winsorize=(\{.*\})\s*$", params, re.DOTALL)
    if not m:
        return
    try:
        w = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        res.errors.append(f"{tag} winsorize 區塊不是合法 JSON（{e}）— "
                          f"用 row_from_arrays(winsorize={{...}}) 產生，不要手打")
        return
    miss = [k for k in WINSOR_REQUIRED if k not in w]
    if miss:
        res.errors.append(
            f"{tag} winsorize 缺必填欄位：{', '.join(miss)} — "
            f"06 §3.3 分支 C 的完整欄位，其中 pct_of_total_amount"
            f"（被壓掉多少營收）與 reason 是這個區塊存在的理由"
        )
    miss2 = [k for k in WINSOR_NICE if k not in w]
    if miss2:
        res.warnings.append(f"{tag} winsorize 缺 {', '.join(miss2)} — "
                            f"06 §3.3 有列，回查時會用到")
    if w.get("conclusion_flip") is True:
        res.warnings.append(f"{tag} winsorize 的 conclusion_flip=true — "
                            f"06 §3.3：正文必須註明結論會翻，不能只留在這份紀錄裡")


def validate_log(project: str, verbose: bool = False) -> ValidateResult:
    """檢查每一列六欄是否齊全。缺「為什麼是它」= 違反 00 §1.4，回 error。

    三桶（error / warning / info），退出碼由 ValidateResult.exit_code 給。
    """
    res = ValidateResult()
    csv_path, md_path, mirror_path = log_paths(project, create=False)

    if not csv_path.exists():
        res.errors.append(
            f"找不到轉換紀錄：{csv_path} — "
            f"M3 只要動過任何一欄就必須留這份（06 §六）。"
            f"跑 write_log(專案, rows) 產生；若這個專案真的一欄都沒轉，"
            f"也要留一列 method='none' 寫明原因，不能沒有檔案"
        )
        return res

    rows = _read_rows(csv_path)
    with csv_path.open("rb") as f:
        head = f.read(3)
    if head != b"\xef\xbb\xbf":
        res.warnings.append(
            f"{csv_path.name} 不是 utf-8-sig — Excel 直接開會中文亂碼。"
            f"重跑 write_log() 即可修正"
        )

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f), [])
    if header != SCHEMA:
        res.errors.append(
            f"欄名或順序不對：{header} — "
            f"06 §六 明訂 SCHEMA 順序不可改，應為 {SCHEMA}。"
            f"下游 verify_outputs 按位置讀，順序一換就對錯欄"
        )
        return res

    if not rows:
        res.warnings.append(
            "紀錄是空的（只有表頭）— 若 M3 真的沒轉任何欄，"
            "請留一列 method='none' 並在 rationale 寫明；空檔案分不出「沒轉」與「忘了寫」"
        )

    seen: dict[str, int] = {}
    for i, d in enumerate(rows, start=1):
        name = (d.get("col_name") or "").strip()
        tag = f"第 {i} 列「{name or '(無欄名)'}」"

        # ── 六欄齊全（第 1、2、3、4 欄不可空）──────────────
        if not name:
            res.errors.append(f"{tag} 沒有欄名 — 六欄缺一不可（06 §六）。"
                              f"補上含轉換後綴的完整欄名（06 §4.2）")
        elif name in seen:
            res.errors.append(
                f"{tag} 欄名與第 {seen[name]} 列重複 — 每個被轉換的欄佔一列。"
                f"同一欄試了兩種轉換就給兩個欄名（`x__log`、`x__yj`），"
                f"不要用同名兩列，下游 join 會一對多"
            )
        else:
            seen[name] = i

        if not (d.get("src_profile") or "").strip():
            res.errors.append(f"{tag} 缺第 2 欄（原分布特性）— "
                              f"沒有原分布就無法判斷這個轉換該不該選（06 §一 先分流再選方法）")
        else:
            miss = [k for k in ("n=", "min=", "max=", "p50=", "skew=", "zero=")
                    if k not in d["src_profile"]]
            if miss:
                res.warnings.append(
                    f"{tag} 第 2 欄缺 {', '.join(m.rstrip('=') for m in miss)} — "
                    f"06 §六 要求 n/min/max/p50/skew/zero_ratio/neg_ratio。"
                    f"用 profile_series() 產生就不會漏"
                )

        if not (d.get("method") or "").strip():
            res.errors.append(f"{tag} 缺第 3 欄（選了哪個轉換）— "
                              f"不轉換也要寫，格式是 'none + <模型族>'（06 §六）")

        # ── 第四欄：這支腳本存在的理由 ─────────────────────
        rationale = (d.get("rationale") or "").strip()
        if not rationale:
            res.errors.append(
                f"{tag} 缺第 4 欄（為什麼是它）— "
                f"違反 00 §1.4「參數必附理由」。半年後沒人記得為什麼選這個轉換，"
                f"換一批資料要不要沿用也沒人敢決定。"
                f"寫法：情境編號 + 第幾順位 + 前面順位為什麼不行（06 §六）"
            )
        else:
            if not _RE_SITUATION.search(rationale):
                res.errors.append(
                    f"{tag} 第 4 欄沒有情境編號 — "
                    f"06 §六 CHECKS_M3 第 1 條要求 rationale 含情境編號與順位。"
                    f"補上「情境 N」（N = 1~7，見 06 §1.2 順位表）"
                )
            if not _RE_RANK.search(rationale):
                res.errors.append(
                    f"{tag} 第 4 欄沒有順位 — "
                    f"同上。補上「第 ① 順位」並說明前面順位為什麼不行；"
                    f"若該情境只有一條路（如情境 3 的 Hurdle）寫「唯一順位」"
                )
            if len(rationale) < 12:
                res.warnings.append(
                    f"{tag} 第 4 欄只有 {len(rationale)} 個字 — "
                    f"「情境 1 第 ① 順位」本身不算理由，要寫前面順位為什麼不行"
                )

        # ── 第五欄：參數值 ─────────────────────────────────
        params = (d.get("params") or "").strip()
        method = (d.get("method") or "").strip()
        if not params:
            res.warnings.append(
                f"{tag} 第 5 欄空白 — 沒有參數請填「{NA}」。"
                f"空白分不出「這個轉換沒有參數」與「忘了寫」"
            )
        elif _METHOD_NEEDS_PARAM.search(method) and not re.search(r"\d", params):
            res.errors.append(
                f"{tag} method='{method}' 有參數但第 5 欄沒有數值 — "
                f"違反 00 §1.4。λ／θ／c／切點／分位都要寫出實際值，"
                f"換一批資料重跑要載入同一份（06 §4.1）"
            )
        if params not in ("", NA) and re.search(r"\d", params) \
                and not re.search(r"fit_on", params, re.IGNORECASE):
            res.warnings.append(
                f"{tag} 第 5 欄沒寫 fit_on — 06 §六 要求「參數值 + fit_on（train/full）」。"
                f"參數從全資料 fit 是 18-G4 目標洩漏的入口（06 §4.1），要標出來"
            )
        _check_winsorize(tag, params, res)

        # ── 第六欄：轉換後偏度與排序相關 ───────────────────
        sk = _as_float(d.get("post_skew", ""))
        rho = _as_float(d.get("spearman_vs_src", ""))
        no_transform = bool(re.search(r"^\s*(none|不轉換)", method, re.IGNORECASE))

        if sk is None and rho is None:
            if not no_transform:
                res.warnings.append(
                    f"{tag} 第 6 欄兩個數字都是「{NA}」但 method 看起來有轉換 — "
                    f"有產生轉換欄就要附偏度與 Spearman（06 §6.1）；"
                    f"真的沒產生欄位請把 method 寫成 'none + <模型族>'"
                )
        else:
            if sk is not None and sk != sk:
                res.errors.append(
                    f"{tag} 轉換後偏度是 NaN — 06 §6.1：這是 bug 不是統計問題。"
                    f"多半是 log 吃到 0 或負值，回去修 06 §一 的情境判定"
                )
            elif sk is not None and abs(sk) >= SKEW_MAX:
                res.warnings.append(
                    f"{tag} 轉換後偏度 {sk:.4f}，|skew| ≥ {SKEW_MAX} — "
                    f"轉換沒達成統計目的，M4 這一關會擋。"
                    f"換下一順位，或依 06 §3.2 分支 C 考慮 winsorize"
                )
            if rho is not None and rho != rho:
                res.errors.append(
                    f"{tag} Spearman 是 NaN — 轉換後欄全為 NaN 或全為同一個值。"
                    f"06 §6.1：Bug，回去修情境判定"
                )
            elif rho is not None and rho < 0:
                res.errors.append(
                    f"{tag} Spearman {rho:.4f} 為負 — 用了非單調轉換"
                    f"（如對含負值的欄取平方，06 §6.1 最後一列）。重新分流"
                )
            elif rho is not None and rho < SPEARMAN_MIN:
                res.errors.append(
                    f"{tag} Spearman {rho:.4f} < {SPEARMAN_MIN} — M4 門檻不過（06 §6.1）。"
                    f"winsorize 砍太多或 clip 範圍設錯，回去改參數"
                )
            elif rho is not None and rho < SPEARMAN_TIE:
                res.warnings.append(
                    f"{tag} Spearman {rho:.4f} 落在 {SPEARMAN_MIN}~{SPEARMAN_TIE} — "
                    f"有並列產生。與第 5 欄的 n_rows_clipped 對得起來就通過（06 §6.1）"
                )
        if no_transform and (sk is not None or rho is not None):
            res.warnings.append(
                f"{tag} method 寫不轉換卻有第 6 欄數字 — "
                f"沒產生轉換欄就沒有「轉換後偏度」，兩者必有一個寫錯"
            )

    # ── 鏡射與 markdown ────────────────────────────────────
    if mirror_path.exists():
        if mirror_path.read_bytes() != csv_path.read_bytes():
            res.warnings.append(
                f"鏡射檔與正本不一致：{mirror_path} — "
                f"06 §六 的路徑是 顧客特徵表/，正本在 執行紀錄/。"
                f"有人手改了其中一份。重跑 write_log() 讓兩份同步"
            )
        else:
            res.infos.append(f"鏡射檔與正本一致：{mirror_path}")
    else:
        res.warnings.append(
            f"沒有鏡射檔 {mirror_path} — 06 §六 寫的路徑是 顧客特徵表/，"
            f"照那條路徑找的下游會找不到。write_log(..., mirror=True) 會補上"
        )

    if not md_path.exists():
        res.warnings.append(f"沒有 {md_path.name} — 人眼看的版本缺席，"
                            f"重跑 write_log() 會一併產生")

    n_ok = len(rows) - len({m.split("「")[1].split("」")[0]
                            for m in res.errors if "「" in m})
    res.infos.append(f"共 {len(rows)} 列，{max(n_ok, 0)} 列六欄齊全")
    if verbose:
        for d in rows:
            res.infos.append(f"  · {d.get('col_name', '')} ← {d.get('method', '')}")
    return res


# ── 自我測試：用素材庫樣本實跑一次 ──────────────────────────
def self_test(project: str) -> int:
    """拿課程信用卡樣本（100 位客戶 / 7,764 筆）真的做一次轉換並落檔。

    這不是示範資料，是實跑：M、R 由樣本現算，第 2、6 欄的數字全部是算出來的。
    斷言用 17 §五 已驗證的基準值（客戶 89：R=19、M=150,681）。
    """
    import numpy as np
    import pandas as pd

    from paths import archive_root
    ar = archive_root()
    if ar is None:
        print("⛔ 找不到素材庫 00_source_archive — self-test 需要樣本檔。"
              "改用 --from-json 或在 config.yml 指定「素材庫」")
        return 1
    src = ar / "local" / "資料集剖析" / "samples" / "ntu_creditcard__transactions.parquet"
    if not src.exists():
        print(f"⛔ 找不到樣本：{src} — self-test 需要它。改用 --from-json")
        return 1

    df = pd.read_parquet(src)
    g = df.groupby("客戶ID")
    m = g["刷卡金額"].sum().sort_index()
    r = (pd.Timestamp("2012-12-01") - g["刷卡日期"].max()).dt.days.sort_index()
    assert len(m) == 100, f"客戶數應為 100，實得 {len(m)}"
    assert int(m.loc[89]) == 150_681, f"客戶 89 的 M 應為 150,681，實得 {int(m.loc[89])}"
    assert int(r.loc[89]) == 19, f"客戶 89 的 R 應為 19，實得 {int(r.loc[89])}"
    print(f"✅ 樣本斷言通過：{len(df):,} 筆交易 / {len(m)} 位客戶，"
          f"客戶 89 R={int(r.loc[89])}、M={int(m.loc[89]):,}")

    mv = m.to_numpy(dtype="float64")
    rv = r.to_numpy(dtype="float64")

    # ① 情境 1 第 ① 順位：不轉換，改 Gamma GLM
    rows = [row_from_arrays(
        col_name="m_net_twd",
        method="none + Gamma GLM(log link)",
        rationale=("情境 1 第 ① 順位（min>0、skew>1）。交付物含「預測年度營收」，"
                   "走 log-OLS 再 exp 會系統性低估 e^(σ²/2) 倍（06 §二），"
                   "② log(x) 只做描述、③ Box-Cox 的 λ 一樣有反轉換問題"),
        src=mv, dst=None,
        params=f"family=Gamma, link=log; as_of=2012-12-01; fit_on=train",
    )]

    # ② 情境 1 第 ② 順位：log，只做描述與分群輸入
    rows.append(row_from_arrays(
        col_name="m_net_twd__log",
        method="ln(x)",
        rationale=("情境 1 第 ② 順位。僅供 EDA 直方圖與分群輸入；"
                   "① Gamma GLM 是建模路線不產生欄位，不能拿來當分群矩陣的欄"),
        src=mv, dst=np.log(mv),
        params=f"{NA}（無參數）; fit_on=full（purpose=descriptive_only，06 §4.1 允許）",
    ))

    # ③ 時間型欄位：NTILE(5) 而不是 log（06 §4.5）
    q5 = pd.qcut(r.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    cuts = np.quantile(rv, [0.2, 0.4, 0.6, 0.8])
    rows.append(row_from_arrays(
        col_name="r_days_since_last_sale__q5",
        method="NTILE(5) 分位分箱",
        rationale=("時間型欄位，情境 1 的 log 不適用：log 會讓 30vs60 與 300vs600 "
                   "變成同樣差距（06 §4.5）。等寬分箱會把多數客戶塞進第一箱，"
                   "所以分位分箱是唯一順位"),
        src=rv, dst=q5.to_numpy(dtype="float64"),
        params=(f"切點 {'/'.join(f'{c:.1f}' for c in cuts)}; "
                f"as_of=2012-12-01; fit_on=train"),
    ))

    # ④ 分支 C：winsorize，帶 06 §3.3 的完整欄位
    lo, hi = float(np.quantile(mv, 0.01)), float(np.quantile(mv, 0.99))
    mw = np.clip(mv, lo, hi)
    n_clip = int((mv != mw).sum())
    rows.append(row_from_arrays(
        col_name="m_net_twd__w0199",
        method="winsorize(1%, 99%)",
        rationale=("情境 1 第 ② 順位的 log 之後仍有極端值影響分群質心，"
                   "依 06 §3.2 分支 C 在轉換後再 winsorize；"
                   "分支 A 的 trimming 不允許（會改樣本數）"),
        src=mv, dst=mw,
        params=f"lower_q=0.01, upper_q=0.99; fit_on=train",
        winsorize={
            "applied": True, "branch": "C",
            "reason": "log 後前 1% 仍主導 K-means 質心",
            "tried_before": ["log"],
            "lower_q": 0.01, "upper_q": 0.99,
            "lower_value": round(lo, 1), "upper_value": round(hi, 1),
            "n_rows_clipped": n_clip,
            "pct_of_rows": round(n_clip / len(mv), 4),
            "pct_of_total_amount": round(float((mv - mw).sum() / mv.sum()), 4),
            "affected_cust_ids": [str(c) for c in m.index[mv != mw].tolist()],
            "conclusion_flip": False,
        },
    ))

    written = write_log(project, rows, merge=False)
    print(f"\n已寫入 {len(rows)} 列：")
    for k, v in written.items():
        print(f"  · {k:<7} {v}")
    return 0


# ── CLI ─────────────────────────────────────────────────────
def _print_result(project: str, res: ValidateResult, verbose: bool) -> None:
    csv_path, _, _ = log_paths(project, create=False)
    print("=" * 64)
    print(f"轉換紀錄驗收 — {project}")
    print(f"檔案：{csv_path}")
    print("=" * 64)

    if verbose and res.infos:
        print("\n通過")
        print("-" * 64)
        for m in res.infos:
            print(f"  {m}" if m.startswith("  ") else f"  ✅ {m}")

    if res.warnings:
        print("\n⚠ 可以往下走，但這些要知道")
        print("-" * 64)
        for m in res.warnings:
            print(f"  ⚠ {m}")

    if res.errors:
        print("\n⛔ 不通過，必須先補")
        print("-" * 64)
        for m in res.errors:
            print(f"  ⛔ {m}")

    print("\n" + "=" * 64)
    n_err, n_warn = len(res.errors), len(res.warnings)
    if n_err:
        print(f"結果：{n_err} 個 error、{n_warn} 個 warning → 轉換紀錄不合格")
    elif n_warn:
        print(f"結果：{n_warn} 個 warning → 合格，但有事項待補")
    else:
        print(f"結果：全部通過（{len(res.infos)} 項）→ 轉換紀錄合格")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="M3 轉換紀錄（06 §六 六欄格式）的落檔與驗收",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出碼：0 全通過｜1 有 error｜2 只有 warning",
    )
    ap.add_argument("project", help="專案代號")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-json", metavar="檔案",
                   help="讀一份 JSON（六欄的 list）寫進紀錄")
    g.add_argument("--validate", action="store_true", help="只驗收，不寫檔")
    g.add_argument("--self-test", action="store_true",
                   help="用素材庫樣本實跑一次轉換並落檔（會覆寫該專案的紀錄）")
    ap.add_argument("--replace", action="store_true",
                    help="--from-json 時整份重寫，而不是照 col_name 合併")
    ap.add_argument("--no-mirror", action="store_true",
                    help="不要鏡射到 顧客特徵表/（預設會鏡射，06 §六 的路徑）")
    ap.add_argument("--verbose", action="store_true", help="連通過項也列出")
    args = ap.parse_args(argv)

    if args.self_test:
        rc = self_test(args.project)
        if rc:
            return rc
        print()
        res = validate_log(args.project, verbose=args.verbose)
        _print_result(args.project, res, args.verbose)
        return res.exit_code

    if args.from_json:
        src = Path(args.from_json)
        if not src.exists():
            print(f"⛔ 找不到 {src} — 確認路徑，或用 row_from_arrays() 在程式裡建列")
            return 1
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"⛔ {src} 不是合法 JSON（{e}）— 用 UTF-8 存檔，"
                  f"外層是 list，每個元素是六欄的 dict")
            return 1
        if isinstance(data, dict):
            data = [data]
        try:
            rows = [row_from_dict(d) for d in data]
        except (ValueError, KeyError, TypeError) as e:
            print(f"⛔ {e}")
            return 1
        written = write_log(args.project, rows,
                            merge=not args.replace, mirror=not args.no_mirror)
        print(f"已寫入 {len(rows)} 列：")
        for k, v in written.items():
            print(f"  · {k:<7} {v}")
        print()

    res = validate_log(args.project, verbose=args.verbose)
    _print_result(args.project, res, args.verbose)
    return res.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
