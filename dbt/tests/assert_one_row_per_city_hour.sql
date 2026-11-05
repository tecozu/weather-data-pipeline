-- The hourly fact must have exactly one row per city and hour, even after
-- incremental runs with overlapping lookback windows.
select city, observed_hour_local, count(*) as n
from {{ ref('fct_hourly_weather') }}
group by city, observed_hour_local
having count(*) > 1
