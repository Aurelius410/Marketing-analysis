# 欄位契約比對報告 — ntu_creditcard

- 產出時間：2026-07-27T21:57:08
- 契約檔：`E:\Projects\行銷分析\projects\測試_契約比對\原始資料\contracts\ntu_creditcard.yml`
- 退出碼：2（0 通過｜1 有 error 擋住｜2 只有 warning｜3 腳本失敗）

## 比對範圍

| 表 | 實檔 | 欄數 | 列數 |
|---|---|---:|---:|
| transactions | `ntu_creditcard__transactions.parquet` | 8 | 7,764 |
| customers | `ntu_creditcard__customers.parquet` | 11 | 100 |
| step5_cai | `ntu_creditcard__step5_cai.parquet` | 6 | 99 |

## error（擋住）

（無）

## warning（可往下，要進報告的『資料限制』節）

⚠ `transactions.刷卡日期` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.生日` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.辦第一張信用卡的時間` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.Unnamed: 10` 契約 VARCHAR、實檔 DOUBLE — 型別族不同。確認是上游換了型別還是契約寫錯；契約寫錯就改契約，上游換型別就要評估下游計算會不會靜默改變
⚠ `step5_cai.MLE` 契約 DECIMAL(18,6)、實檔 DOUBLE — 實檔是浮點但契約要 DECIMAL。載入時 CAST，並比對總和差異 —— 先加總再轉換與先轉換再加總的結果不同
⚠ `step5_cai.WMLE` 契約 DECIMAL(18,6)、實檔 DOUBLE — 實檔是浮點但契約要 DECIMAL。載入時 CAST，並比對總和差異 —— 先加總再轉換與先轉換再加總的結果不同
⚠ `step5_cai.CAI` 契約 DECIMAL(18,6)、實檔 DOUBLE — 實檔是浮點但契約要 DECIMAL。載入時 CAST，並比對總和差異 —— 先加總再轉換與先轉換再加總的結果不同

## info

· `CAI` 標為 segment_input —— 18-E2：只能是行為指標（R/F/M/RFM Score/CAI/CRI/因素分數/LN_F/LN_M），人口統計變數不准進分群
· `transactions.刷卡金額` 契約 DECIMAL(18,4)、實檔 BIGINT —— 整數轉 DECIMAL 無損，可放行
· `transactions` grain (交易序號) 唯一，7,764 列
· `customers` grain (客戶ID) 唯一，100 列
· `step5_cai` grain (Custom ID) 唯一，99 列
· `transactions.刷卡類型` 值域相符：2/2 個宣告值出現，無未宣告的值
· `transactions.刷卡地點` 值域相符：2/2 個宣告值出現，無未宣告的值
· `transactions.刷卡產品產業分類` 值域相符：15/15 個宣告值出現，無未宣告的值
· `customers.居住地` 值域相符：4/4 個宣告值出現，無未宣告的值
· `customers.教育程度` 值域相符：6/6 個宣告值出現，無未宣告的值
· `customers.性別` 值域相符：2/2 個宣告值出現，無未宣告的值
· `customers.婚姻狀況` 值域相符：2/2 個宣告值出現，無未宣告的值
· `customers.職業` 值域相符：13/13 個宣告值出現，無未宣告的值
· `customers.CAI` 值域相符：2/2 個宣告值出現，無未宣告的值
· sentinel `step2_interval.int = 9999` 的表不在比對範圍，跳過
· sentinel `cards.信用額度 = 0` 的表不在比對範圍，跳過
· `step5_cai.CAI` unit: percent，值域 [-43.6659, 54.5906]，口徑一致
· `step5_cai.CAI` 宣告成 percent —— 02 §十 的通則是率一律存 ratio。若非公式本身自帶 ×100（如 17 §4.2 的 CAI），staging 請除以 100
· 首次比對，建立契約快照：contract_snapshot__ntu_creditcard.json（往後偷改 grain 或刪 renames 舊鍵會被擋下）

---

> 規格出處：04_資料體檢.md §一 步驟②、§四；02_資料模型規格.md §十
