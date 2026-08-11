import os
import time

import requests
from dotenv import load_dotenv

from src.config import (
    API_INTERVAL,
    API_MAX_RETRIES,
    API_OUTPUT_SIZE,
    RATE_LIMIT_SLEEP_SECONDS,
)

load_dotenv()

from src.logging_config import get_logger

logger = get_logger(__name__)


API_KEY = os.getenv("TWELVE_API_KEY")

def get_stock_data_time_series(
    symbol: str = "AAPL",
    max_retries: int = API_MAX_RETRIES,
):
    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": API_INTERVAL,
        "outputsize": API_OUTPUT_SIZE,
        "apikey": API_KEY,
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=10,
            )

            if response.status_code == 429:
                logger.warning(
                    "Rate limit hit for %s, sleeping %ss",
                    symbol,
                    RATE_LIMIT_SLEEP_SECONDS,
                )
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)
                continue

            response.raise_for_status()
            data = response.json()

            if "values" in data:
                return data["values"]

            if data.get("code") == 429:
                # print(
                #     f"[RATE LIMIT] Hit for {symbol}, "
                #     f"sleeping {RATE_LIMIT_SLEEP_SECONDS}s..."
                # )
                logger.warning(
                    "Rate limit hit for %s, sleeping %ss",
                    symbol,
                    RATE_LIMIT_SLEEP_SECONDS,
                )
                time.sleep(RATE_LIMIT_SLEEP_SECONDS)
                continue

            #print(f"[API ERROR] {symbol}: {data}")
            logger.error("API error for %s: %s", symbol, data,)
            return None

        except requests.exceptions.RequestException as exc:
            # print(
            #     f"[REQUEST ERROR] {symbol} "
            #     f"(attempt {attempt + 1}/{max_retries}): {exc}"
            # )
            logger.error("Request error for %s (attempt %s/%s): %s",
                         symbol, attempt + 1, max_retries, exc,)

    logger.error("Failed to fetch data for %s after %s attempts",
                 symbol, max_retries,)
    return None


def get_stock_data_quote(symbol="AAPL"):
    url = "https://api.twelvedata.com/quote"

    params = {
        "symbol": symbol,
        "interval": API_INTERVAL,
        "apikey": API_KEY,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()
