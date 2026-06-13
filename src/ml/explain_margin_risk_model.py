from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FEATURES_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_scoring_features.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_model_predictions.csv"
)

MODEL_PATH = PROJECT_ROOT / "models" / "margin_risk_model.joblib"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "models" / "feature_columns.json"

OUTPUT_TOP_DRIVERS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_top_drivers.csv"
)

OUTPUT_FEATURE_IMPORTANCE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_feature_importance.csv"
)

OUTPUT_EXPLAINED_PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_predictions_explained.csv"
)


def clean_feature_name(feature_name: str) -> str:
    """
    Convert sklearn-transformed feature names into business-readable labels.
    """

    name = feature_name.replace("numeric__", "").replace("categorical__", "")

    if name.startswith("region_"):
        return "Region = " + name.replace("region_", "")

    if name.startswith("store_format_"):
        return "Store format = " + name.replace("store_format_", "")

    if name.startswith("category_"):
        return "Category = " + name.replace("category_", "")

    replacements = {
        "net_sales_revenue": "Net sales revenue",
        "gross_margin": "Gross margin",
        "gross_margin_rate": "Gross margin rate",
        "margin_at_risk": "Margin-at-risk",
        "markdown_loss": "Markdown loss",
        "refund_amount": "Refund amount",
        "shrink_value": "Shrink value",
        "transactions": "Transactions",
        "units_sold": "Units sold",
        "inventory_stockout_rate": "Inventory stockout rate",
        "inventory_overstock_rate": "Inventory overstock rate",
        "inventory_sell_through_rate": "Inventory sell-through rate",
        "avg_weeks_of_supply": "Average weeks of supply",
        "avg_inventory_value": "Average inventory value",
        "fulfillment_shipment_count": "Fulfillment shipment count",
        "fulfillment_delay_rate": "Fulfillment delay rate",
        "fulfillment_short_shipment_rate": "Fulfillment short shipment rate",
        "fulfillment_avg_delay_days": "Fulfillment average delay days",
        "fulfillment_avg_lead_time_days": "Fulfillment average lead time days",
        "supplier_count": "Supplier count",
        "supplier_shipment_count": "Supplier shipment count",
        "supplier_delay_rate": "Supplier delay rate",
        "supplier_short_shipment_rate": "Supplier short shipment rate",
        "supplier_avg_delay_days": "Supplier average delay days",
        "supplier_avg_lead_time_days": "Supplier average lead time days",
        "supplier_reliability_score": "Supplier reliability score",
        "margin_risk_rate": "Current margin risk rate",
        "markdown_loss_rate": "Markdown loss rate",
        "refund_rate_value": "Refund value rate",
        "shrink_rate_value": "Shrink value rate",
        "gross_margin_dollars_per_unit": "Gross margin dollars per unit",
        "revenue_per_transaction": "Revenue per transaction",
        "units_per_transaction": "Units per transaction",
    }

    return replacements.get(name, name.replace("_", " ").title())


def get_action_recommendation(top_features: list[str]) -> str:
    """
    Create a business recommendation based on the top model drivers.
    """

    joined = " ".join(top_features).lower()

    if "overstock" in joined or "weeks of supply" in joined:
        return "Review demand planning, replenishment assumptions, and markdown exposure."

    if "stockout" in joined:
        return "Review availability risk, replenishment timing, and lost-sales exposure."

    if "refund" in joined or "return" in joined:
        return "Investigate return reasons, product quality, sizing, and customer experience."

    if "shrink" in joined:
        return "Review shrink controls, theft exposure, damage handling, and inventory accuracy."

    if "markdown" in joined:
        return "Review promotion strategy, pricing pressure, and slow-moving inventory."

    if (
        "supplier" in joined
        or "fulfillment" in joined
        or "lead time" in joined
        or "delay" in joined
    ):
        return "Review supplier reliability, lead-time planning, and replenishment risk."

    if "gross margin" in joined:
        return "Review category margin structure, product cost, and pricing quality."

    if "revenue" in joined or "transactions" in joined or "units sold" in joined:
        return "Evaluate revenue scale together with margin quality and risk exposure."

    return "Review store-category performance drivers and compare against peer segments."


def get_effect_label(shap_value: float) -> str:
    """
    Label whether a feature increases or reduces predicted risk.
    """

    if shap_value > 0:
        return "Increases predicted risk"

    if shap_value < 0:
        return "Reduces predicted risk"

    return "Neutral"


