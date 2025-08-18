
  
    

    create or replace table `pipeline-466508`.`ecommerce_analytics`.`platform_share`
      
    
    

    OPTIONS()
    as (
      -- Users by Platform (Android/iOS/Desktop/Web)
-- Assigns each user their dominant platform based on most recent activity

WITH classified AS (
  SELECT
    user_id,
    CASE
      WHEN LOWER(browser) = 'safari' THEN 'iOS'
      WHEN LOWER(browser) = 'chrome' THEN 'Android' -- Assume Chrome is primarily mobile/Android
      WHEN LOWER(browser) = 'firefox' THEN 'Desktop'
      WHEN LOWER(browser) = 'ie' THEN 'Desktop'
      ELSE 'Web'
    END AS platform,
    TIMESTAMP(created_at) AS ts
  FROM `bigquery-public-data`.`thelook_ecommerce`.`events`
),

latest_per_user AS (
  SELECT 
    user_id,
    platform
  FROM (
    SELECT 
      user_id,
      platform,
      ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY ts DESC) AS rn
    FROM classified
  )
  WHERE rn = 1
)

SELECT
  platform,
  COUNT(*) AS users,
  SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER ()) AS share
FROM latest_per_user
GROUP BY platform
ORDER BY users DESC
    );
  