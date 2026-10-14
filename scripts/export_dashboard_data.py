"""Export compact Parquet files the Streamlit dashboard reads (small enough to commit and deploy).

Usage:
    python scripts/export_dashboard_data.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "data"

ORDERS = """
SELECT order_id, customer_unique_id, customer_state AS state, order_status,
       purchased_at, order_month, payment_value, item_count, main_payment_type,
       delivery_days, days_vs_estimate, is_late, review_score
FROM fct_orders
WHERE order_status NOT IN ('canceled', 'unavailable')
  AND order_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
"""

ITEMS = """
SELECT oi.order_id, p.category, oi.seller_id, oi.price, oi.freight_value
FROM order_items oi
JOIN products p USING (product_id)
JOIN fct_orders f USING (order_id)
WHERE f.order_status NOT IN ('canceled', 'unavailable')
  AND f.order_month BETWEEN DATE '2017-01-01' AND DATE '2018-08-01'
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "olist.duckdb"), read_only=True)
    for name, query in {"orders": ORDERS, "items": ITEMS}.items():
        path = OUT / f"{name}.parquet"
        con.execute(f"COPY ({query}) TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        print(f"{path.relative_to(ROOT)}: {path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
