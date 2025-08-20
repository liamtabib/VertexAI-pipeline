#!/usr/bin/env python3
"""
Test the corrected new user registration funnel query
"""

import os
from google.cloud import bigquery

def test_original_query():
    """Test the original query logic"""
    
    query = """
    WITH new_user_registrations AS (
      SELECT
        COUNT(DISTINCT id) AS new_user_registrations
      FROM `bigquery-public-data.thelook_ecommerce.users`
      WHERE DATE(created_at) BETWEEN 
        DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 60 DAY) AND 
        DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 30 DAY)
    ),

    new_users_who_viewed_products AS (
      SELECT
        COUNT(DISTINCT events.user_id) AS users_who_viewed_products
      FROM `bigquery-public-data.thelook_ecommerce.events` events
      JOIN `bigquery-public-data.thelook_ecommerce.users` users
        ON events.user_id = users.id
      WHERE 
        events.event_type = 'product'
        AND DATE(users.created_at) BETWEEN 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 60 DAY) AND 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 30 DAY)
        AND DATE(events.created_at) >= DATE(users.created_at)
    ),

    new_users_who_added_to_cart AS (
      SELECT
        COUNT(DISTINCT events.user_id) AS users_who_added_to_cart
      FROM `bigquery-public-data.thelook_ecommerce.events` events
      JOIN `bigquery-public-data.thelook_ecommerce.users` users
        ON events.user_id = users.id
      WHERE 
        events.event_type = 'cart'
        AND DATE(users.created_at) BETWEEN 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 60 DAY) AND 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 30 DAY)
        AND DATE(events.created_at) >= DATE(users.created_at)
    ),

    new_users_who_purchased AS (
      SELECT
        COUNT(DISTINCT events.user_id) AS users_who_purchased
      FROM `bigquery-public-data.thelook_ecommerce.events` events
      JOIN `bigquery-public-data.thelook_ecommerce.users` users
        ON events.user_id = users.id
      WHERE 
        events.event_type = 'purchase'
        AND DATE(users.created_at) BETWEEN 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 60 DAY) AND 
          DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 30 DAY)
        AND DATE(events.created_at) >= DATE(users.created_at)
    ),

    counts AS (
      SELECT
        r.new_user_registrations AS s1,
        v.users_who_viewed_products AS s2, 
        c.users_who_added_to_cart AS s3,
        p.users_who_purchased AS s4
      FROM new_user_registrations r
      CROSS JOIN new_users_who_viewed_products v
      CROSS JOIN new_users_who_added_to_cart c  
      CROSS JOIN new_users_who_purchased p
    )

    SELECT * FROM (
      SELECT 1 AS step, 'New User Registration' AS step_name, s1 AS users FROM counts UNION ALL
      SELECT 2 AS step, 'Product View' AS step_name, s2 AS users FROM counts UNION ALL
      SELECT 3 AS step, 'Add to Cart' AS step_name, s3 AS users FROM counts UNION ALL
      SELECT 4 AS step, 'Purchase' AS step_name, s4 AS users FROM counts
    )
    ORDER BY step
    """
    
    return query

