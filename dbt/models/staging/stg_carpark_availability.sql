{{
    config(
        materialized='view'
    )
}}

with tripdata as 
(
  select *,
    row_number() over(partition by CarParkID, timestamp) as rn
  from {{ source('raw', 'carpark_availability') }}
  where CarParkID is not null 
)
select
    -- Identifier
    {{ dbt_utils.generate_surrogate_key(['CarParkID', 'timestamp']) }} as event_id,
    CarParkID,
    
    -- Location information
    Area,
    Development,
    cast(Latitude as numeric) as Latitude,
    cast(Longitude as numeric) as Longitude,
    
    -- Parking lot information
    cast(AvailableLots as integer) as AvailableLots,
    LotType,
    {{ get_lot_type_description('LotType') }} as lot_type_description,
    Agency,
    
    -- Time-related
    cast(timestamp as timestamp) as event_time,
    cast(extract(date from timestamp) as date) as event_date,
    extract(hour from timestamp) as hour_of_day,
    extract(dayofweek from timestamp) as day_of_week,
    
    -- Additional Information
    case
        when extract(hour from timestamp) between 7 and 9 then 'Morning Peak'
        when extract(hour from timestamp) between 17 and 19 then 'Evening Peak'
        when extract(hour from timestamp) between 6 and 22 then 'Daytime'
        else 'Nighttime'
    end as time_category
from tripdata
where rn = 1

-- dbt build --select <model_name> --vars '{'is_test_run': 'false'}'
{% if var('is_test_run', default=true) %}
  limit 100
{% endif %}