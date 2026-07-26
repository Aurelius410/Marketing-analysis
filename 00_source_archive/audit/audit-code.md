# 對抗式審查 — 程式碼與 SQL 可執行性

審查對象：`skill/行銷數據分析/` 的 SKILL.md、CLAUDE.md、21 份 references，以及 `templates/sql/`、`templates/迴歸建模_程式範本.py`、`scripts/`。

**審查方法（都是實跑，不是目視）**

| 動作 | 結果 |
|---|---|
| 抽出全部 fenced code block | 224 塊（python 74、sql 30、yaml 6、bash/powershell 5、其餘為文字圖） |
| `ast.parse` 全部 python block | **0 個語法錯誤** |
| `duckdb.extract_statements` 全部 sql block | 5 塊解析失敗，其中 4 塊是刻意省略的片段（`SELECT ... FROM ...`、`<grain_cols>` 佔位），1 塊（`templates/sql/*`）是真問題 |
| 用 02 §三的 DDL 在 DuckDB 1.5.5 建出 19 張表，再把各 reference 的 SQL 丟進去 bind／執行 | 見下列發現 |
| `yaml.safe_load` 全部 yaml block 與 templates 下的 .yml/.json/.py | 1 塊 yaml 不合法（15），templates 檔案全部合法 |
| 收集全部 import，逐一 `importlib.util.find_spec` 並比對 requirements.txt | 找到 1 個未列入 requirements 的套件、1 個不存在的自家模組 |
| 實際安裝 altair 到暫存目錄跑 `alt.theme.register` 兩種寫法 | 確認一種會 TypeError |
| 實際載入 ducklake extension 跑 `expire_snapshots` | 確認函式名錯 |

環境：Python 3.14.1 / duckdb 1.5.5 / pandas 2.3.3 / statsmodels 0.14.6 / scikit-learn 1.7.2 / scipy 1.16.3。

---

## critical

### C1. `02_資料模型規格.md` §五 的 `m_net_twd` SQL 與同節數學式互相矛盾，而 DDL 從未宣告退貨列的正負號

**位置**：`references/02_資料模型規格.md` L556（數學式）與 L571–580（SQL）

**原文**

L556：
$$M_i^{\text{net}} = \sum_{t:\ \texttt{sale}} a_t \;-\; \sum_{t:\ \texttt{return}} |a_t| \;+\; \Big(\sum_{t:\ \texttt{exchange\_in}} a_t - \sum_{t:\ \texttt{exchange\_out}} |a_t|\Big)$$

L574–577：
```sql
    SUM(CASE WHEN txn_type IN ('return','exchange_out') THEN amount_twd ELSE 0 END) AS m_return_twd,
    SUM(CASE WHEN txn_type IN ('sale','return','exchange_in','exchange_out')
             THEN amount_twd ELSE 0 END)                                   AS m_net_twd
```

**錯在哪**

數學式明寫「減去 |a_t|」，SQL 卻是四種 txn_type 直接相加。兩者只有在「退貨列的 `amount_twd` 一律存負值」時才等價，但整份 DDL（L235 `amount_twd DECIMAL(18,4) NOT NULL`）、§五的表（L548–554 只寫「減」「抵銷」）、以及全 references 都沒有任何一句宣告這個正負號約定（`grep -rn "exchange_out"` 全庫只有 4 個命中，沒有一處講正負號）。POS 匯出「金額為正 + txn_type 旗標」是常見形式，而 §八 L697 又說超市檔是「43 筆為負＝退貨」——兩種都在文件裡出現過。

**怎麼確認**：在 DuckDB 建一張同欄位的表，插入 `('p1','sale',1000)` 與 `('p1','return',300)`（退貨存正值），跑 §五 那段 SQL：

```
§五 SQL result: [('p1', Decimal('1000.0000'), Decimal('300.0000'), Decimal('1300.0000'))]
§五 math formula  M_net = 1000 - |300| = 700
```

`m_net_twd` 得到 **1300**，正解是 **700**，虛胖 86%。而且 `m_return_twd` 欄在「存負值」的約定下會是負數，欄名卻叫「退貨金額」。無論哪種約定，這兩欄至少有一欄是錯的，且完全不報錯。這正是 §五 自己要防的 18-G2。

**怎麼修**

1. 在 3.3 的 DDL 加一行約定與 CHECK：
   ```sql
   amount_twd DECIMAL(18,4) NOT NULL,   -- 符號約定：return / exchange_out 一律存負值
   CHECK ( (txn_type IN ('return','exchange_out') AND amount_twd <= 0)
        OR (txn_type IN ('sale','exchange_in')    AND amount_twd >= 0)
        OR  txn_type = 'void' )
   ```
2. 把 SQL 改成不依賴符號、與數學式一字對應：
   ```sql
   SUM(CASE WHEN txn_type = 'sale'          THEN amount_twd ELSE 0 END)  AS m_gross_twd,
   SUM(CASE WHEN txn_type IN ('return','exchange_out') THEN ABS(amount_twd) ELSE 0 END) AS m_return_twd,
   SUM(CASE WHEN txn_type IN ('sale','exchange_in')    THEN ABS(amount_twd)
            WHEN txn_type IN ('return','exchange_out') THEN -ABS(amount_twd)
            ELSE 0 END)                                                  AS m_net_twd
   ```
3. 這條同時要寫進 `dim_metric_definition` 與 `references/17 §二`（02 §九 第 4 條本來就要求兩份同步）。

---

### C2. `06_前處理與轉換.md` 的匯率換算 view 會靜默產出未換匯的 `amount_twd`

**位置**：`references/06_前處理與轉換.md` L542–550（view `stg_transaction_twd`）

