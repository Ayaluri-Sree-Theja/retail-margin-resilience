with source as (

    select *
    from {{ source('raw', 'fact_shrink_event') }}

),

renamed as (

    select
        shrink_event_id,
        date_id,
        store_id,
        product_id,
        shrink_reason,
        shrink_units,
        estimated_shrink_value,
        investigation_flag,

        case
            when shrink_reason in ('Theft', 'Organized Retail Crime') then true
            else false
        end as theft_related_flag

    from source

)

select *
from renamed