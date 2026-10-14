-- Q13. RFM segmentation with NTILE scoring (1 = worst, 5 = best).
-- Frequency is extremely skewed (97% buy once), so F is scored on order count directly.
WITH base AS (
    SELECT
        customer_unique_id,
        DATE_DIFF('day', MAX(purchased_at), (SELECT MAX(purchased_at) FROM fct_orders)) AS recency_days,
        COUNT(*)                     AS frequency,
        SUM(payment_value)           AS monetary
    FROM fct_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
      AND payment_value IS NOT NULL
    GROUP BY 1
),
scored AS (
    SELECT
        *,
        6 - NTILE(5) OVER (ORDER BY recency_days, customer_unique_id)  AS r_score,
        CASE WHEN frequency >= 3 THEN 5
             WHEN frequency = 2  THEN 4
             ELSE 1 END                               AS f_score,
        NTILE(5) OVER (ORDER BY monetary, customer_unique_id)         AS m_score
    FROM base
),
segmented AS (
    SELECT
        *,
        CASE
            WHEN f_score >= 4 AND r_score >= 4                   THEN 'Champions'
            WHEN f_score >= 4                                    THEN 'Loyal - slipping'
            WHEN r_score >= 4 AND m_score >= 4                   THEN 'New big spenders'
            WHEN r_score >= 4                                    THEN 'Recent customers'
            WHEN r_score = 3                                     THEN 'Needs attention'
            WHEN r_score <= 2 AND m_score >= 4                   THEN 'At risk - high value'
            ELSE                                                      'Lost / hibernating'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*)                                            AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)  AS pct_customers,
    ROUND(SUM(monetary), 2)                             AS revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_revenue,
    ROUND(AVG(recency_days), 0)                         AS avg_recency_days,
    ROUND(AVG(frequency), 2)                            AS avg_orders,
    ROUND(AVG(monetary), 2)                             AS avg_spend
FROM segmented
GROUP BY segment
ORDER BY revenue DESC;
