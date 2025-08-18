
  
    

    create or replace table `pipeline-466508`.`ecommerce_analytics`.`users_by_country`
      
    
    

    OPTIONS()
    as (
      -- Users by Country
-- Counts users by country, filtering out nulls and standardizing names for GeoJSON compatibility

WITH standardized_countries AS (
  SELECT 
    CASE 
      WHEN country = 'Brasil' THEN 'Brazil'
      WHEN country = 'United States' THEN 'United States of America'
      WHEN country = 'Deutschland' THEN 'Germany'
      ELSE country
    END AS country,
    id
  FROM `bigquery-public-data`.`thelook_ecommerce`.`users`
  WHERE country IS NOT NULL
)

SELECT 
  country, 
  COUNT(*) AS users
FROM standardized_countries
GROUP BY country
ORDER BY users DESC
    );
  