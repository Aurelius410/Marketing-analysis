#!/usr/bin/env python3
"""
M1 資料品質三桶 —— M1 → M2 的**唯一放行機制**（04 §一 步驟⑤、18-G11）。

為什麼需要它：
  M1 錯了，下游全部白做，而且**不會報錯**。課程資料集的實測：`Step 2` 的 `int` 欄
  含 100 個 `9999` 哨兵，不排除直接算平均購買間隔得 199.46 天，真值 10.79 天，
  差 18.5 倍 → 流失門檻訂成 200 天 → 100 位客戶只標出 3 人流失（真實 28 人），
  漏掉的 25 人合計 NT$947,152，占總營收 6.4%。這種錯誤 pipeline 一路綠燈跑到底。
  所以品質檢查不能是「提醒」，必須是**帶退出碼的閘門**：error 桶非空就擋住，
  只能靠在 `原始資料/contracts/<source>.yml` 明確宣告處理方式解除（02 §十）。

三桶與退出碼（04 §四，全 skill 統一，**不准把 1 和 2 對調**）：
    0 = 三桶皆空或只有 info      → 可進 M2
    1 = 有 error                 → 擋住，不准進 M2
    2 = 有 warning 無 error      → 可進 M2，但 warning 必須寫進報告的「資料限制」節
    3 = 檢查腳本本身失敗          → 修腳本，不准手動略過

用法：
    # 檢查專案倉儲裡既有的表
    python check_data_quality.py 2026Q3_電商 --table fact_transaction --table dim_customer

    # 檢查還沒進倉的原始檔（parquet / csv），別名=路徑
    python check_data_quality.py 示範 --file 交易=D:/x/transactions.parquet

    # 帶契約（哨兵宣告、grain、欄位型別與用途都從這裡讀）
    python check_data_quality.py 示範 --file 交易=x.parquet --contract 原始資料/contracts/ntu.yml

    # 接 profile_dataset.py 的逐欄剖析結果（欄位總表.csv 的 suspected_sentinel 欄）
    python check_data_quality.py 示範 --file 交易=x.parquet --profile 開案與問題定義/欄位總表.csv

    # 單獨開關某幾條檢查
    python check_data_quality.py 示範 --file 交易=x.parquet --only Q1,Q2,Q6
    python check_data_quality.py 示範 --file 交易=x.parquet --skip Q11,Q12
    python check_data_quality.py --list          # 列出全部檢查條目與所屬桶

規格出處：`references/04_資料體檢.md` §二（缺失率門檻）、§三（grain 與孤兒率）、
          §四（三桶與 Q1–Q16）、§七（覆蓋率）；`references/18_分析陷阱清單.md` G11；
          `references/02_資料模型規格.md` §十（契約檔與 quality_overrides）。

**此處為實作判斷**（reference 未規定，改動前請先讀這段）：
  1. Q17 負值金額、Q18 日期跨界、Q19 孤兒外鍵、Q20 缺失率門檻 這四條在 04 §四
     沒有 Q 編號 —— Q19/Q20 的規則與門檻寫在 04 §三／§二 的正文，只是沒編號；
     Q17/Q18 是本 skill 新增（理由見各條 rule 的 why 欄）。02 §十 說
     `quality_overrides[].rule` 的值域是 Q1–Q16，**這四條要一併補進 04 §四與 02 §十**，
     否則契約寫 `rule: Q17` 會與 02 的值域說明不一致。
  2. 04 §二 的缺失率階梯是「≥5% warning／≥40% error／≥80% 建議棄用」，本腳本照做。
     若你要的是「>20% 才 warning」，用 `--null-warn-rate 0.20`，但預設以 reference 為準。
  3. 沒有契約時，欄位角色（分母／金額／時間軸／外鍵）改用欄名樣式推定，判定力會下降；
     每次執行都會在 info 桶提醒。**契約是正解，樣式推定只是過渡**。
  4. 連線用 `db.connect(read_only=False)` 而非唯讀 —— 本腳本要掛 TEMP VIEW 讀外部檔，
     並把三桶結果寫成統計表（03 §1.2：`統計表/資料體檢/` 是三桶結果的落點）。
     它只 SELECT，不改任何既有表。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect  # noqa: E402
from paths import project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── 常數 ─────────────────────────────────────────────────
# 04 §4.1 Q2 的哨兵候選集
SENTINEL_NUMBERS = [-1, -9, -99, -999, 0, 9999, 99999, 999999]
SENTINEL_DATES = ["1900-01-01", "1970-01-01", "2099-12-31", "9999-12-31"]

# 04 §4.1 Q3：Excel 樞紐的合計列
GRAND_TOTAL_TOKENS = {
    "grand total", "總計", "合計", "總和", "total", "(blank)", "(空白)", "空白",
}

# 欄名樣式推定（沒有契約時的退路，見 docstring 實作判斷 3）
PAT_AMOUNT = re.compile(r"金額|amount|amt|price|spend|revenue|sales|營收|消費|支出", re.I)
PAT_DENOM = re.compile(r"額度|限額|quota|limit|曝光|impression|分母|denominator|基數|配額", re.I)
PAT_EVENT_DATE = re.compile(r"交易|刷卡|訂單|事件|發生|日期|event|txn|order|purchase|visit|date", re.I)
PAT_CREATE_DATE = re.compile(r"開卡|開戶|建立|申請|辦|加入|註冊|create|open|join|signup|start", re.I)
PAT_EXPIRE_DATE = re.compile(r"到期|失效|結束|終止|expire|end|close|cancel", re.I)
PAT_CURRENCY = re.compile(r"^(currency|curr|ccy|幣別|幣種)$", re.I)
PAT_UA = re.compile(r"user_?agent|^ua$|browser", re.I)
PAT_MEMBER = re.compile(r"member|會員|客戶|customer|user", re.I)
PAT_UNNAMED = re.compile(r"^Unnamed: \d+$")
PAT_CODE_PREFIX = re.compile(r"^(\d+)[_\-.]")

# 全形英數與符號 U+FF01–FF5E、全形空白 U+3000（04 §4.2 Q10）
SQL_FULLWIDTH = r"[\x{FF01}-\x{FF5E}\x{3000}]"

BOT_UA = r"(?i)(bot|crawl|spider|monitor|headless|lighthouse)"

NUM_TYPE_HEADS = {
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "UTINYINT", "USMALLINT",
    "UINTEGER", "UBIGINT", "DECIMAL", "DOUBLE", "FLOAT", "REAL", "NUMERIC",
}


# ── 資料結構 ──────────────────────────────────────────────
@dataclass(frozen=True)
class Col:
    """一個欄位的最小描述。"""
    table: str
    name: str
    dtype: str

    @property
    def head(self) -> str:
        return self.dtype.split("(")[0].upper()

    @property
    def is_num(self) -> bool:
        return self.head in NUM_TYPE_HEADS

    @property
    def is_date(self) -> bool:
        return self.head in {"DATE", "TIMESTAMP", "TIMESTAMP_NS", "TIMESTAMP_S",
                             "TIMESTAMP_MS", "DATETIME"}

    @property
    def is_text(self) -> bool:
        return self.head in {"VARCHAR", "CHAR", "TEXT", "STRING"}


@dataclass
class Finding:
    """一條檢查結果。三桶清單與統計表都由它產生。"""
    rule: str
    name: str
    bucket: str                       # error / warning / info
    target: str                       # 表.欄 或 表
    n: int                            # 幾筆
    total: int                        # 母數（該表列數），0 代表不適用
    detail: str                       # 事實
    action: str                       # 該怎麼辦
    downstream: str                   # 影響哪些下游分析
    samples: list[str] = field(default_factory=list)
    note: str = ""                    # 契約 override 之類的補述
    count_label: str = "筆"           # 計數單位，不是每條檢查都以「筆」為單位

    @property
    def pct(self) -> float:
        return (self.n / self.total) if self.total else 0.0

    def headline(self) -> str:
        cnt = f"{self.n:,} {self.count_label}"
        if self.total:
            cnt += f"（{self.pct:.2%}）"
        return f"{self.rule} {self.name}｜{self.target}｜{cnt}"

    def conclusion(self) -> str:
        """統計表最後一欄的中文結論（18-E15：每張統計表強制帶中文結論）。"""
        tag = {"error": "必須處理才能進 M2", "warning": "可往下但要寫進資料限制節",
               "info": "僅記錄"}[self.bucket]
        return f"{self.detail} → {self.action}（{tag}）"


@dataclass
class Contract:
    """`原始資料/contracts/<source>.yml`，02 §十。缺席時所有欄位為空。"""
    path: Path | None = None
    source: str = ""
    grain: dict[str, list[str]] = field(default_factory=dict)
    columns: dict[str, dict[str, Any]] = field(default_factory=dict)
    sentinels: list[dict[str, Any]] = field(default_factory=list)
    overrides: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    @property
    def loaded(self) -> bool:
        return self.path is not None

    def use_of(self, col: str) -> str:
        return str(self.columns.get(col, {}).get("practical_use", "") or "")

    def unit_of(self, col: str) -> str:
        return str(self.columns.get(col, {}).get("unit", "") or "")

    def dtype_of(self, col: str) -> str:
        return str(self.columns.get(col, {}).get("dtype", "") or "")

    def sentinel_declared(self, col: str, value: Any) -> dict[str, Any] | None:
        for s in self.sentinels:
            if str(s.get("column")) == col and str(s.get("value")) == str(value):
                return s
        return None


@dataclass
class Ctx:
    """一次檢查跑批的全部上下文。"""
    con: Any
    tables: dict[str, list[Col]]
    rows: dict[str, int]
    contract: Contract
    profile: dict[tuple[str, str], dict[str, str]]
    edges: list[tuple[str, str, str, str]]        # 子表, 子欄, 父表, 父欄
    as_of: date | None
    args: argparse.Namespace

    def cols(self, table: str) -> list[Col]:
        return self.tables[table]

    def col(self, table: str, name: str) -> Col | None:
        for c in self.tables.get(table, []):
            if c.name == name:
                return c
        return None


# ── DuckDB 小工具 ────────────────────────────────────────
def qi(name: str) -> str:
    """識別字引號化。中文欄名、含空白的欄名（`Unnamed: 10`）都必須走這裡。"""
    return '"' + str(name).replace('"', '""') + '"'


def qs(value: Any) -> str:
    """字串常值引號化。"""
    return "'" + str(value).replace("'", "''") + "'"


def fetch(ctx: Ctx, sql: str) -> list[tuple]:
    return ctx.con.execute(sql).fetchall()


def one(ctx: Ctx, sql: str, default: Any = None) -> Any:
    r = ctx.con.execute(sql).fetchone()
    return default if r is None else r[0]


def sample_values(ctx: Ctx, table: str, expr: str, where: str, limit: int = 5) -> list[str]:
    """取前 N 筆實例值。三桶輸出一律附實例，不然使用者不知道要去改什麼。"""
    sql = (f"SELECT DISTINCT CAST({expr} AS VARCHAR) FROM {qi(table)} "
           f"WHERE {where} LIMIT {limit}")
    return [str(r[0]) for r in fetch(ctx, sql)]


# ── 規則登錄 ─────────────────────────────────────────────
@dataclass(frozen=True)
class Rule:
    code: str
    name: str
    bucket: str          # 預設桶
    downstream: str      # 影響哪些下游分析
    source: str          # 規格出處
    fn: Callable[[Ctx], list[Finding]]


RULES: dict[str, Rule] = {}


def rule(code: str, name: str, bucket: str, downstream: str, source: str):
    def deco(fn: Callable[[Ctx], list[Finding]]):
        RULES[code] = Rule(code, name, bucket, downstream, source, fn)
        return fn
    return deco


def mk(r_code: str, target: str, n: int, total: int, detail: str, action: str,
       samples: Iterable[str] = (), bucket: str | None = None,
       count_label: str = "筆") -> Finding:
    r = RULES[r_code]
    return Finding(rule=r.code, name=r.name, bucket=bucket or r.bucket, target=target,
                   n=n, total=total, detail=detail, action=action,
                   downstream=r.downstream, samples=list(samples),
                   count_label=count_label)


def width(s: str) -> int:
    """字串在等寬主控台的顯示寬度（中日韓全形算 2）。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def pad(s: str, n: int) -> str:
    return s + " " * max(1, n - width(s))


