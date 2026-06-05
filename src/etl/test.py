import pandas as pd
from src.api.stock_api import get_stock_data
#from src.database.connection import engine

def run_etl(symbol="AAPL"):
    data = get_stock_data(symbol)

    df = pd.DataFrame(data)

    df["symbol"] = symbol

    # umbenennen für DB
    df = df.rename(columns={
        "datetime": "timestamp"
    })

    df.to_sql(
        "stock_prices",
        engine,
        if_exists="append",
        index=False
    )

    print(f"{len(df)} rows inserted for {symbol}")

def main():
    run_etl(symbol="AAPL")


if __name__ == "__main__":
    main()