#!/usr/bin/env python3
"""人口統計變數的**單一判定清單** —— 全 skill 共用，不准在各腳本裡各寫一份。

為什麼要獨立一支：

  1. **18-E2 與 07 §3.1 CRI 血緣用的是同一個判定**。前者問「這一欄能不能
     進分群矩陣」，後者問「CRI 的先驗群是不是拿人口變數分的」。清單各寫一份，
     改了一支忘了另一支，防線就會出現只有攻擊者才知道的破洞。

  2. **血緣必須機器可讀**。`build_features.py` 把先驗分群欄位是不是人口變數
     寫進特徵表，`prep_cluster_matrix.py` 讀回來當作交叉檢查的依據 ——
     兩邊叫同一支函式，判定才會一致。

判定規則（中英分開，理由不同）：
  · **中文欄名用子字串比對**。`婚姻狀況`、`年收入級距` 這種帶後綴的欄名，
    用 `(^|_)婚姻($|_)` 這類詞界正規式會漏掉（中文沒有 `_` 詞界）。
  · **英文欄名用詞界正規式**。`age` 若用子字串比對會誤傷 `average_...`、
    `usage_...`；`sex` 會誤傷 `sex...` 以外還有 `unisex`，所以一律要求
    前後是字串端點或 `_`。

新增類別的規矩：改這裡，不要改呼叫端。並在 `references/07_標籤與分群.md`
§3.1 的「明確禁止」那一行補上對應說明，兩邊要對得起來。
"""

from __future__ import annotations

import re
from typing import Sequence

# ── 人口統計變數（07 §3.1「明確禁止」那一行 + 18-E2）──────────
# 每項是 (類別, 中文關鍵詞, 英文正規式)。中文子字串比對、英文詞界比對。
# 順序有意義：先命中先算。`年收地` 是地區不是收入，所以地區排在收入前面。
DEMOGRAPHIC_TERMS: list[tuple[str, tuple[str, ...], re.Pattern[str]]] = [
    ("性別", ("性別", "生理性別"),
     re.compile(r"(^|_)(gender|sex)($|_)")),
    ("年齡", ("年齡", "年紀", "歲數", "生日", "出生日", "出生年"),
     re.compile(r"(^|_)(age|agegroup|age_group|birth|birthday|birthdate|dob)($|_)")),
    ("婚姻", ("婚姻", "已婚", "未婚", "配偶"),
     re.compile(r"(^|_)(marital|marriage|married|spouse)($|_)")),
    ("地區", ("地區", "縣市", "居住地", "戶籍地", "年收地", "住址", "地址", "區域"),
     re.compile(r"(^|_)(region|area|city|district|county|state|province|"
                r"residence|address|geo)($|_)")),
    ("郵遞區號", ("郵遞區號", "郵區"),
     re.compile(r"(^|_)(zip|zipcode|postal|postcode)($|_)")),
    ("教育程度", ("教育程度", "學歷", "教育"),
     re.compile(r"(^|_)(edu|education|degree|schooling)($|_)")),
    ("職業", ("職業", "行業別", "工作性質"),
     re.compile(r"(^|_)(job|occupation|profession|industry)($|_)")),
    ("收入", ("收入", "所得", "薪資", "年薪", "月薪"),
     re.compile(r"(^|_)(income|salary|wage|earnings)($|_)")),
    ("家庭", ("家庭人數", "子女數", "小孩數", "家戶人數", "同住人數"),
     re.compile(r"(^|_)(household|family_size|children|kids|dependents)($|_)")),
    ("族群國籍", ("國籍", "族群", "種族", "母語", "使用語言"),
     re.compile(r"(^|_)(nationality|ethnicity|race|language|native_language)($|_)")),
]

