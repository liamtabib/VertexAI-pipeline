-- Monthly Active Users aggregated by quarter for cleaner axis display
-- Shows Q1, Q2, Q3, Q4 for each year

WITH monthly_mau AS (
  SELECT 
    DATE_TRUNC(DATE(created_at), MONTH) AS month, 
    user_id
  FROM `bigquery-public-data`.`thelook_ecommerce`.`events`
  WHERE DATE_TRUNC(DATE(created_at), MONTH) < DATE_TRUNC(CURRENT_DATE(), MONTH)
),

quarterly_base AS (
  SELECT 
    DATE_TRUNC(month, QUARTER) AS quarter,
    user_id
  FROM monthly_mau
)

SELECT 
  quarter, 
  COUNT(DISTINCT user_id) AS mau
FROM quarterly_base
GROUP BY quarter
ORDER BY quarter