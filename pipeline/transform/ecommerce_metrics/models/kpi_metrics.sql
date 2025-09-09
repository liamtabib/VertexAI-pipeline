-- KPI Metrics for Dashboard
-- Provides key performance indicators for top-level dashboard display

WITH last_data_date AS (
  SELECT MAX(DATE(created_at)) AS last_updated
  FROM {{ source('thelook_ecommerce', 'events') }}
),

mau_last_30_days AS (
  SELECT COUNT(DISTINCT user_id) AS mau_30_days
  FROM {{ source('thelook_ecommerce', 'events') }}
  WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    AND DATE(created_at) < CURRENT_DATE()
),

purchase_conversion_last_30_days AS (
  WITH events_30_days AS (
    SELECT 
      session_id,
      ARRAY_AGG(DISTINCT event_type) AS event_types
    FROM {{ source('thelook_ecommerce', 'events') }}
    WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      AND DATE(created_at) < CURRENT_DATE()
    GROUP BY session_id
  )
  SELECT 
    COUNTIF('product' IN UNNEST(event_types)) AS product_sessions,
    COUNTIF('product' IN UNNEST(event_types) AND 'purchase' IN UNNEST(event_types)) AS purchase_sessions,
    SAFE_DIVIDE(
      COUNTIF('product' IN UNNEST(event_types) AND 'purchase' IN UNNEST(event_types)),
      COUNTIF('product' IN UNNEST(event_types))
    ) AS purchase_conversion_rate
  FROM events_30_days
)

SELECT
  -- Date last updated
  FORMAT_DATE('%Y-%m-%d', CURRENT_DATE()) AS last_updated_date,
  
  -- MAU last 30 days
  mau_last_30_days.mau_30_days,
  
  -- Purchase conversion rate last 30 days  
  purchase_conversion_last_30_days.purchase_conversion_rate

FROM last_data_date
CROSS JOIN mau_last_30_days
CROSS JOIN purchase_conversion_last_30_days