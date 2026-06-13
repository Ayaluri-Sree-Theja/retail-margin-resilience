with shrink as (

    select *
    from {{ ref('stg_shrink_events') }}

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
        sh.shrink_event_id,
        sh.date_id,
        c.calendar_date,
        c.fiscal_year,
        c.fiscal_quarter,
        c.fiscal_week,
        c.is_holiday_season,

        sh.store_id,
        st.region,
        st.state,
        st.city,
        st.store_format,
        st.risk_profile as store_risk_profile,

        sh.product_id,
        p.category,
        p.subcategory,
        p.brand_type,
        p.price_band,
        p.shrink_risk_level,

        sh.shrink_reason,
        sh.theft_related_flag,
        sh.shrink_units,
        sh.estimated_shrink_value,
        sh.investigation_flag,

        case
            when sh.estimated_shrink_value >= 250 then 'High Value Event'
            when sh.estimated_shrink_value >= 100 then 'Medium Value Event'
            else 'Low Value Event'
        end as shrink_value_band

    from shrink sh

    left join calendar c
        on sh.date_id = c.date_id

    left join stores st
        on sh.store_id = st.store_id

    left join products p
        on sh.product_id = p.product_id

)

select *
from final