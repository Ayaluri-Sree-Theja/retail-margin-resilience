# Filing Assumption Matrix

This document explains how public-company research was translated into synthetic data assumptions for the Retail Margin Resilience Analytics project.

Target Corporation is used as the public-company reference for business context. The operational dataset in this repository is simulated and does **not** represent Target's internal data.

---

## Purpose

The purpose of this matrix is to separate:

1. what came from public research,
2. how it was interpreted as a business theme,
3. how that theme became a synthetic data assumption,
4. where the assumption appears in the final analytics project.

This document is included to make the project transparent and portfolio-safe.

---

## Source boundary

Public filings and investor materials were used only for business context.

They were **not** used to extract actual:

* store-level transactions,
* SKU-level performance,
* supplier-level performance,
* return records,
* shrink events,
* inventory snapshots,
* fulfillment records,
* internal operating metrics.

All operational data in this project is synthetic.

---

## Public source files used

The repository includes the following public annual report PDFs for business context:

```text
docs/sources/2023-Annual-Report-Target-Corporation.pdf
docs/sources/2024-Annual-Report-Target-Corporation.pdf
docs/sources/target_2025_annual_report.pdf
```

These files support business framing only.

---

# Assumption Matrix

## 1. Margin pressure

| Item                    | Description                                                                                                           |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Large retailers must protect profitability while managing pricing, promotions, costs, and operational leakage.        |
| Project interpretation  | Margin should be analyzed beyond simple sales and revenue.                                                            |
| Synthetic assumption    | Sales transactions include unit price, unit cost, discounts, net sales revenue, cost of goods sold, and gross margin. |
| Generated data affected | `fact_sales`                                                                                                          |
| dbt models affected     | `stg_sales`, `int_sales_enriched`, `mart_executive_margin_resilience`, `mart_store_category_profitability`            |
| Metrics affected        | Net sales revenue, gross margin amount, gross margin rate, markdown loss, margin-at-risk, margin risk rate            |
| Dashboard use           | Executive Margin Resilience, Store & Category Profitability, Predictive Risk Intelligence                             |
| ML use                  | Gross margin rate, margin risk rate, markdown loss rate                                                               |
| Limitation              | Synthetic margins are modeled for portfolio realism and do not represent Target's actual margin structure.            |

---

## 2. Markdown and discount exposure

| Item                    | Description                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Retailers often use promotions and markdowns to manage demand, inventory, and price competitiveness.                         |
| Project interpretation  | Markdown pressure should be included as one source of margin-risk.                                                           |
| Synthetic assumption    | Promotions and discounts are assigned to a portion of sales transactions.                                                    |
| Generated data affected | `dim_promotion`, `fact_sales`                                                                                                |
| dbt models affected     | `stg_promotions`, `stg_sales`, `int_sales_enriched`, `mart_executive_margin_resilience`, `mart_store_category_profitability` |
| Metrics affected        | Discount amount, markdown loss, markdown loss rate, margin-at-risk                                                           |
| Dashboard use           | Executive Margin Resilience, Store & Category Profitability                                                                  |
| ML use                  | Markdown loss rate                                                                                                           |
| Simulator use           | Manual lever and leakage reduction scenario                                                                                  |
| Limitation              | Markdown behavior is simulated and not calibrated to actual Target promotional events.                                       |

---

## 3. Inventory productivity

| Item                    | Description                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Inventory levels affect sales availability, markdown exposure, working capital, and operational efficiency.       |
| Project interpretation  | Inventory health should be analyzed through both shortage and excess conditions.                                  |
| Synthetic assumption    | Weekly inventory snapshots are generated by store and product.                                                    |
| Generated data affected | `fact_inventory_snapshot`                                                                                         |
| dbt models affected     | `stg_inventory_snapshots`, `int_inventory_enriched`, `mart_inventory_health`                                      |
| Metrics affected        | Ending inventory units, ending inventory value, stockout rate, overstock rate, weeks of supply, sell-through rate |
| Dashboard use           | Inventory Health, Executive Action Summary                                                                        |
| ML use                  | Inventory stockout rate, inventory overstock rate, average weeks of supply, inventory sell-through rate           |
| Simulator use           | Inventory recovery scenario and operational stress test                                                           |
| Limitation              | Inventory thresholds are synthetic and designed for analytical demonstration.                                     |

