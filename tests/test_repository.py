import pandas as pd
from sqlalchemy import text

from src.database.connection import engine
from src.database.repository import insert_stock_data


def test_insert_stock_data_ignores_duplicates():
    test_data = pd.DataFrame(
        [
            {
                "symbol": "TEST",
                "timestamp": pd.Timestamp("2026-01-01 10:00:00"),
                "timestamp_ny": pd.Timestamp(
                    "2026-01-01 10:00:00",
                    tz="America/New_York",
                ),
                "timestamp_berlin": pd.Timestamp(
                    "2026-01-01 16:00:00",
                    tz="Europe/Berlin",
                ),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
                "created_at": pd.Timestamp("2026-01-01 12:00:00"),
            }
        ]
    )

    # Vorher sicherstellen, dass unser Testdatensatz nicht existiert
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM stock_prices
                WHERE symbol = 'TEST'
                AND timestamp = '2026-01-01 10:00:00'
                """
            )
        )

    first_insert = insert_stock_data(test_data)
    second_insert = insert_stock_data(test_data)

    assert first_insert == 1
    assert second_insert == 0

    # Aufräumen
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM stock_prices
                WHERE symbol = 'TEST'
                AND timestamp = '2026-01-01 10:00:00'
                """
            )
        )
