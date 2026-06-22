from src.database.connection import engine
import pandas as pd
from datetime import datetime

def check_price_drop(drop_threshold=5, lookback_minutes=30):
    query = f"""
    SELECT *
    FROM (
        SELECT
            symbol,
            MIN(timestamp) AS start_time,
            MAX(timestamp) AS end_time,
            (ARRAY_AGG(close ORDER BY timestamp ASC))[1] AS start_price,
            (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS end_price,
            ((ARRAY_AGG(close ORDER BY timestamp DESC))[1] -
             (ARRAY_AGG(close ORDER BY timestamp ASC))[1]) /
             (ARRAY_AGG(close ORDER BY timestamp ASC))[1] * 100 AS change_pct
        FROM stock_prices
        WHERE timestamp >= (
            SELECT MAX(timestamp) - INTERVAL '{lookback_minutes} minutes'
            FROM stock_prices
        )
        GROUP BY symbol
    ) t
    WHERE change_pct <= {drop_threshold};
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        print("No alerts")
        return None

    print("ALERTS FOUND:")
    df['alert_type'] = f"DROP_{drop_threshold}_PERCENT_IN_{lookback_minutes}_MINUTES"
    df['created_at'] = datetime.today()
    df.to_sql(
        "stock_alerts",
        engine,
        if_exists="append",
        index=False
    )

def main_alert():
    check_price_drop(drop_threshold=-5, lookback_minutes=30)

if __name__ == "__main__":
    main_alert()
    