# Metric Definitions

This document defines the business metrics used in the Retail Margin Resilience Analytics project.

The goal of the metric layer is to measure how margin pressure emerges from connected operational issues such as demand volatility, stockouts, overstock, returns, shrink, markdowns, supplier delays, and fulfillment delays.

## Metric philosophy

This project does not treat revenue as the only measure of retail performance.

A store-category can generate strong sales while still carrying high margin-risk because of:

* high markdown exposure,
* frequent returns,
* shrink loss,
* stockout pressure,
* excess inventory,
* supplier delays,
* fulfillment delays,
* weak gross margin rate.

The metrics are designed to help identify where profit protection may require operational action.

## General calculation rules

Unless otherwise noted:

* Rates are calculated as numerator divided by denominator.
* Percentage values are shown as percentage points in dashboard and simulator outputs.
* Financial values are synthetic USD values.
* Store-category metrics are aggregated from transaction or snapshot-level data.
* Division by zero should return `0` or `null`, depending on downstream reporting needs.
* Risk thresholds are distribution-based within the synthetic dataset and are not universal retail benchmarks.

---

# Sales and Margin Metrics

## Gross sales amount

**Definition**

Total sales value before discounts, returns, shrink, or markdown-related leakage.

**Formula**

```text
gross_sales_amount = units_sold × unit_price
```

**Business interpretation**

Measures top-line sales activity before revenue reductions.

---

## Discount amount

**Definition**

Value reduced from gross sales due to applied discounts or promotions.

**Formula**

```text
discount_amount = gross_sales_amount × discount_rate
```

**Business interpretation**

Indicates promotional or markdown pressure at the transaction level.

---

## Net sales revenue

**Definition**

Sales revenue after discounts.

**Formula**

```text
net_sales_revenue = gross_sales_amount - discount_amount
```

**Business interpretation**

Primary revenue measure used for margin and leakage rate calculations.

---

## Cost of goods sold

**Definition**

Estimated product cost associated with units sold.

**Formula**

```text
cost_of_goods_sold = units_sold × unit_cost
```

**Business interpretation**

Represents the cost base used to calculate gross margin.

---

## Gross margin amount

**Definition**

Profit remaining after subtracting product cost from net sales revenue.

**Formula**

```text
gross_margin_amount = net_sales_revenue - cost_of_goods_sold
```

**Business interpretation**

Measures core product-level profitability before returns, shrink, and broader operating expenses.

---

## Gross margin rate

**Definition**

Gross margin amount as a share of net sales revenue.

**Formula**

```text
gross_margin_rate = gross_margin_amount / net_sales_revenue
```

**Business interpretation**

Shows how efficiently sales convert into gross profit.

A lower gross margin rate may indicate high cost pressure, pricing weakness, discounting, or unfavorable product mix.

---

# Markdown, Return, and Shrink Metrics

## Markdown loss

**Definition**

Estimated margin or revenue pressure caused by discounting and markdown activity.

**Formula**

```text
markdown_loss = discount_amount
```

**Business interpretation**

Represents profit pressure caused by selling below full expected price.

Markdown loss is especially important when overstock or weak demand forces price reductions.

---

## Refund amount

**Definition**

Total dollar value refunded to customers for returned items.

**Formula**

```text
refund_amount = returned_units × refund_unit_amount
```

**Business interpretation**

Measures revenue leakage caused by returns.

High refund amount can indicate product quality issues, size or fit problems, fulfillment errors, damaged items, or customer dissatisfaction.

---

## Return rate by units

**Definition**

Returned units as a share of sold units.

**Formula**

```text
return_rate_units = returned_units / units_sold
```

**Business interpretation**

Measures how frequently sold units come back as returns.

---

## Refund value rate

**Definition**

Refund amount as a share of net sales revenue.

**Formula**

```text
refund_value_rate = refund_amount / net_sales_revenue
```

**Business interpretation**

