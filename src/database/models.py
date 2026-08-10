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
