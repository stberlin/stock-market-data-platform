import pandas as pd
from src.api.stock_api import get_stock_data
from src.database.connection import engine
from datetime import datetime

def get_stock_prices_sql():
    query = """
    SELECT timestamp
    FROM stock_prices;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        print("No data to return")
        return None

    print("Data available:")
    return df


def run_etl(symbol="AAPL"):
    data = get_stock_data(symbol)

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
    cutoff = now - pd.Timedelta(minutes=30)

    df_filtered = df[df["timestamp"] >= cutoff]


    existing_timestamp = get_stock_prices_sql()
    
    if existing_timestamp is not None:
        # filter out existing values
        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"])

        existing_timestamp_set = set(existing_timestamp["timestamp"])

        df_final = df_filtered[~df_filtered["timestamp"].isin(existing_timestamp_set)]
    else:
        df_final = df_filtered.copy()

    df_final.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )

    print(f"{len(df_final)} rows inserted for {symbol}")


if __name__ == "__main__":
    run_etl("AAPL")