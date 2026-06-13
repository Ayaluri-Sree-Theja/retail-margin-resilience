# Data Model Plan

## Modeling Approach

The project will use a dimensional model with fact and dimension tables.

The raw data will be generated using Python, loaded into PostgreSQL, transformed using dbt, and exposed to Power BI through analytics marts.

## Core Dimension Tables

### dim_store

Grain: one row per store.

Columns:

- store_id
- store_name
- region
- state
- city
- store_format
- store_size_sqft
- opened_date
- risk_profile
- fulfillment_enabled

### dim_product

Grain: one row per SKU.

Columns:

- product_id
- sku
- product_name
- category
- subcategory
- brand_type
- unit_price
- unit_cost
- margin_rate
- return_risk_level
- shrink_risk_level

### dim_supplier

Grain: one row per supplier.

Columns:

- supplier_id
- supplier_name
- supplier_region
- average_lead_time_days
- reliability_score
- delay_risk_level

### dim_calendar

Grain: one row per date.

Columns:

- date_id
- calendar_date
- year
- quarter
- month
- week
- day_of_week
- is_weekend
- is_holiday_season

### dim_promotion

Grain: one row per promotion.

Columns:

- promotion_id
- promotion_name
- promotion_type
- discount_pct
- start_date
- end_date
- category
- channel

## Core Fact Tables

### fact_sales

Grain: one row per transaction line.

Columns:

- sales_id
- transaction_id
- date_id
- store_id
- product_id
- promotion_id
- channel
- quantity_sold
- unit_price
- discount_pct
- final_sale_price
- gross_revenue
- net_sales_revenue
- unit_cost
- gross_margin

### fact_inventory_snapshot

Grain: one row per store-product-date.

Columns:

- inventory_snapshot_id
- date_id
- store_id
- product_id
- beginning_inventory_units
- ending_inventory_units
- received_units
- sold_units
- returned_units
- shrink_units
- stockout_flag
- overstock_flag
- inventory_value

### fact_purchase_order

Grain: one row per purchase order line.

Columns:

- purchase_order_id
- po_line_id
- supplier_id
- product_id
- store_id
- order_date
- expected_delivery_date
- ordered_units
- unit_cost
- order_status

### fact_shipment

Grain: one row per shipment line.

Columns:

- shipment_id
- purchase_order_id
- supplier_id
- product_id
- store_id
- shipped_date
- expected_delivery_date
- delivered_date
- shipped_units
- delivered_units
- delayed_flag
- delay_days

### fact_return

Grain: one row per return line.

Columns:

- return_id
- sales_id
- date_id
- store_id
- product_id
- channel
- return_reason
- returned_units
- refund_amount
- return_condition

### fact_shrink_event

Grain: one row per store-product-date-shrink event.

Columns:

- shrink_event_id
- date_id
- store_id
- product_id
- shrink_reason
- shrink_units
- estimated_shrink_value
- investigation_flag

## ML Output Tables

### ml_demand_forecast

Grain: one row per store-product-week.

Columns:

- forecast_id
- store_id
- product_id
- week_start_date
- actual_units
- forecasted_units
- forecast_error
- demand_volatility_score
- model_version

### ml_risk_scores

Grain: one row per store-product-week-risk type.

Columns:

- risk_score_id
- store_id
- product_id
- week_start_date
- stockout_risk_score
- overstock_risk_score
- return_risk_score
- shrink_risk_score
- margin_risk_score
- recommended_action
- model_version