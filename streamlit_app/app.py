from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FEATURES_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_scoring_features.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_margin_risk_predictions_explained.csv"
)

MODEL_PATH = PROJECT_ROOT / "models" / "margin_risk_model.joblib"
FEATURE_COLUMNS_PATH = PROJECT_ROOT / "models" / "feature_columns.json"
MODEL_METRICS_PATH = PROJECT_ROOT / "models" / "model_metrics.json"


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Retail Margin Risk Simulator",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# LOAD DATA / MODEL
# ============================================================

@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    features_df = pd.read_csv(FEATURES_PATH)
    predictions_df = pd.read_csv(PREDICTIONS_PATH)

    for df in [features_df, predictions_df]:
        df["store_category_label"] = (
            df["store_name"].astype(str)
            + " | "
            + df["category"].astype(str)
        )

    return features_df, predictions_df


@st.cache_resource
def load_model_and_features():
    model_pipeline = joblib.load(MODEL_PATH)

    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as file:
        feature_metadata = json.load(file)

    feature_columns = feature_metadata["feature_columns"]

    return model_pipeline, feature_columns


@st.cache_data
def load_model_metrics() -> dict[str, Any]:
    if not MODEL_METRICS_PATH.exists():
        return {}

    with open(MODEL_METRICS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# FORMAT HELPERS
# ============================================================

def format_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.1%}"


