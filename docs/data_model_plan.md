# Data Model Plan

This document describes the data model design for the Retail Margin Resilience Analytics project.

The project uses a synthetic retail operating model inspired by public-company retail context. Target Corporation is used as the public-company reference for business framing, but the operational dataset is fully simulated and does **not** represent Target's internal data.

---

## Modeling objective

The data model is designed to support one final business question:

> How can a large retailer protect profit while balancing demand volatility, stockouts, overstock, returns, shrink, markdown exposure, supplier delays, and fulfillment delays?

The model is built to connect operational activity with margin-risk outcomes across stores, products, categories, suppliers, inventory, fulfillment, and profitability.

---

## Modeling approach

The project uses a layered analytics architecture:

```text
Synthetic data generation
        ↓
PostgreSQL raw warehouse
        ↓
dbt staging models
        ↓
dbt intermediate models
        ↓
dbt mart models
        ↓
Power BI dashboard
        ↓
ML feature engineering
        ↓
Streamlit what-if simulator
```

The model is intentionally designed to show a realistic analytics workflow rather than a single flat dataset.

---

## Core business grains

The project uses multiple grains because retail margin-risk cannot be analyzed correctly from one table alone.

| Grain               | Purpose                                            |
| ------------------- | -------------------------------------------------- |
| Calendar date       | Fiscal mapping and trend analysis                  |
| Store               | Store-level segmentation and risk profile          |
| Product             | Category, cost, price, return, and shrink behavior |
| Supplier            | Replenishment and reliability analysis             |
| Promotion           | Discount and markdown behavior                     |
| Sales transaction   | Revenue and margin activity                        |
| Return event        | Refund and return leakage                          |
| Shrink event        | Inventory loss and operational leakage             |
| Purchase order line | Replenishment demand                               |
| Shipment            | Supplier and fulfillment reliability               |
| Store-product-week  | Inventory position and availability                |
| Store-category-year | Profitability, ML features, and simulator grain    |

---

# Conceptual Data Model

The conceptual model centers on the idea that margin-risk emerges from connected retail operations.

```text
Stores
  ├── Sales
  ├── Returns
  ├── Shrink events
  ├── Inventory snapshots
  ├── Purchase orders
  └── Shipments

Products
  ├── Sales
  ├── Returns
  ├── Shrink events
  ├── Inventory snapshots
  ├── Purchase orders
  └── Shipments

Suppliers
  ├── Purchase orders
  └── Shipments

Promotions
  └── Sales

Calendar
  ├── Sales
  ├── Returns
  ├── Shrink events
  ├── Inventory snapshots
  ├── Purchase orders
  └── Shipments
```

The core analytical idea is:

```text
sales + returns + shrink + inventory + supplier + fulfillment
        ↓
store-category profitability
        ↓
margin-risk rate
        ↓
next-year high margin-risk prediction
        ↓
what-if scenario simulation
```

---

# Logical Data Model

## Dimension tables

The model uses five core dimensions.

### dim_calendar

Calendar and fiscal mapping table.

**Primary key**

```text
date_key
```

**Purpose**

Supports fiscal-year reporting, weekly inventory snapshots, trend analysis, and joins across fact tables.

---

### dim_store

Synthetic store master table.

**Primary key**

```text
store_id
```

**Purpose**

Supports store-level analysis, regional grouping, and synthetic risk profile assignment.

---

### dim_product

Synthetic product master table.

**Primary key**

```text
product_id
```

**Purpose**

Supports product, subcategory, and category analysis. Also stores unit cost, unit price, return-risk assumptions, and shrink-risk assumptions.

---

### dim_supplier

Synthetic supplier master table.

**Primary key**

```text
supplier_id
```

**Purpose**

Supports purchase order, shipment, supplier reliability, lead time, and fulfillment analysis.

---

### dim_promotion

Synthetic promotion table.

**Primary key**

```text
promotion_id
```

**Purpose**

Supports discount, promotion, markdown exposure, and margin pressure analysis.

---

## Fact tables

The model uses six main fact tables.

### fact_sales

Synthetic sales transaction table.

