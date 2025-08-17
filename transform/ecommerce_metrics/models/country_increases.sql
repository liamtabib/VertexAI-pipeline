-- Top 5 countries with biggest increases in last 30 days
-- Compares current 30-day period vs previous 30-day period

WITH periods AS (
  SELECT 
    CASE 
      WHEN country = 'Brasil' THEN 'Brazil'
      WHEN country = 'United States' THEN 'United States of America'
      WHEN country = 'Deutschland' THEN 'Germany'
      ELSE country
    END AS country,
    CASE 
      WHEN DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN 'current'
      WHEN DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY) 
       AND DATE(created_at) < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) THEN 'previous'
      ELSE 'other'
    END AS period
  FROM {{ source('thelook_ecommerce', 'users') }}
  WHERE country IS NOT NULL
    AND DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
),

period_counts AS (
  SELECT 
    country,
    COUNTIF(period = 'current') AS current_users,
    COUNTIF(period = 'previous') AS previous_users
  FROM periods
  WHERE period IN ('current', 'previous')
  GROUP BY country
  HAVING previous_users > 0  -- Avoid division by zero
),

total_users AS (
  SELECT 
    CASE 
      WHEN country = 'Brasil' THEN 'Brazil'
      WHEN country = 'United States' THEN 'United States of America'
      WHEN country = 'Deutschland' THEN 'Germany'
      ELSE country
    END AS country,
    COUNT(*) AS total_user_base
  FROM {{ source('thelook_ecommerce', 'users') }}
  WHERE country IS NOT NULL
  GROUP BY country
),

with_change AS (
  SELECT 
    p.country,
    p.current_users AS new_users_last_30_days,
    t.total_user_base,
    SAFE_DIVIDE(p.current_users, t.total_user_base) * 100 AS increase_percentage
  FROM period_counts p
  JOIN total_users t ON p.country = t.country
  WHERE p.current_users > 0  -- Only countries with new users
    AND t.total_user_base >= 50  -- Filter for countries with meaningful user base
)

SELECT 
  country,
  new_users_last_30_days AS increase_number,
  increase_percentage
FROM with_change
ORDER BY increase_percentage DESC
LIMIT 3