---

## 4. Stockout exposure

| Item                    | Description                                                                                             |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Product unavailability can reduce sales opportunity and weaken customer experience.                     |
| Project interpretation  | Stockouts should be treated as a margin-resilience risk, not only an inventory metric.                  |
| Synthetic assumption    | Store-product-week records can be flagged as stockout snapshots when inventory falls below a threshold. |
| Generated data affected | `fact_inventory_snapshot`                                                                               |
| dbt models affected     | `int_inventory_enriched`, `mart_inventory_health`, `mart_store_category_profitability`                  |
| Metrics affected        | Stockout snapshots, stockout rate                                                                       |
| Dashboard use           | Inventory Health, Predictive Risk Intelligence                                                          |
| ML use                  | Inventory stockout rate                                                                                 |
| Simulator use           | Inventory recovery scenario, operational stress test                                                    |
| Limitation              | Stockout flags are simulated from generated inventory positions and demand assumptions.                 |

---

## 5. Overstock exposure

| Item                    | Description                                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| Public-company theme    | Excess inventory can create markdown pressure and reduce inventory productivity.                     |
| Project interpretation  | Overstock should be connected to margin-risk because excess supply can lead to discounting.          |
| Synthetic assumption    | Store-product-week records can be flagged as overstock snapshots when inventory exceeds a threshold. |
| Generated data affected | `fact_inventory_snapshot`                                                                            |
| dbt models affected     | `int_inventory_enriched`, `mart_inventory_health`, `mart_store_category_profitability`               |
| Metrics affected        | Overstock snapshots, overstock rate, average inventory value, weeks of supply                        |
| Dashboard use           | Inventory Health, Executive Action Summary                                                           |
| ML use                  | Inventory overstock rate, average weeks of supply, average inventory value                           |
| Simulator use           | Inventory recovery scenario, operational stress test                                                 |
| Limitation              | Overstock logic is synthetic and does not represent actual Target planning thresholds.               |

---

## 6. Returns leakage

| Item                    | Description                                                                                              |
| ----------------------- | -------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Returns can reduce realized revenue and create operational handling costs or markdown pressure.          |
| Project interpretation  | Refunds should be treated as a measurable leakage path.                                                  |
| Synthetic assumption    | Return events are generated from sales activity using product, category, channel, and risk assumptions.  |
| Generated data affected | `fact_return`                                                                                            |
| dbt models affected     | `stg_returns`, `int_returns_enriched`, `mart_return_shrink_leakage`, `mart_store_category_profitability` |
| Metrics affected        | Returned units, refund amount, return rate, refund value rate                                            |
| Dashboard use           | Returns & Shrink Leakage, Store & Category Profitability                                                 |
| ML use                  | Refund value rate                                                                                        |
| Simulator use           | Return reduction scenario, leakage reduction scenario                                                    |
| Limitation              | Return reasons and rates are simulated and should not be interpreted as actual company behavior.         |

---

## 7. Shrink exposure

| Item                    | Description                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Shrink is a retail operating risk that can reduce inventory value and profitability.                          |
| Project interpretation  | Shrink should be modeled as an operational loss and included in margin-risk.                                  |
| Synthetic assumption    | Shrink events are generated by store, product, reason, units, and estimated value.                            |
| Generated data affected | `fact_shrink_event`                                                                                           |
| dbt models affected     | `stg_shrink_events`, `int_shrink_enriched`, `mart_return_shrink_leakage`, `mart_store_category_profitability` |
| Metrics affected        | Shrink units, shrink value, shrink value rate, investigation flag                                             |
| Dashboard use           | Returns & Shrink Leakage, Executive Action Summary                                                            |
| ML use                  | Shrink value rate                                                                                             |
| Simulator use           | Leakage reduction scenario, operational stress test                                                           |
| Limitation              | Shrink reasons and values are simulated for analytics demonstration only.                                     |

---

## 8. Supplier reliability

