-- Q11. How many customers come back? (customer_unique_id = real person)
WITH per_customer AS (
    SELECT customer_unique_id, COUNT(*) AS orders, SUM(payment_value) AS spend
    FROM fct_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
)
SELECT
    CASE WHEN orders = 1 THEN '1 order'
         WHEN orders = 2 THEN '2 orders'
         ELSE '3+ orders' END                         AS customer_type,
    COUNT(*)                                          AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_customers,
    ROUND(100.0 * SUM(spend) / SUM(SUM(spend)) OVER (), 2) AS pct_revenue,
    ROUND(AVG(spend), 2)                              AS avg_lifetime_spend
FROM per_customer
GROUP BY 1
ORDER BY 1;