def validate_required_files() -> None:
    required_files = [
        FEATURES_PATH,
        PREDICTIONS_PATH,
        MODEL_PATH,
        FEATURE_COLUMNS_PATH,
    ]

    missing_files = [path for path in required_files if not path.exists()]

    if missing_files:
        missing_text = "\n".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            "Missing required files:\n"
            f"{missing_text}\n\n"
            "Run these first:\n"
            "1. python src/ml/build_margin_risk_features.py\n"
            "2. python src/ml/train_margin_risk_model.py"
        )


def validate_row_alignment(
    features_df: pd.DataFrame,
    predictions_df: pd.DataFrame,
) -> None:
    if len(features_df) != len(predictions_df):
        raise ValueError(
            "Feature and prediction row counts do not match.\n"
            f"Feature rows: {len(features_df):,}\n"
            f"Prediction rows: {len(predictions_df):,}\n"
            "Rerun train_margin_risk_model.py after generating scoring features."
        )

    key_columns = ["fiscal_year", "store_id", "category"]

    for column in key_columns:
        if column not in features_df.columns:
            raise ValueError(f"Missing column in features file: {column}")

        if column not in predictions_df.columns:
            raise ValueError(f"Missing column in predictions file: {column}")

    mismatch_mask = (
        (features_df["fiscal_year"] != predictions_df["fiscal_year"])
        | (features_df["store_id"] != predictions_df["store_id"])
        | (features_df["category"] != predictions_df["category"])
    )

    mismatch_count = int(mismatch_mask.sum())

    if mismatch_count > 0:
        raise ValueError(
            "Feature and prediction rows are not aligned by fiscal_year, store_id, and category.\n"
            f"Mismatched rows: {mismatch_count:,}\n"
            "Rerun train_margin_risk_model.py."
        )


def validate_feature_columns(
    features_df: pd.DataFrame,
    feature_columns: list[str],
) -> None:
    missing_columns = [
        column for column in feature_columns
        if column not in features_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Scoring feature file is missing model feature columns:\n"
            f"{missing_columns}"
        )


