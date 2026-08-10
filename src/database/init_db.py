from sqlalchemy import text

from src.database.connection import engine


CREATE_STOCK_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timestamp_ny TIMESTAMPTZ,
    timestamp_berlin TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    created_at TIMESTAMP,
    UNIQUE (symbol, timestamp)
);
"""


def init_db():
    with engine.begin() as connection:
        connection.execute(text(CREATE_STOCK_PRICES_TABLE))

    print("Database initialized.")


if __name__ == "__main__":
    init_db()
