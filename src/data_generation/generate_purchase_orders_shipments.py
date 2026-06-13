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
SUPPLIER_FILE = RAW_DATA_DIR / "dim_supplier.csv"
CALENDAR_FILE = RAW_DATA_DIR / "dim_calendar.csv"

PO_OUTPUT_FILE = RAW_DATA_DIR / "fact_purchase_order.csv"
SHIPMENT_OUTPUT_FILE = RAW_DATA_DIR / "fact_shipment.csv"


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def choose_weighted(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def assign_supplier_to_product(products, suppliers):
    """
    Assign each product to a primary supplier.
    Higher-risk categories have a slightly higher chance of international suppliers.
    """

    supplier_records = suppliers.to_dict("records")
    assignments = []

    for product in products.to_dict("records"):
        category = product["category"]

        if category in ["Hardlines", "Beauty", "Apparel & Accessories", "Home Furnishings & Decor"]:
            preferred_regions = ["Domestic", "Asia-Pacific", "Mexico", "Canada", "Europe"]
            weights = [0.40, 0.38, 0.08, 0.05, 0.09]
        else:
            preferred_regions = ["Domestic", "Mexico", "Canada", "Asia-Pacific", "Europe"]
            weights = [0.72, 0.12, 0.07, 0.06, 0.03]

        selected_region = choose_weighted(preferred_regions, weights)

        eligible_suppliers = [
            supplier for supplier in supplier_records
            if supplier["supplier_region"] == selected_region
        ]

        if not eligible_suppliers:
            eligible_suppliers = supplier_records

        supplier = random.choice(eligible_suppliers)

        assignments.append({
            "product_id": product["product_id"],
            "supplier_id": supplier["supplier_id"]
        })

    return pd.DataFrame(assignments)


def calculate_order_frequency(category):
    """
    Determine how often a category tends to be reordered.
    Lower number = more frequent ordering.
    """

    if category == "Food & Beverage":
        return 1

    if category == "Household Essentials":
        return 2

    if category == "Beauty":
        return 3

    if category == "Apparel & Accessories":
        return 4

    if category == "Hardlines":
        return 4

    if category == "Home Furnishings & Decor":
        return 5

    return 4


def calculate_order_quantity(category, weekly_units_sold):
    """
    Generate purchase order quantity based on weekly demand and category behavior.
    """

    weekly_units_sold = max(float(weekly_units_sold), 1.0)

    if category == "Food & Beverage":
        coverage_weeks = random.uniform(1.2, 2.2)
    elif category == "Household Essentials":
        coverage_weeks = random.uniform(1.5, 3.0)
    elif category == "Beauty":
        coverage_weeks = random.uniform(2.0, 4.0)
    elif category == "Apparel & Accessories":
        coverage_weeks = random.uniform(2.5, 5.0)
    elif category == "Hardlines":
        coverage_weeks = random.uniform(2.5, 5.0)
    else:
        coverage_weeks = random.uniform(3.0, 6.0)

    order_units = int(np.ceil(weekly_units_sold * coverage_weeks))

    # Add order pack-size behavior.
    if category in ["Food & Beverage", "Household Essentials"]:
        pack_size = 12
    elif category in ["Beauty"]:
        pack_size = 6
    else:
        pack_size = 4

    order_units = int(np.ceil(order_units / pack_size) * pack_size)

    return max(order_units, pack_size)


def get_po_status(order_date, expected_delivery_date, max_calendar_date):
    """
    Assign purchase order status.
    """

    if expected_delivery_date > max_calendar_date:
        return "Open"

    return choose_weighted(
        ["Delivered", "Delivered", "Delivered", "Cancelled"],
        [0.70, 0.20, 0.07, 0.03]
    )


def calculate_delay_days(supplier_row, category, is_holiday_order):
    """
    Calculate shipment delay based on supplier reliability, supplier risk, category, and holiday season.
    """

    reliability = float(supplier_row["reliability_score"])
    delay_risk_level = supplier_row["delay_risk_level"]

    if delay_risk_level == "High":
        base_delay_probability = 0.28
    elif delay_risk_level == "Medium":
        base_delay_probability = 0.16
    else:
        base_delay_probability = 0.07

    if supplier_row["supplier_region"] == "Asia-Pacific":
        base_delay_probability += 0.07

    if category in ["Hardlines", "Apparel & Accessories", "Home Furnishings & Decor"]:
        base_delay_probability += 0.03

    if is_holiday_order:
        base_delay_probability += 0.06

    # Better reliability lowers delay probability.
    if reliability >= 92:
        base_delay_probability -= 0.04
    elif reliability < 78:
        base_delay_probability += 0.05

    base_delay_probability = min(max(base_delay_probability, 0.02), 0.45)

    if random.random() > base_delay_probability:
        return 0

    if delay_risk_level == "High":
        return random.randint(2, 14)

    if delay_risk_level == "Medium":
        return random.randint(1, 8)

    return random.randint(1, 4)


def generate_purchase_orders_and_shipments():
    print("Reading raw CSV files...")

    sales = pd.read_csv(SALES_FILE)
    products = pd.read_csv(PRODUCT_FILE)
    stores = pd.read_csv(STORE_FILE)
    suppliers = pd.read_csv(SUPPLIER_FILE)
    calendar = pd.read_csv(CALENDAR_FILE, parse_dates=["calendar_date"])

    print(f"Sales rows:    {len(sales):,}")
    print(f"Products:      {len(products):,}")
    print(f"Stores:        {len(stores):,}")
    print(f"Suppliers:     {len(suppliers):,}")
    print(f"Calendar rows: {len(calendar):,}")

    calendar_lookup = calendar[
        ["date_id", "calendar_date", "week_of_year", "year", "month", "is_holiday_season"]
    ]

    sales_enriched = sales.merge(
        calendar_lookup,
        on="date_id",
        how="left"
    )

    sales_enriched = sales_enriched.merge(
        products[["product_id", "category"]],
        on="product_id",
        how="left"
    )

    # Aggregate weekly demand at store-product level.
    weekly_demand = (
        sales_enriched
        .groupby(["store_id", "product_id", "year", "week_of_year"], as_index=False)
        .agg(
            week_start_date=("calendar_date", "min"),
            weekly_units_sold=("quantity_sold", "sum"),
            category=("category", "first"),
            unit_cost=("unit_cost", "first"),
            is_holiday_week=("is_holiday_season", "max")
        )
    )

    print(f"Weekly store-product demand rows: {len(weekly_demand):,}")

    # Assign suppliers to products.
    product_supplier = assign_supplier_to_product(products, suppliers)

    weekly_demand = weekly_demand.merge(
        product_supplier,
        on="product_id",
        how="left"
    )

    weekly_demand = weekly_demand.merge(
        suppliers,
        on="supplier_id",
        how="left"
    )

    max_calendar_date = calendar["calendar_date"].max()

    purchase_order_rows = []
    shipment_rows = []

    po_counter = 1
    po_line_counter = 1
    shipment_counter = 1

    print("\nGenerating purchase orders and shipments...")

    for row in weekly_demand.itertuples(index=False):
        row_dict = row._asdict()

        category = row_dict["category"]
        order_frequency = calculate_order_frequency(category)

        week_of_year = int(row_dict["week_of_year"])

        # Use modular logic so not every weekly demand row creates a PO.
        if week_of_year % order_frequency != 0:
            continue

        # Avoid tiny demand rows creating too many low-value POs.
        weekly_units_sold = float(row_dict["weekly_units_sold"])

        if weekly_units_sold < 2 and random.random() > 0.35:
            continue

        order_date = pd.Timestamp(row_dict["week_start_date"]) - pd.Timedelta(days=random.randint(1, 5))

        # Keep order dates within project date range.
        min_calendar_date = calendar["calendar_date"].min()
        if order_date < min_calendar_date:
            order_date = min_calendar_date

        avg_lead_time = int(row_dict["average_lead_time_days"])
        expected_delivery_date = order_date + pd.Timedelta(days=avg_lead_time)

        order_status = get_po_status(
            order_date=order_date,
            expected_delivery_date=expected_delivery_date,
            max_calendar_date=max_calendar_date
        )

        ordered_units = calculate_order_quantity(
            category=category,
            weekly_units_sold=weekly_units_sold
        )

        unit_cost = round(float(row_dict["unit_cost"]), 2)

        purchase_order_id = f"PO{po_counter:010d}"
        po_line_id = f"POL{po_line_counter:010d}"

        purchase_order_rows.append({
            "purchase_order_id": purchase_order_id,
            "po_line_id": po_line_id,
            "supplier_id": row_dict["supplier_id"],
            "product_id": row_dict["product_id"],
            "store_id": row_dict["store_id"],
            "order_date": order_date.date(),
            "expected_delivery_date": expected_delivery_date.date(),
            "ordered_units": ordered_units,
            "unit_cost": unit_cost,
            "order_status": order_status,
        })

        if order_status == "Delivered":
            delay_days = calculate_delay_days(
                supplier_row=row_dict,
                category=category,
                is_holiday_order=bool(row_dict["is_holiday_week"])
            )

            shipped_date = order_date + pd.Timedelta(days=random.randint(1, 3))
            delivered_date = expected_delivery_date + pd.Timedelta(days=delay_days)

            shipped_units = ordered_units

            # Most delivered shipments are complete; some short-ship.
            if random.random() < 0.08:
                delivered_units = max(int(ordered_units * random.uniform(0.70, 0.95)), 1)
            else:
                delivered_units = ordered_units

            shipment_rows.append({
                "shipment_id": f"SHP{shipment_counter:010d}",
                "purchase_order_id": purchase_order_id,
                "supplier_id": row_dict["supplier_id"],
                "product_id": row_dict["product_id"],
                "store_id": row_dict["store_id"],
                "shipped_date": shipped_date.date(),
                "expected_delivery_date": expected_delivery_date.date(),
                "delivered_date": delivered_date.date(),
                "shipped_units": shipped_units,
                "delivered_units": delivered_units,
                "delayed_flag": delay_days > 0,
                "delay_days": delay_days,
            })

            shipment_counter += 1

        po_counter += 1
        po_line_counter += 1

    purchase_orders = pd.DataFrame(purchase_order_rows)
    shipments = pd.DataFrame(shipment_rows)

    print(f"\nGenerated purchase order rows: {len(purchase_orders):,}")
    print(f"Generated shipment rows:       {len(shipments):,}")

    return purchase_orders, shipments


def validate_outputs(purchase_orders, shipments):
    print("\nPurchase order validation summary:")
    print(f"PO rows: {len(purchase_orders):,}")
    print(f"Distinct purchase_order_id: {purchase_orders['purchase_order_id'].nunique():,}")
    print(f"Distinct po_line_id: {purchase_orders['po_line_id'].nunique():,}")
    print(f"Total ordered units: {purchase_orders['ordered_units'].sum():,}")
    print(f"Total ordered cost: ${(purchase_orders['ordered_units'] * purchase_orders['unit_cost']).sum():,.2f}")

    print("\nPO status mix:")
    print(purchase_orders["order_status"].value_counts())

    print("\nShipment validation summary:")
    print(f"Shipment rows: {len(shipments):,}")

    if len(shipments) > 0:
        print(f"Distinct shipment_id: {shipments['shipment_id'].nunique():,}")
        print(f"Total shipped units: {shipments['shipped_units'].sum():,}")
        print(f"Total delivered units: {shipments['delivered_units'].sum():,}")
        print(f"Delayed shipments: {shipments['delayed_flag'].sum():,}")
        print(f"Delay rate: {shipments['delayed_flag'].mean():.4f}")
        print(f"Average delay days: {shipments['delay_days'].mean():.2f}")

        print("\nDelay days distribution:")
        print(shipments["delay_days"].describe())


def main():
    purchase_orders, shipments = generate_purchase_orders_and_shipments()
    validate_outputs(purchase_orders, shipments)

    purchase_orders.to_csv(PO_OUTPUT_FILE, index=False)
    shipments.to_csv(SHIPMENT_OUTPUT_FILE, index=False)

    print(f"\nSaved fact_purchase_order.csv to: {PO_OUTPUT_FILE}")
    print(f"Saved fact_shipment.csv to: {SHIPMENT_OUTPUT_FILE}")
    print("Purchase order and shipment generation complete.")


if __name__ == "__main__":
    main()