def main() -> None:
    print("Generating SHAP-style prediction explanations...")

    validate_required_files()

    features_df = pd.read_csv(FEATURES_PATH).reset_index(drop=True)
    predictions_df = pd.read_csv(PREDICTIONS_PATH).reset_index(drop=True)

    print(f"\nLoaded scoring features: {FEATURES_PATH}")
    print(f"Feature rows   : {len(features_df):,}")
    print(f"Feature columns: {len(features_df.columns):,}")

    print(f"\nLoaded predictions: {PREDICTIONS_PATH}")
    print(f"Prediction rows   : {len(predictions_df):,}")
    print(f"Prediction columns: {len(predictions_df.columns):,}")

    validate_row_alignment(features_df, predictions_df)

    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as file:
        feature_metadata = json.load(file)

    feature_columns = feature_metadata["feature_columns"]

    validate_feature_columns(features_df, feature_columns)

    model_pipeline = joblib.load(MODEL_PATH)

    preprocessor = model_pipeline.named_steps["preprocessor"]
    estimator = model_pipeline.named_steps["model"]

    estimator_name = estimator.__class__.__name__
    print(f"\nLoaded model type: {estimator_name}")

    if estimator_name != "LogisticRegression":
        raise ValueError(
            "This explanation script is designed for the selected LogisticRegression model. "
            f"Current model is: {estimator_name}"
        )

    x = features_df[feature_columns]

    transformed_x = preprocessor.transform(x)

    if hasattr(transformed_x, "toarray"):
        transformed_x = transformed_x.toarray()

    transformed_feature_names = preprocessor.get_feature_names_out()

    clean_feature_names = [
        clean_feature_name(feature_name)
        for feature_name in transformed_feature_names
    ]

    print(f"Rows explained       : {transformed_x.shape[0]:,}")
    print(f"Transformed features : {transformed_x.shape[1]:,}")

    print("\nRunning SHAP LinearExplainer...")

    explainer = shap.LinearExplainer(estimator, transformed_x)
    shap_values = explainer.shap_values(transformed_x)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap_values = np.asarray(shap_values)

    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    feature_importance_df = pd.DataFrame(
        {
            "feature": clean_feature_names,
            "mean_abs_shap_value": mean_abs_shap,
        }
    ).sort_values(
        by="mean_abs_shap_value",
        ascending=False,
    )

    OUTPUT_FEATURE_IMPORTANCE_PATH.parent.mkdir(parents=True, exist_ok=True)

    feature_importance_df.to_csv(
        OUTPUT_FEATURE_IMPORTANCE_PATH,
        index=False,
    )

    driver_rows = []

    for row_index in range(shap_values.shape[0]):
        row_shap_values = shap_values[row_index]
        top_indices = np.argsort(np.abs(row_shap_values))[::-1][:3]

        top_features = [
            clean_feature_names[index]
            for index in top_indices
        ]

        top_values = [
            float(row_shap_values[index])
            for index in top_indices
        ]

        row = {
            "row_id": row_index,
            "fiscal_year": features_df.loc[row_index, "fiscal_year"],
            "store_id": features_df.loc[row_index, "store_id"],
            "store_name": features_df.loc[row_index, "store_name"],
            "region": features_df.loc[row_index, "region"],
            "store_format": features_df.loc[row_index, "store_format"],
            "category": features_df.loc[row_index, "category"],

            "risk_probability": predictions_df.loc[row_index, "risk_probability"],
            "decision_threshold": predictions_df.loc[row_index, "decision_threshold"],
            "predicted_risk_band": predictions_df.loc[row_index, "predicted_risk_band"],
            "predicted_high_margin_risk": predictions_df.loc[
                row_index,
                "predicted_high_margin_risk",
            ],

            "actual_high_margin_risk_next_year": features_df.loc[
                row_index,
                "high_margin_risk_next_year",
            ],
            "next_year_margin_risk_rate": features_df.loc[
                row_index,
                "next_year_margin_risk_rate",
            ],

            "top_driver_1": top_features[0],
            "top_driver_1_effect": get_effect_label(top_values[0]),
            "top_driver_1_shap_value": top_values[0],

            "top_driver_2": top_features[1],
            "top_driver_2_effect": get_effect_label(top_values[1]),
            "top_driver_2_shap_value": top_values[1],

            "top_driver_3": top_features[2],
            "top_driver_3_effect": get_effect_label(top_values[2]),
            "top_driver_3_shap_value": top_values[2],

            "recommended_action": get_action_recommendation(top_features),
            "model_version": predictions_df.loc[row_index, "model_version"],
        }

        driver_rows.append(row)

    top_drivers_df = pd.DataFrame(driver_rows)

    top_drivers_df.to_csv(
        OUTPUT_TOP_DRIVERS_PATH,
        index=False,
    )

    explained_predictions_df = predictions_df.merge(
        top_drivers_df[
            [
                "fiscal_year",
                "store_id",
                "category",
                "top_driver_1",
                "top_driver_1_effect",
                "top_driver_2",
                "top_driver_2_effect",
                "top_driver_3",
                "top_driver_3_effect",
                "recommended_action",
            ]
        ],
        on=["fiscal_year", "store_id", "category"],
        how="left",
    )

    explained_predictions_df.to_csv(
        OUTPUT_EXPLAINED_PREDICTIONS_PATH,
        index=False,
    )

    print("\nExplanation outputs saved:")
    print(f"Top drivers        : {OUTPUT_TOP_DRIVERS_PATH}")
    print(f"Feature importance : {OUTPUT_FEATURE_IMPORTANCE_PATH}")
    print(f"Explained preds    : {OUTPUT_EXPLAINED_PREDICTIONS_PATH}")

    print("\nFeature importance row count:")
    print(len(feature_importance_df))

    print("\nTop global drivers:")
    print(feature_importance_df.head(15))

    print("\nExplained prediction fiscal year distribution:")
    print(explained_predictions_df["fiscal_year"].value_counts().sort_index())

    print("\nPrediction explanation preview:")
    preview_columns = [
        "fiscal_year",
        "store_id",
        "category",
        "risk_probability",
        "predicted_risk_band",
        "top_driver_1",
        "top_driver_1_effect",
        "top_driver_2",
        "top_driver_2_effect",
        "recommended_action",
    ]

    print(top_drivers_df[preview_columns].tail(10))


if __name__ == "__main__":
    main()