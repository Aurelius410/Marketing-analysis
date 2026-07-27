#!/usr/bin/env python3
"""
產生 `dirty_mini.parquet` 與 `dirty_mini_customers.parquet` —— 檢查器自己的測試素材。

為什麼需要它：
  04 §九 明訂「課程資料集的檢查全綠時**不要當成通過**」。那份基準集實測負值 0 筆、
  整列重複 0 筆、孤兒 0 筆、全形半形混用 0 筆、單一幣別、無 UA 欄，
  **Q1/Q6/Q7/Q8/Q10/Q11/Q12 這七條在它上面永遠不可能變紅**。
  沒有髒樣本，`check_data_quality.py` 就只被測到「不會誤報」，沒被測到「抓得到」。

  這兩份檔案刻意每一種髒法只放少量列，方便肉眼核對筆數：
  期望值寫在下方 EXPECTED，改資料時請一起改。

用法：
    python make_dirty_mini.py            # 寫到本檔所在目錄
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).resolve().parent

# 每一條檢查在這份 fixture 上該抓到幾筆（改資料就要改這裡）
EXPECTED = {
    "Q1  刷卡金額 cast 失敗": 2,
    "Q2  間隔天數 = 9999（＝客戶數 15）": 15,
    "Q4  客戶碼+日序 黏接碰撞": 1,
    "Q5  信用額度 = 0": 1,
    "Q6  交易序號 重複": 2,
    "Q8  currency 為 NULL": 1,
    "Q10 全形英數 / 前後空白": "1 + 1",
    "Q11 實付金額 ≤ 10、會員編號 = TEST": "1 + 1",
    "Q12 UA 命中 bot": 1,
    "Q13 產業分類缺 01/04、X2. 破格": "2 + 1",
    "Q17 實付金額 負值": 1,
    "Q18 交易日期 落在觀察窗外": 2,
    "Q19 客戶ID 孤兒（9999901）": 1,
    "Q20 備註 90% 缺、職業 50% 缺": "18 + 10（兩條都是 error 級）",
    "Q20 currency 5% 缺": "1（warning 級）",
}


def build_fact() -> pd.DataFrame:
    n = 20
    cust = [101, 102, 103, 104, 105, 106, 107, 108,
            109, 110, 111, 112, 113, 114, 9999901]      # 15 個，最後一個是孤兒
    return pd.DataFrame({
        # Q6：交易序號 1 重複兩次 → 19 個相異值、2 列涉入
        "交易序號": [1, 1] + list(range(2, 20)),
        "客戶ID": cust + cust[:5],
        # Q11：一個測試會員號
        "會員編號": ["M%04d" % i for i in range(1, 20)] + ["TEST"],
        # Q18：一筆未來日、一筆 1899（觀察窗 1900-01-01 ~ as_of）
        "交易日期": [date(2012, 1, 1 + i % 28) for i in range(18)]
                     + [date(2035, 6, 1), date(1899, 5, 5)],
        # Q1：raw 層一律 VARCHAR。兩筆帶千分位與幣別符號 → TRY_CAST 靜默變 NULL
        "刷卡金額": ["1234", "688", "NT$1,234", "155", "1,000"] + [str(100 + i) for i in range(15)],
        # Q11 一筆 5 元、Q17 一筆負值（退貨）
        "實付金額": [1234, 688, 1234, 155, 1000, 5, -48000] + [100 + i for i in range(13)],
        # Q2：9999 出現 15 次 = 客戶數 15
        "間隔天數": [9999] * 15 + [10, 12, 8, 14, 9],
        # Q8：一筆幣別 NULL
        "currency": ["TWD"] * 19 + [None],
        # Q10：一筆全形英數、一筆前後空白
        "刷卡地點": ["大台北地區"] * 18 + ["ＴＡＩＰＥＩ", " 高屏地區 "],
        # Q12：一筆 bot UA
        "user_agent": ["Mozilla/5.0 (Windows NT 10.0)"] * 19
                      + ["Mozilla/5.0 (compatible; Googlebot/2.1)"],
        # Q20：缺失率 90%（error 級，建議棄用）
        "備註": [None] * 18 + ["補刷", "分期"],
        # Q20：缺失率 30%（warning 級）
        "職業": ["軍公教", None, "服務業", None, "製造業", None] * 3 + ["自由業", None],
        # Q13：前綴缺 01 與 04、X2. 用點分隔破壞 split('_')
        "產業分類": (["02_餐飲", "03_旅遊", "05_百貨"] * 6) + ["X2.中信錢加值", "02_餐飲"],
        # Q4：'89'+'40526' 與 '894'+'0526' 無分隔符黏接後都是 '8940526'
        "客戶碼": ["89", "894"] + [str(200 + i) for i in range(18)],
        "日序": ["40526", "0526"] + [str(40000 + i) for i in range(18)],
    })[["交易序號", "客戶ID", "會員編號", "交易日期", "刷卡金額", "實付金額",
        "間隔天數", "currency", "刷卡地點", "user_agent", "備註", "職業",
        "產業分類", "客戶碼", "日序"]].head(20)


def build_dim() -> pd.DataFrame:
    """顧客維度。刻意不含 9999901 → 事實表那一列變孤兒（Q19）。"""
    ids = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    return pd.DataFrame({
        "客戶ID": ids,
        # Q5：一位客戶的額度 0（停用卡殘留），是「額度使用率」的分母
        "信用額度": [280000, 0] + [100000 + 10000 * i for i in range(12)],
        "辦第一張信用卡的時間": [date(2005, 1, 11)] * 14,
        "生日": [date(1975, 3, 2)] * 14,
    })


def main() -> int:
    fact, dim = build_fact(), build_dim()
    p1 = OUT / "dirty_mini.parquet"
    p2 = OUT / "dirty_mini_customers.parquet"
    fact.to_parquet(p1, index=False)
    dim.to_parquet(p2, index=False)
    print(f"✅ 已寫出 {p1}（{len(fact)} 列 × {len(fact.columns)} 欄）")
    print(f"✅ 已寫出 {p2}（{len(dim)} 列 × {len(dim.columns)} 欄）")
    print("\n這份 fixture 該讓哪幾條變紅：")
    for k, v in EXPECTED.items():
        print(f"  · {k:<34} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
