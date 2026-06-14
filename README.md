# Retail Margin Resilience Analytics Platform

A Target-inspired synthetic retail analytics platform that analyzes how a large-format retailer can protect margin while balancing demand volatility, stockouts, overstock, returns, shrink, markdowns, supplier delays, and fulfillment reliability.

This project combines data engineering, analytics engineering, business intelligence, machine learning, and decision simulation into one end-to-end portfolio case study.

**Deployed Streamlit simulator:** https://retail-margin-risk-simulator.streamlit.app/

---

## Project Objective

Retailers do not lose margin from one isolated problem. Margin pressure usually emerges from several connected operational issues:

* stockouts that reduce sales opportunity,
* overstock that increases markdown exposure,
* returns that reduce realized revenue,
* shrink that creates leakage,
* supplier and fulfillment delays that affect availability,
* category and store-level variation in profitability.

The objective of this project is to build a decision-support system that helps answer:

> How can a retailer identify margin-risk early, explain the drivers, and test operational interventions before the risk becomes visible in financial outcomes?

---

## What This Project Includes

This project includes five connected layers:

1. **Synthetic retail data generation**

   * Store, product, supplier, promotion, calendar, sales, returns, shrink, purchase order, shipment, and inventory snapshot data.
   * Synthetic data is inspired by public retail operating patterns and annual-report research, not actual Target transactional data.

2. **PostgreSQL warehouse**

   * Raw schemas and relational tables for generated retail operations data.
   * SQL validation checks for row counts, reconciliation, and metric consistency.

3. **dbt analytics engineering**

   * Staging models for source standardization.
   * Intermediate models for enriched business logic.
   * Mart models for executive, inventory, returns/shrink, fulfillment, store-category, and supplier analysis.
   * Model tests and documentation-ready transformations.

4. **Power BI executive dashboard**

   * Executive margin resilience summary.
   * Inventory health.
   * Return and shrink leakage.
   * Fulfillment reliability.
   * Store and category profitability.
   * Supplier performance.
   * Predictive risk intelligence page.

5. **Machine learning and Streamlit simulator**

   * Next-year high margin-risk prediction model.
   * Driver explanation layer.
   * What-if simulator for operational interventions.
   * Scenario summary download.
   * Model governance notes for responsible interpretation.

---

## Deployed Application

The Streamlit application allows users to:

* select fiscal year, category, store-category, and risk segment,
* view current predicted margin-risk,
* inspect model drivers,
* simulate intervention scenarios,
* compare original versus simulated risk,
* download a scenario summary,
* review model governance information.

**Live app:** https://retail-margin-risk-simulator.streamlit.app/

Example scenario types:

* Inventory recovery
* Leakage reduction
* Supply chain improvement
* Operational stress test
* Custom scenario

---

## Repository Structure

```text
retail-margin-resilience/
│
├── README.md
├── requirements.txt
├── docker-compose.yml
│
├── streamlit_app/
│   └── app.py
│
├── models/
│   ├── feature_columns.json
│   ├── margin_risk_model.joblib
│   └── model_metrics.json
│
├── data/
│   └── processed/
│       ├── ml_margin_risk_predictions_explained.csv
│       └── ml_margin_risk_scoring_features.csv
│
├── dbt_retail/
│   ├── dbt_project.yml
│   ├── profiles_template.yml
│   ├── macros/
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
│
├── src/
│   ├── data_generation/
│   ├── ingestion/
│   └── ml/
│
├── sql/
│   ├── init/
│   └── validation/
│
├── powerbi/
│   └── Retail_Margin_Resilience_Dashboard.pbix
│
└── docs/
    ├── data_dictionary.md
    ├── data_model_plan.md
    ├── filing_assumption_matrix.md
    ├── metric_definitions.md
    ├── project_scope.md
    ├── research_notes_target.md
    ├── source_log.md
    └── sources/
```

---

## Synthetic Dataset Summary

