import pandas as pd
from src.api.stock_api import get_stock_data_time_series, get_stock_data_quote
from src.database.connection import engine
from datetime import datetime
import time

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


def run_etl(symbol):
    data = get_stock_data_time_series(symbol)
    #data_quote = get_stock_data_quote(symbol)

    df = pd.DataFrame(data)

    df["symbol"] = symbol

    df = df.rename(columns={"datetime": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["timestamp_ny"] = df["timestamp"].dt.tz_localize("America/New_York")
    df["timestamp_berlin"] = df["timestamp_ny"].dt.tz_convert("Europe/Berlin")
    df['created_at'] = datetime.today()
    df["open"] = pd.to_numeric(df["open"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["low"] = pd.to_numeric(df["low"], errors="coerce")
    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("int64")

    now = df["timestamp"].max()
    cutoff = now - pd.Timedelta(minutes=50)

    df_filtered = df[df["timestamp"] >= cutoff]


    existing_timestamp = get_stock_prices_sql()
    
    if existing_timestamp is not None:
        # filter out existing values
        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])

        #existing_timestamp_set = set(existing_timestamp["timestamp"])
        #df_final = df_filtered[~df_filtered["timestamp"].isin(existing_timestamp_set)]

        existing_keys = set(zip(existing_timestamp["symbol"], existing_timestamp["timestamp"]))
        df_final = df_filtered[~df_filtered.apply(lambda row: (row["symbol"], row["timestamp"]) in existing_keys, axis=1)]

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
    stock_list = ['QNC', 'AAPL', 'TSLA', 'GOOGL', 'IREN', 'NVDA', 'MU', 'PL', 'QBTS', 'RGTI', 'NTLA', 'CRWV', 'NBIS']
    total = len(stock_list)
    for i, asset in enumerate(stock_list, start=1):
        print(f"[{i}/{total}] Processing {asset}...")
        run_etl(asset)
        if i < total:
            time.sleep(8)

    print("Finished processing all assets.")


if __name__ == "__main__":
    main_stock()
    