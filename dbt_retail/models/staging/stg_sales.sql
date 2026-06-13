with source as (

    select *
    from {{ source('raw', 'fact_sales') }}

),

renamed as (

    select
        sales_id,
        transaction_id,
        date_id,
        store_id,
        product_id,
        promotion_id,
        channel,
        quantity_sold,
        unit_price,
        discount_pct,
        final_sale_price,
        gross_revenue,
        net_sales_revenue,
        unit_cost,
        gross_margin,

        case
            when net_sales_revenue = 0 then null
            else gross_margin / net_sales_revenue
        end as gross_margin_rate,

        unit_price - final_sale_price as markdown_amount_per_unit,

        quantity_sold * (unit_price - final_sale_price) as markdown_loss

    from source

)

select *
from renamed