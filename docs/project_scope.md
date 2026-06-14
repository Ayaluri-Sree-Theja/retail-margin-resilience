# Project Scope

## Project name

Retail Margin Resilience Analytics

## Project type

Public-company-informed synthetic retail analytics case study.

This project is designed as an end-to-end analytics platform, not as a single dashboard. It combines business analysis, data engineering, analytics engineering, business intelligence, machine learning, model interpretation, and decision simulation.

## Anchor company

Target Corporation is used as the public-company reference for business context.

The operational dataset in this repository is simulated and does **not** represent Target's internal data.

## Final business question

How can a large retailer protect profit while balancing demand volatility, stockouts, overstock, returns, shrink, markdown exposure, supplier delays, and fulfillment delays?

## Business context

Large-format retailers face margin pressure from multiple connected operating problems. A store-category can appear healthy from a revenue perspective while still carrying hidden risk through:

* excess inventory,
* stockout exposure,
* markdown pressure,
* return leakage,
* shrink loss,
* supplier delays,
* fulfillment delays,
* weak category profitability.

This project treats margin resilience as a multi-factor operating problem rather than a simple sales reporting problem.

## Project objective

The objective is to build a decision-support platform that helps identify, explain, and simulate margin-risk at the store-category level.

The platform should help answer:

1. Which store-category combinations are most exposed to margin-risk?
2. What operational drivers are contributing to that risk?
3. Are risks coming from inventory, returns, shrink, markdowns, suppliers, or fulfillment?
4. Which business interventions could reduce predicted risk?
5. Which cases require deeper review even after improvement scenarios?
6. How can leaders prioritize action across stores, categories, and suppliers?

## In scope

The project includes the following workstreams.

### 1. Research and business framing

* Review public filings and investor materials for business context.
* Identify margin, inventory, fulfillment, and shrink-related themes.
* Convert public-company context into realistic project assumptions.
* Document assumptions separately from generated synthetic data.

### 2. Synthetic data generation

Generate synthetic retail operating data across:

* calendar,
* stores,
* products,
* suppliers,
* promotions,
* sales,
* returns,
* shrink events,
* purchase orders,
* shipments,
* weekly inventory snapshots.

The data is designed to simulate operational relationships between sales demand, inventory availability, supplier reliability, returns, shrink, markdowns, and margin-risk.

### 3. PostgreSQL warehouse

Build a PostgreSQL warehouse with:

* raw schemas,
* relational source tables,
* indexes,
* validation checks,
* load scripts.

### 4. dbt analytics engineering

Build dbt models across:

* staging,
* intermediate,
* marts.

The dbt layer standardizes source data, applies business logic, and creates analytics-ready marts for dashboarding and ML feature engineering.

### 5. KPI and metric layer

Define and calculate metrics related to:

* sales,
* gross margin,
* markdowns,
* returns,
* shrink,
* margin-at-risk,
* inventory health,
* supplier reliability,
* fulfillment reliability,
* predicted margin-risk.

### 6. Power BI dashboard

Build a Power BI dashboard for executive and operational analysis.

Dashboard pages include:

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

### 7. Machine learning risk model

Build an early-warning model that predicts whether a store-category combination is likely to become high margin-risk in the following fiscal year.

The model uses store-category operational features such as:

* current margin risk rate,
* gross margin rate,
* stockout rate,
* overstock rate,
* refund value rate,
* shrink value rate,
* markdown loss rate,
* weeks of supply,
* supplier lead time,
* fulfillment lead time.

### 8. Model driver explanation

Create an explanation layer that identifies which model inputs most influence predicted risk.

The explanation layer supports:

* global driver review,
* store-category driver review,
* original versus simulated driver comparison.

### 9. Streamlit what-if simulator

Deploy a Streamlit app that allows users to:

* filter by fiscal year,
* select case mode,
* select category,
* select risk band,
* select store-category,
* apply scenario presets,
* manually adjust operational levers,
* compare original and simulated risk,
* view changed levers,
* download scenario summaries,
* review model governance notes.

Deployed app:

https://retail-margin-risk-simulator.streamlit.app/

## Out of scope

The project does **not** include:

