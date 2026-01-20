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
    account_id,
    campaign_name,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    ingested_at,
    extract_run_id,
    extracted_at
  from {{ ref('stg_google_ads__campaign_daily') }}
),

meta_ads as (
  select
    report_date,
    campaign_id,
    account_id,
    campaign_name,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    ingested_at,
    extract_run_id,
    extracted_at
  from {{ ref('stg_meta_ads__campaign_daily') }}
),

unified as (
  select
    report_date,
    campaign_id,
    account_id,
    campaign_name,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    ingested_at,
    extract_run_id,
    extracted_at,
    current_timestamp() as unified_at
  from google_ads
  
  union all
  
  select
    report_date,
    campaign_id,
    account_id,
    campaign_name,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    ingested_at,
    extract_run_id,
    extracted_at,
    current_timestamp() as unified_at
  from meta_ads
)

select * from unified
