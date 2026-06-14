# Data Dictionary

This document describes the datasets, tables, model outputs, and business grains used in the Retail Margin Resilience Analytics project.

The project uses synthetic retail operations data. Public company filings and investor materials are used only for business context and assumption design. No internal Target data is used.

---

## Data Layer Overview

The project has five main data layers:

1. **Synthetic source data**

   * Generated using Python scripts.
   * Represents retail operations such as sales, returns, shrink, inventory, purchase orders, and shipments.

2. **PostgreSQL raw warehouse**

   * Stores generated source tables.
   * Loaded using Python ingestion scripts.
   * Initialized through SQL schema scripts.

3. **dbt transformation layer**

   * Standardizes raw data through staging models.
   * Builds enriched intermediate models.
   * Produces business-ready mart tables.

4. **Power BI reporting layer**

   * Uses dbt marts for executive and operational reporting.

5. **ML and simulator layer**

   * Uses store-category-year features.
   * Produces next-year margin-risk predictions.
   * Powers the deployed Streamlit simulator.

---

## Data Sources

The operational data in this project is synthetic and generated from Python scripts.

The synthetic data is informed by:

* public annual reports,
* retail operating patterns,
* inventory and fulfillment logic,
* margin and leakage assumptions,
* business rules documented in project notes.

The project does **not** use actual Target transactional, store, SKU, supplier, or customer data.

---

# Core Business Grains

## Calendar grain

One row per calendar date.

Used for:

* fiscal year mapping,
* fiscal month mapping,
* fiscal week mapping,
* trend analysis,
* date joins across fact tables.

---

## Store grain

One row per store.

Used for:

* store-level segmentation,
* region analysis,
* risk profile assignment,
* store-category profitability.

---

## Product grain

One row per product or SKU-like item.

Used for:

* category analysis,
* product cost and price assumptions,
* inventory and sales simulation,
* return and shrink behavior.

---

## Supplier grain

One row per supplier.

Used for:

* supplier lead time analysis,
* purchase order generation,
* shipment reliability,
* supplier performance mart.

---

## Promotion grain

One row per promotion.

Used for:

* discount behavior,
* markdown exposure,
* sales and margin pressure.

---

## Transaction grain

One row per sales transaction or operational event.

Used for:

* sales,
* returns,
* shrink events,
* purchase orders,
* shipments.

---

## Weekly inventory snapshot grain

One row per store-product-week.

Used for:

* ending inventory units,
* inventory value,
* stockout flags,
* overstock flags,
* weeks of supply,
* sell-through behavior.

---

## Store-category-year grain

One row per store, product category, and fiscal year.

Used for:

* profitability marts,
* ML feature engineering,
* next-year margin-risk prediction,
* Streamlit simulator.

---

# Dimension Tables

## dim_calendar

**Business purpose**

Provides fiscal and calendar attributes for joining dates across sales, returns, shrink, inventory, purchase orders, and shipments.

**Grain**

One row per calendar date.

**Key fields**

| Field          | Description                      |
| -------------- | -------------------------------- |
| date_key       | Date identifier used for joins   |
| calendar_date  | Actual calendar date             |
| fiscal_year    | Fiscal year assigned to the date |
| fiscal_quarter | Fiscal quarter                   |
| fiscal_month   | Fiscal month                     |
| fiscal_week    | Fiscal week                      |
| day_of_week    | Day name or day number           |
| is_weekend     | Weekend indicator                |

**Used by**

* fact_sales
* fact_return
* fact_shrink_event
* fact_inventory_snapshot
* fact_purchase_order
* fact_shipment
* dbt marts
* Power BI dashboard

---

## dim_store

**Business purpose**

Represents synthetic store locations and store-level risk characteristics.

**Grain**

One row per store.

**Key fields**

| Field        | Description                                  |
| ------------ | -------------------------------------------- |
| store_id     | Unique store identifier                      |
| store_name   | Synthetic store name                         |
| region       | Store region                                 |
| state        | Store state                                  |
| city         | Store city                                   |
| store_format | Store format or operating type               |
| risk_profile | Synthetic risk segment assigned to the store |
| opening_date | Store opening date assumption                |