def format_currency(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"

    return f"${value:,.0f}"


def get_value(row: pd.Series, column: str, default: float = 0.0) -> float:
    if column not in row.index:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return float(value)


def clean_feature_name(feature_name: str) -> str:
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
        "fulfillment_avg_delay_days": "Fulfillment average lead time days",
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
# ============================================================
# RISK / SCENARIO LOGIC
# ============================================================

def assign_risk_band(probability: float, decision_threshold: float) -> str:
    watch_threshold = max(decision_threshold * 0.60, 0.25)
    critical_threshold = max(decision_threshold + 0.25, 0.75)

    if probability >= critical_threshold:
        return "Critical"

    if probability >= decision_threshold:
        return "High Risk"

    if probability >= watch_threshold:
        return "Watch"

    return "Low"


def classify_scenario(
    original_probability: float,
    simulated_probability: float,
    original_band: str,
    simulated_band: str,
    scenario_preset: str,
) -> str:
    delta = simulated_probability - original_probability

    if scenario_preset == "Operational stress test":
        return "Stress scenario"

    if simulated_probability >= 0.90 and delta >= 0.20:
        return "Stress scenario"

    if delta <= -0.05:
        return "Risk reduction scenario"

    if delta >= 0.05:
        return "Risk escalation scenario"

    if original_band != simulated_band:
        return "Band movement scenario"

    return "Stable scenario"


def generate_scenario_narrative(
    scenario_type: str,
    original_probability: float,
    simulated_probability: float,
    original_band: str,
    simulated_band: str,
    changed_levers_df: pd.DataFrame,
    recommended_action: str,
) -> str:
    delta_pp = (simulated_probability - original_probability) * 100

    if changed_levers_df.empty:
        lever_text = "No business levers were changed."
    else:
        top_changed = changed_levers_df["Lever"].head(3).tolist()
        lever_text = "Key changed levers: " + ", ".join(top_changed) + "."

    if scenario_type == "Risk reduction scenario":
        movement_text = (
            f"The scenario meaningfully reduces predicted margin-risk "
            f"by {abs(delta_pp):.1f} percentage points."
        )
    elif scenario_type == "Risk escalation scenario":
        movement_text = (
            f"The scenario increases predicted margin-risk by {delta_pp:.1f} "
            f"percentage points and should be treated cautiously."
        )
    elif scenario_type == "Stress scenario":
        movement_text = (
            f"This stress scenario pushes predicted risk sharply higher "
            f"by {delta_pp:.1f} percentage points."
        )
    elif scenario_type == "Band movement scenario":
        movement_text = (
            f"The risk band changes from {original_band} to {simulated_band}."
        )
    else:
        movement_text = (
            "The scenario creates only a modest change in predicted margin-risk."
        )

    if original_band != simulated_band:
        band_text = f"The risk band changes from {original_band} to {simulated_band}."
    else:
        band_text = f"The risk band remains {simulated_band}."

    return (
        f"{movement_text} {band_text} {lever_text} "
        f"Recommended business review: {recommended_action}"
    )


# ============================================================
# CASE MODE LOGIC
# ============================================================

def apply_case_mode(df: pd.DataFrame, case_mode: str) -> pd.DataFrame:
    working_df = df.copy()

    if case_mode == "All cases":
        return working_df

    if case_mode == "Best demo cases":
        return working_df[
            working_df["risk_probability"].between(0.30, 0.80, inclusive="both")
        ]

    if case_mode == "Near-threshold cases":
        return working_df[
            (working_df["risk_probability"] - working_df["decision_threshold"]).abs()
            <= 0.10
        ]

    if case_mode == "High-risk improvement cases":
        return working_df[
            (working_df["predicted_risk_band"] == "High Risk")
            & working_df["risk_probability"].between(0.45, 0.80, inclusive="both")
        ]

    if case_mode == "Watch deterioration cases":
        return working_df[
            (working_df["predicted_risk_band"] == "Watch")
            & working_df["risk_probability"].between(0.25, 0.40, inclusive="both")
        ]

    if case_mode == "Critical stress cases":
        return working_df[
            (working_df["predicted_risk_band"] == "Critical")
            & (working_df["risk_probability"] >= 0.90)
        ]

    return working_df


# ============================================================
# SCENARIO PRESETS
# ============================================================

def cap_rate(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def cap_positive(value: float) -> float:
    return max(float(value), 0.0)


def apply_scenario_preset(
    base_features: pd.Series,
    scenario_preset: str,
) -> pd.Series:
    scenario_features = base_features.copy()

    if scenario_preset == "Custom":
        return scenario_features

    if scenario_preset == "Inventory recovery":
        scenario_features["inventory_stockout_rate"] = cap_rate(
            get_value(base_features, "inventory_stockout_rate") * 0.70
        )
        scenario_features["inventory_overstock_rate"] = cap_rate(
            get_value(base_features, "inventory_overstock_rate") * 0.70
        )
        scenario_features["avg_weeks_of_supply"] = cap_positive(
            get_value(base_features, "avg_weeks_of_supply") * 0.70
        )

    elif scenario_preset == "Return reduction":
        scenario_features["refund_rate_value"] = cap_rate(
            get_value(base_features, "refund_rate_value") * 0.55
        )
        scenario_features["markdown_loss_rate"] = cap_rate(
            get_value(base_features, "markdown_loss_rate") * 0.75
        )

    elif scenario_preset == "Leakage reduction":
        scenario_features["markdown_loss_rate"] = cap_rate(
            get_value(base_features, "markdown_loss_rate") * 0.60
        )
        scenario_features["refund_rate_value"] = cap_rate(
            get_value(base_features, "refund_rate_value") * 0.60
        )
        scenario_features["shrink_rate_value"] = cap_rate(
            get_value(base_features, "shrink_rate_value") * 0.60
        )

    elif scenario_preset == "Supply chain improvement":
        scenario_features["supplier_avg_lead_time_days"] = cap_positive(
            get_value(base_features, "supplier_avg_lead_time_days") * 0.80
        )
        scenario_features["fulfillment_avg_lead_time_days"] = cap_positive(
            get_value(base_features, "fulfillment_avg_lead_time_days") * 0.85
        )

    elif scenario_preset == "Operational stress test":
        scenario_features["inventory_stockout_rate"] = cap_rate(
            get_value(base_features, "inventory_stockout_rate") * 1.60
        )
        scenario_features["inventory_overstock_rate"] = cap_rate(
            get_value(base_features, "inventory_overstock_rate") * 1.50
        )
        scenario_features["refund_rate_value"] = cap_rate(
            get_value(base_features, "refund_rate_value") * 1.75
        )
        scenario_features["shrink_rate_value"] = cap_rate(
            get_value(base_features, "shrink_rate_value") * 2.00
        )
        scenario_features["markdown_loss_rate"] = cap_rate(
            get_value(base_features, "markdown_loss_rate") * 1.50
        )
        scenario_features["avg_weeks_of_supply"] = cap_positive(
            get_value(base_features, "avg_weeks_of_supply") * 1.50
        )
        scenario_features["supplier_avg_lead_time_days"] = cap_positive(
            get_value(base_features, "supplier_avg_lead_time_days") * 1.20
        )
        scenario_features["fulfillment_avg_lead_time_days"] = cap_positive(
            get_value(base_features, "fulfillment_avg_lead_time_days") * 1.20
        )

    return scenario_features
# ============================================================
# SLIDER HELPERS
# ============================================================

def get_feature_range(
    features_df: pd.DataFrame,
    column: str,
    current_value: float,
    preset_value: float,
    stress_ranges: bool,
    is_rate: bool,
) -> tuple[float, float]:
    series = pd.to_numeric(features_df[column], errors="coerce").dropna()

    if series.empty:
        if is_rate:
            return 0.0, 1.0

        return 0.0, max(current_value, preset_value, 1.0) * 1.5

    if stress_ranges:
        if is_rate:
            return 0.0, 1.0

        high_value = max(
            float(series.quantile(0.95)) * 1.50,
            current_value * 1.50,
            preset_value * 1.50,
            5.0,
        )

        return 0.0, high_value

    q05 = float(series.quantile(0.05))
    q95 = float(series.quantile(0.95))

    if is_rate:
        lower = max(0.0, min(q05, current_value, preset_value) * 0.80)
        upper = min(1.0, max(q95, current_value, preset_value) * 1.25)

        if upper <= lower:
            upper = min(1.0, lower + 0.05)

        return lower, upper

    lower = max(0.0, min(q05, current_value, preset_value) * 0.75)
    upper = max(q95 * 1.25, current_value, preset_value, 1.0)

    if upper <= lower:
        upper = lower + 1.0

    return lower, upper


def percent_slider(
    label: str,
    preset_value: float,
    min_value: float,
    max_value: float,
    key: str,
    help_text: str | None = None,
) -> float:
    value_pct = st.slider(
        label=label,
        min_value=float(min_value * 100),
        max_value=float(max_value * 100),
        value=float(np.clip(preset_value * 100, min_value * 100, max_value * 100)),
        step=0.1,
        format="%.1f%%",
        key=key,
        help=help_text,
    )

    return value_pct / 100


def numeric_slider(
    label: str,
    preset_value: float,
    min_value: float,
    max_value: float,
    step: float,
    key: str,
    help_text: str | None = None,
) -> float:
    return st.slider(
        label=label,
        min_value=float(min_value),
        max_value=float(max_value),
        value=float(np.clip(preset_value, min_value, max_value)),
        step=float(step),
        key=key,
        help=help_text,
    )


def add_change_row(
    rows: list[dict[str, Any]],
    lever: str,
    current_value: float,
    simulated_value: float,
    is_rate: bool,
) -> None:
    if is_rate:
        current_display = format_pct(current_value)
        simulated_display = format_pct(simulated_value)
        changed = abs(current_value - simulated_value) > 0.0005
    else:
        current_display = f"{current_value:.1f}"
        simulated_display = f"{simulated_value:.1f}"
        changed = abs(current_value - simulated_value) > 0.05

    rows.append(
        {
            "Lever": lever,
            "Current": current_display,
            "Simulated": simulated_display,
            "Changed": changed,
            "Raw Current": current_value,
            "Raw Simulated": simulated_value,
        }
    )


# ============================================================
# MODEL CONTRIBUTION LOGIC
# ============================================================

def get_model_contributions(
    model_pipeline,
    feature_columns: list[str],
    row: pd.Series,
    top_n: int = 5,
) -> pd.DataFrame:
    preprocessor = model_pipeline.named_steps["preprocessor"]
    estimator = model_pipeline.named_steps["model"]

    x = pd.DataFrame([row[feature_columns]])
    transformed_x = preprocessor.transform(x)

    if hasattr(transformed_x, "toarray"):
        transformed_x = transformed_x.toarray()

    feature_names = preprocessor.get_feature_names_out()
    coefficients = estimator.coef_[0]
    contributions = transformed_x[0] * coefficients

    contribution_df = pd.DataFrame(
        {
            "Driver": [clean_feature_name(name) for name in feature_names],
            "Contribution": contributions,
        }
    )

    contribution_df["Abs Contribution"] = contribution_df["Contribution"].abs()

    contribution_df["Effect"] = np.where(
        contribution_df["Contribution"] >= 0,
        "Increases predicted risk",
        "Reduces predicted risk",
    )

    contribution_df = contribution_df.sort_values(
        by="Abs Contribution",
        ascending=False,
    )

    contribution_df["Impact Score"] = contribution_df["Contribution"].round(3)

    return contribution_df[["Driver", "Effect", "Impact Score"]].head(top_n)

# ============================================================
# SCENARIO REPORT
# ============================================================

def build_scenario_report(
    selected_prediction: pd.Series,
    original_probability: float,
    simulated_probability: float,
    original_band: str,
    simulated_band: str,
    scenario_type: str,
    changed_levers_df: pd.DataFrame,
    narrative: str,
) -> str:
    lines = []

    lines.append("Retail Margin Risk Simulator - Scenario Summary")
    lines.append("=" * 60)
    lines.append(f"Fiscal Year: {selected_prediction['fiscal_year']}")
    lines.append(f"Store: {selected_prediction['store_name']}")
    lines.append(f"Category: {selected_prediction['category']}")
    lines.append("")
    lines.append(f"Original Risk Probability: {format_pct(original_probability)}")
    lines.append(f"Simulated Risk Probability: {format_pct(simulated_probability)}")
    lines.append(f"Original Risk Band: {original_band}")
    lines.append(f"Simulated Risk Band: {simulated_band}")
    lines.append(f"Scenario Type: {scenario_type}")
    lines.append("")
    lines.append("Changed Levers:")

    if changed_levers_df.empty:
        lines.append("- No levers changed")
    else:
        for _, row in changed_levers_df.iterrows():
            lines.append(f"- {row['Lever']}: {row['Current']} → {row['Simulated']}")

    lines.append("")
    lines.append("Scenario Interpretation:")
    lines.append(narrative)
    lines.append("")
    lines.append("Model Note:")
    lines.append(
        "This simulator changes selected model input features and recalculates predicted risk. "
        "Results should be interpreted as local sensitivity analysis for investigation planning, "
        "not as causal proof or an automated decision rule."
    )

    return "\n".join(lines)
# ============================================================
# LOAD OBJECTS
# ============================================================

features_df, predictions_df = load_data()
model_pipeline, feature_columns = load_model_and_features()
model_metrics = load_model_metrics()


# ============================================================
# HEADER
# ============================================================

st.title("Retail Margin Risk Simulator")

st.caption(
    "Interactive decision simulator for testing how changes in inventory, margin, returns, shrink, "
    "and fulfillment signals affect predicted next-year margin-risk."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Scenario Selection")

available_years = sorted(predictions_df["fiscal_year"].dropna().unique().tolist())
default_year = 2025 if 2025 in available_years else available_years[-1]

selected_year = st.sidebar.selectbox(
    "Fiscal Year",
    options=available_years,
    index=available_years.index(default_year),
)

year_predictions_base = predictions_df[
    predictions_df["fiscal_year"] == selected_year
].copy()

case_mode_options = [
    "All cases",
    "Best demo cases",
    "Near-threshold cases",
    "High-risk improvement cases",
    "Watch deterioration cases",
    "Critical stress cases",
]

selected_case_mode = st.sidebar.selectbox(
    "Case Mode",
    options=case_mode_options,
    index=0,
)

year_predictions = apply_case_mode(year_predictions_base, selected_case_mode)

if year_predictions.empty:
    st.sidebar.warning(
        "No records for this case mode. Showing all cases for the selected year."
    )
    year_predictions = year_predictions_base.copy()

category_options = ["All"] + sorted(
    year_predictions["category"].dropna().unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Category",
    options=category_options,
)

if selected_category != "All":
    year_predictions = year_predictions[
        year_predictions["category"] == selected_category
    ].copy()

if year_predictions.empty:
    st.warning("No records match the selected category.")
    st.stop()

risk_band_options = ["All"] + sorted(
    year_predictions["predicted_risk_band"].dropna().unique().tolist()
)

selected_risk_band = st.sidebar.selectbox(
    "Predicted Risk Band",
    options=risk_band_options,
)

if selected_risk_band != "All":
    year_predictions = year_predictions[
        year_predictions["predicted_risk_band"] == selected_risk_band
    ].copy()

if year_predictions.empty:
    st.warning("No records match the selected filters.")
    st.stop()

year_predictions = year_predictions.sort_values(
    by="risk_probability",
    ascending=False,
).reset_index(drop=True)

year_predictions["selection_label"] = (
    year_predictions["risk_probability"].apply(lambda value: f"{value:.1%}")
    + " | "
    + year_predictions["predicted_risk_band"].astype(str)
    + " | "
    + year_predictions["store_name"].astype(str)
    + " | "
    + year_predictions["category"].astype(str)
)

selected_row_index = st.sidebar.selectbox(
    "Store-Category",
    options=year_predictions.index.tolist(),
    format_func=lambda index: year_predictions.loc[index, "selection_label"],
)

selected_prediction = year_predictions.loc[selected_row_index]

scenario_preset_options = [
    "Custom",
    "Inventory recovery",
    "Return reduction",
    "Leakage reduction",
    "Supply chain improvement",
    "Operational stress test",
]

selected_scenario_preset = st.sidebar.selectbox(
    "Scenario Preset",
    options=scenario_preset_options,
    index=0,
)

stress_ranges = st.sidebar.checkbox(
    "Enable stress-test ranges",
    value=(selected_scenario_preset == "Operational stress test"),
)

selected_features = features_df[
    (features_df["fiscal_year"] == selected_prediction["fiscal_year"])
    & (features_df["store_id"] == selected_prediction["store_id"])
    & (features_df["category"] == selected_prediction["category"])
].iloc[0]


# ============================================================
# CURRENT PREDICTION
# ============================================================

original_probability = float(selected_prediction["risk_probability"])
decision_threshold = float(selected_prediction["decision_threshold"])
original_band = str(selected_prediction["predicted_risk_band"])

st.subheader("Current Prediction")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric("Risk Probability", format_pct(original_probability))

with summary_col2:
    st.metric("Risk Band", original_band)

with summary_col3:
    st.metric("Decision Threshold", format_pct(decision_threshold))

with summary_col4:
    st.metric(
        "Net Sales Revenue",
        format_currency(get_value(selected_prediction, "net_sales_revenue")),
    )

driver_col, action_col = st.columns([1.1, 1.4])

with driver_col:
    st.markdown("### Original Model Drivers")

    original_driver_table = pd.DataFrame(
        {
            "Driver": [
                selected_prediction.get("top_driver_1", "N/A"),
                selected_prediction.get("top_driver_2", "N/A"),
                selected_prediction.get("top_driver_3", "N/A"),
            ],
            "Effect": [
                selected_prediction.get("top_driver_1_effect", "N/A"),
                selected_prediction.get("top_driver_2_effect", "N/A"),
                selected_prediction.get("top_driver_3_effect", "N/A"),
            ],
        }
    )

    st.dataframe(
        original_driver_table,
        use_container_width=True,
        hide_index=True,
    )

with action_col:
    st.markdown("### Recommended Investigation")

    st.info(
        str(
            selected_prediction.get(
                "recommended_action",
                "Review store-category performance drivers.",
            )
        )
    )
# ============================================================
# WHAT-IF SIMULATOR
# ============================================================

st.divider()

st.subheader("What-if Risk Simulator")

st.caption(
    "Adjust selected business levers and recalculate the model's predicted risk. "
    "This is sensitivity analysis, not a causal optimization engine."
)

preset_features = apply_scenario_preset(
    base_features=selected_features,
    scenario_preset=selected_scenario_preset,
)

scenario_features = selected_features.copy()
change_rows: list[dict[str, Any]] = []

row_key = (
    f"{selected_prediction['fiscal_year']}_"
    f"{selected_prediction['store_id']}_"
    f"{selected_prediction['category']}_"
    f"{selected_scenario_preset}_"
    f"{stress_ranges}"
)

left_col, middle_col, right_col = st.columns(3)

with left_col:
    st.markdown("#### Margin & Leakage")

    margin_levers = [
        (
            "gross_margin_rate",
            "Gross margin rate",
            "Higher gross margin usually improves margin resilience.",
        ),
        (
            "markdown_loss_rate",
            "Markdown loss rate",
            "Higher markdown exposure usually increases margin risk.",
        ),
        (
            "refund_rate_value",
            "Refund value rate",
            "Higher refund exposure can signal return-driven margin leakage.",
        ),
    ]

    for column, label, help_text in margin_levers:
        current = get_value(selected_features, column)
        preset = get_value(preset_features, column)

        min_value, max_value = get_feature_range(
            features_df=features_df,
            column=column,
            current_value=current,
            preset_value=preset,
            stress_ranges=stress_ranges,
            is_rate=True,
        )

        simulated = percent_slider(
            label=label,
            preset_value=preset,
            min_value=min_value,
            max_value=max_value,
            key=f"{row_key}_{column}",
            help_text=help_text,
        )

        scenario_features[column] = simulated

        add_change_row(
            rows=change_rows,
            lever=label,
            current_value=current,
            simulated_value=simulated,
            is_rate=True,
        )

with middle_col:
    st.markdown("#### Inventory")

    inventory_levers = [
        (
            "inventory_stockout_rate",
            "Inventory stockout rate",
            True,
            "Higher stockout rate can indicate lost sales and availability risk.",
        ),
        (
            "inventory_overstock_rate",
            "Inventory overstock rate",
            True,
            "Higher overstock rate can increase markdown and holding-cost exposure.",
        ),
        (
            "avg_weeks_of_supply",
            "Average weeks of supply",
            False,
            "Higher weeks of supply can indicate slower inventory movement.",
        ),
    ]

    for column, label, is_rate, help_text in inventory_levers:
        current = get_value(selected_features, column)
        preset = get_value(preset_features, column)

        min_value, max_value = get_feature_range(
            features_df=features_df,
            column=column,
            current_value=current,
            preset_value=preset,
            stress_ranges=stress_ranges,
            is_rate=is_rate,
        )

        if is_rate:
            simulated = percent_slider(
                label=label,
                preset_value=preset,
                min_value=min_value,
                max_value=max_value,
                key=f"{row_key}_{column}",
                help_text=help_text,
            )
        else:
            simulated = numeric_slider(
                label=label,
                preset_value=preset,
                min_value=min_value,
                max_value=max_value,
                step=0.1,
                key=f"{row_key}_{column}",
                help_text=help_text,
            )

        scenario_features[column] = simulated

        add_change_row(
            rows=change_rows,
            lever=label,
            current_value=current,
            simulated_value=simulated,
            is_rate=is_rate,
        )

with right_col:
    st.markdown("#### Shrink & Fulfillment")

    fulfillment_levers = [
        (
            "shrink_rate_value",
            "Shrink value rate",
            True,
            "Higher shrink exposure can indicate theft, damage, or inventory control issues.",
        ),
        (
            "supplier_avg_lead_time_days",
            "Supplier average lead time days",
            False,
            "Longer supplier lead time can increase replenishment and availability risk.",
        ),
        (
            "fulfillment_avg_lead_time_days",
            "Fulfillment average lead time days",
            False,
            "Longer fulfillment lead time can indicate service and delivery friction.",
        ),
    ]

    for column, label, is_rate, help_text in fulfillment_levers:
        current = get_value(selected_features, column)
        preset = get_value(preset_features, column)

        min_value, max_value = get_feature_range(
            features_df=features_df,
            column=column,
            current_value=current,
            preset_value=preset,
            stress_ranges=stress_ranges,
            is_rate=is_rate,
        )

        if is_rate:
            simulated = percent_slider(
                label=label,
                preset_value=preset,
                min_value=min_value,
                max_value=max_value,
                key=f"{row_key}_{column}",
                help_text=help_text,
            )
        else:
            simulated = numeric_slider(
                label=label,
                preset_value=preset,
                min_value=min_value,
                max_value=max_value,
                step=0.1,
                key=f"{row_key}_{column}",
                help_text=help_text,
            )

        scenario_features[column] = simulated

        add_change_row(
            rows=change_rows,
            lever=label,
            current_value=current,
            simulated_value=simulated,
            is_rate=is_rate,
        )


# ============================================================
# SCENARIO RESULT
# ============================================================

scenario_input_df = pd.DataFrame([scenario_features])

simulated_probability = float(
    model_pipeline.predict_proba(scenario_input_df[feature_columns])[:, 1][0]
)

simulated_band = assign_risk_band(
    probability=simulated_probability,
    decision_threshold=decision_threshold,
)

delta_probability = simulated_probability - original_probability

all_changes_df = pd.DataFrame(change_rows)
changed_levers_df = all_changes_df[all_changes_df["Changed"]].copy()

scenario_type = classify_scenario(
    original_probability=original_probability,
    simulated_probability=simulated_probability,
    original_band=original_band,
    simulated_band=simulated_band,
    scenario_preset=selected_scenario_preset,
)

narrative = generate_scenario_narrative(
    scenario_type=scenario_type,
    original_probability=original_probability,
    simulated_probability=simulated_probability,
    original_band=original_band,
    simulated_band=simulated_band,
    changed_levers_df=changed_levers_df,
    recommended_action=str(
        selected_prediction.get(
            "recommended_action",
            "Review store-category performance drivers.",
        )
    ),
)

st.divider()

st.subheader("Scenario Result")

result_col1, result_col2, result_col3, result_col4 = st.columns(4)

with result_col1:
    st.metric("Original Risk", format_pct(original_probability))

with result_col2:
    st.metric(
        "Simulated Risk",
        format_pct(simulated_probability),
        delta=f"{delta_probability * 100:+.1f} pp",
    )

with result_col3:
    st.metric("Original Band", original_band)

with result_col4:
    st.metric("Simulated Band", simulated_band)

if scenario_type == "Risk reduction scenario":
    st.success(f"Scenario Type: {scenario_type}")
elif scenario_type in ["Risk escalation scenario", "Stress scenario"]:
    st.warning(f"Scenario Type: {scenario_type}")
else:
    st.info(f"Scenario Type: {scenario_type}")

summary_col, change_col = st.columns([1.15, 1])

with summary_col:
    st.markdown("### Scenario Interpretation")

    if scenario_type == "Risk reduction scenario":
        st.success(narrative)
    elif scenario_type in ["Risk escalation scenario", "Stress scenario"]:
        st.warning(narrative)
    else:
        st.info(narrative)

with change_col:
    st.markdown("### Changed Levers")

    if changed_levers_df.empty:
        st.info("No levers changed from the current case.")
    else:
        st.dataframe(
            changed_levers_df[["Lever", "Current", "Simulated"]],
            use_container_width=True,
            hide_index=True,
        )
# ============================================================
# ORIGINAL VS SIMULATED DRIVERS
# ============================================================

st.divider()

st.subheader("Original vs Simulated Model Drivers")

original_contributions = get_model_contributions(
    model_pipeline=model_pipeline,
    feature_columns=feature_columns,
    row=selected_features,
    top_n=5,
)

simulated_contributions = get_model_contributions(
    model_pipeline=model_pipeline,
    feature_columns=feature_columns,
    row=scenario_features,
    top_n=5,
)

st.markdown("#### Original Drivers")

st.dataframe(
    original_contributions,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Driver": st.column_config.TextColumn(
            "Driver",
            width="large",
        ),
        "Effect": st.column_config.TextColumn(
            "Effect",
            width="medium",
        ),
        "Impact Score": st.column_config.NumberColumn(
            "Impact Score",
            format="%.3f",
            width="small",
        ),
    },
)

st.markdown("#### Simulated Drivers")

st.dataframe(
    simulated_contributions,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Driver": st.column_config.TextColumn(
            "Driver",
            width="large",
        ),
        "Effect": st.column_config.TextColumn(
            "Effect",
            width="medium",
        ),
        "Impact Score": st.column_config.NumberColumn(
            "Impact Score",
            format="%.3f",
            width="small",
        ),
    },
)