**原文**（L542–545）
```sql
CREATE OR REPLACE VIEW stg_transaction_twd AS
SELECT t.*,
       t.amount * COALESCE(fx.rate, 1.0) AS amount_twd,
       CASE WHEN t.currency <> 'TWD' AND fx.rate IS NULL
            THEN 'ERROR: fx rate missing' END AS fx_flag   -- 缺匯率要擋，不可靜默補 1.0
```

**錯在哪**（兩個獨立的靜默錯誤）

1. **註解說「不可靜默補 1.0」，程式碼寫的正是 `COALESCE(fx.rate, 1.0)`**。缺匯率時 `amount_twd = amount × 1.0`，也就是把 USD 3,200 當 NT$3,200 —— 02 §一 L5 用來論證這張表存在必要性的那個「ROAS 從 1.18 算成 37.5」案例，被這行 SQL 原封不動重現。`fx_flag` 只是旁邊多一欄，不會擋住任何下游查詢。
2. **`SELECT t.*` 已經帶出 `fact_transaction.amount_twd`（02 DDL L235），再 alias 一個同名欄會撞名**。DuckDB 不報錯，而是把新算的那欄自動改名成 `amount_twd_1`：

   ```
   duplicate amount_twd? ['amount_twd', 'amount_twd_1']
   ```

   於是下游 `SELECT amount_twd FROM stg_transaction_twd` 拿到的是**原始未換匯的那一欄**，換匯結果被藏在 `amount_twd_1` 裡沒人用。全程零警告。

**怎麼確認**：把 02 §三的 DDL 全部建起來，再把這個 view 的欄名改對後建立，`DESCRIBE` 出來就是上面那兩欄。

**怎麼修**
```sql
CREATE OR REPLACE VIEW stg_transaction_twd AS
SELECT t.* EXCLUDE (amount_twd),
       t.line_amount_net * fx.rate_to_twd AS amount_twd,   -- 不 COALESCE，缺就是 NULL
       (t.currency <> 'TWD' AND fx.rate_to_twd IS NULL) AS fx_missing
FROM fact_transaction t
LEFT JOIN dim_fx_rate fx
       ON fx.currency = t.currency AND fx.rate_date = t.biz_date AND fx.rate_type = 'daily';
```
並在 `sql/checks/` 加一條斷言 `SELECT count(*) FROM stg_transaction_twd WHERE fx_missing`，非 0 即 error —— 「擋」要靠 check SQL，不能靠一個沒人讀的欄位。

---

## important

### I1. `06` 重新定義 `dim_fx_rate`，schema 與 02 §3.7 完全不同，而且用 `IF NOT EXISTS` 讓衝突靜默

**位置**：`references/06_前處理與轉換.md` L531–539

**原文**（L531–532）
```sql
-- 02_資料模型規格.md 的維度表，M3 之前必須建好
CREATE TABLE IF NOT EXISTS dim_fx_rate (
    from_ccy   VARCHAR NOT NULL,      -- 'JPY'
    to_ccy     VARCHAR NOT NULL,      -- 'TWD'（報告幣別，寫進專案核心.md）
```

**錯在哪**：02 §3.7 L436–441 的 `dim_fx_rate` 是 `(rate_date, currency, rate_to_twd, rate_type, source)`，PK 是 `(rate_date, currency, rate_type)`；06 這張是 `(from_ccy, to_ccy, rate_date, rate, rate_type, src)`。註解卻宣稱它就是 02 那張表。`rate_type` 的允許值也不同（02：`daily/period_avg/period_end`；06：`daily_close/month_avg/budget_fixed`），而下面的 view 又寫死 `fx.rate_type = 'daily_close'` —— 對著 02 的資料永遠 join 不到任何一列。

**怎麼確認**：先跑 02 的全部 DDL，再跑 06 這一塊：
```
OK   -- 02_資料模型規格.md 的維度表，M3 之前必須建好      ← IF NOT EXISTS 靜默 no-op
FAIL  | BinderException Binder Error: Table "fx" does not have a column named "from_ccy"
after IF NOT EXISTS, dim_fx_rate cols: ['rate_date','currency','rate_to_twd','rate_type','source']
```

**怎麼修**：刪掉 06 的 `CREATE TABLE`，改成一行「見 02 §3.7，不在此重複定義」；view 一律用 02 的欄名（`currency` / `rate_to_twd` / `rate_type='daily'`）。02 §九 的維護表要加一列：「06 §五的 fx view 隨 02 §3.7 一起改」。

---

### I2. `06` 的 fx view 用了 `fact_transaction` 上不存在的欄

**位置**：`references/06_前處理與轉換.md` L544、L550

**原文**：`t.amount * COALESCE(fx.rate, 1.0)`、`AND fx.rate_date = t.txn_date`

**錯在哪**：02 DDL 的 `fact_transaction` 沒有 `amount`（只有 `unit_price` / `line_amount_gross` / `line_amount_net` / `amount_twd`），也沒有 `txn_date`（只有 `event_ts_utc` / `event_ts_local` / `biz_date`）。而且 02 §四 L498 明訂 `biz_date` 是「唯一允許 join `dim_date` 的欄」。

**怎麼確認**：對著 02 的 DDL 建這個 view：
```
FAIL: BinderException Binder Error: Table "t" does not have a column named "txn_date"
```

**怎麼修**：`t.amount` → `t.line_amount_net`，`t.txn_date` → `t.biz_date`。

---

### I3. `17_指標公式庫.md` §二的 RFM 評分 SQL 引用了自己上一段沒產出的欄名

**位置**：`references/17_指標公式庫.md` L72–77

**原文**
```sql
SELECT cust_id,
    6 - NTILE(5) OVER (ORDER BY R ASC)  AS R_score,   -- R 小 → 分數高
    NTILE(5) OVER (ORDER BY F ASC)      AS F_score,
    NTILE(5) OVER (ORDER BY M ASC)      AS M_score
FROM feat_rfm;
```

