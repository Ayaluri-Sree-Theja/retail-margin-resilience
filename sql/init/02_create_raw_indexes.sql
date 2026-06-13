CREATE INDEX IF NOT EXISTS idx_fact_sales_date
ON raw.fact_sales(date_id);

CREATE INDEX IF NOT EXISTS idx_fact_sales_store_product
ON raw.fact_sales(store_id, product_id);

CREATE INDEX IF NOT EXISTS idx_inventory_date_store_product
ON raw.fact_inventory_snapshot(date_id, store_id, product_id);

CREATE INDEX IF NOT EXISTS idx_returns_date_store_product
ON raw.fact_return(date_id, store_id, product_id);

CREATE INDEX IF NOT EXISTS idx_shrink_date_store_product
ON raw.fact_shrink_event(date_id, store_id, product_id);

CREATE INDEX IF NOT EXISTS idx_shipment_supplier_store
ON raw.fact_shipment(supplier_id, store_id);

CREATE INDEX IF NOT EXISTS idx_purchase_order_supplier_store
ON raw.fact_purchase_order(supplier_id, store_id);