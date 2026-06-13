with sales as (

    select
        fiscal_year,
        region,
        store_id,
        store_name,
        store_format,
        category,

        count(distinct transaction_id) as transactions,
        sum(quantity_sold) as units_sold,
        sum(gross_revenue) as gross_revenue,
        sum(net_sales_revenue) as net_sales_revenue,
        sum(gross_margin) as gross_margin,
        sum(markdown_loss) as markdown_loss
    from {{ ref('int_sales_enriched') }}
    group by 1, 2, 3, 4, 5, 6

),

returns as (

    select
        fiscal_year,
        store_id,
        category,

        sum(returned_units) as returned_units,
        sum(refund_amount) as refund_amount
    from {{ ref('int_returns_enriched') }}
    group by 1, 2, 3

),

shrink as (

    select
        fiscal_year,
        store_id,
        category,

        sum(shrink_units) as shrink_units,
        sum(estimated_shrink_value) as shrink_value
    from {{ ref('int_shrink_enriched') }}
    group by 1, 2, 3

),

final as (

    select
        s.fiscal_year,
        s.region,
        s.store_id,
        s.store_name,
        s.store_format,
        s.category,

        s.transactions,
        s.units_sold,
        s.gross_revenue,
        s.net_sales_revenue,
        s.gross_margin,

        case
            when s.net_sales_revenue = 0 then null
            else s.gross_margin / s.net_sales_revenue
        end as gross_margin_rate,

        s.markdown_loss,

        coalesce(r.returned_units, 0) as returned_units,
        coalesce(r.refund_amount, 0) as refund_amount,

        coalesce(sh.shrink_units, 0) as shrink_units,
        coalesce(sh.shrink_value, 0) as shrink_value,

        s.net_sales_revenue - coalesce(r.refund_amount, 0) as return_adjusted_revenue,
        s.gross_margin - coalesce(sh.shrink_value, 0) as shrink_adjusted_margin,

        coalesce(r.refund_amount, 0)
            + coalesce(sh.shrink_value, 0)
            + coalesce(s.markdown_loss, 0) as margin_at_risk

    from sales s

    left join returns r
        on s.fiscal_year = r.fiscal_year
        and s.store_id = r.store_id
        and s.category = r.category

    left join shrink sh
        on s.fiscal_year = sh.fiscal_year
        and s.store_id = sh.store_id
        and s.category = sh.category

)

select *
from final