**錯在哪**：同一份文件 L40–50 建的 `feat_rfm` 欄位是 `cust_id, r_days_since_last_sale, f_txn_cnt, f_active_days, m_net_twd`，沒有 `R`/`F`/`M` 這三欄。而且 `F` 到底是 `f_txn_cnt` 還是 `f_active_days`，這段 SQL 迴避了 L45 自己強調的「兩者並存不可混用」。

**怎麼確認**：照 L40–50 建一張 `feat_rfm`，跑 L72–77：
```
FAIL: BinderException Binder Error: Referenced column "R" not found in FROM clause!
```

**怎麼修**
```sql
SELECT cust_id,
    6 - NTILE(5) OVER (ORDER BY r_days_since_last_sale ASC) AS r_score,
    NTILE(5) OVER (ORDER BY f_active_days ASC)              AS f_score,  -- 口徑二選一，寫進指標字典
    NTILE(5) OVER (ORDER BY m_net_twd ASC)                  AS m_score
FROM feat_rfm;
```

---

### I4. 三份文件對同一張交易表用了三套欄名／表名，02 §九 要求同步卻沒同步

**位置**：`references/17_指標公式庫.md` L40–50、`references/03_倉儲與檔案結構.md` L204 與 L359–389、`references/02_資料模型規格.md` L210–248

**原文**

17 L44–49：
```sql
    SUM(amount)                                         AS m_net_twd
FROM fact_transaction
WHERE txn_date <= DATE '2012-12-01'      -- as_of_date 防洩漏，不可省
```

03 L204：
```
| `fct_` | mart 事實 | `fct_transaction`、`fct_marketing_spend` | 表註解第一行 |
```

03 L372：`FROM fct_transaction`

**錯在哪**：02 的 DDL 建的是 `fact_transaction`（欄位 `person_key` / `biz_date` / `amount_twd`）；03 的命名規約說 mart 事實表前綴是 `fct_`，自己的 `feat_rfm.sql` 也讀 `fct_transaction`（欄位 `customer_id`）；17 讀 `fact_transaction` 但欄位是 `cust_id` / `txn_date` / `amount`。02 §九 L755 明寫「`references/17_指標公式庫` 的口徑改了 → 檢查 §五的 `v_txn_for_rfm`…不同步就是靜默錯誤」，但同步只做了 `txn_type='sale'` 過濾，沒做欄名。

**怎麼確認**：對著 02 的 DDL 逐一 bind：
```
17 §2 feat_rfm  → FAIL: Binder Error: Referenced column "txn_date" not found in FROM clause!
03 feat_rfm.sql → FAIL: Catalog Error: Table with name fct_transaction does not exist!
```

**怎麼修**：選一套（建議照 02，因為那是 DDL 的權威）並全庫替換：表名 `fact_transaction`、鍵 `person_key`、日期 `biz_date`、金額 `amount_twd`。若真要保留 `fct_` 前綴給 mart 層，就在 02 §三加一句「本節 DDL 為 mart 層，實際表名帶 `fct_` 前綴」，並把 02 的四張 `fact_*` 全部改名。

---

### I5. `10_行銷_購物籃與品類.md` 的品類轉移 SQL 用中文欄名，違反 02 §3.1 自己的硬規則

**位置**：`references/10_行銷_購物籃與品類.md` L188–207

**原文**（L190–195）
```sql
WITH seq AS (                                        -- ① 去重到「顧客-日」，且必須排序
  SELECT DISTINCT 客戶ID, 交易日期, 品類 FROM fact_transaction
),
nxt AS (
  SELECT 客戶ID, 品類 AS A,
         LEAD(品類) OVER (PARTITION BY 客戶ID ORDER BY 交易日期) AS B
```

**錯在哪**：02 §3.1 L151 是硬規則 ——「表名欄名 **全小寫 snake_case ASCII，禁止中文**…partition value 出現中文會炸」。這段直接對 `fact_transaction`（有 DDL 的表）用中文欄名，而且 `fact_transaction` 根本沒有品類欄（品類在 `dim_product.category_l2_*`，要 join）。

另外 SQL 本身有一個重現性問題：`ORDER BY 交易日期` 沒有 tie-break，同一天買多個品類時 `LEAD` 取到誰是未定義的，同一份資料跑兩次可能得到不同的轉移矩陣。

**怎麼確認**：對著 02 的 DDL 跑：
```
FAIL: BinderException Binder Error: Referenced column "客戶ID" not found in FROM clause!
```
（SQL 語法本身沒問題 —— 換成合法欄名後在 DuckDB 1.5.5 執行成功，包含 `SUM(SUM(n)) OVER ()` 這種巢狀彙總。）

**怎麼修**
```sql
WITH seq AS (
  SELECT DISTINCT t.person_key, t.biz_date, p.category_l2_code AS cat
  FROM fact_transaction t JOIN dim_product p ON p.product_key = t.product_key AND p.is_current
  WHERE t.txn_type = 'sale'
),
nxt AS (
  SELECT person_key, cat AS a,
         LEAD(cat) OVER (PARTITION BY person_key ORDER BY biz_date, cat) AS b   -- cat 當 tie-break
  FROM seq
)
```
並在 §此節補一句「同日多品類的排序規則」，否則報表數字不可重現。

---

### I6. 三張表把可為 NULL 的欄放進 PRIMARY KEY，正常資料就插不進去

**位置**：`references/02_資料模型規格.md` L322 + L334、L394 + L399、L445 + L448

**原文**

