"""Fetch current weather for a list of cities and land it in Postgres, idempotently.

Design:
* the raw API payload is stored as JSONB next to the parsed columns, so models can be
  rebuilt or extended later without calling the API again (replayability);
* (city, observed_at) is unique and inserts use ON CONFLICT DO NOTHING, so retries
  and overlapping runs never create duplicates;
* configuration comes from environment variables, nothing is hard-coded;
* WEATHER_API_MOCK=1 generates deterministic payloads (CI, local dev, no API quota).
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import requests

log = logging.getLogger("weather_ingestion")

API_URL = "http://api.weatherstack.com/current"
DDL = """
create schema if not exists raw;
create table if not exists raw.weather_observations (
    city            text        not null,
    country         text,
    observed_at     timestamp   not null,   -- local time at the city
    utc_offset_h    numeric,
    temperature_c   numeric,
    feels_like_c    numeric,
    humidity_pct    numeric,
    wind_speed_kmh  numeric,
    precip_mm       numeric,
    description     text,
    payload         jsonb       not null,
    ingested_at     timestamptz not null default now(),
    primary key (city, observed_at)
);
"""
INSERT = """
insert into raw.weather_observations
    (city, country, observed_at, utc_offset_h, temperature_c, feels_like_c,
     humidity_pct, wind_speed_kmh, precip_mm, description, payload)
values (%(city)s, %(country)s, %(observed_at)s, %(utc_offset_h)s, %(temperature_c)s,
        %(feels_like_c)s, %(humidity_pct)s, %(wind_speed_kmh)s, %(precip_mm)s,
        %(description)s, %(payload)s)
on conflict (city, observed_at) do nothing
"""


@dataclass(frozen=True)
class Settings:
    cities: list[str]
    api_key: str | None
    mock: bool
    db: dict

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            cities=[c.strip() for c in os.getenv("WEATHER_CITIES", "Rio de Janeiro").split(";")],
            api_key=os.getenv("WEATHER_API_KEY"),
            mock=os.getenv("WEATHER_API_MOCK", "0") == "1",
            db={
                "host": os.getenv("POSTGRES_HOST", "db"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "dbname": os.getenv("POSTGRES_DB", "weather"),
                "user": os.getenv("POSTGRES_USER", "weather"),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
            },
        )


class PayloadError(ValueError):
    """The API answered, but not with a usable observation (e.g. quota or bad key)."""


def parse_observation(payload: dict) -> dict:
    """Weatherstack payload -> row for raw.weather_observations. Pure: easy to unit test."""
    if "error" in payload:
        err = payload["error"]
        raise PayloadError(f"API error {err.get('code')}: {err.get('info')}")
    try:
        loc, cur = payload["location"], payload["current"]
        return {
            "city": loc["name"],
            "country": loc.get("country"),
            "observed_at": datetime.strptime(loc["localtime"], "%Y-%m-%d %H:%M"),
            "utc_offset_h": float(loc["utc_offset"]),
            "temperature_c": cur.get("temperature"),
            "feels_like_c": cur.get("feelslike"),
            "humidity_pct": cur.get("humidity"),
            "wind_speed_kmh": cur.get("wind_speed"),
            "precip_mm": cur.get("precip"),
            "description": (cur.get("weather_descriptions") or [None])[0],
            "payload": json.dumps(payload),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PayloadError(f"unexpected payload shape: {exc}") from exc


def mock_payload(city: str, now: datetime, seed: int | None = None) -> dict:
    """Plausible, deterministic payload for a city and hour (no network)."""
    key = f"{city}|{now:%Y%m%d%H}".encode()
    rng = random.Random(seed if seed is not None else zlib.crc32(key))  # stable across runs
    hour = now.replace(minute=0, second=0, microsecond=0)
    temp = round(22 + 6 * rng.random() - 4 * (hour.hour < 7), 1)
    return {
        "location": {
            "name": city,
            "country": "Brazil",
            "localtime": hour.strftime("%Y-%m-%d %H:%M"),
            "utc_offset": "-3.0",
        },
        "current": {
            "temperature": temp,
            "feelslike": round(temp + rng.uniform(-1, 3), 1),
            "humidity": rng.randint(45, 95),
            "wind_speed": rng.randint(0, 30),
            "precip": round(max(0.0, rng.gauss(0, 2)), 1),
            "weather_descriptions": [
                rng.choice(["Sunny", "Partly cloudy", "Overcast", "Light rain"])
            ],
        },
    }


def fetch(city: str, api_key: str, retries: int = 3, backoff_s: float = 2.0) -> dict:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(API_URL, params={"access_key": api_key, "query": city}, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = backoff_s * 2 ** (attempt - 1)
            log.warning("fetch %s failed (%s), retry %d in %.0fs", city, exc, attempt, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def run(settings: Settings | None = None, now: datetime | None = None) -> int:
    """Fetch every configured city and insert new observations. Returns rows inserted."""
    import psycopg2  # imported here so parsing/mocking can be tested without a database

    settings = settings or Settings.from_env()
    if not settings.mock and not settings.api_key:
        raise RuntimeError("WEATHER_API_KEY is not set (or set WEATHER_API_MOCK=1)")
    now = now or datetime.now(UTC) - timedelta(hours=3)

    rows = []
    for city in settings.cities:
        payload = mock_payload(city, now) if settings.mock else fetch(city, settings.api_key)
        rows.append(parse_observation(payload))

    with psycopg2.connect(**settings.db) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        inserted = 0
        for row in rows:
            cur.execute(INSERT, row)
            inserted += cur.rowcount
    log.info("%d cities fetched, %d new observations", len(rows), inserted)
    return inserted


def backfill_mock(hours: int, settings: Settings | None = None) -> int:
    """Load `hours` of mock history (used by CI and for a quick local demo)."""
    settings = settings or Settings.from_env()
    settings = Settings(settings.cities, settings.api_key, True, settings.db)
    end = datetime(2026, 7, 31, 23)
    return sum(run(settings, end - timedelta(hours=h)) for h in range(hours))


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) > 2 and sys.argv[1] == "backfill-mock":
        print(backfill_mock(int(sys.argv[2])))
    else:
        print(run())
