from pathlib import Path
import random
from datetime import datetime

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

OUTPUT_FILE = RAW_DATA_DIR / "fact_sales.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def choose_weighted(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def get_fiscal_year(calendar_date):
    """
    Target-like fiscal year approximation based on our project calendar.

    FY2023: 2023-01-29 to 2024-02-03
    FY2024: 2024-02-04 to 2025-02-01
    FY2025: 2025-02-02 to 2026-01-31
    """

    date_value = pd.Timestamp(calendar_date)

    if pd.Timestamp("2023-01-29") <= date_value <= pd.Timestamp("2024-02-03"):
        return 2023
    if pd.Timestamp("2024-02-04") <= date_value <= pd.Timestamp("2025-02-01"):
        return 2024
    if pd.Timestamp("2025-02-02") <= date_value <= pd.Timestamp("2026-01-31"):
        return 2025

    return None


def get_seasonality_multiplier(calendar_row):
    """
    Create retail seasonality.

    Logic:
    - November/December higher demand
    - July/August back-to-school effect
    - Weekends stronger than weekdays
    """

    month = int(calendar_row["month"])
    is_weekend = bool(calendar_row["is_weekend"])

    multiplier = 1.0

    if month in [11, 12]:
        multiplier *= 1.45

    if month in [7, 8]:
        multiplier *= 1.18

    if month in [1, 2]:
        multiplier *= 0.92

    if is_weekend:
        multiplier *= 1.22

    return multiplier


def get_fiscal_year_demand_multiplier(fiscal_year):
    """
    Add year-level demand behavior.

    This is not exact Target data. It is a simulation rule informed by
    the filing narrative that retail demand and comparable sales varied
    across the three years.
    """

    if fiscal_year == 2023:
        return 1.03
    if fiscal_year == 2024:
        return 1.00
    if fiscal_year == 2025:
        return 0.96

    return 1.00


def get_store_multiplier(store_row):
    """
    Store demand varies by format and fulfillment capability.
    """

    store_format = store_row["store_format"]
    fulfillment_enabled = bool(store_row["fulfillment_enabled"])

    if store_format == "Large Format":
        multiplier = 1.45
    elif store_format == "Standard":
        multiplier = 1.00
    else:
        multiplier = 0.55

    if fulfillment_enabled:
        multiplier *= 1.12

    return multiplier


def get_category_demand_multiplier(category, month):
    """
    Category-specific seasonal behavior.
    """

    if category == "Apparel & Accessories":
        if month in [8, 11, 12]:
            return 1.35
        return 1.00

    if category == "Beauty":
        if month in [11, 12, 5]:
            return 1.20
        return 1.00

    if category == "Household Essentials":
        return 1.10

    if category == "Food & Beverage":
        if month in [11, 12]:
            return 1.25
        return 1.05

    if category == "Home Furnishings & Decor":
        if month in [3, 4, 5, 11, 12]:
            return 1.20
        return 1.00

    if category == "Hardlines":
        if month in [11, 12]:
            return 1.40
        if month in [7, 8]:
            return 1.15
        return 1.00

    return 1.00


def get_channel(store_row, calendar_row):
    """
    Generate sales channel.

    Fulfillment-enabled stores have more omnichannel activity.
    """

    fulfillment_enabled = bool(store_row["fulfillment_enabled"])
    is_weekend = bool(calendar_row["is_weekend"])
    month = int(calendar_row["month"])

    if fulfillment_enabled:
        channels = ["Store", "Online", "Drive Up", "Same-Day Delivery"]
        weights = [0.62, 0.18, 0.13, 0.07]
    else:
        channels = ["Store", "Online"]
        weights = [0.82, 0.18]

    # Holiday digital lift
    if month in [11, 12] and fulfillment_enabled:
        channels = ["Store", "Online", "Drive Up", "Same-Day Delivery"]
        weights = [0.54, 0.23, 0.15, 0.08]

    # Weekend store lift
    if is_weekend and fulfillment_enabled:
        channels = ["Store", "Online", "Drive Up", "Same-Day Delivery"]
        weights = [0.66, 0.15, 0.13, 0.06]

    return choose_weighted(channels, weights)


def find_applicable_promotion(product_row, channel, calendar_date, promotions):
    """
    Find a promotion that applies to a sale.

    Promotion applies when:
    - date is within promo window
    - promo category matches product category or All Categories
    - promo channel matches sale channel or All Channels

    Not every eligible sale receives a promotion.
    """

    product_category = product_row["category"]

    eligible = promotions[
        (promotions["start_date"] <= calendar_date)
        & (promotions["end_date"] >= calendar_date)
        & (
            (promotions["category"] == product_category)
            | (promotions["category"] == "All Categories")
        )
        & (
            (promotions["channel"] == channel)
            | (promotions["channel"] == "All Channels")
        )
    ]

    if eligible.empty:
        return None, 0.0

    # Even if eligible, not every item gets the promotion.
    if random.random() > 0.55:
        return None, 0.0

    promo = eligible.sample(n=1, random_state=random.randint(1, 10_000)).iloc[0]

    return promo["promotion_id"], float(promo["discount_pct"])