**Used by**

* fact_sales
* fact_return
* fact_shrink_event
* fact_inventory_snapshot
* mart_store_category_profitability
* ML feature engineering
* Streamlit simulator

---

## dim_product

**Business purpose**

Represents synthetic products and category hierarchy.

**Grain**

One row per product.

**Key fields**

| Field               | Description                                |
| ------------------- | ------------------------------------------ |
| product_id          | Unique product identifier                  |
| product_name        | Synthetic product name                     |
| category            | Product category                           |
| subcategory         | Product subcategory                        |
| brand_type          | Private label or national brand assumption |
| unit_cost           | Synthetic unit cost                        |
| unit_price          | Synthetic selling price                    |
| return_risk_profile | Product-level return risk assumption       |
| shrink_risk_profile | Product-level shrink risk assumption       |

**Used by**

* fact_sales
* fact_return
* fact_shrink_event
* fact_inventory_snapshot
* mart_store_category_profitability
* mart_inventory_health
* ML feature engineering

---

## dim_supplier

**Business purpose**

Represents suppliers used for replenishment and shipment reliability analysis.

**Grain**

One row per supplier.

**Key fields**

| Field              | Description                           |
| ------------------ | ------------------------------------- |
| supplier_id        | Unique supplier identifier            |
| supplier_name      | Synthetic supplier name               |
| supplier_region    | Supplier location or operating region |
| reliability_tier   | Synthetic reliability segment         |
| avg_lead_time_days | Expected supplier lead time           |
| delay_risk_profile | Supplier delay risk assumption        |

**Used by**

* fact_purchase_order
* fact_shipment
* mart_supplier_performance
* ML feature engineering

---

## dim_promotion

**Business purpose**

Represents promotional and discount activity.

**Grain**

One row per promotion.

**Key fields**

| Field          | Description                 |
| -------------- | --------------------------- |
| promotion_id   | Unique promotion identifier |
| promotion_name | Promotion description       |
| promotion_type | Promotion type              |
| discount_rate  | Discount percentage         |
| start_date     | Promotion start date        |
| end_date       | Promotion end date          |
| category       | Promotion category focus    |

**Used by**

* fact_sales
* mart_executive_margin_resilience
* mart_store_category_profitability
* ML feature engineering

---

# Fact Tables

## fact_sales

**Business purpose**

Captures synthetic retail sales transactions.

**Grain**

One row per sales transaction.

**Key fields**

| Field               | Description                                      |
| ------------------- | ------------------------------------------------ |
| sales_id            | Unique sales transaction identifier              |
| date_key            | Transaction date                                 |
| store_id            | Store where sale occurred                        |
| product_id          | Product sold                                     |
| promotion_id        | Promotion applied, if applicable                 |
| channel             | Sales channel                                    |
| units_sold          | Units sold                                       |
| unit_price          | Selling price per unit                           |
| unit_cost           | Cost per unit                                    |
| gross_sales_amount  | Units sold multiplied by unit price              |
| discount_amount     | Synthetic discount or markdown value             |
| net_sales_revenue   | Gross sales less discount                        |
| cost_of_goods_sold  | Units sold multiplied by unit cost               |
| gross_margin_amount | Net sales revenue less cost of goods sold        |
| gross_margin_rate   | Gross margin amount divided by net sales revenue |

**Business use**

* Revenue analysis
* Gross margin analysis
* Channel analysis
* Store-category profitability
* ML feature creation

---

## fact_return

**Business purpose**

Captures synthetic customer returns and refund leakage.

**Grain**

One row per return event.

**Key fields**

| Field            | Description                             |
| ---------------- | --------------------------------------- |
| return_id        | Unique return identifier                |
| sales_id         | Related sales transaction, if available |
| date_key         | Return date                             |
| store_id         | Store associated with return            |
| product_id       | Returned product                        |
| channel          | Return channel                          |
| returned_units   | Number of returned units                |
| refund_amount    | Refund value                            |
| return_reason    | Reason for return                       |
| return_condition | Condition of returned item              |

**Business use**

