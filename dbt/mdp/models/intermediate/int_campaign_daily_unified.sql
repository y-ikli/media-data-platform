{{
  config(
    materialized='view',
    tags=['intermediate', 'unified']
  )
}}

with google_ads as (
  select
    report_date,
    campaign_id,
    campaign_name,
    impressions,
    clicks,
    conversions,
    cost_usd as spend,
    ingested_at,
    extract_run_id,
    source,
    'google_ads' as platform
  from {{ ref('stg_google_ads__campaign_daily') }}
),

meta_ads as (
  select
    report_date,
    campaign_id,
    campaign_name,
    impressions,
    clicks,
    conversions,
    spend_usd as spend,
    ingested_at,
    extract_run_id,
    source,
    'meta_ads' as platform
  from {{ ref('stg_meta_ads__campaign_daily') }}
),

unified as (
  select
    report_date,
    campaign_id,
    campaign_name,
    impressions,
    clicks,
    conversions,
    spend,
    ingested_at,
    extract_run_id,
    source,
    platform,
    current_timestamp() as unified_at
  from google_ads
  union all
  select
    report_date,
    campaign_id,
    campaign_name,
    impressions,
    clicks,
    conversions,
    spend,
    ingested_at,
    extract_run_id,
    source,
    platform,
    current_timestamp() as unified_at
  from meta_ads
)

select * from unified
