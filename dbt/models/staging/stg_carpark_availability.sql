{{
  config(
    materialized='view'
  )
}}

with tripdata as (
  select *,
    row_number() over(partition by CarParkID, timestamp, LotType) as rn
  from {{ source('raw', 'carpark_availability') }}
  where CarParkID is not null
)

select
  -- Identifier
  {{ dbt_utils.generate_surrogate_key(['CarParkID', 'timestamp', 'LotType']) }} as event_id,
  CarParkID,

  -- Location information
  Area,
  Development,
  Location,
  Latitude,
  Longitude,

  -- Parking lot information
  AvailableLots,
  LotType,
  case safe_cast(LotType as string)
    when 'C' then 'Car'
    when 'H' then 'Heavy Vehicle'
    when 'M' then 'Motorcycle'
    when 'Y' then 'Motorcycle'
    else 'Unknown'
  end as lot_type_description,
  Agency,

  -- Time-related (Singapore Time UTC+8)
  timestamp as event_time,
  CAST(DATE(TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) AS DATE) as event_date,
  EXTRACT(HOUR FROM TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) as hour_of_day,
  EXTRACT(DAYOFWEEK FROM TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) as day_of_week,

  -- Processing time-related
  ingestion_time,
  processing_time,

  -- Additional Information
  case
    when EXTRACT(HOUR FROM TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) between 7 and 9 then 'Morning Peak'
    when EXTRACT(HOUR FROM TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) between 17 and 19 then 'Evening Peak'
    when EXTRACT(HOUR FROM TIMESTAMP_ADD(timestamp, INTERVAL 8 HOUR)) between 6 and 22 then 'Daytime'
    else 'Nighttime'
  end as time_category

from tripdata
where rn = 1

-- Remove default limit
-- dbt build --select <model_name> --vars '{'is_test_run': 'false'}'
{% if var('is_test_run', default=false) %}
  limit 100
{% endif %}
