with source as (

    select *
    from {{ source('raw', 'fact_inventory_snapshot') }}

),

renamed as (

    select
        inventory_snapshot_id,
        date_id,
        store_id,
        product_id,
        beginning_inventory_units,
        ending_inventory_units,
        received_units,
        sold_units,
        returned_units,
        shrink_units,
        stockout_flag,
        overstock_flag,
        inventory_value,

        beginning_inventory_units + received_units + returned_units as available_inventory_units,

        case
            when beginning_inventory_units = 0 then null
            else sold_units::numeric / beginning_inventory_units
        end as sell_through_rate,

        case
            when sold_units > 0 and ending_inventory_units = 0 then true
            else false
        end as hard_stockout_flag

    from source

)

select *
from renamed