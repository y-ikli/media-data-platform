-- Test: KPI calculations are mathematically correct
-- Tests that CTR = clicks / impressions, CPC = spend / clicks, etc.
-- Returns rows where a KPI deviates from expected formula — test fails if any row returned.

SELECT
  report_date,
  campaign_id,
  platform
FROM {{ ref('mart_campaign_daily') }}
WHERE
  -- CTR error: should be clicks / impressions when impressions > 0
  (impressions > 0 AND ctr IS NOT NULL AND ABS(SAFE_DIVIDE(clicks, impressions) - ctr) > 0.0001)
  -- CPC error: should be spend / clicks when clicks > 0
  OR (clicks > 0 AND cpc IS NOT NULL AND ABS(SAFE_DIVIDE(spend, clicks) - cpc) > 0.01)
  -- CPA error: skip Meta rows (conversions null), only check Google
  OR (conversions IS NOT NULL AND conversions > 0 AND cpa IS NOT NULL AND ABS(SAFE_DIVIDE(spend, conversions) - cpa) > 0.01)
QUALIFY ROW_NUMBER() OVER (ORDER BY report_date DESC) <= 1000