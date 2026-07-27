-- 各通路 cohort 的累積毛利曲線 → payback period（M8-3 §四）
-- 規格見 references/11_行銷_成長與促銷.md §4.3
-- 參數：$gross_margin（毛利率，ratio）
-- DuckDB 具名參數是 $name，不是 :name。綁法：con.execute(sql, {"gross_margin": 0.35})
--
-- 依賴：dim_customer.first_purchase_date 與 dim_customer.acquisition_channel_key
-- （02 §3.2 的兩個 Type 1 衍生欄，由 fact_transaction／首單歸因回算後物化）。
--
-- Payback_m = min{ m : Σ_{k=1..m} GM_k(cohort) >= CAC }
-- GM_k 是「已實現」人均毛利，不是預測值 —— 這正是 payback 比 CLV/CAC 穩健的原因。
-- 未滿觀測窗的月齡格必須標 '—'（無樣本），不可外推補值。

WITH cohort AS (
    SELECT c.person_key,
           c.acquisition_channel_key                   AS ch,
           DATE_TRUNC('month', c.first_purchase_date)  AS cohort_m
    FROM dim_customer c
    WHERE c.is_current
      AND c.first_purchase_date IS NOT NULL            -- 首購日缺值者不進 cohort，另報筆數
),
size AS (
    SELECT ch, cohort_m, COUNT(*) AS n_acquired FROM cohort GROUP BY 1, 2
),
gm AS (
    SELECT co.ch, co.cohort_m,
           DATE_DIFF('month', co.cohort_m, DATE_TRUNC('month', t.biz_date)) AS m_since,
           SUM(t.amount_twd * $gross_margin)                                AS gm_twd
    FROM fact_transaction t
    JOIN cohort co USING (person_key)
    WHERE t.txn_type = 'sale' AND t.is_test_txn = FALSE
    GROUP BY 1, 2, 3
)
SELECT g.ch, g.cohort_m, g.m_since,
       s.n_acquired,
       g.gm_twd / s.n_acquired                                                    AS gm_per_head,
       SUM(g.gm_twd / s.n_acquired) OVER (
           PARTITION BY g.ch, g.cohort_m ORDER BY g.m_since
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)                      AS cum_gm_per_head
FROM gm g JOIN size s USING (ch, cohort_m)
WHERE g.m_since >= 0
ORDER BY g.ch, g.cohort_m, g.m_since;

-- 三種 CAC 口徑必須並排輸出（§4.1）：
--   CAC_blended = 全部行銷支出 / 全部新客數
--   CAC_paid    = 付費媒體支出 / 可歸因付費新客數
--   CAC_loaded  = (行銷 + 銷售人力 + 首購折扣補貼) / 首購新客數
-- 分母一律只用「首購新客」（回流客佔 30% 時 CAC 低估 30%）。
-- 只報 CAC_paid 等於藏成本 —— blended 與 paid 的落差必須列出來。
