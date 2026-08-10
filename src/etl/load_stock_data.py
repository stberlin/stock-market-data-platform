import time
from datetime import datetime

import pandas as pd

from src.api.stock_api import get_stock_data_time_series
from src.config import STOCK_SYMBOLS, SYMBOL_REQUEST_DELAY_SECONDS
from src.database.connection import engine

def get_stock_prices_sql():
    query = """
    SELECT timestamp, symbol
    FROM stock_prices;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        print("No comparison data to return")
        return None

    print("Comparison data available")
    return df


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
        print(f"No API data returned for {symbol}")
        return

    df = transform_stock_data(data, symbol)

    now = df["timestamp"].max()
    cutoff = now - pd.Timedelta(minutes=60)

    df_filtered = df[df["timestamp"] >= cutoff].copy()


    existing_timestamp = get_stock_prices_sql()

    if existing_timestamp is not None:
        # filter out existing values
        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])

        #existing_keys = set(zip(existing_timestamp["symbol"], existing_timestamp["timestamp"]))
        #df_final = df_filtered[~df_filtered.apply(lambda row: (row["symbol"], row["timestamp"]) in existing_keys, axis=1)].copy()
        df_final = df_filtered.merge(
            existing_timestamp,
            on=["symbol", "timestamp"],
            how="left",
            indicator=True,
        )

        df_final = (
            df_final[df_final["_merge"] == "left_only"]
            .drop(columns="_merge")
        )
    else:
        df_final = df_filtered.copy()

    if not df_final.empty:
        df_final.to_sql(
            "stock_prices",
            engine,
            if_exists="append",
            index=False
        )
        print(f"{len(df_final)} rows inserted for {symbol}")
    else:
        print(f"No data to update for {symbol}")

def main_stock():
    #stock_list = ['QNC', 'AAPL', 'TSLA', 'GOOGL', 'IREN', 'NVDA', 'MU', 'PL', 'QBTS', 'RGTI', 'NTLA', 'CRWV', 'NBIS']
    total = len(STOCK_SYMBOLS)
    for i, asset in enumerate(STOCK_SYMBOLS, start=1):
        print(f"[{i}/{total}] Processing {asset}...")
        run_etl(asset)
        if i < total:
            time.sleep(SYMBOL_REQUEST_DELAY_SECONDS)

    print("Finished processing all assets.")


if __name__ == "__main__":
    main_stock()
