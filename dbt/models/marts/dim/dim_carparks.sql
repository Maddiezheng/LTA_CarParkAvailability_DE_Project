{{
    config(
        materialized='table'
    )
}}

WITH ranked_carparks AS (
    SELECT 
        CarParkID,
        Area,
        Development,
        Latitude,
        Longitude,
        LotType,
        lot_type_description,
        Agency,
        event_time,
        ROW_NUMBER() OVER (PARTITION BY CarParkID, LotType ORDER BY event_time DESC) AS rn
    FROM {{ ref('stg_carpark_availability') }}
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['CarParkID', 'LotType']) }} as carpark_lot_key,
    CarParkID,
    Area,
    Development,
    Latitude,
    Longitude,
    LotType,
    lot_type_description,
    Agency
FROM ranked_carparks
WHERE rn = 1