def test_corrected_query():
    """Test the corrected query logic"""
    
    query = """
    WITH new_user_registrations AS (
      SELECT
        id AS user_id,
        created_at AS registration_date
      FROM `bigquery-public-data.thelook_ecommerce.users`
      WHERE DATE(created_at) BETWEEN 
        DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 60 DAY) AND 
        DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 30 DAY)
    ),

    -- Get all events for new users that occurred after their registration
    new_user_events AS (
      SELECT
        nur.user_id,
        nur.registration_date,
        e.event_type,
        e.created_at AS event_date,
        -- Add sequence number to identify first occurrence of each event type
        ROW_NUMBER() OVER (
          PARTITION BY nur.user_id, e.event_type 
          ORDER BY e.created_at
        ) AS event_sequence
      FROM new_user_registrations nur
      JOIN `bigquery-public-data.thelook_ecommerce.events` e
        ON e.user_id = nur.user_id
      WHERE DATE(e.created_at) >= DATE(nur.registration_date)
        AND e.event_type IN ('product', 'cart', 'purchase')
    ),

    -- Get first occurrence of each event type per user
    first_events AS (
      SELECT
        user_id,
        registration_date,
        event_type,
        event_date
      FROM new_user_events
      WHERE event_sequence = 1
    ),

    -- Pivot to get one row per user with their first event dates
    user_funnel_steps AS (
      SELECT
        user_id,
        registration_date,
        MIN(CASE WHEN event_type = 'product' THEN event_date END) AS first_product_view,
        MIN(CASE WHEN event_type = 'cart' THEN event_date END) AS first_add_to_cart,
        MIN(CASE WHEN event_type = 'purchase' THEN event_date END) AS first_purchase
      FROM first_events
      GROUP BY user_id, registration_date
    ),

    -- Create funnel flags ensuring proper sequence
    user_funnel_flags AS (
      SELECT
        user_id,
        registration_date,
        first_product_view,
        first_add_to_cart,
        first_purchase,
        
        -- Step 1: User viewed a product
        CASE WHEN first_product_view IS NOT NULL THEN 1 ELSE 0 END AS viewed_product,
        
        -- Step 2: User viewed product AND added to cart (and cart came after or same day as product view)
        CASE 
          WHEN first_product_view IS NOT NULL 
           AND first_add_to_cart IS NOT NULL 
           AND first_add_to_cart >= first_product_view 
          THEN 1 ELSE 0 
        END AS added_to_cart,
        
        -- Step 3: User completed steps 1&2 AND purchased (and purchase came after or same day as cart)
        CASE 
          WHEN first_product_view IS NOT NULL 
           AND first_add_to_cart IS NOT NULL 
           AND first_purchase IS NOT NULL
           AND first_add_to_cart >= first_product_view 
           AND first_purchase >= first_add_to_cart
          THEN 1 ELSE 0 
        END AS purchased
      FROM user_funnel_steps
    ),

    -- Calculate final counts
    funnel_counts AS (
      SELECT
        COUNT(*) AS new_user_registrations,
        SUM(viewed_product) AS users_who_viewed_products,
        SUM(added_to_cart) AS users_who_added_to_cart,
        SUM(purchased) AS users_who_purchased
      FROM new_user_registrations nur
      LEFT JOIN user_funnel_flags uff ON nur.user_id = uff.user_id
    )

    -- Final output with step-by-step breakdown
    SELECT * FROM (
      SELECT 1 AS step, 'New User Registration' AS step_name, new_user_registrations AS users FROM funnel_counts 
      UNION ALL
      SELECT 2 AS step, 'Product View' AS step_name, users_who_viewed_products AS users FROM funnel_counts 
      UNION ALL
      SELECT 3 AS step, 'Add to Cart' AS step_name, users_who_added_to_cart AS users FROM funnel_counts 
      UNION ALL
      SELECT 4 AS step, 'Purchase' AS step_name, users_who_purchased AS users FROM funnel_counts
    )
    ORDER BY step
    """
    
    return query

def run_queries():
    """Run both queries and compare results"""
    
    # Check if BigQuery credentials are available
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and not os.getenv('GCP_PROJECT'):
        print("BigQuery credentials not available. Showing query analysis only.")
        print("\n" + "="*60)
        print("ORIGINAL QUERY ANALYSIS:")
        print("="*60)
        print(test_original_query())
        print("\n" + "="*60)
        print("CORRECTED QUERY ANALYSIS:")
        print("="*60)
        print(test_corrected_query())
        return
    
    try:
        client = bigquery.Client()
        
        print("Running original query...")
        original_results = client.query(test_original_query()).to_dataframe()
        
        print("Running corrected query...")
        corrected_results = client.query(test_corrected_query()).to_dataframe()
        
        print("\n" + "="*60)
        print("ORIGINAL FUNNEL RESULTS:")
        print("="*60)
        print(original_results)
        
        # Calculate conversion rates for original
        print("\nOriginal Conversion Rates:")
        for i in range(1, len(original_results)):
            prev_users = original_results.iloc[i-1]['users']
            curr_users = original_results.iloc[i]['users']
            conversion_rate = (curr_users / prev_users * 100) if prev_users > 0 else 0
            print(f"{original_results.iloc[i-1]['step_name']} → {original_results.iloc[i]['step_name']}: {conversion_rate:.1f}% ({curr_users:,} / {prev_users:,})")
        
        print("\n" + "="*60)
        print("CORRECTED FUNNEL RESULTS:")
        print("="*60)
        print(corrected_results)
        
        # Calculate conversion rates for corrected
        print("\nCorrected Conversion Rates:")
        for i in range(1, len(corrected_results)):
            prev_users = corrected_results.iloc[i-1]['users']
            curr_users = corrected_results.iloc[i]['users']
            conversion_rate = (curr_users / prev_users * 100) if prev_users > 0 else 0
            print(f"{corrected_results.iloc[i-1]['step_name']} → {corrected_results.iloc[i]['step_name']}: {conversion_rate:.1f}% ({curr_users:,} / {prev_users:,})")
        
    except Exception as e:
        print(f"Error running BigQuery: {e}")

if __name__ == "__main__":
    run_queries()