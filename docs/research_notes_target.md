# Research Notes: Target-Inspired Retail Context

This document summarizes the public-company business context used to frame the Retail Margin Resilience Analytics project.

Target Corporation is used as the anchor company for business context only. The operational dataset in this repository is synthetic and does **not** represent Target's internal data.

---

## Purpose of this research note

The purpose of this document is to explain how public retail context was converted into a synthetic analytics case study.

This document does not attempt to reproduce Target's actual operations. Instead, it identifies broad retail themes that are relevant to a large-format retailer and uses those themes to guide:

* project framing,
* synthetic data assumptions,
* metric design,
* dashboard focus areas,
* ML feature design,
* simulator scenario design.

---

## Anchor company

Target Corporation is used as the public-company reference because it represents a large-format retailer with:

* broad product categories,
* store and digital channels,
* inventory-intensive operations,
* supplier and fulfillment complexity,
* exposure to returns,
* exposure to shrink,
* margin pressure from promotions and markdowns,
* operational complexity across stores, products, suppliers, and fulfillment flows.

The project uses Target as a recognizable business context, not as a source of internal operational records.

---

## Core business problem identified

A large retailer does not lose margin from one single issue.

Margin pressure can emerge from a combination of:

* demand volatility,
* excess inventory,
* stockouts,
* markdowns,
* returns,
* shrink,
* supplier delays,
* fulfillment delays,
* weak category profitability,
* store-level operating differences.

The final business question became:

```text
How can a large retailer protect profit while balancing demand volatility, stockouts, overstock, returns, shrink, markdown exposure, supplier delays, and fulfillment delays?
```

---

## Public-company themes used for project framing

### 1. Margin protection

Large retailers must protect profitability while still competing on price, promotions, assortment, and convenience.

For this project, margin protection was translated into metrics such as:

* gross margin amount,
* gross margin rate,
* markdown loss,
* refund amount,
* shrink value,
* margin-at-risk,
* margin risk rate.

---

### 2. Inventory productivity

Inventory is a major operating lever in retail.

Too little inventory can create stockouts and missed sales.

Too much inventory can create markdown pressure, excess carrying value, and slower sell-through.

For this project, inventory productivity was translated into metrics such as:

* ending inventory units,
* ending inventory value,
* average inventory value,
* stockout rate,
* overstock rate,
* weeks of supply,
* inventory sell-through rate.

---

### 3. Returns leakage

Returns reduce realized revenue and can create additional handling, processing, and markdown pressure.

For this project, returns were modeled as a leakage path through:

* returned units,
* refund amount,
* return reason,
* refund value rate,
* return and shrink leakage.

---

### 4. Shrink exposure

Shrink is a material retail operating issue and can come from theft, damage, inventory miscounts, receiving mismatch, organized retail crime, spoilage, or return processing loss.

For this project, shrink was modeled through:

* shrink units,
* estimated shrink value,
* shrink reason,
* investigation flag,
* shrink value rate.

---

### 5. Fulfillment reliability

Retail performance depends on product availability and timely movement of goods.

Supplier delays and fulfillment delays can create stockout pressure, missed sales, customer dissatisfaction, and potential return risk.

For this project, fulfillment reliability was represented through:

* shipment count,
* delayed shipments,
* delay days,
* delay rate,
* supplier lead time,
* fulfillment lead time,
* short shipment rate.

---

### 6. Store-category variation

Retail risk is not evenly distributed.

Some stores and categories may carry higher risk due to product mix, demand patterns, return behavior, shrink exposure, supplier issues, or inventory imbalance.

For this project, the main analytical grain became:

```text
store + category + fiscal year
```

This grain supports:

* profitability analysis,
* store-category risk ranking,
* ML feature engineering,
* Streamlit scenario simulation.

---

## How research themes became synthetic data assumptions

The public-company research themes were converted into synthetic data assumptions.

| Research theme             | Synthetic data translation                                |
| -------------------------- | --------------------------------------------------------- |
| Margin pressure            | Gross margin, markdown loss, margin-at-risk               |
| Inventory productivity     | Stockout, overstock, weeks of supply, inventory value     |
| Returns leakage            | Return events, refund amounts, return reasons             |
| Shrink exposure            | Shrink events, shrink value, shrink reasons               |
| Supplier reliability       | Purchase orders, shipments, delays, lead time             |
| Fulfillment pressure       | Delayed shipments, short shipments, fulfillment lead time |
| Store/category differences | Store risk profiles and category-level variation          |
| Executive prioritization   | Risk rate plus business value exposure                    |

