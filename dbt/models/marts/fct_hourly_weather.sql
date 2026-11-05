-- One row per city and local hour. Incremental: each run only processes hours that
-- received new observations (with a 1-day lookback for late-arriving data).
{{ config(
    materialized='incremental',
    unique_key=['city', 'observed_hour_local'],
    incremental_strategy='delete+insert'
) }}

with obs as (
    select *
    from {{ ref('stg_weather_observations') }}
    {% if is_incremental() %}
    where observed_hour_local >= (select max(observed_hour_local) - interval '1 day' from {{ this }})
    {% endif %}
)

select
    city,
    observed_hour_local,
    count(*)                         as observations,
    round(avg(temperature_c), 2)     as temperature_c,
    round(avg(feels_like_c), 2)      as feels_like_c,
    round(avg(humidity_pct), 1)      as humidity_pct,
    round(avg(wind_speed_kmh), 1)    as wind_speed_kmh,
    sum(precip_mm)                   as precip_mm,
    max(ingested_at)                 as last_ingested_at
from obs
group by city, observed_hour_local