**Grain**

One row per sales transaction.

**Foreign keys**

```text
date_key
store_id
product_id
promotion_id
```

**Purpose**

Supports sales, discount, revenue, cost, and gross margin metrics.

---

### fact_return

Synthetic return event table.

**Grain**

One row per return event.

**Foreign keys**

```text
date_key
store_id
product_id
sales_id
```

**Purpose**

Supports return-rate, refund leakage, product return pattern, and margin-risk analysis.

---

### fact_shrink_event

Synthetic shrink event table.

**Grain**

One row per shrink event.

**Foreign keys**

```text
date_key
store_id
product_id
```

**Purpose**

Supports shrink value, shrink reason, operational loss, and risk exposure analysis.

---

### fact_purchase_order

Synthetic purchase order line table.

**Grain**

One row per purchase order line.

**Foreign keys**

```text
order_date_key
store_id
product_id
supplier_id
```

**Purpose**

Supports replenishment demand, order volume, ordered units, and supplier performance.

---

### fact_shipment

Synthetic shipment table.

**Grain**

One row per shipment.

**Foreign keys**

```text
purchase_order_id
supplier_id
store_id
product_id
```

**Purpose**

Supports delivery performance, delay analysis, short shipment analysis, and lead time metrics.

---

### fact_inventory_snapshot

Synthetic weekly inventory snapshot table.

**Grain**

One row per store-product-week.

**Foreign keys**

```text
store_id
product_id
week_start_date
```

**Purpose**

Supports stockout, overstock, ending inventory, inventory value, sell-through, and weeks-of-supply metrics.

---

# Relationship Design

## Sales relationships

```text
fact_sales.date_key → dim_calendar.date_key
fact_sales.store_id → dim_store.store_id
fact_sales.product_id → dim_product.product_id
fact_sales.promotion_id → dim_promotion.promotion_id
```

Sales connects demand, promotion, store, product, revenue, and margin.

---

## Return relationships

```text
fact_return.date_key → dim_calendar.date_key
fact_return.store_id → dim_store.store_id
fact_return.product_id → dim_product.product_id
fact_return.sales_id → fact_sales.sales_id
```

Returns connect refund leakage back to product, store, time, and optionally original sales activity.

---

## Shrink relationships

```text
fact_shrink_event.date_key → dim_calendar.date_key
fact_shrink_event.store_id → dim_store.store_id
fact_shrink_event.product_id → dim_product.product_id
```

Shrink connects operational loss to store, product, category, and time.

---

## Purchase order relationships

```text
fact_purchase_order.order_date_key → dim_calendar.date_key
fact_purchase_order.store_id → dim_store.store_id
fact_purchase_order.product_id → dim_product.product_id
fact_purchase_order.supplier_id → dim_supplier.supplier_id
```

Purchase orders connect replenishment planning to suppliers, stores, products, and time.

---

## Shipment relationships

```text
fact_shipment.purchase_order_id → fact_purchase_order.purchase_order_id
fact_shipment.supplier_id → dim_supplier.supplier_id
fact_shipment.store_id → dim_store.store_id
fact_shipment.product_id → dim_product.product_id
```

Shipments connect supply execution to supplier reliability and inventory availability.

---

## Inventory relationships

```text
fact_inventory_snapshot.store_id → dim_store.store_id
fact_inventory_snapshot.product_id → dim_product.product_id
fact_inventory_snapshot.week_start_date → dim_calendar.calendar_date
```

Inventory snapshots connect weekly availability, stockout, overstock, and sell-through behavior to store and product context.

---

# Physical Warehouse Plan

The PostgreSQL warehouse contains raw tables created through SQL scripts.

## SQL initialization files

```text
sql/init/00_create_schemas.sql
sql/init/01_create_raw_tables.sql
sql/init/02_create_raw_indexes.sql
```

## Validation files

```text
sql/validation/validate_marts.sql
```

## Raw warehouse purpose

The raw warehouse stores generated source data before dbt transformations.

Primary responsibilities:

* preserve generated source records,
* support repeatable loading,
* provide a clean base for dbt staging models,
* allow validation of generated row counts and relationships.

