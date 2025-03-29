{{
  config(
    materialized='table'
  )
}}

SELECT
  time_category,
  COALESCE(Area, 'Not Specified') AS Area,
  lot_type_description,
  AVG(AvailableLots) AS avg_available_lots,
  COUNT(*) AS data_points
FROM 
  {{ ref('stg_carpark_availability') }}
GROUP BY
  time_category,
  COALESCE(Area, 'Not Specified'),
  lot_type_description
