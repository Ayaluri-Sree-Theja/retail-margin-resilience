with sales as (

    select
        fiscal_year,
        fiscal_quarter,
        category,
        sum(quantity_sold) as units_sold,
        sum(net_sales_revenue) as net_sales_revenue,
        sum(gross_margin) as gross_margin
    from {{ ref('int_sales_enriched') }}
    group by 1, 2, 3

),

returns as (

    select
        fiscal_year,
        fiscal_quarter,
        category,
        count(*) as return_lines,
        sum(returned_units) as returned_units,
        sum(refund_amount) as refund_amount,
        sum(case when return_loss_flag = true then refund_amount else 0 end) as damaged_unsellable_refund_amount
    from {{ ref('int_returns_enriched') }}
    group by 1, 2, 3

),

shrink as (

    select
        fiscal_year,
        fiscal_quarter,
        category,
        count(*) as shrink_events,
        sum(shrink_units) as shrink_units,
        sum(estimated_shrink_value) as shrink_value,
        sum(case when theft_related_flag = true then estimated_shrink_value else 0 end) as theft_related_shrink_value,
        sum(case when investigation_flag = true then 1 else 0 end) as investigation_events
    from {{ ref('int_shrink_enriched') }}
    group by 1, 2, 3

),

final as (

    select
        s.fiscal_year,
        s.fiscal_quarter,
        s.category,

        s.units_sold,
        s.net_sales_revenue,
        s.gross_margin,

        coalesce(r.return_lines, 0) as return_lines,
        coalesce(r.returned_units, 0) as returned_units,
        coalesce(r.refund_amount, 0) as refund_amount,
        coalesce(r.damaged_unsellable_refund_amount, 0) as damaged_unsellable_refund_amount,

        case
            when s.units_sold = 0 then null
            else coalesce(r.returned_units, 0)::numeric / s.units_sold
        end as unit_return_rate,

        s.net_sales_revenue - coalesce(r.refund_amount, 0) as return_adjusted_revenue,

        coalesce(sh.shrink_events, 0) as shrink_events,
        coalesce(sh.shrink_units, 0) as shrink_units,
        coalesce(sh.shrink_value, 0) as shrink_value,
        coalesce(sh.theft_related_shrink_value, 0) as theft_related_shrink_value,
        coalesce(sh.investigation_events, 0) as investigation_events,

        s.gross_margin - coalesce(sh.shrink_value, 0) as shrink_adjusted_margin,

        coalesce(r.refund_amount, 0) + coalesce(sh.shrink_value, 0) as return_shrink_leakage_value

    from sales s

    left join returns r
        on s.fiscal_year = r.fiscal_year
        and s.fiscal_quarter = r.fiscal_quarter
        and s.category = r.category

    left join shrink sh
        on s.fiscal_year = sh.fiscal_year
        and s.fiscal_quarter = sh.fiscal_quarter
        and s.category = sh.category

)

select *
from final