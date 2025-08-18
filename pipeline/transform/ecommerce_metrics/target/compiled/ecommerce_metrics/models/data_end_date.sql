-- Data freshness indicator
-- Shows the latest date in the events table

SELECT MAX(DATE(created_at)) AS data_end_date
FROM `bigquery-public-data`.`thelook_ecommerce`.`events`