* Return rate analysis
* Refund leakage analysis
* Category return patterns
* Store-category margin-risk modeling

---

## fact_shrink_event

**Business purpose**

Captures synthetic inventory loss events.

**Grain**

One row per shrink event.

**Key fields**

| Field                  | Description                                                                 |
| ---------------------- | --------------------------------------------------------------------------- |
| shrink_event_id        | Unique shrink event identifier                                              |
| date_key               | Shrink event date                                                           |
| store_id               | Store where shrink occurred                                                 |
| product_id             | Product affected                                                            |
| shrink_units           | Units lost                                                                  |
| estimated_shrink_value | Estimated value of lost inventory                                           |
| shrink_reason          | Theft, damage, miscount, ORC, mismatch, spoilage, or return processing loss |
| investigation_flag     | Indicator for events requiring review                                       |

**Business use**

* Shrink value analysis
* Operational leakage analysis
* Category risk identification
* Store-level risk assessment
* ML feature creation

---

## fact_purchase_order

**Business purpose**

Captures synthetic replenishment orders placed with suppliers.

**Grain**

One row per purchase order line.

**Key fields**

| Field                  | Description                      |
| ---------------------- | -------------------------------- |
| purchase_order_id      | Unique purchase order identifier |
| order_date_key         | Purchase order date              |
| store_id               | Destination store                |
| product_id             | Ordered product                  |
| supplier_id            | Supplier                         |
| ordered_units          | Units ordered                    |
| ordered_cost           | Total cost of ordered units      |
| purchase_order_status  | Delivered, cancelled, or open    |
| expected_delivery_date | Expected supplier delivery date  |

**Business use**

* Replenishment analysis
* Supplier order volume
* Supplier performance
* Shipment matching

---

## fact_shipment

**Business purpose**

Captures synthetic supplier shipment and delivery activity.

**Grain**

One row per shipment.

**Key fields**

| Field                  | Description                                    |
| ---------------------- | ---------------------------------------------- |
| shipment_id            | Unique shipment identifier                     |
| purchase_order_id      | Related purchase order                         |
| supplier_id            | Supplier                                       |
| store_id               | Destination store                              |
| product_id             | Product shipped                                |
| shipped_units          | Units shipped                                  |
| delivered_units        | Units delivered                                |
| shipment_date          | Shipment date                                  |
| delivery_date          | Delivery date                                  |
| expected_delivery_date | Expected delivery date                         |
| delay_days             | Number of delayed days                         |
| delayed_flag           | Indicates whether shipment was delayed         |
| short_shipment_flag    | Indicates whether delivered quantity was short |

**Business use**

* Supplier reliability
* Fulfillment delay analysis
* Lead time measurement
* Inventory risk modeling

---

## fact_inventory_snapshot

**Business purpose**

Captures weekly inventory position by store and product.

**Grain**

One row per store-product-week.

**Key fields**

| Field                     | Description                           |
| ------------------------- | ------------------------------------- |
| snapshot_id               | Unique inventory snapshot identifier  |
| week_start_date           | Start date of inventory week          |
| fiscal_year               | Fiscal year                           |
| store_id                  | Store                                 |
| product_id                | Product                               |
| beginning_inventory_units | Starting inventory units              |
| received_units            | Units received                        |
| sold_units                | Units sold                            |
| returned_units            | Units returned                        |
| shrink_units              | Units lost to shrink                  |
| ending_inventory_units    | Ending inventory units                |
| ending_inventory_value    | Estimated value of ending inventory   |
| stockout_flag             | Indicates stockout condition          |
| overstock_flag            | Indicates overstock condition         |
| weeks_of_supply           | Estimated weeks of inventory coverage |
| sell_through_rate         | Inventory sell-through rate           |

**Business use**

* Inventory health analysis
* Stockout analysis
* Overstock analysis
* Weeks of supply tracking
* Store-category ML features

---

# dbt Staging Models

Staging models standardize raw source tables, apply basic cleaning, and prepare consistent field names for downstream transformations.

## stg_calendar

Standardized calendar and fiscal date attributes.

## stg_stores

Standardized store attributes.

## stg_products

Standardized product and category attributes.

