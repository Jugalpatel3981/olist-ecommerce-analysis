-- Q2. Monthly revenue, orders and month-over-month growth (window function LAG).
WITH monthly AS (
    SELECT
        order_month,
        COUNT(*)                     AS orders,
        COUNT(DISTINCT customer_unique_id) AS customers,
        ROUND(SUM(payment_value), 2) AS revenue,
        ROUND(AVG(payment_value), 2) AS avg_order_value
    FROM fct_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
      AND order_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
    GROUP BY order_month
)
SELECT
    *,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
          / LAG(revenue) OVER (ORDER BY order_month), 1) AS revenue_mom_pct,
    ROUND(SUM(revenue) OVER (ORDER BY order_month), 2)  AS cumulative_revenue
FROM monthly
ORDER BY order_month;
