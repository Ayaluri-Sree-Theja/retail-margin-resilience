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
SHRINK_FILE = RAW_DATA_DIR / "fact_shrink_event.csv"

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

def truncate_fact_shrink_event():
    with engine.begin() as connection:
        print("Truncating raw.fact_shrink_event...")
        connection.execute(text("TRUNCATE TABLE raw.fact_shrink_event;"))


def load_fact_shrink_event():
    if not SHRINK_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SHRINK_FILE}")

    print(f"Reading file: {SHRINK_FILE}")
    shrink = pd.read_csv(SHRINK_FILE)

    print(f"Rows to load: {len(shrink):,}")

    shrink.to_sql(
        name="fact_shrink_event",
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=10000,
    )

    print("Loaded raw.fact_shrink_event successfully.")


def validate_fact_shrink_event():
    summary_query = """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT shrink_event_id) AS distinct_shrink_event_ids,
            MIN(date_id) AS min_date_id,
            MAX(date_id) AS max_date_id,
            SUM(shrink_units) AS total_shrink_units,
            ROUND(SUM(estimated_shrink_value), 2) AS total_estimated_shrink_value,
            ROUND(AVG(estimated_shrink_value), 2) AS avg_shrink_event_value,
            SUM(CASE WHEN investigation_flag = TRUE THEN 1 ELSE 0 END) AS investigation_flags
        FROM raw.fact_shrink_event;
    """

    null_check_query = """
        SELECT
            SUM(CASE WHEN shrink_event_id IS NULL THEN 1 ELSE 0 END) AS null_shrink_event_id,
            SUM(CASE WHEN date_id IS NULL THEN 1 ELSE 0 END) AS null_date_id,
            SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) AS null_store_id,
            SUM(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id,
            SUM(CASE WHEN shrink_units IS NULL THEN 1 ELSE 0 END) AS null_shrink_units,
            SUM(CASE WHEN estimated_shrink_value IS NULL THEN 1 ELSE 0 END) AS null_estimated_shrink_value
        FROM raw.fact_shrink_event;
    """

    integrity_query = """
        SELECT
            SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END) AS shrink_without_matching_product,
            SUM(CASE WHEN st.store_id IS NULL THEN 1 ELSE 0 END) AS shrink_without_matching_store,
            SUM(CASE WHEN c.date_id IS NULL THEN 1 ELSE 0 END) AS shrink_without_matching_date,
            SUM(CASE WHEN s.sold_units IS NULL THEN 1 ELSE 0 END) AS shrink_without_sales_activity,
            SUM(CASE WHEN e.shrink_units <= 0 THEN 1 ELSE 0 END) AS non_positive_shrink_units,
            SUM(CASE WHEN e.estimated_shrink_value <= 0 THEN 1 ELSE 0 END) AS non_positive_shrink_value
        FROM raw.fact_shrink_event e
        LEFT JOIN raw.dim_product p
            ON e.product_id = p.product_id
        LEFT JOIN raw.dim_store st
            ON e.store_id = st.store_id
        LEFT JOIN raw.dim_calendar c
            ON e.date_id = c.date_id
        LEFT JOIN (
            SELECT
                date_id,
                store_id,
                product_id,
                SUM(quantity_sold) AS sold_units
            FROM raw.fact_sales
            GROUP BY date_id, store_id, product_id
        ) s
            ON e.date_id = s.date_id
            AND e.store_id = s.store_id
            AND e.product_id = s.product_id;
    """

    reason_query = """
        SELECT
            shrink_reason,
            COUNT(*) AS row_count,
            SUM(shrink_units) AS shrink_units,
            ROUND(SUM(estimated_shrink_value), 2) AS shrink_value
        FROM raw.fact_shrink_event
        GROUP BY shrink_reason
        ORDER BY row_count DESC;
    """

    category_query = """
        SELECT
            p.category,
            COUNT(*) AS row_count,
            SUM(e.shrink_units) AS shrink_units,
            ROUND(SUM(e.estimated_shrink_value), 2) AS shrink_value
        FROM raw.fact_shrink_event e
        LEFT JOIN raw.dim_product p
            ON e.product_id = p.product_id
        GROUP BY p.category
        ORDER BY row_count DESC;
    """

    store_risk_query = """
        SELECT
            st.risk_profile,
            COUNT(*) AS row_count,
            SUM(e.shrink_units) AS shrink_units,
            ROUND(SUM(e.estimated_shrink_value), 2) AS shrink_value
        FROM raw.fact_shrink_event e
        LEFT JOIN raw.dim_store st
            ON e.store_id = st.store_id
        GROUP BY st.risk_profile
        ORDER BY row_count DESC;
    """

    product_risk_query = """
        SELECT
            p.shrink_risk_level,
            COUNT(*) AS row_count,
            SUM(e.shrink_units) AS shrink_units,
            ROUND(SUM(e.estimated_shrink_value), 2) AS shrink_value
        FROM raw.fact_shrink_event e
        LEFT JOIN raw.dim_product p
            ON e.product_id = p.product_id
        GROUP BY p.shrink_risk_level
        ORDER BY row_count DESC;
    """

    with engine.connect() as connection:
        print("\nFact shrink validation summary:")
        result = connection.execute(text(summary_query)).mappings().first()

        for key, value in result.items():
            print(f"{key}: {value}")

        print("\nNull check:")
        null_results = connection.execute(text(null_check_query)).mappings().first()

        for key, value in null_results.items():
            print(f"{key}: {value}")

        print("\nIntegrity checks:")
        integrity_results = connection.execute(text(integrity_query)).mappings().first()

        for key, value in integrity_results.items():
            print(f"{key}: {value}")

        print("\nShrink by reason:")
        for row in connection.execute(text(reason_query)).mappings().all():
            print(
                f"{row['shrink_reason']}: "
                f"{row['row_count']:,} rows | "
                f"{row['shrink_units']:,} units | "
                f"${row['shrink_value']:,.2f}"
            )

        print("\nShrink by category:")
        for row in connection.execute(text(category_query)).mappings().all():
            print(
                f"{row['category']}: "
                f"{row['row_count']:,} rows | "
                f"{row['shrink_units']:,} units | "
                f"${row['shrink_value']:,.2f}"
            )

        print("\nShrink by store risk profile:")
        for row in connection.execute(text(store_risk_query)).mappings().all():
            print(
                f"{row['risk_profile']}: "
                f"{row['row_count']:,} rows | "
                f"{row['shrink_units']:,} units | "
                f"${row['shrink_value']:,.2f}"
            )

        print("\nShrink by product risk level:")
        for row in connection.execute(text(product_risk_query)).mappings().all():
            print(
                f"{row['shrink_risk_level']}: "
                f"{row['row_count']:,} rows | "
                f"{row['shrink_units']:,} units | "
                f"${row['shrink_value']:,.2f}"
            )


def main():
    print("Starting fact_shrink_event load...")

    truncate_fact_shrink_event()
    load_fact_shrink_event()
    validate_fact_shrink_event()

    print("\nfact_shrink_event load complete.")


if __name__ == "__main__":
    main()