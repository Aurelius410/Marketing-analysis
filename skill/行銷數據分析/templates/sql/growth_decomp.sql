-- 成長分解：營收變化的五項拆解（M8-3 §一）
-- 規格見 references/11_行銷_成長與促銷.md §1.2–§1.5
-- 參數：$a_start, $b_start, $b_end, $a_end（兩期必須等長，且不得橫跨量測變更日）
-- DuckDB 具名參數是 $name，不是 :name（:name 是 SQLAlchemy 風格，DuckDB 連 parse 都不過）。
-- 綁法：con.execute(sql, {"a_start": ..., "a_end": ..., "b_start": ..., "b_end": ...})
--
-- 依賴：dim_customer.first_purchase_date（02 §3.2 的 Type 1 衍生欄，由 fact_transaction
-- 回算後物化）。不可改用「資料裡最早一筆」代替 —— 資料窗左截斷會把老客誤判成首購（18-G3、11 §1.3）。
--
-- 恆等式：ΔR = 首購新客 + 回流客 + 既有客增購 + 既有客減購 − 流失損失
-- 跑完必做加法檢核（相對誤差 < 1e-9），對不上代表 person_key 重複（18-G1）
-- 或兩期過濾條件不一致 —— 兩者都是錯誤，不是數值問題。

WITH base AS (
    SELECT t.person_key,
           SUM(t.amount_twd)          FILTER (WHERE t.biz_date BETWEEN $a_start AND $a_end) AS r_a,
           SUM(t.amount_twd)          FILTER (WHERE t.biz_date BETWEEN $b_start AND $b_end) AS r_b,
           COUNT(DISTINCT t.txn_id)   FILTER (WHERE t.biz_date BETWEEN $a_start AND $a_end) AS f_a,
           COUNT(DISTINCT t.txn_id)   FILTER (WHERE t.biz_date BETWEEN $b_start AND $b_end) AS f_b,
           MIN(c.first_purchase_date) AS first_dt
    FROM fact_transaction t
    JOIN dim_customer c ON c.person_key = t.person_key AND c.is_current
    WHERE t.txn_type = 'sale'          -- 不可省：退貨會讓兩期都失真（18-G2）
      AND t.is_test_txn = FALSE        -- 不可省：測試交易標記不刪，但不進分析
      AND t.biz_date BETWEEN $a_start AND $b_end
    GROUP BY 1
),
tagged AS (
    SELECT *,
           COALESCE(r_a, 0) AS ra,
           COALESCE(r_b, 0) AS rb,
           CASE
             -- 新客必須拆兩類，否則 CAC 分母會系統性偏大、CAC 低估（§1.3）
             WHEN r_a IS NULL AND r_b IS NOT NULL AND first_dt >= $b_start THEN '1_首購新客'
             WHEN r_a IS NULL AND r_b IS NOT NULL AND first_dt <  $a_start THEN '2_回流客'
             WHEN r_a IS NULL AND r_b IS NOT NULL                          THEN '9_無法判定'
             WHEN r_a IS NOT NULL AND r_b IS NOT NULL AND r_b >= r_a        THEN '3_既有客增購'
             WHEN r_a IS NOT NULL AND r_b IS NOT NULL                       THEN '4_既有客減購'
             WHEN r_b IS NULL                                               THEN '5_流失'
           END AS bucket
    FROM base
)
SELECT bucket,
       COUNT(*)                                              AS n_customers,
       SUM(rb - ra)                                          AS contrib_twd,
       SUM(rb - ra) / NULLIF(SUM(SUM(ra)) OVER (), 0) * 100  AS contrib_pct_of_base,
       -- 二階拆解只對既有客有意義；交互項另算，不可靜默分攤（§1.4）
       SUM(CASE WHEN bucket IN ('3_既有客增購','4_既有客減購')
                THEN (ra / NULLIF(f_a, 0)) * (f_b - f_a) END)                     AS eff_freq,
       SUM(CASE WHEN bucket IN ('3_既有客增購','4_既有客減購')
                THEN f_a * (rb / NULLIF(f_b,0) - ra / NULLIF(f_a,0)) END)         AS eff_ticket,
       SUM(CASE WHEN bucket IN ('3_既有客增購','4_既有客減購')
                THEN (f_b - f_a) * (rb / NULLIF(f_b,0) - ra / NULLIF(f_a,0)) END) AS eff_interaction
FROM tagged
GROUP BY 1
ORDER BY 1;

-- 維度版：把 person_key 換成 <dim>（品類／通路／地區／顧客類型），四組維度預設全跑（BT-02）
-- Σ 各切片貢獻 == 總變化，誤差 < 0.1%，否則報錯 —— 這會抓出遺漏切片與重複計算。
