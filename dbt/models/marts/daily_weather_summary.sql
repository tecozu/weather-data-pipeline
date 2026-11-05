-- Daily summary per city, the table behind the Superset dashboard.
select
    city,
    observed_hour_local::date                          as day,
    count(*)                                           as hours_observed,
    round(min(temperature_c), 1)                       as min_temperature_c,
    round(max(temperature_c), 1)                       as max_temperature_c,
    round(avg(temperature_c), 1)                       as avg_temperature_c,
    round(avg(humidity_pct), 0)                        as avg_humidity_pct,
    round(max(wind_speed_kmh), 0)                      as max_wind_speed_kmh,
    round(sum(precip_mm), 1)                           as total_precip_mm,
    sum(case when precip_mm > 0 then 1 else 0 end)     as rainy_hours,
    round(count(*) / 24.0, 2)                          as coverage_ratio
from {{ ref('fct_hourly_weather') }}
group by city, observed_hour_local::date
