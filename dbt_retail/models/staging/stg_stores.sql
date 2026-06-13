with source as (

    select *
    from {{ source('raw', 'dim_store') }}

),

renamed as (

    select
        store_id,
        store_name,
        region,
        state,
        city,
        store_format,
        store_size_sqft,
        opened_date::date as opened_date,
        risk_profile,
        fulfillment_enabled,

        case
            when store_size_sqft >= 170000 then 'Large'
            when store_size_sqft >= 90000 then 'Standard'
            else 'Small'
        end as store_size_band

    from source

)

select *
from renamed