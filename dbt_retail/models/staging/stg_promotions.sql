with source as (

    select *
    from {{ source('raw', 'dim_promotion') }}

),

renamed as (

    select
        promotion_id,
        promotion_name,
        promotion_type,
        discount_pct,
        start_date::date as start_date,
        end_date::date as end_date,
        category,
        channel,

        end_date::date - start_date::date + 1 as promotion_duration_days,

        case
            when discount_pct >= 0.30 then 'Deep Discount'
            when discount_pct >= 0.15 then 'Moderate Discount'
            when discount_pct > 0 then 'Light Discount'
            else 'No Discount'
        end as discount_band

    from source

)

select *
from renamed