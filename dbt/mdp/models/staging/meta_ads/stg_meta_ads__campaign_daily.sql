{{
  config(
    materialized='view',
    tags=['staging', 'meta_ads']
  )
}}

with source as (
  select * from `{{ var('gcp_project') }}.{{ var('raw_dataset') }}.raw_meta_ads__campaign_daily`
),

renamed as (
  select
    -- Primary keys
    date as report_date,
    campaign_id,
    
    -- Dimensions
    account_id,
    campaign_name,
    'meta_ads' as platform,
    
    -- Metrics
    cast(impressions as int64) as impressions,
    cast(clicks as int64) as clicks,
    cast(spend as numeric) as spend,
    cast(conversions as int64) as conversions,
    
    -- Metadata
    ingested_at,
    extract_run_id,
    _airbyte_emitted_at as extracted_at
    
  from source
  where date is not null
    and campaign_id is not null
)

select * from renamed
