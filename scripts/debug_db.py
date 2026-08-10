from sqlalchemy import text

from src.database.connection import engine


with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Database connection OK:", result.scalar())