from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPLAINED_PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_predictions_explained.csv"
)

TOP_DRIVERS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_top_drivers.csv"
)

FEATURE_IMPORTANCE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_feature_importance.csv"
)


def get_database_url() -> str:
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or "localhost"
    port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or "5432"
    db = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or "retail_margin_resilience"
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or "postgres"
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD") or "postgres"

    password_encoded = quote_plus(password)

    return f"postgresql+psycopg2://{user}:{password_encoded}@{host}:{port}/{db}"


def validate_file_exists(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}\n"
            "Run the ML scripts first:\n"
            "1. python src/ml/build_margin_risk_features.py\n"
            "2. python src/ml/train_margin_risk_model.py\n"
            "3. python src/ml/explain_margin_risk_model.py"
        )


def clean_dataframe_for_sql(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep pandas nulls as SQL NULLs and avoid problematic infinite values.
    """
    cleaned_df = df.copy()

    cleaned_df = cleaned_df.replace(
        {
            float("inf"): pd.NA,
            float("-inf"): pd.NA,
        }
    )

    return cleaned_df


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    engine,
) -> None:
    print(f"\nLoading ml.{table_name}...")
    print(f"Rows   : {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    df.to_sql(
        name=table_name,
        con=engine,
        schema="ml",
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi",
    )

    print(f"Loaded ml.{table_name} successfully.")


def create_indexes(engine) -> None:
    print("\nCreating ML table indexes...")

    index_sql = [
        """
        CREATE INDEX IF NOT EXISTS idx_ml_margin_risk_predictions_year
        ON ml.margin_risk_predictions (fiscal_year);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ml_margin_risk_predictions_category
        ON ml.margin_risk_predictions (category);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ml_margin_risk_predictions_region
        ON ml.margin_risk_predictions (region);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ml_margin_risk_predictions_band
        ON ml.margin_risk_predictions (predicted_risk_band);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ml_margin_risk_predictions_store_category
        ON ml.margin_risk_predictions (store_id, category);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_ml_feature_importance_feature
        ON ml.margin_risk_feature_importance (feature);
        """,
    ]

    with engine.begin() as connection:
        for statement in index_sql:
            connection.execute(text(statement))

    print("Indexes created successfully.")


def print_validation_summary(engine) -> None:
    print("\nValidation summary:")

    validation_queries = {
        "ml.margin_risk_predictions overall": """
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT store_id) AS distinct_stores,
                COUNT(DISTINCT category) AS distinct_categories,
                ROUND(AVG(risk_probability)::numeric, 4) AS avg_risk_probability,
                SUM(predicted_high_margin_risk) AS predicted_high_risk_count
            FROM ml.margin_risk_predictions;
        """,
        "ml.margin_risk_predictions by fiscal year": """
            SELECT
                fiscal_year,
                COUNT(*) AS row_count,
                ROUND(AVG(risk_probability)::numeric, 4) AS avg_risk_probability,
                SUM(predicted_high_margin_risk) AS predicted_high_risk_count,
                COUNT(next_year_margin_risk_rate) AS rows_with_actual_next_year_outcome,
                COUNT(*) - COUNT(next_year_margin_risk_rate) AS rows_without_actual_next_year_outcome
            FROM ml.margin_risk_predictions
            GROUP BY fiscal_year
            ORDER BY fiscal_year;
        """,
        "ml.margin_risk_top_drivers": """
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT store_id) AS distinct_stores,
                COUNT(DISTINCT category) AS distinct_categories
            FROM ml.margin_risk_top_drivers;
        """,
        "ml.margin_risk_feature_importance": """
            SELECT
                COUNT(*) AS row_count,
                ROUND(MAX(mean_abs_shap_value)::numeric, 4) AS max_importance
            FROM ml.margin_risk_feature_importance;
        """,
    }

    with engine.begin() as connection:
        for section_name, query in validation_queries.items():
            print(f"\n{section_name}")
            results = connection.execute(text(query)).mappings().all()

            for row in results:
                print(dict(row))


def main() -> None:
    print("Loading updated ML outputs into PostgreSQL...")

    validate_file_exists(EXPLAINED_PREDICTIONS_PATH)
    validate_file_exists(TOP_DRIVERS_PATH)
    validate_file_exists(FEATURE_IMPORTANCE_PATH)

    engine = create_engine(get_database_url())

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS ml;"))

    explained_predictions_df = pd.read_csv(EXPLAINED_PREDICTIONS_PATH)
    top_drivers_df = pd.read_csv(TOP_DRIVERS_PATH)
    feature_importance_df = pd.read_csv(FEATURE_IMPORTANCE_PATH)

    explained_predictions_df = clean_dataframe_for_sql(explained_predictions_df)
    top_drivers_df = clean_dataframe_for_sql(top_drivers_df)
    feature_importance_df = clean_dataframe_for_sql(feature_importance_df)

    loaded_at = pd.Timestamp.utcnow()

    explained_predictions_df["loaded_at"] = loaded_at
    top_drivers_df["loaded_at"] = loaded_at
    feature_importance_df["loaded_at"] = loaded_at

    print("\nInput file checks:")
    print(f"Explained predictions rows : {len(explained_predictions_df):,}")
    print(f"Top drivers rows           : {len(top_drivers_df):,}")
    print(f"Feature importance rows    : {len(feature_importance_df):,}")

    print("\nExplained prediction fiscal year distribution:")
    print(explained_predictions_df["fiscal_year"].value_counts().sort_index())

    load_dataframe(
        df=explained_predictions_df,
        table_name="margin_risk_predictions",
        engine=engine,
    )

    load_dataframe(
        df=top_drivers_df,
        table_name="margin_risk_top_drivers",
        engine=engine,
    )

    load_dataframe(
        df=feature_importance_df,
        table_name="margin_risk_feature_importance",
        engine=engine,
    )

    create_indexes(engine)

    print_validation_summary(engine)

    print("\nML output load complete.")


if __name__ == "__main__":
    main()