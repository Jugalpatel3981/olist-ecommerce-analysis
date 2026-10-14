-- Q1. Headline KPIs: how big is the business?
-- Valid orders exclude canceled / unavailable ones.
SELECT
    COUNT(*)                                   AS total_orders,
    COUNT(DISTINCT customer_unique_id)         AS unique_customers,
    ROUND(SUM(payment_value), 2)               AS total_revenue,
    ROUND(AVG(payment_value), 2)               AS avg_order_value,
    ROUND(AVG(item_count), 2)                  AS avg_items_per_order,
    ROUND(AVG(review_score), 2)                AS avg_review_score,
    ROUND(100.0 * AVG(CASE WHEN is_late THEN 1 ELSE 0 END)
          FILTER (WHERE order_status = 'delivered'), 2) AS late_delivery_pct,
    ROUND(AVG(delivery_days) FILTER (WHERE order_status = 'delivered'), 1) AS avg_delivery_days
FROM fct_orders
WHERE order_status NOT IN ('canceled', 'unavailable');
