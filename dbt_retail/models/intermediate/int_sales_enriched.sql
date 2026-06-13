with sales as (

    select *
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

promotions as (

    select *
    from {{ ref('stg_promotions') }}

),

final as (

    select
        s.sales_id,
        s.transaction_id,
        s.date_id,
        c.calendar_date,
        c.fiscal_year,
        c.fiscal_quarter,
        c.fiscal_week,
        c.calendar_month,
        c.month_name,
        c.is_weekend,
        c.is_holiday_season,

        s.store_id,
        st.store_name,
        st.region,
        st.state,
        st.city,
        st.store_format,
        st.store_size_band,
        st.risk_profile as store_risk_profile,
        st.fulfillment_enabled,

        s.product_id,
        p.sku,
        p.product_name,
        p.category,
        p.subcategory,
        p.brand_type,
        p.price_band,
        p.return_risk_level,
        p.shrink_risk_level,

        s.promotion_id,
        promo.promotion_name,
        promo.promotion_type,
        promo.discount_band,

        s.channel,
        s.quantity_sold,
        s.unit_price,
        s.unit_cost,
        s.discount_pct,
        s.final_sale_price,
        s.gross_revenue,
        s.net_sales_revenue,
        s.gross_margin,
        s.gross_margin_rate,
        s.markdown_amount_per_unit,
        s.markdown_loss

    from sales s

    left join calendar c
        on s.date_id = c.date_id

    left join stores st
        on s.store_id = st.store_id

    left join products p
        on s.product_id = p.product_id

    left join promotions promo
        on s.promotion_id = promo.promotion_id

)

select *
from final