L322 / L334：
```sql
    creative_key      BIGINT,
    ...
    PRIMARY KEY (platform, account_id, campaign_key, creative_key, report_date, data_as_of_date)
```
L394 / L399：
```sql
    zone_id           VARCHAR,                   -- 店內區域（動線熱圖）
    ...
    PRIMARY KEY (store_key, biz_date, hour_slot, zone_id)
```
L445 / L448：`raw_campaign_pattern VARCHAR,` … `PRIMARY KEY (raw_source, raw_medium, raw_campaign_pattern, valid_from)`

**錯在哪**：這三欄都刻意宣告成可為 NULL（`dim_creative` 是選配、`zone_id` 是「動線熱圖」才有的店內感測、`raw_campaign_pattern` 明顯是選配的 pattern），但 DuckDB 對 PK 欄一律隱含 NOT NULL。結果是最常見的情況（活動層級 spend 無素材拆分、沒有區域感測器的門市、不需要 campaign pattern 的通路對照）直接插不進去。

**怎麼確認**：把 02 §三的 19 張表全部建起來（全部 `CREATE TABLE` 成功），再插入含 NULL 的一列：
```
FAIL insert NULL-in-PK fact_marketing_spend | ConstraintException: NOT NULL constraint failed: fact_marketing_spend.creative_key
FAIL insert NULL-in-PK fact_store_traffic   | ConstraintException: NOT NULL constraint failed: fact_store_traffic.zone_id
FAIL dim_channel_mapping NULL pattern       | ConstraintException: NOT NULL constraint failed: dim_channel_mapping.raw_campaign_pattern
```

**怎麼修**：三個 PK 欄各給一個哨兵預設值並標成 NOT NULL，把「無此維度」顯式化：
```sql
creative_key         BIGINT  NOT NULL DEFAULT 0,     -- 0 = 無素材層拆分
zone_id              VARCHAR NOT NULL DEFAULT '_ALL', -- _ALL = 全店，無區域感測
raw_campaign_pattern VARCHAR NOT NULL DEFAULT '*',    -- * = 不依 campaign 細分
```
（不要改成 UNIQUE 索引，那會讓 NULL 彼此不相等而放進重複列。）

---

### I7. `16` 對 `anova3()` 的呼叫方式與 `08` 的定義不相容，會 TypeError

**位置**：`references/16_統計推論紀律.md` L477，定義在 `references/08_迴歸建模.md` L166

**原文**

08 L166：
```python
def anova3(formula: str, data):
```
16 L477：
```python
res = anova3(model)                      # 強制 C(x, Sum) 編碼
```

**錯在哪**：`anova3` 吃的是「formula 字串 + data」，不是已 fit 的 model。這是同一份 skill 裡對同一支 helper 的兩種簽章。

**怎麼確認**：實作 08 那 6 行，兩種呼叫都跑：
```
--- anova3(formula, data) ---   （正常，輸出 Type III 表，C(grp, Sum) 已生效）
--- 16 §: anova3(model) ---
FAIL: TypeError anova3() missing 1 required positional argument: 'data'
```
（順帶確認 08 的實作本身正確：`re.sub(r"C\((\w+)\)", r"C(\1, Sum)", ...)` 對 `y ~ x1 * C(grp)` 也能正確改寫成 `x1:C(grp, Sum)`；`C(grp, Treatment)` 會如預期 raise。）

**怎麼修**：16 L477 改成 `res = anova3("y ~ x1 + x2 + C(grp)", df)`，或把 08 的 `anova3` 加一個 overload 接受 `RegressionResults`（從 `model.model.formula` / `model.model.data.frame` 取回 formula 與 data 重 fit）。二選一，但兩份文件必須一致。

---

### I8. `scripts/stats_utils.py` 不存在，但 `08` 與 `16` 直接 import 它

**位置**：`references/08_迴歸建模.md` L127、`references/16_統計推論紀律.md` L475（另有 SKILL.md L195 引用）

**原文**

08 L127：
```python
from scripts.stats_utils import plot_lm, vif_table, anova3, emmeans, emm_contrasts
```
16 L475：
```python
from scripts.stats_utils import anova3, posthoc, chi2_safe
```

**錯在哪**：`skill/行銷數據分析/scripts/` 底下只有 `anonymize_pii.py`、`paths.py`、`setup_check.py`。SKILL.md L195 還把它寫成硬規則：「❌ 直接呼叫 `anova_lm(typ=3)` —— 會靜默算錯，用 `scripts/stats_utils.py` 的 `anova3()`」。使用者照做會直接 `ModuleNotFoundError`。

**怎麼確認**：`ls scripts/` 只有那三支；另外掃過全部 code block 的 import，`templates/迴歸建模_程式範本.py` 需要的 7 個名字（`y_profile` / `FAMILY_CALLS` / `psi_hat` / `influence_flags` / `sensitivity` / `backward_aic` / `segment_slope_test`）**全部存在**，只有 `stats_utils` 整支缺席。

**怎麼修**：建 `scripts/stats_utils.py`，至少實作被 import 的 8 個名字（`anova3` / `posthoc` / `chi2_safe` / `plot_lm` / `vif_table` / `emmeans` / `emm_contrasts` / `compare_two_groups`）；在補上之前，把 08 L127 與 16 L475 改成註解說明「待實作」，並把 `setup_check.py` 加一條「stats_utils 是否可 import」的檢查。

---

### I9. `imblearn` 有被 import，但兩份 requirements 都沒有它

**位置**：`references/12_預測建模.md` L256–257

**原文**
```python
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
```

**錯在哪**：`grep -in "imb\|smote\|imbalanced" requirements.txt requirements-causal.txt` 完全沒有命中（exit 1）。掃全庫 import 後，這是唯一「有被 import 但沒被登記」的第三方套件（`shap`、`jieba`、`econml` 都在 requirements 裡，`econml` 也已正確標註 `.venv-causal`）。

