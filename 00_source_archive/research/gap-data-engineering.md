---
title: 缺口分析 — 資料工程與資料品質視角
doc_type: gap_review
reviewer: Claude Code subagent（資深分析架構審查者．資料工程與資料品質視角）
reviewed_at: 2026-07-26
language: zh-TW
scope: |
  審查對象：10_blueprint/01_框架藍圖_v1.md、10_blueprint/02_技術選型與防呆規則_定案.md、
  skill/行銷數據分析/SKILL.md、references/05_指標公式庫.md、references/07_分析陷阱清單.md
  依據素材：00_source_archive 全 18 份 digest，重點讀 research/01（倉儲）、research/02（B.16 歸因）、
  local/資料集剖析/marketing_datasets_profile.md（1,103 行全讀）、local/大數據行銷IB5082/02（四大資料檔）
exclusions: |
  本文刻意不重複 references/07 已收錄的 E1–E22、G1–G16、T1–T10。
  凡與既有條目主題相鄰者，均在該條目內明寫「G? 已覆蓋哪一半、本條補的是哪一半」。
counts:
  critical: 10
  important: 9
  nice-to-have: 2
  blueprint_corrections: 11
---

# 缺口分析 — 資料工程與資料品質視角

## 0. 一句話結論

**現有藍圖的資料工程厚度，集中在「單機引擎怎麼用」（研究 01 做得非常好），而幾乎沒有覆蓋「四種資料型態各自的口徑陷阱」。**

具體地說：G1–G16 是從**教材**的缺口反推出來的，所以它們全部是 CRM 交易資料的問題（身分、退貨、cohort、洩漏、投入資料）。但藍圖 §9 第 4 條已經拍板「四種資料型態全都會遇到」，而 D4 行銷投入域與 D5 行為域**在品質規則上是零覆蓋**：整份 skill 沒有出現過「時區」、「幣別」、「回填」、「attribution window」、「UTM」、「bot」、「同意管理」、「營業日」、「SCD」、「測試交易」任何一個詞。

第二個結論更刺眼：**素材裡已經寫好的品質規則，一條都沒有落地。** `marketing_datasets_profile.md` 裡有九處明確寫著「Skill 的 ingest 應該…」（9999 哨兵、Excel 樞紐 Grand Total、`Unnamed: N` helper column、字串黏接鍵碰撞、25% 矛盾的首卡日、額度 0 的除零、n=1 客戶、`1:男` 複合值、`X2.` 破壞 `split('_')`），這些是真的在包子自己的檔案上實測出來的，比任何通用最佳實務都值錢，但 references/07 的 G 系列一條都沒收。

---

## 1. 審查方法與可信度

- 藍圖與 skill 四份檔案逐行讀完。
- `marketing_datasets_profile.md` 1,103 行全讀（含 Step 1–5 的原始 Excel 公式與對帳結果）。
- `research/01_warehouse_sql_parquet.md` 讀 §3–§8（medallion 落地、schema 演進、品質分層、idempotency）。
- `research/02` 讀 B.16（歸因，本文 D6 的依據）。
- `local/大數據行銷IB5082/02` 讀 p.23 七步、p.39 動態檔十列欄位、p.44–48 日期維度。
- 用 `grep -ril` 對整個 `00_source_archive` 掃過 26 個資料工程關鍵詞，確認哪些主題是**素材真的沒有**，而不是我沒讀到。掃描結果：`timezone` / `貨幣` / `緩慢變動` / `attribution window` / `歸因窗` / `consent` / `營業日` / `測試交易` / `身分解析` / `血緣` **在全部 18 份素材中零命中**；`時區`、`SCD`、`lineage`、`遲到` 各僅 1–2 次且都是一筆帶過。

**可信度聲明**：本文所有「素材沒有覆蓋」的主張，來自上述 grep 全庫掃描，不是印象。所有帶數字的失敗情境，數字若來自 `marketing_datasets_profile.md` 的實測則標【實測】，若為我構造的示意則標【示意】。修補動作全部指定到「哪一支腳本／哪一條 SQL 斷言／哪一張表要加哪一欄」，沒有「應建立完善機制」這類話。

---

## 2. critical —— 會直接產出錯誤數字並導致錯誤行動

### D1　進場沒有 schema 契約；`union_by_name` 對「欄位改名」會靜默拆成兩欄

**現況**：S2 的 `profile_dataset.py` 是**單批快照**剖析（型別、缺失率、唯一值、五數摘要），沒有任何「這批 vs 上一批」的比對。而 research/01 §5.1 已經明確查證並警告：`union_by_name = true` 遇到改名欄位會產出**兩欄各半 NULL**，而它同時又建議 raw 層讀取「一律加這個，不要省」。兩件事放在一起就是一個靜默炸彈，而 SKILL.md 完全沒有對策。

**會怎麼出錯**【示意】：Meta Ads 報表匯出欄名從 `Amount spent (TWD)` 改成 `Spend`。raw 用 `union_by_name` 讀 6 個月的檔，得到 `Amount spent (TWD)` 與 `Spend` 兩欄，各有一半是 NULL。staging 的 SQL 只 `SELECT "Amount spent (TWD)" AS spend`，於是最近三個月的花費全部變成 NULL，`SUM(spend)` 少算一半。ROAS 從真實的 1.6 算成 3.2 → 回報「這個活動 ROAS 3.2，遠高於門檻 2.0，建議下月預算加倍」→ 實際上加碼的是一個剛好打平的活動。**這種錯誤不會有任何報錯，而且 profile 報告的「缺失率」欄位會照實顯示 50%，但沒有人被要求去看它。**

**修補動作**：
1. 新增 `contracts/<source>.yml`（每個來源一份），至少釘：`columns`（名稱 + 型別 + nullable）、`grain`（主鍵欄位清單）、`enum_domains`（類別欄的合法值集合）、`renames`（舊名 → 新名的縫合對照，append-only）。
2. 新增 `scripts/check_schema_contract.py`，在寫 raw **之前**跑：契約有、實檔沒有 → error；實檔有、契約沒有 → error 並印出「請加進契約或加進 renames」。這比 pandera 更早一層，pandera 守的是出口（research/01 §6.4 的定位正確，不必改）。
3. 新增 `sql/checks/raw__null_rate_drift.sql`：對每個來源的每一欄，比對本次載入與前一次載入的 NULL 率，差 >20 個百分點即 error。這一條抓的正是「改名造成半邊 NULL」，而且是唯一能自動抓到的方式。
4. staging 縫合一律寫成 `COALESCE(new_name, old_name) AS new_name`（research/01 §5.1 已給出這個寫法，只是沒被寫進 skill）。

---

### D2　時間戳語意與時區未定義：全 skill 只出現過一次「時區正規化」四個字

**現況**：research/01 §3.1 的分層表在 `20_staging` 的「允許做的事」欄裡寫了「時區正規化」四個字，就這樣。沒有任何地方規定：raw 存什麼、staging 轉成什麼、事實表要有幾個時間欄、`dim_date` 用哪一個欄 join。而藍圖的 `dim_date` 是**日粒度**的，這代表「哪一天」這個判斷會被時區直接決定。

**四種資料的時間語意實際上完全不同**（這是必須寫進 references/02 的表）：

| 來源 | 原始時間語意 | 常見坑 |
|---|---|---|
| GA4 / BigQuery export | `event_timestamp` 是 **UTC microseconds**（int64） | 直接 `CAST(... AS DATE)` 得到 UTC 日 |
| Meta / Google Ads 報表 | 日期是**廣告帳戶時區**的日，不是 UTC 也不一定是 Asia/Taipei | 同一天的 spend 與內部訂單錯開 |
| POS | 本地時間、**通常無時區資訊** | 被誤認為 UTC 而位移 8 小時 |
| CRM / 電商 API | 常見 ISO8601 帶 `+08:00`，也常見已被上游轉成 UTC | 兩批資料混用兩種語意 |

**會怎麼出錯**【示意】：做「線上瀏覽 → 門市購買」的同日轉換分析。web 事件用 GA4 的 UTC 日切，POS 用本地日切。台灣時間 00:00–08:00 的網站行為會被歸到**前一天**。這段時間流量不大（約 6%），但它把「週一凌晨的瀏覽」算成週日 → 週日的線上導流看起來比實際高 6 個百分點 → 報告結論「週日線上導流最強，建議把 EDM 發送時間從週三改到週日」→ 改完之後成效下降，而且沒有人會想到是時區。

