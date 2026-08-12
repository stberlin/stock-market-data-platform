from src.database.connection import engine
import pandas as pd
import os
from datetime import datetime
from src.notifications.telegram import send_telegram_message
from src.config import COMPANY_NAMES
from src.database.repository import (
    insert_intraday_level_alert,
    insert_signal_alert_v2,
    signal_already_notified,
    mark_signal_as_notified,
)

import logging

logger = logging.getLogger(__name__)


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def check_intrawindow_drawdown(
    drop_threshold=-2.0,
    lookback_minutes=30,
):
    query = f"""
    WITH base AS (
        SELECT
            symbol,
            timestamp,
            close,
            volume
        FROM stock_prices
        WHERE timestamp >= (
            SELECT MAX(timestamp) - INTERVAL '{lookback_minutes} minutes'
            FROM stock_prices
        )
    ),

    running_high AS (
        SELECT
            symbol,
            timestamp,
            close,
            volume,

            MAX(close) OVER (
                PARTITION BY symbol
                ORDER BY timestamp
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS high_so_far

        FROM base
    ),

    drawdowns AS (
        SELECT
            symbol,
            timestamp,
            close,
            volume,
            high_so_far,

            (
                (close - high_so_far)
                / high_so_far
                * 100
            ) AS drawdown_pct

        FROM running_high
    ),

    worst_drawdown AS (
        SELECT DISTINCT ON (symbol)
            symbol,
            timestamp AS trough_time,
            close AS trough_price,
            high_so_far AS peak_price,
            volume AS volume_now,
            drawdown_pct

        FROM drawdowns
        ORDER BY symbol, drawdown_pct ASC
    ),

    today_data AS (
        SELECT
            symbol,
            timestamp,
            close
        FROM stock_prices
        WHERE DATE(timestamp) = (
            SELECT DATE(MAX(timestamp))
            FROM stock_prices
        )
    ),

    intraday_context AS (
        SELECT
            symbol,

            (ARRAY_AGG(close ORDER BY timestamp ASC))[1] AS day_open,

            MAX(close) AS day_high,

            (ARRAY_AGG(close ORDER BY timestamp DESC))[1] AS current_price

        FROM today_data
        GROUP BY symbol
    )

    SELECT
        w.symbol,
        w.trough_time,
        w.peak_price,
        w.trough_price,
        w.drawdown_pct,
        w.volume_now,

        i.day_open,
        i.day_high,
        i.current_price,

        (
            (i.current_price - i.day_open)
            / i.day_open
            * 100
        ) AS change_from_open_pct,

        (
            (i.current_price - i.day_high)
            / i.day_high
            * 100
        ) AS drawdown_from_day_high_pct

    FROM worst_drawdown w

    LEFT JOIN intraday_context i
        ON w.symbol = i.symbol

    ORDER BY w.drawdown_pct ASC;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        logger.info("No intrawindow drawdowns found")
        return None

    logger.info("%s intrawindow drawdowns found", len(df))

    return df


def detect_candidates(
    signal_df,
    intrawindow_threshold=-1.0,
    from_open_threshold=-3.0,
    from_day_high_threshold=-3.0,
    rsi_threshold=30,
):
    if signal_df is None or signal_df.empty:
        logger.info("No signal data available for candidate detection")
        return None

    candidates = signal_df[
        (signal_df["drawdown_pct"] <= intrawindow_threshold)
        | (signal_df["change_from_open_pct"] <= from_open_threshold)
        | (signal_df["drawdown_from_day_high_pct"] <= from_day_high_threshold)
        | (signal_df["rsi_5m_14"] < rsi_threshold)
    ].copy()

    if candidates.empty:
        logger.info("No candidates detected")
        return None

    logger.info("%s candidates detected", len(candidates))

    return candidates


def calculate_rsi(period=14):
    query = """
        SELECT
            symbol,
            timestamp,
            close
        FROM stock_prices
        ORDER BY symbol, timestamp
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        logger.info("No price data available for RSI calculation")
        return None

    results = []

    for symbol, group in df.groupby("symbol"):

        group = group.sort_values("timestamp").copy()

        # Veränderung zum vorherigen 5-Minuten-Close
        delta = group["close"].diff()

        # Positive Veränderungen
        gain = delta.clip(lower=0)

        # Negative Veränderungen als positive Verlustgröße
        loss = -delta.clip(upper=0)

        # Wilder Smoothing
        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        latest_rsi = rsi.iloc[-1]

        results.append({
            "symbol": symbol,
            "rsi_5m_14": latest_rsi
        })

    return pd.DataFrame(results)


