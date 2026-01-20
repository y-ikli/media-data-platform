-- Test: No negative values in performance metrics
-- Ensures data integrity by checking that metrics like impressions, clicks, spend are never negative

SELECT
  report_date,
  campaign_id,
  platform,
  impressions,
  clicks,
  spend,
  conversions
FROM {{ ref('mart_campaign_daily') }}
WHERE impressions < 0
   OR clicks < 0
   OR spend < 0
   OR conversions < 0
QUALIFY ROW_NUMBER() OVER (ORDER BY report_date DESC) <= 1000
