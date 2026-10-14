-- Q4. Top 15 product categories by revenue, with share of total and rank.
WITH cat AS (
    SELECT
        p.category,
        COUNT(DISTINCT oi.order_id)              AS orders,
        COUNT(*)                                 AS items_sold,
        ROUND(SUM(oi.price), 2)                  AS revenue,
        ROUND(AVG(oi.price), 2)                  AS avg_price
    FROM order_items oi
    JOIN products p   USING (product_id)
    JOIN orders o     USING (order_id)
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY p.category
)
SELECT
    RANK() OVER (ORDER BY revenue DESC)                    AS rank,
    *,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 2)       AS revenue_share_pct,
    ROUND(100.0 * SUM(revenue) OVER (ORDER BY revenue DESC)
          / SUM(revenue) OVER (), 2)                       AS cumulative_share_pct
FROM cat
ORDER BY revenue DESC
LIMIT 15;
