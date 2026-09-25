{{ config(materialized='table', cluster_by=(['platform'] if target.type == 'bigquery' else none)) }}

{#- Agrégat mensuel par plateforme. Les ratios sont recalculés à partir des sommes (Σdépense / Σclics),
    jamais moyennés : la moyenne des CPC journaliers pondère un jour à 10 clics comme un jour à 10 000. -#}

select
    {{ mdp.month_start('report_date') }}             as report_month,
    platform,
    data_mode,
    count(distinct campaign_id)                              as campaigns,
    sum(impressions)                                         as impressions,
    sum(clicks)                                              as clicks,
    sum(spend)                                               as spend,
    sum(conversions)                                         as conversions,
    sum(conversion_value)                                    as conversion_value,
    {{ safe_ratio('sum(clicks)', 'sum(impressions)') }}      as ctr,
    {{ safe_ratio('sum(spend)', 'sum(clicks)', 2) }}         as cpc,
    {{ safe_ratio('sum(spend)', 'sum(conversions)', 2) }}    as cpa,
    {{ safe_ratio('sum(conversion_value)', 'sum(spend)') }}  as roas
from {{ ref('mart_campaign_daily') }}
group by 1, 2, 3
