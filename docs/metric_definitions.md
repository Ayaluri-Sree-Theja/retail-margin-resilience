# Metric Definitions

## 1. Gross Revenue

Total sales revenue before returns, markdown impact, and shrink adjustments.

Formula:

gross_revenue = quantity_sold * unit_price

## 2. Net Sales Revenue

Sales revenue after discounts.

Formula:

net_sales_revenue = quantity_sold * final_sale_price

## 3. Gross Margin

Revenue remaining after product cost.

Formula:

gross_margin = net_sales_revenue - cost_of_goods_sold

## 4. Gross Margin Rate

Gross margin as a percentage of net sales revenue.

Formula:

gross_margin_rate = gross_margin / net_sales_revenue

## 5. Return-Adjusted Revenue

Revenue after removing refunded value from returned items.

Formula:

return_adjusted_revenue = net_sales_revenue - refund_amount

## 6. Return-Adjusted Margin

Margin after accounting for refunded sales.

Formula:

return_adjusted_margin = gross_margin - estimated_return_loss

## 7. Shrink Value

Estimated value of inventory lost due to theft, damage, miscounts, or unexplained inventory mismatch.

Formula:

shrink_value = shrink_units * unit_cost

## 8. Shrink Rate

Shrink units as a percentage of available inventory.

Formula:

shrink_rate = shrink_units / beginning_inventory_units

## 9. Shrink-Adjusted Margin

Gross margin after subtracting shrink value.

Formula:

shrink_adjusted_margin = gross_margin - shrink_value

## 10. Markdown Loss

Revenue lost due to selling products below original planned price.

Formula:

markdown_loss = original_price - final_sale_price

## 11. Markdown Exposure

Potential margin risk from excess inventory likely to require discounting.

Formula:

markdown_exposure = overstock_units * expected_markdown_amount_per_unit

## 12. Inventory Turnover

How efficiently inventory is sold and replaced.

Formula:

inventory_turnover = cost_of_goods_sold / average_inventory_value

## 13. Weeks of Supply

How many weeks current inventory can support expected demand.

Formula:

weeks_of_supply = current_inventory_units / forecasted_weekly_demand

## 14. Stockout Rate

Percentage of store-SKU-days where inventory was unavailable while demand existed.

Formula:

stockout_rate = stockout_days / total_active_selling_days

## 15. Overstock Units

Inventory units above expected demand and safety stock needs.

Formula:

overstock_units = current_inventory_units - expected_demand_units - safety_stock_units

## 16. Sell-Through Rate

Percentage of available inventory sold during a period.

Formula:

sell_through_rate = units_sold / beginning_inventory_units

## 17. Return Rate

Percentage of sold units that were returned.

Formula:

return_rate = returned_units / units_sold

## 18. Fulfillment Delay Rate

Percentage of shipments delivered later than expected.

Formula:

fulfillment_delay_rate = delayed_shipments / total_shipments

## 19. On-Time Delivery Rate

Percentage of shipments delivered on or before expected delivery date.

Formula:

on_time_delivery_rate = on_time_shipments / total_shipments

## 20. Supplier Lead Time

Number of days between purchase order date and delivery date.

Formula:

supplier_lead_time_days = delivered_date - purchase_order_date

## 21. Lead Time Variance

Variation between actual lead time and expected lead time.

Formula:

lead_time_variance = actual_lead_time_days - expected_lead_time_days

## 22. Margin-at-Risk

Estimated margin exposed to operational issues such as stockouts, overstock, returns, shrink, and delays.

Formula:

margin_at_risk = markdown_exposure + shrink_value + estimated_return_loss + estimated_stockout_margin_loss