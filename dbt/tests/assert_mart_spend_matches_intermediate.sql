-- La dépense totale des marts doit être celle des données intermédiaires, au centime près,
-- par plateforme et par devise. Une ligne renvoyée = un écart.
with intermediate as (
    select
        platform,
        currency,
        round(sum(spend), 2) as spend
    from {{ ref('int_campaign_daily') }}
    group by platform, currency
),

mart as (
    select
        platform,
        currency,
        round(sum(spend), 2) as spend
    from {{ ref('mart_campaign_daily') }}
    group by platform, currency
)

select
    coalesce(i.platform, m.platform) as platform,
    coalesce(i.currency, m.currency) as currency,
    i.spend as intermediate_spend,
    m.spend as mart_spend
from intermediate as i
full outer join mart as m
    on i.platform = m.platform and i.currency = m.currency
where i.spend is null or m.spend is null or i.spend != m.spend
