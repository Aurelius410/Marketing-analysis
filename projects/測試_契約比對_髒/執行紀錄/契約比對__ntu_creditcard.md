# 欄位契約比對報告 — ntu_creditcard

- 產出時間：2026-07-27T21:53:59
- 契約檔：`E:\Projects\行銷分析\projects\測試_契約比對_髒\原始資料\contracts\ntu_creditcard.yml`
- 退出碼：1（0 通過｜1 有 error 擋住｜2 只有 warning｜3 腳本失敗）

## 比對範圍

| 表 | 實檔 | 欄數 | 列數 |
|---|---|---:|---:|
| transactions | `ntu_creditcard__transactions.parquet` | 8 | 7,764 |
| customers | `ntu_creditcard__customers.parquet` | 11 | 100 |
| step5_cai | `ntu_creditcard__step5_cai.parquet` | 6 | 99 |

## error（擋住）

⛔ 金額欄 `MLE` 宣告成 DOUBLE — 02 §十 明文禁止 DOUBLE/FLOAT 存金額 —— 二進位浮點加總會漂移，對帳永遠差幾分錢。改 DECIMAL(18,4)
⛔ 欄位 `WMLE` 的宣告多了不認得的鍵：6) — 多半是 YAML flow mapping 的逗號陷阱 —— `dtype: DECIMAL(18,4)` 沒加引號時，`{}` 裡的逗號會把它拆成 `dtype: DECIMAL(18` 加一個叫 `4)` 的空鍵，而 YAML 不會報錯。dtype 帶括號一律寫成 dtype: 'DECIMAL(18,4)'。合法鍵只有 dtype/name/note/nullable/practical_use/table/unit
⛔ renames 有自我改名 `自己` → `自己` — 刪掉這一筆。它會讓 staging 的 COALESCE 變成同一欄自己 coalesce 自己
⛔ renames 的新名 `自己` 不在 columns 裡 — 改名後的欄位也要有契約。把 `自己` 加進 columns:
⛔ renames 的新名 `不存在的新欄` 不在 columns 裡 — 改名後的欄位也要有契約。把 `不存在的新欄` 加進 columns:
⛔ quality_overrides[0]（rule=Q2）缺 decided_by — 02 §十：這是 exit code 1 的唯一解除途徑。少一個鍵等於有人默默把紅燈關掉、而且查不到是誰關的
⛔ 實檔有、契約沒有：1 欄 — **請加進契約或加進 renames** —— 若這是既有欄位改名，寫 renames: 舊名 → 新名（append-only，不准刪舊鍵）；若是上游真的新增的欄位，加進 columns: 並補齊dtype/unit/nullable/practical_use 四個鍵。放著不管的下場是 union_by_name 靜默拆欄、各半 NULL（03 W5、gap D1）
- · transactions.刷卡類型  (VARCHAR)
⛔ `customers.Unnamed: 10` 契約宣告 nullable: false，實際有 1 個 NULL（1.00%） — 兩條路：確定該欄本來就可能空 → 契約改成 nullable: true 並在下游明寫補值或排除；不該空 → 這是上游或載入邏輯壞了，回頭查（NULL 在 JOIN 鍵上會靜默掉列，在 measure 上會讓 avg 的分母縮水）
⛔ `transactions` 的 grain (客戶ID, 刷卡日期) 不唯一：1,390 組重複、涉及 3,860 列（共 7,764 列） — 04 Q6。**只有「所有欄位皆同」才算真重複** —— 同卡同日同金額不是重複，課程資料集有 323 組是正常的重複刷（04 §三）。先確認粒度判斷對不對：以為是「一筆交易」其實是「一筆交易的一個品項」是最常見的情況
- · transactions: 13687, 2012-01-30 00:00:00 ×13
- · transactions: 605, 2012-09-03 00:00:00 ×11
- · transactions: 605, 2012-10-01 00:00:00 ×11
- · transactions: 605, 2012-07-30 00:00:00 ×10
- · transactions: 605, 2012-07-09 00:00:00 ×10
⛔ `transactions.刷卡地點` 出現 1 個契約沒宣告的值（合計 216 列，占 2.78%） — 上游多了一個分類。groupby 會多一列、對照表會漏接、卡方的期望次數被稀釋，而全程零報錯。確認是新分類 → 加進 enum_domains 的 values 並補上它在指標口徑裡的歸屬（18-G10）；是髒值 → 進 sentinels 宣告處理方式
- · '國外' ×216

## warning（可往下，要進報告的『資料限制』節）

⚠ renames 有鏈式改名 `自己` → `自己` → `自己` — staging 的 COALESCE 要把整條鏈串起來，漏一段就是半欄 NULL（03 W5）
⚠ 契約欄位 `消費地區`（table: transactions） 實檔沒有，但舊名 `刷卡地點` 還在 — 上游還沒完成改名。staging 一律 COALESCE(新名, 舊名) AS 新名 接住（03 W5）
⚠ `transactions.刷卡日期` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.生日` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.辦第一張信用卡的時間` 契約 DATE、實檔 TIMESTAMP_NS — 日期／時間戳不同族。實檔帶時分秒時，DATE 相等比較與 GROUP BY 會少一天；轉換時明寫 CAST(... AS DATE) 並用契約的 source_tz `Asia/Taipei` 先落地時區（02 §四）
⚠ `customers.Unnamed: 10` 契約 VARCHAR、實檔 DOUBLE — 型別族不同。確認是上游換了型別還是契約寫錯；契約寫錯就改契約，上游換型別就要評估下游計算會不會靜默改變
⚠ `step5_cai.WMLE` 契約 DECIMAL(18、實檔 DOUBLE — 型別族不同。確認是上游換了型別還是契約寫錯；契約寫錯就改契約，上游換型別就要評估下游計算會不會靜默改變
⚠ `step5_cai.CAI` 契約 DECIMAL(18,6)、實檔 DOUBLE — 實檔是浮點但契約要 DECIMAL。載入時 CAST，並比對總和差異 —— 先加總再轉換與先轉換再加總的結果不同

## info

· `CAI` 標為 segment_input —— 18-E2：只能是行為指標（R/F/M/RFM Score/CAI/CRI/因素分數/LN_F/LN_M），人口統計變數不准進分群
· `transactions.刷卡地點` 契約未直接宣告，但 renames 登錄了 `刷卡地點` → `消費地區`，視為已涵蓋
· `transactions.刷卡金額` 契約 DECIMAL(18,4)、實檔 BIGINT —— 整數轉 DECIMAL 無損，可放行
· `customers` grain (客戶ID) 唯一，100 列
· `step5_cai` grain (Custom ID) 唯一，99 列
· `transactions.刷卡類型` 值域相符：2/2 個宣告值出現，無未宣告的值
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
