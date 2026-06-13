with source as (

    select *
    from {{ source('raw', 'dim_supplier') }}

),

renamed as (

    select
        supplier_id,
        supplier_name,
        supplier_region,
        average_lead_time_days,
        reliability_score,
        delay_risk_level,

        case
            when reliability_score >= 90 then 'Reliable'
            when reliability_score >= 80 then 'Moderate'
            else 'Unstable'
        end as supplier_reliability_band

    from source

)

select *
from renamed