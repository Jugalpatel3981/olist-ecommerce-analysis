"""Load the raw Olist CSVs into a DuckDB database and build clean analytics tables.

Layers:
    raw_*     -> CSVs loaded as-is
    clean views / tables -> typed, deduplicated, translated, business-ready

Usage:
    python scripts/build_database.py
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "olist.duckdb"

RAW_TABLES = {
    "raw_customers": "olist_customers_dataset.csv",
    "raw_geolocation": "olist_geolocation_dataset.csv",
    "raw_order_items": "olist_order_items_dataset.csv",
    "raw_payments": "olist_order_payments_dataset.csv",
    "raw_reviews": "olist_order_reviews_dataset.csv",
    "raw_orders": "olist_orders_dataset.csv",
    "raw_products": "olist_products_dataset.csv",
    "raw_sellers": "olist_sellers_dataset.csv",
    "raw_category_translation": "product_category_name_translation.csv",
}

CLEAN_SQL = """
-- Customers: one row per customer_id (order-level id); customer_unique_id = real person
CREATE OR REPLACE TABLE customers AS
SELECT
    customer_id,
    customer_unique_id,
    LPAD(CAST(customer_zip_code_prefix AS VARCHAR), 5, '0') AS zip_prefix,
    customer_city  AS city,
    customer_state AS state
FROM raw_customers;

-- Sellers
CREATE OR REPLACE TABLE sellers AS
SELECT
    seller_id,
    LPAD(CAST(seller_zip_code_prefix AS VARCHAR), 5, '0') AS zip_prefix,
    seller_city  AS city,
    seller_state AS state
FROM raw_sellers;

-- Products with English category names (fix misspelled source columns)
CREATE OR REPLACE TABLE products AS
SELECT
    p.product_id,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    p.product_name_lenght        AS name_length,
    p.product_description_lenght AS description_length,
    p.product_photos_qty         AS photos_qty,
    p.product_weight_g           AS weight_g,
    p.product_length_cm * p.product_height_cm * p.product_width_cm AS volume_cm3
FROM raw_products p
LEFT JOIN raw_category_translation t USING (product_category_name);

-- Orders with derived delivery metrics
CREATE OR REPLACE TABLE orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP)      AS purchased_at,
    CAST(order_approved_at AS TIMESTAMP)             AS approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP)  AS shipped_at,
    CAST(order_delivered_customer_date AS TIMESTAMP) AS delivered_at,
    CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimated_delivery_at,
    DATE_TRUNC('month', CAST(order_purchase_timestamp AS TIMESTAMP))::DATE AS order_month,
    DATE_DIFF('day', CAST(order_purchase_timestamp AS TIMESTAMP),
                     CAST(order_delivered_customer_date AS TIMESTAMP)) AS delivery_days,
    DATE_DIFF('day', CAST(order_estimated_delivery_date AS TIMESTAMP),
                     CAST(order_delivered_customer_date AS TIMESTAMP)) AS days_vs_estimate,
    CAST(order_delivered_customer_date AS TIMESTAMP)
        > CAST(order_estimated_delivery_date AS TIMESTAMP) AS is_late
FROM raw_orders;

-- Order items
CREATE OR REPLACE TABLE order_items AS
SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_at,
    price,
    freight_value
FROM raw_order_items;

-- Payments
CREATE OR REPLACE TABLE payments AS
SELECT order_id, payment_sequential, payment_type, payment_installments, payment_value
FROM raw_payments
WHERE payment_type <> 'not_defined';

-- Reviews: the source has duplicate review rows per order; keep the latest one
CREATE OR REPLACE TABLE reviews AS
SELECT order_id, review_id, review_score, review_comment_message,
       CAST(review_creation_date AS TIMESTAMP) AS reviewed_at
FROM raw_reviews
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC) = 1;

-- Analysis-ready fact table: one row per order
CREATE OR REPLACE TABLE fct_orders AS
WITH items AS (
    SELECT order_id,
           COUNT(*)            AS item_count,
           SUM(price)          AS items_value,
           SUM(freight_value)  AS freight_value,
           COUNT(DISTINCT seller_id) AS seller_count
    FROM order_items
    GROUP BY order_id
),
pay AS (
    SELECT order_id,
           SUM(payment_value) AS payment_value,
           ARG_MAX(payment_type, payment_value) AS main_payment_type,
           MAX(payment_installments) AS installments
    FROM payments
    GROUP BY order_id
)
SELECT
    o.*,
    c.customer_unique_id,
    c.city  AS customer_city,
    c.state AS customer_state,
    i.item_count,
    i.items_value,
    i.freight_value,
    i.items_value + i.freight_value AS order_value,
    i.seller_count,
    p.payment_value,
    p.main_payment_type,
    p.installments,
    r.review_score
FROM orders o
JOIN customers c USING (customer_id)
LEFT JOIN items i USING (order_id)
LEFT JOIN pay p USING (order_id)
LEFT JOIN reviews r USING (order_id);
"""


def main() -> None:
    missing = [f for f in RAW_TABLES.values() if not (RAW_DIR / f).exists()]
    if missing:
        raise SystemExit(f"Missing raw files: {missing}. Run scripts/download_data.py first.")

    DB_PATH.unlink(missing_ok=True)
    con = duckdb.connect(str(DB_PATH))

    for table, filename in RAW_TABLES.items():
        con.execute(
            f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto(?, header=true)",
            [str(RAW_DIR / filename)],
        )
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"loaded {table:<26} {n:>10,} rows")

    con.execute(CLEAN_SQL)
    for table in ["customers", "sellers", "products", "orders", "order_items",
                  "payments", "reviews", "fct_orders"]:
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"built  {table:<26} {n:>10,} rows")

    con.close()
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    main()
