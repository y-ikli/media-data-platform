{{
  config(
    materialized='incremental',
    incremental_strategy='insert_overwrite' if target.type == 'bigquery' else 'delete+insert',
    unique_key=['report_date', 'campaign_id', 'platform'],
    partition_by={'field': 'report_date', 'data_type': 'date', 'granularity': 'day'} if target.type == 'bigquery' else none,
    cluster_by=['platform', 'campaign_id'] if target.type == 'bigquery' else none,
    on_schema_change='fail'
  )
}}

{#- Incrémental : on retraite une fenêtre glissante (var lookback_days) plutôt que les seules nouvelles dates,
    car les plateformes corrigent leurs chiffres a posteriori. Pour rejouer un intervalle plus ancien :
      dbt run -s mart_campaign_daily --vars '{reprocess_from: "2024-01-01"}'
    Pour tout reconstruire : dbt run -s mart_campaign_daily --full-refresh. -#}

with unified as (
    select * from {{ ref('int_campaign_daily_unified') }}
    {% if is_incremental() %}
    where report_date >=
        {% if var('reprocess_from', none) %}
            cast('{{ var("reprocess_from") }}' as date)
        {% else %}
            (select {{ mdp.date_offset('max(report_date)', -1 * var('lookback_days')) }} from {{ this }})
        {% endif %}
    {% endif %}
)

select
    report_date,
    campaign_id,
    campaign_name,
    platform,
    data_mode,

    impressions,
    clicks,
    spend_usd                                                as spend,
    conversions,
    conversion_value,
    likes,
    comments,
    shares,
    video_views,
    page_engagement,

    {{ safe_ratio('clicks', 'impressions') }}                as ctr,
    {{ safe_ratio('spend_usd', 'clicks', 2) }}               as cpc,
    {{ safe_ratio('spend_usd', 'conversions', 2) }}          as cpa,
    {{ safe_ratio('conversions', 'clicks') }}                as conversion_rate,
    {{ safe_ratio('conversion_value', 'spend_usd') }}        as roas,

    ingested_at,
    extract_run_id,
    current_timestamp                                        as mart_created_at
from unified
