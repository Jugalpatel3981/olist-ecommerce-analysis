-- Q6. Payment method mix and installment behaviour.
SELECT
    payment_type,
    COUNT(DISTINCT order_id)                         AS orders,
    ROUND(SUM(payment_value), 2)                     AS revenue,
    ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 2) AS revenue_share_pct,
    ROUND(AVG(payment_value), 2)                     AS avg_payment,
    ROUND(AVG(payment_installments), 2)              AS avg_installments
FROM payments
GROUP BY payment_type
ORDER BY revenue DESC;