**修補動作**：
1. **硬規則寫進 references/02**：事實表一律存三個欄位 —— `event_ts_utc TIMESTAMPTZ`（唯一可跨源比較的時間）、`event_ts_local TIMESTAMP`（呈現用）、`biz_date DATE`（**唯一允許 join `dim_date` 的欄**，定義 = `CAST(event_ts_utc AT TIME ZONE 'Asia/Taipei' AS DATE)`，跨夜業態另見 D9）。
2. raw 層時間一律存 **VARCHAR 原樣**（研究已建議 raw 全 VARCHAR，這裡是同一條規則的必然結果），並強制附一欄 `source_tz`（來自 D1 的契約檔，不是猜的）。
3. `sql/checks/stg_*__tz_shift.sql`：對每個來源畫「小時分布」，若某來源的小時分布與同類來源存在**整體位移 8 小時**的形狀（例如 POS 的尖峰落在凌晨 4–6 點），即 error。這個檢查很土但抓得到，因為人類活動的小時分布形狀非常穩定。
4. `check_data_quality.py` 加一則 error：任何 `TIMESTAMP` 欄位若無對應的 `source_tz` 宣告 → 不准進 staging。

---

### D3　多幣別未經匯率維度表正規化就直接 `SUM`

**現況**：素材裡「幣別」只出現在 `marketing_datasets_profile.md` 的一則建議——缺幣別欄時發一則 `WARNING: currency column absent, unit inferred as TWD`。這是對的但只解決了「單一幣別但沒寫」的情況，完全沒有處理**多幣別**。而廣告投放域幾乎必然多幣別：Meta / Google Ads 的帳戶幣別是開帳戶時定的，跨境或代理商代開的帳戶常是 USD。

**會怎麼出錯**【示意】：三個 Meta 廣告帳戶，兩個 TWD、一個 USD。`fact_marketing_spend` 直接 `SUM(spend)`。USD 帳戶當月 spend 3,200（實為 USD，約 NT$102,000）被當成 NT$3,200。該帳戶帶回營收 NT$120,000 → 算出 ROAS = 120,000 / 3,200 = **37.5**，實際是 1.18。報告把它列為「最高效通路，建議把 60% 預算移過去」→ 移過去的是一個實際上剛好打平的帳戶，而真正 ROAS 2.8 的通路被砍。**37.5 這個數字荒謬到應該被質疑，但因為 ROAS 沒有「同欄數量級差 >100 倍」的離群掃描（E9 只針對統計表），它會直接進報告。**

**修補動作**：
1. 治理域新增 `dim_fx_rate(rate_date DATE, currency VARCHAR, rate_to_twd DECIMAL(18,8), source VARCHAR)`。**匯率是維度資料，不是程式裡的常數**——這是 G10「指標定義必須是資料」的同一個道理，只是 G10 沒想到匯率。
2. `fact_marketing_spend` 一律四欄並存：`spend_original`、`currency`、`spend_twd`、`fx_rate_date`。禁止只存 `spend`。
3. `sql/checks/fact_spend__currency_resolved.sql`：`WHERE currency IS NULL OR currency NOT IN (SELECT currency FROM dim_fx_rate WHERE rate_date = f.fx_rate_date)` → 回傳非 0 列即 error。
4. 換匯日期政策要寫進指標字典（用交易日匯率 vs 期末匯率 vs 月均匯率），因為它會改變數字，而且事後沒人記得用了哪一種。
5. **延伸到「單位」**：同一條檢查機制要覆蓋率的表示法。廣告平台匯出的 CTR 有 `2.35`（百分比數）與 `0.0235`（比例）兩種，混算平均 CTR 會得到 1.19 → 「整體 CTR 119%」。契約檔的每個率欄位必填 `unit: ratio|percent`，staging 一律轉成 `ratio` 存，只在呈現層乘 100。

---

### D4　廣告平台回填造成數字事後變動：缺 `data_as_of_date` 雙時間軸

**現況**：整份素材零覆蓋。research/01 §7 的 idempotency 方案（`OVERWRITE_OR_IGNORE` + 明確日期範圍、`MERGE INTO`）處理的是「重跑不要重複灌」，但**它隱含假設同一個 `report_date` 的數字是穩定的**。廣告平台不是這樣：Meta 的 7 天點擊 / 1 天瀏覽歸因窗代表 7/1 的 conversions 會一路被回填到 7/8；Google Ads 的轉換回溯窗最長 30 天甚至 90 天；影片瀏覽歸因也有延遲。**同一個 `report_date` 在不同抓取日會給出不同數字，這不是 bug，是規格。**

**會怎麼出錯**【示意】兩種，兩種都很痛：

- **情境 A（低估近期，最常見）**：每天凌晨抓「昨天」的資料，用 `OVERWRITE_OR_IGNORE` 寫入 `report_date=` 分區，之後不再回頭。7/1 抓到 conversions=120，而回填完成後真實值是 168（+40%）。於是**每一天的資料都停在「未回填完成」的狀態**，整條時間序列被系統性低估。新活動上線第三天回報「conversions 只有 118，CPA NT$840，遠高於目標 500，建議關停」→ 關掉一個真實 CPA 是 NT$600 的有效活動。
- **情境 B（數字打架，殺傷信任）**：7/2 產出的月中報告寫「7 月上旬 ROAS 1.8」，8/1 產出的月報寫「7 月 ROAS 2.5」。儀表板每天覆寫、沒有 snapshot，於是無法解釋差異來源，主管的結論是「你們的數字不能信」。

**修補動作**：
1. **`fact_marketing_spend` / `fact_ad_performance` 的 grain 改成雙時間軸複合鍵**：`(platform, account_id, campaign_id, report_date, data_as_of_date)`。`report_date` = 成效歸屬的日；`data_as_of_date` = 抓取日。這是唯一能同時回答「7 月 ROAS 是多少」與「當時我們以為是多少」的結構。
2. 載入策略改成**滾動回抓**：每次抓取覆蓋 `report_date >= today - N`，`N ≥ 該平台最長歸因窗 + 1`。把 N 存進治理域的 `dim_attribution_setting`（見 D6），不要寫死在腳本裡。Meta 7d-click/1d-view → N=8；Google Ads 預設 30 天轉換窗 → N=31。
3. 新增 `sql/checks/spend_restatement.sql`：對每個 `report_date`，比較最新 `data_as_of_date` 與首次抓取的 conversions/spend 差異，>5% 即寫入清理日誌並列入 S3 回報的異動清單。
4. **報告與儀表板的每一張廣告成效圖強制標註「資料截止日 data_as_of = YYYY-MM-DD」**，並對最近 N 天的資料加上「回填未完成」的視覺標記（灰底或虛線）。這一條要進 references/08。
5. 分析口徑硬規則：**「最近 N 天不得用於趨勢判斷與活動開關決策」**，寫進 references/07 的新條目。

---

### D5　通路對照表缺失：UTM 不一致會把同一個通路拆成好幾列

**現況**：藍圖 §3.1 有 `dim_channel`，但只是列在表格裡，沒有任何規格說它怎麼從原始 UTM 產生。整份素材沒有出現「UTM」一詞。

**會怎麼出錯**【示意】：同一個 Facebook 活動因為不同人建連結，`utm_source` 出現 `facebook` / `Facebook` / `fb` / `FB` / `facebook.com`，`utm_medium` 出現 `cpc` / `CPC` / `paid_social` / `paid-social`。直接 `GROUP BY utm_source, utm_medium` 做通路營收排行 → Facebook 被拆成 5 列，最大那一列只佔 Facebook 真實營收的 45%（NT$1,080,000 中的 NT$486,000）→ 在通路排行榜上從第 1 名掉到第 5 名 → 報告建議「Facebook 表現不如預期，把預算移往 Google」→ 砍掉真正最強的通路。

