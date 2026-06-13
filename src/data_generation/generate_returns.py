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
CALENDAR_FILE = RAW_DATA_DIR / "dim_calendar.csv"
OUTPUT_FILE = RAW_DATA_DIR / "fact_return.csv"


# ---------------------------------------------------------------------
# Return logic helpers
# ---------------------------------------------------------------------

def choose_weighted(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def get_return_probability(row):
    """
    Estimate return probability based on category, channel, product risk,
    and discounting.

    This is simulated logic, not Target internal data.
    """

    category = row["category"]
    channel = row["channel"]
    return_risk_level = row["return_risk_level"]
    discount_pct = float(row["discount_pct"])
    month = int(row["month"])

    category_base_rate = {
        "Apparel & Accessories": 0.120,
        "Beauty": 0.035,
        "Household Essentials": 0.018,
        "Food & Beverage": 0.006,
        "Home Furnishings & Decor": 0.070,
        "Hardlines": 0.055,
    }

    channel_multiplier = {
        "Store": 0.80,
        "Online": 1.65,
        "Drive Up": 1.20,
        "Same-Day Delivery": 1.35,
    }

    risk_multiplier = {
        "Low": 0.80,
        "Medium": 1.00,
        "High": 1.25,
    }

    base_rate = category_base_rate.get(category, 0.035)
    channel_factor = channel_multiplier.get(channel, 1.00)
    risk_factor = risk_multiplier.get(return_risk_level, 1.00)

    # Heavy discount items are slightly less likely to be returned.
    if discount_pct >= 0.30:
        discount_factor = 0.85
    elif discount_pct >= 0.15:
        discount_factor = 0.92
    else:
        discount_factor = 1.00

    # Holiday purchases have slightly higher post-purchase return behavior.
    holiday_factor = 1.15 if month in [11, 12] else 1.00

    probability = base_rate * channel_factor * risk_factor * discount_factor * holiday_factor

    # Cap probability so it does not become unrealistic.
    return min(probability, 0.22)


def get_return_lag_days(category):
    """
    Estimate days between sale and return.
    """

    if category == "Food & Beverage":
        return random.randint(1, 5)

    if category == "Household Essentials":
        return random.randint(1, 14)

    if category == "Beauty":
        return random.randint(2, 25)

    if category == "Apparel & Accessories":
        return random.randint(2, 45)

    if category == "Home Furnishings & Decor":
        return random.randint(3, 60)

    if category == "Hardlines":
        return random.randint(2, 50)

    return random.randint(2, 30)


def get_return_reason(category, channel):
    """
    Generate realistic return reason by category.
    """

    if category == "Apparel & Accessories":
        reasons = ["Size/Fit Issue", "Changed Mind", "Quality Issue", "Wrong Item", "Late Delivery"]
        weights = [0.42, 0.25, 0.15, 0.10, 0.08]

    elif category == "Beauty":
        reasons = ["Product Preference", "Quality Issue", "Damaged Item", "Changed Mind", "Wrong Item"]
        weights = [0.35, 0.22, 0.16, 0.17, 0.10]

    elif category == "Household Essentials":
        reasons = ["Damaged Item", "Wrong Item", "Changed Mind", "Quality Issue", "Duplicate Purchase"]
        weights = [0.25, 0.25, 0.20, 0.18, 0.12]

    elif category == "Food & Beverage":
        reasons = ["Damaged Item", "Quality Issue", "Expired/Unsatisfactory", "Wrong Item"]
        weights = [0.30, 0.30, 0.25, 0.15]

    elif category == "Home Furnishings & Decor":
        reasons = ["Changed Mind", "Damaged Item", "Wrong Item", "Quality Issue", "Size/Space Issue"]
        weights = [0.32, 0.24, 0.17, 0.15, 0.12]

    elif category == "Hardlines":
        reasons = ["Defective Item", "Changed Mind", "Wrong Item", "Missing Parts", "Damaged Item"]
        weights = [0.28, 0.24, 0.18, 0.15, 0.15]

    else:
        reasons = ["Changed Mind", "Wrong Item", "Damaged Item", "Quality Issue"]
        weights = [0.35, 0.25, 0.20, 0.20]

    # Online and delivery channels have slightly more wrong-item/late-delivery behavior.
    if channel in ["Online", "Same-Day Delivery"]:
        if random.random() < 0.08:
            return "Late Delivery"

    return choose_weighted(reasons, weights)


def get_return_condition(return_reason):
    """
    Assign return condition based on reason.
    """

    if return_reason in ["Damaged Item", "Defective Item", "Missing Parts", "Expired/Unsatisfactory"]:
        conditions = ["Damaged", "Unsellable", "Opened", "Resellable"]
        weights = [0.42, 0.28, 0.20, 0.10]

    elif return_reason in ["Size/Fit Issue", "Changed Mind", "Duplicate Purchase", "Size/Space Issue"]:
        conditions = ["Resellable", "Opened", "Damaged"]
        weights = [0.76, 0.20, 0.04]

    elif return_reason in ["Wrong Item", "Late Delivery"]:
        conditions = ["Resellable", "Opened", "Damaged"]
        weights = [0.64, 0.28, 0.08]

    else:
        conditions = ["Resellable", "Opened", "Damaged", "Unsellable"]
        weights = [0.55, 0.28, 0.12, 0.05]

    return choose_weighted(conditions, weights)


def get_returned_units(quantity_sold):
    """
    Return quantity cannot exceed sold quantity.
    """

    quantity_sold = int(quantity_sold)

    if quantity_sold <= 1:
        return 1

    return choose_weighted(
        list(range(1, quantity_sold + 1)),
        [0.70] + [0.30 / (quantity_sold - 1)] * (quantity_sold - 1)
    )


# ---------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------

def generate_returns():
    print("Reading sales, product, and calendar data...")

    sales = pd.read_csv(SALES_FILE)
    products = pd.read_csv(PRODUCT_FILE)
    calendar = pd.read_csv(CALENDAR_FILE, parse_dates=["calendar_date"])

    calendar_lookup = calendar[["date_id", "calendar_date", "month"]].copy()

    sales = sales.merge(
        products[["product_id", "category", "return_risk_level"]],
        on="product_id",
        how="left"
    )

    sales = sales.merge(
        calendar_lookup,
        on="date_id",
        how="left"
    )

    max_calendar_date = calendar["calendar_date"].max()

    print(f"Sales rows available: {len(sales):,}")
    print(f"Max calendar date: {max_calendar_date.date()}")

    rows = []
    return_counter = 1

    print("\nGenerating return events...")

    for row in sales.itertuples(index=False):
        row_dict = row._asdict()

        return_probability = get_return_probability(row_dict)

        if random.random() > return_probability:
            continue

        sale_date = row_dict["calendar_date"]
        category = row_dict["category"]
        channel = row_dict["channel"]

        lag_days = get_return_lag_days(category)
        return_date = sale_date + pd.Timedelta(days=lag_days)

        # Do not create returns outside our modeled calendar range.
        if return_date > max_calendar_date:
            continue

        return_date_id = int(return_date.strftime("%Y%m%d"))

        returned_units = get_returned_units(row_dict["quantity_sold"])
        final_sale_price = float(row_dict["final_sale_price"])
        refund_amount = round(returned_units * final_sale_price, 2)

        return_reason = get_return_reason(category, channel)
        return_condition = get_return_condition(return_reason)

        rows.append({
            "return_id": f"RET{return_counter:010d}",
            "sales_id": row_dict["sales_id"],
            "date_id": return_date_id,
            "store_id": row_dict["store_id"],
            "product_id": row_dict["product_id"],
            "channel": channel,
            "return_reason": return_reason,
            "returned_units": returned_units,
            "refund_amount": refund_amount,
            "return_condition": return_condition,
        })

        return_counter += 1

    returns = pd.DataFrame(rows)

    print(f"\nGenerated return rows: {len(returns):,}")

    return returns, sales


def validate_returns(returns, sales):
    print("\nReturn validation summary:")

    total_sales_rows = len(sales)
    total_sales_units = sales["quantity_sold"].sum()
    total_return_rows = len(returns)
    total_returned_units = returns["returned_units"].sum()
    total_refund_amount = returns["refund_amount"].sum()

    print(f"Sales rows: {total_sales_rows:,}")
    print(f"Return rows: {total_return_rows:,}")
    print(f"Return row rate: {total_return_rows / total_sales_rows:.4f}")
    print(f"Total sales units: {total_sales_units:,}")
    print(f"Total returned units: {total_returned_units:,}")
    print(f"Unit return rate: {total_returned_units / total_sales_units:.4f}")
    print(f"Total refund amount: ${total_refund_amount:,.2f}")

    print("\nReturns by channel:")
    print(returns["channel"].value_counts())

    print("\nReturns by reason:")
    print(returns["return_reason"].value_counts())

    print("\nReturns by condition:")
    print(returns["return_condition"].value_counts())

    enriched_returns = returns.merge(
        sales[["sales_id", "category"]],
        on="sales_id",
        how="left"
    )

    print("\nReturns by category:")
    print(enriched_returns["category"].value_counts())


def main():
    returns, sales = generate_returns()
    validate_returns(returns, sales)

    returns.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved fact_return.csv to: {OUTPUT_FILE}")
    print("Return generation complete.")


if __name__ == "__main__":
    main()