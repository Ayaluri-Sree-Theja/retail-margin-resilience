from pathlib import Path
import os

from dotenv import load_dotenv
import psycopg2


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INVENTORY_FILE = RAW_DATA_DIR / "fact_inventory_snapshot.csv"

load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Check your .env file.")


COPY_COLUMNS = [
    "inventory_snapshot_id",
    "date_id",
    "store_id",
    "product_id",
    "beginning_inventory_units",
    "ending_inventory_units",
    "received_units",
    "sold_units",
    "returned_units",
    "shrink_units",
    "stockout_flag",
    "overstock_flag",
    "inventory_value",
]


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def truncate_inventory_table(connection):
    with connection.cursor() as cursor:
        print("Truncating raw.fact_inventory_snapshot...")
        cursor.execute("TRUNCATE TABLE raw.fact_inventory_snapshot;")
    connection.commit()


def load_inventory_with_copy(connection):
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {INVENTORY_FILE}")

    columns_sql = ", ".join(COPY_COLUMNS)

    copy_sql = f"""
        COPY raw.fact_inventory_snapshot ({columns_sql})
        FROM STDIN
        WITH CSV HEADER
    """

    print(f"Loading file with COPY: {INVENTORY_FILE}")

    with connection.cursor() as cursor:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
            cursor.copy_expert(copy_sql, file)

    connection.commit()
    print("Loaded raw.fact_inventory_snapshot successfully.")


def validate_inventory(connection):
    summary_query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT inventory_snapshot_id) AS distinct_snapshot_ids,
            MIN(date_id) AS min_date_id,
            MAX(date_id) AS max_date_id,
            SUM(received_units) AS total_received_units,
            SUM(sold_units) AS total_sold_units,
            SUM(returned_units) AS total_returned_units,
            SUM(shrink_units) AS total_shrink_units,
            SUM(ending_inventory_units) AS total_ending_inventory_units,
            ROUND(SUM(inventory_value), 2) AS total_inventory_value,
            SUM(CASE WHEN stockout_flag = TRUE THEN 1 ELSE 0 END) AS stockout_snapshots,
            ROUND(
                SUM(CASE WHEN stockout_flag = TRUE THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(*), 0),
                4
            ) AS stockout_rate,
            SUM(CASE WHEN overstock_flag = TRUE THEN 1 ELSE 0 END) AS overstock_snapshots,
            ROUND(
                SUM(CASE WHEN overstock_flag = TRUE THEN 1 ELSE 0 END)::numeric
                / NULLIF(COUNT(*), 0),
                4
            ) AS overstock_rate
        FROM raw.fact_inventory_snapshot;
    """

    null_check_query = """
        SELECT
            SUM(CASE WHEN inventory_snapshot_id IS NULL THEN 1 ELSE 0 END) AS null_inventory_snapshot_id,
            SUM(CASE WHEN date_id IS NULL THEN 1 ELSE 0 END) AS null_date_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN beginning_inventory_units IS NULL THEN 1 ELSE 0 END) AS null_beginning_inventory_units,
            SUM(CASE WHEN ending_inventory_units IS NULL THEN 1 ELSE 0 END) AS null_ending_inventory_units,
            SUM(CASE WHEN received_units IS NULL THEN 1 ELSE 0 END) AS null_received_units,
            SUM(CASE WHEN sold_units IS NULL THEN 1 ELSE 0 END) AS null_sold_units,
            SUM(CASE WHEN returned_units IS NULL THEN 1 ELSE 0 END) AS null_returned_units,
            SUM(CASE WHEN shrink_units IS NULL THEN 1 ELSE 0 END) AS null_shrink_units,
            SUM(CASE WHEN stockout_flag IS NULL THEN 1 ELSE 0 END) AS null_stockout_flag,
            SUM(CASE WHEN overstock_flag IS NULL THEN 1 ELSE 0 END) AS null_overstock_flag,
            SUM(CASE WHEN inventory_value IS NULL THEN 1 ELSE 0 END) AS null_inventory_value
        FROM raw.fact_inventory_snapshot;
    """

    integrity_query = """
        SELECT
            SUM(CASE WHEN c.date_id IS NULL THEN 1 ELSE 0 END) AS inventory_without_matching_date,
            SUM(CASE WHEN st.store_id IS NULL THEN 1 ELSE 0 END) AS inventory_without_matching_store,
            SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END) AS inventory_without_matching_product,
            SUM(CASE WHEN i.beginning_inventory_units < 0 THEN 1 ELSE 0 END) AS negative_beginning_inventory,
            SUM(CASE WHEN i.ending_inventory_units < 0 THEN 1 ELSE 0 END) AS negative_ending_inventory,
            SUM(CASE WHEN i.received_units < 0 THEN 1 ELSE 0 END) AS negative_received_units,
            SUM(CASE WHEN i.sold_units < 0 THEN 1 ELSE 0 END) AS negative_sold_units,
            SUM(CASE WHEN i.returned_units < 0 THEN 1 ELSE 0 END) AS negative_returned_units,
            SUM(CASE WHEN i.shrink_units < 0 THEN 1 ELSE 0 END) AS negative_shrink_units,
            SUM(CASE WHEN i.inventory_value < 0 THEN 1 ELSE 0 END) AS negative_inventory_value
        FROM raw.fact_inventory_snapshot i
        LEFT JOIN raw.dim_calendar c
            ON i.date_id = c.date_id
        LEFT JOIN raw.dim_store st
            ON i.store_id = st.store_id
        LEFT JOIN raw.dim_product p
            ON i.product_id = p.product_id;
    """

    reconciliation_query = """
        SELECT
            (SELECT SUM(quantity_sold) FROM raw.fact_sales) AS sales_units_from_fact_sales,
            (SELECT SUM(sold_units) FROM raw.fact_inventory_snapshot) AS sales_units_from_inventory,
            (SELECT SUM(returned_units) FROM raw.fact_return) AS returned_units_from_fact_return,
            (SELECT SUM(returned_units) FROM raw.fact_inventory_snapshot) AS returned_units_from_inventory,
            (SELECT SUM(shrink_units) FROM raw.fact_shrink_event) AS shrink_units_from_fact_shrink,
            (SELECT SUM(shrink_units) FROM raw.fact_inventory_snapshot) AS shrink_units_from_inventory,
            (SELECT SUM(delivered_units) FROM raw.fact_shipment WHERE delivered_date <= '2026-01-31') AS delivered_units_from_shipments_in_calendar,
            (SELECT SUM(received_units) FROM raw.fact_inventory_snapshot) AS received_units_from_inventory;
    """

    with connection.cursor() as cursor:
        print("\nInventory validation summary:")
        cursor.execute(summary_query)
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        for key, value in zip(columns, row):
            print(f"{key}: {value}")

        print("\nNull check:")
        cursor.execute(null_check_query)
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        for key, value in zip(columns, row):
            print(f"{key}: {value}")

        print("\nIntegrity checks:")
        cursor.execute(integrity_query)
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        for key, value in zip(columns, row):
            print(f"{key}: {value}")

        print("\nReconciliation checks:")
        cursor.execute(reconciliation_query)
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        for key, value in zip(columns, row):
            print(f"{key}: {value}")


def main():
    print("Starting fact_inventory_snapshot load...")

    connection = get_connection()

    try:
        truncate_inventory_table(connection)
        load_inventory_with_copy(connection)
        validate_inventory(connection)

    finally:
        connection.close()

    print("\nfact_inventory_snapshot load complete.")


if __name__ == "__main__":
    main()