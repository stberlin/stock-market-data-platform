from src.database.connection import engine
import pandas as pd
from datetime import datetime
import requests
import sys
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def check_price_drop(drop_threshold=5, lookback_minutes=30):
    query = f"""
WITH base AS (
    SELECT *
    FROM stock_prices
    WHERE timestamp >= (
        SELECT MAX(timestamp) - INTERVAL '{lookback_minutes} minutes'
        FROM stock_prices
    )
),

latest AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        timestamp,
        volume
    FROM stock_prices
    ORDER BY symbol, timestamp DESC
),

today_avg AS (
    SELECT
        symbol,
        AVG(volume) AS avg_volume_today
    FROM stock_prices
    WHERE DATE(timestamp) = CURRENT_DATE
    GROUP BY symbol
),

week_avg AS (
    SELECT
        symbol,
        AVG(volume) AS avg_volume_7d
    FROM stock_prices
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY symbol
),

price_calc AS (
    SELECT
        symbol,
        MIN(timestamp) AS start_time,
        MAX(timestamp) AS end_time,

        (ARRAY_AGG(close ORDER BY timestamp ASC))[1] AS start_price,
        (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS end_price,

        (
            (ARRAY_AGG(close ORDER BY timestamp DESC))[1] -
            (ARRAY_AGG(close ORDER BY timestamp ASC))[1]
        ) /
        (ARRAY_AGG(close ORDER BY timestamp ASC))[1] * 100 AS change_pct
    FROM base
    GROUP BY symbol
)

SELECT
    p.symbol,
    p.start_time,
    p.end_time,
    p.start_price,
    p.end_price,
    p.change_pct,

    l.volume AS volume_now,
    t.avg_volume_today,
    w.avg_volume_7d

FROM price_calc p
LEFT JOIN latest l ON p.symbol = l.symbol
LEFT JOIN today_avg t ON p.symbol = t.symbol
LEFT JOIN week_avg w ON p.symbol = w.symbol

WHERE p.change_pct <= {drop_threshold};
"""

    df = pd.read_sql(query, engine)

    if df.empty:
        print("No alerts")
        sys.exit(0)

    print("ALERTS FOUND:")
    return df


def compute_score(change_pct, volume_now, avg_today, avg_7d):

    # -------------------------
    # 1. PRICE SCORE
    # -------------------------
    price_score = min(abs(change_pct) * 10, 100)
    price_score = min(price_score, 100)

    # -------------------------
    # 2. VOLUME SCORE
    # -------------------------
    if avg_today == 0:
        volume_score = 0
    else:
        volume_ratio = volume_now / avg_today
        volume_score = min(volume_ratio * 50, 100)

    # -------------------------
    # 3. CONTEXT SCORE
    # -------------------------
    if avg_7d == 0:
        context_score = 0
    else:
        context_ratio = avg_today / avg_7d
        context_score = min(context_ratio * 50, 100)

    # -------------------------
    # FINAL SCORE
    # -------------------------
    score = (
        price_score * 0.4 +
        volume_score * 0.35 +
        context_score * 0.25
    )

    # -------------------------
    # CLASSIFICATION
    # -------------------------
    if score >= 85:
        label = "HIGH_CONVICTION"
    elif score >= 70:
        label = "STRONG_SIGNAL"
    elif score >= 40:
        label = "WATCHLIST"
    else:
        label = "NOISE"

    # -------------------------
    # FAKE MOVE FLAG
    # -------------------------
    fake_move = (change_pct < 0 and volume_score < 30)

    return score, label, fake_move


def score_calculator(alert_df):
    alert_df["score"] = 0
    alert_df["label"] = ""
    alert_df["fake_move"] = False

    for i, row in alert_df.iterrows():

        score, label, fake = compute_score(
            row["change_pct"],
            row["volume_now"],
            row["avg_volume_today"],
            row["avg_volume_7d"]
        )

        alert_df.at[i, "score"] = score
        alert_df.at[i, "label"] = label
        alert_df.at[i, "fake_move"] = fake

    return alert_df


