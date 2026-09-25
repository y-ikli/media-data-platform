{#- Union des plateformes dans un schéma commun. Les colonnes absentes d'une plateforme sont NULL et typées :
    NULL signifie « non disponible pour cette source », jamais 0. -#}
with google_ads as (
    select
        report_date, campaign_id, campaign_name,
        'google_ads' as platform,
        impressions, clicks, conversions, conversion_value,
        cost_usd as spend_usd,
        cast(null as bigint) as likes,
        cast(null as bigint) as comments,
        cast(null as bigint) as shares,
        cast(null as bigint) as video_views,
        cast(null as bigint) as page_engagement,
        data_mode, ingested_at, extract_run_id
    from {{ ref('stg_google_ads__campaign_daily') }}
),

meta_ads as (
    select
        report_date, campaign_id, campaign_name,
        'meta_ads' as platform,
        impressions, clicks, conversions, conversion_value,
        spend_usd,
        likes, comments, shares, video_views, page_engagement,
        data_mode, ingested_at, extract_run_id
    from {{ ref('stg_meta_ads__campaign_daily') }}
)

select * from google_ads
union all
select * from meta_ads
