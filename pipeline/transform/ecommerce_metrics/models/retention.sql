-- Monthly Cohort Retention Analysis
-- Shows retention rates for the 5 most recent cohorts

WITH cohort AS (
  SELECT 
    id AS user_id, 
    DATE_TRUNC(DATE(created_at), MONTH) AS cohort_month
  FROM {{ source('thelook_ecommerce', 'users') }}
  WHERE DATE_TRUNC(DATE(created_at), MONTH) < DATE_TRUNC(CURRENT_DATE(), MONTH)
),

activity AS (
  SELECT DISTINCT 
    user_id, 
    DATE_TRUNC(DATE(created_at), MONTH) AS active_month
  FROM {{ source('thelook_ecommerce', 'events') }}
),

-- Ensure all cohort members are counted as 100% retained in month 0
cohort_month_zero AS (
  SELECT 
    cohort_month,
    0 AS age_month,
    COUNT(*) AS active_users
  FROM cohort
  GROUP BY cohort_month
),

-- Calculate retention for months 1+
matrix_future AS (
  SELECT 
    c.cohort_month,
    DATE_DIFF(a.active_month, c.cohort_month, MONTH) AS age_month,
    COUNT(DISTINCT a.user_id) AS active_users
  FROM cohort c
  JOIN activity a USING (user_id)
  WHERE DATE_DIFF(a.active_month, c.cohort_month, MONTH) > 0
  GROUP BY c.cohort_month, age_month
),

-- Combine month 0 (100% retention) with future months
matrix AS (
  SELECT cohort_month, age_month, active_users FROM cohort_month_zero
  UNION ALL
  SELECT cohort_month, age_month, active_users FROM matrix_future
),

sizes AS (
  SELECT 
    cohort_month, 
    COUNT(*) AS cohort_size
  FROM cohort
  GROUP BY cohort_month
),

rates AS (
  SELECT 
    m.cohort_month, 
    m.age_month, 
    m.active_users, 
    s.cohort_size,
    SAFE_DIVIDE(m.active_users, s.cohort_size) AS retention_rate
  FROM matrix m
  JOIN sizes s USING (cohort_month)
),

ranked AS (
  SELECT 
    cohort_month, 
    cohort_size,
    DENSE_RANK() OVER (ORDER BY cohort_month DESC) AS rnk
  FROM sizes
)

SELECT
  r.cohort_month,
  CONCAT(
    CAST(EXTRACT(YEAR FROM r.cohort_month) AS STRING), 
    '-', 
    LPAD(CAST(EXTRACT(MONTH FROM r.cohort_month) AS STRING), 2, '0')
  ) AS cohort_label,
  rates.age_month,
  rates.retention_rate
FROM rates
JOIN ranked r USING (cohort_month)
WHERE r.rnk <= 4
  AND r.cohort_size >= 50  -- Filter small cohorts
  AND rates.age_month <= 4  -- Limit to 0-4 months (5 data points)
ORDER BY cohort_month, age_month