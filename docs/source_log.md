# Source Log

This document lists the public source materials used to frame the Retail Margin Resilience Analytics project.

Target Corporation is used as the public-company reference for business context. The operational dataset in this repository is synthetic and does **not** represent Target's internal data.

---

## Purpose of this source log

The purpose of this document is to make the research basis of the project transparent.

The public sources were used to understand broad retail business context, including:

* margin pressure,
* inventory productivity,
* returns and refund exposure,
* shrink exposure,
* supplier and fulfillment complexity,
* store and category operating variation,
* executive-level retail performance themes.

The sources were **not** used to extract internal operating data or transaction-level records.

---

## Source boundary

Public filings and investor materials were used only for business context and assumption design.

They were not used as direct inputs for:

* sales transactions,
* SKU-store data,
* supplier records,
* customer records,
* return records,
* shrink events,
* inventory snapshots,
* purchase orders,
* shipment records,
* machine learning labels,
* model predictions.

All operational records in this project were generated synthetically.

---

# Public Source Files Included in Repository

The following source files are included in the repository under:

```text
docs/sources/
```

## 1. 2023 Annual Report — Target Corporation

**Repository path**

```text
docs/sources/2023-Annual-Report-Target-Corporation.pdf
```

**Source type**

Public annual report.

**How it was used**

Used for business context related to:

* large-format retail operations,
* sales and margin framing,
* inventory and operating performance themes,
* risk and business environment context,
* retail reporting language.

**How it was not used**

This report was not used to extract:

* transaction-level data,
* store-level data,
* SKU-level data,
* customer data,
* supplier-level records,
* actual Target operating metrics for the synthetic dataset.

---

## 2. 2024 Annual Report — Target Corporation

**Repository path**

```text
docs/sources/2024-Annual-Report-Target-Corporation.pdf
```

**Source type**

Public annual report.

**How it was used**

Used for business context related to:

* profitability and margin discussion,
* inventory and operations framing,
* shrink and retail risk context,
* fulfillment and supply chain context,
* executive reporting themes.

**How it was not used**

This report was not used to create actual Target-like transaction records.

All operating rows in the project were generated using synthetic assumptions and Python scripts.

---

## 3. 2025 Annual Report — Target Corporation

**Repository path**

```text
docs/sources/target_2025_annual_report.pdf
```

**Source type**

Public annual report.

**How it was used**

Used for updated public-company context related to:

* retail operating environment,
* margin and profitability themes,
* inventory productivity,
* fulfillment and digital retail context,
* risk factor framing,
* business language for final documentation.

**How it was not used**

This report was not used as a direct data source for:

* Power BI data,
* dbt marts,
* ML training rows,
* Streamlit simulator inputs,
* model outcomes.

---

# Research-to-Project Mapping

## Margin protection

**Research signal**

Retailers must manage profitability while balancing pricing, promotions, inventory, and operational costs.

**Project translation**

The project includes:

* gross margin amount,
* gross margin rate,
* markdown loss,
* refund amount,
* shrink value,
* margin-at-risk,
* margin risk rate.

**Project files influenced**

```text
docs/metric_definitions.md
dbt_retail/models/marts/mart_executive_margin_resilience.sql
dbt_retail/models/marts/mart_store_category_profitability.sql
src/ml/build_margin_risk_features.py
streamlit_app/app.py
```

---

## Inventory productivity

**Research signal**

Inventory management is central to retail performance because both shortage and excess can damage profitability.

**Project translation**

The project includes:

* weekly inventory snapshots,
* ending inventory value,
* stockout flags,
* overstock flags,
* weeks of supply,
* sell-through rate.

**Project files influenced**

```text
src/data_generation/generate_inventory_snapshots.py
dbt_retail/models/staging/stg_inventory_snapshots.sql
dbt_retail/models/intermediate/int_inventory_enriched.sql
dbt_retail/models/marts/mart_inventory_health.sql
streamlit_app/app.py
```

---

## Returns leakage

**Research signal**

Returns reduce realized revenue and can create additional operational and margin pressure.

**Project translation**

The project includes:

* return events,
* returned units,
* refund amount,
* return reason,
* refund value rate,
* return and shrink leakage.

**Project files influenced**

```text
src/data_generation/generate_returns.py
dbt_retail/models/staging/stg_returns.sql
dbt_retail/models/intermediate/int_returns_enriched.sql
dbt_retail/models/marts/mart_return_shrink_leakage.sql
streamlit_app/app.py
```

---

## Shrink exposure

**Research signal**

Shrink is a major retail operating risk and can reduce both inventory value and margin.

**Project translation**

The project includes:

* shrink events,
* shrink units,
* estimated shrink value,
* shrink reason,
* investigation flag,
* shrink value rate.

**Project files influenced**

```text
src/data_generation/generate_shrink_events.py
dbt_retail/models/staging/stg_shrink_events.sql
dbt_retail/models/intermediate/int_shrink_enriched.sql
dbt_retail/models/marts/mart_return_shrink_leakage.sql
streamlit_app/app.py
```

---

## Supplier and fulfillment reliability

**Research signal**

Retail performance depends on reliable replenishment and timely product movement.

**Project translation**

The project includes:

