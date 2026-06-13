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
RETURN_FILE = RAW_DATA_DIR / "fact_return.csv"

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

def truncate_fact_return():
    """
    Truncate raw.fact_return before reloading.
    """

    with engine.begin() as connection:
        print("Truncating raw.fact_return...")
        connection.execute(text("TRUNCATE TABLE raw.fact_return;"))


def load_fact_return():
    """
    Load fact_return.csv into raw.fact_return.
    """

    if not RETURN_FILE.exists():
        raise FileNotFoundError(f"Missing file: {RETURN_FILE}")

    print(f"Reading file: {RETURN_FILE}")
    returns = pd.read_csv(RETURN_FILE)

    print(f"Rows to load: {len(returns):,}")

    returns.to_sql(
        name="fact_return",
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10000,
    )

    print("Loaded raw.fact_return successfully.")


def validate_fact_return():
    """
    Validate fact_return after loading.
    """

    summary_query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT return_id) AS distinct_return_ids,
            COUNT(DISTINCT sales_id) AS distinct_sales_ids_returned,
            MIN(date_id) AS min_return_date_id,
            MAX(date_id) AS max_return_date_id,
            SUM(returned_units) AS total_returned_units,
            ROUND(SUM(refund_amount), 2) AS total_refund_amount,
            ROUND(AVG(refund_amount), 2) AS avg_refund_amount
        FROM raw.fact_return;
    """

    null_check_query = """
        SELECT
            SUM(CASE WHEN return_id IS NULL THEN 1 ELSE 0 END) AS null_return_id,
            SUM(CASE WHEN sales_id IS NULL THEN 1 ELSE 0 END) AS null_sales_id,
            SUM(CASE WHEN date_id IS NULL THEN 1 ELSE 0 END) AS null_date_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN returned_units IS NULL THEN 1 ELSE 0 END) AS null_returned_units,
            SUM(CASE WHEN refund_amount IS NULL THEN 1 ELSE 0 END) AS null_refund_amount
        FROM raw.fact_return;
    """

    channel_query = """
        SELECT
            channel,
            COUNT(*) AS row_count,
            SUM(returned_units) AS returned_units,
            ROUND(SUM(refund_amount), 2) AS refund_amount
        FROM raw.fact_return
        GROUP BY channel
        ORDER BY row_count DESC;
    """

    reason_query = """
        SELECT
            return_reason,
            COUNT(*) AS row_count,
            ROUND(SUM(refund_amount), 2) AS refund_amount
        FROM raw.fact_return
        GROUP BY return_reason
        ORDER BY row_count DESC;
    """

    category_query = """
        SELECT
            p.category,
            COUNT(*) AS return_rows,
            SUM(r.returned_units) AS returned_units,
            ROUND(SUM(r.refund_amount), 2) AS refund_amount
        FROM raw.fact_return r
        LEFT JOIN raw.dim_product p
            ON r.product_id = p.product_id
        GROUP BY p.category
        ORDER BY return_rows DESC;
    """

    integrity_query = """
        SELECT
            SUM(CASE WHEN s.sales_id IS NULL THEN 1 ELSE 0 END) AS returns_without_matching_sale,
            SUM(CASE WHEN r.returned_units > s.quantity_sold THEN 1 ELSE 0 END) AS returns_exceeding_sold_units,
            SUM(CASE WHEN r.refund_amount <= 0 THEN 1 ELSE 0 END) AS non_positive_refunds
        FROM raw.fact_return r
        LEFT JOIN raw.fact_sales s
            ON r.sales_id = s.sales_id;
    """

    with engine.connect() as connection:
        print("\nFact return validation summary:")
        result = connection.execute(text(summary_query)).mappings().first()

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nNull check:")
        null_results = connection.execute(text(null_check_query)).mappings().first()

        for key, value in null_results.items():
            print(f"{key}: {value}")

        print("\nRows by channel:")
        channel_results = connection.execute(text(channel_query)).mappings().all()

        for row in channel_results:
            print(
                f"{row['channel']}: "
                f"{row['row_count']:,} rows | "
                f"{row['returned_units']:,} units | "
                f"${row['refund_amount']:,.2f}"
            )

        print("\nTop return reasons:")
        reason_results = connection.execute(text(reason_query)).mappings().all()

        for row in reason_results:
            print(
                f"{row['return_reason']}: "
                f"{row['row_count']:,} rows | "
                f"${row['refund_amount']:,.2f}"
            )

        print("\nReturns by category:")
        category_results = connection.execute(text(category_query)).mappings().all()

        for row in category_results:
            print(
                f"{row['category']}: "
                f"{row['return_rows']:,} rows | "
                f"{row['returned_units']:,} units | "
                f"${row['refund_amount']:,.2f}"
            )

        print("\nIntegrity checks:")
        integrity_results = connection.execute(text(integrity_query)).mappings().first()

        for key, value in integrity_results.items():
            print(f"{key}: {value}")


def main():
    print("Starting fact_return load...")

    truncate_fact_return()
    load_fact_return()
    validate_fact_return()

    print("\nfact_return load complete.")


if __name__ == "__main__":
    main()