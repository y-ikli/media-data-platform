select
  *
from {{ ref('stg_google_ads__campaign_daily') }}
