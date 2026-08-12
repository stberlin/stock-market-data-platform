from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Date,
    Boolean,
)

metadata = MetaData()

stock_prices = Table(
    "stock_prices",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(10), nullable=False),
    Column("timestamp", DateTime, nullable=False),
    Column("timestamp_ny", DateTime(timezone=True)),
    Column("timestamp_berlin", DateTime(timezone=True)),
    Column("open", Numeric),
    Column("high", Numeric),
    Column("low", Numeric),
    Column("close", Numeric),
    Column("volume", BigInteger),
    Column("created_at", DateTime),
    UniqueConstraint("symbol", "timestamp", name="uq_stock_symbol_timestamp"),
)

stock_alerts = Table(
    "stock_alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(10), nullable=False),
    Column("company_name", String(100)),
    Column("start_time", DateTime),
    Column("end_time", DateTime),
    Column("start_price", Numeric),
    Column("end_price", Numeric),
    Column("change_pct", Numeric),
    Column("volume_now", BigInteger),
    Column("avg_volume_today", Numeric),
    Column("avg_volume_7d", Numeric),
    Column("market_conviction_score", Numeric),
    Column("rebound_score", Numeric),
    Column("signal_direction", String(20)),
    Column("volume_confirmation", String(20)),
    Column("volume_ratio", Numeric),
    Column("relative_day_volume", Numeric),
    Column("created_at", DateTime),
    Column("alert_type", String(100)),
)

intraday_level_alerts = Table(
    "intraday_level_alerts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("symbol", String(10), nullable=False),
    Column("alert_level", Numeric, nullable=False),
    Column("change_from_open_pct", Numeric, nullable=False),
    Column("current_price", Numeric),
    Column("trading_day", Date, nullable=False),
    Column("created_at", DateTime, nullable=False),

    UniqueConstraint(
        "symbol",
        "alert_level",
        "trading_day",
        name="uq_intraday_level_alert"
    ),
)

signal_alerts_v2 = Table(
    "signal_alerts_v2",
    metadata,
    Column("id", Integer, primary_key=True),

    Column("symbol", String(10), nullable=False),

    Column("trough_time", DateTime),
    Column("peak_price", Numeric),
    Column("trough_price", Numeric),
    Column("drawdown_pct", Numeric),

    Column("day_open", Numeric),
    Column("day_high", Numeric),
    Column("current_price", Numeric),
    Column("change_from_open_pct", Numeric),
    Column("drawdown_from_day_high_pct", Numeric),

    Column("rsi_5m_14", Numeric),
    Column("rsi_daily_14", Numeric),

    Column("volume_ratio", Numeric),

    Column("signal", String(50), nullable=False),

    Column("trading_day", Date, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("company_name", String(100)),

    Column("notified", Boolean, nullable=False, default=False),
)
