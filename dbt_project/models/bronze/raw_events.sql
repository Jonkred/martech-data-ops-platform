{{ config(materialized='table') }}

SELECT
    id::VARCHAR AS event_id,
    anonymous_id::VARCHAR AS anonymous_id,
    user_id::VARCHAR AS user_id,
    event_type::VARCHAR AS event_name,
    properties::JSON AS properties,
    ingested_at::TIMESTAMP AS ingested_at
FROM public.raw_stream_events