The project uses a synthetic dataset covering fiscal retail operations from 2023 through early 2026.

Key generated entities include:

* 60 stores
* 360 products
* 60 suppliers
* 75 promotions
* 1,099 calendar days
* 623,496 sales rows
* 31,139 return rows
* 14,002 shrink event rows
* 160,286 purchase order rows
* 154,297 shipment rows
* 3,391,200 weekly inventory snapshot rows

The synthetic data is designed to reflect realistic operational relationships between demand, inventory availability, supplier reliability, returns, shrink, markdown exposure, and margin risk.

---

## Core Business Metrics

The project focuses on margin resilience rather than simple revenue reporting.

Core metrics include:

* Net sales revenue
* Gross margin amount
* Gross margin rate
* Markdown loss
* Refund amount
* Shrink value
* Margin-at-risk
* Margin risk rate
* Return rate
* Shrink rate
* Stockout rate
* Overstock rate
* Weeks of supply
* Supplier delay rate
* Fulfillment delay rate
* Predicted high margin-risk probability

Definitions are documented in `docs/metric_definitions.md`.

---

## Machine Learning Layer

The ML layer predicts whether a store-category combination is likely to become high margin-risk in the following fiscal year.

The model uses historical operational signals such as:

* current margin risk rate,
* stockout rate,
* overstock rate,
* refund value rate,
* shrink value rate,
* markdown loss rate,
* gross margin rate,
* weeks of supply,
* supplier lead time,
* fulfillment lead time.

Model summary:

* Model type: Logistic regression
* Objective: early warning detection of next-year high margin-risk
* Split strategy: train on FY2023, test on FY2024
* Decision threshold: 39.3%
* Precision: 57.8%
* Recall: 94.9%
* F1 score: 0.718
* ROC-AUC: 0.946

The model is intentionally framed as an early-warning decision-support model. It is not presented as causal proof or as an automated decision rule.

---

## Streamlit What-If Simulator

The deployed simulator extends the ML model into a business-facing decision tool.

Users can test scenarios such as:

* reducing stockout and overstock pressure,
* reducing returns, shrink, and markdown leakage,
* improving supplier and fulfillment lead times,
* applying operational stress conditions,
* manually adjusting key risk levers.

The simulator recalculates predicted margin-risk and explains how the risk changes under each scenario.

The downloadable scenario summary includes:

* fiscal year,
* store,
* category,
* original risk probability,
* simulated risk probability,
* original and simulated risk bands,
* scenario type,
* changed levers,
* scenario interpretation,
* model governance note.

---

## Power BI Dashboard

The Power BI dashboard provides executive and operational views across the retail margin resilience problem.

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

The dashboard file is available in:

```text
powerbi/Retail_Margin_Resilience_Dashboard.pbix
```

---

## Tech Stack

* Python
* pandas
* NumPy
* scikit-learn
* joblib
* PostgreSQL
* dbt
* SQL
* Power BI
* Streamlit
* GitHub
* Docker

---

## How to Run the Streamlit App Locally

Clone the repository:

```bash
git clone https://github.com/Ayaluri-Sree-Theja/retail-margin-resilience.git
cd retail-margin-resilience
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run streamlit_app/app.py
```

---

## Important Disclaimer

This is a synthetic analytics project created for portfolio and learning purposes.

This project is not affiliated with, endorsed by, or based on internal data from Target Corporation. Public annual reports and filings were used only to guide realistic business assumptions and retail context. All transactional, operational, inventory, supplier, and ML datasets are synthetic.

---

## Portfolio Positioning

This project demonstrates the ability to:

* translate a business problem into measurable analytical questions,
* design synthetic but realistic operational data,
* build a relational warehouse,
* transform data using dbt,
* create executive BI reporting,
* train and evaluate an ML early-warning model,
* explain model drivers,
* deploy a business-facing what-if simulator,
* communicate limitations and governance clearly.

The project is designed to represent a realistic analytics platform rather than a single dashboard.