---

# dbt Modeling Plan

The dbt project is located in:

```text
dbt_retail/
```

The dbt layer has three main levels:

1. staging,
2. intermediate,
3. marts.

---

## Staging layer

Staging models standardize raw source tables.

Directory:

```text
dbt_retail/models/staging/
```

Staging models:

```text
stg_calendar.sql
stg_stores.sql
stg_products.sql
stg_suppliers.sql
stg_promotions.sql
stg_sales.sql
stg_returns.sql
stg_shrink_events.sql
stg_purchase_orders.sql
stg_shipments.sql
stg_inventory_snapshots.sql
```

### Staging layer responsibilities

* Rename fields consistently.
* Cast data types.
* Standardize date fields.
* Preserve primary and foreign keys.
* Prepare clean sources for enrichment.
* Apply basic metric calculations where appropriate.

---

## Intermediate layer

Intermediate models enrich source-level records with dimensional context and reusable business logic.

Directory:

```text
dbt_retail/models/intermediate/
```

Intermediate models:

```text
int_sales_enriched.sql
int_returns_enriched.sql
int_shrink_enriched.sql
int_inventory_enriched.sql
int_fulfillment_enriched.sql
```

### Intermediate layer responsibilities

* Join facts to dimensions.
* Add fiscal context.
* Add store and category context.
* Calculate reusable business fields.
* Prepare data for mart aggregation.
* Reduce repeated logic across marts.

---

## Mart layer

Mart models are analytics-ready tables used by Power BI and ML feature engineering.

Directory:

```text
dbt_retail/models/marts/
```

Final mart models:

```text
mart_executive_margin_resilience.sql
mart_inventory_health.sql
mart_return_shrink_leakage.sql
mart_fulfillment_reliability.sql
mart_store_category_profitability.sql
mart_supplier_performance.sql
```

---

# Final Mart Design

## mart_executive_margin_resilience

**Purpose**

Executive-level view of revenue, margin, leakage, and risk.

**Primary business questions**

* How much revenue and gross margin is being generated?
* How much value is exposed through markdowns, returns, and shrink?
* Is margin-risk improving or worsening over time?
* Which periods show the highest resilience pressure?

**Metric groups**

* Net sales revenue
* Gross margin amount
* Gross margin rate
* Markdown loss
* Refund amount
* Shrink value
* Margin-at-risk
* Margin risk rate

---

## mart_inventory_health

**Purpose**

Inventory productivity and availability risk.

**Primary business questions**

* Where are stockouts occurring?
* Where is excess inventory building?
* Which store-category combinations have weak sell-through?
* Which areas have high weeks of supply?

**Metric groups**

* Ending inventory units
* Ending inventory value
* Average inventory value
* Stockout rate
* Overstock rate
* Weeks of supply
* Sell-through rate

---

## mart_return_shrink_leakage

**Purpose**

Combined return and shrink leakage analysis.

**Primary business questions**

* Which categories have the highest refund exposure?
* Which stores or categories show high shrink pressure?
* Where is leakage most material relative to sales?
* Which return reasons or shrink reasons require review?

**Metric groups**

* Returned units
* Refund amount
* Refund value rate
* Shrink units
* Shrink value
* Shrink value rate
* Return and shrink leakage
* Leakage rate

---

## mart_fulfillment_reliability

**Purpose**

Supplier and fulfillment reliability tracking.

**Primary business questions**

* Which supplier or category combinations are delayed?
* Where are short shipments occurring?
* Which fulfillment flows have long lead times?
* How do delays connect to store-category margin pressure?

**Metric groups**

* Shipment count
* Delayed shipments
* Delay rate
* Average delay days
* Supplier lead time
* Fulfillment lead time
* Short shipment rate

---

## mart_store_category_profitability

**Purpose**

Store-category profitability and risk base table.

**Primary business questions**

* Which store-category combinations generate revenue?
* Which combinations have weak gross margin?
* Which combinations carry high margin-at-risk?
* Which combinations are candidates for predictive risk modeling?

**Metric groups**