# ══════════════════════════════════════════════════════════
# error 桶
# ══════════════════════════════════════════════════════════
@rule("Q1", "型別 cast 靜默失敗", "error",
      "M2 均數與檢定、M3 轉換、M8 的 M 與客單價、M13 排名建議",
      "04 §4.1 Q1")
def q1_cast(ctx: Ctx) -> list[Finding]:
    """cast 後 NULL 數 ≠ cast 前空字串/NULL 數 → error，並印出前 5 筆無法轉換的原始值。

    有契約時照契約宣告的 dtype 轉，只要有一筆轉不過去就是 error。
    沒有契約時退化成推定：某 VARCHAR 欄有 ≥80%（`--cast-hint-rate`）的值轉得過去
    卻不是 100%，代表它本來就該是數值/日期欄，剩下的那幾筆是千分位、幣別符號、
    全形數字之類的髒值 —— 那 3% 靜默變 NULL，該店營收就少 18%（04 Q1 的 gap D17 案例）。
    """
    out: list[Finding] = []
    hint = ctx.args.cast_hint_rate
    for t, cols in ctx.tables.items():
        total = ctx.rows[t]
        for c in cols:
            if not c.is_text:
                continue
            nonnull = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                               f"WHERE {qi(c.name)} IS NOT NULL AND trim({qi(c.name)}) <> ''", 0)
            if not nonnull:
                continue
            declared = ctx.contract.dtype_of(c.name).upper()
            targets: list[str]
            if declared and not declared.startswith("VARCHAR"):
                targets = [declared]
                strict = True
            else:
                targets = ["DOUBLE", "DATE"]
                strict = False

            for tgt in targets:
                n_fail = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NOT NULL "
                                  f"AND trim({qi(c.name)}) <> '' "
                                  f"AND TRY_CAST({qi(c.name)} AS {tgt}) IS NULL", 0)
                if n_fail == 0:
                    continue
                ok_rate = 1 - n_fail / nonnull
                if not strict and ok_rate < hint:
                    continue          # 本來就是文字欄，不是 cast 失敗
                pre_null = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NULL "
                                    f"OR trim({qi(c.name)}) = ''", 0)
                bad = sample_values(
                    ctx, t, qi(c.name),
                    f"{qi(c.name)} IS NOT NULL AND trim({qi(c.name)}) <> '' "
                    f"AND TRY_CAST({qi(c.name)} AS {tgt}) IS NULL")
                src = "契約宣告" if strict else f"推定（{ok_rate:.1%} 的值轉得過去）"
                out.append(mk(
                    "Q1", f"{t}.{c.name}", n_fail, nonnull,
                    f"cast 成 {tgt}（{src}）後 NULL 數 = {pre_null + n_fail:,}，"
                    f"cast 前只有 {pre_null:,} —— 有 {n_fail:,} 筆靜默變 NULL",
                    f"先清洗原始值再轉型（去千分位/幣別符號/全形數字），"
                    f"或在契約把 {c.name} 的 dtype 改成 VARCHAR 並說明為什麼不轉",
                    bad))
                break                 # 一欄只報一次，避免 DOUBLE/DATE 重複報
    return out


@rule("Q2", "哨兵值 / 魔術數", "error",
      "M8 的 MLE/WMLE/CAI、流失門檻、M6 分群（RFM 分數）、任何平均數",
      "04 §4.1 Q2")
def q2_sentinel(ctx: Ctx) -> list[Finding]:
    """哨兵放 error 不放 warning —— warning 會被忽略，而它會讓平均間隔差 18.5 倍。

    兩個來源合流：
      ① `profile_dataset.py` 的 `欄位總表.csv`，`suspected_sentinel` 欄非空即 SUSPECTED_SENTINEL；
      ② 本腳本自掃：候選值出現次數「恰等於或極接近某個鍵欄的相異值數」（04 Q2 觸發條件）。
    契約 `sentinels:` 已宣告 column+value+action 的降為 info，這是解除 error 的唯一途徑。
    """
    out: list[Finding] = []
    near = ctx.args.sentinel_near

    for t, cols in ctx.tables.items():
        total = ctx.rows[t]
        if not total:
            continue
        # 鍵欄相異值數：契約標 subject_key/fk 的優先，否則取所有整數/字串欄
        key_cards: list[tuple[str, int]] = []
        for c in cols:
            use = ctx.contract.use_of(c.name)
            if use in ("subject_key", "fk") or (
                    not ctx.contract.loaded and (c.is_num or c.is_text)):
                nq = one(ctx, f"SELECT count(DISTINCT {qi(c.name)}) FROM {qi(t)}", 0)
                # 相異值 <10 的欄不當比對基準：兩三個值的欄（性別、卡等）本來就會
                # 和任何小計數「極接近」，那是巧合不是哨兵
                if nq and nq >= 10:
                    key_cards.append((c.name, nq))

        for c in cols:
            prof = ctx.profile.get((t, c.name)) or ctx.profile.get(("", c.name)) or {}
            flagged = prof.get("suspected_sentinel", "")
            if flagged.lower() in ("false", "0", "nan", "none"):
                flagged = ""
            candidates: list[Any] = []
            if c.is_num:
                candidates = list(SENTINEL_NUMBERS)
            elif c.is_date:
                candidates = list(SENTINEL_DATES)
            elif c.is_text:
                candidates = [str(v) for v in SENTINEL_NUMBERS]
            for v in candidates:
                if c.is_date:
                    # TIMESTAMP_NS 的值域到 2262 年，直接比 9999-12-31 會拋型別錯，
                    # 所以兩邊都先降到 DATE 再比
                    lhs, rhs = f"CAST({qi(c.name)} AS DATE)", f"DATE {qs(v)}"
                else:
                    lhs, rhs = qi(c.name), (qs(v) if c.is_text else str(v))
                n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {lhs} = {rhs}", 0)
                if not n:
                    continue
                hit_key = next(
                    (k for k, nq in key_cards
                     if k != c.name and abs(n - nq) <= near * nq), None)
                from_profile = bool(flagged) and str(flagged) in ("", str(v), "true", "True", "1")
                if not hit_key and not from_profile:
                    continue
                why = (f"profile_dataset 已標記 suspected_sentinel"
                       if from_profile and not hit_key else
                       f"出現 {n:,} 次，與鍵欄 {hit_key} 的相異值數 "
                       f"{dict(key_cards).get(hit_key, 0):,} 相符或極接近")
                dec = ctx.contract.sentinel_declared(c.name, v)
                if dec:
                    f = mk("Q2", f"{t}.{c.name}", n, total,
                           f"值 {v} {why}",
                           f"契約已宣告 action={dec.get('action')}：{dec.get('reason', '')}",
                           bucket="info")
                    f.note = "契約 sentinels 已宣告，不擋"
                else:
                    f = mk("Q2", f"{t}.{c.name}", n, total,
                           f"值 {v} 是 SUSPECTED_SENTINEL：{why}",
                           f"在契約的 sentinels: 宣告 "
                           f"{{column: {c.name}, value: {v}, action: to_null|keep|exclude, reason: …}} 後重跑")
                out.append(f)
    return out