**修補動作**：
1. 治理域新增 `dim_channel_mapping(raw_source, raw_medium, raw_campaign_pattern, channel_group, channel_detail, is_paid, valid_from)`。**必須是維度表，不能是 SQL 裡的 `CASE WHEN`**——理由與 G10 相同：`CASE WHEN` 會被複製到十個 SQL 檔然後彼此不同步。
2. staging 一律先 `lower(trim(x))` 再對照。
3. `sql/checks/stg_web__unmapped_channel.sql`：列出所有無法對照到 `channel_group` 的 `(raw_source, raw_medium)` 組合及其 session/營收占比。**未對照量 >1% 即 error**（不是 warning），錯誤訊息直接印出待補的組合清單，讓修補動作是「把這幾列貼進 mapping 表」而不是「去 debug」。
4. 加一條 warning 檢查：**同一個 `channel_group` 底下出現多個只差大小寫或連字號的 `raw_source`** → 提示 mapping 表可能漏了正規化。

---

### D6　跨平台 attribution window 不可比，卻把各平台自報的 conversions 相加

**現況**：research/02 §B.16 已經誠實寫出「Markov 歸因不是因果推論」與「需要使用者層級完整觸點路徑」，這部分很好。但**沒有任何地方講「各平台自報數字不可加總」這件更基本、更常犯的事**。references/07 的 G5 講的是「沒有投入資料就談 ROI」，G6 講的是「相關寫成因果」，兩者都不覆蓋這一條。

**會怎麼出錯**【示意】：月報做「各通路 conversions 與 ROAS 排行」，資料直接取各平台後台自報值：Meta 430（7 天點擊/1 天瀏覽）、Google 380（30 天點擊）、LINE 150、EDM 120，合計 1,080。內部訂單系統該月實際只有 **620** 筆。原因有兩個：同一筆訂單被多個平台各自認領（重複計算約 380 筆），以及不同歸因窗把不同時間的轉換算進來。用 1,080 算整體 ROAS 得 2.6，實際 1.5。報告結論「整體 ROAS 2.6，健康，建議全面加碼 30%」→ 加碼一個實際上剛過打平線的組合。**更細的錯**：把 Meta（7 天窗）與 Google（30 天窗）畫在同一張「通路 ROAS 排行」長條圖上，等於用兩把不同刻度的尺量兩個人。

**修補動作**：
1. 治理域新增 `dim_attribution_setting(platform, account_id, window_click_days, window_view_days, attribution_model, valid_from, valid_to)`。這張表同時是 D4 滾動回抓窗 N 的來源。
2. **硬規則（進 references/07 與 SKILL.md 的「絕對不要出現的東西」）**：平台自報 conversions **只能各自呈現，絕不相加**；也不可與內部訂單數直接比對「差多少」而不說明機制。
3. 跨平台總量一律回到**內部訂單為單一真相**，平台數字只用於「該平台內部的期間比較」與「該平台內部的活動間比較」。
4. 報表固定加一列**「平台自報總和 vs 內部實際訂單」的落差百分比**，並在腳註寫明「落差來自跨平台重複認領與歸因窗差異，非資料錯誤」。這一列的存在會讓任何人自動停止相加。
5. 每一張跨平台圖表強制標註各平台的歸因窗（例如 `Meta (7d click/1d view)` / `Google (30d click)`），標不出來就不准畫。

---

### D7　緩慢變動維度（SCD）完全缺失：門市代碼變更會讓同店比較說謊，維度覆寫會改寫歷史

**現況**：整份素材裡 `SCD` 出現兩次，都是一筆帶過（research/01 §3.1 的 mart 層「允許做的事」列了「SCD」三個字母；§8.3 誠實列出「放棄了 dbt 的 snapshot（SCD Type 2）」）。`緩慢變動` 零命中。而藍圖 §3 的 `dim_customer` / `dim_product` 都是單一 Parquet 檔、無版本欄位，`dim_store` 甚至不存在（POS 域只有 `fact_store_traffic`）。**這代表預設行為是覆寫式更新，也就是「歷史會被今天的維度值改寫」。**

**會怎麼出錯**——兩個情境，第二個是任務點名的門市代碼變更：

- **情境 A（維度覆寫改寫歷史）**【示意】：顧客的 `居住地` 從高屏改成大台北（搬家，CRM 資料更新）。因為 `dim_customer` 是覆寫的，這位顧客**過去兩年在高屏的所有消費，今天全部被歸到大台北**。500 位顧客中有 40 位搬遷，於是「大台北地區同期營收成長 22%」→ 報告建議把高屏的行銷資源撤回大台北 → 實際上高屏沒有衰退，是統計口徑在移動。同一個機制也會毀掉「白金卡客人消費比較高」這類分析：卡等是**消費高之後才升等**的，用今天的卡等回貼歷史交易，必然得到「白金卡消費高」，然後建議「推廣白金卡」——這是 G6 的因果錯誤，但**成因是 SCD 缺失**，G6 那條完全沒指向這個機制。
- **情境 B（門市代碼變更破壞同店銷售）**【示意】：門市改裝重開，代碼從 `T012` 換成 `T105`（POS 系統常態）。直接 `GROUP BY store_id` 算同店銷售（SSS）→ `T012` 在 6 月「關店」、`T105` 在 7 月「新開」→ SSS 計算把 `T105` 當新店排除、把 `T012` 當關店排除，該商圈的 SSS 從真實的 **+3%** 算成 **−8%**（因為改裝期間的低基期留在 T012，而改裝後的成長全在被排除的 T105）→ 結論「改裝沒有帶來成長，建議暫停後續五家門市的改裝計畫」→ 停掉一個實際有效的資本支出計畫。

**修補動作**：
1. `dim_store` 建成 **SCD Type 2**：`store_key`（代理鍵，事實表存這個）、`store_id`（自然鍵）、`store_group_id`（**跨代碼串接用，改裝/搬遷/換代碼時保持不變**）、`valid_from`、`valid_to`、`is_current`，加上營運屬性 `open_date` / `close_date` / `remodel_periods`。
2. `dim_customer` 對「會變、且會影響歸因」的屬性採 SCD2：居住地、婚姻狀況、會員等級、卡等。不會影響歸因的（生日、性別）維持 Type 1。**判準寫進 references/02：這個屬性有沒有被用在「分組比較歷史數字」上？有就 SCD2。**
3. 事實表一律存**代理鍵**（`customer_key` / `store_key`），join 時用 `event_ts_utc BETWEEN valid_from AND valid_to`。這是「as-of join」，DuckDB 用 `ASOF JOIN` 原生支援，寫起來不痛。
4. 同店銷售的 SQL 硬規則：`GROUP BY store_group_id`，且**限制在兩期都營業的門市**（`WHERE store_group_id IN (SELECT ... 兩期皆有營業日)`），並在報表標明納入的門市數與排除的門市數與原因。
5. `sql/checks/dim_store__code_change.sql`：偵測「某 `store_id` 的交易在某日突然歸零，且同期出現一個新 `store_id` 且地址/縣市/鄉鎮相同」→ 列為 warning 要求人工確認是否應併入同一個 `store_group_id`。
6. `sql/checks/dim_scd2__no_overlap.sql`：同一自然鍵的有效期間不得重疊、不得有空隙、`is_current` 恰好一列。SCD2 最常見的 bug 就是這三個，不檢查必出。

---

### D8　退貨與換貨：G2 只處理了 M，沒處理 `txn_type`、沒處理 R 被污染、沒處理期間錯配

**現況**：G2 說「指標字典明訂 M 口徑；預設淨額，並輸出毛額／淨額對照」。這只解決了三分之一。而 `05_指標公式庫` 的 RFM SQL 是 `COUNT(*) AS F, SUM(amount) AS M FROM fact_transaction`，**沒有任何 `txn_type` 過濾**——因為課程資料集實測「刷卡金額無負值、無零值，不含退貨」（profile §2.5.4【實測】），所以這個漏洞在驗收時 100% 通不出來。

**三個 G2 沒覆蓋的錯誤**：

