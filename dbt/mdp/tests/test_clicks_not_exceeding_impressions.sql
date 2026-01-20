-- Test: Logical consistency - clicks ≤ impressions
-- Validates that the number of clicks does not exceed impressions

SELECT
  report_date,
  campaign_id,
  platform,
  impressions,
  clicks
FROM {{ ref('mart_campaign_daily') }}
WHERE clicks > impressions
QUALIFY ROW_NUMBER() OVER (ORDER BY report_date DESC) <= 1000
