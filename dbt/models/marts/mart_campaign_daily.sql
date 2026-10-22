{{
    config(
        materialized='incremental',
        incremental_strategy='insert_overwrite',
        partition_by={'field': 'date', 'data_type': 'date', 'granularity': 'day'},
        cluster_by=['platform', 'campaign_id'],
        on_schema_change='fail',
    )
}}

-- Mesures et indicateurs par campagne et par jour.
-- Un ratio vaut NULL (jamais 0) quand son dénominateur est nul ou inconnu : safe_divide.
select
    date,
    platform,
    campaign_id,
    campaign_name,
    currency,
    impressions,
    clicks,
    spend,
    conversions,
    conversion_value,
    safe_divide(clicks, impressions) as ctr,
    safe_divide(spend, clicks) as cpc,
    safe_divide(spend, conversions) as cpa,
    safe_divide(conversions, clicks) as conversion_rate,
    safe_divide(conversion_value, spend) as roas,
    data_mode,
    ingested_at
from {{ ref('int_campaign_daily') }}
{% if is_incremental() %}
    where date >= {{ incremental_start_date() }}
{% endif %}