- **R 被退貨日污染（最嚴重）**【示意】：一位顧客最後一次購買是 2025-08-10，2026-07-20 辦了退貨。退貨在系統裡是一筆交易列。`R = 基準日 − MAX(txn_date)` → R = 6 天 → 這位一年沒買的顧客被算成「最近極活躍」，RFM 分群落在 `R_score=5` → 進了「新客戶 New/Promising」或「冠軍客戶」名單 → 收到加購推薦與 VIP 禮。**這在真實 CRM 資料上是必然發生的，而且完全沉默。**
- **F 被換貨重複計算**【示意】：換貨在多數 POS/電商是「一筆退 + 一筆買」。3% 的訂單換貨 → 這些顧客的 F 各多算 2 次而不是 0 次 → 換貨率高的品類（服飾）顧客的 F 被系統性高估 → 「服飾客群忠誠度最高」→ 把 CRM 預算移到一個其實是退換貨造成的假象。
- **期間錯配與 restatement 政策未宣告**【示意】：12 月營收 1,000 萬，其中 80 萬在隔年 1 月退貨。記在**退貨日**：12 月虛高 8%、1 月被打成 −8%，月報的「1 月營收衰退」是假的。記在**原交易日**：已公布的 12 月報表事後被改寫，而沒有人知道它被改寫過。**兩種做法都對，但必須選一個、宣告它、並讓改寫可被偵測。** 目前 skill 兩件都沒做。

**修補動作**：
1. `fact_transaction` 強制新增 `txn_type VARCHAR`（`sale` / `return` / `void` / `exchange_out` / `exchange_in`）與 `original_txn_id`。這兩欄要進 references/02 的 DDL，且列為必填——沒有這兩欄的資料源在 S2 就要標「無法正確計算 R/F」。
2. **R 與 F 的口徑硬規則**：`WHERE txn_type = 'sale'`。加一支斷言 `sql/checks/feat_rfm__source_filter.sql`，用 DuckDB 的 `duckdb_views()` / SQL 檔文字掃描確認 `feat_rfm` 的來源查詢包含這個過濾——聽起來土，但這正是「防止未來的自己忘記」最有效的做法，同 T3 用 `anova3()` 包住 `anova_lm` 的思路。
3. M 用淨額，但**記在原交易日**（避免月報被 1 月的退貨打穿），並在指標字典新增 `restatement_policy` 欄位明寫這個選擇。同時輸出「毛額 / 退貨 / 淨額」三欄對照（G2 只要求兩欄）。
4. 因為 M 記在原交易日，已公布的數字會事後變動——這與 D4 是**同一個問題的另一個面向**，所以用同一個機制解：`data_as_of_date` + `checks/*_restatement.sql`。
5. 換貨處理：`exchange_out` + `exchange_in` 在 F 上**淨計 0 次**、在 M 上淨計價差。指標字典要有一列說明。
6. 迴歸測試必須用 dirty fixture（見 D16），因為課程資料集永遠測不出這一組 bug。

---

### D10　哨兵值／魔術數未偵測：素材裡有實測案例，Skill 卻沒有這條檢查

**現況**：`marketing_datasets_profile.md` §2.6 明確寫出建議——「若某數值欄出現 9999 / 99999 / −1 / −999 且**頻率恰等於群組數**，高度可疑為哨兵值，須排除後再算統計量」。這是一條非常精準、可直接實作的規則，來自包子自己檔案上的實測。**它沒有進 references/07，也沒有進 SKILL.md。**

**會怎麼出錯**【實測數字】：課程資料集的 `Step 2` 的 `int` 欄含 100 個 `9999`（每位客戶最後一筆的哨兵）。若未排除就算平均購買間隔：`mean = 199.46`；排除後真值 `mean = 10.79`。**差 18.5 倍。** 用 199.46 當「平均購買間隔」→ 流失判定門檻設成「超過 200 天未購買才算流失」→ 100 位客戶裡只有 3 位被標流失（真實應為 28 位「沉睡/流失」群，profile §2.7 實測）→ 挽回名單漏掉 25 人，這 25 人合計 M 為 NT$947,152（占總營收 6.4%）。而且因為 CAI 的 MLE 是分母，哨兵污染會讓 `CAI = (MLE − WMLE)/MLE` 整體被壓向 0 → 所有人都看起來「節奏穩定」→ 流失預警完全失效。

**同類的魔術數**（POS/CRM 常見，一併寫進規則）：`1900-01-01` / `1970-01-01` / `9999-12-31` 當日期哨兵；`0` 當「未知」信用額度（profile §2.5.6【實測】：信用卡 19817 的額度為 0，任何「額度使用率 = 消費/額度」都會除以零）；`-1` 當未知數量；`999999` 當未知郵遞區號。

**修補動作**：
1. `profile_dataset.py` 新增 `sentinel_scan()`：對每個數值欄檢查候選哨兵集合 `{-1, -9, -99, -999, 0, 9999, 99999, 999999}` 與日期哨兵集合 `{1900-01-01, 1970-01-01, 2099-12-31, 9999-12-31}` 的出現次數；若某值的出現次數 **恰等於或極接近某個 group-by 鍵的相異值數**（例如恰等於客戶數 100），標為 `SUSPECTED_SENTINEL` 並列為 S2 卡點必答項。
2. `check_data_quality.py` 把 `SUSPECTED_SENTINEL` 放進 **error 桶**（不是 warning）——理由是它會靜默污染平均數，而 warning 會被忽略。要往下走必須在契約檔 `contracts/<source>.yml` 的 `sentinels:` 明確宣告該值的處理方式（`to_null` / `keep` / `exclude`）。
3. `sql/checks/*__division_by_zero.sql`：所有比率型指標的分母欄，回傳 `WHERE denominator = 0 OR denominator IS NULL` 的列數，>0 即 error 並要求宣告處理方式（額度 0 的卡應被判定為停用卡而排除，見 profile §2.5.6）。
4. 一併把 profile 裡另外三條實測規則寫進 `references/04_資料品質與踩雷庫.md`（這三條不夠格單獨成一條 critical，但都是免費的檢查）：
   - **Excel 樞紐表雜訊列**：讀入時自動剔除列標籤為 `Grand Total` / `總計` / `合計` / `(blank)` / `(空白)` 的列。實測：`Step 4` 是 101 列 = 99 客戶 + Grand Total + (blank)；若不剔除，`Sum of Weight = 306,520` 的 Grand Total 會變成一位「顧客」並衝上 CAI 榜首。
   - **`Unnamed: N` helper column**：保留但標記 `helper_column`，不當業務欄位。實測：K 欄只少 1 格，會讓 `dropna(axis=1, how='all')` 誤判為業務欄。
   - **字串黏接鍵碰撞**：`=A2&B2` 產生的 `客戶ID ++ 日期序號` 無分隔鍵理論上會碰撞（`89&40526` vs `894&0526` vs `8&940526` 都是 `8940526`）。實測本檔 5,294 組無碰撞是運氣。一律改用 `客戶ID || '|' || 日期` 或直接 `GROUP BY` 兩欄。

---

### D11　同意管理與量測制度變更造成的量測斷層，會被讀成業務變化

**現況**：`consent` 在全部 18 份素材零命中，`同意` 只出現在報告文體與文字探勘的無關語境。而藍圖 §3.1 的 D5 行為域直接把 `fact_web_event` 當成完整的行為紀錄，沒有任何「涵蓋率」概念。

**會怎麼出錯**【示意】：網站導入 CMP（cookie 同意管理平台），同意率 62%，未同意者不進 GA4。上線當日 session 數從 158,000 掉到 98,000（−38%）。恰好同期改版了 landing page。報告的趨勢圖是一條連續折線，結論「改版導致流量下滑 38%，建議立即回滾」→ 回滾一個實際上提升了轉換率的改版，而且回滾後流量不會回來（因為那 38% 是量測缺口不是真實流量），於是繼續往下找錯，浪費兩週。

**第二層錯誤更難察覺**：同意者與未同意者的行為分布不同（願意接受 cookie 的人通常對品牌熟悉度較高、轉換率較高）。用 62% 的同意樣本算轉換率 → 系統性高估 → 拿這個轉換率去算「若把流量翻倍可多賺多少」→ 高估收益，據此批准了一筆廣告預算。這是**選擇偏誤**，而 G 系列的選擇偏誤條目（藍圖 §S6 第二道關）舉的例子是問卷，完全沒指向量測制度。

