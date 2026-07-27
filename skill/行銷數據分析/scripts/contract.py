#!/usr/bin/env python3
"""
資料契約 `原始資料/contracts/<source>.yml` 的**唯一解析實作**（02 §十）。

為什麼要抽出來：
  `check_data_quality.py` 與 `check_schema_contract.py` 各自寫過一份 `load_contract()`
  —— 一份回傳自訂 dataclass、缺檔丟 `FileNotFoundError`，一份回傳 dict、丟自訂
  `ContractError`，讀的卻是同一個檔。契約 schema 一改（例如 `columns[]` 多一個
  `table:` 鍵、`grain` 換寫法）就會兩邊分岔：一支看得懂新契約、另一支看不懂，
  而且**兩支都不會報錯**，只會靜默降級成「沒有契約」的判定路徑。M1 的放行機制
  建立在契約上，契約解析分岔 = 放行機制分岔（00 §七：兩處分岔比兩處都錯更糟）。

  所以契約怎麼讀、YAML 壞掉怎麼報、缺檔怎麼報，全部只在這一支裡寫一次。

提供什麼：
    ContractError            契約本身壞掉（讀不到／YAML 語法錯／最外層不是 mapping）
    qi(name) / qs(value)     DuckDB 識別字與字串常值引號化（原本兩支各寫一份）
    read_contract_yaml(path) 讀成原始 dict —— 給還在用 dict 走訪的呼叫端
    Contract                 解析後的結構（grain / columns / sentinels / overrides）
    load_contract(path)      主入口，回傳 Contract；`.raw` 保留原始 dict

用法：
    from contract import Contract, ContractError, load_contract, qi, qs

    c = load_contract(path)                 # 缺檔 → ContractError
    c = load_contract(None)                 # → 空 Contract（loaded=False）
    c.raw                                    # 原始 dict，未解析的鍵（enum_domains…）從這拿
    c.unit_of("刷卡金額", table="transactions")   # 逐表查；查不到才退回不分表

規格出處：`references/02_資料模型規格.md` §十（契約檔規格與 quality_overrides）、
          `references/04_資料體檢.md` §一 步驟②。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 02 §十：unit 三碼大寫視為 ISO-4217 幣別
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class ContractError(Exception):
    """契約檔本身壞掉（讀不到、YAML 語法錯）。是資料問題不是腳本問題 → 退出碼 1。"""


# ── DuckDB 引號化（兩支腳本原本各寫一份，語意完全相同）─────────────
def qi(name: str) -> str:
    """識別字引號化。中文欄名、含空白的欄名（`Unnamed: 10`）都必須走這裡。"""
    return '"' + str(name).replace('"', '""') + '"'


def qs(value: Any) -> str:
    """字串常值引號化。"""
    return "'" + str(value).replace("'", "''") + "'"


def is_currency(unit: str) -> bool:
    """unit 是不是 ISO-4217 三碼幣別（02 §十）。"""
    return bool(_CURRENCY_RE.match((unit or "").strip()))


# ── 原始 YAML 讀取 ─────────────────────────────────────────────────
def read_contract_yaml(path: Path) -> dict[str, Any]:
    """讀契約成原始 dict。錯誤訊息一律「事實 — 該怎麼辦」兩段式。"""
    path = Path(path)
    if not path.exists():
        raise ContractError(
            f"找不到契約檔：{path} — "
            f"契約住在 <專案>/原始資料/contracts/<source>.yml（03 §1.2）。"
            f"首次進場沒有契約時，先複製 templates/contracts/example.yml 改欄名，"
            f"或跑 profile_dataset.py 由剖析結果生草稿，交包子確認後才算數")
    try:
        import yaml
    except ImportError as e:                      # pragma: no cover
        raise ContractError(
            "PyYAML 未安裝，讀不了契約檔 — pip install pyyaml（requirements.txt 第 1 層）"
        ) from e
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:                        # noqa: BLE001
        raise ContractError(
            f"契約 YAML 解析失敗：{path}（{e}）— "
            f"多半是中文冒號、tab 縮排或引號沒收尾。用 templates/contracts/example.yml 對照"
        ) from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ContractError(
            f"契約最外層不是 mapping：{path} — 檢查第一行是不是多了 '- '")
    return data


# ── 解析後的結構 ───────────────────────────────────────────────────
@dataclass
class Contract:
    """`原始資料/contracts/<source>.yml`，02 §十。缺席時所有欄位為空。"""
    path: Path | None = None
    source: str = ""
    grain: dict[str, list[str]] = field(default_factory=dict)
    columns: dict[str, dict[str, Any]] = field(default_factory=dict)
    sentinels: list[dict[str, Any]] = field(default_factory=list)
    overrides: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    # (表名, 欄名) → 該欄宣告。02 §十 的 columns[] 是跨表聯集清單，同一個欄名在不同表
    # 的角色會不同（客戶ID 在交易檔是 fk、在客戶檔是 subject_key），所以逐表另存一份。
    columns_by_table: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    @property
    def loaded(self) -> bool:
        return self.path is not None

    # ── 逐欄查詢 ──────────────────────────────────────────────
    def spec_of(self, col: str, table: str | None = None) -> dict[str, Any]:
        """查一欄的宣告。給了 table 就先逐表查，查不到才退回不分表的聯集清單。

        退回是刻意的：02 §十 原本的 columns[] 不帶 `table:`，舊契約全部只有欄名。
        """
        if table is not None:
            hit = self.columns_by_table.get((table, col))
            if hit is not None:
                return hit
        return self.columns.get(col, {}) or {}

    def use_of(self, col: str, table: str | None = None) -> str:
        return str(self.spec_of(col, table).get("practical_use", "") or "")

    def unit_of(self, col: str, table: str | None = None) -> str:
        return str(self.spec_of(col, table).get("unit", "") or "")

    def dtype_of(self, col: str, table: str | None = None) -> str:
        return str(self.spec_of(col, table).get("dtype", "") or "")

    def currency_of(self, col: str, table: str | None = None) -> str:
        """該欄契約宣告的幣別；沒宣告或不是 ISO-4217 三碼就回空字串（04 Q16）。"""
        u = self.unit_of(col, table).strip()
        return u if is_currency(u) else ""

    def sentinel_declared(self, col: str, value: Any) -> dict[str, Any] | None:
        for s in self.sentinels:
            if str(s.get("column")) == col and str(s.get("value")) == str(value):
                return s
        return None

    # ── 表名 ──────────────────────────────────────────────────
    def declared_tables(self) -> list[str]:
        """契約提到的所有表名（grain 鍵 + columns[].table）。`*` 是單表簡寫不算表名。"""
        names = {t for t in self.grain if t != "*"}
        names |= {t for (t, _c) in self.columns_by_table}
        return sorted(names)


def load_contract(path: Path | None, *, required: bool = True) -> Contract:
    """主入口。path=None → 空 Contract（呼叫端自行決定要不要抱怨）。

    required=False 時，檔案不存在也回空 Contract 而不是丟 ContractError ——
    給「有就讀、沒有就降級」的呼叫端用。**M1 放行相關的路徑一律用預設的 True**。
    """
    if path is None:
        return Contract()
    path = Path(path)
    if not path.exists() and not required:
        return Contract()

    raw = read_contract_yaml(path)

    grain = raw.get("grain") or {}
    if isinstance(grain, list):                       # 單表契約的簡寫
        grain = {"*": [str(x) for x in grain]}
    grain = {str(k): [str(x) for x in (v or [])] for k, v in grain.items()}

    cols: dict[str, dict[str, Any]] = {}
    by_table: dict[tuple[str, str], dict[str, Any]] = {}
    for item in raw.get("columns") or []:
        if not (isinstance(item, dict) and item.get("name")):
            continue
        name = str(item["name"])
        cols.setdefault(name, item)                   # 同名跨表時保留第一筆，維持舊行為
        tbl = item.get("table")
        if tbl:
            by_table[(str(tbl), name)] = item

    ov: dict[str, list[dict[str, Any]]] = {}
    for item in raw.get("quality_overrides") or []:
        if isinstance(item, dict) and item.get("rule"):
            ov.setdefault(str(item["rule"]).upper(), []).append(item)

    return Contract(path=path, source=str(raw.get("source", "") or ""), grain=grain,
                    columns=cols, sentinels=list(raw.get("sentinels") or []),
                    overrides=ov, raw=raw, columns_by_table=by_table)
