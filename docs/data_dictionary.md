# Data Dictionary Draft

## Dimensions
- dim_store: one row per store
- dim_product: one row per SKU
- dim_supplier: one row per supplier
- dim_calendar: one row per calendar date
- dim_promotion: one row per promotion

## Facts
- fact_sales: one row per transaction line
- fact_inventory_snapshot: one row per store-SKU-date
- fact_purchase_order: one row per purchase order line
- fact_shipment: one row per shipment line
- fact_return: one row per return line
- fact_shrink_event: one row per store-SKU-date-event

## ML outputs
- forecast_outputs: one row per store-SKU-week forecast
- risk_scores: one row per store-SKU-week-risk type