| Item                    | Description                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Public-company theme    | Retail operations depend on reliable supplier replenishment and timely product flow.                               |
| Project interpretation  | Supplier performance should be connected to inventory and fulfillment risk.                                        |
| Synthetic assumption    | Suppliers are assigned reliability patterns that affect purchase orders and shipments.                             |
| Generated data affected | `dim_supplier`, `fact_purchase_order`, `fact_shipment`                                                             |
| dbt models affected     | `stg_suppliers`, `stg_purchase_orders`, `stg_shipments`, `int_fulfillment_enriched`, `mart_supplier_performance`   |
| Metrics affected        | Ordered units, shipped units, delivered units, supplier fill rate, supplier delay rate, supplier average lead time |
| Dashboard use           | Supplier Performance, Fulfillment Reliability                                                                      |
| ML use                  | Supplier average lead time days, supplier delay rate, supplier fill rate                                           |
| Simulator use           | Supply chain improvement scenario, operational stress test                                                         |
| Limitation              | Supplier reliability tiers are synthetic and not based on actual vendor performance.                               |

---

## 9. Fulfillment reliability

| Item                    | Description                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Fulfillment delays can affect customer experience, availability, and operational performance.                 |
| Project interpretation  | Fulfillment delay should be modeled as a risk signal that can contribute to margin pressure.                  |
| Synthetic assumption    | Shipments include expected delivery dates, actual delivery dates, delay days, and short-shipment flags.       |
| Generated data affected | `fact_shipment`                                                                                               |
| dbt models affected     | `stg_shipments`, `int_fulfillment_enriched`, `mart_fulfillment_reliability`                                   |
| Metrics affected        | Shipment count, delayed shipments, delay rate, average delay days, fulfillment lead time, short shipment rate |
| Dashboard use           | Fulfillment Reliability, Supplier Performance                                                                 |
| ML use                  | Fulfillment average lead time days, fulfillment delay rate                                                    |
| Simulator use           | Supply chain improvement scenario, operational stress test                                                    |
| Limitation              | Fulfillment records are simulated and do not reflect actual logistics events.                                 |

---

## 10. Store-level variation

| Item                    | Description                                                                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Retail performance varies by location because of demand, customer behavior, inventory execution, shrink exposure, and local operations. |
| Project interpretation  | Store-level risk profiles should create realistic variation across the synthetic network.                                               |
| Synthetic assumption    | Stores are assigned risk profiles that influence shrink, returns, inventory pressure, and margin-risk.                                  |
| Generated data affected | `dim_store`, all major fact tables                                                                                                      |
| dbt models affected     | All store-level staging, intermediate, and mart models                                                                                  |
| Metrics affected        | Store-level sales, margin, leakage, inventory, fulfillment, and predicted risk metrics                                                  |
| Dashboard use           | Store & Category Profitability, Inventory Health, Predictive Risk Intelligence                                                          |
| ML use                  | Store-category-year feature records                                                                                                     |
| Limitation              | Store risk profiles are synthetic and not based on actual store performance.                                                            |

---

## 11. Category-level variation

| Item                    | Description                                                                                                           |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Retail categories behave differently in terms of margin, returns, shrink, inventory velocity, and promotion exposure. |
| Project interpretation  | Category should be a core analysis dimension.                                                                         |
| Synthetic assumption    | Product categories are assigned different cost, price, return, shrink, and demand behavior assumptions.               |
| Generated data affected | `dim_product`, all product-linked fact tables                                                                         |
| dbt models affected     | Product, sales, returns, shrink, inventory, and profitability models                                                  |
| Metrics affected        | Category sales, gross margin, leakage, inventory health, predicted risk                                               |
| Dashboard use           | All major analytical pages                                                                                            |
| ML use                  | Category-level features and one-hot encoded category signals                                                          |
| Simulator use           | Category filter and store-category selection                                                                          |
| Limitation              | Category behaviors are simulated for analytical variety.                                                              |

---

## 12. Executive prioritization