**怎麼確認**：上述 grep + `importlib.util.find_spec("imblearn")` 回 None。

**怎麼修**：requirements.txt 的「機器學習與分群」段加 `imbalanced-learn>=0.13   # 只在堅持 SMOTE 時才需要；預設走 scale_pos_weight`。或者，既然 L233 已經寫死「硬規則：`class_weight`/`scale_pos_weight` 優先於 SMOTE」、L243 又論證 SMOTE 在 RFM 這種低維空間會造假樣本，也可以把這 3 行改成純註解範例並標明「需另裝 imbalanced-learn」。

---

### I10. `templates/sql/` 兩支 SQL 都無法執行：`:param` 不是 DuckDB 語法，且引用不存在的欄

**位置**：`templates/sql/growth_decomp.sql` L11–15、`templates/sql/cac_payback.sql` L11、L23

**原文**

growth_decomp.sql L11、L15：
```sql
           SUM(t.amount_twd)          FILTER (WHERE t.biz_date BETWEEN :a_start AND :a_end) AS r_a,
           ...
           MIN(c.first_purchase_date) AS first_dt
```
cac_payback.sql L11、L23：
```sql
           c.acquisition_channel_key                   AS ch,
           ...
           SUM(t.amount_twd * :gross_margin)                                AS gm_twd
```

**錯在哪**（兩件事）

1. DuckDB 具名參數是 `$name`，不是 `:name`。兩支檔案連 parse 都過不了。
2. `dim_customer`（02 §3.2 L157–189）**沒有 `first_purchase_date`，也沒有 `acquisition_channel_key`**。

**怎麼確認**
```
growth_decomp.sql  parse FAIL as-is: Parser Error: syntax error at or near ":"
                   parse OK after :x -> $x
                   BIND/EXEC FAIL: Binder Error: Table "c" does not have a column named "first_purchase_date"
cac_payback.sql    同上
02 dim_customer 欄位：['customer_key','person_key','customer_id','registered_date','name_hash',
                       'address_hash','phone_hash','zip_code','birth_date','gender','education',
                       'occupation','job_title','annual_income_band','housing_type','household_size',
                       'family_lifecycle','leisure_activity','hobby','contact_pref','lifestyle_segment',
                       'personality_trait','channel_pref','member_tier','valid_from','valid_to',
                       'is_current','_source_file','_ingested_at']
```

補一句：把欄補齊之後，`growth_decomp.sql` 的**數學是對的** —— 用合成資料實測，四個桶的 `contrib_twd` 加總 = 150.0 = `rev_b − rev_a`，二階拆解 `eff_freq + eff_ticket + eff_interaction`（−100 + 400 − 200 = 100）也精確等於該桶的 `contrib_twd`。所以這裡要修的只有欄位與參數語法，別動邏輯。

**怎麼修**
1. 全檔 `:x` → `$x`（DuckDB Python 端用 `con.execute(sql, {"a_start": ...})`）。
2. 02 §3.2 的 `dim_customer` 補兩欄（並在 §九 註記為衍生欄、由 `fact_transaction` 回算後物化）：
   ```sql
   first_purchase_date     DATE,      -- Type 1；來源 = MIN(biz_date) WHERE txn_type='sale'
   acquisition_channel_key BIGINT,    -- Type 1；首購那筆的 channel_key
   ```
   或者把兩支 template 改成自己算 first purchase 的 CTE，不依賴維度表。

---

### I11. 全庫的專案子目錄名分兩套，`paths.py` 只建其中一套

**位置**：`references/03_倉儲與檔案結構.md` L30–33、L36–69（宣告）；違反者遍布 15 份 reference

**原文**

03 L30：
> 資料夾名稱**不帶數字編號、用完整名稱**——數字編號在 Excel 分頁上有用（強制排序），在檔案總管裡只會讓你記不住 `05` 是模型還是圖表。

但 13 L94：
```python
df.to_parquet("02_staging/s6_01_segmented.parquet")   # 含原文與斷詞兩欄，可回查
```
05 L331：
```sql
) TO '04_features/feature_check_M2.parquet' (FORMAT parquet, COMPRESSION zstd);
```
14 L443–450：`"06_delivery/insights.md"`、`"06_delivery/sizing.csv"` …

**錯在哪**：`scripts/paths.py` 只建 `原始資料 / 清理後資料 / 分析資料表 / 顧客特徵表 / 圖表 / 交付物 / 專案記憶` 這一套中文目錄（L64–71、L167–185）。而 `00 / 01 / 04 / 05 / 06 / 07 / 09 / 10 / 12 / 13 / 14 / 15 / 16 / 18 / 19` 共 15 份 reference 用的是英文編號目錄，統計出現次數：`04_features/` 14 次、`06_delivery/` 12 次、`05_models/` 10 次、`00_intake/` 9 次、`06_figures/` 7 次、`03_mart/` 6 次、`02_staging/` 6 次、`07_report/` 4 次、`01_raw/` 2 次（`00_source_archive/` 43 次是教材庫，不算）。照抄任何一段都會踩空目錄。

**怎麼確認**：`grep -rhno "0[0-9]_[a-z_]\{3,\}/" references/*.md | sort | uniq -c` 得到上面的次數；`grep -n` 讀 `paths.py` L64–71 / L167–185 確認只建中文目錄；實跑一次 `COPY ... TO '04_features/x.parquet'` 在目錄不存在時：
```
COPY w/o dir FAIL: IOException IO Error: Cannot open file "04_features/feature_check_M2.parquet": 系統找不到指定的路徑。
```