## stg_suppliers

Standardized supplier attributes.

## stg_promotions

Standardized promotion attributes.

## stg_sales

Standardized sales transaction fields and sales metrics.

## stg_returns

Standardized return event fields and refund metrics.

## stg_shrink_events

Standardized shrink event fields and shrink value metrics.

## stg_purchase_orders

Standardized purchase order fields.

## stg_shipments

Standardized shipment, lead time, delay, and short-shipment fields.

## stg_inventory_snapshots

Standardized weekly inventory snapshot fields.

---

# dbt Intermediate Models

Intermediate models combine staging models and calculate enriched business logic.

## int_sales_enriched

**Purpose**

Adds product, store, calendar, and promotion context to sales transactions.

**Business use**

Supports sales, margin, markdown, and profitability analysis.

---

## int_returns_enriched

**Purpose**

Adds product, store, and calendar context to return events.

**Business use**

Supports return leakage analysis and store-category return metrics.

---

## int_shrink_enriched

**Purpose**

Adds product, store, and calendar context to shrink events.

**Business use**

Supports shrink exposure analysis and operational loss metrics.

---

## int_inventory_enriched

**Purpose**

Adds product, category, store, and fiscal context to inventory snapshots.

**Business use**

Supports stockout, overstock, weeks of supply, and inventory value metrics.

---

## int_fulfillment_enriched

**Purpose**

Combines shipment, supplier, product, store, and calendar context.

**Business use**

Supports supplier and fulfillment reliability analysis.

---

# dbt Mart Models

The mart layer contains final analytics-ready tables used by Power BI and ML feature engineering.

## mart_executive_margin_resilience

**Grain**

Fiscal period-level summary.

**Business purpose**

Provides executive-level KPIs across sales, margin, markdowns, returns, shrink, inventory, and margin-risk.

**Key metric groups**

* Net sales revenue
* Gross margin
* Margin-at-risk
* Margin risk rate
* Return leakage
* Shrink leakage
* Markdown loss
* Inventory pressure

---

## mart_inventory_health

**Grain**

Store-category-fiscal period or store-category-year, depending on dashboard aggregation.

**Business purpose**

Tracks inventory productivity and risk.

**Key metric groups**

* Ending inventory units
* Ending inventory value
* Average inventory value
* Stockout rate
* Overstock rate
* Weeks of supply
* Sell-through rate

---

## mart_return_shrink_leakage

**Grain**

Store-category-fiscal year or category-level aggregation.

**Business purpose**

Combines return and shrink exposure.

**Key metric groups**

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

**Grain**

Store-category-supplier or fulfillment period aggregation.

**Business purpose**

Measures supplier and fulfillment reliability.

**Key metric groups**

* Shipment count
* Delayed shipments
* Delay rate
* Average delay days
* Lead time days
* Short shipment rate

---

## mart_store_category_profitability

**Grain**

Store-category-fiscal year.

**Business purpose**

Primary profitability and ML feature base table.

**Key metric groups**

* Net sales revenue
* Gross margin amount
* Gross margin rate
* Markdown loss
* Refund amount
* Shrink value
* Margin-at-risk
* Margin risk rate
* High margin-risk flag

**Used by**

* Power BI profitability page
* Predictive risk intelligence page
* ML feature engineering
* Streamlit simulator

---

## mart_supplier_performance

**Grain**

Supplier-category-fiscal year or supplier-level aggregation.

**Business purpose**

Measures supplier reliability and replenishment performance.

**Key metric groups**

* Ordered units
* Shipped units
* Delivered units
* Fill rate
* Delay rate
* Average lead time
* Short shipment rate

---

# Machine Learning Files

The ML layer creates feature datasets, prediction outputs, and model artifacts used by the deployed Streamlit app.

## data/processed/ml_margin_risk_scoring_features.csv

**Business purpose**

Contains store-category-year records used for scoring current fiscal-year risk.

**Grain**

One row per store-category-fiscal year.

**Used by**

* Streamlit simulator
* ML prediction recalculation
* Scenario feature adjustment

**Important fields**

