-- Google Ads : une ligne par campagne et par jour, coût converti des micros vers la devise.
with source as (
    select * from {{ source('ads_raw', 'google_ads_campaign_daily') }}
),

deduplicated as (
    -- Garde-fou : le chargement est idempotent, mais si un doublon passait, la dernière
    -- ingestion gagne.
    select *
    from source
    qualify row_number() over (
        partition by date, campaign_id
        order by ingested_at desc
    ) = 1
)

select
    date,
    'google_ads' as platform,
    campaign_id,
    campaign_name,
    currency_code as currency,
    impressions,
    clicks,
    cost_micros / 1000000 as spend,
    conversions,
    conversion_value,
    data_mode,
    extract_run_id,
    ingested_at
from deduplicated
