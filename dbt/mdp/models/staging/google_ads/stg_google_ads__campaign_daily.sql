{{
  config(
    materialized='view',
    tags=['staging', 'google_ads']
  )
}}

select
  date as report_date,
  campaign_id,
  campaign_name,
  impressions,
  clicks,
  conversions,
  cost_usd,
  cpc,
  cpa,
  ctr,
  conversion_rate,
  ingested_at,
  extract_run_id,
  source
from `{{ var('gcp_project') }}.{{ var('raw_dataset') }}.google_ads_campaign_daily`
where date is not null
  and campaign_id is not null

