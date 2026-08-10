import pandas as pd

from src.etl.load_stock_data import transform_stock_data


def test_transform_stock_data_converts_api_response():
    raw_data = [
        {
            "datetime": "2026-08-07 15:55:00",
            "open": "313.22",
            "high": "314.18",
            "low": "313.20",
            "close": "313.30",
            "volume": "2197847",
        }
    ]

    result = transform_stock_data(raw_data, "AAPL")

    assert len(result) == 1
    assert result.loc[0, "symbol"] == "AAPL"

    assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])
    assert pd.api.types.is_numeric_dtype(result["open"])
    assert pd.api.types.is_integer_dtype(result["volume"])

    assert "timestamp_ny" in result.columns
    assert "timestamp_berlin" in result.columns
    assert "created_at" in result.columns

    assert result.loc[0, "close"] == 313.30


def test_transform_stock_data_invalid_numbers():
    raw_data = [
        {
            "datetime": "2026-08-07 15:55:00",
            "open": "abc",
            "high": None,
            "low": "",
            "close": "313.30",
            "volume": "xyz",
        }
    ]

    result = transform_stock_data(raw_data, "AAPL")

    assert pd.isna(result.loc[0, "open"])
    assert pd.isna(result.loc[0, "high"])
    assert pd.isna(result.loc[0, "low"])

    assert result.loc[0, "close"] == 313.30
    assert result.loc[0, "volume"] == 0


def test_transform_stock_data_creates_timezone_columns():
    raw_data = [
        {
            "datetime": "2026-08-07 15:55:00",
            "open": "313.22",
            "high": "314.18",
            "low": "313.20",
            "close": "313.30",
            "volume": "2197847",
        }
    ]

    result = transform_stock_data(raw_data, "AAPL")

    timestamp_ny = result.loc[0, "timestamp_ny"]
    timestamp_berlin = result.loc[0, "timestamp_berlin"]

    assert timestamp_ny.tzinfo is not None
    assert timestamp_berlin.tzinfo is not None

    assert str(timestamp_ny.tzinfo) == "America/New_York"
    assert str(timestamp_berlin.tzinfo) == "Europe/Berlin"

    assert timestamp_ny.hour == 15
    assert timestamp_berlin.hour == 21