# ── 非人口、但同樣不准進分群矩陣的屬性欄（07 §3.1）──────────
# 卡別／會員等級是**公司給的屬性**不是顧客的行為；M5 標籤是分群的下游產物，
# 拿它當分群輸入是循環推論。這些不算「人口變數」，血緣判定不看它們，
# 但白名單檢查一樣要擋。
NON_BEHAVIORAL_TERMS: list[tuple[str, tuple[str, ...], re.Pattern[str]]] = [
    ("卡別", ("卡別", "卡等", "卡片等級"),
     re.compile(r"(^|_)(card_type|card_grade|cardtype|card_level)($|_)")),
    ("會員等級", ("會員等級", "會員層級", "等級"),
     re.compile(r"(^|_)(member_level|membership|tier|grade)($|_)")),
    ("M5 標籤", ("標籤", "分群標籤", "族群標籤"),
     re.compile(r"(^|_)(label|tag|segment|flag|cluster_id)($|_)")),
]

# 分群輸入的黑名單 = 人口變數 + 其他非行為屬性。18-E2 一律擋下。
CLUSTER_INPUT_BLACKLIST = DEMOGRAPHIC_TERMS + NON_BEHAVIORAL_TERMS


# ── CRI 先驗群的血緣型別（07 §3.1 CRI 列）────────────────────
PRIOR_NONE = "none"                 # 沒有先驗分群層 → CRI 全 N/A
PRIOR_BEHAVIORAL = "behavioral"     # 行為分層（F 三分位、品類廣度…）→ CRI 可進矩陣
PRIOR_DEMOGRAPHIC = "demographic"   # 人口變數 → CRI 不得進矩陣
PRIOR_MIXED = "mixed"               # 有人口也有非人口 → 一樣不得進矩陣
PRIOR_TYPES = (PRIOR_NONE, PRIOR_BEHAVIORAL, PRIOR_DEMOGRAPHIC, PRIOR_MIXED)


def _match(name: str, table: list[tuple[str, tuple[str, ...], re.Pattern[str]]]) -> str | None:
    raw = str(name).strip()
    low = raw.lower()
    for cat, zh_terms, pat in table:
        if any(t in raw for t in zh_terms):
            return cat
        if pat.search(low):
            return cat
    return None


def classify_demographic(name: str) -> str | None:
    """這一欄是不是人口統計變數？是就回傳類別名，不是回傳 None。"""
    return _match(name, DEMOGRAPHIC_TERMS)


def classify_blacklist(name: str) -> str | None:
    """這一欄能不能進分群矩陣？不能就回傳類別名（18-E2）。"""
    return _match(name, CLUSTER_INPUT_BLACKLIST)


def classify_prior_cols(cols: Sequence[str] | None) -> tuple[str, list[str]]:
    """判定 CRI 先驗分群的血緣型別。

    回傳 (型別, 命中人口清單的欄位)。型別取值見 PRIOR_TYPES。

    注意「behavioral」的語意是**沒有命中人口變數清單**，不是「已證明是行為量」——
    清單不可能窮盡所有人口欄名。所以 build_features 除了型別之外還會把
    先驗欄位名一起寫進特徵表，讓 prep_cluster_matrix 能重判、讓人能覆核。
    """
    cols = [str(c).strip() for c in (cols or []) if str(c).strip()]
    if not cols:
        return PRIOR_NONE, []
    demo = [c for c in cols if classify_demographic(c) is not None]
    if not demo:
        return PRIOR_BEHAVIORAL, []
    if len(demo) == len(cols):
        return PRIOR_DEMOGRAPHIC, demo
    return PRIOR_MIXED, demo


def describe_prior_cols(cols: Sequence[str] | None) -> str:
    """給人看的一行說明，例如「性別（性別）、F三分位（非人口）」。"""
    cols = [str(c).strip() for c in (cols or []) if str(c).strip()]
    if not cols:
        return "（無先驗分群欄位）"
    return "、".join(f"{c}（{classify_demographic(c) or '非人口'}）" for c in cols)


if __name__ == "__main__":   # 手動抽驗：python demographic_vars.py 性別 f_三分位
    import sys
    names = sys.argv[1:] or ["性別", "年齡", "婚姻狀況", "年收地", "教育程度",
                             "職業", "年收入級距", "f_tertile", "average_days",
                             "usage_cnt", "m_net_twd"]
    for n in names:
        print(f"{n:<20} 人口={classify_demographic(n) or '-':<8} "
              f"黑名單={classify_blacklist(n) or '-'}")
    print("先驗判定：", classify_prior_cols(names))
