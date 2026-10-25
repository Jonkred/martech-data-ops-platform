{{ config(materialized='table') }}

WITH resolved_mapping AS (
    -- Mapeia anonymous_id para o user_id conhecido mais recente
    SELECT DISTINCT
        anonymous_id,
        FIRST_VALUE(user_id) OVER(
            PARTITION BY anonymous_id 
            ORDER BY ingested_at DESC 
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS canonical_user_id
    FROM {{ ref('raw_events') }}
    WHERE user_id IS NOT NULL AND user_id != ''
)

SELECT
    e.event_id,
    COALESCE(e.user_id, m.canonical_user_id, e.anonymous_id) AS resolved_customer_id,
    e.event_name,
    e.properties,
    e.ingested_at
FROM {{ ref('raw_events') }} e
LEFT JOIN resolved_mapping m ON e.anonymous_id = m.anonymous_id