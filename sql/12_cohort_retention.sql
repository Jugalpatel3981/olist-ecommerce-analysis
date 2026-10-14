-- Q12. Monthly cohort retention: % of each first-purchase cohort that buys again in month N.
WITH valid AS (
    SELECT customer_unique_id, order_month
    FROM fct_orders
    WHERE order_status NOT IN ('canceled', 'unavailable')
      AND order_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
),
first_purchase AS (
    SELECT customer_unique_id, MIN(order_month) AS cohort_month
    FROM valid GROUP BY 1
),
activity AS (
    SELECT DISTINCT
        f.cohort_month,
        v.customer_unique_id,
        DATE_DIFF('month', f.cohort_month, v.order_month) AS month_number
    FROM valid v
    JOIN first_purchase f USING (customer_unique_id)
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS customers FROM first_purchase GROUP BY 1
)
SELECT
    a.cohort_month,
    c.customers                                       AS cohort_size,
    a.month_number,
    COUNT(*)                                          AS active_customers,
    ROUND(100.0 * COUNT(*) / c.customers, 2)          AS retention_pct
FROM activity a
JOIN cohort_size c USING (cohort_month)
WHERE a.month_number BETWEEN 0 AND 12
GROUP BY a.cohort_month, c.customers, a.month_number
ORDER BY a.cohort_month, a.month_number;
