-- Typed, standardized observations with both local and UTC timestamps.
-- New attributes can be pulled from the raw JSONB payload without re-calling the API
-- (uv_index below is read from the payload, not from a landed column).
select
    city,
    country,
    observed_at                                                       as observed_at_local,
    observed_at - make_interval(mins => (utc_offset_h * 60)::int)     as observed_at_utc,
    date_trunc('hour', observed_at)                                   as observed_hour_local,
    temperature_c::numeric                                            as temperature_c,
    feels_like_c::numeric                                             as feels_like_c,
    humidity_pct::numeric                                             as humidity_pct,
    wind_speed_kmh::numeric                                           as wind_speed_kmh,
    coalesce(precip_mm, 0)::numeric                                   as precip_mm,
    nullif(payload -> 'current' ->> 'uv_index', '')::numeric          as uv_index,
    description,
    ingested_at
from {{ source('raw', 'weather_observations') }}
