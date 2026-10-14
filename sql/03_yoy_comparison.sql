-- Q3. Year-over-year: Jan-Aug 2018 vs Jan-Aug 2017.
SELECT
    YEAR(order_month)                     AS year,
    COUNT(*)                              AS orders,
    ROUND(SUM(payment_value), 2)          AS revenue,
    ROUND(AVG(payment_value), 2)          AS avg_order_value,
    ROUND(AVG(review_score), 2)           AS avg_review
FROM fct_orders
WHERE order_status NOT IN ('canceled', 'unavailable')
  AND MONTH(order_month) BETWEEN 1 AND 8
  AND YEAR(order_month) IN (2017, 2018)
GROUP BY 1
ORDER BY 1;
