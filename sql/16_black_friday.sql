-- Q16. Black Friday 2017 impact: daily orders around 24 Nov 2017 vs. the November baseline.
WITH daily AS (
    SELECT CAST(purchased_at AS DATE) AS day, COUNT(*) AS orders, SUM(payment_value) AS revenue
    FROM fct_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
      AND purchased_at >= DATE '2017-11-01' AND purchased_at < DATE '2017-12-01'
    GROUP BY 1
)
SELECT
    day,
    DAYNAME(day)                                         AS weekday,
    orders,
    ROUND(revenue, 2)                                    AS revenue,
    ROUND(orders / MEDIAN(orders) OVER (), 2)            AS x_vs_median_day
FROM daily
ORDER BY orders DESC
LIMIT 10;