* purchase orders,
* shipments,
* delivered units,
* delayed shipments,
* delay days,
* supplier lead time,
* fulfillment lead time,
* short shipment rate.

**Project files influenced**

```text
src/data_generation/generate_purchase_orders_shipments.py
dbt_retail/models/staging/stg_purchase_orders.sql
dbt_retail/models/staging/stg_shipments.sql
dbt_retail/models/intermediate/int_fulfillment_enriched.sql
dbt_retail/models/marts/mart_fulfillment_reliability.sql
dbt_retail/models/marts/mart_supplier_performance.sql
streamlit_app/app.py
```

---

## Store-category variation

**Research signal**

Retail operating performance varies across stores and product categories.

**Project translation**

The project uses store-category-year as the core analytical and ML grain.

**Project files influenced**

```text
dbt_retail/models/marts/mart_store_category_profitability.sql
src/ml/build_margin_risk_features.py
src/ml/train_margin_risk_model.py
src/ml/explain_margin_risk_model.py
streamlit_app/app.py
```

---

# Internal Project Artifacts Created from Research

The following documents were created as project artifacts based on the research and synthetic design process.

## docs/project_scope.md

Defines:

* final business question,
* project objective,
* in-scope work,
* out-of-scope boundaries,
* final deliverables,
* ML and simulator scope.

## docs/research_notes_target.md

Documents:

* public-company business themes,
* how those themes shaped the project,
* the distinction between public context and synthetic data.

## docs/filing_assumption_matrix.md

Documents:

* how public-company themes became synthetic assumptions,
* where those assumptions appear in data generation,
* dbt models,
* Power BI,
* ML,
* Streamlit.

## docs/metric_definitions.md

Defines:

* sales metrics,
* margin metrics,
* return metrics,
* shrink metrics,
* inventory metrics,
* supplier metrics,
* fulfillment metrics,
* ML metrics,
* simulator metrics.

## docs/data_model_plan.md

Documents:

* conceptual model,
* logical model,
* physical warehouse plan,
* dbt modeling plan,
* ML feature model,
* Streamlit data plan.

## docs/data_dictionary.md

Documents:

* source table purpose,
* dimension tables,
* fact tables,
* dbt models,
* ML files,
* model artifacts,
* Power BI file.

---

# Data Source Classification

| Source type                      | Used in project? | Notes                                                |
| -------------------------------- | ---------------: | ---------------------------------------------------- |
| Public annual reports            |              Yes | Used for business context only                       |
| Investor materials               |              Yes | Used for business framing and terminology            |
| Actual Target transactional data |               No | Not used                                             |
| Actual Target SKU-level data     |               No | Not used                                             |
| Actual Target store-level data   |               No | Not used                                             |
| Actual Target customer data      |               No | Not used                                             |
| Actual Target supplier records   |               No | Not used                                             |
| Synthetic generated data         |              Yes | Used for warehouse, dbt, Power BI, ML, and Streamlit |
| ML-generated prediction outputs  |              Yes | Used for Streamlit and predictive dashboard page     |

---

# Synthetic Data Generation Sources

The synthetic operating data was generated using Python scripts in:

```text
src/data_generation/
```

Generated areas include:

```text
generate_dimensions.py
generate_sales.py
generate_returns.py
generate_shrink_events.py
generate_purchase_orders_shipments.py
generate_inventory_snapshots.py
patch_store_risk_profiles.py
```

These scripts created simulated data for:

* stores,
* products,
* suppliers,
* promotions,
* sales,
* returns,
* shrink events,
* purchase orders,
* shipments,
* inventory snapshots.

---

# Source Use by Project Layer

| Project layer             | Source basis                                          |
| ------------------------- | ----------------------------------------------------- |
| Business framing          | Public annual reports and research notes              |
| Synthetic data generation | Project assumptions and Python generation logic       |
| PostgreSQL warehouse      | Synthetic generated data                              |
| dbt transformations       | Synthetic warehouse tables                            |
| Power BI dashboard        | dbt marts and ML outputs                              |
| ML training               | Synthetic mart-derived feature records                |
| Streamlit simulator       | Synthetic scoring features and trained model artifact |
| Documentation             | Public context plus generated project outputs         |

---

# Important Limitations

## Public reports are not operational datasets

Annual reports provide high-level business context.

They do not provide the detailed row-level data needed for:

* store-category sales,
* weekly inventory snapshots,
* individual return events,
* shrink events,
* supplier shipments,
* ML labels.

All such records are synthetic.

---

## Synthetic assumptions are not company facts

The assumptions used in this project are designed to create a realistic analytics workflow.

They should not be interpreted as factual claims about Target Corporation.

---

## Model outputs are synthetic-case outputs

The ML model predicts risk within the synthetic dataset.

The model does not predict actual Target risk.

---

## Simulator outputs are sensitivity analysis

The Streamlit simulator changes model input features and recalculates predicted risk.

The simulator does not prove causal impact.

---

# Final Source Statement

This project uses Target Corporation as a public-company anchor for retail business context.

The final analytics platform, including the warehouse, dbt models, Power BI dashboard, ML model, and Streamlit simulator, is built from synthetic data created for educational and portfolio purposes.

No internal company data is used.
