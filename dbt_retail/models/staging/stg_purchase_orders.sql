with source as (

    select *
    from {{ source('raw', 'fact_purchase_order') }}

),

renamed as (

    select
        purchase_order_id,
        po_line_id,
        supplier_id,
        product_id,
        store_id,
        order_date::date as order_date,
        expected_delivery_date::date as expected_delivery_date,
        ordered_units,
        unit_cost,
        order_status,

        expected_delivery_date::date - order_date::date as expected_lead_time_days,

        ordered_units * unit_cost as ordered_cost

    from source

)

select *
from renamed