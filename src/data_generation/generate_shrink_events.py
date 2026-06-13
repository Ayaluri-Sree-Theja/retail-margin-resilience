from pathlib import Path
import random

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SALES_FILE = RAW_DATA_DIR / "fact_sales.csv"
PRODUCT_FILE = RAW_DATA_DIR / "dim_product.csv"
STORE_FILE = RAW_DATA_DIR / "dim_store.csv"
CALENDAR_FILE = RAW_DATA_DIR / "dim_calendar.csv"
OUTPUT_FILE = RAW_DATA_DIR / "fact_shrink_event.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def choose_weighted(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def get_shrink_probability(row):
    """
    Estimate probability of a shrink event for a store-product-date.

    This is simulated logic. It is designed to create realistic shrink
    exposure patterns using product risk, store risk, category, seasonality,
    and sales activity.
    """

    shrink_risk_level = row["shrink_risk_level"]
    risk_profile = row["risk_profile"]
    category = row["category"]
    is_holiday_season = bool(row["is_holiday_season"])
    sold_units = int(row["sold_units"])

    base_rate_by_product_risk = {
        "Low": 0.006,
        "Medium": 0.014,
        "High": 0.030,
    }

    store_risk_multiplier = {
        "Low": 0.85,
        "Medium": 1.35,
        "High": 2.00,
    }

    category_multiplier = {
        "Apparel & Accessories": 1.10,
        "Beauty": 1.45,
        "Household Essentials": 1.05,
        "Food & Beverage": 0.75,
        "Home Furnishings & Decor": 0.70,
        "Hardlines": 1.40,
    }

    base_rate = base_rate_by_product_risk.get(shrink_risk_level, 0.010)
    store_factor = store_risk_multiplier.get(risk_profile, 1.00)
    category_factor = category_multiplier.get(category, 1.00)

    holiday_factor = 1.18 if is_holiday_season else 1.00

    # More activity means more opportunity for mismatches/damage/loss.
    if sold_units >= 8:
        activity_factor = 1.30
    elif sold_units >= 4:
        activity_factor = 1.15
    else:
        activity_factor = 1.00

    probability = base_rate * store_factor * category_factor * holiday_factor * activity_factor

    return min(probability, 0.12)


def get_shrink_reason(category):
    """
    Generate shrink reason by category.
    """

    if category == "Food & Beverage":
        reasons = [
            "Damage",
            "Spoilage/Expiration",
            "Inventory Miscount",
            "Theft",
            "Receiving Mismatch",
        ]
        weights = [0.25, 0.38, 0.18, 0.10, 0.09]

    elif category == "Beauty":
        reasons = [
            "Theft",
            "Damage",
            "Inventory Miscount",
            "Organized Retail Crime",
            "Receiving Mismatch",
        ]
        weights = [0.36, 0.18, 0.18, 0.18, 0.10]

    elif category == "Hardlines":
        reasons = [
            "Theft",
            "Damage",
            "Inventory Miscount",
            "Organized Retail Crime",
            "Receiving Mismatch",
        ]
        weights = [0.30, 0.22, 0.18, 0.20, 0.10]

    elif category == "Apparel & Accessories":
        reasons = [
            "Theft",
            "Damage",
            "Inventory Miscount",
            "Return Processing Loss",
            "Receiving Mismatch",
        ]
        weights = [0.26, 0.18, 0.24, 0.20, 0.12]

    elif category == "Household Essentials":
        reasons = [
            "Damage",
            "Inventory Miscount",
            "Theft",
            "Receiving Mismatch",
            "Return Processing Loss",
        ]
        weights = [0.30, 0.25, 0.18, 0.15, 0.12]

    else:
        reasons = [
            "Damage",
            "Inventory Miscount",
            "Theft",
            "Receiving Mismatch",
            "Return Processing Loss",
        ]
        weights = [0.32, 0.25, 0.16, 0.15, 0.12]

    return choose_weighted(reasons, weights)


def get_shrink_units(category, unit_cost, sold_units):
    """
    Generate shrink units.

    High-value products usually have fewer units per event.
    Lower-value categories may have more units per event.
    """

    sold_units = max(int(sold_units), 1)

    if unit_cost >= 100:
        return 1

    if category in ["Beauty", "Hardlines"]:
        return choose_weighted([1, 2, 3], [0.78, 0.17, 0.05])

    if category == "Food & Beverage":
        return choose_weighted([1, 2, 3, 4, 5, 6], [0.35, 0.25, 0.17, 0.10, 0.08, 0.05])

    if category == "Household Essentials":
        return choose_weighted([1, 2, 3, 4], [0.55, 0.25, 0.14, 0.06])

    return choose_weighted([1, 2, 3], [0.70, 0.22, 0.08])


