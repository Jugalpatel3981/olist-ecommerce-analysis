"""Pre-aggregate the data for the static GitHub Pages dashboard (docs/index.html).

Filterable facts are stored as compact arrays keyed by (month, state), so the page can
re-aggregate in the browser without a server.

Usage:
    python scripts/export_web_data.py
"""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data.json"
SQL_DIR = ROOT / "sql"
VALID = "order_status NOT IN ('canceled', 'unavailable') AND order_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'"
BUCKETS = ["10+ days early", "1-9 days early", "On time", "1-5 days late", "6-10 days late", "10+ days late"]


def rows(con, query: str) -> list:
    return [list(r) for r in con.execute(query).fetchall()]


def main() -> None:
    con = duckdb.connect(str(ROOT / "data" / "olist.duckdb"), read_only=True)
    months = [r[0] for r in rows(con, f"SELECT DISTINCT strftime(order_month, '%Y-%m') FROM fct_orders WHERE {VALID} ORDER BY 1")]
    states = [r[0] for r in rows(con, f"SELECT DISTINCT customer_state FROM fct_orders WHERE {VALID} ORDER BY 1")]
    cats = [r[0] for r in rows(con, "SELECT DISTINCT category FROM products ORDER BY 1")]
    pays = [r[0] for r in rows(con, f"SELECT DISTINCT main_payment_type FROM fct_orders WHERE {VALID} AND main_payment_type IS NOT NULL ORDER BY 1")]
    con.execute("CREATE TEMP TABLE m AS SELECT * FROM (VALUES " + ",".join(f"('{x}',{i})" for i, x in enumerate(months)) + ") t(month, mi)")
    con.execute("CREATE TEMP TABLE s AS SELECT * FROM (VALUES " + ",".join(f"('{x}',{i})" for i, x in enumerate(states)) + ") t(state, si)")
    con.execute("CREATE TEMP TABLE c AS SELECT * FROM (VALUES " + ",".join(f"('{x}',{i})" for i, x in enumerate(cats)) + ") t(category, ci)")
    con.execute("CREATE TEMP TABLE p AS SELECT * FROM (VALUES " + ",".join(f"('{x}',{i})" for i, x in enumerate(pays)) + ") t(pay, pi)")
    con.execute(f"""CREATE TEMP TABLE f AS SELECT o.*, m.mi, s.si FROM fct_orders o
                   JOIN m ON strftime(o.order_month, '%Y-%m') = m.month JOIN s ON o.customer_state = s.state WHERE {VALID}""")

    data = {
        "months": months, "states": states, "categories": cats, "payments": pays, "buckets": BUCKETS,
        # [month, state, orders, revenue, review_sum, review_n, delivered, late, delivery_days_sum,
        #  late_review_sum, late_review_n, ontime_review_sum, ontime_review_n]
        "facts": rows(con, """
            SELECT mi, si, COUNT(*), ROUND(SUM(payment_value), 2),
                   SUM(review_score), COUNT(review_score),
                   COUNT(*) FILTER (WHERE order_status = 'delivered' AND delivered_at IS NOT NULL),
                   COUNT(*) FILTER (WHERE order_status = 'delivered' AND is_late),
                   SUM(delivery_days) FILTER (WHERE order_status = 'delivered'),
                   COALESCE(SUM(review_score) FILTER (WHERE order_status = 'delivered' AND is_late), 0),
                   COUNT(review_score) FILTER (WHERE order_status = 'delivered' AND is_late),
                   COALESCE(SUM(review_score) FILTER (WHERE order_status = 'delivered' AND NOT is_late), 0),
                   COUNT(review_score) FILTER (WHERE order_status = 'delivered' AND NOT is_late)
            FROM f GROUP BY 1, 2 ORDER BY 1, 2"""),
        # [month, state, bucket, orders, review_sum]
        "buckets_facts": rows(con, """
            SELECT mi, si,
                   CASE WHEN days_vs_estimate <= -10 THEN 0 WHEN days_vs_estimate <= -1 THEN 1
                        WHEN days_vs_estimate <= 0 THEN 2 WHEN days_vs_estimate <= 5 THEN 3
                        WHEN days_vs_estimate <= 10 THEN 4 ELSE 5 END,
                   COUNT(*), SUM(review_score)
            FROM f WHERE order_status = 'delivered' AND delivered_at IS NOT NULL AND review_score IS NOT NULL
            GROUP BY 1, 2, 3"""),
        # [month, state, category, revenue, items]
        "category_facts": rows(con, """
            SELECT f.mi, f.si, c.ci, ROUND(SUM(oi.price), 2), COUNT(*)
            FROM f JOIN order_items oi USING (order_id) JOIN products pr USING (product_id)
            JOIN c ON pr.category = c.category GROUP BY 1, 2, 3"""),
        # [month, state, payment, revenue]
        "payment_facts": rows(con, """
            SELECT mi, si, p.pi, ROUND(SUM(payment_value), 2)
            FROM f JOIN p ON f.main_payment_type = p.pay GROUP BY 1, 2, 3"""),
    }

    # Unfiltered analyses (whole dataset) reuse the project's SQL files
    def q(prefix: str):
        return con.execute(next(SQL_DIR.glob(f"{prefix}*.sql")).read_text()).df()

    rfm = q("13")
    data["rfm"] = rfm[["segment", "customers", "pct_customers", "pct_revenue", "avg_spend", "avg_recency_days"]].values.tolist()
    coh = q("12")
    coh["cohort"] = coh["cohort_month"].astype(str).str[:7]
    piv = coh.pivot(index="cohort", columns="month_number", values="retention_pct")
    piv = piv[[c for c in piv.columns if 1 <= c <= 12]]
    data["cohort"] = {"cohorts": piv.index.tolist(), "months": [int(c) for c in piv.columns],
                      "values": [[None if v != v else round(float(v), 2) for v in r] for r in piv.values]}
    rep = q("11")
    data["repeat"] = rep[["customer_type", "customers", "pct_customers", "pct_revenue"]].values.tolist()
    seller = [r[0] for r in rows(con, f"""
        SELECT SUM(oi.price) FROM order_items oi JOIN f USING (order_id) GROUP BY oi.seller_id ORDER BY 1 DESC""")]
    total, run, curve = sum(seller), 0.0, [[0, 0]]
    step = max(len(seller) // 200, 1)
    for i, v in enumerate(seller, 1):
        run += v
        if i % step == 0 or i == len(seller):
            curve.append([round(i / len(seller) * 100, 2), round(run / total * 100, 2)])
    data["sellers"] = {"count": len(seller), "curve": curve}

    OUT.write_text(json.dumps(data, separators=(",", ":"), default=float))
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1e3:.0f} KB · {len(data['facts'])} fact rows, "
          f"{len(data['category_facts'])} category rows")


if __name__ == "__main__":
    main()
