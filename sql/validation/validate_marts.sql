-- ============================================================
-- Retail Margin Resilience Analytics
-- Phase 5A: Mart Validation Queries
-- ============================================================


-- ------------------------------------------------------------
-- 1. Confirm mart row counts
-- ------------------------------------------------------------

SELECT 'mart_executive_margin_resilience' AS table_name, COUNT(*) AS row_count
FROM marts.mart_executive_margin_resilience
UNION ALL
SELECT 'mart_inventory_health', COUNT(*)
FROM marts.mart_inventory_health
UNION ALL
SELECT 'mart_return_shrink_leakage', COUNT(*)
FROM marts.mart_return_shrink_leakage
UNION ALL
SELECT 'mart_fulfillment_reliability', COUNT(*)
FROM marts.mart_fulfillment_reliability
UNION ALL
SELECT 'mart_store_category_profitability', COUNT(*)
FROM marts.mart_store_category_profitability
UNION ALL
SELECT 'mart_supplier_performance', COUNT(*)
FROM marts.mart_supplier_performance
ORDER BY table_name;


-- Expected approximate output:
-- mart_executive_margin_resilience     12
-- mart_fulfillment_reliability         6993
-- mart_inventory_health                11304
-- mart_return_shrink_leakage           72
-- mart_store_category_profitability    1080
-- mart_supplier_performance            2544


-- ------------------------------------------------------------
-- 2. Executive quarterly KPI validation
-- ------------------------------------------------------------

SELECT
    fiscal_year,
    fiscal_quarter,
    total_transactions,
    units_sold,
    ROUND(net_sales_revenue, 2) AS net_sales_revenue,
    ROUND(gross_margin, 2) AS gross_margin,
    ROUND(gross_margin_rate, 4) AS gross_margin_rate,
    ROUND(refund_amount, 2) AS refund_amount,
    ROUND(shrink_value, 2) AS shrink_value,
    ROUND(markdown_loss, 2) AS markdown_loss,
    ROUND(margin_at_risk, 2) AS margin_at_risk,
    ROUND(stockout_snapshot_rate, 4) AS stockout_snapshot_rate,
    ROUND(overstock_snapshot_rate, 4) AS overstock_snapshot_rate,
    ROUND(fulfillment_delay_rate, 4) AS fulfillment_delay_rate
FROM marts.mart_executive_margin_resilience
ORDER BY fiscal_year, fiscal_quarter;


-- ------------------------------------------------------------
-- 3. Reconcile sales totals: mart vs intermediate
-- ------------------------------------------------------------

WITH mart_totals AS (
    SELECT
        SUM(units_sold) AS mart_units_sold,
        ROUND(SUM(net_sales_revenue), 2) AS mart_net_sales_revenue,
        ROUND(SUM(gross_margin), 2) AS mart_gross_margin
    FROM marts.mart_executive_margin_resilience
),

intermediate_totals AS (
    SELECT
        SUM(quantity_sold) AS int_units_sold,
        ROUND(SUM(net_sales_revenue), 2) AS int_net_sales_revenue,
        ROUND(SUM(gross_margin), 2) AS int_gross_margin
    FROM intermediate.int_sales_enriched
)

SELECT
    mart_units_sold,
    int_units_sold,
    mart_units_sold - int_units_sold AS units_difference,

    mart_net_sales_revenue,
    int_net_sales_revenue,
    mart_net_sales_revenue - int_net_sales_revenue AS revenue_difference,

    mart_gross_margin,
    int_gross_margin,
    mart_gross_margin - int_gross_margin AS margin_difference
FROM mart_totals
CROSS JOIN intermediate_totals;


-- Expected:
-- units_difference = 0
-- revenue_difference = 0.00 or extremely close
-- margin_difference = 0.00 or extremely close


-- ------------------------------------------------------------
-- 4. Reconcile return totals
-- ------------------------------------------------------------

WITH mart_returns AS (
    SELECT
        SUM(returned_units) AS mart_returned_units,
        ROUND(SUM(refund_amount), 2) AS mart_refund_amount
    FROM marts.mart_return_shrink_leakage
),

