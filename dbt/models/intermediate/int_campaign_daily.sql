-- Les deux plateformes au même format : une ligne par plateforme, campagne et jour.
{% set common_columns = [
    'date', 'platform', 'campaign_id', 'campaign_name', 'currency',
    'impressions', 'clicks', 'spend', 'conversions', 'conversion_value',
    'data_mode', 'extract_run_id', 'ingested_at',
] %}

{% for model in ['stg_google_ads__campaign_daily', 'stg_meta_ads__campaign_daily'] %}
    select {{ common_columns | join(', ') }}
    from {{ ref(model) }}
    {% if not loop.last %}union all{% endif %}
{% endfor %}
