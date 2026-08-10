from sqlalchemy.dialects.postgresql import insert

from src.database.connection import engine
from src.database.models import stock_alerts, stock_prices


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
            records,
        )

    return result.rowcount