**修補動作**：
1. 治理域新增 `log_measurement_change(change_date, scope, change_type, description, expected_impact_direction, coverage_before, coverage_after)`。記錄：CMP 上線/改版、GA4 SDK 版本變更、追蹤碼部署、網域變更、App SDK 升級、iOS ATT 政策生效、瀏覽器擋追蹤政策變更。**這張表是 `dim_date` 的兄弟表**——`dim_date` 記「這一天有什麼行銷刺激」（教材 p.44 的公司促銷、競爭者活動），`log_measurement_change` 記「這一天量測方式變了什麼」。教材有前者、沒有後者。
2. **references/08 的硬規則**：任何跨越 `log_measurement_change` 記錄日的趨勢圖，**強制在該日畫斷線（break）並加註**，不准畫成連續折線。這條要進 `verify_outputs.py`：檢查圖表的日期範圍是否跨越變更日，跨越但無斷線標記 → 不准輸出。
3. 網站指標一律附「量測涵蓋率」：`coverage_rate = 可量測 session / 估計總 session`（用伺服器日誌、CDN 日誌或 CMP 自己回報的同意率當分母）。報告的每個網站指標旁標 `(涵蓋率 62%)`。
4. **禁止用 GA4 session 當母體算滲透率或市占**（分母不完整），要用內部訂單或伺服器日誌。
5. 若要用同意樣本外推，必須做同意者 vs 非同意者的可觀測特徵比較（裝置、來源、地區）並在報告寫明差異——不做就只能標「本數字僅代表可量測樣本」。

---

## 3. important —— 會讓結論不穩、對不上、或給出假的安全感

### D9　營業日 ≠ 自然日；行銷月 ≠ 會計期

**現況**：`營業日` 全庫零命中。藍圖的 `dim_date` 完全採用教材 p.45 的設計（一天一列、七個星期 0/1、週休二日、連續假期），這個設計本身很好，但它假設「日」只有一種切法。

**會怎麼出錯**【示意】：餐飲/娛樂/便利商店跨夜營業（打烊 02:00–06:00）。用 `CAST(txn_ts AS DATE)` 切自然日 → 週五 23:00–02:00 的營收被拆到週五與週六兩天，其中深夜段（常是尖峰，占該營業日 35%）被記到週六。結果「週六是最強日」→ 把人力排班與促銷檔期押在週六白天，實際尖峰是週五深夜。更糟的是它同時破壞教材 p.45 的假日旗標：那筆營收的 `dim_date` join 到「週六、週休二日=1」，而消費行為實際發生在「週五、平日」的情境下 → 日期效應迴歸的係數整體被污染。

**第二個面向**：零售常用 4-4-5 會計期或「每月 26 日結帳」。行銷月報用自然月、財務用會計期 → 兩邊營收永遠差幾個百分點，每個月花時間對帳且沒有結論。

**修補動作**：
1. `dim_store` 新增 `biz_day_cutoff_hour INT`（跨夜業態填 6，一般零售填 0）。
2. 事實表存兩欄：`calendar_date`（`CAST(event_ts_local AS DATE)`）與 `biz_date`（`CAST(event_ts_local - INTERVAL (s.biz_day_cutoff_hour) HOUR AS DATE)`）。**`dim_date` 一律 join `biz_date`**（與 D2 的規則一致）。
3. `dim_date` 新增 `fiscal_year` / `fiscal_period` / `fiscal_week`，由專案在 S1 宣告會計期規則（自然月 / 4-4-5 / 26 日結）。報表標題強制標明用的是哪一種。
4. `sql/checks/fact_pos__txn_within_open_hours.sql`：每筆交易的時間必須落在該門市該營業日的營業時段內，違反即 warning（抓得到門市營業時間設定錯誤與 POS 時鐘漂移）。

---

### D12　bot 與內部流量未過濾

**現況**：`bot` 在素材裡的命中全部是無關語境（文字探勘的 robots、TMBA 的 robot）。網站行為域沒有任何過濾規則。

**會怎麼出錯**【示意】：監控探針、爬蟲、與自己團隊的壓測合計占 session 的 8%，這些 session 停留 0 秒、單頁、零轉換。它們進入分母 → 整站轉換率被稀釋。改版當月剛好新增了一個監控探針（每分鐘打一次首頁），bot 流量從 8% 升到 14% → 轉換率從 2.50% 掉到 2.33%（−0.17pp）→ 報告「改版造成轉換率下滑」→ 回滾。同一個機制在廣告端更貴：若某個聯播網通路帶來的多是無效流量，它的「每 session 成本」看起來最低 → 加碼投放，實際零轉換。

**修補動作**：
1. `stg_web_event` 一律套過濾層，規則放在 `contracts/web_bot_rules.yml`（可版控、可 diff）：UA 黑名單（含 `bot|crawl|spider|monitor|headless|lighthouse`）、內部 IP / CIDR 白名單排除、已知雲端供應商 IP 段、單 session 事件數 > p99.9、停留 0 秒且單頁且無互動事件。
2. **不要直接刪**：標記 `is_bot BOOLEAN` 保留在 staging，mart 的分析視圖 `WHERE NOT is_bot`。這樣「排除了多少」永遠可回查，符合 S3 清理日誌的精神。
3. `sql/checks/stg_web__bot_rate.sql`：bot 排除率的**週對週變化 >5 個百分點即 warning**（抓的是「新增了一個探針」這種事件），排除率 >20% 即 error。
4. 清理日誌與 S3 回報固定列出 bot 排除筆數與占比。

---

### D13　遲到資料與載入完整度：缺 watermark，也缺「完整度斷言」

**現況**：research/01 §7 的 idempotency 方案很完整地處理了「重跑不要多灌」，但**完全沒有處理「這一批到底載完了沒有」**。`遲到` 全庫只在既有 skill 慣例裡出現一次且無關。同時，藍圖把「一天一列連續不跳號」寫成 `dim_date` 的硬約束（教材 p.45 的評註講得很清楚：交易可為零但日期列必須存在，否則無法估計「不購買」的機率），但**沒有任何檢查落實它**。

**會怎麼出錯**——兩個方向，一個少一個多：

- **少了（遲到）**【示意】：月報在次月 3 號跑。5 家門市（共 42 家）因連線問題晚兩天上傳。該月營收低估 4.2%，且分店排名把那 5 家打到末段 → 該月獎金核算錯誤、陳列與人力調整往錯的方向做。等資料補齊後沒有人重跑月報。
- **多了（重複載入）**【示意】：廣告 API 分頁重疊或手動重跑腳本，7/15 的列出現兩次 → spend double count → 該日 ROAS 腰斬 → 「7/15 的活動異常低效」→ 關停一個正常的活動。
- **`dim_date` 缺日**【示意】：`dim_date` 用 `SELECT DISTINCT txn_date FROM fact_transaction` 生成（最省事、最常見的做法）→ 沒有交易的日子不存在 → 做日期效應迴歸時，零銷售日被當成缺值而不是 0 → 週一（門市休館日多）的平均銷售被高估 → 「週一表現不錯，不需要調整」。

**修補動作**：
1. 治理域新增 `ingest_watermark(source, biz_date, first_seen_at, last_updated_at, row_count, sum_key_metric, load_run_id)`。每次載入 upsert。這張表同時服務 D4（回填偵測）與這一條。
2. `sql/checks/ingest__completeness.sql`：對每個 `(source, biz_date)`，比對 `row_count` 與「前四週同 weekday 的中位數」，落差 >30% 即 error（抓遲到與重複兩個方向）。POS 另加「應上傳門市數 vs 實際上傳門市數」的斷言，缺門市即 error 並列出門市代碼。
3. 報告固定新增一張**「資料完整度」表**（來源 × 期間 × 列數 × 涵蓋門市數 × 資料截止日），這是 D4 的「資料截止日」標註的同一件事，統一在這張表交代。
4. `dim_date` 一律用 `generate_series` 生成，並加兩條斷言：`count(*) = date_diff('day', min(d), max(d)) + 1`（連續不跳號）；所有事實表的 `biz_date` 都能 join 到 `dim_date`（零孤兒）。
5. **每張表的 grain 要變成持續斷言，不只是 S2 的一次性觀察**：`sql/checks/<table>__grain_unique.sql`，`GROUP BY <契約宣告的 grain 欄位> HAVING count(*) > 1`。目前 SKILL 的 S2 有「粒度判定」，但那是一次性的人工判斷，之後沒有任何東西守著它。
6. raw 一律加 `_source_file` 與 `_ingested_at`（research/01 §3.1 已建議，未寫進 skill），讓重複載入可被歸因到具體檔案。

---

### D14　session 定義未釘死，且與 GA4 介面數字必然對不上

