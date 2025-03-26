{{
    config(
        materialized='table'
    )
}}

SELECT
    hour_of_day,
    Area,
    lot_type_description,
    AVG(avg_available_lots) AS avg_available_lots_by_hour,
    COUNT(DISTINCT event_date) AS num_days
FROM {{ ref('rpt_carpark_utilization') }}
GROUP BY
    hour_of_day,
    Area,
    lot_type_description
ORDER BY
    Area,
    lot_type_description,
    hour_of_day