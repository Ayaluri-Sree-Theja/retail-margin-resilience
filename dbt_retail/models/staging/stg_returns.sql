with source as (

    select *
    from {{ source('raw', 'fact_return') }}

),

renamed as (

    select
        return_id,
        sales_id,
        date_id,
        store_id,
        product_id,
        channel,
        return_reason,
        returned_units,
        refund_amount,
        return_condition,

        case
            when return_condition in ('Damaged', 'Unsellable') then true
            else false
        end as return_loss_flag

    from source

)

select *
from renamed