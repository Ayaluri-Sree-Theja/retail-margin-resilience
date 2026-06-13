CREATE TABLE IF NOT EXISTS raw.dim_store (
    store_id VARCHAR(20) PRIMARY KEY,
    store_name VARCHAR(100),
    region VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(100),
    store_format VARCHAR(50),
    store_size_sqft INTEGER,
    opened_date DATE,
    risk_profile VARCHAR(30),
    fulfillment_enabled BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.dim_product (
    product_id VARCHAR(20) PRIMARY KEY,
    sku VARCHAR(50),
    product_name VARCHAR(150),
    category VARCHAR(75),
    subcategory VARCHAR(75),
    brand_type VARCHAR(50),
    unit_price NUMERIC(10,2),
    unit_cost NUMERIC(10,2),
    margin_rate NUMERIC(6,4),
    return_risk_level VARCHAR(30),
    shrink_risk_level VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.dim_supplier (
    supplier_id VARCHAR(20) PRIMARY KEY,
    supplier_name VARCHAR(150),
    supplier_region VARCHAR(75),
    average_lead_time_days INTEGER,
    reliability_score NUMERIC(5,2),
    delay_risk_level VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.dim_calendar (
    date_id INTEGER PRIMARY KEY,
    calendar_date DATE UNIQUE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    week_of_year INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday_season BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.dim_promotion (
    promotion_id VARCHAR(20) PRIMARY KEY,
    promotion_name VARCHAR(150),
    promotion_type VARCHAR(50),
    discount_pct NUMERIC(6,4),
    start_date DATE,
    end_date DATE,
    category VARCHAR(75),
    channel VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_sales (
    sales_id VARCHAR(30) PRIMARY KEY,
    transaction_id VARCHAR(30),
    date_id INTEGER,
    store_id VARCHAR(20),
    product_id VARCHAR(20),
    promotion_id VARCHAR(20),
    channel VARCHAR(50),
    quantity_sold INTEGER,
    unit_price NUMERIC(10,2),
    discount_pct NUMERIC(6,4),
    final_sale_price NUMERIC(10,2),
    gross_revenue NUMERIC(12,2),
    net_sales_revenue NUMERIC(12,2),
    unit_cost NUMERIC(10,2),
    gross_margin NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_inventory_snapshot (
    inventory_snapshot_id VARCHAR(30) PRIMARY KEY,
    date_id INTEGER,
    store_id VARCHAR(20),
    product_id VARCHAR(20),
    beginning_inventory_units INTEGER,
    ending_inventory_units INTEGER,
    received_units INTEGER,
    sold_units INTEGER,
    returned_units INTEGER,
    shrink_units INTEGER,
    stockout_flag BOOLEAN,
    overstock_flag BOOLEAN,
    inventory_value NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_purchase_order (
    purchase_order_id VARCHAR(30),
    po_line_id VARCHAR(30) PRIMARY KEY,
    supplier_id VARCHAR(20),
    product_id VARCHAR(20),
    store_id VARCHAR(20),
    order_date DATE,
    expected_delivery_date DATE,
    ordered_units INTEGER,
    unit_cost NUMERIC(10,2),
    order_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_shipment (
    shipment_id VARCHAR(30) PRIMARY KEY,
    purchase_order_id VARCHAR(30),
    supplier_id VARCHAR(20),
    product_id VARCHAR(20),
    store_id VARCHAR(20),
    shipped_date DATE,
    expected_delivery_date DATE,
    delivered_date DATE,
    shipped_units INTEGER,
    delivered_units INTEGER,
    delayed_flag BOOLEAN,
    delay_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_return (
    return_id VARCHAR(30) PRIMARY KEY,
    sales_id VARCHAR(30),
    date_id INTEGER,
    store_id VARCHAR(20),
    product_id VARCHAR(20),
    channel VARCHAR(50),
    return_reason VARCHAR(100),
    returned_units INTEGER,
    refund_amount NUMERIC(12,2),
    return_condition VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.fact_shrink_event (
    shrink_event_id VARCHAR(30) PRIMARY KEY,
    date_id INTEGER,
    store_id VARCHAR(20),
    product_id VARCHAR(20),
    shrink_reason VARCHAR(100),
    shrink_units INTEGER,
    estimated_shrink_value NUMERIC(12,2),
    investigation_flag BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);