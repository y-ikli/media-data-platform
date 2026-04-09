{{
  config(
    materialized='view',
    tags=['intermediate', 'unified']
  )
}}

with google_ads as (
  select
    report_date,
    cast(campaign_id as string) as campaign_id,
    campaign_name,
    impressions,
    clicks,
    conversions,
    cost_usd as spend,
    null as likes,
    null as comments,
    null as shares,
    null as video_views,
    null as page_engagement,
    ingested_at,
    extract_run_id,
    source,
    'google_ads' as platform
  from {{ ref('stg_google_ads__campaign_daily') }}
),

meta_ads as (
  select
    report_date,
    cast(campaign_id as string) as campaign_id,
    campaign_name,
    impressions,
    clicks,
    null as conversions,
    spend_usd as spend,
    likes,
    comments,
    shares,
    video_views,
    page_engagement,
    ingested_at,
    extract_run_id,
    source,
    'meta_ads' as platform
  from {{ ref('stg_meta_ads__campaign_daily') }}
)

select * from google_ads
union all
select * from meta_ads