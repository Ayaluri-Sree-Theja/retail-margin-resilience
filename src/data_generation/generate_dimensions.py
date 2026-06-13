from pathlib import Path
from datetime import datetime, timedelta
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
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def choose_weighted(options, weights):
    """
    Pick one value from a list using probability weights.
    """
    return random.choices(options, weights=weights, k=1)[0]


def risk_label_from_score(score):
    """
    Convert numeric risk score into readable risk label.
    """
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def create_date_id(date_value):
    """
    Convert a date into integer YYYYMMDD format.
    Example: 2025-02-01 -> 20250201
    """
    return int(date_value.strftime("%Y%m%d"))


# ---------------------------------------------------------------------
# 1. dim_calendar
# ---------------------------------------------------------------------

def generate_calendar():
    """
    Generate calendar from FY2023 start to FY2025 end.

    Target's annual reports note that FY2023 had 53 weeks while
    FY2024 and FY2025 had 52 weeks. We model the complete fiscal range:

    FY2023: 2023-01-29 to 2024-02-03
    FY2024: 2024-02-04 to 2025-02-01
    FY2025: 2025-02-02 to 2026-01-31

    The raw calendar table does not yet store fiscal-year columns.
    Fiscal attributes can be added later in dbt staging/intermediate models.
    """

    start_date = pd.Timestamp("2023-01-29")
    end_date = pd.Timestamp("2026-01-31")

    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    calendar = pd.DataFrame({
        "calendar_date": dates
    })

    calendar["date_id"] = calendar["calendar_date"].apply(create_date_id)
    calendar["year"] = calendar["calendar_date"].dt.year
    calendar["quarter"] = calendar["calendar_date"].dt.quarter
    calendar["month"] = calendar["calendar_date"].dt.month
    calendar["month_name"] = calendar["calendar_date"].dt.month_name()
    calendar["week_of_year"] = calendar["calendar_date"].dt.isocalendar().week.astype(int)
    calendar["day_of_week"] = calendar["calendar_date"].dt.dayofweek + 1
    calendar["day_name"] = calendar["calendar_date"].dt.day_name()
    calendar["is_weekend"] = calendar["day_of_week"].isin([6, 7])

    # Holiday season for retail: November and December
    calendar["is_holiday_season"] = calendar["month"].isin([11, 12])

    calendar = calendar[
        [
            "date_id",
            "calendar_date",
            "year",
            "quarter",
            "month",
            "month_name",
            "week_of_year",
            "day_of_week",
            "day_name",
            "is_weekend",
            "is_holiday_season",
        ]
    ]

    return calendar


# ---------------------------------------------------------------------
# 2. dim_store
# ---------------------------------------------------------------------

def generate_stores(n_stores=60):
    """
    Generate store dimension.

    Store format and size are important because Target reports different
    store-size bands in its annual reports. We simulate a smaller portfolio
    of stores while preserving realistic variation in format, region,
    size, fulfillment capability, and operational risk.
    """

    regions = {
        "Northeast": [
            ("MA", "Boston"),
            ("NY", "Albany"),
            ("NJ", "Jersey City"),
            ("PA", "Philadelphia"),
            ("CT", "Hartford"),
        ],
        "South": [
            ("TX", "Austin"),
            ("FL", "Orlando"),
            ("GA", "Atlanta"),
            ("NC", "Charlotte"),
            ("TN", "Nashville"),
        ],
        "Midwest": [
            ("MN", "Minneapolis"),
            ("IL", "Chicago"),
            ("OH", "Columbus"),
            ("MI", "Detroit"),
            ("WI", "Madison"),
        ],
        "West": [
            ("CA", "Los Angeles"),
            ("WA", "Seattle"),
            ("AZ", "Phoenix"),
            ("CO", "Denver"),
            ("NV", "Las Vegas"),
        ],
    }

    store_formats = ["Large Format", "Standard", "Small Format"]
    store_format_weights = [0.20, 0.65, 0.15]

    rows = []

    for i in range(1, n_stores + 1):
        store_id = f"ST{i:04d}"

        region = choose_weighted(
            ["Northeast", "South", "Midwest", "West"],
            [0.20, 0.35, 0.25, 0.20]
        )

        state, city = random.choice(regions[region])

        store_format = choose_weighted(store_formats, store_format_weights)

        if store_format == "Large Format":
            size = random.randint(170000, 210000)
            fulfillment_probability = 0.95
        elif store_format == "Standard":
            size = random.randint(90000, 169999)
            fulfillment_probability = 0.80
        else:
            size = random.randint(25000, 49999)
            fulfillment_probability = 0.45

        opened_year = random.randint(1995, 2024)
        opened_month = random.randint(1, 12)
        opened_day = random.randint(1, 28)
        opened_date = datetime(opened_year, opened_month, opened_day).date()

        risk_score = np.clip(np.random.beta(2, 5), 0, 1)
        risk_profile = risk_label_from_score(risk_score)

        fulfillment_enabled = random.random() < fulfillment_probability

        rows.append({
            "store_id": store_id,
            "store_name": f"Target Store {i:04d}",
            "region": region,
            "state": state,
            "city": city,
            "store_format": store_format,
            "store_size_sqft": size,
            "opened_date": opened_date,
            "risk_profile": risk_profile,
            "fulfillment_enabled": fulfillment_enabled,
        })

    stores = pd.DataFrame(rows)
    return stores


