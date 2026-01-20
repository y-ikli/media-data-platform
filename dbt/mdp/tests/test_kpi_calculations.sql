-- Test: KPI calculations are mathematically correct
-- Tests that CTR = clicks / impressions, CPC = spend / clicks, etc.
-- This test ensures no data corruption in calculated fields.

SELECT
  report_date,
  campaign_id,
  platform,
  -- CTR should be clicks / impressions (or NULL if impressions = 0)
  CASE 
    WHEN impressions = 0 THEN ctr IS NULL
    ELSE ABS(SAFE_DIVIDE(clicks, impressions) - ctr) > 0.0001
  END AS ctr_calc_error,
  
  -- CPC should be spend / clicks (or NULL if clicks = 0)
  CASE 
    WHEN clicks = 0 THEN cpc IS NULL
    ELSE ABS(SAFE_DIVIDE(spend, clicks) - cpc) > 0.01
  END AS cpc_calc_error,
  
  -- CPA should be spend / conversions (or NULL if conversions = 0)
  CASE 
    WHEN conversions = 0 THEN cpa IS NULL
    ELSE ABS(SAFE_DIVIDE(spend, conversions) - cpa) > 0.01
  END AS cpa_calc_error
FROM {{ ref('mart_campaign_daily') }}
WHERE ctr_calc_error OR cpc_calc_error OR cpa_calc_error
QUALIFY ROW_NUMBER() OVER (ORDER BY report_date DESC) <= 1000
