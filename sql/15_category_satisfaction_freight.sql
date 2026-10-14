-- Q15. Category health: freight burden and satisfaction (categories with 500+ orders).
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id)                                 AS orders,
    ROUND(AVG(oi.price), 2)                                     AS avg_price,
    ROUND(AVG(oi.freight_value), 2)                             AS avg_freight,
    ROUND(100.0 * SUM(oi.freight_value) / SUM(oi.price), 1)     AS freight_to_price_pct,
    ROUND(AVG(f.review_score), 2)                               AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN f.is_late THEN 1 ELSE 0 END), 1) AS late_pct
FROM order_items oi
JOIN products p   USING (product_id)
JOIN fct_orders f USING (order_id)
WHERE f.order_status = 'delivered'
GROUP BY p.category
HAVING COUNT(DISTINCT oi.order_id) >= 500
ORDER BY avg_review ASC;
