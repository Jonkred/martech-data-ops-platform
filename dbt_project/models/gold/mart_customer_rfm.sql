{{ config(materialized='table') }}

WITH purchases AS (
    SELECT
        resolved_customer_id,
        ingested_at,
        (properties->>'revenue')::NUMERIC AS order_value
    FROM {{ ref('int_identity_resolved') }}
    WHERE event_name = 'order_completed'
)

SELECT
    resolved_customer_id,
    COUNT(1) AS total_orders,
    COALESCE(SUM(order_value), 0) AS total_revenue_ltv,
    MAX(ingested_at) AS last_active_date,
    CASE 
        WHEN COALESCE(SUM(order_value), 0) >= 1000 THEN 'VIP'
        WHEN COUNT(1) >= 3 THEN 'High-Engagement'
        ELSE 'Regular'
    END AS audience_segment,
    CURRENT_TIMESTAMP AS calculated_at
FROM purchases
GROUP BY 1