# ---------------------------------------------------------------------
# 3. dim_product
# ---------------------------------------------------------------------

def generate_products(n_products=360):
    """
    Generate product/SKU dimension.

    We use Target-like retail categories but this is not Target internal
    product data. The six categories create different pricing, margin,
    return, and shrink behavior for later fact generation.
    """

    category_config = {
        "Apparel & Accessories": {
            "weight": 0.15,
            "subcategories": ["Women", "Men", "Kids", "Shoes", "Accessories"],
            "price_range": (12, 85),
            "margin_range": (0.34, 0.48),
            "return_risk": "High",
            "shrink_risk": "Medium",
        },
        "Beauty": {
            "weight": 0.13,
            "subcategories": ["Skincare", "Haircare", "Cosmetics", "Fragrance"],
            "price_range": (5, 60),
            "margin_range": (0.32, 0.50),
            "return_risk": "Medium",
            "shrink_risk": "High",
        },
        "Household Essentials": {
            "weight": 0.24,
            "subcategories": ["Cleaning", "Paper Goods", "Personal Care", "Baby"],
            "price_range": (4, 45),
            "margin_range": (0.18, 0.34),
            "return_risk": "Low",
            "shrink_risk": "Medium",
        },
        "Food & Beverage": {
            "weight": 0.15,
            "subcategories": ["Pantry", "Frozen", "Snacks", "Beverages", "Fresh"],
            "price_range": (2, 35),
            "margin_range": (0.12, 0.28),
            "return_risk": "Low",
            "shrink_risk": "Low",
        },
        "Home Furnishings & Decor": {
            "weight": 0.15,
            "subcategories": ["Furniture", "Bedding", "Kitchen", "Storage", "Decor"],
            "price_range": (10, 180),
            "margin_range": (0.28, 0.45),
            "return_risk": "Medium",
            "shrink_risk": "Low",
        },
        "Hardlines": {
            "weight": 0.18,
            "subcategories": ["Electronics", "Toys", "Sporting Goods", "Seasonal", "Entertainment"],
            "price_range": (8, 300),
            "margin_range": (0.16, 0.38),
            "return_risk": "Medium",
            "shrink_risk": "High",
        },
    }

    categories = list(category_config.keys())
    category_weights = [category_config[c]["weight"] for c in categories]

    brand_types = ["Owned Brand", "National Brand", "Exclusive Partnership", "Marketplace"]
    brand_weights = [0.35, 0.45, 0.15, 0.05]

    rows = []

    for i in range(1, n_products + 1):
        product_id = f"PRD{i:05d}"
        sku = f"SKU-{100000 + i}"

        category = choose_weighted(categories, category_weights)
        config = category_config[category]

        subcategory = random.choice(config["subcategories"])
        brand_type = choose_weighted(brand_types, brand_weights)

        min_price, max_price = config["price_range"]
        unit_price = round(random.uniform(min_price, max_price), 2)

        min_margin, max_margin = config["margin_range"]
        margin_rate = round(random.uniform(min_margin, max_margin), 4)

        unit_cost = round(unit_price * (1 - margin_rate), 2)

        product_name = f"{brand_type} {subcategory} Item {i:05d}"

        rows.append({
            "product_id": product_id,
            "sku": sku,
            "product_name": product_name,
            "category": category,
            "subcategory": subcategory,
            "brand_type": brand_type,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "margin_rate": margin_rate,
            "return_risk_level": config["return_risk"],
            "shrink_risk_level": config["shrink_risk"],
        })

    products = pd.DataFrame(rows)
    return products


# ---------------------------------------------------------------------
# 4. dim_supplier
# ---------------------------------------------------------------------

def generate_suppliers(n_suppliers=60):
    """
    Generate supplier dimension.

    Supplier reliability and lead time variation will later drive
    stockout risk, delayed shipments, and fulfillment reliability KPIs.
    """

    supplier_regions = ["Domestic", "Mexico", "Canada", "Asia-Pacific", "Europe"]
    supplier_region_weights = [0.55, 0.10, 0.05, 0.25, 0.05]

    rows = []

    for i in range(1, n_suppliers + 1):
        supplier_id = f"SUP{i:04d}"
        supplier_region = choose_weighted(supplier_regions, supplier_region_weights)

        if supplier_region == "Domestic":
            avg_lead_time = random.randint(3, 10)
            reliability_score = round(random.uniform(82, 98), 2)
        elif supplier_region in ["Mexico", "Canada"]:
            avg_lead_time = random.randint(7, 18)
            reliability_score = round(random.uniform(78, 95), 2)
        elif supplier_region == "Asia-Pacific":
            avg_lead_time = random.randint(21, 55)
            reliability_score = round(random.uniform(68, 92), 2)
        else:
            avg_lead_time = random.randint(14, 35)
            reliability_score = round(random.uniform(72, 94), 2)

        if reliability_score >= 90:
            delay_risk_level = "Low"
        elif reliability_score >= 80:
            delay_risk_level = "Medium"
        else:
            delay_risk_level = "High"

        rows.append({
            "supplier_id": supplier_id,
            "supplier_name": f"Supplier {i:04d}",
            "supplier_region": supplier_region,
            "average_lead_time_days": avg_lead_time,
            "reliability_score": reliability_score,
            "delay_risk_level": delay_risk_level,
        })

    suppliers = pd.DataFrame(rows)
    return suppliers


