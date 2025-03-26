{{
    config(
        materialized='table',
        partition_by={
            "field": "event_date",
            "data_type": "date",
            "granularity": "day"
        }
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
    time_category
FROM {{ ref('stg_carpark_availability') }}