**現況**：藍圖 §10 把「`fact_web_event` 的 grain 要到什麼程度（每次 pageview？每個 session？）」列為**待包子確認的問題**，`dim_session` 只出現在表格裡沒有規格。這代表 session 化規則目前是空白。

**會怎麼出錯**【示意】：自建 sessionization 用「30 分鐘閒置切割」。GA4 除了 30 分鐘閒置，還會在 **campaign 參數變更時切出新 session**，且有自己的跨午夜規則。結果自算 sessions = 124,000、GA4 介面 = 158,000（差 27%）。用自算分母得轉換率 3.2%，行銷團隊看 GA4 介面是 2.5%。報告對外宣稱 3.2% → 被平台數字打回 → 整份報告的可信度歸零，而爭論的其實不是誰錯，是兩個都對但定義不同。

**修補動作**：
1. `references/02` 明文寫死 `dim_session` 的切割規則（四條，缺一不可）：inactivity 30 分鐘、跨 `biz_date` 強制切（與 D2/D9 一致）、`utm_*` 任一參數變更時切、`is_bot` 事件不參與 session 化（與 D12 串接）。
2. `dim_session` 存 `session_def_version`，規則變更時遞增，並在 `log_measurement_change`（D11）記一列。
3. **報告與儀表板的所有 session 類指標強制加註**「本報告 session 採自訂定義（v1），與 GA4 介面數字不可直接比較」。這一條進 `verify_outputs.py` 的檢查清單。
4. S2 的體檢報告加一項：自算 sessions 與平台介面 sessions 的落差百分比，>10% 要在 S2 卡點說明原因（通常是 campaign 切割與 bot 過濾）。

---

### D15　identity 的兩個時間面向：匿名縫合會回溯改寫歸因；合併事件本身會讓「活躍會員數」說謊

**現況**：G1 已經覆蓋「同一顧客兩張卡 → 被算成兩個低頻顧客」以及三種比對策略，這部分不重複。**G1 沒有覆蓋的是 identity 的時間維度**：`map_identity` 在藍圖裡沒有任何時間欄位。

**會怎麼出錯**——兩個情境：

- **匿名 → 已知的縫合會回溯改寫上層漏斗**【示意】（任務點名的跨裝置）：使用者先在手機上看展示廣告、匿名瀏覽 5 天，第 6 天在桌機登入購買。若 `user_id` 只在登入後存在、且沒有 `anonymous_id ↔ user_id` 的縫合，前 5 天的觸點全部歸「Direct / (none)」→ 展示廣告的功勞被完全抹掉 → 「展示廣告零轉換，建議砍掉全部預算 NT$180,000/月」→ 砍掉的是上層漏斗。反向也會錯：**縫合窗口開太大**（例如 180 天）會把很久以前的匿名行為都算進來，讓上層通路功勞虛胖。
- **合併事件讓時間序列指標跳動**【示意】：一次資料清理把 40 對重複會員合併。合併後「活躍會員數」從 5,240 降到 5,200（−0.8%），而該月的 CRM 報告寫「活躍會員數連續兩個月下滑」→ 啟動一筆挽回預算。真實原因是 identity 版本變了。**指標的分母被悄悄重新定義，而沒有任何機制記錄它。**

**修補動作**：
1. `map_identity` 新增 `valid_from` / `valid_to` / `merge_event_id` / `merge_method`（`exact` / `rule` / `probabilistic`）/ `confidence` / `reviewed_by`。機率式比對的結果**必須**帶 confidence 並有人工抽驗紀錄（G1 已要求抽驗，這裡是把它變成欄位）。
2. `map_identity` 加 `anonymous_id` ↔ `user_id` 的 stitching，並明訂**縫合回溯窗口**（建議 30 天）寫進指標字典。報告標明「可縫合率 X%」。
3. **每次 identity 合併要輸出影響量報告**（進 S3 清理日誌與異動清單）：本次合併影響 N 位顧客、M 筆交易、活躍會員數變動 ±X、受影響顧客的 RFM 分群移動矩陣。
4. 指標一律標「以 identity 版本 vN 計算」。跨期比較若橫跨合併事件，在 `log_measurement_change`（D11）記一列並在趨勢圖畫斷線——**與 D11 用同一個機制**，因為 identity 合併本質上就是量測定義變更。

---

### D16　迴歸測試的基準資料集過於乾淨，會給出假的安全感

**現況**：藍圖 §8 寫「P1–P3 用課程資料集當驗收標的，因為它有已知正確答案。**這是這個專案最幸運的地方 —— 我們有 ground truth**」。這句話對「公式算對了」成立，對「資料品質邏輯正確」**完全不成立**，而藍圖沒有區分這兩件事。

**這份資料集的實測乾淨程度**（全部來自 `marketing_datasets_profile.md`【實測】）：

| 品質面向 | 實測結果 | 意味著 |
|---|---|---|
| 負值 / 零值金額 | **0 筆** | 退貨/沖銷邏輯無法被測試 |
| 整列重複 | **0 筆** | 去重邏輯無法被測試 |
| 參照完整性孤兒 | **0 筆**（三個方向全 0） | 孤兒鍵處理無法被測試 |
| 缺月 | **0 個**（24 個完整月） | 完整度斷言無法被測試 |
| 全形半形混用 / 多餘空白 | **0 筆** | 編碼正規化無法被測試 |
| 幣別 | 單一（TWD，且無欄位） | 多幣別邏輯無法被測試 |
| 時區 | 無（純日期） | 時區邏輯無法被測試 |
| 主鍵重複 | **0 筆** | grain 斷言無法被測試 |

**會怎麼出錯**【示意】：按 D8 的分析，`05_指標公式庫` 的 RFM SQL 沒有 `txn_type` 過濾。`tests/test_metrics.py` 對課程資料集跑，客戶 89 得 R=19/F=85/M=150,681，**全綠**。上線套到真實 CRM 資料，退貨列被當成 sale：R 被退貨日污染、F 虛胖。綠燈給了「這支腳本正確」的錯誤信心，而那個綠燈在結構上永遠不可能變紅。

**修補動作**：
1. 新增 `tests/fixtures/dirty_mini.parquet`（約 200 列，手工構造，附一份 `dirty_mini_expected.yml` 寫明每個缺陷應被哪一條檢查抓到）。刻意植入至少十種缺陷：退貨列（負金額 + `txn_type='return'` + 遠離最後購買日）、換貨對、整列重複、孤兒外鍵、`9999` 哨兵、Excel 樞紐 `Grand Total` 列、同一人兩張卡（含同開卡日同額度的疑似補發，見 D21）、跨時區時間戳、測試交易（金額 1 元 + `member_id='TEST'`）、缺三天的日期序列、多幣別 spend 列、大小寫不一致的 UTM。
2. **測試改成雙向斷言**：`test_metrics.py` 對課程資料集斷言「數字等於基準值」（現況，保留）；新增 `test_quality_gates.py` 對 dirty fixture 斷言「每一條檢查都**確實抓到**它該抓的缺陷」——也就是測試檢查器本身，不只測試指標。
3. `references/05` 的驗證基準值表要加一列註記：**「本基準資料集無退貨、無重複、無孤兒、無多幣別、無時區，因此 `test_metrics.py` 全綠不代表退貨/去重/孤兒/幣別/時區邏輯正確；那些邏輯由 `test_quality_gates.py` 對 dirty fixture 驗證。」** 不寫這一行，半年後的自己一定會誤信綠燈。

---

### D17　型別轉換靜默變 NULL；金額用 DOUBLE 累加

**現況**：research/01 建議「raw 層一律存 VARCHAR，型別轉換全部延到 staging」，這個策略正確。但**沒有任何機制檢查 cast 有沒有靜默失敗**。DuckDB 的 `TRY_CAST` 失敗回 NULL 不報錯，而一旦有人為了讓 pipeline 跑過去而加了 `TRY_CAST`，錯誤就永久沉默。

**會怎麼出錯**【示意】：POS 匯出的金額欄含千分位（`1,234`）與貨幣符號（`NT$1,234`）。`TRY_CAST(amount AS DECIMAL)` → 全部 NULL。某家門市（用了不同版本的匯出工具）整月營收 `SUM` 得 0 → 分店排名最後一名 → 「該店營收為零，建議評估收店」。**極端案例容易被發現，但只有 3% 的列失敗時（例如只有大額交易才有千分位）就完全不會被發現**：該店營收少 18%，剛好落在「表現不佳」而非「明顯異常」的區間。

