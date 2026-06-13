from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAINING_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_training_features.csv"
)

SCORING_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_scoring_features.csv"
)

LEGACY_OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_features.csv"
)


def get_database_url() -> str:
    """
    Reads PostgreSQL connection settings from .env.
    Supports either POSTGRES_* or DB_* variable names.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or "localhost"
    port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or "5432"
    db = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or "retail_margin_resilience"
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or "postgres"
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"

    password_encoded = quote_plus(password)

    return f"postgresql+psycopg2://{user}:{password_encoded}@{host}:{port}/{db}"


def validate_columns(df: pd.DataFrame, required_columns: list[str], table_name: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(
            f"\nMissing columns from {table_name}: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace({0: pd.NA})).fillna(0)


def main() -> None:
    print("Building ML margin-risk feature dataset...")

    database_url = get_database_url()
    engine = create_engine(database_url)

    # ---------------------------------------------------------------------
    # 1. Base store-category profitability mart
    # ---------------------------------------------------------------------
    store_sql = """
        SELECT
            fiscal_year,
            store_id,
            store_name,
            region,
            store_format,
            category,
            net_sales_revenue,
            gross_margin,
            gross_margin_rate,
            margin_at_risk,
            markdown_loss,
            refund_amount,
            shrink_value,
            transactions,
            units_sold
        FROM marts.mart_store_category_profitability
        WHERE net_sales_revenue > 0
    """

    store_df = pd.read_sql(store_sql, engine)

    validate_columns(
        store_df,
        [
            "fiscal_year",
            "store_id",
            "store_name",
            "region",
            "store_format",
            "category",
            "net_sales_revenue",
            "gross_margin",
            "gross_margin_rate",
            "margin_at_risk",
            "markdown_loss",
            "refund_amount",
            "shrink_value",
            "transactions",
            "units_sold",
        ],
        "marts.mart_store_category_profitability",
    )

    print(f"Store-category rows: {len(store_df):,}")

    # ---------------------------------------------------------------------
    # 2. Inventory features by year, region, store format, category
    # ---------------------------------------------------------------------
    inventory_sql = """
        SELECT
            fiscal_year,
            region,
            store_format,
            category,
            AVG(stockout_rate) AS inventory_stockout_rate,
            AVG(overstock_rate) AS inventory_overstock_rate,
            AVG(sell_through_rate) AS inventory_sell_through_rate,
            AVG(avg_weeks_of_supply_proxy) AS avg_weeks_of_supply,
            AVG(avg_inventory_value) AS avg_inventory_value
        FROM marts.mart_inventory_health
        GROUP BY
            fiscal_year,
            region,
            store_format,
            category
    """

    inventory_df = pd.read_sql(inventory_sql, engine)

    print(f"Inventory feature rows: {len(inventory_df):,}")

    # ---------------------------------------------------------------------
    # 3. Fulfillment features by year and category
    # ---------------------------------------------------------------------
    fulfillment_sql = """
        SELECT
            fiscal_year,
            category,
            SUM(shipment_count) AS fulfillment_shipment_count,
            SUM(delayed_shipments)::numeric / NULLIF(SUM(shipment_count), 0) AS fulfillment_delay_rate,
            SUM(short_shipments)::numeric / NULLIF(SUM(shipment_count), 0) AS fulfillment_short_shipment_rate,
            AVG(avg_delay_days) AS fulfillment_avg_delay_days,
            AVG(avg_actual_lead_time_days) AS fulfillment_avg_lead_time_days
        FROM marts.mart_fulfillment_reliability
        GROUP BY
            fiscal_year,
            category
    """

    fulfillment_df = pd.read_sql(fulfillment_sql, engine)

    print(f"Fulfillment feature rows: {len(fulfillment_df):,}")

    # ---------------------------------------------------------------------
    # 4. Supplier features by year and category
    # ---------------------------------------------------------------------
    supplier_sql = """
        SELECT
            fiscal_year,
            category,
            COUNT(DISTINCT supplier_id) AS supplier_count,
            SUM(shipment_count) AS supplier_shipment_count,
            SUM(delayed_shipments)::numeric / NULLIF(SUM(shipment_count), 0) AS supplier_delay_rate,
            SUM(short_shipments)::numeric / NULLIF(SUM(shipment_count), 0) AS supplier_short_shipment_rate,
            AVG(avg_delay_days) AS supplier_avg_delay_days,
            AVG(avg_actual_lead_time_days) AS supplier_avg_lead_time_days,
            AVG(reliability_score) AS supplier_reliability_score
        FROM marts.mart_supplier_performance
        GROUP BY
            fiscal_year,
            category
    """

    supplier_df = pd.read_sql(supplier_sql, engine)

    print(f"Supplier feature rows: {len(supplier_df):,}")

    # ---------------------------------------------------------------------
    # 5. Join features
    # ---------------------------------------------------------------------
    features = store_df.merge(
        inventory_df,
        on=["fiscal_year", "region", "store_format", "category"],
        how="left",
    )

    features = features.merge(
        fulfillment_df,
        on=["fiscal_year", "category"],
        how="left",
    )

    features = features.merge(
        supplier_df,
        on=["fiscal_year", "category"],
        how="left",
    )

    # ---------------------------------------------------------------------
    # 6. Current-year derived features
    # ---------------------------------------------------------------------
    features["margin_risk_rate"] = safe_divide(
        features["margin_at_risk"],
        features["net_sales_revenue"],
    )

    features["markdown_loss_rate"] = safe_divide(
        features["markdown_loss"],
        features["net_sales_revenue"],
    )

    features["refund_rate_value"] = safe_divide(
        features["refund_amount"],
        features["net_sales_revenue"],
    )

    features["shrink_rate_value"] = safe_divide(
        features["shrink_value"],
        features["net_sales_revenue"],
    )

    features["gross_margin_dollars_per_unit"] = safe_divide(
        features["gross_margin"],
        features["units_sold"],
    )

    features["revenue_per_transaction"] = safe_divide(
        features["net_sales_revenue"],
        features["transactions"],
    )

    features["units_per_transaction"] = safe_divide(
        features["units_sold"],
        features["transactions"],
    )

    # ---------------------------------------------------------------------
    # 7. Create next-year target
    # ---------------------------------------------------------------------
    p75_margin_risk_rate = features["margin_risk_rate"].quantile(0.75)

    print(f"Store-category margin risk rate P75 threshold: {p75_margin_risk_rate:.4f}")

    target_lookup = features[
        ["store_id", "category", "fiscal_year", "margin_risk_rate"]
    ].copy()

    target_lookup["fiscal_year"] = target_lookup["fiscal_year"] - 1
    target_lookup = target_lookup.rename(
        columns={"margin_risk_rate": "next_year_margin_risk_rate"}
    )

    model_df = features.merge(
        target_lookup,
        on=["store_id", "category", "fiscal_year"],
        how="left",
    )

    scoring_df = features.merge(
    target_lookup,
    on=["store_id", "category", "fiscal_year"],
    how="left",
)

    scoring_df["target_threshold_p75_margin_risk_rate"] = p75_margin_risk_rate

    scoring_df["high_margin_risk_next_year"] = pd.NA

    has_actual_next_year = scoring_df["next_year_margin_risk_rate"].notna()

    scoring_df.loc[has_actual_next_year, "high_margin_risk_next_year"] = (
        scoring_df.loc[has_actual_next_year, "next_year_margin_risk_rate"]
        >= p75_margin_risk_rate
    ).astype(int)

    training_df = scoring_df.dropna(subset=["next_year_margin_risk_rate"]).copy()

    training_df["high_margin_risk_next_year"] = (
        training_df["high_margin_risk_next_year"]
        .astype(int)
    )

    # ---------------------------------------------------------------------
    # 8. Fill feature missing values
    # ---------------------------------------------------------------------
    numeric_cols = model_df.select_dtypes(include=["number"]).columns.tolist()

    for col in numeric_cols:
        model_df[col] = model_df[col].fillna(0)

    # ---------------------------------------------------------------------
    # 9. Save dataset
    # ---------------------------------------------------------------------
    TRAINING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    training_df.to_csv(TRAINING_OUTPUT_PATH, index=False)
    scoring_df.to_csv(SCORING_OUTPUT_PATH, index=False)

    # Keep old filename for backward compatibility.
    training_df.to_csv(LEGACY_OUTPUT_PATH, index=False)

    print("\nML feature datasets created successfully.")

    print(f"Training output path: {TRAINING_OUTPUT_PATH}")
    print(f"Training rows: {len(training_df):,}")
    print(f"Training columns: {len(training_df.columns):,}")

    print(f"\nScoring output path: {SCORING_OUTPUT_PATH}")
    print(f"Scoring rows: {len(scoring_df):,}")
    print(f"Scoring columns: {len(scoring_df.columns):,}")

    print("\nTraining target distribution:")
    print(training_df["high_margin_risk_next_year"].value_counts(dropna=False))
    print(training_df["high_margin_risk_next_year"].value_counts(normalize=True).round(4))

    print("\nScoring fiscal year distribution:")
    print(scoring_df["fiscal_year"].value_counts().sort_index())

    print("\nScoring target availability:")
    print(scoring_df["high_margin_risk_next_year"].value_counts(dropna=False))

    print("\nPreview:")
    preview_cols = [
        "fiscal_year",
        "store_id",
        "store_name",
        "region",
        "store_format",
        "category",
        "margin_risk_rate",
        "next_year_margin_risk_rate",
        "high_margin_risk_next_year",
    ]
    print(scoring_df[preview_cols].tail(10))
    
if __name__ == "__main__":
    main()