**怎麼修**：定一套（既然 03 是倉儲規格的權威，就用中文那套），把 15 份 reference 裡的路徑字串全部換掉，並且**一律改成走 `paths.py`**：
```python
from paths import project_dir
p = project_dir(PROJECT)
df.to_parquet(p.staging / "s6_01_segmented.parquet")
```
再在 `verify_outputs.py` 加一條 CHECK：「reference 內不得出現 `0N_english/` 形式的硬編路徑」。

---

### I12. 退出碼語意在四個地方互相矛盾

**位置**：`scripts/setup_check.py` L303–308、`references/04_資料體檢.md` L64 與 L250–266、`references/07_標籤與分群.md` L200、`references/20_交付物產製.md` L358

**原文**

setup_check.py L5–8：
```
    0 = 全通過
    1 = 有 error，不能開工
    2 = 只有 warning，能開工但某些模組不可用
```
04 L266：
```python
    sys.exit(gate())          # 0 通過｜1 有 warning｜2 有 error（擋住）｜3 腳本失敗
```
07 L200：
```python
# scripts/kmeans_preflight.py —— 五道關，回傳 exit code 0/1/2（沿用 setup_check 的語意）
```
20 L358：
```python
# 退出碼：0 = 全綠可交付｜1 = 有 error，不得輸出｜2 = 僅 warning，可交付但須登錄異狀檔
```

**錯在哪**：`setup_check.py`（實際程式碼，L303 `return 1` if errors、L306 `return 2` if warnings）與 20 是「1=error、2=warning」；04 是「1=warning、2=error」，剛好相反。07 又宣稱自己「沿用 setup_check 的語意」，但沒有實作可比對。任何 CI wrapper 或 `&&` 串接都會把「有 error 必須擋住」讀成「只是 warning，可以往下」。

**怎麼確認**：讀 `scripts/setup_check.py` L290–310 的 `return` 分支，與 04 L249–263 的 `gate()` 對照。

**怎麼修**：全庫統一成 setup_check 的語意（`0 通過｜1 error 擋住｜2 warning 可往下`），把 04 L64 的 `raise SystemExit(2)` 改成 `raise SystemExit(1)`，L259 的 `return 2` 改 `return 1`、L262 的 `return 1` 改 `return 2`，並把 L266 的註解一起改。這條值得寫進 `00_通則與紀律.md` 當成全 skill 的約定。

---

### I13. `19` 的 Altair 主題註冊有一個會 TypeError

**位置**：`references/19_圖表與統計表規格.md` L640

**原文**
```python
@alt.theme.register("baozi_dark")
def baozi_dark() -> alt.theme.ThemeConfig:
```

**錯在哪**：`alt.theme.register` 的簽章是 `register(name: LiteralString, *, enable: bool)` —— `enable` 是**沒有預設值的 keyword-only 參數**，不能省。L634 的 `@alt.theme.register("baozi_light", enable=True)` 是對的，L640 少了 `enable`。

**怎麼確認**：把 altair 裝進暫存目錄（不動主環境）實跑：
```
altair 6.2.2
OK   enable=True form
FAIL no-enable form | TypeError register() missing 1 required keyword-only argument: 'enable'
```
（順帶：`requirements.txt` 寫 `altair>=5.5`，今天 pip 會裝到 6.2.2，模組路徑已是 `altair.vegalite.v6`。若 19 §的其他寫法有假設 v5，值得一併確認。）

**怎麼修**：`@alt.theme.register("baozi_dark", enable=False)`。

---

### I14. `03` 的 DuckLake 維護腳本呼叫了不存在的函式名

**位置**：`references/03_倉儲與檔案結構.md` L481

**原文**
```python
con.execute(f"CALL mart.expire_snapshots(versions => {expirable})")
con.execute("CALL mart.merge_adjacent_files()")   # 小檔合併，見 W12
```

**錯在哪**：DuckLake 沒有 `<catalog>.expire_snapshots`。正確形式是全域表函式 `ducklake_expire_snapshots('<catalog>', versions => [...])`。旁邊那行 `mart.merge_adjacent_files()` 反而是對的，所以不是「整段都用錯風格」，就是這一行錯。

**怎麼確認**：載入 ducklake extension、ATTACH 一個 lake、實際呼叫：
```
FAIL mart.expire_snapshots | CatalogException: Table Function with name expire_snapshots does not exist!
                             Did you mean "main.ducklake_expire_snapshots"?
OK   mart.merge_adjacent_files
OK   CALL ducklake_expire_snapshots('mart', versions => [1,2])
FAIL CALL mart.ducklake_expire_snapshots(versions => [1,2])
```
（同一塊的 `FROM ducklake_snapshots('mart')` 與 20 L414 的 `SELECT max(snapshot_id) FROM ducklake_snapshots('mart')` 都正確 —— 欄位實測為 `snapshot_id, snapshot_time, schema_version, changes, author, commit_message, commit_extra_info`。）

**怎麼修**
```python
con.execute("CALL ducklake_expire_snapshots('mart', versions => ?)", [expirable])
```
另外 `expirable` 目前包含 snapshot 0（建 schema 那一版），建議明確排除。

---

### I15. `09` 的 `migration_matrix()` 在使用 `states=` 參數時必定 AssertionError，且回傳 object dtype

**位置**：`references/09_行銷_顧客價值.md` L262–270

**原文**
```python
    if normalize == "row":
        row_tot = counts.sum(axis=1)
        prob = counts.div(row_tot.replace(0, pd.NA), axis=0)   # 列總計為 0 → N/A 不填 0
        assert (prob.sum(axis=1).dropna() - 1).abs().max() < 1e-9
```