@rule("Q3", "Excel 樞紐 Grand Total 列", "error",
      "M8 的 CAI 排行、M6 群中心、所有全體平均與加總",
      "04 §4.1 Q3")
def q3_grand_total(ctx: Ctx) -> list[Finding]:
    """首欄值命中 Grand Total / 總計 / (blank) → 那一列會變成一位「顧客」衝上榜首。"""
    out: list[Finding] = []
    toks = ",".join(qs(x) for x in GRAND_TOTAL_TOKENS)
    for t, cols in ctx.tables.items():
        if not cols:
            continue
        first = cols[0]
        expr = f"lower(trim(CAST({qi(first.name)} AS VARCHAR)))"
        n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {expr} IN ({toks})", 0)
        if n:
            bad = sample_values(ctx, t, qi(first.name), f"{expr} IN ({toks})")
            out.append(mk("Q3", f"{t}.{first.name}", n, ctx.rows[t],
                          f"首欄命中樞紐合計列標記（{'、'.join(bad)}）",
                          "在載入層就 WHERE 掉這幾列，不要讓它進 staging；"
                          "或改從原始明細重算，不要吃 Excel 樞紐的輸出",
                          bad))
    return out


@rule("Q4", "字串黏接鍵碰撞", "error",
      "M8 的間隔型指標（客戶×日 去重）、M6 分群、任何以複合鍵 join 的表",
      "04 §4.1 Q4")
def q4_concat_key(ctx: Ctx) -> list[Finding]:
    """複合 grain 若用無分隔符黏接成單一字串，`89&40526`／`894&0526` 會撞成同一鍵。

    做法：比對「黏接後的相異值數」與「真正的複合鍵相異值數」。少掉的就是碰撞組。
    課程檔 5,294 組實測無碰撞 —— 那是運氣不是設計，所以這條照樣要跑。
    """
    out: list[Finding] = []
    for t, gcols in grains(ctx).items():
        if t not in ctx.tables or len(gcols) < 2:
            continue
        cast = [f"CAST({qi(c)} AS VARCHAR)" for c in gcols]
        n_concat = one(ctx, f"SELECT count(DISTINCT {' || '.join(cast)}) FROM {qi(t)}", 0)
        cols_sql = ", ".join(qi(c) for c in gcols)
        n_tuple = one(ctx, f"SELECT count(*) FROM (SELECT DISTINCT {cols_sql} FROM {qi(t)})", 0)
        if n_concat < n_tuple:
            out.append(mk("Q4", f"{t}({'+'.join(gcols)})", n_tuple - n_concat, n_tuple,
                          f"無分隔符黏接後相異值 {n_concat:,} < 真實複合鍵相異值 {n_tuple:,}",
                          f"改用 {' || chr(124) || '.join(gcols)} 這種帶分隔符的寫法，"
                          f"或直接 GROUP BY 兩欄，不要黏成字串"))
    return out


@rule("Q5", "除零", "error",
      "所有比率型指標（額度使用率、轉換率、ROAS）—— 一個 inf 會讓整欄 mean() 報廢",
      "04 §4.1 Q5")
def q5_div_zero(ctx: Ctx) -> list[Finding]:
    """比率型指標的分母欄存在 = 0 或 IS NULL 的列。

    **此處為實作判斷**：契約沒有「哪個欄是哪個比率的分母」這個鍵，所以分母欄用
    `--denominator 表.欄` 指定，沒指定時用欄名樣式推定（額度/限額/quota/曝光/分母…）。
    實測案例：信用卡 19817 的 `信用額度 = 0`（1998 年到期的停用卡殘留）。
    """
    out: list[Finding] = []
    explicit = {tuple(x.split(".", 1)) for x in ctx.args.denominator if "." in x}
    for t, cols in ctx.tables.items():
        for c in cols:
            if not c.is_num:
                continue
            is_denom = ((t, c.name) in explicit
                        or ctx.contract.unit_of(c.name) in ("ratio", "percent")
                        or bool(PAT_DENOM.search(c.name)))
            if not is_denom:
                continue
            n = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                         f"WHERE {qi(c.name)} = 0 OR {qi(c.name)} IS NULL", 0)
            if n:
                key = cols[0].name
                bad = sample_values(ctx, t, qi(key),
                                    f"{qi(c.name)} = 0 OR {qi(c.name)} IS NULL")
                out.append(mk("Q5", f"{t}.{c.name}", n, ctx.rows[t],
                              f"分母欄有 {n:,} 列為 0 或 NULL（{key} = {'、'.join(bad)}）",
                              "算比率前先判定這幾列的語意（停用？未開通？未曝光？）並排除，"
                              "或改用 NULLIF(分母, 0) 讓結果是 NULL 而不是 inf"))
    return out


@rule("Q6", "grain 不唯一", "error",
      "所有彙總（sum/count 重複計算）→ M8 的 F/M、M11 的 ROAS、任何 join 後的分母",
      "04 §4.1 Q6、§三")
def q6_grain(ctx: Ctx) -> list[Finding]:
    """grain 是「一列代表什麼」。它必須是持續斷言，不是 M1 的一次性觀察。

    沒有宣告 grain 的表一律出 warning —— 沒有東西守著粒度，下一批資料進來時它會靜默失效
    （上游改分頁邏輯、廣告 API 重複回傳、POS 重跑）。
    """
    out: list[Finding] = []
    g = grains(ctx)
    for t in ctx.tables:
        gcols = g.get(t)
        if not gcols:
            out.append(mk("Q6", t, 0, 0,
                          "未宣告 grain，無法驗證主鍵唯一性",
                          f"在契約寫 grain: {{{t}: [欄名…]}}，或用 --grain {t}=欄1,欄2",
                          bucket="warning"))
            continue
        missing = [c for c in gcols if ctx.col(t, c) is None]
        if missing:
            out.append(mk("Q6", t, 0, 0,
                          f"契約宣告的 grain 欄在實檔找不到：{'、'.join(missing)}",
                          "契約與實檔不符，先跑 check_schema_contract.py 對齊",
                          bucket="error"))
            continue
        cols_sql = ", ".join(qi(c) for c in gcols)
        dup = fetch(ctx, f"SELECT {cols_sql}, count(*) AS n FROM {qi(t)} "
                         f"GROUP BY {cols_sql} HAVING count(*) > 1 ORDER BY n DESC LIMIT 5")
        n_groups = one(ctx, f"SELECT count(*) FROM (SELECT {cols_sql} FROM {qi(t)} "
                            f"GROUP BY {cols_sql} HAVING count(*) > 1)", 0)
        if n_groups:
            n_rows = one(ctx, f"SELECT coalesce(sum(n), 0) FROM (SELECT count(*) AS n FROM {qi(t)} "
                              f"GROUP BY {cols_sql} HAVING count(*) > 1)", 0)
            bad = ["+".join(str(x) for x in r[:-1]) + f" ×{r[-1]}" for r in dup]
            out.append(mk("Q6", f"{t}({'+'.join(gcols)})", n_rows, ctx.rows[t],
                          f"{n_groups:,} 組主鍵重複，涉及 {n_rows:,} 列",
                          "先判定是真重複（所有欄位皆同 → 去重並記入清理日誌）"
                          "還是粒度比你以為的更細（→ grain 要再往下一層）。"
                          "04 §三：只有『所有欄位皆同』才算真重複",
                          bad))
    return out


@rule("Q7", "NULL 率漂移", "error",
      "所有以該欄為輸入的指標；典型是 ROAS 從 1.6 被算成 3.2",
      "04 §4.1 Q7")
