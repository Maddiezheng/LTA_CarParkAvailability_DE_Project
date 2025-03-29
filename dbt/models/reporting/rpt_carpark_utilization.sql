{{
  config(
    materialized='table'
  )
}}

WITH latest_data AS (
  SELECT
    CarParkID,
    Area,
    Development,
    Latitude,
    Longitude,
    LotType,
    lot_type_description,
    Agency,
    AvailableLots,
    event_time,
    event_date,
    hour_of_day,
    time_category,
    ROW_NUMBER() OVER(PARTITION BY CarParkID, LotType ORDER BY event_time DESC) AS rn
  FROM {{ ref('stg_carpark_availability') }}
),

aggregated_data AS (
  SELECT
    CarParkID,
    COALESCE(Area, 'Not Specified') AS Area,
    Development,
    Latitude,
    Longitude,
    LotType,
    lot_type_description,
    Agency,
    AVG(AvailableLots) AS avg_available_lots,
    COUNT(*) AS data_points,
    MAX(event_date) AS max_date,
    MAX(hour_of_day) AS max_hour,
    STRING_AGG(DISTINCT time_category, ', ') AS time_categories
  FROM {{ ref('stg_carpark_availability') }}
  GROUP BY
    CarParkID,
    COALESCE(Area, 'Not Specified'),
    Development,
    Latitude,
    Longitude,
    LotType,
    lot_type_description,
    Agency
)

SELECT
  a.*,
  l.AvailableLots AS current_available_lots,
  l.time_category AS current_time_category,
  l.event_date AS current_date,
  l.hour_of_day AS current_hour
FROM
  aggregated_data a
LEFT JOIN
  latest_data l
ON
  a.CarParkID = l.CarParkID
  AND a.LotType = l.LotType
  AND l.rn = 1