Measures the financial impact of returns relative to revenue.

This is more useful than unit return rate when return values vary by category.

---

## Shrink value

**Definition**

Estimated value of inventory lost due to theft, damage, inventory miscount, organized retail crime, receiving mismatch, spoilage, or return processing loss.

**Formula**

```text
shrink_value = shrink_units × estimated_unit_cost_or_value
```

**Business interpretation**

Measures operational leakage that reduces inventory and margin without producing revenue.

---

## Shrink rate by units

**Definition**

Shrink units as a share of available or handled inventory units.

**Formula**

```text
shrink_rate_units = shrink_units / inventory_units_available
```

**Business interpretation**

Measures physical inventory loss intensity.

---

## Shrink value rate

**Definition**

Shrink value as a share of net sales revenue.

**Formula**

```text
shrink_value_rate = shrink_value / net_sales_revenue
```

**Business interpretation**

Measures financial exposure from shrink relative to sales.

High shrink value rate may indicate store-level operational risk, category vulnerability, or process control issues.

---

## Return and shrink leakage

**Definition**

Combined financial leakage from customer refunds and shrink loss.

**Formula**

```text
return_shrink_leakage = refund_amount + shrink_value
```

**Business interpretation**

Measures non-markdown leakage that reduces realized profitability.

---

## Leakage rate

**Definition**

Return and shrink leakage as a share of net sales revenue.

**Formula**

```text
leakage_rate = return_shrink_leakage / net_sales_revenue
```

**Business interpretation**

Shows how much revenue is being offset by returns and shrink.

---

# Margin-Risk Metrics

## Margin-at-risk

**Definition**

Combined value of margin pressure from markdowns, refunds, and shrink.

**Formula**

```text
margin_at_risk = markdown_loss + refund_amount + shrink_value
```

**Business interpretation**

Measures the total operational value putting margin under pressure.

This is a central project metric because it combines the major controllable leakage categories.

---

## Margin risk rate

**Definition**

Margin-at-risk as a share of net sales revenue.

**Formula**

```text
margin_risk_rate = margin_at_risk / net_sales_revenue
```

**Business interpretation**

Measures how much of the revenue base is exposed to markdown, return, and shrink pressure.

A higher margin risk rate indicates weaker margin resilience.

---

## High margin-risk flag

**Definition**

A binary flag identifying store-category combinations with unusually high margin risk.

**Formula**

```text
high_margin_risk_flag = 1 if margin_risk_rate >= threshold else 0
```

**Threshold approach**

The project uses distribution-based thresholds from the synthetic dataset.

Common reference points:

```text
P50 = median margin risk rate
P75 = high-risk threshold
P90 = critical-risk reference threshold
```

**Business interpretation**

This flag is used to identify store-category combinations that require further review.

---

## Next-year high margin-risk target

**Definition**

The machine learning target variable indicating whether a store-category becomes high margin-risk in the following fiscal year.

**Formula**

```text
high_margin_risk_next_year = 1 if next_year_margin_risk_rate >= P75 threshold else 0
```

**Business interpretation**

This target supports early-warning risk modeling.

The model asks:

```text
Given current-year operating signals, is this store-category likely to become high margin-risk next year?
```

---

# Inventory Health Metrics

## Ending inventory units

**Definition**

Inventory units available at the end of a weekly snapshot period.

**Formula**

```text
ending_inventory_units = beginning_inventory_units + received_units + returned_units - sold_units - shrink_units
```

**Business interpretation**

Measures remaining inventory position after sales, replenishment, returns, and shrink.

---

## Ending inventory value

**Definition**

Estimated value of ending inventory.

**Formula**

```text
ending_inventory_value = ending_inventory_units × unit_cost
```

**Business interpretation**

Measures capital tied up in inventory.

High ending inventory value can indicate overstock risk, especially when sell-through is weak.

---

## Average inventory value

**Definition**

