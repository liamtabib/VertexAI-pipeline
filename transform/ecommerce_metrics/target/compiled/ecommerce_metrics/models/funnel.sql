-- Shopping Funnel for Latest Full Month
-- 3-step conversion funnel: product → cart → purchase

WITH latest_full_month AS (
  SELECT DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 1 MONTH) AS month
),

month_events AS (
  SELECT 
    session_id, 
    event_type
  FROM `bigquery-public-data`.`thelook_ecommerce`.`events`
  CROSS JOIN latest_full_month
  WHERE DATE_TRUNC(DATE(created_at), MONTH) = latest_full_month.month
),

sessions AS (
  SELECT 
    session_id, 
    ARRAY_AGG(DISTINCT event_type) AS steps
  FROM month_events
  GROUP BY session_id
),

counts AS (
  SELECT
    COUNTIF('product' IN UNNEST(steps)) AS s1,
    COUNTIF('product' IN UNNEST(steps) AND 'cart' IN UNNEST(steps)) AS s2,
    COUNTIF('product' IN UNNEST(steps) AND 'cart' IN UNNEST(steps) AND 'purchase' IN UNNEST(steps)) AS s3
  FROM sessions
)

SELECT * FROM (
  SELECT 1 AS step, 'Product View' AS step_name, s1 AS sessions FROM counts UNION ALL
  SELECT 2 AS step, 'Add to Cart' AS step_name, s2 AS sessions FROM counts UNION ALL
  SELECT 3 AS step, 'Purchase' AS step_name, s3 AS sessions FROM counts
)
ORDER BY step