* Net sales revenue
* Gross margin amount
* Gross margin rate
* Markdown loss
* Refund amount
* Shrink value
* Margin-at-risk
* Margin risk rate
* High margin-risk flag

**Downstream use**

* Power BI Store & Category Profitability page
* Power BI Predictive Risk Intelligence page
* ML feature engineering
* Streamlit simulator

---

## mart_supplier_performance

**Purpose**

Supplier performance and replenishment reliability.

**Primary business questions**

* Which suppliers have low fill rates?
* Which suppliers are frequently delayed?
* Which suppliers create risk for specific categories?
* How do lead times vary by supplier and category?

**Metric groups**

* Ordered units
* Shipped units
* Delivered units
* Supplier fill rate
* Supplier delay rate
* Average lead time days
* Short shipment rate

---

# ML Feature Model Plan

The ML layer converts mart-level outputs into a store-category-year feature table.

## Feature grain

```text
store_id + category + fiscal_year
```

This grain is used because margin-risk is most actionable when tied to both store and category.

## Feature inputs

Feature groups include:

### Profitability features

* net sales revenue,
* gross margin amount,
* gross margin rate,
* margin-at-risk,
* margin risk rate,
* markdown loss rate.

### Return and shrink features

* refund value rate,
* return rate,
* shrink value rate,
* shrink event rate,
* leakage rate.

### Inventory features

* stockout rate,
* overstock rate,
* average weeks of supply,
* inventory sell-through rate,
* average inventory value.

### Supplier and fulfillment features

* supplier average lead time days,
* supplier delay rate,
* supplier fill rate,
* fulfillment average lead time days,
* fulfillment delay rate,
* short shipment rate.

## Target variable

The target variable is:

```text
high_margin_risk_next_year
```

Definition:

```text
1 if next_year_margin_risk_rate >= P75 threshold
0 otherwise
```

The target is built from next fiscal-year margin-risk.

## Scoring design

The model is trained using historical years and then used to score current-year records.

Final model framing:

```text
Training period: FY2023
Test period: FY2024
Scoring period: FY2025
```

## Model artifact files

```text
models/margin_risk_model.joblib
models/feature_columns.json
models/model_metrics.json
```

## Processed ML files used by Streamlit

```text
data/processed/ml_margin_risk_scoring_features.csv
data/processed/ml_margin_risk_predictions_explained.csv
```

---

# Streamlit Simulator Data Plan

The Streamlit simulator uses only the final scoring and prediction artifacts.

## Input files

```text
streamlit_app/app.py
models/margin_risk_model.joblib
models/feature_columns.json
models/model_metrics.json
data/processed/ml_margin_risk_scoring_features.csv
data/processed/ml_margin_risk_predictions_explained.csv
```

## Simulator grain

```text
store-category-fiscal year
```

## Simulator workflow

```text
User selects case
        ↓
App loads original feature row
        ↓
User applies scenario preset or manual lever changes
        ↓
App updates selected feature values
        ↓
Model recalculates risk probability
        ↓
App compares original vs simulated risk
        ↓
App displays changed levers and driver comparison
        ↓
User can download scenario summary
```

## Scenario levers

The simulator allows changes to:

* inventory stockout rate,
* inventory overstock rate,
* average weeks of supply,
* refund value rate,
* shrink value rate,
* markdown loss rate,
* supplier average lead time days,
* fulfillment average lead time days,
* gross margin rate.

## Scenario presets

Final scenario presets:

* Inventory recovery
* Return reduction
* Leakage reduction
* Supply chain improvement
* Operational stress test
* Custom scenario

---

# Power BI Data Plan

The Power BI dashboard is designed around the dbt marts.

## Dashboard file

```text
powerbi/Retail_Margin_Resilience_Dashboard.pbix
```

## Dashboard pages

1. Executive Action Summary
2. Executive Margin Resilience
3. Inventory Health
4. Returns & Shrink Leakage
5. Fulfillment Reliability
6. Store & Category Profitability
7. Supplier Performance
8. Metric Definitions
9. Risk Threshold Reference
10. Predictive Risk Intelligence

