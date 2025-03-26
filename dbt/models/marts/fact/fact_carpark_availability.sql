{{
    config(
        materialized='table'
    )
}}

SELECT
    event_id,
    CarParkID,
    event_time,
    event_date,
    hour_of_day,
    day_of_week,
    AvailableLots,
    LotType,
    lot_type_description,
    time_category,
    ingestion_time,
    processing_time
FROM {{ ref('stg_carpark_availability') }}