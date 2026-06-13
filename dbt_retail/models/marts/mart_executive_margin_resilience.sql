with sales as (

    select
        fiscal_year,
        fiscal_quarter,
        count(distinct transaction_id) as total_transactions,
        count(*) as sales_lines,
        sum(quantity_sold) as units_sold,
        sum(gross_revenue) as gross_revenue,
        sum(net_sales_revenue) as net_sales_revenue,
        sum(gross_margin) as gross_margin,
        sum(markdown_loss) as markdown_loss
    from {{ ref('int_sales_enriched') }}
    group by 1, 2

),

returns as (

    select
        fiscal_year,
        fiscal_quarter,
        count(*) as return_lines,
        sum(returned_units) as returned_units,
        sum(refund_amount) as refund_amount
    from {{ ref('int_returns_enriched') }}
    group by 1, 2

),

shrink as (

    select
        fiscal_year,
        fiscal_quarter,
        count(*) as shrink_events,
        sum(shrink_units) as shrink_units,
        sum(estimated_shrink_value) as shrink_value,
        sum(case when investigation_flag = true then 1 else 0 end) as investigation_events
    from {{ ref('int_shrink_enriched') }}
    group by 1, 2

),

inventory as (

    select
        fiscal_year,
        fiscal_quarter,
        count(*) as inventory_snapshots,
        avg(inventory_value) as avg_snapshot_inventory_value,
        sum(case when stockout_flag = true then 1 else 0 end) as stockout_snapshots,
        sum(case when overstock_flag = true then 1 else 0 end) as overstock_snapshots,
        sum(sold_units) as inventory_sold_units,
        sum(received_units) as received_units
    from {{ ref('int_inventory_enriched') }}
    group by 1, 2

),

fulfillment as (

    select
        c.fiscal_year,
        c.fiscal_quarter,
        count(*) as shipment_count,
        sum(case when f.delayed_flag = true then 1 else 0 end) as delayed_shipments,
        avg(f.delay_days) as avg_delay_days,
        sum(f.short_shipped_units) as short_shipped_units
    from {{ ref('int_fulfillment_enriched') }} f
    left join {{ ref('stg_calendar') }} c
        on f.delivered_date = c.calendar_date
    where c.fiscal_year is not null
    group by 1, 2

),

final as (

    select
        s.fiscal_year,
        s.fiscal_quarter,

        s.total_transactions,
        s.sales_lines,
        s.units_sold,
        s.gross_revenue,
        s.net_sales_revenue,
        s.gross_margin,

        case
            when s.net_sales_revenue = 0 then null
            else s.gross_margin / s.net_sales_revenue
        end as gross_margin_rate,

        s.markdown_loss,

        coalesce(r.return_lines, 0) as return_lines,
        coalesce(r.returned_units, 0) as returned_units,
        coalesce(r.refund_amount, 0) as refund_amount,

        s.net_sales_revenue - coalesce(r.refund_amount, 0) as return_adjusted_revenue,

        case
            when s.units_sold = 0 then null
            else coalesce(r.returned_units, 0)::numeric / s.units_sold
        end as unit_return_rate,

        coalesce(sh.shrink_events, 0) as shrink_events,
        coalesce(sh.shrink_units, 0) as shrink_units,
        coalesce(sh.shrink_value, 0) as shrink_value,
        coalesce(sh.investigation_events, 0) as investigation_events,

        s.gross_margin - coalesce(sh.shrink_value, 0) as shrink_adjusted_margin,

        coalesce(i.inventory_snapshots, 0) as inventory_snapshots,
        coalesce(i.avg_snapshot_inventory_value, 0) as avg_snapshot_inventory_value,
        coalesce(i.stockout_snapshots, 0) as stockout_snapshots,
        coalesce(i.overstock_snapshots, 0) as overstock_snapshots,

        case
            when i.inventory_snapshots = 0 then null
            else i.stockout_snapshots::numeric / i.inventory_snapshots
        end as stockout_snapshot_rate,

        case
            when i.inventory_snapshots = 0 then null
            else i.overstock_snapshots::numeric / i.inventory_snapshots
        end as overstock_snapshot_rate,

        coalesce(f.shipment_count, 0) as shipment_count,
        coalesce(f.delayed_shipments, 0) as delayed_shipments,
        coalesce(f.avg_delay_days, 0) as avg_delay_days,
        coalesce(f.short_shipped_units, 0) as short_shipped_units,

        case
            when f.shipment_count = 0 then null
            else f.delayed_shipments::numeric / f.shipment_count
        end as fulfillment_delay_rate,

        coalesce(s.markdown_loss, 0)
            + coalesce(r.refund_amount, 0)
            + coalesce(sh.shrink_value, 0) as margin_at_risk

    from sales s

    left join returns r
        on s.fiscal_year = r.fiscal_year
        and s.fiscal_quarter = r.fiscal_quarter

    left join shrink sh
        on s.fiscal_year = sh.fiscal_year
        and s.fiscal_quarter = sh.fiscal_quarter

    left join inventory i
        on s.fiscal_year = i.fiscal_year
        and s.fiscal_quarter = i.fiscal_quarter

    left join fulfillment f
        on s.fiscal_year = f.fiscal_year
        and s.fiscal_quarter = f.fiscal_quarter

)

select *
from final