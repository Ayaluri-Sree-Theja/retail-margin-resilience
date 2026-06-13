# Target Filing Research Notes

## Purpose

This document translates Target Corporation’s public filing themes into analytics requirements for the Retail Margin Resilience Analytics project.

The goal is not to copy Target’s business exactly. The goal is to use public-company evidence to design a realistic retail analytics case study.

## Filing-Informed Business Themes

| Theme | Filing-Informed Business Context | Analytics Translation |
|---|---|---|
| Gross margin pressure | Target reported that gross margin rate declined from 28.2% in 2024 to 27.9% in 2025. | Build gross margin, return-adjusted margin, shrink-adjusted margin, and margin-at-risk KPIs. |
| Markdown pressure | Target cited higher markdowns and purchase order cancellation costs as part of the gross margin decline. | Track markdown exposure, overstock units, sell-through rate, and aging inventory. |
| Shrink | Target states that inventory is reduced for estimated losses related to shrink and markdowns. | Build shrink rate, shrink value, shrink-adjusted margin, and high-risk SKU-store combinations. |
| Category mix | Target cited changes in category sales mix as a gross margin driver. | Analyze profitability by category, department, store, and channel. |
| Inventory productivity | Retailers must balance excess inventory and stockouts. | Build weeks of supply, inventory turnover, stockout rate, overstock exposure, and reorder alerts. |
| Fulfillment reliability | Omnichannel retail creates fulfillment cost and service-level pressure. | Track supplier delays, on-time delivery rate, lead time variance, fill rate, and fulfillment delay rate. |
| Returns leakage | Returns reduce realized revenue and margin. | Build return-adjusted revenue, return-adjusted margin, return reason mix, and return risk score. |

## Executive Use Cases

### VP Retail Operations

Needs to understand:

- Margin-at-risk
- Shrink exposure
- Stockout risk
- Overstock exposure
- Fulfillment reliability
- Priority actions by region and category

### Supply Chain Manager

Needs to understand:

- Supplier delay patterns
- Lead time variance
- Purchase order reliability
- Store-SKU stockout risk
- Reorder urgency

### Merchandising / Category Manager

Needs to understand:

- Overstocked products
- Markdown candidates
- Low sell-through SKUs
- Return-prone categories
- Category margin performance

### Finance / Analytics Manager

Needs to understand:

- Return-adjusted revenue
- Shrink-adjusted margin
- Markdown loss
- Margin leakage drivers
- KPI definitions and assumptions

## Project Assumptions

Because this project uses simulated operational data, the dataset will be generated using realistic retail assumptions:

- Demand increases during holiday periods.
- Promotions increase units sold but reduce unit margin.
- Apparel and electronics have higher return rates than grocery.
- Small high-value products have higher shrink exposure.
- Supplier delays increase stockout risk.
- Overstocked products increase markdown exposure.
- Online orders have higher return rates than store purchases.
- Store risk profiles vary by region and store format.