def get_investigation_flag(shrink_reason, shrink_units, estimated_shrink_value, risk_profile):
    """
    Flag events that would likely require review.
    """

    if shrink_reason == "Organized Retail Crime":
        return True

    if estimated_shrink_value >= 250:
        return True

    if shrink_units >= 5:
        return True

    if risk_profile == "High" and estimated_shrink_value >= 100:
        return True

    return False


# ---------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------

def generate_shrink_events():
    print("Reading sales, product, store, and calendar data...")

    sales = pd.read_csv(SALES_FILE)
    products = pd.read_csv(PRODUCT_FILE)
    stores = pd.read_csv(STORE_FILE)
    calendar = pd.read_csv(CALENDAR_FILE)

    # Aggregate to store-product-date activity.
    sales_activity = (
        sales
        .groupby(["date_id", "store_id", "product_id"], as_index=False)
        .agg(
            sold_units=("quantity_sold", "sum"),
            net_sales_revenue=("net_sales_revenue", "sum")
        )
    )

    enriched = sales_activity.merge(
        products[["product_id", "category", "unit_cost", "shrink_risk_level"]],
        on="product_id",
        how="left"
    )

    enriched = enriched.merge(
        stores[["store_id", "risk_profile"]],
        on="store_id",
        how="left"
    )

    enriched = enriched.merge(
        calendar[["date_id", "is_holiday_season"]],
        on="date_id",
        how="left"
    )

    print(f"Store-product-date activity rows: {len(enriched):,}")

    rows = []
    shrink_counter = 1

    print("\nGenerating shrink events...")

    for row in enriched.itertuples(index=False):
        row_dict = row._asdict()

        probability = get_shrink_probability(row_dict)

        if random.random() > probability:
            continue

        category = row_dict["category"]
        unit_cost = float(row_dict["unit_cost"])
        sold_units = int(row_dict["sold_units"])
        risk_profile = row_dict["risk_profile"]

        shrink_reason = get_shrink_reason(category)
        shrink_units = get_shrink_units(category, unit_cost, sold_units)

        estimated_shrink_value = round(shrink_units * unit_cost, 2)

        investigation_flag = get_investigation_flag(
            shrink_reason=shrink_reason,
            shrink_units=shrink_units,
            estimated_shrink_value=estimated_shrink_value,
            risk_profile=risk_profile
        )

        rows.append({
            "shrink_event_id": f"SHR{shrink_counter:010d}",
            "date_id": int(row_dict["date_id"]),
            "store_id": row_dict["store_id"],
            "product_id": row_dict["product_id"],
            "shrink_reason": shrink_reason,
            "shrink_units": shrink_units,
            "estimated_shrink_value": estimated_shrink_value,
            "investigation_flag": investigation_flag,
        })

        shrink_counter += 1

    shrink_events = pd.DataFrame(rows)

    print(f"\nGenerated shrink event rows: {len(shrink_events):,}")

    return shrink_events, enriched


def validate_shrink_events(shrink_events, enriched):
    print("\nShrink event validation summary:")

    print(f"Eligible activity rows: {len(enriched):,}")
    print(f"Shrink event rows: {len(shrink_events):,}")
    print(f"Shrink event rate: {len(shrink_events) / len(enriched):.4f}")
    print(f"Total shrink units: {shrink_events['shrink_units'].sum():,}")
    print(f"Total estimated shrink value: ${shrink_events['estimated_shrink_value'].sum():,.2f}")
    print(f"Average shrink event value: ${shrink_events['estimated_shrink_value'].mean():,.2f}")
    print(f"Investigation flags: {shrink_events['investigation_flag'].sum():,}")

    print("\nShrink by reason:")
    print(shrink_events["shrink_reason"].value_counts())

    enriched_shrink = shrink_events.merge(
        enriched[["date_id", "store_id", "product_id", "category", "risk_profile", "shrink_risk_level"]],
        on=["date_id", "store_id", "product_id"],
        how="left"
    )

    print("\nShrink by category:")
    print(enriched_shrink["category"].value_counts())

    print("\nShrink by store risk profile:")
    print(enriched_shrink["risk_profile"].value_counts())

    print("\nShrink by product risk level:")
    print(enriched_shrink["shrink_risk_level"].value_counts())


def main():
    shrink_events, enriched = generate_shrink_events()
    validate_shrink_events(shrink_events, enriched)

    shrink_events.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved fact_shrink_event.csv to: {OUTPUT_FILE}")
    print("Shrink event generation complete.")


if __name__ == "__main__":
    main()