def q7_null_drift(ctx: Ctx) -> list[Finding]:
    """本次載入 vs 前次載入的 NULL 率差 >20 個百分點。

    抓的是「上游欄位改名 + union_by_name 靜默拆成兩欄各半 NULL」。
    基準值存在 `執行紀錄/null_rate_baseline.json`，第一次跑沒有基準 → info 並建立。
    """
    out: list[Finding] = []
    base_path = ctx.args._baseline_path
    prev: dict[str, float] = {}
    if base_path and base_path.exists():
        try:
            # utf-8-sig：Windows 上被記事本或 PowerShell Set-Content 存過的檔會帶 BOM，
            # 用 utf-8 讀會直接炸掉，而這種手改基準檔的情況很常見
            prev = json.loads(base_path.read_text(encoding="utf-8-sig")).get("null_rate", {})
        except Exception as e:  # noqa: BLE001
            out.append(mk("Q7", str(base_path.name), 0, 0,
                          f"NULL 率基準檔讀取失敗：{e}",
                          "刪掉基準檔重建，或修好它 —— 沒有基準就抓不到欄位改名",
                          bucket="warning"))
    cur: dict[str, float] = {}
    for t, cols in ctx.tables.items():
        total = ctx.rows[t] or 1
        for c in cols:
            nn = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NULL", 0)
            rate = nn / total
            cur[f"{t}.{c.name}"] = rate
            if f"{t}.{c.name}" in prev:
                d = rate - prev[f"{t}.{c.name}"]
                if abs(d) > ctx.args.null_drift:
                    out.append(mk("Q7", f"{t}.{c.name}", nn, ctx.rows[t],
                                  f"NULL 率 {prev[f'{t}.{c.name}']:.1%} → {rate:.1%}"
                                  f"（差 {d * 100:+.1f} 個百分點）",
                                  "查上游是不是改了欄名（union_by_name 會靜默拆成兩欄各半 NULL）；"
                                  "改名要寫進契約的 renames:（append-only）"))
    if not prev:
        out.append(mk("Q7", "（全部欄位）", len(cur), 0,
                      "沒有前次載入的 NULL 率基準，本次無法比對",
                      f"已建立基準於 {base_path}，下次載入才抓得到漂移",
                      bucket="info", count_label="個欄"))
    ctx.args._null_rate_now = cur
    return out


@rule("Q8", "多幣別未解析", "error",
      "M11 的 ROAS 與預算配置、M8 的 M 值 —— USD 3,200 被當 NT$3,200 會算出 ROAS 37.5",
      "04 §4.1 Q8")
def q8_currency(ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    fx = set()
    try:
        rs = fetch(ctx, "SELECT DISTINCT currency FROM dim_fx_rate")
        fx = {str(r[0]) for r in rs}
    except Exception:  # noqa: BLE001
        pass
    for t, cols in ctx.tables.items():
        for c in cols:
            if not PAT_CURRENCY.search(c.name):
                continue
            n_null = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NULL", 0)
            if n_null:
                out.append(mk("Q8", f"{t}.{c.name}", n_null, ctx.rows[t],
                              f"幣別欄有 {n_null:,} 列為 NULL",
                              "補齊幣別，或在契約宣告單一幣別並移除本欄"))
            if fx:
                bad = [r[0] for r in fetch(
                    ctx, f"SELECT DISTINCT {qi(c.name)} FROM {qi(t)} "
                         f"WHERE {qi(c.name)} IS NOT NULL") if str(r[0]) not in fx]
                if bad:
                    out.append(mk("Q8", f"{t}.{c.name}", len(bad), 0,
                                  f"{len(bad)} 個幣別碼不在 dim_fx_rate：{'、'.join(map(str, bad[:5]))}",
                                  "補 dim_fx_rate 的匯率列，金額換算前不准彙總",
                                  [str(x) for x in bad[:5]], count_label="個幣別碼"))
    return out


@rule("Q17", "負值金額", "error",
      "M8 的 M 值與 VIP 名單、CLV、客單價 —— 買 50 萬退 48 萬會被算成高價值忠誠客",
      "本 skill 新增（18-G2 退貨與取消未處理）")
def q17_negative(ctx: Ctx) -> list[Finding]:
    """金額欄出現負值 = 這批資料混了退貨/沖銷，而且沒有 `txn_type` 可以分辨。

    為什麼是 error 不是 warning：負值不會讓任何步驟報錯，它只會讓 M 值虛胖或虛瘦。
    18-G2 的情境是「顧客買 50 萬退 48 萬，M 虛胖成高價值忠誠，被丟進 VIP 名單」。
    要往下走就在契約宣告 `quality_overrides: [{rule: Q17, decision: …}]` 並說明口徑
    （毛額還是淨額）—— 這正是 18-G2 要求的「指標字典明訂 M 口徑」。
    """
    out: list[Finding] = []
    has_type = {t: any(re.search(r"txn_type|交易類型|交易別|退貨|is_return", c.name, re.I)
                       for c in cols) for t, cols in ctx.tables.items()}
    for t, cols in ctx.tables.items():
        for c in cols:
            if not c.is_num:
                continue
            if not (PAT_AMOUNT.search(c.name)
                    or ctx.contract.unit_of(c.name) in ("TWD", "USD", "JPY", "EUR", "CNY")):
                continue
            n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} < 0", 0)
            if not n:
                continue
            key = cols[0].name
            bad = sample_values(ctx, t, f"{qi(key)} || ':' || CAST({qi(c.name)} AS VARCHAR)",
                                f"{qi(c.name)} < 0")
            tail = ("；本表有交易類型欄，可據以拆毛額/淨額"
                    if has_type[t] else "；本表**沒有** txn_type 欄，無法分辨退貨與正常交易")
            out.append(mk("Q17", f"{t}.{c.name}", n, ctx.rows[t],
                          f"金額欄有 {n:,} 筆負值{tail}",
                          "在指標字典明訂 M 的口徑（預設淨額）並輸出毛額／淨額對照；"
                          "契約寫 quality_overrides: [{rule: Q17, decision: …}] 才放行",
                          bad))
    return out


@rule("Q18", "日期跨界", "error",
      "R 值（未來日 → R 為負）、as_of 時序切分（18-G4 目標洩漏）、時間序列與季節拆解",
      "本 skill 新增（04 §4.2 Q14 只管實體有效期，不管觀察窗）")
def q18_date_range(ctx: Ctx) -> list[Finding]:
    """事件日期欄落在觀察窗之外（> 基準日，或早於 --min-date）。

    為什麼是 error：未來日期會讓 R = as_of − last_date 變成負數，而負的 R 在 RFM 分箱
    裡會落到「最近才買」那一箱 —— 一筆匯入時打錯年份的交易，就能把一個沉睡客送進冠軍群。
    只查事件型日期欄（time_axis 或欄名像交易/訂單/事件），不查到期日 —— 到期日本來就在未來。
    """
    out: list[Finding] = []
    as_of = ctx.as_of or date.today()
    lo = ctx.args.min_date
    for t, cols in ctx.tables.items():
        for c in cols:
            if not c.is_date:
                continue
            use = ctx.contract.use_of(c.name)
            is_event = (use == "time_axis" or
                        (not use and PAT_EVENT_DATE.search(c.name)
                         and not PAT_EXPIRE_DATE.search(c.name)))
            if not is_event:
                continue
            where = (f"CAST({qi(c.name)} AS DATE) > DATE {qs(as_of.isoformat())} "
                     f"OR CAST({qi(c.name)} AS DATE) < DATE {qs(lo)}")
            n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {where}", 0)
            if n:
                bad = sample_values(ctx, t, f"CAST({qi(c.name)} AS DATE)", where)
                out.append(mk("Q18", f"{t}.{c.name}", n, ctx.rows[t],
                              f"{n:,} 筆事件日期落在觀察窗 [{lo}, {as_of}] 之外",
                              "確認基準日 as_of_date 對不對（--as-of），再決定是修值還是移到 隔離區/；"
                              "不准直接刪 —— 樣本流失要能交代（18-E22）",
                              bad))
    return out


@rule("Q19", "孤兒外鍵", "error",
      "join 後的樣本流失（18-E22）、顧客層彙總的分母、RFM 的母體",
      "04 §三 參照完整性（孤兒率 >1% error、>0 warning）")
def q19_orphan(ctx: Ctx) -> list[Finding]:
    """子表的外鍵在父表找不到對應 → join 後那些列會消失，而且沒有人會發現。"""
    out: list[Finding] = []
    for child, ccol, parent, pcol in ctx.edges:
        total = ctx.rows[child] or 1
        sql = (f"SELECT count(*) FROM {qi(child)} c "
               f"LEFT JOIN (SELECT DISTINCT {qi(pcol)} AS k FROM {qi(parent)}) p "
               f"ON c.{qi(ccol)} = p.k WHERE p.k IS NULL AND c.{qi(ccol)} IS NOT NULL")
        n = one(ctx, sql, 0)
        if not n:
            continue
        rate = n / total
        bucket = "error" if rate > ctx.args.orphan_error_rate else "warning"
        bad = [str(r[0]) for r in fetch(
            ctx, f"SELECT DISTINCT c.{qi(ccol)} FROM {qi(child)} c "
                 f"LEFT JOIN (SELECT DISTINCT {qi(pcol)} AS k FROM {qi(parent)}) p "
                 f"ON c.{qi(ccol)} = p.k WHERE p.k IS NULL AND c.{qi(ccol)} IS NOT NULL LIMIT 5")]
        out.append(mk("Q19", f"{child}.{ccol} → {parent}.{pcol}", n, total,
                      f"孤兒 {n:,} 筆（孤兒率 {rate:.2%}）",
                      "補父表的缺列，或在契約宣告這批孤兒的處置（保留為 NULL 外鍵？移到 隔離區/？）；"
                      "報告要寫出 join 前後的樣本數差異",
                      bad, bucket=bucket))
    return out