def calculate_volume_context():
    query = """
    WITH latest AS (
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
        WHERE DATE(timestamp) = (
            SELECT DATE(MAX(timestamp))
            FROM stock_prices
        )
        GROUP BY symbol
    )

    SELECT
        l.symbol,
        l.volume AS current_volume,
        t.avg_volume_today,

        CASE
            WHEN t.avg_volume_today > 0
            THEN l.volume / t.avg_volume_today
            ELSE NULL
        END AS volume_ratio

    FROM latest l
    LEFT JOIN today_avg t
        ON l.symbol = t.symbol;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        logger.info("No volume data available")
        return None

    return df


def build_signal_context(
    lookback_minutes=30,
    rsi_period=14,
):
    price_df = check_intrawindow_drawdown(
        lookback_minutes=lookback_minutes,
    )

    if price_df is None:
        logger.info("No price data found")
        return None

    rsi_df = calculate_rsi(period=rsi_period)
    daily_rsi_df = calculate_daily_rsi(period=14)
    volume_df = calculate_volume_context()

    signal_df = price_df.copy()

    if rsi_df is not None:
        signal_df = signal_df.merge(
            rsi_df,
            on="symbol",
            how="left",
        )
    else:
        signal_df["rsi_5m_14"] = None

    if daily_rsi_df is not None:
        signal_df = signal_df.merge(
            daily_rsi_df,
            on="symbol",
            how="left",
        )
    else:
        signal_df["rsi_daily_14"] = None

    if volume_df is not None:
        signal_df = signal_df.merge(
            volume_df,
            on="symbol",
            how="left",
        )
    else:
        signal_df["current_volume"] = None
        signal_df["avg_volume_today"] = None
        signal_df["volume_ratio"] = None

    def classify_rsi(value):
        if pd.isna(value):
            return "INSUFFICIENT_DATA"
        elif value < 30:
            return "OVERSOLD"
        elif value > 70:
            return "OVERBOUGHT"
        else:
            return "NEUTRAL"

    signal_df["rsi_5m_state"] = signal_df["rsi_5m_14"].apply(classify_rsi)
    signal_df["rsi_daily_state"] = (signal_df["rsi_daily_14"].apply(classify_rsi))

    return signal_df


def classify_candidate(row):
    drawdown = row["drawdown_pct"]
    day_change = row["change_from_open_pct"]
    day_high_drawdown = row["drawdown_from_day_high_pct"]
    rsi_5m = row["rsi_5m_14"]
    rsi_daily = row["rsi_daily_14"]
    volume_ratio = row["volume_ratio"]

    # Drop bereits weitgehend recovered
    if day_high_drawdown > -0.5:
        return "RECOVERED"

    # Strong Rebound Watch:
    # kurzfristig überverkauft,
    # aber Daily RSI nicht ebenfalls stark überverkauft
    if (
        pd.notna(rsi_5m)
        and rsi_5m < 30
        and drawdown <= -1.0
        and volume_ratio < 2.0
        and (
            pd.isna(rsi_daily)
            or rsi_daily >= 30
        )
    ):
        return "STRONG_REBOUND_WATCH"

    # Rebound Watch:
    # kurzfristig überverkauft,
    # Daily RSI ebenfalls niedrig oder noch unbekannt
    if (
        pd.notna(rsi_5m)
        and rsi_5m < 30
        and drawdown <= -1.0
        and volume_ratio < 2.0
    ):
        return "REBOUND_WATCH"

    # Starker Verkaufsdruck
    if (
        drawdown <= -1.0
        and volume_ratio >= 2.0
    ):
        return "SELL_PRESSURE"

    # Größerer Tagestrend nach unten
    if (
        day_change <= -3.0
        or day_high_drawdown <= -3.0
    ):
        return "INTRADAY_DROP"

    return "WATCH"


def classify_candidates(candidate_df):
    if candidate_df is None or candidate_df.empty:
        return None

    result_df = candidate_df.copy()

    result_df["signal"] = result_df.apply(
        classify_candidate,
        axis=1,
    )

    return result_df

NOTIFIABLE_SIGNALS = {
    "STRONG_REBOUND_WATCH",
    "REBOUND_WATCH",
    "SELL_PRESSURE",
    "INTRADAY_DROP",
}


def process_signal_alerts(classified_df):
    if classified_df is None or classified_df.empty:
        logger.info("No classified signals to process")
        return []

    notifications = []

    for _, row in classified_df.iterrows():
        trading_day = datetime.now().date()

        already_notified = signal_already_notified(
            symbol=row["symbol"],
            signal=row["signal"],
            trading_day=trading_day,
        )

        alert_data = {
            "symbol": row["symbol"],
            "company_name": COMPANY_NAMES.get(
                row["symbol"],
                row["symbol"],
            ),
            "trough_time": row["trough_time"],
            "peak_price": row["peak_price"],
            "trough_price": row["trough_price"],
            "drawdown_pct": row["drawdown_pct"],
            "day_open": row["day_open"],
            "day_high": row["day_high"],
            "current_price": row["current_price"],
            "change_from_open_pct": row["change_from_open_pct"],
            "drawdown_from_day_high_pct": row["drawdown_from_day_high_pct"],
            "rsi_5m_14": row["rsi_5m_14"],
            "rsi_daily_14": row["rsi_daily_14"],
            "volume_ratio": row["volume_ratio"],
            "signal": row["signal"],
            "trading_day": trading_day,
            "created_at": datetime.now(),
        }

        alert_id = insert_signal_alert_v2(alert_data)

        if (
            row["signal"] in NOTIFIABLE_SIGNALS
            and not already_notified
        ):
            notifications.append({
                "alert_id": alert_id,
                **alert_data,
            })

    logger.info(
        "%s signals stored, %s new notifications",
        len(classified_df),
        len(notifications),
    )

    return notifications


def build_signal_message(notifications):
    if not notifications:
        return None

    message = "📊 <b>MARKET SIGNAL REPORT</b>\n\n"

    for alert in notifications:
        rsi_5m = alert["rsi_5m_14"]
        rsi_daily = alert["rsi_daily_14"]

        rsi_5m_text = (
            f"{rsi_5m:.1f}"
            if pd.notna(rsi_5m)
            else "N/A"
        )

        rsi_daily_text = (
            f"{rsi_daily:.1f}"
            if pd.notna(rsi_daily)
            else "N/A"
        )

        message += (
            f"<b>{alert['company_name']} ({alert['symbol']})</b>\n"
            f"Signal: {alert['signal']}\n"
            f"30m Drop: {alert['drawdown_pct']:.2f}% | "
            f"Today: {alert['change_from_open_pct']:.2f}%\n"
            f"From High: {alert['drawdown_from_day_high_pct']:.2f}% | "
            f"Vol: {alert['volume_ratio']:.2f}x\n"
            f"RSI 5m: {rsi_5m_text} | "
            f"RSI Daily: {rsi_daily_text}\n"
            f"Price: ${alert['current_price']:.2f}\n\n"
        )

    return message


def send_signal_alerts(notifications):
    if not notifications:
        logger.info("No new signal notifications to send")
        return

    message = build_signal_message(notifications)

    result = send_telegram_message(
        message=message,
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
    )

    if result is not None:
        for alert in notifications:
            mark_signal_as_notified(alert["alert_id"])

        logger.info(
            "%s signal notifications sent",
            len(notifications),
        )

    else:
        logger.warning(
            "Signal notification sending failed"
        )


def calculate_daily_rsi(period=14):
    query = """
    WITH daily_close AS (
        SELECT DISTINCT ON (symbol, DATE(timestamp))
            symbol,
            DATE(timestamp) AS trading_day,
            close
        FROM stock_prices
        ORDER BY symbol, DATE(timestamp), timestamp DESC
    )

    SELECT
        symbol,
        trading_day,
        close
    FROM daily_close
    ORDER BY symbol, trading_day;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        logger.info("No daily price data available for RSI calculation")
        return None

    results = []

    for symbol, group in df.groupby("symbol"):

        group = group.sort_values("trading_day").copy()

        delta = group["close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False,
            min_periods=period
        ).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        latest_rsi = rsi.iloc[-1]

        results.append({
            "symbol": symbol,
            "rsi_daily_14": latest_rsi
        })

    return pd.DataFrame(results)


