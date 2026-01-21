{{
  config(
    materialized='table',
    tags=['marts', 'campaign', 'core'],
    cluster_by=['report_date', 'platform']
  )
}}

with unified as (
  select * from {{ ref('int_campaign_daily_unified') }}
),

kpi_calculation as (
  select
    report_date,
    campaign_id,
    campaign_name,
    platform,
    impressions,
    clicks,
    spend,
    conversions,
    -- Derived KPIs
    case when impressions > 0 then round(safe_divide(clicks, impressions), 4) else null end as ctr,
    case when conversions > 0 then round(safe_divide(spend, conversions), 2) else null end as cpa,
    case when spend > 0 then round(safe_divide(conversions, spend), 4) else null end as roas,
    case when clicks > 0 then round(safe_divide(spend, clicks), 2) else null end as cpc,
    case when clicks > 0 then round(safe_divide(conversions, clicks), 4) else null end as conversion_rate,
    ingested_at,
    extract_run_id,
    source,
    current_timestamp() as mart_created_at
  from unified
  where report_date is not null
    and campaign_id is not null
    and platform is not null
)

select * from kpi_calculation