Average weekly ending inventory value across the selected period.

**Formula**

```text
average_inventory_value = average(ending_inventory_value)
```

**Business interpretation**

Used to understand how much inventory value is held over time.

---

## Stockout flag

**Definition**

Indicates whether a store-product-week has insufficient or zero available inventory.

**Formula**

```text
stockout_flag = 1 if ending_inventory_units <= stockout_threshold else 0
```

**Business interpretation**

Identifies missed sales risk due to product unavailability.

---

## Stockout rate

**Definition**

Share of inventory snapshots that are flagged as stockouts.

**Formula**

```text
stockout_rate = stockout_snapshots / total_inventory_snapshots
```

**Business interpretation**

Measures availability risk.

High stockout rate can reduce sales opportunity and damage customer experience.

---

## Overstock flag

**Definition**

Indicates whether a store-product-week has excess inventory relative to expected demand.

**Formula**

```text
overstock_flag = 1 if ending_inventory_units >= overstock_threshold else 0
```

**Business interpretation**

Identifies inventory positions that may create markdown or holding-cost pressure.

---

## Overstock rate

**Definition**

Share of inventory snapshots that are flagged as overstock.

**Formula**

```text
overstock_rate = overstock_snapshots / total_inventory_snapshots
```

**Business interpretation**

Measures excess inventory exposure.

High overstock rate may signal demand mismatch, poor replenishment planning, or slow-moving product.

---

## Weeks of supply

**Definition**

Estimated number of weeks current inventory can support expected demand.

**Formula**

```text
weeks_of_supply = ending_inventory_units / average_weekly_units_sold
```

**Business interpretation**

Measures inventory coverage.

Very low weeks of supply can indicate stockout risk.

Very high weeks of supply can indicate overstock or markdown risk.

---

## Inventory sell-through rate

**Definition**

Share of available inventory that sells during the period.

**Formula**

```text
inventory_sell_through_rate = units_sold / (units_sold + ending_inventory_units)
```

**Business interpretation**

Measures how effectively inventory converts into sales.

Low sell-through may indicate weak demand, poor assortment, or overstock exposure.

---

# Supplier and Purchase Order Metrics

## Ordered units

**Definition**

Total units requested from suppliers through purchase orders.

**Formula**

```text
ordered_units = sum(purchase_order_units)
```

**Business interpretation**

Measures replenishment demand placed on suppliers.

---

## Delivered units

**Definition**

Total units delivered through shipments.

**Formula**

```text
delivered_units = sum(delivered_units)
```

**Business interpretation**

Measures actual received supply.

---

## Supplier fill rate

**Definition**

Delivered units as a share of ordered units.

**Formula**

```text
supplier_fill_rate = delivered_units / ordered_units
```

**Business interpretation**

Measures supplier reliability in fulfilling ordered quantities.

A low fill rate can contribute to stockout risk.

---

## Short shipment rate

**Definition**

Share of shipments where delivered quantity is less than ordered or shipped quantity.

**Formula**

```text
short_shipment_rate = short_shipments / total_shipments
```

**Business interpretation**

Measures supplier or logistics under-delivery risk.

---

## Supplier delay rate

**Definition**

Share of supplier shipments delivered later than expected.

**Formula**

```text
supplier_delay_rate = delayed_supplier_shipments / total_supplier_shipments
```

**Business interpretation**

Measures supplier timeliness.

High supplier delay rate can increase stockout risk and reduce fulfillment reliability.

---

## Supplier average lead time days

**Definition**

Average number of days between purchase order creation and supplier delivery.

**Formula**

```text
supplier_avg_lead_time_days = average(delivery_date - purchase_order_date)
```

**Business interpretation**

Measures how long replenishment takes.

Long lead times reduce flexibility and can increase inventory planning risk.

---

# Fulfillment Metrics

## Fulfillment shipment count

**Definition**

Number of fulfillment or shipment records in the selected period.

