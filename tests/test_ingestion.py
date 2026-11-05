import json
from datetime import datetime

import pytest

from weather_ingestion import PayloadError, mock_payload, parse_observation

REAL_SHAPE = {
    "location": {"name": "Rio De Janeiro", "country": "Brazil",
                 "localtime": "2025-08-03 16:01", "utc_offset": "-3.0"},
    "current": {"temperature": 23, "feelslike": 25, "humidity": 69, "wind_speed": 11,
                "precip": 0, "weather_descriptions": ["Sunny"], "uv_index": 1},
}  # fmt: skip


def test_parse_real_payload_shape():
    row = parse_observation(REAL_SHAPE)
    assert row["city"] == "Rio De Janeiro"
    assert row["observed_at"] == datetime(2025, 8, 3, 16, 1)
    assert row["utc_offset_h"] == -3.0
    assert row["temperature_c"] == 23
    assert row["description"] == "Sunny"
    assert json.loads(row["payload"]) == REAL_SHAPE  # raw payload kept for replay


def test_api_errors_are_not_silently_inserted():
    # Weatherstack returns HTTP 200 with an "error" object when the quota is exceeded
    quota = {"success": False, "error": {"code": 104, "info": "usage limit reached"}}
    with pytest.raises(PayloadError, match="104"):
        parse_observation(quota)


def test_malformed_payload_raises():
    with pytest.raises(PayloadError):
        parse_observation({"location": {"name": "X"}})


def test_mock_is_deterministic_and_parseable():
    t = datetime(2026, 7, 31, 14, 37)
    a, b = mock_payload("Recife", t), mock_payload("Recife", t)
    assert a == b
    row = parse_observation(a)
    assert row["observed_at"] == datetime(2026, 7, 31, 14, 0)  # truncated to the hour
    assert 0 <= row["humidity_pct"] <= 100


def test_mock_differs_between_cities():
    t = datetime(2026, 7, 31, 14)
    assert mock_payload("Recife", t) != mock_payload("Curitiba", t)
