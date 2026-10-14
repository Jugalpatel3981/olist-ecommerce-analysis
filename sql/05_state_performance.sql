-- Q5. Revenue, delivery speed and satisfaction by customer state.
SELECT
    customer_state                                   AS state,
    COUNT(*)                                         AS orders,
    ROUND(SUM(payment_value), 2)                     AS revenue,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(payment_value), 2)                     AS avg_order_value,
    ROUND(AVG(freight_value), 2)                     AS avg_freight,
    ROUND(AVG(delivery_days), 1)                     AS avg_delivery_days,
    ROUND(100.0 * AVG(CASE WHEN is_late THEN 1 ELSE 0 END), 1) AS late_pct,
    ROUND(AVG(review_score), 2)                      AS avg_review
FROM fct_orders
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY revenue DESC;
