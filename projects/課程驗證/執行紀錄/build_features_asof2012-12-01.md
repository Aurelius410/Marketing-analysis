# build_features 執行紀錄｜課程驗證｜as_of = 2012-12-01

- 產出：`E:\Projects\行銷分析\projects\課程驗證\顧客特徵表\feat_customer_asof2012-12-01.parquet`（100 位顧客、39 欄）
- 列數流：原始交易 7,764 → 去重後 5,294 → 間隔數 5,194 → 顧客數 100

## 雙路徑交叉驗算（00 §1.3）

| 指標 | 路徑 A | 路徑 B | 類型 | n | max_abs_diff | max_rel_diff | 容差 | 結果 |
|---|---|---|---|---:|---:|---:|---:|:--:|
| 顧客交易筆數 F | SQL GROUP BY COUNT | pandas pivot_table 計數 | 整數 | 100 | 0.000e+00 | 0.000e+00 | 0 | ✅ |
| 顧客金額 M | 交易明細層 SUM | 顧客×日彙總後再 SUM | 代數等價 | 100 | 0.000e+00 | 0.000e+00 | 1e-09 | ✅ |
| RFM 分位 r_score | SQL NTILE(5) | pandas 百分位序位切 | 分位 | 100 | 0.000e+00 | 0.000e+00 | 1 | ✅ |
| RFM 分位 f_score | SQL NTILE(5) | pandas 百分位序位切 | 分位 | 100 | 0.000e+00 | 0.000e+00 | 1 | ✅ |
| RFM 分位 m_score | SQL NTILE(5) | pandas 百分位序位切 | 分位 | 100 | 0.000e+00 | 0.000e+00 | 1 | ✅ |
| 平均購買間隔 λ (≡MLE) | SQL AVG(interval_days) | (末日−首日)/間隔數 | 代數等價 | 99 | 0.000e+00 | 0.000e+00 | 1e-09 | ✅ |

## ⚠ 警告

- 來源沒有 txn_type 欄，全部列視為 sale — 退貨／沖銷邏輯在這批資料上**無法被驗證**（17 §八）。若原始系統其實有退貨列，請補上該欄再重跑，否則 M 會虛胖、R 會偏近（18-G2）
- 沒有提供自訂 Bob Stone 參數，只算原版 — 09 §2.2 明訂本 skill 不給自訂權重的預設值（那是不能外包的商業判斷）。要算就傳 bobstone_custom=BobStoneCustom(...)，權重三段理由缺一不可
- 1 位顧客只有 1 個消費日，算不出間隔 → MLE/WMLE/CAI 標 N/A — 00 §四：這是「有樣本但算不出來」，報告寫 N/A 不是留白，並依 18-E22 交代人數（覆蓋率 99.0%）
- 沒有先驗分群層 → CRI 全部標 N/A（00 §五 M8-1 的降級規則）— 要算就給 dim_source 與 prior_group_cols，例如 --dim customers.parquet --prior-group-cols 性別

## · 明細

- 欄名對照：person_key←客戶ID、biz_date←刷卡日期、amount_twd←刷卡金額、txn_type←(缺，補 'sale')
- 原文 R-score 變體 INT(2^(4−INT(R/90))) 實際值域 0~16，超出 17 §3.2 宣稱的 1~16（R ≥ 450 時指數轉負）。要用這個變體就得自訂末段級距
