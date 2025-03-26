{{
    config(
        materialized='table'
    )
}}

SELECT
    f.event_date,
    f.hour_of_day,
    d.Area,
    d.Development,
    d.CarParkID,
    AVG(f.AvailableLots) AS avg_available_lots,
    COUNT(f.event_id) AS data_points,
    d.LotType,
    d.lot_type_description,
    d.Agency,
    d.Latitude,
    d.Longitude,
    f.time_category
FROM {{ ref('fact_carpark_availability') }} f
JOIN {{ ref('dim_carparks') }} d 
    ON f.CarParkID = d.CarParkID AND f.LotType = d.LotType
GROUP BY 
    f.event_date,
    f.hour_of_day,
    d.Area,
    d.Development,
    d.CarParkID,
    d.LotType,
    d.lot_type_description,
    d.Agency,
    d.Latitude,
    d.Longitude,
    f.time_category