from pathlib import Path
import math
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
RETURN_FILE = RAW_DATA_DIR / "fact_return.csv"
SHRINK_FILE = RAW_DATA_DIR / "fact_shrink_event.csv"
SHIPMENT_FILE = RAW_DATA_DIR / "fact_shipment.csv"

STORE_FILE = RAW_DATA_DIR / "dim_store.csv"
PRODUCT_FILE = RAW_DATA_DIR / "dim_product.csv"
CALENDAR_FILE = RAW_DATA_DIR / "dim_calendar.csv"

OUTPUT_FILE = RAW_DATA_DIR / "fact_inventory_snapshot.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def get_project_week_start(date_value):
    """
    Use the project fiscal calendar start date as the anchor.

    FY2023 starts on 2023-01-29, which is a Sunday.
    Every inventory snapshot represents a store-product-week.
    """

    project_start = pd.Timestamp("2023-01-29")
    date_value = pd.Timestamp(date_value)

    days_since_start = (date_value - project_start).days
    week_number = days_since_start // 7

    return project_start + pd.Timedelta(days=week_number * 7)


def get_target_coverage_weeks(category):
    """
    Different categories need different inventory coverage behavior.
    """

    if category == "Food & Beverage":
        return random.uniform(1.0, 2.2)

    if category == "Household Essentials":
        return random.uniform(2.0, 3.5)

    if category == "Beauty":
        return random.uniform(2.5, 4.5)

    if category == "Apparel & Accessories":
        return random.uniform(3.0, 5.5)

    if category == "Hardlines":
        return random.uniform(3.0, 5.5)

    if category == "Home Furnishings & Decor":
        return random.uniform(4.0, 7.0)

    return random.uniform(2.0, 5.0)


def get_safety_stock_units(category, avg_weekly_units):
    """
    Safety stock protects against demand volatility and supplier delays.
    """

    avg_weekly_units = max(float(avg_weekly_units), 0.25)

    if category in ["Food & Beverage", "Household Essentials"]:
        multiplier = 0.75
    elif category in ["Beauty", "Hardlines"]:
        multiplier = 1.10
    else:
        multiplier = 1.25

    return max(1, math.ceil(avg_weekly_units * multiplier))


def get_overstock_threshold(category, avg_weekly_units):
    """
    Overstock threshold by category.

    This threshold is intentionally conservative because a store may hold
    several weeks of inventory without being truly overstocked. Slow-moving
    and seasonal categories tolerate more inventory before being flagged.
    """

    avg_weekly_units = max(float(avg_weekly_units), 0.25)

    if category == "Food & Beverage":
        weeks = 7.0
        minimum_units = 18
    elif category == "Household Essentials":
        weeks = 9.0
        minimum_units = 22
    elif category == "Beauty":
        weeks = 11.0
        minimum_units = 24
    elif category == "Apparel & Accessories":
        weeks = 13.0
        minimum_units = 28
    elif category == "Hardlines":
        weeks = 13.0
        minimum_units = 28
    elif category == "Home Furnishings & Decor":
        weeks = 15.0
        minimum_units = 32
    else:
        weeks = 10.0
        minimum_units = 24

    return max(minimum_units, math.ceil(avg_weekly_units * weeks))

def build_week_calendar(calendar):
    """
    Build one row per project week using the project fiscal calendar.
    """

    calendar = calendar.copy()
    calendar["calendar_date"] = pd.to_datetime(calendar["calendar_date"])
    calendar["week_start_date"] = calendar["calendar_date"].apply(get_project_week_start)

    week_calendar = (
        calendar
        .groupby("week_start_date", as_index=False)
        .agg(
            date_id=("date_id", "min"),
            week_end_date=("calendar_date", "max")
        )
        .sort_values("week_start_date")
        .reset_index(drop=True)
    )

    week_calendar["project_week_number"] = range(1, len(week_calendar) + 1)

    return week_calendar


def aggregate_weekly_sales(sales, calendar):
    calendar_lookup = calendar[["date_id", "calendar_date"]].copy()
    calendar_lookup["calendar_date"] = pd.to_datetime(calendar_lookup["calendar_date"])
    calendar_lookup["week_start_date"] = calendar_lookup["calendar_date"].apply(get_project_week_start)

    sales_weekly = sales.merge(
        calendar_lookup[["date_id", "week_start_date"]],
        on="date_id",
        how="left"
    )

    weekly_sales = (
        sales_weekly
        .groupby(["week_start_date", "store_id", "product_id"], as_index=False)
        .agg(sold_units=("quantity_sold", "sum"))
    )

    return weekly_sales


