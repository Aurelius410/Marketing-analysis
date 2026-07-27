#!/usr/bin/env python3
"""
欄位契約比對 —— M1 步驟②，寫進 raw 之前的最後一道 schema 關卡。

為什麼需要它（不是「多一道手續」）：
  · 上游改欄名不會報錯。Meta 報表 `Amount spent (TWD)` 改叫 `Spend`，`union_by_name`
    會**靜默拆成兩欄各半 NULL** → 近三個月 spend 全 NULL → ROAS 從 1.6 算成 3.2 →
    「建議預算加倍」。全程零紅字（03 W5、18-G1 系列的 gap D1）。
  · 上游多一個沒見過的分類值，groupby 就多一列、對照表就漏接、卡方期望次數被稀釋。
  · 04 §一 步驟② 明訂：**契約有、實檔沒有 → error；實檔有、契約沒有 → error**。
    先擋在這裡，比讓錯誤資料進 raw 之後再回頭清便宜一個數量級 —— raw 是唯讀凍結層。
  · 契約本身也會被偷改。改了 `grain`、刪了 `renames` 舊鍵，半年前那份報告就重跑不出來
    （02 §十 末段）。本腳本存快照，下次偷改直接擋。

規格出處：
  · 04_資料體檢.md §一 步驟②（比對規則）、§四（三桶與退出碼語意）
  · 02_資料模型規格.md §十（契約檔欄位規格：source/encoding/source_tz/grain/columns/
    renames/sentinels/quality_overrides）
  · 18_分析陷阱清單.md G1–G16（G10 指標口徑、G11 品質關卡、G13 PII）
  · 03_倉儲與檔案結構.md §2（契約放 原始資料/contracts/）、W5（renames append-only）

此處為實作判斷（reference 未定義，本腳本擴充）：
  · `enum_domains` —— 02 §十 沒有這個鍵。它是 04 Q13「編碼序號缺口與命名破格」的事前版本。
  · `columns[].table` —— 02 §十 的範例是跨表聯集清單；同一欄名在不同表角色不同
    （客戶ID 在交易檔是 fk、在客戶檔是 subject_key），故允許逐表宣告。省略即「任一表」。
  · 型別不符的分級 —— 02 §3.1 規定 raw 一律 VARCHAR、型別轉換延到 staging，所以
    「實檔是 VARCHAR 但契約宣告 BIGINT」是規約而非錯誤（info）。只有「幣別欄宣告成
    DOUBLE/FLOAT」是 error（02 §十 明文禁止）。其餘型別族不同一律 warning。
  · grain 唯一性 —— 04 §三 要求 grain 變成持續斷言，Q6 判 error。本腳本一併跑，
    fail closed（寧可兩支腳本都擋，不要兩支都以為對方會擋）。

三桶 + 退出碼（全庫統一，權威定義見 00 §八；與 setup_check.py、
check_data_quality.py、verify_outputs 同一套，不准對調）：
    0  = 三桶皆空或只有 info      → 可進步驟③
    1  = 有 error                 → 擋住，必須在契約裡宣告處理方式後重跑
    2  = 只有 warning             → 可往下，但條目要進報告的「資料限制」節
    64 = 用法錯誤（旗標打錯、--source 與 --contract 都沒給）→ 比對根本沒跑
    70 = 腳本本身失敗             → 修腳本，不准手動略過（舊版是 3）

用法：
    # 契約放 <專案>/原始資料/contracts/<source>.yml，實檔放 <專案>/原始資料/
    python check_schema_contract.py 2026Q3_電商 --source ntu_creditcard

    # 資料還沒進專案，直接指到素材位置
    python check_schema_contract.py 示範專案 --source ntu_creditcard \\
        --data D:/samples/ntu_creditcard__transactions.parquet \\
        --data D:/samples/ntu_creditcard__customers.parquet

    # 只看有哪些差異、不寫報告也不動快照
    python check_schema_contract.py 示範專案 --source ntu_creditcard --dry-run --verbose

首次進場還沒有契約：拿 templates/contracts/example.yml 當骨架，或跑 profile_dataset.py
由步驟③ 的剖析結果生草稿 —— 草稿要交包子確認後才算數（04 §一 步驟②）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import (  # noqa: E402
    ContractError, is_currency, load_contract, qi, qs as ql,
)
from db import connect  # noqa: E402
from exitcodes import (  # noqa: E402
    EX_OK, EX_ERROR, EX_WARN, EX_SOFTWARE, GateArgumentParser,
)
from paths import project_dir  # noqa: E402

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


# ══ 三桶 ════════════════════════════════════════════════════════════════
errors: list[str] = []
warnings: list[str] = []
infos: list[str] = []


def err(fact: str, todo: str) -> None:
    """error：擋住。訊息一律「事實 — 該怎麼辦」兩段式。"""
    errors.append(f"{fact} — {todo}")


def warn(fact: str, todo: str) -> None:
    warnings.append(f"{fact} — {todo}")


def info(msg: str) -> None:
    infos.append(msg)


# ContractError / load_contract / qi / ql / is_currency 都由 scripts/contract.py 提供
# （import 在檔頭）—— 本檔與 check_data_quality.py 讀同一個 contracts/<source>.yml，
# 解析實作只能有一份，否則契約 schema 一改就兩邊分岔。


def detail(bucket: list[str], line: str) -> None:
    """明細行。縮排四格，計數時不另計為一項。"""
    bucket.append(f"    · {line}")


# ══ 規格常數（全部有出處） ═══════════════════════════════════════════════
# 02 §十：contracts 必填鍵
REQUIRED_KEYS = ["source", "encoding", "source_tz", "grain", "columns"]

# 04 §二：實務用途七標籤。deprecated 併入 helper 分支
PRACTICAL_USES = {
    "subject_key", "fk", "time_axis", "measure",
    "segment_input", "profile_only", "helper", "deprecated",
}

# 02 §十：unit 值域。三碼大寫視為 ISO-4217 幣別（is_currency 在 contract.py）
UNIT_VOCAB = {"ratio", "percent", "days", "count", "—", "-", "—"}

# 02 §十：sentinels.action
SENTINEL_ACTIONS = {"to_null", "keep", "exclude"}

# 04 §四：品質規則編號 Q1–Q16
QUALITY_RULES = {f"Q{i}" for i in range(1, 17)}
OVERRIDE_KEYS = ["rule", "decision", "reason", "decided_by", "decided_on"]

# enum_domains 的未知值處置（本 skill 擴充）
ON_UNKNOWN = {"error", "warn"}

# columns[] 允許的鍵。多出來的鍵 99% 是 YAML flow mapping 的逗號陷阱造成的：
#   {name: 刷卡金額, dtype: DECIMAL(18,4), unit: TWD}
# 在 `{}` 裡逗號是分隔符，會被拆成 `dtype: DECIMAL(18` 與一個叫 `4)` 的空鍵，
# **YAML 不會報錯**，型別比對從此永遠對不上。dtype 帶括號一律加引號。
COLUMN_KEYS = {"table", "name", "dtype", "unit", "nullable", "practical_use", "note"}

# DuckDB 型別族。比對用族，不用字面 —— DECIMAL(18,4) 與 DECIMAL(18,6) 不該互相報錯
_TYPE_FAMILY: dict[str, str] = {
    "TINYINT": "int", "SMALLINT": "int", "INTEGER": "int", "INT": "int",
    "INT1": "int", "INT2": "int", "INT4": "int", "INT8": "int",
    "BIGINT": "int", "HUGEINT": "int", "UHUGEINT": "int", "LONG": "int",
    "UTINYINT": "int", "USMALLINT": "int", "UINTEGER": "int", "UBIGINT": "int",
    "DECIMAL": "decimal", "NUMERIC": "decimal",
    "FLOAT": "float", "REAL": "float", "FLOAT4": "float",
    "DOUBLE": "float", "FLOAT8": "float",
    "VARCHAR": "str", "CHAR": "str", "BPCHAR": "str", "TEXT": "str", "STRING": "str",
    "DATE": "date",
    "TIMESTAMP": "timestamp", "DATETIME": "timestamp",
    "TIMESTAMP_NS": "timestamp", "TIMESTAMP_MS": "timestamp",
    "TIMESTAMP_S": "timestamp", "TIMESTAMP_US": "timestamp",
    "TIMESTAMPTZ": "timestamp", "TIMESTAMP WITH TIME ZONE": "timestamp",
    "TIME": "time", "TIMETZ": "time",
    "BOOLEAN": "bool", "BOOL": "bool", "LOGICAL": "bool",
    "BLOB": "blob", "BYTEA": "blob", "UUID": "uuid", "JSON": "json",
    "INTERVAL": "interval",
}

# 讀得動的實檔格式。xlsx 走 DuckDB excel 擴充，載不起來就降級
READABLE_SUFFIXES = {".parquet", ".csv", ".tsv", ".txt", ".xlsx", ".xlsm"}

MAX_ENUM_SCAN = 5000     # 單欄相異值掃描上限，超過視為「這欄不該宣告成 enum」
SAMPLE_SHOW = 8          # 明細最多列幾個值


def type_family(dtype: str) -> str:
    """把 DECIMAL(18,4)、TIMESTAMP_NS、VARCHAR[] 之類壓成型別族。"""
    t = (dtype or "").strip().upper()
    if t.endswith("[]") or t.startswith(("LIST", "STRUCT", "MAP", "UNION", "ARRAY")):
        return "nested"
    t = re.sub(r"\(.*\)$", "", t).strip()
    return _TYPE_FAMILY.get(t, t.lower() or "unknown")


# ══ 資料結構 ════════════════════════════════════════════════════════════
@dataclass
class ActualTable:
    """一張實檔對應的表。"""
    name: str
    path: Path
    expr: str                                  # DuckDB 可讀的來源運算式
    columns: dict[str, str] = field(default_factory=dict)   # 欄名 → DuckDB 型別
    n_rows: int = 0


# ══ 契約自身健檢 ════════════════════════════════════════════════════════
def check_contract_shape(c: dict[str, Any], source: str, path: Path) -> None:
    """契約自身的健檢。契約寫錯 = 放行機制失效，全部從嚴（02 §十）。"""
    for k in REQUIRED_KEYS:
        if k not in c or c[k] in (None, "", [], {}):
            err(f"契約缺必填鍵 `{k}`",
                f"02 §十 五個必填鍵：{'/'.join(REQUIRED_KEYS)}。補進 {path.name}")

    declared = str(c.get("source", "")).strip()
    if declared and declared != source:
        err(f"契約 source `{declared}` 與檔名 `{path.stem}` 不一致",
            "02 §十：source 必須與 contracts/ 檔名、_source_file、"
            "ingest_watermark.source 同字串。改成一致，不要兩邊各改一半")

    enc = str(c.get("encoding", "")).strip()
    if enc:
        try:
            "".encode(enc)
        except LookupError:
            err(f"encoding `{enc}` 不是 Python 認得的編碼名",
                "台灣常見值：utf-8 / big5 / cp950 / windows-950-2000。"
                "不准留空靠猜（03 W1）")

    tz = str(c.get("source_tz", "")).strip()
    if tz:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(tz)
        except Exception:                          # noqa: BLE001
            err(f"source_tz `{tz}` 不是有效的 IANA 時區",
                "填 Asia/Taipei 這種格式。無宣告時區的 TIMESTAMP 欄不准進 staging（02 §四）")

    _check_columns_shape(c.get("columns"), path)
    _check_renames_shape(c.get("renames"), c.get("columns"))
    _check_sentinels_shape(c.get("sentinels"))
    _check_enum_shape(c.get("enum_domains"))
    _check_overrides_shape(c.get("quality_overrides"))


def _check_columns_shape(cols: Any, path: Path) -> None:
    if not isinstance(cols, list):
        err("契約 columns 不是 list", f"02 §十：columns 是 list of map。見 {path.name}")
        return

    seen: set[tuple[str | None, str]] = set()
    for i, e in enumerate(cols):
        if not isinstance(e, dict) or "name" not in e:
            err(f"columns[{i}] 不是含 name 的 map", "每欄五鍵：name/dtype/unit/nullable/practical_use")
            continue
        name = str(e["name"])
        tbl = e.get("table")
        key = (str(tbl) if tbl else None, name)
        if key in seen:
            err(f"columns 重複宣告 `{name}`" + (f"（table: {tbl}）" if tbl else ""),
                "同一欄只能有一筆宣告，否則後面那筆會靜默覆蓋前面")
        seen.add(key)

        stray = [k for k in e if k not in COLUMN_KEYS]
        if stray:
            err(f"欄位 `{name}` 的宣告多了不認得的鍵：{'、'.join(map(str, stray))}",
                "多半是 YAML flow mapping 的逗號陷阱 —— `dtype: DECIMAL(18,4)` 沒加引號時，"
                "`{}` 裡的逗號會把它拆成 `dtype: DECIMAL(18` 加一個叫 `4)` 的空鍵，"
                "而 YAML 不會報錯。dtype 帶括號一律寫成 dtype: 'DECIMAL(18,4)'。"
                f"合法鍵只有 {'/'.join(sorted(COLUMN_KEYS))}")

        dtype = str(e.get("dtype", "")).strip()
        unit = str(e.get("unit", "")).strip()
        use = str(e.get("practical_use", "")).strip()

        if not dtype:
            err(f"欄位 `{name}` 沒宣告 dtype", "02 §十：dtype 必填。金額一律 DECIMAL(18,4)")
        if not unit:
            err(f"欄位 `{name}` 沒宣告 unit",
                "02 §十：unit 必填，率欄位一律 ratio。無單位就填 '—'，不准留空")
        elif unit not in UNIT_VOCAB and not is_currency(unit):
            warn(f"欄位 `{name}` 的 unit `{unit}` 不在值域內",
                 "02 §十 值域：ratio / percent / <三碼幣別> / days / count / '—'。"
                 "自訂單位下游沒人看得懂，會在 19 的圖表註腳原樣印出去")
        if "nullable" not in e:
            err(f"欄位 `{name}` 沒宣告 nullable", "02 §十：nullable 必填，填 true 或 false")
        elif not isinstance(e["nullable"], bool):
            err(f"欄位 `{name}` 的 nullable 是 `{e['nullable']}` 不是布林",
                "YAML 的 'false' 加引號會變字串。拿掉引號")
        if not use:
            err(f"欄位 `{name}` 沒宣告 practical_use",
                "04 §二：填不出來代表這欄還沒被想清楚，不准留空")
        elif use not in PRACTICAL_USES:
            err(f"欄位 `{name}` 的 practical_use `{use}` 不是七標籤之一",
                f"只能是 {'/'.join(sorted(PRACTICAL_USES))}")

        # 02 §十：金額一律 DECIMAL(18,4)，禁止 DOUBLE/FLOAT
        if is_currency(unit) and type_family(dtype) == "float":
            err(f"金額欄 `{name}` 宣告成 {dtype}",
                "02 §十 明文禁止 DOUBLE/FLOAT 存金額 —— 二進位浮點加總會漂移，"
                "對帳永遠差幾分錢。改 DECIMAL(18,4)")
        if use == "measure" and unit in ("—", "-"):
            warn(f"measure 欄 `{name}` 的 unit 是 '—'",
                 "度量欄要宣告單位與幣別（04 §二）。沒單位的數字到了 14 決策轉譯"
                 "就變成「多 3.2」而沒人知道是 3.2 元還是 3.2%")
        # 18-E2：分群輸入白名單只能是行為指標
        if use == "segment_input":
            info(f"`{name}` 標為 segment_input —— 18-E2：只能是行為指標"
                 f"（R/F/M/RFM Score/CAI/CRI/因素分數/LN_F/LN_M），人口統計變數不准進分群")


def _check_renames_shape(rn: Any, cols: Any) -> None:
    if rn is None:
        return
    if not isinstance(rn, dict):
        err("契約 renames 不是 map", "02 §十：renames 是 map `舊欄名: 新欄名`")
        return
    declared = {str(e.get("name")) for e in (cols or []) if isinstance(e, dict)}
    for old, new in rn.items():
        old_s, new_s = str(old), str(new)
        if old_s == new_s:
            err(f"renames 有自我改名 `{old_s}` → `{new_s}`",
                "刪掉這一筆。它會讓 staging 的 COALESCE 變成同一欄自己 coalesce 自己")
        if declared and new_s not in declared:
            err(f"renames 的新名 `{new_s}` 不在 columns 裡",
                f"改名後的欄位也要有契約。把 `{new_s}` 加進 columns:")
        if new_s in rn:
            warn(f"renames 有鏈式改名 `{old_s}` → `{new_s}` → `{rn[new_s]}`",
                 "staging 的 COALESCE 要把整條鏈串起來，漏一段就是半欄 NULL（03 W5）")


def _check_sentinels_shape(sn: Any) -> None:
    if sn is None:
        return
    if not isinstance(sn, list):
        err("契約 sentinels 不是 list", "02 §十：sentinels 是 list of map")
        return
    for i, e in enumerate(sn):
        if not isinstance(e, dict):
            err(f"sentinels[{i}] 不是 map", "每項要有 column / value / action / reason")
            continue
        if "column" not in e or "value" not in e:
            err(f"sentinels[{i}] 缺 column 或 value", "兩個都是必填，不然不知道要處理誰")
        act = str(e.get("action", "")).strip()
        if act not in SENTINEL_ACTIONS:
            err(f"sentinels[{i}]（{e.get('column')}={e.get('value')}）的 action 是 `{act}`",
                f"只能是 {'/'.join(sorted(SENTINEL_ACTIONS))}。"
                f"寫錯等於哨兵沒被處理，而 04 Q2 實測平均間隔會差 18.5 倍")
        if not str(e.get("reason", "")).strip():
            warn(f"sentinels[{i}]（{e.get('column')}={e.get('value')}）沒寫 reason",
                 "半年後沒人記得為什麼 9999 要換成 NULL。補一句話")


def _check_enum_shape(ed: Any) -> None:
    if ed is None:
        return
    if not isinstance(ed, dict):
        err("契約 enum_domains 不是 map", "寫法：`欄名: [合法值…]` 或 `欄名: {values: [...]}`")
        return
    for col, spec in ed.items():
        vals, on_unknown = _enum_spec(spec)
        if vals is None:
            err(f"enum_domains `{col}` 沒有合法值清單",
                "寫成 `欄名: [值1, 值2]` 或 `欄名: {values: [值1, 值2]}`")
        elif not vals:
            err(f"enum_domains `{col}` 的合法值清單是空的",
                "空清單代表「所有值都非法」，實檔一定全紅。刪掉這一條或補上值")
        if on_unknown not in ON_UNKNOWN:
            err(f"enum_domains `{col}` 的 on_unknown 是 `{on_unknown}`",
                f"只能是 {'/'.join(sorted(ON_UNKNOWN))}，預設 error")


def _enum_spec(spec: Any) -> tuple[list[str] | None, str]:
    """把兩種寫法收斂成 (合法值清單, on_unknown)。"""
    if isinstance(spec, list):
        return [str(v) for v in spec], "error"
    if isinstance(spec, dict):
        vals = spec.get("values")
        vals = [str(v) for v in vals] if isinstance(vals, list) else None
        return vals, str(spec.get("on_unknown", "error")).strip()
    return None, "error"


def _enum_table(spec: Any) -> str | None:
    if isinstance(spec, dict) and spec.get("table"):
        return str(spec["table"])
    return None


def _check_overrides_shape(qo: Any) -> None:
    if qo is None:
        return
    if not isinstance(qo, list):
        err("契約 quality_overrides 不是 list", "02 §十：list of map")
        return
    for i, e in enumerate(qo):
        if not isinstance(e, dict):
            err(f"quality_overrides[{i}] 不是 map", f"五鍵：{'/'.join(OVERRIDE_KEYS)}")
            continue
        missing = [k for k in OVERRIDE_KEYS if not str(e.get(k, "")).strip()]
        if missing:
            err(f"quality_overrides[{i}]（rule={e.get('rule')}）缺 {'、'.join(missing)}",
                "02 §十：這是 exit code 1 的唯一解除途徑。少一個鍵等於"
                "有人默默把紅燈關掉、而且查不到是誰關的")
        rule = str(e.get("rule", "")).strip()
        if rule and rule not in QUALITY_RULES:
            err(f"quality_overrides[{i}] 的 rule `{rule}` 不是 Q1–Q16",
                "04 §四 的規則編號。打錯的話這條豁免永遠不會生效，而且不會有人發現")
        d = e.get("decided_on")
        if d is not None and not isinstance(d, (date, datetime)):
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(d)):
                warn(f"quality_overrides[{i}] 的 decided_on `{d}` 不是 YYYY-MM-DD",
                     "決策日期要能排序，才知道哪個決定比較新")


# ══ 實檔盤點 ════════════════════════════════════════════════════════════
def table_name_of(path: Path, source: str) -> str:
    """檔名 → 表名。ntu_creditcard__transactions.parquet → transactions"""
    stem = path.stem
    for pre in (f"{source}__", f"{source}_", "raw_"):
        if stem.lower().startswith(pre.lower()):
            return stem[len(pre):]
    return stem


def source_expr(path: Path, encoding: str) -> str | None:
    """組出 DuckDB 讀得動的來源運算式。raw 一律當 VARCHAR 讀（02 §3.1）。"""
    p = path.as_posix().replace("'", "''")
    ext = path.suffix.lower()
    if ext == ".parquet":
        return f"read_parquet('{p}')"
    if ext in (".csv", ".tsv", ".txt"):
        delim = "\\t" if ext == ".tsv" else ","
        return (f"read_csv('{p}', header = true, delim = '{delim}', "
                f"encoding = {ql(encoding or 'utf-8')}, sample_size = -1, "
                f"all_varchar = true)")
    if ext in (".xlsx", ".xlsm"):
        return f"read_xlsx('{p}', all_varchar = true)"
    return None


def discover_files(project_paths: Any, source: str,
                   explicit: list[Path]) -> list[Path]:
    """找出這個來源的實檔。--data 優先；否則掃 原始資料/。"""
    if explicit:
        return explicit
    raw = project_paths.raw
    if not raw.exists():
        return []
    hits: list[Path] = []
    # 慣例一：原始資料/<source>/*；慣例二：原始資料/<source>__*.parquet
    for base in (raw / source, raw):
        if not base.exists():
            continue
        for p in sorted(base.iterdir()):
            if not p.is_file() or p.suffix.lower() not in READABLE_SUFFIXES:
                continue
            if base == raw and not p.stem.lower().startswith(source.lower()):
                continue
            hits.append(p)
        if hits:
            break
    return hits


def load_actual(con: Any, files: list[Path], source: str,
                encoding: str) -> dict[str, ActualTable]:
    """讀每個實檔的欄位清單與列數。讀不動的降級成 warning，不擋。"""
    out: dict[str, ActualTable] = {}
    for f in files:
        expr = source_expr(f, encoding)
        if expr is None:
            warn(f"實檔 `{f.name}` 的格式不支援比對",
                 "先用 profile_dataset.py 串流轉成 parquet 再比對。"
                 "大 xlsx 直接 read_excel 峰值可破 8–10 GB（04 §一 ①）")
            continue
        name = table_name_of(f, source)
        try:
            rows = con.execute(f"DESCRIBE SELECT * FROM {expr}").fetchall()
            n = con.execute(f"SELECT count(*) FROM {expr}").fetchone()[0]
        except Exception as e:                     # noqa: BLE001
            warn(f"實檔 `{f.name}` 讀不起來（{type(e).__name__}: {e}）",
                 "xlsx 需要 DuckDB excel 擴充（首次載入要網路）；"
                 "csv 亂碼多半是 encoding 宣告錯（03 W1）。轉成 parquet 最保險")
            continue
        if name in out:
            warn(f"表名 `{name}` 對應到兩個實檔（{out[name].path.name}、{f.name}）",
                 "檔名去掉來源前綴後撞名，比對會只認前一個。改檔名或用 --data 指定")
            continue
        out[name] = ActualTable(name=name, path=f, expr=expr,
                                columns={r[0]: r[1] for r in rows}, n_rows=int(n))
    return out


# ══ 比對本體 ════════════════════════════════════════════════════════════
def _find_table(tables: dict[str, ActualTable], want: str) -> ActualTable | None:
    """契約宣告的表名 → 實檔。

    比對順序：完全相同 → 不分大小寫（Windows 檔名大小寫不敏感，03 §命名）
    → `__` 之後的尾段（`ntu_creditcard__step5_cai` 對得上契約的 `step5_cai`）。
    尾段比對只在唯一命中時才算數，否則寧可判定找不到 —— 猜錯表比找不到表更難查。
    """
    if want in tables:
        return tables[want]
    low = want.lower()
    for k, v in tables.items():
        if k.lower() == low:
            return v
    tail = [v for k, v in tables.items() if k.lower().split("__")[-1] == low]
    return tail[0] if len(tail) == 1 else None


def declared_tables(c: dict[str, Any]) -> set[str]:
    """契約裡出現過的所有表名（grain 的鍵 + columns[].table）。"""
    out: set[str] = set()
    g = c.get("grain")
    if isinstance(g, dict):
        out |= {str(k) for k in g}
    for e in c.get("columns") or []:
        if isinstance(e, dict) and e.get("table"):
            out.add(str(e["table"]))
    for spec in (c.get("enum_domains") or {}).values():
        t = _enum_table(spec)
        if t:
            out.add(t)
    return out


def check_table_mapping(c: dict[str, Any], tables: dict[str, ActualTable]) -> bool:
    """契約宣告的表名對不上任何實檔 → 這不是「跳過」，是整份比對沒發生。"""
    want = declared_tables(c)
    if not want:
        return True
    matched = {t for t in want if _find_table(tables, t) is not None}
    if matched:
        for t in sorted(want - matched):
            info(f"契約宣告的表 `{t}` 不在本次比對範圍（沒有對應實檔），其欄位／grain 跳過")
        return True
    err(f"契約宣告的表 {'、'.join(sorted(want))} 沒有一個對得上實檔 "
        f"{'、'.join(sorted(tables))}",
        "表名是從檔名推導的：去掉 `<source>__` 前綴後的部分。"
        "對不上就等於整份契約一條都沒比到，比沒跑還危險。"
        "把檔名改成 <source>__<表名>.parquet，或把契約的表名改成實際檔名")
    return False


def compare_columns(c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """04 §一 步驟②：契約有實檔沒有 → error；實檔有契約沒有 → error。"""
    entries = [e for e in c.get("columns") or [] if isinstance(e, dict) and "name" in e]
    renames: dict[str, str] = {str(k): str(v) for k, v in (c.get("renames") or {}).items()}

    # ---- 方向一：契約有、實檔沒有 ----
    missing: list[str] = []
    for e in entries:
        name = str(e["name"])
        tbl = str(e["table"]) if e.get("table") else None

        if tbl:
            at = _find_table(tables, tbl)
            if at is None:
                continue          # 表整張不在範圍，check_table_mapping 已統一交代過
            present = name in at.columns
            where = f"（table: {at.name}）"
        else:
            present = any(name in t.columns for t in tables.values())
            where = ""

        if present:
            continue
        # 舊名還在 → staging 用 COALESCE 接得住，降成 warning
        olds = [o for o, n in renames.items()
                if n == name and any(o in t.columns for t in tables.values())]
        if olds:
            warn(f"契約欄位 `{name}`{where} 實檔沒有，但舊名 `{'、'.join(olds)}` 還在",
                 "上游還沒完成改名。staging 一律 COALESCE(新名, 舊名) AS 新名 接住（03 W5）")
        else:
            missing.append(f"{name}{where}")

    if missing:
        err(f"契約有、實檔沒有：{len(missing)} 欄",
            "上游把欄位拿掉或改名了。確認是哪一種："
            "改名 → 加進 renames: 舊名 → 新名（append-only，不刪舊鍵）；"
            "真的下架 → 把該欄的 practical_use 改成 helper 並在 note 註明停用日")
        for m in missing[:20]:
            detail(errors, m)
        if len(missing) > 20:
            detail(errors, f"…另有 {len(missing) - 20} 欄")

    # ---- 方向二：實檔有、契約沒有 ----
    by_table: dict[str, set[str]] = {}
    anywhere: set[str] = set()
    for e in entries:
        name = str(e["name"])
        if e.get("table"):
            at = _find_table(tables, str(e["table"]))
            key = (at.name if at else str(e["table"])).lower()
            by_table.setdefault(key, set()).add(name)
        else:
            anywhere.add(name)

    extra: list[str] = []
    for at in tables.values():
        declared = by_table.get(at.name.lower(), set()) | anywhere
        for col in at.columns:
            if col in declared:
                continue
            if col in renames:
                info(f"`{at.name}.{col}` 契約未直接宣告，但 renames 登錄了 "
                     f"`{col}` → `{renames[col]}`，視為已涵蓋")
                continue
            extra.append(f"{at.name}.{col}  ({at.columns[col]})")

    if extra:
        err(f"實檔有、契約沒有：{len(extra)} 欄",
            "**請加進契約或加進 renames** —— 若這是既有欄位改名，寫 renames: 舊名 → 新名"
            "（append-only，不准刪舊鍵）；若是上游真的新增的欄位，加進 columns: 並補齊"
            "dtype/unit/nullable/practical_use 四個鍵。"
            "放著不管的下場是 union_by_name 靜默拆欄、各半 NULL（03 W5、gap D1）")
        for x in extra[:20]:
            detail(errors, x)
        if len(extra) > 20:
            detail(errors, f"…另有 {len(extra) - 20} 欄")


def compare_types(c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """型別比對。分級理由見檔頭「此處為實作判斷」。"""
    for e in c.get("columns") or []:
        if not isinstance(e, dict) or "name" not in e:
            continue
        name = str(e["name"])
        want = str(e.get("dtype", "")).strip()
        unit = str(e.get("unit", "")).strip()
        if not want:
            continue
        tbl = str(e["table"]) if e.get("table") else None
        targets = ([_find_table(tables, tbl)] if tbl
                   else [t for t in tables.values() if name in t.columns])
        for at in targets:
            if at is None or name not in at.columns:
                continue
            got = at.columns[name]
            fw, fg = type_family(want), type_family(got)
            if fw == fg:
                if fw == "decimal" and want.upper().replace(" ", "") != got.upper().replace(" ", ""):
                    info(f"`{at.name}.{name}` 精度不同：契約 {want}、實檔 {got}（族相同，cast 安全）")
                continue

            tag = f"`{at.name}.{name}` 契約 {want}、實檔 {got}"
            if is_currency(unit) and fg == "float":
                err(f"金額欄 {tag}",
                    "02 §十 禁止 DOUBLE/FLOAT 存金額。載入時就 CAST 成 DECIMAL(18,4)，"
                    "不要等到 mart 才轉 —— 浮點誤差在聚合階段就已經產生")
            elif fg == "str":
                info(f"{tag} —— raw 一律存 VARCHAR 是規約（02 §3.1），型別轉換延到 staging。"
                     f"staging 必須跑 04 Q1：cast 後 NULL 數 ≠ cast 前空值數即 error")
            elif {fw, fg} == {"date", "timestamp"}:
                warn(f"{tag}",
                     f"日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；"
                     f"轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz "
                     f"`{c.get('source_tz')}` 先把時區換算完（02 §四）")
            elif {fw, fg} == {"int", "decimal"}:
                info(f"{tag} —— 整數轉 DECIMAL 無損，可放行")
            elif fw == "decimal" and fg == "float":
                warn(f"{tag}",
                     "實檔是浮點但契約要 DECIMAL。載入時 CAST，並比對總和差異 —— "
                     "先加總再轉換與先轉換再加總的結果不同")
            else:
                warn(f"{tag}",
                     "型別族不同。確認是上游換了型別還是契約寫錯；"
                     "契約寫錯就改契約，上游換型別就要評估下游計算會不會靜默改變")


def check_nullable(con: Any, c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """nullable: false 的欄位實際含 NULL → error。"""
    todo: dict[str, list[str]] = {}
    for e in c.get("columns") or []:
        if not isinstance(e, dict) or e.get("nullable") is not False:
            continue
        name = str(e.get("name", ""))
        tbl = str(e["table"]) if e.get("table") else None
        targets = ([_find_table(tables, tbl)] if tbl
                   else [t for t in tables.values() if name in t.columns])
        for at in targets:
            if at is not None and name in at.columns:
                todo.setdefault(at.name, []).append(name)

    for tname, cols in todo.items():
        at = tables[tname]
        if at.n_rows == 0:
            continue
        sel = ", ".join(
            f"count(*) FILTER (WHERE {qi(col)} IS NULL) AS c{i}"
            for i, col in enumerate(cols)
        )
        row = con.execute(f"SELECT {sel} FROM {at.expr}").fetchone()
        for i, col in enumerate(cols):
            n = int(row[i])
            if n:
                rate = n / at.n_rows
                err(f"`{tname}.{col}` 契約宣告 nullable: false，實際有 "
                    f"{n:,} 個 NULL（{rate:.2%}）",
                    "兩條路：確定該欄本來就可能空 → 契約改成 nullable: true 並在下游"
                    "明寫補值或排除；不該空 → 這是上游或載入邏輯壞了，回頭查"
                    "（NULL 在 JOIN 鍵上會靜默掉列，在 measure 上會讓 avg 的分母縮水）")


def check_grain(con: Any, c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """grain 欄位存在性 + 唯一性（04 §三、Q6）。"""
    grain = c.get("grain")
    if isinstance(grain, list):
        if len(tables) == 1:
            grain = {next(iter(tables)): grain}
        else:
            err(f"契約 grain 是單一 list，但本次有 {len(tables)} 張表",
                "多表來源的 grain 要寫成 `表名: [欄位…]`。"
                "checks/<table>__grain_unique.sql 直接讀它（04 §三）")
            return
    if not isinstance(grain, dict):
        err(f"契約 grain 型別不對（{type(grain).__name__}）",
            "寫成 `表名: [欄位…]`，或單表來源寫成一個 list")
        return

    for tname, cols in grain.items():
        at = _find_table(tables, str(tname))
        if at is None:
            continue          # check_table_mapping 已統一交代過
        if not isinstance(cols, list) or not cols:
            err(f"`{tname}` 的 grain 不是非空 list",
                "找不到唯一鍵時要明寫「本表無主鍵」並列出最接近的複合鍵與重複率（04 §一 ④），"
                "不是留空")
            continue
        cols = [str(x) for x in cols]
        absent = [x for x in cols if x not in at.columns]
        if absent:
            err(f"`{tname}` 的 grain 欄位 {'、'.join(absent)} 在實檔不存在",
                "grain 是所有下游去重與 JOIN 的地基。先修欄名（可能是改名，"
                "去 renames 登錄），再重跑")
            continue
        if at.n_rows == 0:
            warn(f"`{tname}` 是空表（0 列）", "grain 唯一性無從驗證。確認上游是不是抓空了")
            continue

        key = ", ".join(qi(x) for x in cols)
        dup = con.execute(
            f"SELECT count(*), coalesce(sum(n), 0) FROM ("
            f"  SELECT {key}, count(*) AS n FROM {at.expr} "
            f"  GROUP BY {key} HAVING count(*) > 1)"
        ).fetchone()
        n_groups, n_rows_dup = int(dup[0]), int(dup[1])
        if n_groups:
            err(f"`{tname}` 的 grain ({', '.join(cols)}) 不唯一："
                f"{n_groups:,} 組重複、涉及 {n_rows_dup:,} 列（共 {at.n_rows:,} 列）",
                "04 Q6。**只有「所有欄位皆同」才算真重複** —— 同卡同日同金額不是重複，"
                "課程資料集有 323 組是正常的重複刷（04 §三）。先確認粒度判斷對不對："
                "以為是「一筆交易」其實是「一筆交易的一個品項」是最常見的情況")
            top = con.execute(
                f"SELECT {key}, count(*) AS n FROM {at.expr} "
                f"GROUP BY {key} HAVING count(*) > 1 ORDER BY n DESC LIMIT 5"
            ).fetchall()
            for r in top:
                detail(errors, f"{tname}: " + ", ".join(str(v) for v in r[:-1]) + f" ×{r[-1]}")
        else:
            info(f"`{tname}` grain ({', '.join(cols)}) 唯一，{at.n_rows:,} 列")


def check_enum_domains(con: Any, c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """類別欄合法值。未知值預設 error（本 skill 擴充）。"""
    ed = c.get("enum_domains")
    if not isinstance(ed, dict):
        return
    sentinel_vals = _sentinel_values_by_column(c)

    for col, spec in ed.items():
        col = str(col)
        allowed, on_unknown = _enum_spec(spec)
        if not allowed:
            continue
        want_tbl = _enum_table(spec)
        if want_tbl:
            at = _find_table(tables, want_tbl)
            targets = [at] if at else []
        else:
            targets = [t for t in tables.values() if col in t.columns]
            if not targets:
                err(f"enum_domains 宣告的欄位 `{col}` 在任何實檔都不存在",
                    "欄名改了、或這條 enum 是從別的來源複製過來忘了改。"
                    "修欄名（或加 table: 指明是哪張表）—— 沒對到欄位的值域宣告"
                    "會讓人以為這欄已經被守住了")
                continue

        for at in targets:
            if col not in at.columns:
                err(f"enum_domains 宣告的欄位 `{at.name}.{col}` 在實檔不存在",
                    "欄名可能改了。去 renames 登錄，或把這條 enum 一起改名")
                continue
            rows = con.execute(
                f"SELECT CAST({qi(col)} AS VARCHAR) AS v, count(*) AS n "
                f"FROM {at.expr} WHERE {qi(col)} IS NOT NULL "
                f"GROUP BY 1 ORDER BY n DESC LIMIT {MAX_ENUM_SCAN + 1}"
            ).fetchall()
            if len(rows) > MAX_ENUM_SCAN:
                warn(f"`{at.name}.{col}` 相異值超過 {MAX_ENUM_SCAN:,}",
                     "這欄不該宣告成 enum。改用 dim 表對照，或標成高基數類別欄"
                     "（04 §4.3 info 桶）")
                continue

            allow_set = set(allowed) | {str(v) for v in sentinel_vals.get(col, set())}
            unknown = [(v, n) for v, n in rows if v not in allow_set]
            unseen = [v for v in allowed if v not in {r[0] for r in rows}]

            if unknown:
                total = sum(n for _, n in unknown)
                fact = (f"`{at.name}.{col}` 出現 {len(unknown)} 個契約沒宣告的值"
                        f"（合計 {total:,} 列，占 {total / max(at.n_rows, 1):.2%}）")
                todo = ("上游多了一個分類。groupby 會多一列、對照表會漏接、卡方的期望次數"
                        "被稀釋，而全程零報錯。確認是新分類 → 加進 enum_domains 的 values "
                        "並補上它在指標口徑裡的歸屬（18-G10）；是髒值 → 進 sentinels 宣告處理方式")
                if on_unknown == "warn":
                    warn(fact, todo)
                    bucket = warnings
                else:
                    err(fact, todo)
                    bucket = errors
                for v, n in unknown[:SAMPLE_SHOW]:
                    detail(bucket, f"{v!r} ×{n:,}")
                if len(unknown) > SAMPLE_SHOW:
                    detail(bucket, f"…另有 {len(unknown) - SAMPLE_SHOW} 個")
            if not unknown:
                info(f"`{at.name}.{col}` 值域相符：{len(rows)}/{len(allowed)} 個宣告值出現，"
                     f"無未宣告的值")
            if unseen:
                warn(f"`{at.name}.{col}` 契約宣告的 {len(unseen)} 個合法值這次一筆都沒出現",
                     f"可能是上游停用了分類、也可能是這批資料被過濾掉了。"
                     f"確認後再決定要不要保留：{'、'.join(map(repr, unseen[:SAMPLE_SHOW]))}")


def _sentinel_values_by_column(c: dict[str, Any]) -> dict[str, set[Any]]:
    out: dict[str, set[Any]] = {}
    for e in c.get("sentinels") or []:
        if isinstance(e, dict) and "column" in e and "value" in e:
            out.setdefault(str(e["column"]), set()).add(e["value"])
    return out


def check_sentinels(con: Any, c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """哨兵值：欄位要在、宣告要生效。實際偵測未宣告的哨兵是 04 Q2 的工作。"""
    for e in c.get("sentinels") or []:
        if not isinstance(e, dict) or "column" not in e or "value" not in e:
            continue
        col, val = str(e["column"]), e["value"]
        act = str(e.get("action", "")).strip()
        want_tbl = str(e["table"]) if e.get("table") else None

        if want_tbl:
            at = _find_table(tables, want_tbl)
            if at is None:
                info(f"sentinel `{want_tbl}.{col} = {val}` 的表不在比對範圍，跳過")
                continue
            targets = [at]
        else:
            targets = [t for t in tables.values() if col in t.columns]
            if not targets:
                err(f"sentinel 宣告的欄位 `{col}` 在任何實檔都不存在",
                    "欄名改了或這條契約過期。修欄名（或加 table: 指明是哪張表），"
                    "不要放著 —— 沒生效的哨兵宣告會讓人以為已經處理過了")
                continue

        for at in targets:
            if col not in at.columns:
                err(f"sentinel 宣告的欄位 `{at.name}.{col}` 在實檔不存在",
                    "同上：修欄名或加進 renames")
                continue
            n = int(con.execute(
                f"SELECT count(*) FROM {at.expr} WHERE "
                f"CAST({qi(col)} AS VARCHAR) = {ql(val)} "
                f"OR TRY_CAST({qi(col)} AS DOUBLE) = TRY_CAST({ql(val)} AS DOUBLE)"
            ).fetchone()[0])
            if n == 0:
                warn(f"sentinel `{at.name}.{col} = {val}` 這批資料一筆都沒中",
                     "上游可能已經修好了，也可能是欄位語意變了。"
                     "契約 append-only 不用刪，但要確認 action 還適用")
            else:
                info(f"sentinel `{at.name}.{col} = {val}` 命中 {n:,} 列，"
                     f"action = {act}（{n / max(at.n_rows, 1):.2%}）")


def check_units(con: Any, c: dict[str, Any], tables: dict[str, ActualTable]) -> None:
    """率欄位的 ratio / percent 口徑抽驗 —— 抓的是經典的 ×100 錯位。"""
    for e in c.get("columns") or []:
        if not isinstance(e, dict):
            continue
        unit = str(e.get("unit", "")).strip()
        if unit not in ("ratio", "percent"):
            continue
        name = str(e.get("name", ""))
        tbl = str(e["table"]) if e.get("table") else None
        targets = ([_find_table(tables, tbl)] if tbl
                   else [t for t in tables.values() if name in t.columns])
        for at in targets:
            if at is None or name not in at.columns or at.n_rows == 0:
                continue
            row = con.execute(
                f"SELECT min(TRY_CAST({qi(name)} AS DOUBLE)), "
                f"max(TRY_CAST({qi(name)} AS DOUBLE)), "
                f"count(TRY_CAST({qi(name)} AS DOUBLE)) FROM {at.expr}"
            ).fetchone()
            lo, hi, n_num = row[0], row[1], int(row[2])
            if n_num == 0 or lo is None or hi is None:
                warn(f"`{at.name}.{name}` 宣告 unit: {unit} 但沒有一個值轉得成數字",
                     "率欄位卻是文字，多半夾了 '%' 或千分位。"
                     "轉換時先 replace 再 cast，並跑 04 Q1 對照 cast 前後的 NULL 數")
                continue
            span = max(abs(lo), abs(hi))
            if unit == "ratio" and span > 1.5:
                warn(f"`{at.name}.{name}` 宣告 unit: ratio，實際值域 "
                     f"[{lo:.6g}, {hi:.6g}]",
                     "看起來已經是百分點。02 §十 要求率一律存 ratio（0.0235），"
                     "只在呈現層乘 100 —— 兩邊各乘一次就是 100 倍誤差")
            elif unit == "percent" and span <= 1.0:
                warn(f"`{at.name}.{name}` 宣告 unit: percent，實際值域 "
                     f"[{lo:.6g}, {hi:.6g}]",
                     "看起來其實是 ratio。改宣告 unit: ratio，"
                     "或確認上游真的是「0.35 個百分點」這種小數")
            else:
                info(f"`{at.name}.{name}` unit: {unit}，值域 [{lo:.6g}, {hi:.6g}]，口徑一致")
            if unit == "percent":
                info(f"`{at.name}.{name}` 宣告成 percent —— 02 §十 的通則是率一律存 ratio。"
                     f"若非公式本身自帶 ×100（如 17 §4.2 的 CAI），staging 請除以 100")


# ══ append-only 守衛 ════════════════════════════════════════════════════
def snapshot_file(project_paths: Any, source: str) -> Path:
    return project_paths.log / f"contract_snapshot__{source}.json"


def _snapshot_of(c: dict[str, Any]) -> dict[str, Any]:
    grain = c.get("grain")
    if isinstance(grain, list):
        grain = {"__single__": [str(x) for x in grain]}
    elif isinstance(grain, dict):
        grain = {str(k): [str(x) for x in (v or [])] for k, v in grain.items()}
    else:
        grain = {}
    cols = sorted({
        f"{e.get('table', '')}|{e['name']}"
        for e in c.get("columns") or []
        if isinstance(e, dict) and "name" in e
    })
    return {
        "source": str(c.get("source", "")),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "grain": grain,
        "renames_keys": sorted(str(k) for k in (c.get("renames") or {})),
        "columns": cols,
    }


def check_append_only(c: dict[str, Any], snap_path: Path) -> bool:
    """回傳是否可以更新快照。契約只能 append（02 §十 末段）。"""
    now = _snapshot_of(c)
    if not snap_path.exists():
        info(f"首次比對，建立契約快照：{snap_path.name}"
             f"（往後偷改 grain 或刪 renames 舊鍵會被擋下）")
        return True
    try:
        old = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception as e:                         # noqa: BLE001
        warn(f"契約快照讀不起來（{e}）", "刪掉它讓下次重建，append-only 守衛這次不生效")
        return True

    clean = True
    lost = [k for k in old.get("renames_keys", []) if k not in now["renames_keys"]]
    if lost:
        clean = False
        err(f"renames 少了 {len(lost)} 個舊鍵：{'、'.join(lost)}",
            "renames 是 append-only。刪掉舊鍵就回到 union_by_name 靜默拆兩欄各半 NULL 的坑"
            "（03 W5）。把它加回去；欄位真的停用是在 columns 標註，不是刪 renames")

    for tname, cols in (old.get("grain") or {}).items():
        new_cols = now["grain"].get(tname)
        if new_cols is None:
            clean = False
            err(f"grain 少了表 `{tname}`",
                "改 grain 等於讓半年前那份報告重跑不出來（02 §十 末段）。"
                "粒度真的要改就開新 source 代號，不要就地改")
        elif new_cols != cols:
            clean = False
            err(f"grain `{tname}` 從 {cols} 改成 {new_cols}",
                "同上：粒度是所有去重與 JOIN 的地基，就地改會讓歷史結果無法重現。"
                "確定要改 → 開新的 <source> 代號並在 專案記憶/決策紀錄.md 留一筆")

    dropped = [x for x in old.get("columns", []) if x not in now["columns"]]
    if dropped:
        warn(f"columns 少了 {len(dropped)} 筆宣告",
             "契約只能 append。欄位下架的正確做法是把 practical_use 改成 helper "
             "並在 note 註明停用日，不是刪掉整筆 —— 刪了就查不到它曾經存在過")
        for d in dropped[:10]:
            detail(warnings, d.replace("|", " / ") if "|" in d else d)
    return clean


# ══ 報告 ════════════════════════════════════════════════════════════════
def write_contract_report(path: Path, source: str, contract: Path,
                 tables: dict[str, ActualTable], code: int) -> None:
    lines = [
        f"# 欄位契約比對報告 — {source}",
        "",
        f"- 產出時間：{datetime.now().isoformat(timespec='seconds')}",
        f"- 契約檔：`{contract}`",
        f"- 退出碼：{code}（0 通過｜1 有 error 擋住｜2 只有 warning"
        f"｜64 用法錯誤｜70 腳本自身異常；見 00 §八）",
        "",
        "## 比對範圍",
        "",
        "| 表 | 實檔 | 欄數 | 列數 |",
        "|---|---|---:|---:|",
    ]
    for t in tables.values():
        lines.append(f"| {t.name} | `{t.path.name}` | {len(t.columns)} | {t.n_rows:,} |")
    for title, bucket, mark in (("error（擋住）", errors, "⛔"),
                                ("warning（可往下，要進報告的『資料限制』節）", warnings, "⚠"),
                                ("info", infos, "·")):
        lines += ["", f"## {title}", ""]
        if not bucket:
            lines.append("（無）")
        for m in bucket:
            lines.append(f"- {m.strip()}" if m.startswith("    ") else f"{mark} {m}")
    lines += ["", "---", "",
              "> 規格出處：04_資料體檢.md §一 步驟②、§四；02_資料模型規格.md §十",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# ══ 主流程 ══════════════════════════════════════════════════════════════
def run_contract_check(args: argparse.Namespace) -> int:
    p = project_dir(args.project, create=not args.dry_run)

    contract_path = (args.contract if args.contract
                     else p.raw / "contracts" / f"{args.source}.yml")
    if not contract_path.exists():
        print(f"⛔ 找不到契約：{contract_path}")
        print("   — 首次進場沒有契約是正常的，但不能就這樣往下（04 §一 步驟②）。兩條路：")
        print(f"     1) 複製範本改欄名："
              f"cp templates/contracts/example.yml \"{contract_path}\"")
        print("     2) 跑 profile_dataset.py 由步驟③ 的剖析結果生草稿，交包子確認後才算數")
        return EX_ERROR

    # 共用解析（scripts/contract.py）。本檔後續全部以原始 dict 走訪，所以取 .raw；
    # 解析後的 grain / columns / sentinels 也在同一個物件上，之後要收斂可以逐段換過去。
    c = load_contract(contract_path).raw
    source = str(c.get("source") or args.source or contract_path.stem)
    check_contract_shape(c, args.source or contract_path.stem, contract_path)

    files = discover_files(p, args.source or contract_path.stem,
                           [Path(x) for x in (args.data or [])])
    missing_files = [f for f in files if not f.exists()]
    for f in missing_files:
        err(f"指定的實檔不存在：{f}", "檢查路徑；相對路徑是相對於你現在的工作目錄")
    files = [f for f in files if f.exists()]

    if not files:
        print(f"⛔ 找不到來源 `{source}` 的實檔")
        print(f"   — 掃描位置：{p.raw}（檔名要以 `{source}` 開頭，或放在 "
              f"{p.raw / source}/ 底下）")
        print("     也可以直接指定：--data <路徑> --data <路徑>")
        return EX_ERROR

    encoding = str(c.get("encoding") or "utf-8")
    with connect(args.project) as con:
        tables = load_actual(con, files, args.source or contract_path.stem, encoding)
        if not tables:
            print("⛔ 沒有任何實檔讀得起來，無法比對")
            for m in warnings:
                print(f"   {m}")
            return EX_ERROR

        print("=" * 70)
        print("行銷數據分析 Skill — 欄位契約比對（M1 步驟②）")
        print(f"專案：{args.project}｜來源：{source}")
        print(f"契約：{contract_path}")
        print(f"實檔：{len(tables)} 張表")
        for t in tables.values():
            print(f"    · {t.name:<16} {t.path.name}"
                  f"（{len(t.columns)} 欄、{t.n_rows:,} 列）")
        print("=" * 70)

        check_table_mapping(c, tables)
        compare_columns(c, tables)
        compare_types(c, tables)
        check_nullable(con, c, tables)
        check_grain(con, c, tables)
        check_enum_domains(con, c, tables)
        check_sentinels(con, c, tables)
        check_units(con, c, tables)

    snap = snapshot_file(p, source)
    if not args.no_snapshot:
        clean = check_append_only(c, snap)
        if clean and not args.dry_run:
            snap.parent.mkdir(parents=True, exist_ok=True)
            snap.write_text(
                json.dumps(_snapshot_of(c), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # ── 三桶輸出 ──
    if args.verbose and infos:
        print("\n通過與備註")
        print("-" * 70)
        for m in infos:
            print(m if m.startswith("    ") else f"  ✅ {m}")

    if warnings:
        print("\n⚠ 可往下，但這些條目必須進報告的「資料限制」節")
        print("-" * 70)
        for m in warnings:
            print(m if m.startswith("    ") else f"  ⚠ {m}")

    if errors:
        print("\n⛔ 擋住，不准進步驟③")
        print("-" * 70)
        for m in errors:
            print(m if m.startswith("    ") else f"  ⛔ {m}")

    n_err = sum(1 for m in errors if not m.startswith("    "))
    n_warn = sum(1 for m in warnings if not m.startswith("    "))
    n_info = sum(1 for m in infos if not m.startswith("    "))

    print("\n" + "=" * 70)
    if errors:
        code = EX_ERROR
        print(f"結果：{n_err} 個 error、{n_warn} 個 warning、{n_info} 個 info → 擋住")
        print("      契約不符直接擋住，不浪費時間剖析（04 §一 步驟②）。")
        print(f"      解除方式只有一個：在 {contract_path.name} 明確宣告處理方式後重跑。")
    elif warnings:
        code = EX_WARN
        print(f"結果：{n_warn} 個 warning、{n_info} 個 info → 可往下")
        print("      warning 條目要抄進報告的「資料限制」節，不是看過就算。")
    else:
        code = EX_OK
        print(f"結果：契約與實檔一致（{n_info} 項 info）→ 可進步驟③ 逐欄剖析")

    if not args.no_report and not args.dry_run:
        rp = p.log / f"契約比對__{source}.md"
        write_contract_report(rp, source, contract_path, tables, code)
        print(f"\n報告：{rp}")

    return code


def main() -> int:
    ap = GateArgumentParser(
        description="欄位契約比對（M1 步驟②）：contracts/<source>.yml vs 實檔",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("project", help="專案代號")
    ap.add_argument("--source", help="來源代號（= 契約檔名）。省略時用 --contract 的檔名")
    ap.add_argument("--contract", type=Path,
                    help="契約檔路徑。預設 <專案>/原始資料/contracts/<source>.yml")
    ap.add_argument("--data", action="append",
                    help="指定實檔路徑，可重複。省略時掃 <專案>/原始資料/")
    ap.add_argument("--no-snapshot", action="store_true",
                    help="不做 append-only 守衛，也不更新快照")
    ap.add_argument("--no-report", action="store_true", help="不寫報告檔")
    ap.add_argument("--dry-run", action="store_true",
                    help="只比對，不建目錄、不寫報告、不動快照")
    ap.add_argument("--verbose", action="store_true", help="連 info 桶也列出")
    args = ap.parse_args()

    if not args.source and not args.contract:
        ap.error("要嘛給 --source，要嘛給 --contract，兩個都沒有就不知道要比對哪個來源")
    if not args.source:
        args.source = args.contract.stem

    try:
        return run_contract_check(args)
    except ContractError as e:
        # 契約寫壞是「資料側」的問題，不是腳本壞了 → 退出碼 1 而不是 70
        print(f"⛔ {e}")
        return EX_ERROR
    except KeyboardInterrupt:
        print("\n⛔ 使用者中斷")
        return EX_SOFTWARE
    except Exception as e:                         # noqa: BLE001
        print(f"⛔ 比對腳本本身失敗：{type(e).__name__}: {e}")
        print(f"   — 退出碼 {EX_SOFTWARE} 代表腳本壞了，不是資料壞了。"
              f"修腳本，不准手動略過（00 §八、04 §四）")
        import traceback
        traceback.print_exc()
        return EX_SOFTWARE


if __name__ == "__main__":
    raise SystemExit(main())