def calculate_signal(change_pct, volume_now, avg_volume_today, avg_volume_7d):

    # ------------------------
    # Direction
    # ------------------------

    if change_pct > 0:
        signal_direction = "BULLISH"
    elif change_pct < 0:
        signal_direction = "BEARISH"
    else:
        signal_direction = "NEUTRAL"

    # ------------------------
    # Volume Confirmation
    # ------------------------

    # volume_confirmation = False

    # if (
    #     avg_volume_today > 0
    #     and volume_now >= avg_volume_today * 1.5
    # ):
    #     volume_confirmation = True
    volume_ratio = volume_now / avg_volume_today
    if volume_ratio >= 3:
        volume_confirmation = "EXTREME"

    elif volume_ratio >= 2:
        volume_confirmation = "HIGH"

    elif volume_ratio >= 1.2:
        volume_confirmation = "ABOVE_AVERAGE"

    else:
        volume_confirmation = "NORMAL"

    # ------------------------
    # Price Component
    # ------------------------

    price_score = min(abs(change_pct) * 10, 100)

    # ------------------------
    # Current Volume Component
    # ------------------------

    if avg_volume_today > 0:
        volume_ratio = volume_now / avg_volume_today
        volume_score = min(volume_ratio * 50, 100)
    else:
        volume_score = 0

    # ------------------------
    # Historical Context Component
    # ------------------------

    if avg_volume_7d > 0:
        context_ratio = avg_volume_today / avg_volume_7d
        context_score = min(context_ratio * 50, 100)
    else:
        context_score = 0

    # ------------------------
    # Final Strength
    # ------------------------

    market_conviction_score = (
        price_score * 0.60
        + volume_score * 0.30
        + context_score * 0.10
    )

    market_conviction_score = round(market_conviction_score, 2)

    # -------------------------
    # REBOUND
    # -----------------------------

    price_component = min(abs(change_pct) / 10, 1)

    # volume_penalty = min(volume_ratio / 3, 1)

    # rebound_score = (price_component * (1 - volume_penalty)) * 100

    if volume_ratio < 1:
        volume_factor = 1

    elif volume_ratio <= 1.2:
        volume_factor = 0.8

    elif volume_ratio <= 2:
        volume_factor = 0.5

    else:
        volume_factor = 0.2

    relative_day_volume = avg_volume_today / avg_volume_7d

    if relative_day_volume < 0.8:
        historical_factor = 1

    elif relative_day_volume <= 1.2:
        historical_factor = 0.9

    elif relative_day_volume <= 2:
        historical_factor = 0.6

    else:
        historical_factor = 0.3

    rebound_score = (
        price_component *
        volume_factor *
        historical_factor
    ) * 100

    return (
        market_conviction_score,
        rebound_score,
        signal_direction,
        volume_confirmation,
        volume_ratio,
        context_ratio
    )


def signal_calculator(alert_df):
    alert_df["market_conviction_score"] = None
    alert_df["signal_direction"] = None
    alert_df["volume_confirmation"] = None
    alert_df["volume_ratio"] = None
    alert_df["relative_day_volume"] = None
    alert_df["rebound_score"] = None
    # testing
    #alert_df['change_pct'] = alert_df['change_pct'] * 10
    
    for idx, row in alert_df.iterrows():

        (
            market_conviction_score,
            rebound_score,
            signal_direction,
            volume_confirmation,
            volume_ratio,
            context_ratio

            
        ) = calculate_signal(
            row["change_pct"],
            row["volume_now"],
            row["avg_volume_today"],
            row["avg_volume_7d"]
        )

        alert_df.loc[idx, "market_conviction_score"] = market_conviction_score
        alert_df.loc[idx, "rebound_score"] = rebound_score
        alert_df.loc[idx, "signal_direction"] = signal_direction
        alert_df.loc[idx, "volume_confirmation"] = volume_confirmation
        alert_df.loc[idx, "volume_ratio"] = volume_ratio
        alert_df.loc[idx, "relative_day_volume"] = context_ratio


    return alert_df


def add_company_name_column(df):
    ticker_to_name = {
        "QNC": "Quantum eM.",
        "AAPL": "Apple",
        "TSLA": "Tesla",
        "GOOGL": "Alphabet",
        "IREN": "IREN",
        "NVDA": "NVIDIA",
        "MU": "Micron",
        "PL": "Planet Labs",
        "QBTS": "D-Wave",
        "RGTI": "Rigetti",
        "NTLA": "Intellia",
        "CRWV": "CoreWeave",
        "NBIS": "Nebius"
    }
    df["company_name"] = df["symbol"].map(ticker_to_name)
    return df


def alert_signal_processor(alert_signal_df, drop_threshold, lookback_minutes):
    alert_signal_df['created_at'] = datetime.today()
    alert_signal_df['alert_type'] = f"DROP_{drop_threshold}_PERCENT_IN_{lookback_minutes}_MINUTES"
    alert_signal_df_mapped = add_company_name_column(alert_signal_df)

    return alert_signal_df_mapped
    # alert_db_df_list = []
    # for _, row in alert_signal_df.iterrows():

    #     label = classify_row(row)
    #     if label == "STRONG_REBOUND" or "WATCHLIST_REBOUND" or "HIGH_SELL":
    #         alert_db_df_list.append(row)



