-- Test: CTR should never exceed 100% (clicks cannot exceed impressions)
-- If CTR > 1.0, it means either clicks > impressions (data error) or calculation error

SELECT
  report_date,
  campaign_id,
  platform,
  clicks,
  impressions,
  ctr
FROM {{ ref('mart_campaign_daily') }}
WHERE ctr > 1.0
QUALIFY ROW_NUMBER() OVER (ORDER BY report_date DESC) <= 1000
