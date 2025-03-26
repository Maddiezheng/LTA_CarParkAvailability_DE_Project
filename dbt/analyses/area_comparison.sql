-- Compare the availability of parking lots in different areas.
SELECT
  r.Area,
  COUNT(DISTINCT r.CarParkID) as num_carparks,
  AVG(r.avg_available_lots) as avg_available_lots,
  MIN(r.avg_available_lots) as min_avg_available,
  MAX(r.avg_available_lots) as max_avg_available,
  STDDEV(r.avg_available_lots) as std_dev_available
FROM {{ ref('rpt_carpark_utilization') }} r
WHERE r.lot_type_description = 'Car'
GROUP BY r.Area
ORDER BY avg_available_lots ASC