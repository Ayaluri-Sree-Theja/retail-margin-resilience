with source as (

    select *
    from {{ source('raw', 'dim_product') }}

),

renamed as (

    select
        product_id,
        sku,
        product_name,
        category,
        subcategory,
        brand_type,
        unit_price,
        unit_cost,
        margin_rate,
        return_risk_level,
        shrink_risk_level,

        unit_price - unit_cost as unit_margin,

        case
            when unit_price >= 100 then 'High Price'
            when unit_price >= 25 then 'Mid Price'
            else 'Low Price'
        end as price_band

    from source

)

select *
from renamed