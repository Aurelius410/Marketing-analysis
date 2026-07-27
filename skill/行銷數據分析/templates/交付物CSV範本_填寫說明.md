# 交付物 CSV 範本 —— 檔頭說明

`sizing.csv` / `calibration_log.csv` / `excluded_options.csv` / `audience_list.csv`
這四份是 CSV，**沒辦法在檔案裡寫註解**（`verify_outputs.py` 的 `read_csv_rows()` 把
第一列當表頭，加一行 `#` 註解就等於把表頭換掉）。所以它們的「複製後要改哪幾個欄位」
統一寫在這裡。

四份的內容都是台大信用卡／示範專案的**實例**，不是預設值。照抄不改就會交出別人的數字。

---

## 共通：先確認檔名

`verify_outputs.py` 的 M01 檢查（14 §九）在 `<專案>/交付物/` 底下找這幾個檔名，
**檔名不對就是 error，不是 warning**：

| 範本 | 複製到交付物時的檔名 | 檔名對不上會怎樣 |
|---|---|---|
| `sizing.csv` | `sizing.csv`（不變） | D08 整條建議層驗不了 |
| `calibration_log.csv` | `calibration_log.csv`（不變） | M01 error |
| `excluded_options.csv` | `excluded_options.csv`（不變） | M01 warning（為空只是警告） |
| `audience_list.csv` | **必改**：`audience_{rec_id}_{as_of}.csv`，例 `audience_R2_2026-09-30.csv` | M01 只用 `audience_*.csv` 比對，所以照原名複製**驗得過**，但一建議一份名單的規矩就沒守住 |
| `decision_table.md` | **必改**：`decision_tables.md`（複數 s） | M01 error |

另外 `insights.md` 與 `decision_summary.md` 這兩份 M01 也要，但 `templates/` 底下
目前沒有它們的範本，要自己依 14 §二／§六 寫。

---

## `sizing.csv` —— 每條建議一列（14 §三）

`verify_outputs.py` 的 D08 會逐列驗，這幾欄動不了：

- `rec_id` —— 必改。要與 `decision_tables.md` 的 `→ rec_id`、`action_brief_<rec_id>.md`
  的檔名、`audience_{rec_id}_*.csv` 的檔名三邊對得上。
- `evidence_level` —— 必改。只能是 **相關／預測／準實驗／實驗** 四選一（00 §1.5）。
  填「準實驗」或「實驗」時，`模型輸出/analysis_objects.json` 的「證據檢查物件」必須
  真的有東西，否則 D08 直接判 error 並要求降級為「相關」。
- `breakeven_response_rate` —— 必改，**不准留空**。算不出來寫 `N/A`。這一欄是整份提案
  的斷路器（14 §3.1）。
- `verdict` / `net_value_low|point|high` / `safety_multiple` —— 必改成你自己算的數字。
  範本裡 R3 是刻意留的反例（安全倍數 0.55、淨值全負、verdict = 不做）。
- 每個 `rec_id` 還要配一份 `交付物/action_brief_<rec_id>.md`，沒有就是 warning，
  而且措辭白名單（相關級不准出現「提升」「帶動」這類因果詞）無從驗起。

## `calibration_log.csv` —— 業務校準紀錄（M01 必備）

- `reviewer_role` —— 必改成真的訪談過的人與年資，這欄是這份紀錄的證據等級來源。
- `check1..4_verdict` / `divergence_desc` / `dq_recheck_result` / `disposition`
  —— 必改。分歧要寫成「資料側說什麼、經驗側說什麼」兩段，不是只寫「已確認」。
- `linked_experiment_id` —— 分歧走「待試行」時必填，對回 `experiment_design.yml` 的
  `experiment_id`；沒有就填 `—`。

## `excluded_options.csv` —— 排除選項（M01 為空只是 warning）

- 四筆範例分別示範四種 `reason_class`：損益兩平打不平／資料不可行／合規或品牌風險／
  VOI（結果不影響行動）。**全部要換成你自己排除掉的選項**。
- `revisit_condition` —— 必填且要可驗證（寫「折抵金額降到 120 元」這種，不要寫「之後再看」）。
  沒有重看條件的排除，下一季就會有人原封不動再提一次。

## `audience_list.csv` —— 名單（14 §五）

- 檔名必改（見上表）。
- `cust_id` —— 必須是**去識別化後**的鍵（範本的 `h_9f2a1c` 是雜湊過的樣子），
  走 `scripts/anonymize_pii.py`，不要把原始會員編號寫進交付物。
- `segment_def_version` / `as_of_date` / `valid_from` / `valid_to` —— 必改。名單有效期
  過了就要重出，不准沿用。
- `list_sha256` —— 必改。範本寫的是被截斷的 `3b1f...`，要填完整雜湊值，
  這是「發出去的名單就是這一份」的唯一憑據。
- `suppression_reason` —— 排除的人**要留在檔裡並標原因**，不是刪掉。
  刪掉就沒人知道 3,050 人的群為什麼只發了 2,593 封。