**錯在哪**：`states=` 這個參數存在的理由就是 L259 的註解「補齊未出現的狀態，避免矩陣不方陣」。一旦補進一個「沒有人從它轉出去」的狀態，那一列 `row_tot = 0` → `replace(0, pd.NA)` → 整個 DataFrame 變成 **object dtype**，該列全部 `<NA>`。接著 `prob.sum(axis=1)` 對全 NA 列回傳的是 **0.0 不是 NaN**（pandas `skipna=True` 的行為），所以 `.dropna()` 不會把它濾掉，`|0 − 1| = 1 > 1e-9` → AssertionError，而錯誤訊息是上一個 assert 的「有人某期沒有被指派狀態」，指向完全無關的原因。

**怎麼確認**：實跑（pandas 2.3.3），3 位顧客 × 3 期、狀態只有 A/B，傳 `states=["A","B","C"]`：
```
--- case1: no empty rows ---   OK
--- case2: states= superset introduces a zero row ---   FAIL AssertionError
```
再拆開看：
```
      A     B     C
A   0.0   1.0   0.0
B   0.0   1.0   0.0
C  <NA>  <NA>  <NA>
dtypes [dtype('O'), dtype('O'), dtype('O')]
row sums: [1.0, 1.0, 0]  | after dropna: [1.0, 1.0, 0]   max dev: 1
```

**怎麼修**
```python
        row_tot = counts.sum(axis=1)
        prob = counts.div(row_tot.where(row_tot > 0), axis=0)     # 保持 float64，0 → NaN
        chk = prob.sum(axis=1, min_count=1)                       # 全 NaN 列回傳 NaN
        assert (chk.dropna() - 1).abs().max() < 1e-9, "列機率未加總為 1"
```
`.where()` 保住 float dtype，`min_count=1` 讓全 NaN 列真的是 NaN。

---

### I16. `12` 的機率校準用了 sklearn 1.8 就會消失的 API，而 requirements 沒有上界

**位置**：`references/12_預測建模.md` L194–195；`requirements.txt` 的 `scikit-learn>=1.5`

**原文**
```python
cal_p = CalibratedClassifierCV(base, method="sigmoid", cv="prefit").fit(X_calib, y_calib)
cal_i = CalibratedClassifierCV(base, method="isotonic", cv="prefit").fit(X_calib, y_calib)
```

**錯在哪**：`cv="prefit"` 在 sklearn 1.6 已 deprecated，官方公告 1.8 移除。`requirements.txt` 只寫 `scikit-learn>=1.5`，沒有上界，新機器 `pip install -r requirements.txt` 遲早裝到會壞的版本。

**怎麼確認**：在本機 sklearn 1.7.2 實跑並攔截 warning：
```
cv=prefit OK; warnings: ["The `cv='prefit'` option is deprecated in 1.6 and will be removed in 1.8.
                          You can use CalibratedClassifierCV(FrozenEstimator(estimator)) instead."]
```

**怎麼修**
```python
from sklearn.frozen import FrozenEstimator            # sklearn >= 1.6
cal_p = CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid").fit(X_calib, y_calib)
```
requirements.txt 同步改成 `scikit-learn>=1.6`（`FrozenEstimator` 從 1.6 才有）。

---

## minor

### M1. `15` 的 `experiment_design.yml` 骨架 block 標成 ```yaml 但不是合法 YAML

**位置**：`references/15_實驗設計.md` L359（block 起點）

**原文**（L360–361）
```yaml
experiment_id / hypothesis / source_hypothesis_id     # ①  接回 hypothesis_register.csv
primary_metric: {name, metric_def_id, baseline, baseline_sd}   # ②  只准一個
```

**錯在哪**：第一行是純量、第二行開始是 mapping，`yaml.safe_load` 直接爆。上一句寫的是「骨架長這樣」所以本意是示意，但語言標籤是 `yaml`，編輯器與任何 lint 都會當成可解析的 YAML。

**怎麼確認**：對全庫 6 個 yaml block 跑 `yaml.safe_load`，只有這一塊失敗：
```
FAIL 15_實驗設計.md 359 | expected '<document start>', but found '<block mapping start>' in line 2, column 1
```
（`templates/experiment_design.yml`、`config.example.yml`、`templates/cluster_spec.json`、`templates/迴歸建模_程式範本.py` 都通過。）

**怎麼修**：語言標籤改成 ```text，或把第一行寫成合法的 `experiment_id: …` / `hypothesis: …` 三行。

---

### M2. `12` 的校準分箱兩端都用閉區間，邊界樣本被重複計入相鄰兩箱

**位置**：`references/12_預測建模.md` L202

**原文**
```python
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (p >= lo) & (p <= hi)
```

**錯在哪**：`bins` 來自 `np.quantile`，每個內部邊界都是真實存在的預測值，`>= lo` 與 `<= hi` 同時閉合會讓該值同時落進兩個箱，`sum(cnt)` 會大於 `len(p)`。等頻分箱時對 slope 的影響很小，但 `cnt` 欄（會進表 11.1）是錯的。

**怎麼確認**：純算術 —— 對 `p = [0.1, 0.2, 0.3]`、`bins = [0.1, 0.2, 0.3]`，0.2 同時滿足 `>=0.1 & <=0.2` 與 `>=0.2 & <=0.3`。

**怎麼修**：改成左閉右開、最後一箱右閉：
```python
    for i, (lo, hi) in enumerate(zip(bins[:-1], bins[1:])):
        m = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
