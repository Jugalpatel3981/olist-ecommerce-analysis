-- Q10. Seller scorecard: top sellers (min 100 orders) with quality flags.
WITH s AS (
    SELECT
        oi.seller_id,
        ANY_VALUE(se.state)                           AS seller_state,
        COUNT(DISTINCT oi.order_id)                   AS orders,
        ROUND(SUM(oi.price), 2)                       AS revenue,
        ROUND(AVG(f.review_score), 2)                 AS avg_review,
        ROUND(100.0 * AVG(CASE WHEN f.is_late THEN 1 ELSE 0 END), 1) AS late_pct
    FROM order_items oi
    JOIN sellers se    USING (seller_id)
    JOIN fct_orders f  USING (order_id)
    WHERE f.order_status = 'delivered'
    GROUP BY oi.seller_id
    HAVING COUNT(DISTINCT oi.order_id) >= 100
)
SELECT
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
    *,
    CASE
        WHEN avg_review < 3.8 OR late_pct > 15 THEN 'Needs attention'
        WHEN avg_review >= 4.3 AND late_pct < 6 THEN 'Star seller'
        ELSE 'OK'
    END AS seller_flag
FROM s
ORDER BY revenue DESC
LIMIT 25;