def detect_intraday_level_alerts(signal_df):
    if signal_df is None or signal_df.empty:
        logger.info("No signal data available for intraday level detection")
        return []

    levels = [-5.0, -10.0]

    new_alerts = []

    for _, row in signal_df.iterrows():
        symbol = row["symbol"]
        day_change = row["change_from_open_pct"]
        current_price = row["current_price"]

        for level in levels:
            if day_change <= level:
                alert_data = {
                    "symbol": symbol,
                    "company_name": COMPANY_NAMES.get(symbol, symbol),
                    "alert_level": level,
                    "change_from_open_pct": day_change,
                    "current_price": current_price,
                    "trading_day": datetime.now().date(),
                    "created_at": datetime.now(),
                }

                inserted = insert_intraday_level_alert(alert_data)

                if inserted:
                    new_alerts.append(alert_data)

    logger.info("%s new intraday level alerts detected", len(new_alerts))

    return new_alerts


def build_intraday_level_message(new_alerts):
    if not new_alerts:
        return None

    message = "🚨 <b>INTRADAY DROP ALERT</b>\n\n"

    for alert in new_alerts:
        message += (
            f"<b>{alert['symbol']}</b>\n"
            f"Level: {alert['alert_level']:.0f}%\n"
            f"Today: {alert['change_from_open_pct']:.2f}%\n"
            f"Price: ${alert['current_price']:.2f}\n\n"
        )

    return message


def send_intraday_level_alerts(new_alerts):
    message = build_intraday_level_message(new_alerts)

    if message is None:
        logger.info("No new intraday level alerts to send")
        return

    send_telegram_message(
        message=message,
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
    )

    logger.info(
        "%s intraday level alerts sent",
        len(new_alerts),
    )


def main_alert_v2():
    logger.info("Starting alert pipeline v2")

    signal_df = build_signal_context()

    if signal_df is None or signal_df.empty:
        logger.info("No signal context available")
        return

    # Intraday Level Alerts (-5%, -10%)
    intraday_alerts = detect_intraday_level_alerts(signal_df)
    send_intraday_level_alerts(intraday_alerts)

    # Signal Engine
    candidates = detect_candidates(signal_df)

    if candidates is None or candidates.empty:
        logger.info("No signal candidates detected")
        logger.info("Alert pipeline v2 finished")
        return

    classified_candidates = classify_candidates(candidates)

    notifications = process_signal_alerts(
        classified_candidates
    )

    send_signal_alerts(
        notifications
    )

    logger.info("Alert pipeline v2 finished")


if __name__ == "__main__":
    main_alert_v2()
