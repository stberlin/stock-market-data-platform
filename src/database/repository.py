from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

from src.database.connection import engine
from src.database.models import stock_alerts, stock_prices
from src.database.models import intraday_level_alerts
from src.database.models import signal_alerts_v2

def insert_stock_data(df):
    records = df.to_dict(orient="records")

    if not records:
        return 0

    statement = insert(stock_prices).values(records)

    statement = statement.on_conflict_do_nothing(
        index_elements=["symbol", "timestamp"]
    )

    with engine.begin() as connection:
        result = connection.execute(statement)

    return result.rowcount

def insert_alert_data(df):
    records = df.to_dict(orient="records")

    if not records:
        return 0

    with engine.begin() as connection:
        result = connection.execute(
            stock_alerts.insert(),
            records
        )

    return result.rowcount

def insert_intraday_level_alert(alert_data):
    stmt = insert(intraday_level_alerts).values(
        symbol=alert_data["symbol"],
        alert_level=alert_data["alert_level"],
        change_from_open_pct=alert_data["change_from_open_pct"],
        current_price=alert_data["current_price"],
        trading_day=alert_data["trading_day"],
        created_at=alert_data["created_at"],
    )

    stmt = stmt.on_conflict_do_nothing(
        constraint="uq_intraday_level_alert"
    )

    with engine.begin() as conn:
        result = conn.execute(stmt)

    return result.rowcount == 1

def insert_signal_alert_v2(alert_data):
    stmt = signal_alerts_v2.insert().values(
        symbol=alert_data["symbol"],

        trough_time=alert_data["trough_time"],
        peak_price=alert_data["peak_price"],
        trough_price=alert_data["trough_price"],
        drawdown_pct=alert_data["drawdown_pct"],

        day_open=alert_data["day_open"],
        day_high=alert_data["day_high"],
        current_price=alert_data["current_price"],
        change_from_open_pct=alert_data["change_from_open_pct"],
        drawdown_from_day_high_pct=alert_data["drawdown_from_day_high_pct"],

        rsi_5m_14=alert_data["rsi_5m_14"],
        rsi_daily_14=alert_data["rsi_daily_14"],

        volume_ratio=alert_data["volume_ratio"],

        signal=alert_data["signal"],

        trading_day=alert_data["trading_day"],
        created_at=alert_data["created_at"],

        company_name=alert_data["company_name"],

        notified=False,
    )

    with engine.begin() as conn:
        result = conn.execute(stmt)

    return result.inserted_primary_key[0]

def signal_already_notified(symbol, signal, trading_day):
    stmt = (
        select(signal_alerts_v2.c.id)
        .where(
            signal_alerts_v2.c.symbol == symbol,
            signal_alerts_v2.c.signal == signal,
            signal_alerts_v2.c.trading_day == trading_day,
            signal_alerts_v2.c.notified.is_(True),
        )
        .limit(1)
    )

    with engine.connect() as conn:
        result = conn.execute(stmt).first()

    return result is not None

def mark_signal_as_notified(alert_id):
    stmt = (
        signal_alerts_v2.update()
        .where(signal_alerts_v2.c.id == alert_id)
        .values(notified=True)
    )

    with engine.begin() as conn:
        conn.execute(stmt)