def generate_sales():
    print("Reading dimension CSVs...")

    calendar = pd.read_csv(RAW_DATA_DIR / "dim_calendar.csv", parse_dates=["calendar_date"])
    stores = pd.read_csv(RAW_DATA_DIR / "dim_store.csv", parse_dates=["opened_date"])
    products = pd.read_csv(RAW_DATA_DIR / "dim_product.csv")
    promotions = pd.read_csv(
        RAW_DATA_DIR / "dim_promotion.csv",
        parse_dates=["start_date", "end_date"]
    )

    print(f"Calendar rows:   {len(calendar):,}")
    print(f"Store rows:      {len(stores):,}")
    print(f"Product rows:    {len(products):,}")
    print(f"Promotion rows:  {len(promotions):,}")

    product_records = products.to_dict("records")
    store_records = stores.to_dict("records")

    rows = []

    sales_counter = 1
    transaction_counter = 1

    print("\nGenerating sales transaction lines...")

    for _, calendar_row in calendar.iterrows():
        calendar_date = calendar_row["calendar_date"]
        date_id = int(calendar_row["date_id"])
        fiscal_year = get_fiscal_year(calendar_date)

        seasonality_multiplier = get_seasonality_multiplier(calendar_row)
        year_multiplier = get_fiscal_year_demand_multiplier(fiscal_year)

        month = int(calendar_row["month"])

        for store_row in store_records:
            store_multiplier = get_store_multiplier(store_row)

            # Base number of transaction lines by store-day
            base_lambda = 10

            expected_lines = base_lambda * seasonality_multiplier * year_multiplier * store_multiplier

            # Add noise so it does not look too perfect
            expected_lines *= random.uniform(0.75, 1.30)

            n_lines = np.random.poisson(lam=max(expected_lines, 1))

            for _ in range(n_lines):
                product_row = random.choice(product_records)

                category_multiplier = get_category_demand_multiplier(
                    product_row["category"],
                    month
                )

                # Category multiplier affects whether this line survives.
                # This gives stronger categories more representation during relevant periods.
                if random.random() > min(category_multiplier / 1.5, 0.98):
                    continue

                channel = get_channel(store_row, calendar_row)

                promotion_id, discount_pct = find_applicable_promotion(
                    product_row=product_row,
                    channel=channel,
                    calendar_date=calendar_date,
                    promotions=promotions
                )

                unit_price = round(float(product_row["unit_price"]), 2)
                unit_cost = round(float(product_row["unit_cost"]), 2)

                # Most transaction lines are 1 item; essentials/food can have more.
                if product_row["category"] in ["Household Essentials", "Food & Beverage"]:
                    quantity_sold = choose_weighted([1, 2, 3, 4], [0.55, 0.25, 0.14, 0.06])
                else:
                    quantity_sold = choose_weighted([1, 2, 3], [0.78, 0.17, 0.05])

                final_sale_price = round(unit_price * (1 - discount_pct), 2)

                gross_revenue = round(quantity_sold * unit_price, 2)
                net_sales_revenue = round(quantity_sold * final_sale_price, 2)
                gross_margin = round(net_sales_revenue - (quantity_sold * unit_cost), 2)

                sales_id = f"SAL{sales_counter:010d}"
                transaction_id = f"TXN{transaction_counter:010d}"

                rows.append({
                    "sales_id": sales_id,
                    "transaction_id": transaction_id,
                    "date_id": date_id,
                    "store_id": store_row["store_id"],
                    "product_id": product_row["product_id"],
                    "promotion_id": promotion_id,
                    "channel": channel,
                    "quantity_sold": quantity_sold,
                    "unit_price": unit_price,
                    "discount_pct": round(discount_pct, 4),
                    "final_sale_price": final_sale_price,
                    "gross_revenue": gross_revenue,
                    "net_sales_revenue": net_sales_revenue,
                    "unit_cost": unit_cost,
                    "gross_margin": gross_margin,
                })

                sales_counter += 1

                # Approximate multiple lines per transaction sometimes
                if random.random() < 0.70:
                    transaction_counter += 1

    sales = pd.DataFrame(rows)

    print(f"\nGenerated sales rows: {len(sales):,}")

    return sales


def validate_sales(sales):
    print("\nSales validation summary:")

    print(f"Total rows: {len(sales):,}")
    print(f"Total gross revenue: ${sales['gross_revenue'].sum():,.2f}")
    print(f"Total net sales revenue: ${sales['net_sales_revenue'].sum():,.2f}")
    print(f"Total gross margin: ${sales['gross_margin'].sum():,.2f}")

    print("\nRows by channel:")
    print(sales["channel"].value_counts())

    print("\nRows by year:")
    sales["year"] = sales["date_id"].astype(str).str.slice(0, 4)
    print(sales["year"].value_counts().sort_index())

    print("\nAverage discount:")
    print(round(sales["discount_pct"].mean(), 4))

    print("\nGross margin rate:")
    margin_rate = sales["gross_margin"].sum() / sales["net_sales_revenue"].sum()
    print(round(margin_rate, 4))

    sales.drop(columns=["year"], inplace=True)


def main():
    sales = generate_sales()
    validate_sales(sales)

    sales.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved fact_sales.csv to: {OUTPUT_FILE}")
    print("Sales generation complete.")


if __name__ == "__main__":
    main()