---

## Synthetic data design implications

The research framing led to the following design choices.

### Store design

The synthetic dataset includes 60 stores.

Stores are assigned risk profiles to simulate operational differences across locations.

Risk profiles help create realistic variation in:

* shrink exposure,
* return behavior,
* inventory pressure,
* margin-risk outcomes.

---

### Product and category design

The synthetic dataset includes 360 products across multiple retail categories.

Products include assumptions for:

* unit price,
* unit cost,
* category,
* subcategory,
* return tendency,
* shrink tendency.

This supports category-level differences in margin, return, and shrink behavior.

---

### Supplier design

The synthetic dataset includes 60 suppliers.

Suppliers include reliability assumptions to create variation in:

* lead time,
* delay risk,
* fill rate,
* short shipment behavior.

This supports supplier performance analysis and fulfillment reliability metrics.

---

### Promotion design

The synthetic dataset includes 75 promotions.

Promotions support:

* discount activity,
* markdown pressure,
* sales variation,
* margin risk modeling.

---

### Inventory design

Inventory is modeled using weekly store-product snapshots.

This supports the measurement of:

* stockouts,
* overstock,
* ending inventory,
* inventory value,
* weeks of supply,
* sell-through.

Weekly snapshots were chosen because inventory risk is better represented as a position over time rather than a single transaction.

---

## Dashboard design implications

The research themes shaped the final Power BI dashboard pages.

| Dashboard page                 | Research theme supported            |
| ------------------------------ | ----------------------------------- |
| Executive Action Summary       | Executive prioritization            |
| Executive Margin Resilience    | Margin protection                   |
| Inventory Health               | Inventory productivity              |
| Returns & Shrink Leakage       | Returns and shrink exposure         |
| Fulfillment Reliability        | Supplier and fulfillment pressure   |
| Store & Category Profitability | Store-category variation            |
| Supplier Performance           | Supplier reliability                |
| Predictive Risk Intelligence   | Early-warning margin-risk detection |

---

## ML design implications

The research framing led to an early-warning ML model.

The model predicts whether a store-category combination is likely to become high margin-risk in the next fiscal year.

### Target variable

```text
high_margin_risk_next_year
```

### Target definition

```text
1 if next_year_margin_risk_rate >= P75 threshold
0 otherwise
```

### Feature groups

The model uses features connected to the research themes:

* current margin risk rate,
* gross margin rate,
* markdown loss rate,
* refund value rate,
* shrink value rate,
* stockout rate,
* overstock rate,
* weeks of supply,
* supplier lead time,
* fulfillment lead time.

The model was designed for early-warning detection, not causal proof.

---

## Streamlit simulator design implications

The research themes also shaped the Streamlit scenario simulator.

The simulator allows users to test intervention-style scenarios such as:

* Inventory recovery
* Return reduction
* Leakage reduction
* Supply chain improvement
* Operational stress test
* Custom scenario

Each scenario adjusts operational levers and recalculates predicted margin-risk.

This turns the project from a static dashboard into an interactive decision-support tool.

---

## Important boundary between research and data

This project separates business context from operational data.

### Public research provides:

* business framing,
* operating themes,
* metric inspiration,
* assumption direction.

### Synthetic generation provides:

* sales data,
* return data,
* shrink data,
* inventory data,
* supplier data,
* fulfillment data,
* ML training and scoring records.

The public research does **not** provide actual transaction-level data.

---

## What this project does not claim

This project does not claim to know or reproduce:

* Target's actual store-level performance,
* Target's actual SKU-level sales,
* Target's actual inventory levels,
* Target's actual supplier performance,
* Target's actual return rates,
* Target's actual shrink events,
* Target's actual margin-risk profile,
* Target's internal decision systems.

The project is a synthetic case study built for analytics portfolio demonstration.

---

## Final research conclusion

The research process showed that a realistic retail analytics project should not focus only on sales trends.

A stronger project should connect:

```text
inventory health
+ returns leakage
+ shrink exposure
+ markdown pressure
+ supplier reliability
+ fulfillment reliability
+ store-category profitability
= margin resilience
```

This conclusion shaped the final project architecture:

```text
synthetic retail operations data
        ↓
PostgreSQL warehouse
        ↓
dbt marts
        ↓
Power BI dashboard
        ↓
ML risk model
        ↓
Streamlit what-if simulator
```

The final project uses public-company context to frame a realistic retail problem while keeping all operational data synthetic and portfolio-safe.
