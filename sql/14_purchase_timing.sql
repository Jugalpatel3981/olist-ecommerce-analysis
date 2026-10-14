-- Q14. When do customers shop? Orders by weekday and hour block.
SELECT
    ISODOW(purchased_at)                      AS weekday_num,
    DAYNAME(purchased_at)                     AS weekday,
    CASE
        WHEN HOUR(purchased_at) < 6  THEN '00-06 Night'
        WHEN HOUR(purchased_at) < 12 THEN '06-12 Morning'
        WHEN HOUR(purchased_at) < 18 THEN '12-18 Afternoon'
        ELSE                              '18-24 Evening'
    END                                       AS time_of_day,
    COUNT(*)                                  AS orders,
    ROUND(SUM(payment_value), 2)              AS revenue
FROM fct_orders
WHERE order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1, 2, 3
ORDER BY 1, 3;