* actual Target transactional data,
* actual Target store-level data,
* actual Target SKU-level data,
* live database deployment,
* real-time inventory feeds,
* real-time sales feeds,
* production-grade MLOps,
* automated business decisioning,
* causal inference claims,
* financial forecasting for Target Corporation.

## Final deliverables

The final project deliverables are:

* synthetic data generation scripts,
* PostgreSQL schema creation scripts,
* ingestion scripts,
* dbt staging, intermediate, and mart models,
* metric definition documentation,
* Power BI dashboard file,
* ML feature engineering scripts,
* trained risk model artifact,
* model performance summary,
* model driver outputs,
* deployed Streamlit simulator,
* research notes,
* source log,
* data dictionary,
* project documentation.

## Data grain

The project uses multiple data grains.

### Transaction-level grain

Used for:

* sales,
* returns,
* shrink events,
* purchase orders,
* shipments.

### Weekly snapshot grain

Used for:

* inventory position,
* stockout status,
* overstock status,
* weeks of supply,
* inventory value.

### Store-category-year grain

Used for:

* profitability marts,
* ML feature engineering,
* next-year margin-risk prediction,
* Streamlit simulator.

## Final dataset coverage

The synthetic dataset covers fiscal retail operations from 2023 through early 2026.

Generated data includes:

* 60 stores,
* 360 products,
* 60 suppliers,
* 75 promotions,
* 1,099 calendar days,
* 623,496 sales rows,
* 31,139 return rows,
* 14,002 shrink event rows,
* 160,286 purchase order rows,
* 154,297 shipment rows,
* 3,391,200 weekly inventory snapshot rows.

## Final dbt marts

The final dbt mart layer includes:

* `mart_executive_margin_resilience`
* `mart_inventory_health`
* `mart_return_shrink_leakage`
* `mart_fulfillment_reliability`
* `mart_store_category_profitability`
* `mart_supplier_performance`

These marts support the Power BI dashboard and ML feature engineering layer.

## Final ML framing

The model predicts next-year high margin-risk at the store-category level.

Model framing:

* Model type: Logistic Regression
* Objective: early-warning detection of next-year high margin-risk
* Training period: FY2023
* Test period: FY2024
* Scoring period: FY2025
* Decision threshold: 39.3%

Model performance:

* Precision: 57.8%
* Recall: 94.9%
* F1 score: 0.718
* ROC-AUC: 0.946

The model is optimized for early-warning recall. In this business context, missing a future high-risk case can be more costly than flagging additional cases for review.

## Streamlit simulator scope

The simulator is designed for local sensitivity analysis.

Scenario presets include:

* Inventory recovery
* Return reduction
* Leakage reduction
* Supply chain improvement
* Operational stress test
* Custom scenario

The simulator shows:

* original risk probability,
* simulated risk probability,
* original risk band,
* simulated risk band,
* scenario type,
* changed levers,
* original model drivers,
* simulated model drivers,
* scenario interpretation,
* downloadable summary.

## Governance and interpretation

The simulator should be interpreted as a decision-support tool.

It should **not** be interpreted as:

* causal proof,
* a financial forecast,
* an automated decision rule,
* a replacement for business judgment,
* a real Target operating system.

The simulator changes selected model input features and recalculates predicted risk. The output is useful for investigation planning and scenario comparison, not for proving that a specific intervention will cause a specific financial outcome.

## Success criteria

The project is considered successful if it demonstrates the ability to:

* define a realistic retail business problem,
* design a synthetic operational data model,
* generate data with meaningful business relationships,
* build a relational warehouse,
* transform data using dbt,
* create business-ready marts,
* define clear metrics,
* build an executive dashboard,
* train and evaluate an early-warning ML model,
* explain model drivers,
* deploy an interactive simulator,
* document limitations and assumptions clearly.

## Final portfolio positioning

This project demonstrates practical capability across:

* business analysis,
* data analysis,
* data engineering,
* analytics engineering,
* business intelligence,
* machine learning,
* model interpretation,
* decision simulation,
* deployment.

The final project represents a complete analytics platform for retail margin resilience rather than a basic reporting dashboard.
