import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()

API_KEY = os.getenv("TWELVE_API_KEY")

def get_stock_data(symbol="AAPL"):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "5min",
        "outputsize": 100,
        "apikey": API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["values"]