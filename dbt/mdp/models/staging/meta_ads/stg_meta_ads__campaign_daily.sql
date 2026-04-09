{{
  config(
    materialized='view',
    tags=['staging', 'meta_ads']
  )
}}

select
  date as report_date,
  campaign_id,
  campaign_name,
  impressions,
  clicks,
  spend_usd,
  likes,
  comments,
  shares,
  video_views,
  page_engagement,
  ingested_at,
  extract_run_id,
  source
from `{{ var('gcp_project') }}.{{ var('raw_dataset') }}.meta_ads_campaign_daily`
where date is not null
  and campaign_id is not null


