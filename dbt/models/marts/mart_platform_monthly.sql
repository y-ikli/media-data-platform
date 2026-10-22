-- Synthèse mensuelle par plateforme. Les ratios sont recalculés depuis les sommes :
-- une moyenne de ratios journaliers donnerait autant de poids à un petit jour qu'à un gros.
select
    date_trunc(date, month) as month,
    platform,
    currency,
    data_mode,
    count(distinct campaign_id) as campaigns,
    sum(impressions) as impressions,
    sum(clicks) as clicks,
    sum(spend) as spend,
    sum(conversions) as conversions,
    sum(conversion_value) as conversion_value,
    safe_divide(sum(clicks), sum(impressions)) as ctr,
    safe_divide(sum(spend), sum(clicks)) as cpc,
    safe_divide(sum(spend), sum(conversions)) as cpa,
    safe_divide(sum(conversions), sum(clicks)) as conversion_rate,
    safe_divide(sum(conversion_value), sum(spend)) as roas
from {{ ref('mart_campaign_daily') }}
group by month, platform, currency, data_mode
