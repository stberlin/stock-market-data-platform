from src.database.connection import engine

create_table_sql = """
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    timestamp TIMESTAMP,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
);
"""

with engine.connect() as conn:
    conn.execute(create_table_sql)

print("Table created")