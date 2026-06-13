# Filing Assumption Matrix

## Purpose

This document connects Target Corporation's public annual report disclosures to the assumptions used in the Retail Margin Resilience Analytics project.

The goal is not to recreate Target's internal data. The goal is to use public filing evidence to design a realistic simulated retail dataset and analytics system.

## Source Documents

- Target Corporation 2025 Annual Report / Form 10-K
- Target Corporation 2024 Annual Report / Form 10-K
- Target Corporation 2023 Annual Report / Form 10-K

## Data Disclaimer

This project does not use Target internal operational data.

All store-SKU sales, inventory, returns, shrink, supplier, shipment, promotion, forecast, and risk-score data are simulated.

Target's public filings are used only to inform:

- business context
- risk themes
- synthetic data assumptions
- KPI design
- dashboard narrative
- AI/RAG source grounding

---

## Assumption Matrix

| Filing Theme | Filing-Informed Evidence | Business Interpretation | Synthetic Data Rule | Affected Tables | Affected KPIs | Dashboard Page |
|---|---|---|---|---|---|---|
| Gross margin pressure | Target reported gross margin rate movement across 2023, 2024, and 2025. | Margin performance changes over time and can be affected by merchandise mix, markdowns, shrink, and fulfillment costs. | Generate product categories with different margin rates. Add margin pressure through promotions, markdowns, returns, shrink, and supplier delays. | fact_sales, fact_return, fact_shrink_event, fact_inventory_snapshot | gross_margin, gross_margin_rate, return_adjusted_margin, shrink_adjusted_margin, margin_at_risk | Executive Overview |
| Demand volatility | Target discusses variability in operating results and changes in consumer demand across recent years. | Retail demand should vary by season, category, channel, and macro-like pressure. | Add demand seasonality, category demand cycles, holiday spikes, back-to-school spikes, and weaker discretionary demand periods. | fact_sales, fact_inventory_snapshot, ml_demand_forecast | forecasted_units, forecast_error, demand_volatility_score, stockout_rate | Inventory Resilience, ML Risk Intelligence |
| Strong in-stocks | Target's 2025 CEO letter emphasizes sharp pricing, strong in-stocks, and fast fulfillment. | Product availability is a core guest experience and profitability driver. | Generate stockout flags when demand exceeds inventory and replenishment is delayed. | fact_inventory_snapshot, fact_sales, fact_purchase_order, fact_shipment | stockout_rate, weeks_of_supply, order_fill_rate, estimated_stockout_margin_loss | Inventory Resilience |
| Fast fulfillment | Target emphasizes fast fulfillment and end-to-end reliability. | Fulfillment speed and reliability affect availability, customer experience, and cost pressure. | Generate supplier lead times, delayed shipments, delivery dates, and delay days. | fact_purchase_order, fact_shipment, dim_supplier | on_time_delivery_rate, fulfillment_delay_rate, average_lead_time, lead_time_variance | Fulfillment & Supplier Reliability |
| Inventory shrink | Target reports that inventory is reduced for estimated losses related to shrink and markdowns. | Shrink is a measurable profit leakage factor. | Generate shrink events with higher probability for small, high-value, high-risk SKUs and selected store risk profiles. | fact_shrink_event, fact_inventory_snapshot, dim_product, dim_store | shrink_units, shrink_value, shrink_rate, shrink_adjusted_margin | Returns & Shrink Leakage |
| Markdowns | Target discusses markdowns as part of inventory and gross margin management. | Overstock and weak sell-through can lead to markdown exposure. | Generate promotions and markdown-like discounts when products have high inventory and low sell-through. | fact_sales, dim_promotion, fact_inventory_snapshot | markdown_loss, markdown_exposure, sell_through_rate, overstock_units | Inventory Resilience |
| Category mix | Target reports merchandise sales across categories and notes that gross margins vary by merchandise type. | Category mix affects revenue and margin performance. | Use Target-like categories and assign category-specific price, cost, return risk, shrink risk, and margin assumptions. | dim_product, fact_sales, fact_return, fact_shrink_event | category_margin_rate, category_return_rate, category_shrink_rate | Executive Overview, Store Category Profitability |
| Holiday seasonality | Target states that a larger share of annual sales occurs in Q4 because of November and December holiday sales. | Retail demand should spike in holiday periods. | Add higher demand multipliers in November and December, with category-specific holiday effects. | dim_calendar, fact_sales, fact_inventory_snapshot | monthly_sales, holiday_sales_mix, forecast_error | Executive Overview, ML Risk Intelligence |
| Store footprint | Target reports store counts and retail square footage across years. | Store format and size should influence demand, inventory, and fulfillment behavior. | Simulate stores with different formats, square footage, regions, risk profiles, and fulfillment flags. | dim_store, fact_sales, fact_inventory_snapshot, fact_shipment | sales_per_store, sales_per_sqft_proxy, fulfillment_delay_rate | Executive Overview |
| Supply chain scale | Target reports supply chain facilities and ongoing investment in supply chain and operations. | Supply chain reliability is part of margin resilience. | Generate suppliers with reliability scores, lead times, delay risk levels, and shipment performance. | dim_supplier, fact_purchase_order, fact_shipment | supplier_reliability_score, delay_rate, lead_time_variance | Fulfillment & Supplier Reliability |
| Digital / omnichannel growth | Target discusses digital channels, same-day services, and stores supporting fulfillment. | Channel mix affects fulfillment, returns, and inventory behavior. | Generate store, online, drive-up, and same-day delivery sales channels with different return and delay patterns. | fact_sales, fact_return, fact_shipment | channel_sales_mix, channel_return_rate, fulfillment_delay_rate | Executive Overview, Returns & Shrink Leakage |
| Returns leakage | Retail returns reduce realized revenue and margin even when gross sales look healthy. | Return behavior should vary by category and channel. | Generate higher returns for apparel, home, and online channels; lower returns for grocery and essentials. | fact_return, fact_sales, dim_product | return_rate, return_value, return_adjusted_revenue, return_adjusted_margin | Returns & Shrink Leakage |
| 2023 53-week year | Target notes that 2023 had 53 weeks while 2024 and 2025 had 52 weeks. | The calendar model must handle fiscal year differences. | Generate FY2023 with 53 weeks and FY2024/FY2025 with 52 weeks. | dim_calendar, fact_sales, fact_inventory_snapshot, ml_demand_forecast | fiscal_year_sales, weekly_sales_trend, forecast_baseline | Executive Overview |