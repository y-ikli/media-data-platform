{#- Une ligne par (report_date, campaign_id) : la dernière ingestion gagne (voir stg_meta_ads__campaign_daily). -#}
with ranked as (
    select
        *,
        row_number() over (
            partition by date, campaign_id
            order by ingested_at desc, extract_run_id desc
        ) as _rn
    from {{ source('raw', 'google_ads_campaign_daily') }}
    where date is not null and campaign_id is not null
)

select
    cast(date as date)                        as report_date,
    cast(campaign_id as string)               as campaign_id,
    campaign_name,
    cast(impressions as bigint)               as impressions,
    cast(clicks as bigint)                    as clicks,
    cast(conversions as bigint)               as conversions,
    cast(conversion_value as {{ dbt.type_float() }}) as conversion_value,
    cast(cost_usd as {{ dbt.type_float() }})  as cost_usd,
    data_mode,
    ingested_at,
    extract_run_id
from ranked
where _rn = 1
