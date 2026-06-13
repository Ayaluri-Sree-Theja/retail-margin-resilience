with source as (

    select *
    from {{ source('raw', 'fact_shipment') }}

),

renamed as (

    select
        shipment_id,
        purchase_order_id,
        supplier_id,
        product_id,
        store_id,
        shipped_date::date as shipped_date,
        expected_delivery_date::date as expected_delivery_date,
        delivered_date::date as delivered_date,
        shipped_units,
        delivered_units,
        delayed_flag,
        delay_days,

        delivered_date::date - shipped_date::date as actual_transit_days,

        shipped_units - delivered_units as short_shipped_units,

        case
            when delivered_units < shipped_units then true
            else false
        end as short_shipment_flag

    from source

)

select *
from renamed