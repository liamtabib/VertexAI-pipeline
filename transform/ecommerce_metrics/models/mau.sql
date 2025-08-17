-- Monthly Active Users (MAU)
-- Excludes current month to show only complete months

WITH base AS (
  SELECT 
    DATE_TRUNC(DATE(created_at), MONTH) AS month, 
    user_id
  FROM {{ source('thelook_ecommerce', 'events') }}
  WHERE DATE_TRUNC(DATE(created_at), MONTH) < DATE_TRUNC(CURRENT_DATE(), MONTH)
)

SELECT 
  month, 
  COUNT(DISTINCT user_id) AS mau
FROM base
GROUP BY month
ORDER BY month