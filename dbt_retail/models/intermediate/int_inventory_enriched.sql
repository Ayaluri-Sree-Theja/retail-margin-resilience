with inventory as (

    select *
    from {{ ref('stg_inventory_snapshots') }}

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
        i.inventory_snapshot_id,
        i.date_id,
        c.calendar_date as snapshot_date,
        c.fiscal_year,
        c.fiscal_quarter,
        c.fiscal_week,
        c.is_holiday_season,

        i.store_id,
        st.region,
        st.state,
        st.city,
        st.store_format,
        st.store_size_band,
        st.risk_profile as store_risk_profile,
        st.fulfillment_enabled,

        i.product_id,
        p.category,
        p.subcategory,
        p.brand_type,
        p.price_band,
        p.unit_cost,
        p.unit_price,
        p.return_risk_level,
        p.shrink_risk_level,

        i.beginning_inventory_units,
        i.received_units,
        i.returned_units,
        i.sold_units,
        i.shrink_units,
        i.ending_inventory_units,
        i.available_inventory_units,
        i.inventory_value,
        i.sell_through_rate,
        i.stockout_flag,
        i.hard_stockout_flag,
        i.overstock_flag,

        case
            when i.sold_units = 0 then null
            else i.ending_inventory_units::numeric / i.sold_units
        end as weeks_of_supply_proxy,

        case
            when i.stockout_flag = true then 'Stockout Risk'
            when i.overstock_flag = true then 'Overstock Risk'
            else 'Healthy'
        end as inventory_health_status

    from inventory i

    left join calendar c
        on i.date_id = c.date_id

    left join stores st
        on i.store_id = st.store_id

    left join products p
        on i.product_id = p.product_id

)

select *
from final