with source as (

    select *
    from {{ source('raw', 'dim_calendar') }}

),

base as (

    select
        date_id,
        calendar_date::date as calendar_date,
        year as calendar_year,
        quarter as calendar_quarter,
        month as calendar_month,
        month_name,
        week_of_year,
        day_of_week,
        day_name,
        is_weekend,
        is_holiday_season,

        case
            when calendar_date between date '2023-01-29' and date '2024-02-03' then 2023
            when calendar_date between date '2024-02-04' and date '2025-02-01' then 2024
            when calendar_date between date '2025-02-02' and date '2026-01-31' then 2025
        end as fiscal_year,

        case
            when calendar_date between date '2023-01-29' and date '2024-02-03'
                then floor((calendar_date - date '2023-01-29') / 7) + 1
            when calendar_date between date '2024-02-04' and date '2025-02-01'
                then floor((calendar_date - date '2024-02-04') / 7) + 1
            when calendar_date between date '2025-02-02' and date '2026-01-31'
                then floor((calendar_date - date '2025-02-02') / 7) + 1
        end as fiscal_week

    from source

),

final as (

    select
        date_id,
        calendar_date,
        calendar_year,
        calendar_quarter,
        calendar_month,
        month_name,
        week_of_year,
        day_of_week,
        day_name,
        is_weekend,
        is_holiday_season,
        fiscal_year,
        fiscal_week,

        case
            when fiscal_week between 1 and 13 then 1
            when fiscal_week between 14 and 26 then 2
            when fiscal_week between 27 and 39 then 3
            when fiscal_week between 40 and 53 then 4
        end as fiscal_quarter

    from base

)

select *
from final