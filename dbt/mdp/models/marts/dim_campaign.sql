{{ config(materialized='table') }}

{#- Une ligne par campagne et plateforme, avec le nom le plus récent : une campagne renommée ne se
    dédouble plus dans les tableaux de bord qui regroupent par nom. -#}

with ranked as (
    select
        platform,
        campaign_id,
        campaign_name,
        data_mode,
        report_date,
        row_number() over (partition by platform, campaign_id order by report_date desc) as _rn
    from {{ ref('mart_campaign_daily') }}
),

bounds as (
    select platform, campaign_id, min(report_date) as first_report_date, max(report_date) as last_report_date
    from {{ ref('mart_campaign_daily') }}
    group by platform, campaign_id
)

select
    ranked.platform,
    ranked.campaign_id,
    ranked.campaign_name as current_campaign_name,
    ranked.data_mode,
    bounds.first_report_date,
    bounds.last_report_date
from ranked
inner join bounds
    on ranked.platform = bounds.platform and ranked.campaign_id = bounds.campaign_id
where ranked._rn = 1
