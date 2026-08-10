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