```

---

### M3. 幾個範例 block 有未定義變數／未 import 的模組，複製貼上跑不動

**位置**：`references/12_預測建模.md` L146（`gap_rows` / `test_rows`）、L260（`y_pop_rate`）；`references/13_文本分析.md` L189（`itertools`）；`references/15_實驗設計.md` L264（參數 `treat` 定義了但整個函式沒用到）

**原文**（12 L146）
```python
cv = TimeSeriesSplit(n_splits=4, gap=gap_rows, test_size=test_rows)
```
（13 L189）
```python
for a, b in itertools.combinations(METHOD_COLUMNS, 2):
```

**錯在哪**：`ast.parse` 全數通過（語法沒問題），但 `itertools` 在該檔的任何 block 都沒 import，`gap_rows` / `test_rows` / `y_pop_rate` / `METHOD_COLUMNS` 都沒定義。`cuped_adjust(y, x, treat)` 的 `treat` 是簽章裡的死參數。

**怎麼確認**：對每個 python block 做 AST 走訪，收集 `ast.Name` 的 load 與 `ast.Import`；上述名稱在同檔任何 block 中都找不到綁定。

**怎麼修**：在該 block 頂端補一行 `import itertools`；把 `gap_rows = 30  # 依資料調整` 這類佔位值寫出來；`cuped_adjust` 把 `treat` 拿掉（CUPED 的 θ 本來就必須用合併資料估，不吃分組），或在 docstring 說明它是為了介面一致而保留。

---

## 查過但沒問題的部分（避免下一個人重查）

| 檢查項 | 結果 |
|---|---|
| 全部 74 個 python block `ast.parse` | 0 錯 |
| `08` 的 `anova3()` 正則改寫（`C(x)` → `C(x, Sum)`）與 Type III 行為 | 實跑正確，含 `y ~ x1 * C(grp)` 交互項；`C(grp, Treatment)` 會正確 raise |
| `08 L130` `m_full.compare_f_test(m_red)` 的參數順序 | 正確（statsmodels 是在完整模型上呼叫、傳受限模型） |
| `08 L390` `smf.mixedlm(..., groups=...)`、`15 L322` 的 ICC 算法、`15 L331` `cov_type="cluster"` | API 都存在且用法正確 |
| `15 L215–217` 的兩條交叉驗算 assert | 實跑通過：`n_prop(0.032,0.037)=20911.6` vs `20_9e2=20900`（誤差 0.06%）；`solve_power=6279.1` vs `6280`（誤差 0.01%） |
| `16 L120–121` 的 Cohen's h 與 MWE 手算值 | 實算 h=0.008448（註解 0.00844 ✔）、MWE=0.00039474（註解 0.000395 ✔）、0.2/0.00844≈23.7（註解「1/24」✔） |
| `06 L197` `sm.families.Gamma(sm.families.links.Log())` | statsmodels 0.14.6 可用，無 deprecation warning |
| `sklearn.cluster.HDBSCAN` 路徑（requirements 註解說 1.3 起內建） | 正確，1.7.2 可 import |
| `02 L82–90` C1 斷言（HAVING 引用 SELECT alias） | DuckDB 允許，實跑通過 |
| `02 L302–312` `dim_date` 的 `generate_series` + `DAYOFWEEK` | 實跑產出 1,826 列、2009-01-01～2013-12-31 連續無缺；`DAYOFWEEK` 在 DuckDB 是 Sunday=0，與 `dow_sun` 對應正確 |
| `02 L522–540` staging 時間轉換（`AT TIME ZONE` 吃欄位、`INTERVAL (col) HOUR`） | 全部可執行；用 `biz_day_cutoff_hour=6` 實測 2011-06-03 23:30 正確落到 biz_date 2011-06-03 |
| `02 L621–628` `ASOF JOIN` | DuckDB 1.5.5 語法正確 |
| `10 L188–207` 的 `SUM(SUM(n)) OVER ()` 巢狀彙總、`05 L328` 的 `PIVOT (subquery) ON … USING first(…)`、`06 L580` 的 `LIKE … ESCAPE '\'`、`11 L456` 的 `COUNT(*) FILTER (WHERE …)` | 語法全部合法，實跑通過 |
| `03 L278` `INSTALL encodings; LOAD encodings;`（我原本懷疑是 community extension） | 錯的是我 —— `encodings` 在 DuckDB 1.5.5 是核心 extension，`INSTALL` 直接成功；`con.execute()` 一次跑多段 statement 在 duckdb-python 1.5.5 也沒問題 |
| `20 L414` `SELECT max(snapshot_id) FROM ducklake_snapshots('mart')` | 欄名正確 |
| `20 L296–303` XlsxWriter 的 `write_number` / `freeze_panes` / `repeat_rows` 與 Excel 格式碼 | API 名稱與格式碼語法都正確 |
| `templates/sql/growth_decomp.sql` 的成長分解數學 | 合成資料實測：四桶加總 = `rev_b − rev_a`（150.0 = 150.0）；二階拆解 `eff_freq + eff_ticket + eff_interaction` 精確等於該桶貢獻 |
| `templates/迴歸建模_程式範本.py` 對外提供的 7 個名字 | 08 需要的全部存在，`ast.parse` 通過 |
| `templates/*.yml` / `*.json` / `config.example.yml` | 全部合法 |
| `econml` 的環境標註（`11 L492`） | 正確標了 `.venv-causal（Python 3.12）`，沒有誤導使用者在主環境裝 |
| 無語言標籤的 97 個 block | 掃過，全是 ASCII 流程圖／樹狀圖／表格，沒有藏 code |

---

## 順帶一提（不在本次審查視角內，但實測到了）

`CLAUDE.md` 的「開工前必讀」清單有三個檔名指不到實體檔：`references/04_資料品質與踩雷庫.md`（實際是 `04_資料體檢.md`）、`references/07_分析陷阱清單.md`（實際是 `18_分析陷阱清單.md`，`07_` 是 `07_標籤與分群.md`）、`references/05_指標公式庫.md`（實際是 `17_指標公式庫.md`，`05_` 是 `05_資料特徵檢驗.md`）。這應該屬於文件地圖審查者的範圍，列在這裡只是因為我 `ls references/` 時撞到了。

---

最後更新：2026-07-27