intermediate_returns AS (
    SELECT
        SUM(returned_units) AS int_returned_units,
        ROUND(SUM(refund_amount), 2) AS int_refund_amount
    FROM intermediate.int_returns_enriched
)

SELECT
    mart_returned_units,
    int_returned_units,
    mart_returned_units - int_returned_units AS returned_units_difference,

    mart_refund_amount,
    int_refund_amount,
    mart_refund_amount - int_refund_amount AS refund_amount_difference
FROM mart_returns
CROSS JOIN intermediate_returns;


-- Expected:
-- returned_units_difference = 0
-- refund_amount_difference = 0.00 or extremely close


-- ------------------------------------------------------------
-- 5. Reconcile shrink totals
-- ------------------------------------------------------------

WITH mart_shrink AS (
    SELECT
        SUM(shrink_units) AS mart_shrink_units,
        ROUND(SUM(shrink_value), 2) AS mart_shrink_value
    FROM marts.mart_return_shrink_leakage
),

intermediate_shrink AS (
    SELECT
        SUM(shrink_units) AS int_shrink_units,
        ROUND(SUM(estimated_shrink_value), 2) AS int_shrink_value
    FROM intermediate.int_shrink_enriched
)

SELECT
    mart_shrink_units,
    int_shrink_units,
    mart_shrink_units - int_shrink_units AS shrink_units_difference,

    mart_shrink_value,
    int_shrink_value,
    mart_shrink_value - int_shrink_value AS shrink_value_difference
FROM mart_shrink
CROSS JOIN intermediate_shrink;


-- Expected:
-- shrink_units_difference = 0
-- shrink_value_difference = 0.00 or extremely close


-- ------------------------------------------------------------
-- 6. Validate rate fields are between 0 and 1
-- ------------------------------------------------------------

SELECT
    'mart_executive_margin_resilience' AS table_name,
    SUM(CASE WHEN gross_margin_rate < 0 OR gross_margin_rate > 1 THEN 1 ELSE 0 END) AS invalid_gross_margin_rate,
    SUM(CASE WHEN unit_return_rate < 0 OR unit_return_rate > 1 THEN 1 ELSE 0 END) AS invalid_unit_return_rate,
    SUM(CASE WHEN stockout_snapshot_rate < 0 OR stockout_snapshot_rate > 1 THEN 1 ELSE 0 END) AS invalid_stockout_rate,
    SUM(CASE WHEN overstock_snapshot_rate < 0 OR overstock_snapshot_rate > 1 THEN 1 ELSE 0 END) AS invalid_overstock_rate,
    SUM(CASE WHEN fulfillment_delay_rate < 0 OR fulfillment_delay_rate > 1 THEN 1 ELSE 0 END) AS invalid_fulfillment_delay_rate
FROM marts.mart_executive_margin_resilience;

SELECT
    'mart_inventory_health' AS table_name,
    SUM(CASE WHEN stockout_rate < 0 OR stockout_rate > 1 THEN 1 ELSE 0 END) AS invalid_stockout_rate,
    SUM(CASE WHEN overstock_rate < 0 OR overstock_rate > 1 THEN 1 ELSE 0 END) AS invalid_overstock_rate,
    SUM(CASE WHEN sell_through_rate < 0 THEN 1 ELSE 0 END) AS invalid_sell_through_rate
FROM marts.mart_inventory_health;

SELECT
    'mart_fulfillment_reliability' AS table_name,
    SUM(CASE WHEN delay_rate < 0 OR delay_rate > 1 THEN 1 ELSE 0 END) AS invalid_delay_rate,
    SUM(CASE WHEN on_time_delivery_rate < 0 OR on_time_delivery_rate > 1 THEN 1 ELSE 0 END) AS invalid_on_time_delivery_rate,
    SUM(CASE WHEN short_shipment_rate < 0 OR short_shipment_rate > 1 THEN 1 ELSE 0 END) AS invalid_short_shipment_rate
