with inventory as (

    select *
    from {{ ref('int_inventory_enriched') }}

),

final as (

    select
        fiscal_year,
        fiscal_week,
        snapshot_date,
        region,
        store_format,
        category,

        count(*) as snapshot_count,

        sum(beginning_inventory_units) as beginning_inventory_units,
        sum(received_units) as received_units,
        sum(returned_units) as returned_units,
        sum(sold_units) as sold_units,
        sum(shrink_units) as shrink_units,
        sum(ending_inventory_units) as ending_inventory_units,

        avg(inventory_value) as avg_inventory_value,
        sum(inventory_value) as cumulative_snapshot_inventory_value,

        sum(case when stockout_flag = true then 1 else 0 end) as stockout_snapshots,
        sum(case when hard_stockout_flag = true then 1 else 0 end) as hard_stockout_snapshots,
        sum(case when overstock_flag = true then 1 else 0 end) as overstock_snapshots,

        case
            when count(*) = 0 then null
            else sum(case when stockout_flag = true then 1 else 0 end)::numeric / count(*)
        end as stockout_rate,

        case
            when count(*) = 0 then null
            else sum(case when overstock_flag = true then 1 else 0 end)::numeric / count(*)
        end as overstock_rate,

        case
            when sum(beginning_inventory_units) = 0 then null
            else sum(sold_units)::numeric / sum(beginning_inventory_units)
        end as sell_through_rate,

        avg(weeks_of_supply_proxy) as avg_weeks_of_supply_proxy

    from inventory
    group by
        fiscal_year,
        fiscal_week,
        snapshot_date,
        region,
        store_format,
        category

)

select *
from final