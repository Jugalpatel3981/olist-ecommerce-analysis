-- Q8. Late vs on-time: headline comparison.
SELECT
    CASE WHEN is_late THEN 'Late' ELSE 'On time / early' END AS delivery_status,
    COUNT(*)                                             AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS pct_of_orders,
    ROUND(AVG(review_score), 2)                          AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score = 1 THEN 1 ELSE 0 END), 1) AS pct_1_star,
    ROUND(AVG(delivery_days), 1)                         AS avg_delivery_days
FROM fct_orders
WHERE order_status = 'delivered'
  AND delivered_at IS NOT NULL
  AND review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;