def classify_row(row):
    if row["rebound_score"] >= 80:
        return "STRONG_REBOUND"

    elif row["rebound_score"] >= 60:
        return "WATCHLIST_REBOUND"

    elif row["market_conviction_score"] >= 85:
        return "HIGH_SELL"

    elif row["market_conviction_score"] >= 70:
        return "MEDIUM_SELL"

    else:
         return "UNCLEAR"


def run_alert_system(alert_signal_df):

    rebound_watchlist = []
    rebound_strong = []

    sell_strong = []
    # sell_medium = []

    # mixed = []

    # -----------------------
    # 3. ROUTING LOOP
    # -----------------------
    for _, row in alert_signal_df.iterrows():

        label = classify_row(row)

        data = {
            "symbol": row["symbol"],
            "company_name": row['company_name'],
            "change": row["change_pct"],
            "rebound_score": row["rebound_score"],
            "market_conviction_score": row["market_conviction_score"],
            "volume_ratio": row["volume_ratio"],
            "relative_day_volume": row['relative_day_volume'],
            "end_price": row['end_price']
        }

        if label == "STRONG_REBOUND":
            rebound_strong.append(data)

        elif label == "WATCHLIST_REBOUND":
            rebound_watchlist.append(data)

        elif label == "HIGH_SELL":
            sell_strong.append(data)

        # elif label == "MEDIUM_SELL":
        #     sell_medium.append(data)

        # else:
        #     unclear.append(data)
    return rebound_strong, rebound_watchlist, sell_strong


def build_message(rebound_strong, rebound_watchlist, sell_strong):

    message = "📊 MARKET ALERT REPORT\n\n"

    # 🟢 REBOUND SECTION
    if rebound_strong or rebound_watchlist:
        message += "🟢 REBOUND SETUPS\n"

        for r in sorted(rebound_strong, key=lambda x: x["rebound_score"], reverse=True):
            message += (
                f"🔥 {r['company_name']} | {r['change']:.2f}% | "
                f"Price: {r['end_price']:.2f} | "
                f"Score: {r['rebound_score']:.1f} | "
                f"Vol. Ratio: {r['volume_ratio']:.2f} | "
                f"Rel. Vol: {r['relative_day_volume']:.2f}\n"
            )

        for r in sorted(rebound_watchlist, key=lambda x: x["rebound_score"], reverse=True):
            message += (
                f"👀 {r['company_name']} | {r['change']:.2f}% | "
                f"Price: {r['end_price']:.2f} | "
                f"Score: {r['rebound_score']:.1f} | "
                f"Vol. Ratio: {r['volume_ratio']:.2f} | "
                f"Rel. Vol: {r['relative_day_volume']:.2f}\n"
            )

        message += "\n"

    # 🔴 SELL SECTION
    if sell_strong:
        message += "🔴 SELL PRESSURE\n"

        for r in sorted(sell_strong, key=lambda x: x["market_conviction_score"], reverse=True):
            # message += (
            #     f"🚨 {r['symbol']} | {r['change']:.2f}% | "
            #     f"Signal: {r['market_conviction_score']:.1f} | Vol. Ratio: {r['volume_ratio']:.2f} | Rel. Vol: {r['relative_day_volume']:.2f}\n"
            # )
            message += (
                f"🚨 {r['company_name']} | {r['change']:.2f}% | "
                f"Price: {r['end_price']:.2f} | "
                f"Signal: {r['market_conviction_score']:.1f} | "
                f"Vol. Ratio: {r['volume_ratio']:.2f} | "
                f"Rel. Vol: {r['relative_day_volume']:.2f}\n"
            )

        message += "\n"

    # # ⚪ UNCLEAR SECTION (optional)
    # if unclear:
    #     message += "⚪ NO CLEAR SETUP\n"

    #     for u in unclear[:5]:
    #         message += f"{u['symbol']} | {u['change']:.2f}%\n"

    return message


def push_to_db(final_alert_df):
    final_alert_df.to_sql(
        "stock_alerts",
        engine,
        if_exists="append",
        index=False
    )


def send_telegram_message(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"   # optional (für später Formatierung)
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        print("Telegram Error:", response.text)

    return response.json()

    

def main_alert():
    drop_threshold=-3
    lookback_minutes=30
    alert_df = check_price_drop(drop_threshold=drop_threshold, lookback_minutes=lookback_minutes)
    alert_signal_df = signal_calculator(alert_df)
    #alert_score_df = score_calculator(alert_df)
    
    final_alert_df = alert_signal_processor(alert_signal_df, drop_threshold, lookback_minutes)
    push_to_db(final_alert_df)
    rebound_strong, rebound_watchlist, sell_strong = run_alert_system(final_alert_df)
    message = build_message(rebound_strong, rebound_watchlist, sell_strong)
    send_telegram_message(message=message, bot_token=API_KEY, chat_id=CHAT_ID)
    



if __name__ == "__main__":
    main_alert()
    