with shipments as (

    select *
    from {{ ref('stg_shipments') }}

),

purchase_orders as (

    select *
    from {{ ref('stg_purchase_orders') }}

),

suppliers as (

    select *
    from {{ ref('stg_suppliers') }}

),

stores as (

    select *
    from {{ ref('stg_stores') }}

),

products as (

    select *
    from {{ ref('stg_products') }}

),

final as (

    select
        sh.shipment_id,
        sh.purchase_order_id,
        po.po_line_id,

        sh.supplier_id,
        sup.supplier_name,
        sup.supplier_region,
        sup.average_lead_time_days,
        sup.reliability_score,
        sup.delay_risk_level,
        sup.supplier_reliability_band,

        sh.store_id,
        st.region,
        st.state,
        st.city,
        st.store_format,
        st.fulfillment_enabled,

        sh.product_id,
        p.category,
        p.subcategory,
        p.brand_type,
        p.price_band,

        po.order_date,
        po.expected_delivery_date as po_expected_delivery_date,
        sh.shipped_date,
        sh.expected_delivery_date,
        sh.delivered_date,

        po.ordered_units,
        sh.shipped_units,
        sh.delivered_units,
        sh.short_shipped_units,
        sh.short_shipment_flag,

        po.ordered_cost,
        sh.delayed_flag,
        sh.delay_days,
        sh.actual_transit_days,

        sh.delivered_date - po.order_date as actual_lead_time_days,

        case
            when sh.delayed_flag = true then 'Delayed'
            when sh.short_shipment_flag = true then 'Short Shipped'
            else 'On Time / Complete'
        end as fulfillment_status

    from shipments sh

    left join purchase_orders po
        on sh.purchase_order_id = po.purchase_order_id

    left join suppliers sup
        on sh.supplier_id = sup.supplier_id

    left join stores st
        on sh.store_id = st.store_id

    left join products p
        on sh.product_id = p.product_id

)

select *
from final