FROM marts.mart_fulfillment_reliability;

SELECT
    'mart_supplier_performance' AS table_name,
    SUM(CASE WHEN delay_rate < 0 OR delay_rate > 1 THEN 1 ELSE 0 END) AS invalid_delay_rate,
    SUM(CASE WHEN short_shipment_rate < 0 OR short_shipment_rate > 1 THEN 1 ELSE 0 END) AS invalid_short_shipment_rate
FROM marts.mart_supplier_performance;


-- Expected:
-- all invalid values = 0


-- ------------------------------------------------------------
-- 7. Executive trend check by fiscal year
-- ------------------------------------------------------------

SELECT
    fiscal_year,
    SUM(total_transactions) AS total_transactions,
    SUM(units_sold) AS units_sold,
    ROUND(SUM(net_sales_revenue), 2) AS net_sales_revenue,
    ROUND(SUM(gross_margin), 2) AS gross_margin,
    ROUND(SUM(gross_margin) / NULLIF(SUM(net_sales_revenue), 0), 4) AS gross_margin_rate,
    ROUND(SUM(refund_amount), 2) AS refund_amount,
    ROUND(SUM(shrink_value), 2) AS shrink_value,
    ROUND(SUM(markdown_loss), 2) AS markdown_loss,
    ROUND(SUM(margin_at_risk), 2) AS margin_at_risk
FROM marts.mart_executive_margin_resilience
GROUP BY fiscal_year
ORDER BY fiscal_year;


-- ------------------------------------------------------------
-- 8. Top categories by return + shrink leakage
-- ------------------------------------------------------------

SELECT
    fiscal_year,
    category,
    SUM(units_sold) AS units_sold,
    ROUND(SUM(net_sales_revenue), 2) AS net_sales_revenue,
    ROUND(SUM(refund_amount), 2) AS refund_amount,
    ROUND(SUM(shrink_value), 2) AS shrink_value,
    ROUND(SUM(return_shrink_leakage_value), 2) AS return_shrink_leakage_value,
    ROUND(SUM(return_shrink_leakage_value) / NULLIF(SUM(net_sales_revenue), 0), 4) AS leakage_rate
FROM marts.mart_return_shrink_leakage
GROUP BY fiscal_year, category
ORDER BY fiscal_year, leakage_rate DESC;


-- ------------------------------------------------------------
-- 9. Supplier risk validation
-- ------------------------------------------------------------

SELECT
    delay_risk_level,
    COUNT(*) AS supplier_category_quarter_rows,
    SUM(shipment_count) AS shipment_count,
    SUM(delayed_shipments) AS delayed_shipments,
    ROUND(SUM(delayed_shipments)::numeric / NULLIF(SUM(shipment_count), 0), 4) AS weighted_delay_rate,
    ROUND(AVG(avg_delay_days), 2) AS avg_delay_days
FROM marts.mart_supplier_performance
GROUP BY delay_risk_level
ORDER BY weighted_delay_rate DESC;


-- Expected:
-- High delay risk should have highest delay rate
-- Medium should be in the middle
-- Low should have lowest delay rate


-- ------------------------------------------------------------
-- 10. Inventory risk validation
-- ------------------------------------------------------------

SELECT
    fiscal_year,
    category,
    SUM(snapshot_count) AS snapshot_count,
    SUM(stockout_snapshots) AS stockout_snapshots,
    ROUND(SUM(stockout_snapshots)::numeric / NULLIF(SUM(snapshot_count), 0), 4) AS stockout_rate,
    SUM(overstock_snapshots) AS overstock_snapshots,
    ROUND(SUM(overstock_snapshots)::numeric / NULLIF(SUM(snapshot_count), 0), 4) AS overstock_rate,
    SUM(sold_units) AS sold_units,
    SUM(ending_inventory_units) AS ending_inventory_units
FROM marts.mart_inventory_health
GROUP BY fiscal_year, category
ORDER BY fiscal_year, overstock_rate DESC;  