def aggregate_weekly_returns(returns, calendar):
    calendar_lookup = calendar[["date_id", "calendar_date"]].copy()
    calendar_lookup["calendar_date"] = pd.to_datetime(calendar_lookup["calendar_date"])
    calendar_lookup["week_start_date"] = calendar_lookup["calendar_date"].apply(get_project_week_start)

    returns_weekly = returns.merge(
        calendar_lookup[["date_id", "week_start_date"]],
        on="date_id",
        how="left"
    )

    weekly_returns = (
        returns_weekly
        .groupby(["week_start_date", "store_id", "product_id"], as_index=False)
        .agg(returned_units=("returned_units", "sum"))
    )

    return weekly_returns


def aggregate_weekly_shrink(shrink, calendar):
    calendar_lookup = calendar[["date_id", "calendar_date"]].copy()
    calendar_lookup["calendar_date"] = pd.to_datetime(calendar_lookup["calendar_date"])
    calendar_lookup["week_start_date"] = calendar_lookup["calendar_date"].apply(get_project_week_start)

    shrink_weekly = shrink.merge(
        calendar_lookup[["date_id", "week_start_date"]],
        on="date_id",
        how="left"
    )

    weekly_shrink = (
        shrink_weekly
        .groupby(["week_start_date", "store_id", "product_id"], as_index=False)
        .agg(shrink_units=("shrink_units", "sum"))
    )

    return weekly_shrink


def aggregate_weekly_shipments(shipments):
    shipments = shipments.copy()
    shipments["delivered_date"] = pd.to_datetime(shipments["delivered_date"])
    shipments["week_start_date"] = shipments["delivered_date"].apply(get_project_week_start)

    weekly_shipments = (
        shipments
        .groupby(["week_start_date", "store_id", "product_id"], as_index=False)
        .agg(received_units=("delivered_units", "sum"))
    )

    return weekly_shipments


# ---------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------

def generate_inventory_snapshots():
    print("Reading raw CSV files...")

    sales = pd.read_csv(SALES_FILE)
    returns = pd.read_csv(RETURN_FILE)
    shrink = pd.read_csv(SHRINK_FILE)
    shipments = pd.read_csv(SHIPMENT_FILE)

    stores = pd.read_csv(STORE_FILE)
    products = pd.read_csv(PRODUCT_FILE)
    calendar = pd.read_csv(CALENDAR_FILE)

    print(f"Sales rows:     {len(sales):,}")
    print(f"Return rows:    {len(returns):,}")
    print(f"Shrink rows:    {len(shrink):,}")
    print(f"Shipment rows:  {len(shipments):,}")
    print(f"Stores:         {len(stores):,}")
    print(f"Products:       {len(products):,}")
    print(f"Calendar rows:  {len(calendar):,}")

    week_calendar = build_week_calendar(calendar)

    print(f"\nProject weeks: {len(week_calendar):,}")

    weekly_sales = aggregate_weekly_sales(sales, calendar)
    weekly_returns = aggregate_weekly_returns(returns, calendar)
    weekly_shrink = aggregate_weekly_shrink(shrink, calendar)
    weekly_shipments = aggregate_weekly_shipments(shipments)

    # Keep only shipments that fall inside our modeled inventory calendar.
    min_week = week_calendar["week_start_date"].min()
    max_week = week_calendar["week_start_date"].max()

    weekly_shipments = weekly_shipments[
        (weekly_shipments["week_start_date"] >= min_week)
        & (weekly_shipments["week_start_date"] <= max_week)
    ]

    print(f"Weekly sales rows:     {len(weekly_sales):,}")
    print(f"Weekly return rows:    {len(weekly_returns):,}")
    print(f"Weekly shrink rows:    {len(weekly_shrink):,}")
    print(f"Weekly shipment rows:  {len(weekly_shipments):,}")

    # Build full store-product-week grid.
    store_product = (
        stores[["store_id"]]
        .merge(products[["product_id", "category", "unit_cost"]], how="cross")
    )

    full_grid = (
        week_calendar[["week_start_date", "date_id", "project_week_number"]]
        .merge(store_product, how="cross")
    )

    print(f"\nFull inventory grid rows: {len(full_grid):,}")

    inventory = full_grid.merge(
        weekly_sales,
        on=["week_start_date", "store_id", "product_id"],
        how="left"
    )

    inventory = inventory.merge(
        weekly_returns,
        on=["week_start_date", "store_id", "product_id"],
        how="left"
    )

    inventory = inventory.merge(
        weekly_shrink,
        on=["week_start_date", "store_id", "product_id"],
        how="left"
    )

    inventory = inventory.merge(
        weekly_shipments,
        on=["week_start_date", "store_id", "product_id"],
        how="left"
    )

    for col in ["sold_units", "returned_units", "shrink_units", "received_units"]:
        inventory[col] = inventory[col].fillna(0).astype(int)

    # Average weekly sales by store-product, used for initial inventory and thresholds.
    avg_weekly_sales = (
        weekly_sales
        .groupby(["store_id", "product_id"], as_index=False)
        .agg(avg_weekly_units=("sold_units", "mean"))
    )

    inventory = inventory.merge(
        avg_weekly_sales,
        on=["store_id", "product_id"],
        how="left"
    )

    inventory["avg_weekly_units"] = inventory["avg_weekly_units"].fillna(0.25)

    print("\nCalculating inventory balances...")

    rows = []

    snapshot_counter = 1

    # Sorting is important so balances carry forward correctly.
    inventory = inventory.sort_values(
        ["store_id", "product_id", "week_start_date"]
    ).reset_index(drop=True)

    for (store_id, product_id), group in inventory.groupby(["store_id", "product_id"], sort=False):
        group = group.sort_values("week_start_date")

        first_row = group.iloc[0]
        category = first_row["category"]
        avg_weekly_units = float(first_row["avg_weekly_units"])
        unit_cost = float(first_row["unit_cost"])

        coverage_weeks = get_target_coverage_weeks(category)
        safety_stock_units = get_safety_stock_units(category, avg_weekly_units)

        beginning_inventory = max(
            safety_stock_units + 2,
            math.ceil(avg_weekly_units * coverage_weeks + random.randint(2, 12))
        )

        for row in group.itertuples(index=False):
            sold_units = int(row.sold_units)
            returned_units = int(row.returned_units)
            shrink_units = int(row.shrink_units)
            received_units = int(row.received_units)

            available_units = beginning_inventory + received_units + returned_units

            if sold_units + shrink_units > available_units:
                stockout_flag = True
                ending_inventory = 0
            else:
                ending_inventory = available_units - sold_units - shrink_units
                stockout_flag = ending_inventory <= safety_stock_units

            overstock_threshold = get_overstock_threshold(category, avg_weekly_units)
            overstock_flag = ending_inventory >= overstock_threshold

            inventory_value = round(ending_inventory * unit_cost, 2)

            rows.append({
                "inventory_snapshot_id": f"INV{snapshot_counter:010d}",
                "date_id": int(row.date_id),
                "store_id": store_id,
                "product_id": product_id,
                "beginning_inventory_units": int(beginning_inventory),
                "ending_inventory_units": int(ending_inventory),
                "received_units": received_units,
                "sold_units": sold_units,
                "returned_units": returned_units,
                "shrink_units": shrink_units,
                "stockout_flag": stockout_flag,
                "overstock_flag": overstock_flag,
                "inventory_value": inventory_value,
            })

            beginning_inventory = ending_inventory
            snapshot_counter += 1

    inventory_snapshot = pd.DataFrame(rows)

    print(f"\nGenerated inventory snapshot rows: {len(inventory_snapshot):,}")

    return inventory_snapshot