**Formula**

```text
fulfillment_shipment_count = count(shipments)
```

**Business interpretation**

Measures fulfillment activity volume.

---

## Fulfillment delay rate

**Definition**

Share of fulfillment shipments that are delayed.

**Formula**

```text
fulfillment_delay_rate = delayed_fulfillment_shipments / total_fulfillment_shipments
```

**Business interpretation**

Measures customer-facing fulfillment reliability.

High fulfillment delay rate can contribute to returns, dissatisfaction, and margin pressure.

---

## Fulfillment average lead time days

**Definition**

Average number of days required to complete fulfillment.

**Formula**

```text
fulfillment_avg_lead_time_days = average(delivery_date - shipment_date)
```

**Business interpretation**

Measures operational speed.

Long fulfillment lead time can indicate logistics pressure or service reliability issues.

---

# Store-Category Profitability Metrics

## Store-category net sales

**Definition**

Net sales revenue aggregated at the store-category-year level.

**Formula**

```text
store_category_net_sales = sum(net_sales_revenue)
```

**Business interpretation**

Measures business volume for each store-category combination.

---

## Store-category gross margin

**Definition**

Gross margin amount aggregated at the store-category-year level.

**Formula**

```text
store_category_gross_margin = sum(gross_margin_amount)
```

**Business interpretation**

Measures absolute profit contribution from a store-category.

---

## Store-category gross margin rate

**Definition**

Gross margin rate at the store-category-year level.

**Formula**

```text
store_category_gross_margin_rate = store_category_gross_margin / store_category_net_sales
```

**Business interpretation**

Measures profitability efficiency for a store-category combination.

---

## Store-category margin risk rate

**Definition**

Margin-at-risk divided by net sales revenue at the store-category-year level.

**Formula**

```text
store_category_margin_risk_rate = store_category_margin_at_risk / store_category_net_sales
```

**Business interpretation**

Measures store-category margin resilience.

This is one of the most important metrics in the project.

---

# Risk Ranking and Priority Metrics

## Revenue exposed

**Definition**

Net sales revenue associated with store-category combinations flagged as high risk.

**Formula**

```text
revenue_exposed = sum(net_sales_revenue where predicted_high_risk_flag = 1)
```

**Business interpretation**

Measures how much business volume is tied to high-risk predictions.

---

## Critical count

**Definition**

Number of store-category combinations classified in the critical risk band.

**Formula**

```text
critical_count = count(store_category where predicted_risk_band = "Critical")
```

**Business interpretation**

Measures the volume of cases requiring urgent review.

---

## Priority logic

**Definition**

A practical ranking logic that combines risk intensity with business scale.

**Formula concept**

```text
priority_score = risk_rate × business_volume_or_value
```

Examples:

```text
margin_risk_rate × net_sales_revenue
predicted_risk_probability × net_sales_revenue
stockout_rate × net_sales_revenue
overstock_rate × average_inventory_value
```

**Business interpretation**

This prevents the analysis from focusing only on high percentages from small-volume cases.

A high-priority case should usually have both:

* meaningful risk rate,
* meaningful business value exposure.

---

# Machine Learning Metrics

## Predicted risk probability

**Definition**

The model-estimated probability that a store-category will become high margin-risk in the next fiscal year.

**Formula**

```text
predicted_risk_probability = model.predict_proba(features)
```

**Business interpretation**

Shows the model's estimated likelihood of next-year high margin-risk.

---

## Model decision threshold

**Definition**

Probability cutoff used to classify a case as predicted high risk.

**Project value**

```text
decision_threshold = 39.3%
```

**Formula**

```text
predicted_high_risk_flag = 1 if predicted_risk_probability >= decision_threshold else 0
```

**Business interpretation**

The decision threshold is chosen for early-warning usefulness.

It is not the same as the P75 margin-risk threshold used to define the training target.

---

## Predicted risk band

