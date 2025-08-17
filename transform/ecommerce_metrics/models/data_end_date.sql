-- Data freshness indicator
-- Shows the latest date in the events table

SELECT MAX(DATE(created_at)) AS data_end_date
FROM {{ source('thelook_ecommerce', 'events') }}