第二個面向：金額用 `DOUBLE` 累加千萬列會產生浮點誤差，與財務對帳永遠差幾元到幾十元，每次都要花時間確認「這是浮點誤差還是真的漏了資料」。

**修補動作**：
1. **金額型別硬規則**：`DECIMAL(18,4)`，禁止 `DOUBLE`/`FLOAT`。寫進 references/02 的 DDL 與 references/03 的 SQL 慣例。
2. `sql/checks/stg_*__cast_loss.sql`：對每個做過型別轉換的欄位斷言 **`cast 後的 NULL 數 = cast 前的空字串/NULL 數`**。差值 >0 即 error 並印出前 5 筆無法轉換的原始值。這一條 SQL 是本文所有修補動作裡投報率最高的一條——十行 SQL，擋住整類靜默錯誤。
3. staging 的數值清理一律顯式：`replace(replace(trim(x), ',', ''), 'NT$', '')::DECIMAL(18,4)`，並把清理規則寫進 `contracts/<source>.yml` 而不是散在 SQL 裡。
4. 禁止在 staging 用裸 `TRY_CAST` 而不配上第 2 條的斷言。這一條放進 SKILL.md 的「絕對不要出現的東西」。

---

### D19　`F` 的多重口徑沒有在欄名與字典裡區分

**現況**：`05_指標公式庫` §一 說「行銷交易資料的分析單位是**天**，不是筆」並要求去重；§二 說「`F` 的口徑：預設**交易筆數**（去重前的原始筆數）」；§八 的 ground truth 是 F=85（筆數），而 profile 明確指出「若誤用消費天數，客戶 89 會得到 68 而非 85」【實測】。**三種粒度（筆 / 天 / 品項）在同一份文件裡並存，而輸出的欄名都叫 `F`。** G10 要求「指標口徑要有單一真相」，但 G10 的解法是「加一張字典表 + 圖表下方標註」——它沒有解決**欄名本身不帶口徑資訊**這件事。

**會怎麼出錯**【實測數字】：分析師拿 `feat_rfm.F`（=85，筆數）算客單價：150,681 / 85 = **1,773**。但顧客實際「每次來店」的客單價是 150,681 / 68（消費天數）= **2,216**，差 **25%**。用 1,773 訂「把客單價從 1,773 提升到 2,000」的目標 → 這個目標其實早就達成了。更糟的是把 `F`（筆數口徑，85）與 CAI 的間隔數（天口徑，67 個間隔）放進同一個迴歸當自變數，兩者測的是不同東西但高度相關 → VIF 爆掉或係數符號反轉，而診斷不會告訴你成因是口徑混用。

**修補動作**：
1. **欄名強制帶口徑後綴**，禁止裸 `F` / `M`：`f_txn_cnt`（交易筆數）、`f_active_days`（消費天數）、`f_item_cnt`（品項數）、`m_gross_twd`、`m_net_twd`。同理 `r_days_since_last_sale`。
2. `templates/metric_definitions.csv` 每一列必填 `grain`（`txn` / `customer_day` / `item`）、`unit`、`filter`（例如 `txn_type='sale'`）、`as_of_basis`。沒填不准進 `build_features.py`（沿用 references/05 §九「沒有基準值的指標不准進」的同一條紀律）。
3. `sql/checks/feat__grain_sanity.sql`：斷言 `f_active_days <= f_txn_cnt`、`f_txn_cnt <= f_item_cnt`。違反代表口徑或去重出錯，這三個不等式恆成立，是免費的正確性檢查。
4. `references/05` §一與 §二之間要補一段明寫：**「§一 的去重只用於間隔型指標（λ/MLE/WMLE/CAI），不用於 F。兩者是不同的 feature table，欄名必須可區分。」** 目前這兩節並置但沒有講清楚適用範圍，是誤用的直接來源。

---

### D20　可重現性：交付物沒有釘住 snapshot，且 `expire_snapshots` 與「半年後能重跑」直接衝突

**現況**：S8 要求「環境快照與資料指紋（列數／checksum），確保半年後能重跑出同一份數字」。方向對，但有兩個洞：

1. **指紋只在 S8 記錄，不在交付物上**。報告裡的「Champions 20 人、營收占比 48.6%」【實測】沒有綁到任何版本識別。
2. **與定案文件衝突**：定案 §2 把 mart 定為 DuckLake；research/01 §4.4 引用官方明述「DuckLake **never deletes old data files**」並建議定期 `expire_snapshots` + cleanup「否則磁碟會被吃光」。**一旦 expire 了被報告引用的 snapshot，S8 承諾的「半年後重跑出同一份數字」就是空話。** 兩份定案文件各自都對，放在一起互相拆台，而沒有人注意到。

**會怎麼出錯**【示意】：報告寫「Champions 20 人、營收占比 48.6%」。兩週後主管要求重跑，得到「19 人、47.2%」。期間發生了三件事：補載了兩天遲到的 POS 資料（D13）、修了一條退貨規則（D8）、Meta 回填改了 7 月的 spend（D4）。**沒有任何機制能說出是哪一項造成 1.4 個百分點的差異**，於是結論變成「這套系統的數字會漂」，此後每一個數字都要被重新質疑。

**修補動作**：
1. **每份交付物的 header 埋版本三件套**：`run_id`、`ducklake_snapshot_id`（每張輸入表）、`git_commit`。HTML 報告放在頁尾與 HTML 註解，Excel 放在一個 `_meta` 工作表，儀表板放在頁腳。
2. `_log/run_manifest.json` 記錄每次執行：`run_id`、時間、git commit、套件版本、每張輸入表的 `(snapshot_id, row_count, sum(金額欄))` 指紋、用的 `metric_definitions` 版本、產出的檔案清單與其 hash。
3. **snapshot 保留政策**（解上面的衝突）：任何被 `run_manifest.json` 引用過的 snapshot 加入 `protected_snapshots` 清單，`expire_snapshots` 的維護腳本一律排除它們。這條要寫進 references/03，並在 `scripts/` 放一支 `maintain_ducklake.py` 把「protected 清單 → expire 參數」的邏輯固定下來，不要靠人記得。
4. 新增 `scripts/diff_runs.py`：比對兩個 `run_id` 的指標差異，並**自動歸因**到「輸入資料變動」（snapshot_id 或指紋不同）vs「程式邏輯變動」（git commit 不同）vs「口徑變動」（字典版本不同）。research/01 §7.5 已經給了 `ducklake_table_insertions/deletions(...)`，直接接上就能列出「哪幾列變了」——這是現成的能力，只是沒有人把它包成工具。
5. `run_sql.py` runner 加 research/01 §7.4 的 **idempotency 自我檢查**（跑兩次結果應相同）。SKILL.md 的 S3 目前完全沒有 idempotency 這個詞，只寫「可重跑、可 diff」——那是願望，不是檢查。**並且要加強：除了「連跑兩次」，還要測「上游刪一列後重跑」**，因為 `MERGE INTO` 只 upsert 不刪除，上游硬刪的列會在 mart 變成幽靈資料（電商取消訂單若上游直接刪列，mart 會累積 3% 的幽靈訂單 → 月營收高估 3%、被取消訂單的顧客一直留在 Champions 名單裡拿 VIP 禮）。對「上游會硬刪」的來源改用分區全量取代，或加 `sql/checks/mart__orphan_vs_staging.sql` 比對 key 集合差異。

---

### D21　卡片補發／重製未偵測；`card_id` 被當成顧客單位

**現況**：G1 講「同一顧客兩張卡」的**橫向**問題（兩張並存的卡）。它沒有講**縱向**問題：卡片遺失補發、換卡、卡號變更（任務點名）。而課程資料集裡就有直接證據【實測，profile §2.5.6】：客戶 3359 有信用卡 1893 與 19739，**開卡日同為 1994-06-22、到期日同為 2002-06-30、額度同為 195,000、卡等同為普卡**；客戶 3368 有 27175 與 27645，**開卡日同為 2000-07-31、額度同為 100,000**。這兩組高度像是補發或資料重製，而 profile 只把它們算進「237 張卡」。

