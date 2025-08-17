WITH funnel_with_percentages AS (
  SELECT 
    step,
    step_name,
    sessions,
    CASE 
      WHEN step = 1 THEN 100.0
      ELSE ROUND(100.0 * sessions / FIRST_VALUE(sessions) OVER (ORDER BY step), 1)
    END AS percentage
  FROM funnel
)
SELECT step, step_name, sessions, percentage
FROM funnel_with_percentages
ORDER BY step