**Definition**

A readable risk category assigned from predicted risk probability.

**Band logic**

```text
Critical = probability >= critical threshold
High Risk = probability >= decision threshold
Watch = probability >= watch threshold
Low = probability below watch threshold
```

**Business interpretation**

Risk bands make model output easier to interpret in dashboards and the simulator.

---

## Precision

**Definition**

Of all cases predicted as high risk, the share that actually became high risk.

**Formula**

```text
precision = true_positives / (true_positives + false_positives)
```

**Project value**

```text
precision = 57.8%
```

**Business interpretation**

Measures how reliable high-risk predictions are.

---

## Recall

**Definition**

Of all actual high-risk cases, the share the model successfully identified.

**Formula**

```text
recall = true_positives / (true_positives + false_negatives)
```

**Project value**

```text
recall = 94.9%
```

**Business interpretation**

Measures how well the model catches future high-risk cases.

This project prioritizes recall because missing a high-risk store-category can be costly.

---

## F1 score

**Definition**

Harmonic mean of precision and recall.

**Formula**

```text
f1_score = 2 × (precision × recall) / (precision + recall)
```

**Project value**

```text
f1_score = 0.718
```

**Business interpretation**

Measures balance between precision and recall.

---

## ROC-AUC

**Definition**

Measures the model's ability to rank high-risk cases above lower-risk cases across thresholds.

**Project value**

```text
roc_auc = 0.946
```

**Business interpretation**

A higher ROC-AUC indicates strong ranking ability.

---

# Scenario Simulator Metrics

## Original risk probability

**Definition**

Predicted risk probability before any scenario changes.

**Business interpretation**

Represents the model's baseline risk estimate for the selected store-category.

---

## Simulated risk probability

**Definition**

Predicted risk probability after scenario levers are changed.

**Business interpretation**

Represents the model's risk estimate after applying a hypothetical operational intervention.

---

## Risk probability change

**Definition**

Difference between simulated and original risk probability.

**Formula**

```text
risk_probability_change = simulated_risk_probability - original_risk_probability
```

**Business interpretation**

Shows whether the scenario improves or worsens predicted margin-risk.

Negative values indicate risk reduction.

Positive values indicate risk escalation.

---

## Scenario type

**Definition**

Readable classification of the scenario result.

Possible values include:

* Risk reduction scenario
* Risk escalation scenario
* Stress scenario
* Band movement scenario
* Stable scenario

**Business interpretation**

Helps users quickly understand whether the simulated intervention meaningfully changes predicted risk.

---

## Changed levers

**Definition**

List of model input features that were changed in the scenario.

Examples:

* inventory stockout rate,
* inventory overstock rate,
* average weeks of supply,
* refund value rate,
* shrink value rate,
* markdown loss rate,
* supplier lead time,
* fulfillment lead time.

**Business interpretation**

Shows which operational assumptions were changed to produce the simulated result.

---

## Impact score

**Definition**

A model explanation value showing the direction and relative strength of a feature's contribution to the selected prediction.

**Business interpretation**

Helps users understand which drivers are pushing risk higher or lower.

Impact scores should be interpreted directionally, not as direct dollar impact.

---

# Important Interpretation Notes

## Distribution-based thresholds

Risk thresholds in this project are derived from the synthetic dataset distribution.

They should not be interpreted as universal retail benchmarks.

## Synthetic data limitation

All operational data is synthetic.

Metrics are designed to be realistic for portfolio demonstration, but they do not represent Target's actual internal operations.

## Sensitivity analysis limitation

The Streamlit simulator changes model input features and recalculates predicted risk.

It does not prove causality.

A reduction in simulated risk should be interpreted as a signal for further business investigation, not as guaranteed financial improvement.

## Business judgment requirement

The metrics and model outputs are designed to support decision-making.

They should be reviewed alongside operational context, category strategy, store conditions, and business judgment.