**會怎麼出錯**【實測數字】：交易檔同時有 `信用卡ID` 與 `客戶ID` 兩欄，而 `信用卡ID` 的相異值是 **130**、`客戶ID` 是 **100**。任何一時手快用 `信用卡ID` 當顧客單位算 RFM，就會得到 130 個「顧客」而不是 100 個，每個人的 F 被拆散（實測：持有 ≥2 張卡的 68 位客戶中有 44 位只動用 1 張，但那 44 位裡若有補發卡的舊卡有交易，就會被拆）。結果：「睡卡活化」名單把補發卡的**舊卡號**列為需要挽回的休眠卡 → 挽回 DM 寄到一個已註銷的卡號 → 該筆行銷成本 100% 浪費，而且顧客會收到一封提到自己舊卡的信（觀感問題）。

**修補動作**：
1. **references/02 硬規則**：顧客單位一律是 `customer_id`（或 `map_identity` 解析後的 `person_key`）。`card_id` / `device_id` / `member_card_no` 只能當**通路或工具維度**，不得當分析主體。這條進 SKILL.md 的「絕對不要出現的東西」。
2. `sql/checks/dim_card__suspected_reissue.sql`：同一 `customer_id` 底下若有多張卡的 `(開卡日, 到期日, 額度, 卡等)` 完全相同，或開卡日相同且額度相同 → 標為 `SUSPECTED_REISSUE`，列為 S2 卡點的人工判定項（不自動合併，因為也可能是真的兩張同時核發的卡）。
3. 卡片維度用 SCD2（與 D7 同一機制），`card_group_id` 串接補發前後的卡號，讓「這張卡的生命週期」可以跨卡號追蹤。
4. 有效持卡數的計算一律加 `到期日 >= 基準日`（profile §2.5.6 實測：14 張卡在基準日已過期但仍列在持卡檔），並排除額度為 0 的停用卡（1 張，且會造成除零，見 D10）。

---

### D22　POS 測試交易與員工交易未排除

**現況**：`測試交易` 全庫零命中。而 profile 的評註「本檔無負值、無零值 → 不含退貨」很容易讓人推論「金額欄很乾淨」，反而降低了警覺。

**會怎麼出錯**【示意】：新門市開幕前 POS 測試、收銀員教學交易、以及店員自購。典型型態：金額 1 元、同一分鐘同一 terminal 連續 30 筆、`member_id` 為 `TEST` / `0000000` / 店長本人的會員號。若不排除，開幕月的分析得「新店首月客單價 87 元、交易筆數 4,200 筆」（實際客單價 340 元、有效交易 1,050 筆）→ 結論「該商圈客單價明顯偏低，建議調降商品結構往低價帶」→ 把一家其實客單價正常的新店改成低價店型。同一機制也會污染「單日交易筆數」的 p99.9 門檻（D12 的 bot 規則、D13 的完整度斷言都會被它拉歪）。

**修補動作**：
1. `sql/checks/pos__test_txn.sql` 規則庫（規則值放 `contracts/pos_test_rules.yml`）：金額 ≤ 門檻（預設 10 元）、`member_id` 在測試名單、`terminal_id` 屬測試機清單、交易日 < 該門市 `open_date`（來自 D7 的 `dim_store`）、同 terminal 同分鐘筆數 > p99.9、同一 `member_id` 為店內員工（需 HR 對照或人工名單）。
2. **移到 `_quarantine/` 而不是直接刪**，並在 S3 清理日誌與異動清單列出筆數、金額、涉及門市。這與 D12 的「標記不刪」是同一條紀律。
3. 開幕月分析一律排除 `open_date` 前 3 天與 `open_date` 當日（開幕活動的行為不代表常態），並在報告明寫排除規則。

---

## 4. nice-to-have

### N1　Parquet 分割策略被藍圖寫死成月分割，未依查詢模式與 100 MB 門檻決定

藍圖 §S3 的目錄示範是 `stg_transaction/dt=2026-07/part-0.parquet`，`fact_transaction` 標「依年月 partition」。research/01 §4.2 的判準是「用**查詢模式**決定，不是用資料量決定」，且引用官方 Bestpractice「至少 100 MB 每 partition」，並明確給出「資料總量 < 幾百 MB → **完全不要分區**」。CRM 交易百萬列約 200 MB/年，研究的建議是**不分區單一 Parquet**。

**會怎麼出錯**：課程資料集 7,764 列若按年月分割 → 24 個分區、每個約 30 KB。加上研究引用的官方細節「one file is written per thread to each directory」，8 核心會在每個目錄產生最多 8 個檔 → 最多 192 個小檔。而 raw 讀取又被建議一律加 `union_by_name = true`（需讀所有檔案的 metadata 才能建立聯集 schema）→ 查詢規劃時間可能超過實際掃描時間。這不會產出錯誤數字，只會慢並讓 Windows 上的檔案管理變痛，所以是 nice-to-have。

**修補動作**：references/03 寫成**決策表**而非固定值，直接搬 research/01 §3.3 的四列建議（CRM 不分區 / 廣告不分區 / POS `year=/month=` / web `year=/month=/day=`，且明寫「不要用 `hour=`」），並要求 S3 回報時說明「本專案為什麼選這個粒度」。同時把命名規約（全小寫底線、partition value 純 ASCII、日期用 `YYYY-MM-DD` 或 `year=/month=/day=`）從 research/01 §3.2 完整搬進 references/03——包括「**中文絕對不要出現在資料夾名或 partition value**」這一條，因為教材的欄名全是中文（`客戶ID`、`刷卡金額`、`刷卡產品產業分類`），而專案根目錄本身就是 `E:\Projects\行銷分析\`，這個習慣很容易延伸到 partition value（`store=台北信義店`）。附帶：staging 一律把欄名映射成 snake_case ASCII，中文顯示名放 `dim_column_label` 供報告輸出——否則 `smf.ols('刷卡金額 ~ 年齡')` 這種 formula 會在 patsy 的識別字解析上出問題。

### N2　純 SQL runner 放棄了 lineage，但沒有補一個最小替代品

research/01 §8.3 誠實列出「不用 dbt 你放棄了什麼」，第一項就是 `ref()` 的自動 lineage，§8.4 的升級訊號 1 是「改一個 model 要想 10 秒才知道會影響誰（lineage 認知超載）」。以單人專案而論這個取捨正確（定案文件的判斷我同意），但完全空白也不必要。

**修補動作**：一支約 80 行的 `scripts/build_lineage.py`——正則掃 `sql/**/*.sql` 的 `FROM` / `JOIN` / `CREATE OR REPLACE TABLE`，輸出 Mermaid DAG 存到 `_log/lineage.md`，並附一個 `--impact <table>` 參數列出下游受影響的 SQL 檔。它同時解決 research/01 §8.4 的升級訊號 1（延後升級 SQLMesh 的時機）與 D20 的「這個數字從哪來」。純字串解析會漏 CTE 與動態 SQL，但對一個人的專案夠用。

---

## 5. 對藍圖與 Skill 的更正建議（詳見結構化輸出 `blueprint_corrections`）

摘要 11 條，其中三條我認為必須在動筆寫 references 之前處理：

- **最重要**：`05_指標公式庫` §4.2 的 MLE 公式分母寫成 `n_i`，與同文件 §4.1 的 `n_i − 1`、以及已驗證的 SQL `AVG(interval_days)` 相矛盾。這是 E8（公式抄錯）發生在號稱單一真相的公式庫裡。
- **最有價值**：`marketing_datasets_profile.md` 有九處「Skill 的 ingest 應該…」的實測建議，references/07 的 G 系列一條都沒收。這些是包子自己檔案上驗出來的規則，比任何通用清單值錢。
- **最會擋住工作**：SKILL.md 的「開工前務必先讀」點名 references/01/02/04，但磁碟上只有 05 與 07。Skill 一被觸發就會讀不到檔。

---

> 審查者註：本文刻意不涵蓋統計推論與商業轉譯視角（另有兩份缺口分析）。凡我認為現有覆蓋已足夠的地方，我沒有硬湊條目——具體來說，**DuckDB / Parquet 的引擎層地雷（research/01 §10 與 T6–T9）、套件生死判斷（T4/T5）、以及 raw 層全 VARCHAR + 品質檢查分層（research/01 §6）這三塊我認為已經寫得很好，沒有實質缺口**，本文只在需要接上它們時引用。
