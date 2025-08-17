-- Top 5 percentage increasing and decreasing countries last 30 days
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
  FROM `bigquery-public-data`.`thelook_ecommerce`.`users`
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

with_change AS (
  SELECT 
    country,
    current_users,
    previous_users,
    SAFE_DIVIDE(current_users - previous_users, previous_users) AS pct_change
  FROM period_counts
  WHERE previous_users >= 10  -- Filter for countries with meaningful data
),

ranked AS (
  SELECT 
    country,
    current_users,
    previous_users, 
    pct_change,
    ROW_NUMBER() OVER (ORDER BY pct_change DESC) AS growth_rank,
    ROW_NUMBER() OVER (ORDER BY pct_change ASC) AS decline_rank
  FROM with_change
)

SELECT 
  country,
  current_users,
  previous_users,
  pct_change,
  CASE 
    WHEN growth_rank <= 5 THEN 'Top Growth'
    WHEN decline_rank <= 5 THEN 'Top Decline' 
  END AS trend_type
FROM ranked
WHERE growth_rank <= 5 OR decline_rank <= 5
ORDER BY pct_change DESC