# ══════════════════════════════════════════════════════════
# warning 桶
# ══════════════════════════════════════════════════════════
@rule("Q9", "Unnamed helper column", "warning",
      "M2 的相關矩陣（18-E10：與本尊得 r=1.00）、M6 的分群輸入白名單",
      "04 §4.2 Q9")
def q9_unnamed(ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        for c in cols:
            if PAT_UNNAMED.match(c.name):
                nn = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NOT NULL", 0)
                out.append(mk("Q9", f"{t}.{c.name}", nn, ctx.rows[t],
                              f"Excel 匿名欄，非空 {nn:,} 列 —— dropna(how='all') 不會刪掉它",
                              "契約標 practical_use: helper，不當業務欄；"
                              "尤其不准進相關矩陣（實測會和 客戶ID 得 r = 1.00）"))
    return out


@rule("Q10", "全形半形混用 / 多餘空白", "warning",
      "group by 會拆成兩群 → M6 分群、卡方交叉表、M8 品類彙總",
      "04 §4.2 Q10")
def q10_fullwidth(ctx: Ctx) -> list[Finding]:
    """全形英數與前後空白。課程資料集這三項全部 0 筆 —— 所以這條必須用髒 fixture 驗。"""
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        for c in cols:
            if not c.is_text:
                continue
            w_full = f"regexp_matches({qi(c.name)}, {qs(SQL_FULLWIDTH)})"
            n_full = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                              f"WHERE {qi(c.name)} IS NOT NULL AND {w_full}", 0)
            if n_full:
                out.append(mk("Q10", f"{t}.{c.name}", n_full, ctx.rows[t],
                              f"{n_full:,} 列含全形英數字或全形空白",
                              "在 staging 層統一半形（NFKC）後再 group by；"
                              "轉換要記進 log_cleaning，不要在分析腳本裡就地改",
                              sample_values(ctx, t, qi(c.name),
                                            f"{qi(c.name)} IS NOT NULL AND {w_full}")))
            w_sp = f"{qi(c.name)} <> trim({qi(c.name)})"
            n_sp = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                            f"WHERE {qi(c.name)} IS NOT NULL AND {w_sp}", 0)
            if n_sp:
                out.append(mk("Q10", f"{t}.{c.name}", n_sp, ctx.rows[t],
                              f"{n_sp:,} 列有前後多餘空白",
                              "staging 層 trim()，同上要記進 log_cleaning",
                              sample_values(ctx, t, f"'[' || {qi(c.name)} || ']'",
                                            f"{qi(c.name)} IS NOT NULL AND {w_sp}")))
    return out


@rule("Q11", "測試交易", "warning",
      "客單價、交易筆數、M11 的門市比較 —— 新店會得到「客單價 87 元」的假結論",
      "04 §4.2 Q11")
def q11_test_txn(ctx: Ctx) -> list[Finding]:
    """金額 ≤ 門檻（預設 10 元）或會員號命中測試值。

    **此處為實作判斷**：04 Q11 還列了 terminal_id 屬測試機、交易日 < 門市 open_date、
    同 terminal 同分鐘筆數 > p99.9 三項，需要 `dim_store` / `dim_terminal` 才能查，
    本腳本只在這些維度表存在時才有辦法做 —— 目前**未實作**，見 known gaps。
    """
    out: list[Finding] = []
    tokens = {"test", "TEST", "0000000", "測試"}
    for t, cols in ctx.tables.items():
        for c in cols:
            if c.is_num and PAT_AMOUNT.search(c.name):
                n = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                             f"WHERE {qi(c.name)} > 0 AND {qi(c.name)} <= {ctx.args.test_amount}", 0)
                if n:
                    out.append(mk("Q11", f"{t}.{c.name}", n, ctx.rows[t],
                                  f"{n:,} 筆金額 ≤ {ctx.args.test_amount} 元，疑似測試交易或極小額",
                                  "逐筆判定；確認是測試就**移到 隔離區/ 不要直接刪**，"
                                  "並在報告交代排除筆數（18-E22）",
                                  sample_values(ctx, t, qi(c.name),
                                                f"{qi(c.name)} > 0 AND {qi(c.name)} <= {ctx.args.test_amount}")))
            if c.is_text and PAT_MEMBER.search(c.name):
                lits = ",".join(qs(x) for x in tokens)
                n = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                             f"WHERE trim({qi(c.name)}) IN ({lits})", 0)
                if n:
                    out.append(mk("Q11", f"{t}.{c.name}", n, ctx.rows[t],
                                  f"{n:,} 列的會員/客戶識別碼是測試值",
                                  "移到 隔離區/ 並在報告交代"))
    return out


@rule("Q12", "bot 與內部流量", "warning",
      "轉換率、M5 漏斗、A/B 檢定的分母 —— bot 從 8% 升到 14% 會偽造出「改版害轉換率下滑」",
      "04 §4.2 Q12")
def q12_bot(ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    found_ua = False
    for t, cols in ctx.tables.items():
        for c in cols:
            if not (c.is_text and PAT_UA.search(c.name)):
                continue
            found_ua = True
            w = f"regexp_matches({qi(c.name)}, {qs(BOT_UA)})"
            n = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                         f"WHERE {qi(c.name)} IS NOT NULL AND {w}", 0)
            if n:
                out.append(mk("Q12", f"{t}.{c.name}", n, ctx.rows[t],
                              f"{n:,} 列的 UA 命中 bot/crawler/monitor 特徵",
                              "**標記 is_bot 不要刪**；排除率週對週變化 >5pp 要 warning、>20% 要 error",
                              sample_values(ctx, t, qi(c.name),
                                            f"{qi(c.name)} IS NOT NULL AND {w}")))
    if not found_ua:
        out.append(mk("Q12", "（無 user_agent 欄）", 0, 0,
                      "本批資料沒有 UA 欄，bot 檢查不適用",
                      "若資料源是網站行為（D5），缺 UA 欄本身就要回頭問上游",
                      bucket="info"))
    return out


@rule("Q13", "編碼序號缺口與命名破格", "warning",
      "用 split 解析編碼的所有品類分析（M8-2 購物籃、因素分析、品類角色）",
      "04 §4.2 Q13")
def q13_code_gap(ctx: Ctx) -> list[Finding]:
    """類別編碼的數字前綴不連續，或有值不符主要命名慣例。

    實測：15 種產業分類前綴為 [2,3,5,…,16]，缺 01、04；且 `X2.中信錢加值` 用點分隔
    + 字母前綴 —— 用 `split('_')` 解析會在那一列爆掉。
    """
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        for c in cols:
            if not c.is_text:
                continue
            vals = [str(r[0]) for r in fetch(
                ctx, f"SELECT DISTINCT {qi(c.name)} FROM {qi(t)} "
                     f"WHERE {qi(c.name)} IS NOT NULL LIMIT 200")]
            if not (2 <= len(vals) <= ctx.args.max_category):
                continue
            hit = [v for v in vals if PAT_CODE_PREFIX.match(v)]
            if len(hit) < max(2, 0.5 * len(vals)):
                continue
            nums = sorted({int(PAT_CODE_PREFIX.match(v).group(1)) for v in hit})
            # 編碼慣例是從 1（01）起編；最小前綴 ≤3 時從 1 起算，才抓得到「開頭就缺」
            # —— 實測產業分類前綴 [2,3,5,…,16] 缺的是 01 與 04，只從 min 起算會漏掉 01
            lo = 1 if min(nums) <= 3 else min(nums)
            gaps = [n for n in range(lo, max(nums) + 1) if n not in nums]
            odd = [v for v in vals if v not in hit]
            if gaps:
                out.append(mk("Q13", f"{t}.{c.name}", len(gaps), 0,
                              f"編碼前綴 {nums} 不連續，缺 {gaps}",
                              "確認缺的編碼是「本資料集沒有」還是「上游漏給」——"
                              "後者會讓品類覆蓋率被高估",
                              count_label="個編碼缺口"))
            if odd:
                out.append(mk("Q13", f"{t}.{c.name}", len(odd), 0,
                              f"{len(odd)} 個值不符主要命名慣例（NN_名稱）：{'、'.join(odd[:5])}",
                              "不要用 split('_') 解析編碼；改用 regexp_extract 並處理不匹配的情況",
                              odd[:5], count_label="個破格值"))
    return out


@rule("Q14", "時序矛盾", "warning",
      "卡齡／tenure（18-G3 cohort 未對齊）、存活分析、任何用「第一次」定義的變數",
      "04 §4.2 Q14")
