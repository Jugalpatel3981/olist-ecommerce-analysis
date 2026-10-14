-- Q9. Seller concentration (Pareto): what share of revenue comes from the top 10% / 20% of sellers?
WITH seller_rev AS (
    SELECT oi.seller_id, SUM(oi.price) AS revenue
    FROM order_items oi
    JOIN orders o USING (order_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY oi.seller_id
),
ranked AS (
    SELECT
        seller_id,
        revenue,
        PERCENT_RANK() OVER (ORDER BY revenue DESC)   AS pct_rank
    FROM seller_rev
)
SELECT
    CASE
        WHEN pct_rank < 0.01 THEN '1. Top 1%'
        WHEN pct_rank < 0.10 THEN '2. Top 1-10%'
        WHEN pct_rank < 0.20 THEN '3. Top 10-20%'
        WHEN pct_rank < 0.50 THEN '4. Top 20-50%'
        ELSE                      '5. Bottom 50%'
    END                                                AS seller_tier,
    COUNT(*)                                           AS sellers,
    ROUND(SUM(revenue), 2)                             AS revenue,
    ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct
FROM ranked
GROUP BY 1
ORDER BY 1;
