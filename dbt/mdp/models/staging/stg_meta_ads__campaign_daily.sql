{#- Une ligne par (report_date, campaign_id) : la dernière ingestion gagne.
    Les chargements de la zone raw sont idempotents, mais la déduplication est reprise ici par défense
    (chargement manuel, ancien mode append) : la couche aval peut supposer l'unicité du grain. -#}
with ranked as (
    select
        *,
        row_number() over (
            partition by date, campaign_id
            order by ingested_at desc, extract_run_id desc
        ) as _rn
    from {{ source('raw', 'meta_ads_campaign_daily') }}
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
    cast(spend_usd as {{ dbt.type_float() }}) as spend_usd,
    cast(likes as bigint)                     as likes,
    cast(comments as bigint)                  as comments,
    cast(shares as bigint)                    as shares,
    cast(video_views as bigint)               as video_views,
    cast(page_engagement as bigint)           as page_engagement,
    data_mode,
    ingested_at,
    extract_run_id
from ranked
where _rn = 1
