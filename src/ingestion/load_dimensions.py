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

load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Check your .env file.")

engine = create_engine(DATABASE_URL)


# ---------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------

DIMENSION_TABLES = {
    "dim_calendar": "dim_calendar.csv",
    "dim_store": "dim_store.csv",
    "dim_product": "dim_product.csv",
    "dim_supplier": "dim_supplier.csv",
    "dim_promotion": "dim_promotion.csv",
}


def truncate_raw_dimension_tables():
    """
    Truncate dimension tables before reloading.
    This is safe at this stage because we have not loaded fact tables yet.
    """

    table_order = [
        "raw.dim_promotion",
        "raw.dim_calendar",
        "raw.dim_supplier",
        "raw.dim_product",
        "raw.dim_store",
    ]

    with engine.begin() as connection:
        for table in table_order:
            print(f"Truncating {table}...")
            connection.execute(text(f"TRUNCATE TABLE {table};"))


def load_csv_to_postgres(table_name, csv_file):
    """
    Load a CSV file into a PostgreSQL raw schema table.
    """

    csv_path = RAW_DATA_DIR / csv_file

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing file: {csv_path}")

    df = pd.read_csv(csv_path)

    print(f"Loading {csv_file} into raw.{table_name}...")
    print(f"Rows: {len(df):,}")

    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )

    print(f"Loaded raw.{table_name} successfully.\n")


def validate_row_counts():
    """
    Print row counts from PostgreSQL after loading.
    """

    print("Validating PostgreSQL row counts...")

    query = """
        SELECT 'dim_calendar' AS table_name, COUNT(*) AS row_count FROM raw.dim_calendar
        UNION ALL
        SELECT 'dim_store', COUNT(*) FROM raw.dim_store
        UNION ALL
        SELECT 'dim_product', COUNT(*) FROM raw.dim_product
        UNION ALL
        SELECT 'dim_supplier', COUNT(*) FROM raw.dim_supplier
        UNION ALL
        SELECT 'dim_promotion', COUNT(*) FROM raw.dim_promotion
        ORDER BY table_name;
    """

    with engine.connect() as connection:
        result = connection.execute(text(query))

        for row in result:
            print(f"{row.table_name}: {row.row_count:,}")


def main():
    print("Starting dimension load into PostgreSQL...")
    print(f"Raw data directory: {RAW_DATA_DIR}")

    truncate_raw_dimension_tables()

    for table_name, csv_file in DIMENSION_TABLES.items():
        load_csv_to_postgres(table_name, csv_file)

    validate_row_counts()

    print("\nDimension load complete.")


if __name__ == "__main__":
    main()