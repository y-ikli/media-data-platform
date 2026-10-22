-- Meta Ads : une ligne par campagne et par jour, avec les réactions propres à Meta.
with source as (
    select * from {{ source('ads_raw', 'meta_ads_campaign_daily') }}
),

deduplicated as (
    select *
    from source
    qualify row_number() over (
        partition by date, campaign_id
        order by ingested_at desc
    ) = 1
)

select
    date,
    'meta_ads' as platform,
    campaign_id,
    campaign_name,
    account_currency as currency,
    impressions,
    clicks,
    spend,
    conversions,
    conversion_value,
    likes,
    comments,
    shares,
    video_views,
    page_engagement,
    data_mode,
    extract_run_id,
    ingested_at
from deduplicated
