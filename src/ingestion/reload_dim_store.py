from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STORE_FILE = RAW_DATA_DIR / "dim_store.csv"

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing. Check your .env file.")

engine = create_engine(DATABASE_URL)


def main():
    stores = pd.read_csv(STORE_FILE)

    with engine.begin() as connection:
        print("Truncating raw.dim_store...")
        connection.execute(text("TRUNCATE TABLE raw.dim_store;"))

    print(f"Reloading raw.dim_store with {len(stores):,} rows...")

    stores.to_sql(
        name="dim_store",
        con=engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=5000,
    )

    query = """
        SELECT
            risk_profile,
            COUNT(*) AS store_count
        FROM raw.dim_store
        GROUP BY risk_profile
        ORDER BY store_count DESC;
    """

    with engine.connect() as connection:
        results = connection.execute(text(query)).mappings().all()

    print("\nPostgreSQL risk profile distribution:")
    for row in results:
        print(f"{row['risk_profile']}: {row['store_count']}")


if __name__ == "__main__":
    main()