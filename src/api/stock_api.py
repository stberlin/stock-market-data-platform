import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()
import time

API_KEY = os.getenv("TWELVE_API_KEY")

def get_stock_data_time_series(symbol="AAPL", max_retries=3):
    for attempt in range(max_retries):
        url = "https://api.twelvedata.com/time_series"

        params = {
            "symbol": symbol,
            "interval": "5min",
            "outputsize": 100,
            "apikey": API_KEY
        }

        response = requests.get(url, params=params)
        data = response.json()
        
        # success
        if "values" in data:
            return data["values"]

        # rate limit error
        if data.get("code") == 429:
            print(f"[RATE LIMIT] Hit for {symbol}, sleeping 60s...")
            time.sleep(60)
            continue

        # other API error
        print(f"[ERROR] {symbol}: {data}")
        return None

    print(f"[FAILED] {symbol} after retries")
    return None 
        # try:
        #     return data["values"]
        # except KeyError:
        #     print(f"Error: 'values' not found in response: {data}")
        #     return None
        
        # except requests.exceptions.RequestException as e:
        #     print(f"Request failed: {e}")
        #     return None

        # except Exception as e:
        #     print(f"Unexpected error: {e}")
        #     return None


def get_stock_data_quote(symbol="AAPL"):
    url = "https://api.twelvedata.com/quote"

    params = {
        "symbol": symbol,
        "interval": "5min",
        "outputsize": 100,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["values"]