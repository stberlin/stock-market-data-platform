import time
from datetime import datetime
import pandas as pd

from src.api.stock_api import get_stock_data_time_series
from src.config import STOCK_SYMBOLS, SYMBOL_REQUEST_DELAY_SECONDS
from src.database.connection import engine

from sqlalchemy.dialects.postgresql import insert
from src.database.repository import insert_stock_data
from src.logging_config import get_logger

logger = get_logger(__name__)


def transform_stock_data(data, symbol):
    df = pd.DataFrame(data)

    df["symbol"] = symbol

    df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["timestamp_ny"] = df["timestamp"].dt.tz_localize("America/New_York")
    df["timestamp_berlin"] = df["timestamp_ny"].dt.tz_convert("Europe/Berlin")

    df["created_at"] = datetime.now()

    numeric_columns = ["open", "close", "low", "high"]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["volume"] = (
        pd.to_numeric(df["volume"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    return df


def run_etl(symbol):
    data = get_stock_data_time_series(symbol)

    if not data:
        logger.info("No new data to update for %s", symbol)
        return

    df = transform_stock_data(data, symbol)

    now = df["timestamp"].max()
    cutoff = now - pd.Timedelta(minutes=60)

    df_filtered = df[df["timestamp"] >= cutoff].copy()

    inserted_rows = insert_stock_data(df_filtered)

    if inserted_rows > 0:
        logger.info("%s rows inserted for %s", inserted_rows, symbol)
    else:
        logger.info("No new data to update for %s", symbol)


def main_stock():
    total = len(STOCK_SYMBOLS)
    for i, asset in enumerate(STOCK_SYMBOLS, start=1):
        logger.info("[%s/%s] Processing %s", i, total, asset)
        run_etl(asset)
        if i < total:
            time.sleep(SYMBOL_REQUEST_DELAY_SECONDS)

    logger.info("Finished processing all assets.")


if __name__ == "__main__":
    main_stock()
