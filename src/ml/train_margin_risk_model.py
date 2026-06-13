from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAINING_INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_training_features.csv"
)

SCORING_INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_scoring_features.csv"
)

MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "margin_risk_model.joblib"
METRICS_PATH = MODELS_DIR / "model_metrics.json"
FEATURE_COLUMNS_PATH = MODELS_DIR / "feature_columns.json"

PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_model_predictions.csv"
)

MLFLOW_TRACKING_DIR = PROJECT_ROOT / "mlruns"
MLFLOW_EXPERIMENT_NAME = "retail_margin_risk_prediction"

TARGET_COLUMN = "high_margin_risk_next_year"

MIN_ACCEPTABLE_PRECISION = 0.55

EXCLUDE_FROM_FEATURES = [
    # Target / future outcome columns
    "high_margin_risk_next_year",
    "next_year_margin_risk_rate",
    "target_threshold_p75_margin_risk_rate",

    # Direct identifiers
    "store_id",
    "store_name",

    # Used only for chronological split, not as a predictive feature
    "fiscal_year",
]


def select_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    feature_columns = [
        column for column in df.columns
        if column not in EXCLUDE_FROM_FEATURES
    ]

    categorical_columns = [
        column for column in feature_columns
        if df[column].dtype == "object"
    ]

    numeric_columns = [
        column for column in feature_columns
        if column not in categorical_columns
    ]

    return feature_columns, numeric_columns, categorical_columns


def build_preprocessor(
    numeric_columns: list[str],
    categorical_columns: list[str],
    scale_numeric: bool,
) -> ColumnTransformer:
    if scale_numeric:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
    else:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
            ]
        )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ]
    )


def choose_business_threshold(
    y_true: pd.Series,
    y_prob: pd.Series,
    min_precision: float = MIN_ACCEPTABLE_PRECISION,
) -> float:
    """
    Select a business decision threshold for an early-warning model.

    Logic:
    - Prefer thresholds with at least min_precision.
    - Among those thresholds, maximize recall.
    - If no threshold satisfies min_precision, maximize F1.
    """

    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)

    candidate_rows = []

    for threshold, precision, recall in zip(thresholds, precisions[:-1], recalls[:-1]):
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        candidate_rows.append(
            {
                "threshold": float(threshold),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            }
        )

    valid_rows = [
        row for row in candidate_rows
        if row["precision"] >= min_precision
    ]

    if valid_rows:
        best_row = sorted(
            valid_rows,
            key=lambda row: (row["recall"], row["f1"], row["precision"]),
            reverse=True,
        )[0]
    else:
        best_row = sorted(
            candidate_rows,
            key=lambda row: (row["f1"], row["recall"], row["precision"]),
            reverse=True,
        )[0]

    return best_row["threshold"]


def evaluate_model(
    model: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float,
) -> dict[str, Any]:
    y_prob = model.predict_proba(x_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)

    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = 0.0

    return {
        "decision_threshold": float(threshold),
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }


def print_metrics(model_name: str, metrics: dict[str, Any]) -> None:
    print(f"\n{model_name}")
    print("-" * 60)
    print(f"Decision threshold: {metrics['decision_threshold']:.4f}")
    print(f"Accuracy          : {metrics['accuracy']:.4f}")
    print(f"Precision         : {metrics['precision']:.4f}")
    print(f"Recall            : {metrics['recall']:.4f}")
    print(f"F1 Score          : {metrics['f1']:.4f}")
    print(f"ROC-AUC           : {metrics['roc_auc']:.4f}")
    print(f"Confusion Matrix  : {metrics['confusion_matrix']}")


def assign_risk_band(probability: float, decision_threshold: float) -> str:
    """
    Convert model probability into business-friendly risk bands.
    These bands are for interpretation, not model training.
    """

    watch_threshold = max(decision_threshold * 0.60, 0.25)
    critical_threshold = max(decision_threshold + 0.25, 0.75)

    if probability >= critical_threshold:
        return "Critical"

    if probability >= decision_threshold:
        return "High Risk"

    if probability >= watch_threshold:
        return "Watch"

    return "Low"


def validate_input_files() -> None:
    if not TRAINING_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Training file not found: {TRAINING_INPUT_PATH}\n"
            "Run this first: python src/ml/build_margin_risk_features.py"
        )

    if not SCORING_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Scoring file not found: {SCORING_INPUT_PATH}\n"
            "Run this first: python src/ml/build_margin_risk_features.py"
        )


