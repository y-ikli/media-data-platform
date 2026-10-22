-- Une ligne par campagne, avec son nom le plus récent (une campagne peut être renommée).
select
    platform,
    campaign_id,
    array_agg(campaign_name ignore nulls order by date desc, ingested_at desc limit 1)[
        safe_offset(0)
    ] as campaign_name,
    min(date) as first_seen,
    max(date) as last_seen,
    logical_or(data_mode = 'simulated') as has_simulated_data
from {{ ref('int_campaign_daily') }}
group by platform, campaign_id