| Item                    | Description                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Public-company theme    | Leaders need to prioritize action across many stores, categories, suppliers, and operational risks.                          |
| Project interpretation  | The project should combine risk intensity with business value exposure.                                                      |
| Synthetic assumption    | Marts include both percentage-based risk metrics and volume/value metrics.                                                   |
| Generated data affected | All major fact tables                                                                                                        |
| dbt models affected     | Executive, profitability, inventory, leakage, fulfillment, and supplier marts                                                |
| Metrics affected        | Revenue exposed, margin-at-risk, risk rate, average inventory value, predicted risk probability                              |
| Dashboard use           | Executive Action Summary, Predictive Risk Intelligence                                                                       |
| ML use                  | Predicted probability and risk banding                                                                                       |
| Simulator use           | Scenario selection and interpretation                                                                                        |
| Limitation              | Priority logic is designed for portfolio decision-support demonstration and is not an official Target prioritization method. |

---

# ML Assumption Translation

## Early-warning prediction

| Item                    | Description                                                                                                 |
| ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| Business theme          | Retailers benefit from identifying risk before it appears as next-year margin pressure.                     |
| Project interpretation  | Use current-year operating features to predict next-year high margin-risk.                                  |
| ML target               | `high_margin_risk_next_year`                                                                                |
| Target definition       | 1 if next-year margin risk rate is greater than or equal to the synthetic P75 threshold                     |
| Feature grain           | Store-category-fiscal year                                                                                  |
| Final model             | Logistic Regression                                                                                         |
| Reason for model choice | Interpretability and deployment simplicity                                                                  |
| Limitation              | The model predicts synthetic risk labels and should not be interpreted as a real-company forecasting model. |

---

## Model threshold assumption

| Item                     | Description                                                                             |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Business theme           | Missing a high-risk case may be costly in retail operations.                            |
| Project interpretation   | Prioritize recall for early warning.                                                    |
| Final decision threshold | 39.3%                                                                                   |
| Final recall             | 94.9%                                                                                   |
| Final precision          | 57.8%                                                                                   |
| Limitation               | Threshold is chosen for this synthetic case study and is not a universal business rule. |

---

# Streamlit Scenario Assumption Translation

## Scenario presets

| Scenario                 | Business meaning                                           | Main levers changed                                      |
| ------------------------ | ---------------------------------------------------------- | -------------------------------------------------------- |
| Inventory recovery       | Improve inventory balance and reduce availability pressure | Stockout rate, overstock rate, weeks of supply           |
| Return reduction         | Reduce refund leakage                                      | Refund value rate, markdown loss rate                    |
| Leakage reduction        | Reduce markdown, refund, and shrink pressure together      | Markdown loss rate, refund value rate, shrink value rate |
| Supply chain improvement | Improve lead time and replenishment reliability            | Supplier lead time, fulfillment lead time                |
| Operational stress test  | Simulate worsening operational pressure                    | Stockout, overstock, refund, shrink, markdown, lead time |
| Custom scenario          | Manual user-defined sensitivity test                       | User-selected levers                                     |

---

## Scenario interpretation boundary

The simulator is designed for sensitivity analysis.

It does **not** claim that changing a lever will directly cause the predicted outcome in the real world.

The correct interpretation is:

```text
If a selected store-category had these improved or worsened operational conditions, the trained model would estimate this revised level of next-year high margin-risk.
```

---

# Final Assumption Boundary

## What public filings influenced

Public filings and investor materials influenced:

* the business question,
* the importance of margin protection,
* the importance of inventory productivity,
* the inclusion of returns and shrink,
* the inclusion of supplier and fulfillment reliability,
* the executive decision-support framing.

## What public filings did not provide

Public filings did **not** provide:

* synthetic row-level data,
* actual Target store data,
* actual Target SKU data,
* actual Target return data,
* actual Target shrink data,
* actual Target supplier data,
* actual Target inventory snapshots,
* actual model labels,
* actual Streamlit simulator inputs.

---

# Summary

This matrix documents the bridge from public-company business research to synthetic project design.

The public materials gave the project a realistic retail context.

The actual analytics platform is built from synthetic data, generated assumptions, dbt transformations, Power BI dashboards, machine learning outputs, and a deployed Streamlit simulator.
