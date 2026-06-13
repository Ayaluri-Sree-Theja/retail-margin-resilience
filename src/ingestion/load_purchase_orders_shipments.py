from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PO_FILE = RAW_DATA_DIR / "fact_purchase_order.csv"
SHIPMENT_FILE = RAW_DATA_DIR / "fact_shipment.csv"

load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Check your .env file.")

engine = create_engine(DATABASE_URL)


# ---------------------------------------------------------------------
# Load functions
# ---------------------------------------------------------------------

def truncate_tables():
    """
    Truncate shipments first because shipments depend on purchase orders.
    """

    with engine.begin() as connection:
        print("Truncating raw.fact_shipment...")
        connection.execute(text("TRUNCATE TABLE raw.fact_shipment;"))

        print("Truncating raw.fact_purchase_order...")
        connection.execute(text("TRUNCATE TABLE raw.fact_purchase_order;"))


def load_table(file_path, table_name):
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    print(f"\nReading file: {file_path}")
    df = pd.read_csv(file_path)

    print(f"Rows to load into raw.{table_name}: {len(df):,}")

    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10000,
    )

    print(f"Loaded raw.{table_name} successfully.")


def validate_purchase_orders():
    summary_query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT purchase_order_id) AS distinct_purchase_order_ids,
            COUNT(DISTINCT po_line_id) AS distinct_po_line_ids,
            MIN(order_date) AS min_order_date,
            MAX(order_date) AS max_order_date,
            MIN(expected_delivery_date) AS min_expected_delivery_date,
            MAX(expected_delivery_date) AS max_expected_delivery_date,
            SUM(ordered_units) AS total_ordered_units,
            ROUND(SUM(ordered_units * unit_cost), 2) AS total_ordered_cost
        FROM raw.fact_purchase_order;
    """

    status_query = """
        SELECT
            order_status,
            COUNT(*) AS row_count,
            SUM(ordered_units) AS ordered_units,
            ROUND(SUM(ordered_units * unit_cost), 2) AS ordered_cost
        FROM raw.fact_purchase_order
        GROUP BY order_status
        ORDER BY row_count DESC;
    """

    null_query = """
        SELECT
            SUM(CASE WHEN purchase_order_id IS NULL THEN 1 ELSE 0 END) AS null_purchase_order_id,
            SUM(CASE WHEN po_line_id IS NULL THEN 1 ELSE 0 END) AS null_po_line_id,
            SUM(CASE WHEN supplier_id IS NULL THEN 1 ELSE 0 END) AS null_supplier_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END) AS null_order_date,
            SUM(CASE WHEN expected_delivery_date IS NULL THEN 1 ELSE 0 END) AS null_expected_delivery_date,
            SUM(CASE WHEN ordered_units IS NULL THEN 1 ELSE 0 END) AS null_ordered_units,
            SUM(CASE WHEN unit_cost IS NULL THEN 1 ELSE 0 END) AS null_unit_cost
        FROM raw.fact_purchase_order;
    """

    integrity_query = """
        SELECT
            SUM(CASE WHEN s.supplier_id IS NULL THEN 1 ELSE 0 END) AS po_without_matching_supplier,
            SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END) AS po_without_matching_product,
            SUM(CASE WHEN st.store_id IS NULL THEN 1 ELSE 0 END) AS po_without_matching_store,
            SUM(CASE WHEN po.ordered_units <= 0 THEN 1 ELSE 0 END) AS non_positive_ordered_units,
            SUM(CASE WHEN po.unit_cost <= 0 THEN 1 ELSE 0 END) AS non_positive_unit_cost,
            SUM(CASE WHEN po.expected_delivery_date < po.order_date THEN 1 ELSE 0 END) AS expected_before_order_date
        FROM raw.fact_purchase_order po
        LEFT JOIN raw.dim_supplier s
            ON po.supplier_id = s.supplier_id
        LEFT JOIN raw.dim_product p
            ON po.product_id = p.product_id
        LEFT JOIN raw.dim_store st
            ON po.store_id = st.store_id;
    """

    with engine.connect() as connection:
        print("\nPurchase order validation summary:")
        result = connection.execute(text(summary_query)).mappings().first()

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nPO status mix:")
        for row in connection.execute(text(status_query)).mappings().all():
            print(
                f"{row['order_status']}: "
                f"{row['row_count']:,} rows | "
                f"{row['ordered_units']:,} units | "
                f"${row['ordered_cost']:,.2f}"
            )

        print("\nPO null check:")
        for key, value in connection.execute(text(null_query)).mappings().first().items():
            print(f"{key}: {value}")

        print("\nPO integrity checks:")
        for key, value in connection.execute(text(integrity_query)).mappings().first().items():
            print(f"{key}: {value}")


def validate_shipments():
    summary_query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT shipment_id) AS distinct_shipment_ids,
            COUNT(DISTINCT purchase_order_id) AS distinct_purchase_order_ids,
            MIN(shipped_date) AS min_shipped_date,
            MAX(shipped_date) AS max_shipped_date,
            MIN(delivered_date) AS min_delivered_date,
            MAX(delivered_date) AS max_delivered_date,
            SUM(shipped_units) AS total_shipped_units,
            SUM(delivered_units) AS total_delivered_units,
            SUM(CASE WHEN delayed_flag = TRUE THEN 1 ELSE 0 END) AS delayed_shipments,
            ROUND(
                SUM(CASE WHEN delayed_flag = TRUE THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(*), 0),
                4
            ) AS delay_rate,
            ROUND(AVG(delay_days), 2) AS avg_delay_days,
            MAX(delay_days) AS max_delay_days
        FROM raw.fact_shipment;
    """

    null_query = """
        SELECT
            SUM(CASE WHEN shipment_id IS NULL THEN 1 ELSE 0 END) AS null_shipment_id,
            SUM(CASE WHEN purchase_order_id IS NULL THEN 1 ELSE 0 END) AS null_purchase_order_id,
            SUM(CASE WHEN supplier_id IS NULL THEN 1 ELSE 0 END) AS null_supplier_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN shipped_date IS NULL THEN 1 ELSE 0 END) AS null_shipped_date,
            SUM(CASE WHEN expected_delivery_date IS NULL THEN 1 ELSE 0 END) AS null_expected_delivery_date,
            SUM(CASE WHEN delivered_date IS NULL THEN 1 ELSE 0 END) AS null_delivered_date,
            SUM(CASE WHEN shipped_units IS NULL THEN 1 ELSE 0 END) AS null_shipped_units,
            SUM(CASE WHEN delivered_units IS NULL THEN 1 ELSE 0 END) AS null_delivered_units,
            SUM(CASE WHEN delayed_flag IS NULL THEN 1 ELSE 0 END) AS null_delayed_flag,
            SUM(CASE WHEN delay_days IS NULL THEN 1 ELSE 0 END) AS null_delay_days
        FROM raw.fact_shipment;
    """

    integrity_query = """
        SELECT
            SUM(CASE WHEN po.purchase_order_id IS NULL THEN 1 ELSE 0 END) AS shipment_without_matching_po,
            SUM(CASE WHEN po.order_status <> 'Delivered' THEN 1 ELSE 0 END) AS shipment_for_non_delivered_po,
            SUM(CASE WHEN s.shipped_units <= 0 THEN 1 ELSE 0 END) AS non_positive_shipped_units,
            SUM(CASE WHEN s.delivered_units <= 0 THEN 1 ELSE 0 END) AS non_positive_delivered_units,
            SUM(CASE WHEN s.delivered_units > s.shipped_units THEN 1 ELSE 0 END) AS delivered_units_exceed_shipped_units,
            SUM(CASE WHEN s.shipped_date < po.order_date THEN 1 ELSE 0 END) AS shipped_before_order_date,
            SUM(CASE WHEN s.delivered_date < s.shipped_date THEN 1 ELSE 0 END) AS delivered_before_shipped_date,
            SUM(CASE WHEN s.delay_days < 0 THEN 1 ELSE 0 END) AS negative_delay_days,
            SUM(CASE WHEN s.delayed_flag = TRUE AND s.delay_days <= 0 THEN 1 ELSE 0 END) AS delayed_flag_without_delay_days,
            SUM(CASE WHEN s.delayed_flag = FALSE AND s.delay_days > 0 THEN 1 ELSE 0 END) AS delay_days_without_delayed_flag
        FROM raw.fact_shipment s
        LEFT JOIN raw.fact_purchase_order po
            ON s.purchase_order_id = po.purchase_order_id;
    """

    supplier_query = """
        SELECT
            sup.delay_risk_level,
            COUNT(*) AS shipment_rows,
            SUM(CASE WHEN sh.delayed_flag = TRUE THEN 1 ELSE 0 END) AS delayed_shipments,
            ROUND(
                SUM(CASE WHEN sh.delayed_flag = TRUE THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(*), 0),
                4
            ) AS delay_rate,
            ROUND(AVG(sh.delay_days), 2) AS avg_delay_days
        FROM raw.fact_shipment sh
        LEFT JOIN raw.dim_supplier sup
            ON sh.supplier_id = sup.supplier_id
        GROUP BY sup.delay_risk_level
        ORDER BY delay_rate DESC;
    """

    with engine.connect() as connection:
        print("\nShipment validation summary:")
        result = connection.execute(text(summary_query)).mappings().first()

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nShipment null check:")
        for key, value in connection.execute(text(null_query)).mappings().first().items():
            print(f"{key}: {value}")

        print("\nShipment integrity checks:")
        for key, value in connection.execute(text(integrity_query)).mappings().first().items():
            print(f"{key}: {value}")

        print("\nShipment delay by supplier risk level:")
        for row in connection.execute(text(supplier_query)).mappings().all():
            print(
                f"{row['delay_risk_level']}: "
                f"{row['shipment_rows']:,} shipments | "
                f"{row['delayed_shipments']:,} delayed | "
                f"delay rate {row['delay_rate']} | "
                f"avg delay {row['avg_delay_days']} days"
            )


def main():
    print("Starting purchase order and shipment load...")

    truncate_tables()

    load_table(PO_FILE, "fact_purchase_order")
    load_table(SHIPMENT_FILE, "fact_shipment")

    validate_purchase_orders()
    validate_shipments()

    print("\nPurchase order and shipment load complete.")


if __name__ == "__main__":
    main()