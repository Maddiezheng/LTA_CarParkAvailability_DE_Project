{{
  config(
    materialized='table'
  )
}}

SELECT
  hour_of_day,
  COALESCE(Area, 'Not Specified') AS Area,
  lot_type_description,
  AVG(AvailableLots) AS avg_available_lots_by_hour,
  COUNT(DISTINCT event_date) AS num_days,
  COUNT(*) AS data_points
FROM 
  {{ ref('stg_carpark_availability') }}
GROUP BY
  hour_of_day,
  COALESCE(Area, 'Not Specified'),
  lot_type_description
