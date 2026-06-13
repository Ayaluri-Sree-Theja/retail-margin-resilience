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
SALES_FILE = RAW_DATA_DIR / "fact_sales.csv"

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

def truncate_fact_sales():
    """
    Truncate raw.fact_sales before reloading.
    Safe right now because downstream fact tables have not been generated yet.
    """

    with engine.begin() as connection:
        print("Truncating raw.fact_sales...")
        connection.execute(text("TRUNCATE TABLE raw.fact_sales;"))


def load_fact_sales():
    """
    Load fact_sales.csv into raw.fact_sales.
    """

    if not SALES_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SALES_FILE}")

    print(f"Reading file: {SALES_FILE}")
    sales = pd.read_csv(SALES_FILE)

    print(f"Rows to load: {len(sales):,}")

    sales.to_sql(
        name="fact_sales",
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10000,
    )

    print("Loaded raw.fact_sales successfully.")


def validate_fact_sales():
    """
    Validate fact_sales after loading.
    """

    query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT sales_id) AS distinct_sales_ids,
            COUNT(DISTINCT transaction_id) AS distinct_transactions,
            MIN(date_id) AS min_date_id,
            MAX(date_id) AS max_date_id,
            SUM(quantity_sold) AS total_units_sold,
            ROUND(SUM(gross_revenue), 2) AS gross_revenue,
            ROUND(SUM(net_sales_revenue), 2) AS net_sales_revenue,
            ROUND(SUM(gross_margin), 2) AS gross_margin,
            ROUND(SUM(gross_margin) / NULLIF(SUM(net_sales_revenue), 0), 4) AS gross_margin_rate
        FROM raw.fact_sales;
    """

    channel_query = """
        SELECT
            channel,
            COUNT(*) AS row_count,
            ROUND(SUM(net_sales_revenue), 2) AS net_sales_revenue
        FROM raw.fact_sales
        GROUP BY channel
        ORDER BY row_count DESC;
    """

    null_check_query = """
        SELECT
            SUM(CASE WHEN sales_id IS NULL THEN 1 ELSE 0 END) AS null_sales_id,
            SUM(CASE WHEN date_id IS NULL THEN 1 ELSE 0 END) AS null_date_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN quantity_sold IS NULL THEN 1 ELSE 0 END) AS null_quantity_sold,
            SUM(CASE WHEN net_sales_revenue IS NULL THEN 1 ELSE 0 END) AS null_net_sales_revenue,
            SUM(CASE WHEN gross_margin IS NULL THEN 1 ELSE 0 END) AS null_gross_margin
        FROM raw.fact_sales;
    """

    with engine.connect() as connection:
        print("\nFact sales validation summary:")
        result = connection.execute(text(query)).mappings().first()

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nRows by channel:")
        channel_results = connection.execute(text(channel_query)).mappings().all()

        for row in channel_results:
            print(
                f"{row['channel']}: "
                f"{row['row_count']:,} rows | "
                f"${row['net_sales_revenue']:,.2f}"
            )

        print("\nNull check:")
        null_results = connection.execute(text(null_check_query)).mappings().first()

        for key, value in null_results.items():
            print(f"{key}: {value}")


def main():
    print("Starting fact_sales load...")

    truncate_fact_sales()
    load_fact_sales()
    validate_fact_sales()

    print("\nfact_sales load complete.")


if __name__ == "__main__":
    main()