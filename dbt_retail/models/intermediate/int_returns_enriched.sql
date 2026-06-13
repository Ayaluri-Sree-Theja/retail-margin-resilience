with returns as (

    select *
    from {{ ref('stg_returns') }}

),

sales as (

    select
        sales_id,
        transaction_id,
        gross_revenue,
        net_sales_revenue,
        gross_margin,
        quantity_sold
    from {{ ref('stg_sales') }}

),

calendar as (

    select *
    from {{ ref('stg_calendar') }}

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
        r.return_id,
        r.sales_id,
        s.transaction_id,
        r.date_id,
        c.calendar_date as return_date,
        c.fiscal_year,
        c.fiscal_quarter,
        c.fiscal_week,

        r.store_id,
        st.region,
        st.state,
        st.city,
        st.store_format,
        st.risk_profile as store_risk_profile,

        r.product_id,
        p.category,
        p.subcategory,
        p.brand_type,
        p.price_band,
        p.return_risk_level,

        r.channel,
        r.return_reason,
        r.return_condition,
        r.return_loss_flag,
        r.returned_units,
        r.refund_amount,

        s.quantity_sold as original_quantity_sold,
        s.net_sales_revenue as original_net_sales_revenue,
        s.gross_margin as original_gross_margin,

        case
            when s.net_sales_revenue = 0 then null
            else r.refund_amount / s.net_sales_revenue
        end as refund_to_sale_ratio

    from returns r

    left join sales s
        on r.sales_id = s.sales_id

    left join calendar c
        on r.date_id = c.date_id

    left join stores st
        on r.store_id = st.store_id

    left join products p
        on r.product_id = p.product_id

)

select *
from final