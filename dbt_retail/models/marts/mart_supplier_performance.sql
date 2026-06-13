with fulfillment as (

    select *
    from {{ ref('int_fulfillment_enriched') }}

),

calendar as (

    select *
    from {{ ref('stg_calendar') }}

),

enriched as (

    select
        f.*,
        c.fiscal_year,
        c.fiscal_quarter
    from fulfillment f
    left join calendar c
        on f.delivered_date = c.calendar_date
    where c.fiscal_year is not null

),

final as (

    select
        fiscal_year,
        fiscal_quarter,

        supplier_id,
        supplier_name,
        supplier_region,
        delay_risk_level,
        supplier_reliability_band,
        reliability_score,

        category,

        count(*) as shipment_count,
        count(distinct store_id) as stores_served,
        count(distinct product_id) as products_supplied,

        sum(ordered_units) as ordered_units,
        sum(shipped_units) as shipped_units,
        sum(delivered_units) as delivered_units,
        sum(short_shipped_units) as short_shipped_units,

        sum(case when delayed_flag = true then 1 else 0 end) as delayed_shipments,
        sum(case when short_shipment_flag = true then 1 else 0 end) as short_shipments,

        case
            when count(*) = 0 then null
            else sum(case when delayed_flag = true then 1 else 0 end)::numeric / count(*)
        end as delay_rate,

        case
            when count(*) = 0 then null
            else sum(case when short_shipment_flag = true then 1 else 0 end)::numeric / count(*)
        end as short_shipment_rate,

        avg(delay_days) as avg_delay_days,
        max(delay_days) as max_delay_days,
        avg(actual_lead_time_days) as avg_actual_lead_time_days,

        case
            when sum(case when delayed_flag = true then 1 else 0 end)::numeric / nullif(count(*), 0) >= 0.25 then 'High Delay Concern'
            when sum(case when delayed_flag = true then 1 else 0 end)::numeric / nullif(count(*), 0) >= 0.12 then 'Moderate Delay Concern'
            else 'Reliable'
        end as supplier_performance_status

    from enriched
    group by
        fiscal_year,
        fiscal_quarter,
        supplier_id,
        supplier_name,
        supplier_region,
        delay_risk_level,
        supplier_reliability_band,
        reliability_score,
        category

)

select *
from final