# ============================================================
# DOWNLOAD SUMMARY
# ============================================================

st.divider()

report_text = build_scenario_report(
    selected_prediction=selected_prediction,
    original_probability=original_probability,
    simulated_probability=simulated_probability,
    original_band=original_band,
    simulated_band=simulated_band,
    scenario_type=scenario_type,
    changed_levers_df=changed_levers_df,
    narrative=narrative,
)

st.download_button(
    label="Download Scenario Summary",
    data=report_text,
    file_name=(
        f"scenario_summary_"
        f"{selected_prediction['store_id']}_"
        f"{str(selected_prediction['category']).replace(' ', '_')}.txt"
    ),
    mime="text/plain",
)


# ============================================================
# MODEL GOVERNANCE
# ============================================================

with st.expander("Model Details and Governance"):
    best_model = model_metrics.get("best_model", "Unknown")
    objective = model_metrics.get("business_objective", "Unknown")
    min_precision = model_metrics.get("min_acceptable_precision", "Unknown")
    split_strategy = model_metrics.get("split_strategy", "Unknown")

    st.markdown(f"**Model selected:** {best_model}")
    st.markdown(f"**Business objective:** {objective}")
    st.markdown(f"**Split strategy:** {split_strategy}")
    st.markdown(f"**Minimum acceptable precision:** {min_precision}")

    model_results = model_metrics.get("model_results", {})

    if best_model in model_results:
        best_metrics = model_results[best_model]

        governance_df = pd.DataFrame(
            [
                {
                    "Metric": "Decision threshold",
                    "Value": format_pct(best_metrics.get("decision_threshold")),
                },
                {
                    "Metric": "Precision",
                    "Value": format_pct(best_metrics.get("precision")),
                },
                {
                    "Metric": "Recall",
                    "Value": format_pct(best_metrics.get("recall")),
                },
                {
                    "Metric": "F1 score",
                    "Value": f"{best_metrics.get('f1', 0):.3f}",
                },
                {
                    "Metric": "ROC-AUC",
                    "Value": f"{best_metrics.get('roc_auc', 0):.3f}",
                },
            ]
        )

        st.dataframe(
            governance_df,
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Model governance note: the selected model is optimized for early-warning detection. "
        "Recall is prioritized because missing high-risk cases is more costly than flagging extra cases for review."
    )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Model note: This simulator changes selected model input features and recalculates predicted risk. "
    "Results should be interpreted as local sensitivity analysis for investigation planning, "
    "not as causal proof or an automated decision rule."
)