def q14_time_paradox(ctx: Ctx) -> list[Finding]:
    """三種矛盾：表內 開始日 > 結束日、跨表 子表事件日 < 父表建立日、實體在基準日已失效。"""
    out: list[Finding] = []
    # ① 表內：建立日 > 失效日
    for t, cols in ctx.tables.items():
        starts = [c for c in cols if c.is_date and PAT_CREATE_DATE.search(c.name)]
        ends = [c for c in cols if c.is_date and PAT_EXPIRE_DATE.search(c.name)]
        for s in starts:
            for e in ends:
                n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(s.name)} > {qi(e.name)}", 0)
                if n:
                    out.append(mk("Q14", f"{t}.{s.name} > {t}.{e.name}", n, ctx.rows[t],
                                  f"{n:,} 列的起始日晚於結束日",
                                  "這兩欄至少有一欄的語意與欄名不符，回頭問上游；先不要拿來算存續期間"))
        # ③ 基準日之後才失效才算有效
        if ctx.as_of:
            for e in ends:
                n = one(ctx, f"SELECT count(*) FROM {qi(t)} "
                             f"WHERE CAST({qi(e.name)} AS DATE) < DATE {qs(ctx.as_of.isoformat())}", 0)
                if n:
                    out.append(mk("Q14", f"{t}.{e.name}", n, ctx.rows[t],
                                  f"{n:,} 列在基準日 {ctx.as_of} 已失效，卻仍列在有效檔裡",
                                  "決定是排除還是保留；保留的話所有「持有數」類指標都要標明含已失效實體"))
    # ② 跨表：子表事件日早於父表的建立日
    #    子表只看「事件日／建立日」，不看到期日 —— 到期日早於父表建立日是①的衍生現象，
    #    重複報一次只會讓 warning 桶變吵，而吵掉的第一個受害者是真正該看的那條
    for child, ccol, parent, pcol in ctx.edges:
        cdates = [c for c in ctx.cols(child)
                  if c.is_date and not PAT_EXPIRE_DATE.search(c.name)]
        pdates = [c for c in ctx.cols(parent)
                  if c.is_date and PAT_CREATE_DATE.search(c.name)]
        for cd in cdates:
            for pd_ in pdates:
                sql = (f"SELECT count(*), count(DISTINCT c.{qi(ccol)}) FROM {qi(child)} c "
                       f"JOIN {qi(parent)} p ON c.{qi(ccol)} = p.{qi(pcol)} "
                       f"WHERE CAST(c.{qi(cd.name)} AS DATE) < CAST(p.{qi(pd_.name)} AS DATE)")
                r = fetch(ctx, sql)
                n, n_key = (r[0][0], r[0][1]) if r else (0, 0)
                if n:
                    gap = one(ctx, f"SELECT max(datediff('day', CAST(c.{qi(cd.name)} AS DATE), "
                                   f"CAST(p.{qi(pd_.name)} AS DATE))) FROM {qi(child)} c "
                                   f"JOIN {qi(parent)} p ON c.{qi(ccol)} = p.{qi(pcol)} "
                                   f"WHERE CAST(c.{qi(cd.name)} AS DATE) < CAST(p.{qi(pd_.name)} AS DATE)", 0)
                    out.append(mk("Q14", f"{child}.{cd.name} < {parent}.{pd_.name}",
                                  n, ctx.rows[child],
                                  f"{n:,} 列（{n_key:,} 個 {ccol}）的事件早於父表宣稱的建立日，"
                                  f"最大差 {gap:,} 天",
                                  f"不要用 {parent}.{pd_.name} 算年資／卡齡，"
                                  f"改用 min({child}.{cd.name})；差異要寫進報告"))
    return out


@rule("Q15", "樣本不足的實體", "warning",
      "CAI/WMLE/CRI 的覆蓋率與分群輸入資格（04 §七：<60% 不得當分群輸入）",
      "04 §4.2 Q15")
def q15_thin_entity(ctx: Ctx) -> list[Finding]:
    """間隔型指標要 ≥3 個去重消費日（≥2 個間隔）才算得出來。

    只有 1 個間隔時 WMLE ≡ MLE、CAI 恆為 0，那是零資訊不是節奏穩定 ——
    依 17 §4.2 的 NORM.DIST 轉換，這種人會被貼成第 50 百分位的「最穩定」中位顧客。
    """
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        subj = pick_subject(ctx, t)
        tcol = pick_time_axis(ctx, t)
        if not subj or not tcol:
            continue
        # 只有事實表（一個主體多列）才談得上「間隔」。維度表一人一列，
        # 它的日期欄是屬性不是事件軸 —— 拿生日去算購買間隔是無意義的紅字
        n_subj = one(ctx, f"SELECT count(DISTINCT {qi(subj)}) FROM {qi(t)}", 0)
        if n_subj >= ctx.rows[t]:
            continue
        need = ctx.args.min_event_days
        sql = (f"SELECT count(*) FROM (SELECT {qi(subj)} FROM {qi(t)} "
               f"GROUP BY {qi(subj)} HAVING count(DISTINCT CAST({qi(tcol)} AS DATE)) < {need})")
        n = one(ctx, sql, 0)
        n_all = one(ctx, f"SELECT count(DISTINCT {qi(subj)}) FROM {qi(t)}", 0)
        if n:
            bad = [str(r[0]) for r in fetch(
                ctx, f"SELECT {qi(subj)} FROM {qi(t)} GROUP BY {qi(subj)} "
                     f"HAVING count(DISTINCT CAST({qi(tcol)} AS DATE)) < {need} LIMIT 5")]
            out.append(mk("Q15", f"{t}.{subj}（依 {tcol}）", n, n_all,
                          f"{n:,}/{n_all:,} 個實體的去重事件日 < {need}，算不出可用的間隔型指標",
                          f"算 CAI/WMLE/CRI 前先決定：補值、標記還是排除；"
                          f"覆蓋率要照 04 §七 兩層都報（≥{need} 天一層、間隔 ≥5 一層）",
                          bad, count_label="個實體"))
    return out


@rule("Q16", "缺幣別欄", "warning",
      "M 值的幣別、跨帳戶／跨市場彙總",
      "04 §4.2 Q16")
