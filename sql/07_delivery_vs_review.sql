-- Q7. Does late delivery hurt customer satisfaction?
SELECT
    CASE
        WHEN days_vs_estimate <= -10 THEN '1. 10+ days early'
        WHEN days_vs_estimate <= -1  THEN '2. 1-9 days early'
        WHEN days_vs_estimate <= 0   THEN '3. On time'
        WHEN days_vs_estimate <= 5   THEN '4. 1-5 days late'
        WHEN days_vs_estimate <= 10  THEN '5. 6-10 days late'
        ELSE                              '6. 10+ days late'
    END                                              AS delivery_bucket,
    COUNT(*)                                         AS orders,
    ROUND(AVG(review_score), 2)                      AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END), 1) AS pct_bad_reviews,
    ROUND(100.0 * AVG(CASE WHEN review_score = 5 THEN 1 ELSE 0 END), 1)  AS pct_5_star
FROM fct_orders
WHERE order_status = 'delivered'
  AND delivered_at IS NOT NULL
  AND review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;