def validate_scoring_columns(
    scoring_df: pd.DataFrame,
    feature_columns: list[str],
) -> None:
    missing_columns = [
        column for column in feature_columns
        if column not in scoring_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Scoring dataset is missing feature columns:\n"
            f"{missing_columns}"
        )


def main() -> None:
    print("Training realistic margin-risk early-warning models...")

    validate_input_files()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    training_df = pd.read_csv(TRAINING_INPUT_PATH)
    scoring_df = pd.read_csv(SCORING_INPUT_PATH)

    print(f"\nLoaded training dataset: {TRAINING_INPUT_PATH}")
    print(f"Training rows   : {len(training_df):,}")
    print(f"Training columns: {len(training_df.columns):,}")

    print(f"\nLoaded scoring dataset: {SCORING_INPUT_PATH}")
    print(f"Scoring rows    : {len(scoring_df):,}")
    print(f"Scoring columns : {len(scoring_df.columns):,}")

    if TARGET_COLUMN not in training_df.columns:
        raise ValueError(f"Missing target column in training data: {TARGET_COLUMN}")

    training_df = training_df.dropna(subset=[TARGET_COLUMN]).copy()
    training_df[TARGET_COLUMN] = training_df[TARGET_COLUMN].astype(int)

    print("\nTraining target distribution:")
    print(training_df[TARGET_COLUMN].value_counts())
    print(training_df[TARGET_COLUMN].value_counts(normalize=True).round(4))

    print("\nScoring fiscal year distribution:")
    print(scoring_df["fiscal_year"].value_counts().sort_index())

    feature_columns, numeric_columns, categorical_columns = select_feature_columns(
        training_df
    )

    validate_scoring_columns(scoring_df, feature_columns)

    print("\nFeature setup:")
    print(f"Total features      : {len(feature_columns)}")
    print(f"Numeric features    : {len(numeric_columns)}")
    print(f"Categorical features: {len(categorical_columns)}")
    print(f"Categorical columns : {categorical_columns}")

    # Realistic chronological validation:
    # Train on FY2023 signals to predict FY2024 high margin-risk.
    # Test on FY2024 signals to predict FY2025 high margin-risk.
    train_df = training_df[training_df["fiscal_year"] == 2023].copy()
    test_df = training_df[training_df["fiscal_year"] == 2024].copy()

    if train_df.empty or test_df.empty:
        raise ValueError(
            "Expected FY2023 rows for training and FY2024 rows for testing."
        )

    x_train = train_df[feature_columns]
    y_train = train_df[TARGET_COLUMN]

    x_test = test_df[feature_columns]
    y_test = test_df[TARGET_COLUMN]

    print("\nChronological train/test split:")
    print(f"Train rows: {len(x_train):,} | fiscal_year = 2023")
    print(f"Test rows : {len(x_test):,} | fiscal_year = 2024")

    print("\nTrain target distribution:")
    print(y_train.value_counts())
    print(y_train.value_counts(normalize=True).round(4))

    print("\nTest target distribution:")
    print(y_test.value_counts())
    print(y_test.value_counts(normalize=True).round(4))

    mlflow.set_tracking_uri(f"file:{MLFLOW_TRACKING_DIR}")
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    model_specs = {
        "logistic_regression": {
            "model": LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
            ),
            "scale_numeric": True,
            "business_role": "early_warning_interpretable_baseline",
        },
        "random_forest": {
            "model": RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
            ),
            "scale_numeric": False,
            "business_role": "nonlinear_tree_benchmark",
        },
        "gradient_boosting": {
            "model": GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=3,
                random_state=42,
            ),
            "scale_numeric": False,
            "business_role": "precision_oriented_boosting_benchmark",
        },
    }

    results: dict[str, dict[str, Any]] = {}
    trained_models: dict[str, Pipeline] = {}

    for model_name, spec in model_specs.items():
        print(f"\nTraining model: {model_name}")

        preprocessor = build_preprocessor(
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            scale_numeric=spec["scale_numeric"],
        )

        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", spec["model"]),
            ]
        )

        with mlflow.start_run(run_name=model_name):
            pipeline.fit(x_train, y_train)

            y_prob_test = pipeline.predict_proba(x_test)[:, 1]

            selected_threshold = choose_business_threshold(
                y_true=y_test,
                y_prob=y_prob_test,
                min_precision=MIN_ACCEPTABLE_PRECISION,
            )

            metrics = evaluate_model(
                model=pipeline,
                x_test=x_test,
                y_test=y_test,
                threshold=selected_threshold,
            )

            mlflow.log_param("model_name", model_name)
            mlflow.log_param("business_role", spec["business_role"])
            mlflow.log_param("target_column", TARGET_COLUMN)
            mlflow.log_param("split_strategy", "train_2023_test_2024")
            mlflow.log_param("train_rows", len(x_train))
            mlflow.log_param("test_rows", len(x_test))
            mlflow.log_param("feature_count", len(feature_columns))
            mlflow.log_param("numeric_feature_count", len(numeric_columns))
            mlflow.log_param("categorical_feature_count", len(categorical_columns))
            mlflow.log_param("min_acceptable_precision", MIN_ACCEPTABLE_PRECISION)
            mlflow.log_param("decision_threshold", selected_threshold)

            for metric_name, metric_value in metrics.items():
                if metric_name != "confusion_matrix":
                    mlflow.log_metric(metric_name, float(metric_value))

            mlflow.log_dict(
                {"confusion_matrix": metrics["confusion_matrix"]},
                "confusion_matrix.json",
            )

            mlflow.sklearn.log_model(
                sk_model=pipeline,
                artifact_path="model",
            )

        results[model_name] = metrics
        trained_models[model_name] = pipeline

        print_metrics(model_name, metrics)

    eligible_models = [
        model_name for model_name, metrics in results.items()
        if metrics["precision"] >= MIN_ACCEPTABLE_PRECISION
    ]

    if eligible_models:
        best_model_name = sorted(
            eligible_models,
            key=lambda model_name: (
                results[model_name]["recall"],
                results[model_name]["roc_auc"],
                results[model_name]["f1"],
            ),
            reverse=True,
        )[0]
    else:
        best_model_name = sorted(
            results.keys(),
            key=lambda model_name: (
                results[model_name]["f1"],
                results[model_name]["recall"],
                results[model_name]["roc_auc"],
            ),
            reverse=True,
        )[0]

    best_model = trained_models[best_model_name]
    best_metrics = results[best_model_name]
    best_threshold = best_metrics["decision_threshold"]

    print("\n" + "=" * 60)
    print(f"Best business model selected: {best_model_name}")
    print("Selection logic: maximize recall with acceptable precision, then ROC-AUC and F1.")
    print_metrics(best_model_name, best_metrics)

    joblib.dump(best_model, MODEL_PATH)

    model_metrics_output = {
        "best_model": best_model_name,
        "business_objective": "early_warning_detection_of_next_year_high_margin_risk",
        "selection_logic": (
            "Maximize recall with acceptable precision; use ROC-AUC and F1 as secondary metrics."
        ),
        "min_acceptable_precision": MIN_ACCEPTABLE_PRECISION,
        "target_column": TARGET_COLUMN,
        "split_strategy": "train_2023_test_2024",
        "model_results": results,
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(model_metrics_output, file, indent=4)

    feature_metadata = {
        "feature_columns": feature_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "excluded_columns": EXCLUDE_FROM_FEATURES,
    }

    with open(FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as file:
        json.dump(feature_metadata, file, indent=4)

    prediction_df = scoring_df.copy()

    prediction_df["risk_probability"] = best_model.predict_proba(
        scoring_df[feature_columns]
    )[:, 1]

    prediction_df["decision_threshold"] = best_threshold

    prediction_df["predicted_high_margin_risk"] = (
        prediction_df["risk_probability"] >= best_threshold
    ).astype(int)

    prediction_df["predicted_risk_band"] = prediction_df["risk_probability"].apply(
        lambda probability: assign_risk_band(
            probability=probability,
            decision_threshold=best_threshold,
        )
    )

    prediction_df["model_version"] = best_model_name

    prediction_df.to_csv(PREDICTIONS_PATH, index=False)

    print("\nSaved outputs:")
    print(f"Model       : {MODEL_PATH}")
    print(f"Metrics     : {METRICS_PATH}")
    print(f"Features    : {FEATURE_COLUMNS_PATH}")
    print(f"Predictions : {PREDICTIONS_PATH}")
    print(f"MLflow runs : {MLFLOW_TRACKING_DIR}")

    print("\nPrediction fiscal year distribution:")
    print(prediction_df["fiscal_year"].value_counts().sort_index())

    print("\nPrediction preview:")
    preview_columns = [
        "fiscal_year",
        "store_id",
        "store_name",
        "region",
        "store_format",
        "category",
        "risk_probability",
        "decision_threshold",
        "predicted_risk_band",
        "predicted_high_margin_risk",
        "high_margin_risk_next_year",
        "model_version",
    ]

    print(prediction_df[preview_columns].tail(10))


if __name__ == "__main__":
    main()