# ---------------------------------------------------------------------
# 5. dim_promotion
# ---------------------------------------------------------------------

def generate_promotions(n_promotions=75):
    """
    Generate promotions.

    Promotions and markdown-like discounting are important because they
    affect sales volume, realized revenue, gross margin, and later
    markdown exposure analysis.
    """

    categories = [
        "Apparel & Accessories",
        "Beauty",
        "Household Essentials",
        "Food & Beverage",
        "Home Furnishings & Decor",
        "Hardlines",
        "All Categories",
    ]

    promotion_types = [
        "Weekly Ad",
        "Holiday Sale",
        "Clearance",
        "Circle Offer",
        "Back-to-School",
        "Seasonal Event",
        "Digital Deal",
    ]

    channels = ["Store", "Online", "Drive Up", "Same-Day Delivery", "All Channels"]

    start_date = pd.Timestamp("2023-01-29")
    end_date = pd.Timestamp("2026-01-31")

    rows = []

    for i in range(1, n_promotions + 1):
        promotion_id = f"PROMO{i:04d}"
        promotion_type = random.choice(promotion_types)

        # Promotion timing logic
        if promotion_type == "Holiday Sale":
            promo_start_year = random.choice([2023, 2024, 2025])
            promo_start = pd.Timestamp(
                year=promo_start_year,
                month=random.choice([11, 12]),
                day=random.randint(1, 20)
            )
            duration_days = random.randint(7, 21)
        elif promotion_type == "Back-to-School":
            promo_start_year = random.choice([2023, 2024, 2025])
            promo_start = pd.Timestamp(
                year=promo_start_year,
                month=random.choice([7, 8]),
                day=random.randint(1, 20)
            )
            duration_days = random.randint(10, 28)
        elif promotion_type == "Clearance":
            promo_start = start_date + pd.Timedelta(days=random.randint(0, (end_date - start_date).days))
            duration_days = random.randint(14, 45)
        else:
            promo_start = start_date + pd.Timedelta(days=random.randint(0, (end_date - start_date).days))
            duration_days = random.randint(5, 21)

        promo_end = min(promo_start + pd.Timedelta(days=duration_days), end_date)

        if promotion_type == "Clearance":
            discount_pct = round(random.uniform(0.20, 0.50), 4)
        elif promotion_type == "Holiday Sale":
            discount_pct = round(random.uniform(0.10, 0.35), 4)
        elif promotion_type == "Circle Offer":
            discount_pct = round(random.uniform(0.05, 0.20), 4)
        else:
            discount_pct = round(random.uniform(0.05, 0.30), 4)

        category = random.choice(categories)
        channel = random.choice(channels)

        rows.append({
            "promotion_id": promotion_id,
            "promotion_name": f"{promotion_type} {i:04d}",
            "promotion_type": promotion_type,
            "discount_pct": discount_pct,
            "start_date": promo_start.date(),
            "end_date": promo_end.date(),
            "category": category,
            "channel": channel,
        })

    promotions = pd.DataFrame(rows)
    return promotions


# ---------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------

def save_dataframe(df, file_name):
    output_path = RAW_DATA_DIR / file_name
    df.to_csv(output_path, index=False)
    print(f"Saved {file_name}: {len(df):,} rows")


def main():
    print("Generating dimension tables...")
    print(f"Output directory: {RAW_DATA_DIR}")

    calendar = generate_calendar()
    stores = generate_stores(n_stores=60)
    products = generate_products(n_products=360)
    suppliers = generate_suppliers(n_suppliers=60)
    promotions = generate_promotions(n_promotions=75)

    save_dataframe(calendar, "dim_calendar.csv")
    save_dataframe(stores, "dim_store.csv")
    save_dataframe(products, "dim_product.csv")
    save_dataframe(suppliers, "dim_supplier.csv")
    save_dataframe(promotions, "dim_promotion.csv")

    print("\nDimension generation complete.")
    print("\nRow count summary:")
    print(f"dim_calendar:  {len(calendar):,}")
    print(f"dim_store:     {len(stores):,}")
    print(f"dim_product:   {len(products):,}")
    print(f"dim_supplier:  {len(suppliers):,}")
    print(f"dim_promotion: {len(promotions):,}")


if __name__ == "__main__":
    main()