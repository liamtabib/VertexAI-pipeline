SELECT 
  country,
  current_users,
  previous_users,
  pct_change,
  trend_type
FROM country_trends
ORDER BY pct_change DESC