## Reporting grain

Power BI uses multiple grains depending on page:

| Page                           | Primary grain                        |
| ------------------------------ | ------------------------------------ |
| Executive Action Summary       | Fiscal period                        |
| Executive Margin Resilience    | Fiscal period                        |
| Inventory Health               | Store-category-period                |
| Returns & Shrink Leakage       | Store-category-year or category-year |
| Fulfillment Reliability        | Supplier-category-period             |
| Store & Category Profitability | Store-category-year                  |
| Supplier Performance           | Supplier-category-year               |
| Predictive Risk Intelligence   | Store-category-year                  |

---

# Data Quality and Validation Plan

## Validation focus areas

The project validates:

* row counts,
* primary key uniqueness,
* foreign key relationships,
* non-negative financial values,
* date ranges,
* fiscal-year assignment,
* metric reasonableness,
* mart row counts,
* ML feature completeness,
* prediction output completeness.

## dbt tests

dbt model YAML files include tests for:

* not-null fields,
* unique keys,
* accepted values,
* relationships where appropriate.

## SQL validation

Validation SQL is stored in:

```text
sql/validation/validate_marts.sql
```

This file supports final checks across mart outputs.

---

# Data Storage and GitHub Visibility Plan

The repository is designed to show only files required for portfolio review and app deployment.

## Included in GitHub

```text
README.md
requirements.txt
docker-compose.yml
streamlit_app/
models/
data/processed/ml_margin_risk_scoring_features.csv
data/processed/ml_margin_risk_predictions_explained.csv
dbt_retail/
src/
sql/
docs/
powerbi/
```

## Excluded from GitHub

```text
.env
.venv/
mlruns/
data/raw/
data/exports/
extra generated processed files
dbt_retail/target/
dbt_retail/logs/
dbt_retail/dbt_packages/
```

## Reason for excluding raw/generated files

The raw generated files and intermediate generated outputs are excluded because:

* they are reproducible from scripts,
* they are not required for app deployment,
* they make the repository harder to review,
* they distract from the final usable project assets.

The Streamlit app keeps only the two processed files required for deployment.

---

# Key Modeling Decisions

## Store-category-year as ML grain

The model predicts risk at the store-category-year level because this is actionable for retail operators.

A prediction at only category level would be too broad.

A prediction at SKU level would be too granular for executive action.

Store-category-year provides a practical balance.

---

## Margin-at-risk as core risk measure

Margin-at-risk combines:

```text
markdown_loss + refund_amount + shrink_value
```

This reflects the idea that margin pressure comes from multiple leakage paths, not only weak sales.

---

## Distribution-based risk thresholds

The high margin-risk target uses a distribution-based threshold.

The project uses the P75 margin risk rate as the high-risk threshold.

This is appropriate for a synthetic portfolio project because no universal public benchmark exists for this exact synthetic metric.

---

## Early-warning model design

The model is designed to prioritize recall.

In a retail context, missing a future high-risk store-category may be more costly than flagging extra cases for review.

This is why the final decision threshold is lower than 50%.

---

## Simulator as sensitivity analysis

The Streamlit simulator changes selected model input features and recalculates predicted risk.

The simulator is not causal proof.

It is a decision-support tool for comparing hypothetical interventions and prioritizing investigation.

---

# Final Model Boundary

The final data model supports:

* descriptive analytics,
* diagnostic analytics,
* predictive analytics,
* what-if simulation.

The final data model does **not** support:

* real-time operations,
* automated replenishment decisions,
* customer-level personalization,
* causal intervention measurement,
* production financial forecasting.

---

# Summary

This data model is designed to connect retail operating signals to margin-risk outcomes.

It supports an end-to-end analytics workflow:

```text
Generate synthetic data
        ↓
Load PostgreSQL warehouse
        ↓
Transform with dbt
        ↓
Analyze in Power BI
        ↓
Train ML model
        ↓
Explain predictions
        ↓
Deploy Streamlit simulator
```

The final model demonstrates how a retailer could move from fragmented operational signals to a structured margin resilience decision-support platform.