def q16_no_currency(ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        has_amt = [c for c in cols if c.is_num and PAT_AMOUNT.search(c.name)]
        has_cur = any(PAT_CURRENCY.search(c.name) for c in cols)
        if has_amt and not has_cur:
            names = "、".join(c.name for c in has_amt)
            out.append(mk("Q16", f"{t}({names})", len(has_amt), 0,
                          "有金額欄但沒有幣別欄，單位靠推定",
                          "在契約的 columns[].unit 明寫幣別（例：TWD），"
                          "報告要寫 WARNING: currency column absent, unit inferred",
                          count_label="個金額欄"))
    return out


@rule("Q20", "缺失率門檻", "warning",
      "補值方法可用性（>40% 時 MICE/迴歸補出來的是模型不是資料）、M3 轉換、M6 分群",
      "04 §二 逐欄剖析（≥5% warning／≥40% error／≥80% 建議棄用）")
def q20_null_rate(ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for t, cols in ctx.tables.items():
        total = ctx.rows[t]
        if not total:
            continue
        for c in cols:
            nn = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NULL", 0)
            rate = nn / total
            if rate < ctx.args.null_warn_rate:
                continue
            if rate >= ctx.args.null_drop_rate:
                bucket, act = "error", "缺失率過高，建議棄用本欄；要留就必須在契約說明它憑什麼可信"
            elif rate >= ctx.args.null_error_rate:
                bucket, act = "error", ("在契約宣告補值或排除方式；"
                                        "缺失率 >40% 時 MICE/迴歸補出來的是模型不是資料")
            else:
                bucket, act = "warning", "列入報告的『資料限制』節，並在缺失值總表寫處理決議與理由"
            out.append(mk("Q20", f"{t}.{c.name}", nn, total,
                          f"缺失率 {rate:.2%}", act, bucket=bucket))
    return out


# ── 角色推定（沒有契約時的退路） ─────────────────────────
def pick_subject(ctx: Ctx, table: str) -> str | None:
    """分析主體鍵。單欄 grain 本身是「列的身分」不是「主體」—— 契約若把交易序號
    誤標成 subject_key，這裡要擋掉，否則 Q15 會拿一列一個的主鍵去算間隔。"""
    g = grains(ctx).get(table, [])
    row_key = g[0] if len(g) == 1 else None
    for c in ctx.cols(table):
        if ctx.contract.use_of(c.name) == "subject_key" and c.name != row_key:
            return c.name
    for c in ctx.cols(table):
        if re.search(r"^(客戶ID|會員ID|customer_id|member_id|顧客ID)$", c.name, re.I):
            return c.name
    return None


def pick_time_axis(ctx: Ctx, table: str) -> str | None:
    """事件時間軸。**不做「隨便挑一個日期欄」的退路** —— 生日、開卡日、到期日
    都是屬性不是事件軸，挑錯了 Q15 會對每張維度表噴一條假紅字。"""
    for c in ctx.cols(table):
        if ctx.contract.use_of(c.name) == "time_axis":
            return c.name
    for c in ctx.cols(table):
        if (c.is_date and PAT_EVENT_DATE.search(c.name)
                and not PAT_EXPIRE_DATE.search(c.name)
                and not PAT_CREATE_DATE.search(c.name)):
            return c.name
    return None


def grains(ctx: Ctx) -> dict[str, list[str]]:
    """grain 來源優先序：--grain > 契約 grain。"""
    g: dict[str, list[str]] = dict(ctx.contract.grain)
    for spec in ctx.args.grain:
        if "=" in spec:
            t, cols = spec.split("=", 1)
            g[t.strip()] = [c.strip() for c in cols.split(",") if c.strip()]
    return g


def infer_edges(ctx: Ctx) -> list[tuple[str, str, str, str]]:
    """推定外鍵邊：同名欄在另一張表裡唯一且非空 → 那張表是父表。

    **此處為實作判斷**：契約沒有 foreign_keys 鍵，所以用同名 + 父表唯一來推。
    要精確控制就用 --fk 子表.欄=父表.欄。
    """
    edges: list[tuple[str, str, str, str]] = []
    for spec in ctx.args.fk:
        if "=" in spec:
            left, right = spec.split("=", 1)
            if "." in left and "." in right:
                ct, cc = left.split(".", 1)
                pt, pc = right.split(".", 1)
                edges.append((ct.strip(), cc.strip(), pt.strip(), pc.strip()))
    if edges:
        return edges
    unique_keys: dict[tuple[str, str], bool] = {}
    for t, cols in ctx.tables.items():
        for c in cols:
            n = one(ctx, f"SELECT count(*) FROM {qi(t)} WHERE {qi(c.name)} IS NOT NULL", 0)
            nq = one(ctx, f"SELECT count(DISTINCT {qi(c.name)}) FROM {qi(t)}", 0)
            unique_keys[(t, c.name)] = bool(n) and n == nq == ctx.rows[t]
    for ct, ccols in ctx.tables.items():
        for c in ccols:
            for pt in ctx.tables:
                if pt == ct:
                    continue
                if unique_keys.get((pt, c.name)) and not unique_keys.get((ct, c.name)):
                    edges.append((ct, c.name, pt, c.name))
    return edges


# ── 契約與 profile 載入 ──────────────────────────────────
def load_contract(path: Path | None) -> Contract:
    if path is None:
        return Contract()
    if not path.exists():
        raise FileNotFoundError(
            f"找不到契約檔：{path}\n"
            f"  契約住在 <專案>/原始資料/contracts/<source>.yml（03 §1.2）。"
            f"首次進場沒有契約時先跑 profile_dataset.py 生草稿，或先不要帶 --contract。")
    try:
        import yaml
    except ImportError as e:
        raise RuntimeError(
            "要讀契約檔但沒有 PyYAML。跑 pip install pyyaml，"
            "或先不要帶 --contract（判定力會下降）") from e

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    grain = raw.get("grain") or {}
    if isinstance(grain, list):                       # 單表契約的簡寫
        grain = {"*": [str(x) for x in grain]}
    grain = {str(k): [str(x) for x in (v or [])] for k, v in grain.items()}
    cols = {}
    for item in raw.get("columns") or []:
        if isinstance(item, dict) and item.get("name"):
            cols[str(item["name"])] = item
    ov: dict[str, list[dict[str, Any]]] = {}
    for item in raw.get("quality_overrides") or []:
        if isinstance(item, dict) and item.get("rule"):
            ov.setdefault(str(item["rule"]).upper(), []).append(item)
    return Contract(path=path, source=str(raw.get("source", "")), grain=grain,
                    columns=cols, sentinels=list(raw.get("sentinels") or []),
                    overrides=ov)


def load_profile(path: Path | None) -> dict[tuple[str, str], dict[str, str]]:
    """讀 profile_dataset.py 的 `開案與問題定義/欄位總表.csv`（schema 見 04 §二）。"""
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(
            f"找不到欄位總表：{path}\n"
            f"  它由 profile_dataset.py（M1 步驟③）產出。先跑剖析，或不要帶 --profile。")
    out: dict[tuple[str, str], dict[str, str]] = {}
    seen: dict[str, set[str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            t = (row.get("table") or "").strip()
            c = (row.get("column") or "").strip()
            if c:
                out[(t, c)] = {k: (v or "").strip() for k, v in row.items()}
                seen.setdefault(c, set()).add(t)
    # 剖析時的表名（工作表名）常和這裡 --file 給的別名不同，
    # 所以欄名只出現在一張表時額外掛一個不分表的索引，避免整份剖析結果對不上
    for (t, c), v in list(out.items()):
        if len(seen.get(c, ())) == 1:
            out[("", c)] = v
    return out


# ── 資料源掛載 ───────────────────────────────────────────
def mount(con: Any, spec: str) -> str:
    """把 parquet/csv 掛成 TEMP VIEW，回傳表名。spec = [別名=]路徑。"""
    # 只有「=」出現在第一個路徑分隔符之前才算別名，避免吃掉路徑裡的等號
    eq = spec.find("=")
    sep = min([i for i in (spec.find("/"), spec.find("\\")) if i >= 0] or [len(spec)])
    alias, raw = (spec[:eq], spec[eq + 1:]) if 0 < eq < sep else ("", spec)
    path = Path(raw).expanduser()
    name = alias.strip() or path.stem
    if not path.exists():
        raise FileNotFoundError(
            f"找不到資料檔：{path}\n  確認路徑，或改用 --table 檢查倉儲裡既有的表。")
    suf = path.suffix.lower()
    if suf == ".parquet":
        reader = f"read_parquet({qs(path.as_posix())})"
    elif suf in (".csv", ".txt", ".tsv"):
        reader = f"read_csv_auto({qs(path.as_posix())})"
    else:
        raise ValueError(
            f"不支援的副檔名：{suf}（{path.name}）\n"
            f"  只吃 .parquet / .csv。Excel 請先用 profile_dataset.py 串流轉出 parquet —— "
            f"pandas.read_excel() 在 971 MB 的 sheet 上峰值可破 8 GB（04 §一）。")
    con.execute(f"CREATE OR REPLACE TEMP VIEW {qi(name)} AS SELECT * FROM {reader}")
    return name


def describe(con: Any, table: str) -> list[Col]:
    rows = con.execute(f"DESCRIBE SELECT * FROM {qi(table)}").fetchall()
    return [Col(table, r[0], r[1]) for r in rows]


# ── 輸出 ─────────────────────────────────────────────────
def print_bucket(title: str, icon: str, findings: list[Finding], verbose: bool) -> None:
    if not findings:
        return
    print(f"\n{icon} {title}（{len(findings)} 條）")
    print("-" * 72)
    for f in findings:
        print(f"  {icon} {f.headline()}")
        print(f"     · {f.detail}")
        if f.samples:
            print(f"     · 前 {len(f.samples)} 筆：{'、'.join(f.samples)}")
        print(f"     · 影響下游：{f.downstream}")
        print(f"     → {f.action}")
        if f.note:
            print(f"     · 註：{f.note}")
        if verbose:
            print(f"     · 出處：{RULES[f.rule].source}")


def write_report(pp: Any, findings: list[Finding], meta: dict[str, Any]) -> list[Path]:
    """三桶結果的落點是 `統計表/資料體檢/`（03 §1.2）。CSV 最後一欄是中文結論（18-E15）。"""
    out_dir = pp.tables / "資料體檢"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "M1_品質檢查三桶.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["規則", "檢查項", "桶", "檢查對象", "筆數", "母數", "占比",
                    "影響的下游分析", "規格出處", "實例", "中文結論"])
        for f in findings:
            w.writerow([f.rule, f.name, f.bucket, f.target, f.n, f.total or "",
                        f"{f.pct:.4f}" if f.total else "", f.downstream,
                        RULES[f.rule].source, "｜".join(f.samples), f.conclusion()])
    json_path = out_dir / "M1_品質檢查三桶.json"
    json_path.write_text(json.dumps(
        {"meta": meta,
         "findings": [{"rule": f.rule, "name": f.name, "bucket": f.bucket,
                       "target": f.target, "n": f.n, "total": f.total,
                       "detail": f.detail, "action": f.action,
                       "downstream": f.downstream, "samples": f.samples,
                       "note": f.note, "source": RULES[f.rule].source}
                      for f in findings]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return [csv_path, json_path]


def list_rules() -> None:
    print("=" * 72)
    print("check_data_quality.py — 檢查條目（用 --only / --skip 單獨開關）")
    print("=" * 72)
    print(pad("代號", 6) + pad("預設桶", 10) + pad("檢查項", 26) + "出處")
    print("-" * 72)
    for code in sorted(RULES, key=lambda x: int(x[1:])):
        r = RULES[code]
        print(pad(r.code, 6) + pad(r.bucket, 10) + pad(r.name, 26) + r.source)
        print(f"      影響下游：{r.downstream}")


# ── 主流程 ───────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="M1 資料品質三桶（error/warning/info + exit code 0/1/2/3）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", help="專案代號（路徑由 paths.py 解析）")
    ap.add_argument("--table", action="append", default=[], help="檢查倉儲裡既有的表，可重複")
    ap.add_argument("--file", action="append", default=[],
                    help="檢查尚未進倉的 parquet/csv，格式 [別名=]路徑，可重複")
    ap.add_argument("--contract", type=Path, help="契約檔 contracts/<source>.yml")
    ap.add_argument("--profile", type=Path, help="profile_dataset.py 的 欄位總表.csv")
    ap.add_argument("--grain", action="append", default=[], help="表名=欄1,欄2，覆寫契約的 grain")
    ap.add_argument("--fk", action="append", default=[], help="子表.欄=父表.欄，不給就自動推定")
    ap.add_argument("--denominator", action="append", default=[], help="表.欄，指定比率型指標的分母")
    ap.add_argument("--as-of", dest="as_of", help="基準日 YYYY-MM-DD（Q14/Q18 用）")
    ap.add_argument("--only", default="", help="只跑這幾條，逗號分隔（例：Q1,Q2,Q6）")
    ap.add_argument("--skip", default="", help="跳過這幾條，逗號分隔")
    ap.add_argument("--list", action="store_true", help="列出全部檢查條目後結束")
    ap.add_argument("--verbose", action="store_true", help="連通過的檢查與規格出處都印")
    ap.add_argument("--no-write", action="store_true", help="不要寫統計表（預設會寫）")
    # 門檻（每一個的理由都在 04，改門檻要一併改理由）
    ap.add_argument("--null-warn-rate", type=float, default=0.05, help="缺失率 warning 門檻（04 §二：5%%）")
    ap.add_argument("--null-error-rate", type=float, default=0.40, help="缺失率 error 門檻（04 §二：40%%）")
    ap.add_argument("--null-drop-rate", type=float, default=0.80, help="缺失率建議棄用門檻（04 §二：80%%）")
    ap.add_argument("--null-drift", type=float, default=0.20, help="Q7 NULL 率漂移門檻（04：20pp）")
    ap.add_argument("--orphan-error-rate", type=float, default=0.01, help="Q19 孤兒率 error 門檻（04 §三：1%%）")
    ap.add_argument("--min-event-days", type=int, default=3, help="Q15 間隔型指標最低去重事件日（04 §七：3）")
    ap.add_argument("--test-amount", type=float, default=10, help="Q11 測試交易金額門檻（04：10 元）")
    ap.add_argument("--sentinel-near", type=float, default=0.02, help="Q2「極接近鍵基數」的相對容差")
    ap.add_argument("--cast-hint-rate", type=float, default=0.80, help="Q1 無契約時判定「本該是數值欄」的成功率門檻")
    ap.add_argument("--min-date", default="1900-01-01", help="Q18 日期下界")
    ap.add_argument("--max-category", type=int, default=60, help="Q13 視為類別欄的相異值上限")
    return ap


def run(args: argparse.Namespace) -> int:
    if args.list:
        list_rules()
        return 0
    if not args.project:
        print("⛔ 缺少專案代號 — 用法：python check_data_quality.py <專案代號> "
              "--table <表> 或 --file [別名=]<路徑>；只想看檢查清單就下 --list")
        return 3
    if not args.table and not args.file:
        print("⛔ 沒有指定要檢查什麼 — 至少給一個 --table 或 --file。"
              "M1 的閘門不能對空集合放行。")
        return 3

    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    skip = {x.strip().upper() for x in args.skip.split(",") if x.strip()}
    unknown = (only | skip) - set(RULES)
    if unknown:
        print(f"⛔ 不認識的檢查代號：{'、'.join(sorted(unknown))} — 下 --list 看合法代號")
        return 3

    contract = load_contract(args.contract)
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else None

    pp = project_dir(args.project, create=True)
    auto_profile = False
    if args.profile is None:
        # profile_dataset.py（M1 步驟③）的落點固定在這裡，有就自動接上
        cand = pp.intake / "欄位總表.csv"
        if cand.exists():
            args.profile, auto_profile = cand, True
    profile = load_profile(args.profile)
    args._baseline_path = pp.log / "null_rate_baseline.json"
    args._null_rate_now = {}

    findings: list[Finding] = []
    ran: list[str] = []
    with connect(args.project) as con:
        tables: dict[str, list[Col]] = {}
        for spec in args.file:
            tables[mount(con, spec)] = []
        for t in args.table:
            tables[t] = []
        for t in list(tables):
            try:
                tables[t] = describe(con, t)
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(
                    f"讀不到表 {t}：{e}\n"
                    f"  確認表名拼字，或先把資料載進倉儲（M3）。"
                    f"現有表可用 python db.py {args.project} 查。") from e

        rows = {t: con.execute(f"SELECT count(*) FROM {qi(t)}").fetchone()[0] for t in tables}
        ctx = Ctx(con=con, tables=tables, rows=rows, contract=contract, profile=profile,
                  edges=[], as_of=as_of, args=args)
        ctx.edges = infer_edges(ctx)

        # 標題
        print("=" * 72)
        print("行銷數據分析 Skill — M1 資料品質三桶（M1 → M2 的唯一放行機制）")
        print(f"專案：{args.project}｜基準日：{as_of or '未指定'}")
        print(f"表：{'、'.join(f'{t}（{rows[t]:,} 列）' for t in tables)}")
        print(f"契約：{contract.path or '未提供 —— 欄位角色改用欄名樣式推定，判定力下降'}")
        if profile:
            print(f"欄位總表：{args.profile}"
                  f"{'（自動接上 profile_dataset 的產出）' if auto_profile else ''}")
        if ctx.edges:
            print("推定外鍵：" + "、".join(f"{a}.{b}→{c}.{d}" for a, b, c, d in ctx.edges))
        print("=" * 72)

        for code in sorted(RULES, key=lambda x: int(x[1:])):
            if only and code not in only:
                continue
            if code in skip:
                continue
            ran.append(code)
            try:
                findings.extend(RULES[code].fn(ctx))
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"檢查 {code}（{RULES[code].name}）執行失敗：{e!r}") from e

    # 契約 quality_overrides：exit code 1 的唯一解除途徑（02 §十）
    # **此處為實作判斷**：02 §十 的 override 是規則層的，一寫 Q20 就會把所有欄的缺失率
    # 一起放行。本腳本額外支援選填的 `column:` 把 override 收窄到單一欄／單一對象；
    # 不寫 column 就維持 02 的規則層語意。
    for f in findings:
        if f.bucket == "info":
            continue
        for ov in contract.overrides.get(f.rule, []):
            scope = str(ov.get("column") or ov.get("target") or "")
            if scope and scope not in f.target:
                continue
            f.note = (f"契約 quality_overrides 已宣告 decision={ov.get('decision')}"
                      f"{'（僅限 ' + scope + '）' if scope else ''}"
                      f"（{ov.get('decided_by', '?')} {ov.get('decided_on', '?')}）："
                      f"{ov.get('reason', '')}")
            f.bucket = "info"
            break

    errs = [f for f in findings if f.bucket == "error"]
    warns = [f for f in findings if f.bucket == "warning"]
    infos = [f for f in findings if f.bucket == "info"]

    if args.verbose:
        hit = {f.rule for f in findings}
        clean = [c for c in ran if c not in hit]
        if clean:
            print(f"\n✅ 通過（{len(clean)} 條）")
            print("-" * 72)
            for c in clean:
                print(f"  ✅ {c} {RULES[c].name}")

    print_bucket("info — 記錄，不阻擋", "·", infos, args.verbose)
    print_bucket("warning — 可往下，但必須寫進報告的『資料限制』節", "⚠", warns, args.verbose)
    print_bucket("error — 擋住，不准進 M2", "⛔", errs, args.verbose)

    if not args.no_write:
        meta = {"project": args.project, "as_of": str(as_of or ""),
                "tables": {t: rows[t] for t in tables},
                "contract": str(contract.path or ""), "rules_run": ran,
                "generated_at": datetime.now().isoformat(timespec="seconds")}
        for p in write_report(pp, findings, meta):
            print(f"\n· 已寫出：{p}")
        if args._null_rate_now and "Q7" in ran:
            args._baseline_path.parent.mkdir(parents=True, exist_ok=True)
            args._baseline_path.write_text(json.dumps(
                {"generated_at": datetime.now().isoformat(timespec="seconds"),
                 "null_rate": args._null_rate_now}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            print(f"· NULL 率基準已更新：{args._baseline_path}")

    print("\n" + "=" * 72)
    print(f"跑了 {len(ran)} 條檢查｜error {len(errs)}、warning {len(warns)}、info {len(infos)}")
    if errs:
        print("結果：⛔ 擋住，不准進 M2。")
        print("      解除途徑只有一條：在契約的 quality_overrides: 逐條宣告處理方式"
              "（rule / decision / reason / decided_by / decided_on）後重跑（02 §十）。")
        return 1
    if warns:
        print("結果：⚠ 可進 M2，但上列 warning 必須逐條寫進報告的「資料限制」節。")
        return 2
    print("結果：✅ 三桶無 error 無 warning → 可進 M2。")
    print("      提醒：課程級的乾淨資料集上 Q1/Q6/Q7/Q8/Q10/Q11/Q12 永遠不會變紅，"
          "全綠不等於檢查器有效（04 §九）。")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args)
    except Exception as e:  # noqa: BLE001
        print(f"\n⛔ 檢查腳本本身失敗：{e}", file=sys.stderr)
        print("   退出碼 3 —— 修腳本或修參數，不准手動略過這一關（04 §四）。", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
