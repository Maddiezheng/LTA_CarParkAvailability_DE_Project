-- Analyze the peak hours of the parking lot
WITH daily_patterns AS (
  SELECT
    CarParkID,
    hour_of_day,
    AVG(AvailableLots) as avg_available_lots,
    STDDEV(AvailableLots) as std_dev_available_lots,
    COUNT(*) as data_points
  FROM {{ ref('fact_carpark_availability') }}
  GROUP BY
    CarParkID,
    hour_of_day
),

carpark_ranks AS (
  SELECT
    d.*,
    cp.Area,
    cp.Development,
    RANK() OVER (PARTITION BY hour_of_day ORDER BY avg_available_lots) as rank_by_availability
  FROM daily_patterns d
  JOIN {{ ref('dim_carparks') }} cp ON d.CarParkID = cp.CarParkID
  WHERE data_points > 5  
)

-- Find the busiest parking lot every hour.
SELECT
  hour_of_day,
  Area,
  Development,
  CarParkID,
  avg_available_lots,
  std_dev_available_lots,
  data_points
FROM carpark_ranks
WHERE rank_by_availability <= 5
ORDER BY hour_of_day, rank_by_availability