def validate_inventory(inventory_snapshot):
    print("\nInventory validation summary:")

    print(f"Rows: {len(inventory_snapshot):,}")
    print(f"Distinct snapshot IDs: {inventory_snapshot['inventory_snapshot_id'].nunique():,}")
    print(f"Date range: {inventory_snapshot['date_id'].min()} to {inventory_snapshot['date_id'].max()}")

    print(f"Total received units: {inventory_snapshot['received_units'].sum():,}")
    print(f"Total sold units: {inventory_snapshot['sold_units'].sum():,}")
    print(f"Total returned units: {inventory_snapshot['returned_units'].sum():,}")
    print(f"Total shrink units: {inventory_snapshot['shrink_units'].sum():,}")
    print(f"Ending inventory units: {inventory_snapshot['ending_inventory_units'].sum():,}")
    print(f"Ending inventory value: ${inventory_snapshot['inventory_value'].sum():,.2f}")

    stockout_count = inventory_snapshot["stockout_flag"].sum()
    overstock_count = inventory_snapshot["overstock_flag"].sum()

    print(f"Stockout snapshot count: {stockout_count:,}")
    print(f"Stockout snapshot rate: {stockout_count / len(inventory_snapshot):.4f}")

    print(f"Overstock snapshot count: {overstock_count:,}")
    print(f"Overstock snapshot rate: {overstock_count / len(inventory_snapshot):.4f}")

    print("\nNegative value checks:")
    print(f"Negative beginning inventory rows: {(inventory_snapshot['beginning_inventory_units'] < 0).sum()}")
    print(f"Negative ending inventory rows: {(inventory_snapshot['ending_inventory_units'] < 0).sum()}")
    print(f"Negative inventory value rows: {(inventory_snapshot['inventory_value'] < 0).sum()}")

    print("\nSample rows:")
    print(inventory_snapshot.head())


def main():
    inventory_snapshot = generate_inventory_snapshots()
    validate_inventory(inventory_snapshot)

    inventory_snapshot.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved fact_inventory_snapshot.csv to: {OUTPUT_FILE}")
    print("Inventory snapshot generation complete.")


if __name__ == "__main__":
    main()