| Field                          | Description                      |
| ------------------------------ | -------------------------------- |
| fiscal_year                    | Fiscal year of feature record    |
| store_id                       | Store identifier                 |
| store_name                     | Store name                       |
| category                       | Product category                 |
| margin_risk_rate               | Current margin risk rate         |
| gross_margin_rate              | Gross margin rate                |
| refund_value_rate              | Refund amount divided by revenue |
| shrink_value_rate              | Shrink value divided by revenue  |
| markdown_loss_rate             | Markdown loss divided by revenue |
| inventory_stockout_rate        | Stockout snapshot rate           |
| inventory_overstock_rate       | Overstock snapshot rate          |
| avg_weeks_of_supply            | Average weeks of supply          |
| supplier_avg_lead_time_days    | Supplier lead time               |
| fulfillment_avg_lead_time_days | Fulfillment lead time            |

---

## data/processed/ml_margin_risk_predictions_explained.csv

**Business purpose**

Contains model prediction results and explanation-ready output.

**Grain**

One row per store-category-fiscal year.

**Used by**

* Streamlit current prediction section
* Risk band filtering
* Driver explanation comparison
* Scenario summary generation

**Important fields**

| Field                        | Description                                            |
| ---------------------------- | ------------------------------------------------------ |
| fiscal_year                  | Fiscal year of prediction record                       |
| store_id                     | Store identifier                                       |
| store_name                   | Store name                                             |
| category                     | Product category                                       |
| predicted_risk_probability   | Model-estimated next-year high margin-risk probability |
| predicted_high_risk_flag     | Binary predicted high-risk indicator                   |
| predicted_risk_band          | Readable risk band                                     |
| original model driver fields | Driver values used for explanation and comparison      |

---

# Model Artifacts

## models/margin_risk_model.joblib

**Business purpose**

Trained machine learning model used by the Streamlit simulator.

**Model type**

Logistic Regression.

**Used by**

* Streamlit scenario recalculation
* Original versus simulated risk comparison

---

## models/feature_columns.json

**Business purpose**

Stores the feature column order expected by the trained model.

**Used by**

* Streamlit model input alignment
* Scenario recalculation

---

## models/model_metrics.json

**Business purpose**

Stores model performance and governance metadata.

**Used by**

* Streamlit Model Details and Governance section

**Included model metrics**

* decision threshold,
* precision,
* recall,
* F1 score,
* ROC-AUC,
* training and test strategy.

---

# Power BI File

## powerbi/Retail_Margin_Resilience_Dashboard.pbix

**Business purpose**

Power BI dashboard file for executive and operational reporting.

**Dashboard pages**

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

---

# Source Documentation

## docs/sources/

Contains public annual report PDFs used for business context and research assumptions.

These files are included for transparency.

They are not used as transactional data sources.

---

# Important Data Limitations

## Synthetic data

All operational data is generated for educational and portfolio purposes.

The dataset should not be interpreted as actual Target operational data.

## No customer-level data

The project does not include customer-level records, personally identifiable information, loyalty data, or payment data.

## No actual SKU-store data

The SKU-store-level operating records are synthetic.

They are designed to support realistic analytical workflows, not to represent actual company operations.

## No production data pipeline

The project simulates an analytics platform but does not include production-grade orchestration, monitoring, or real-time data ingestion.

---

# Usage Summary

| Layer           | Main files             | Purpose                                          |
| --------------- | ---------------------- | ------------------------------------------------ |
| Data generation | `src/data_generation/` | Generate synthetic retail data                   |
| Ingestion       | `src/ingestion/`       | Load generated data into PostgreSQL              |
| SQL setup       | `sql/init/`            | Create schemas, raw tables, and indexes          |
| Validation      | `sql/validation/`      | Validate marts and business outputs              |
| dbt             | `dbt_retail/models/`   | Build staging, intermediate, and mart tables     |
| ML              | `src/ml/`              | Build features, train model, explain predictions |
| Streamlit       | `streamlit_app/app.py` | Deployed what-if simulator                       |
| Power BI        | `powerbi/`             | Executive dashboard                              |
| Docs            | `docs/`                | Scope, metrics, data dictionary, research notes  |
