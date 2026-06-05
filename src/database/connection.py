from sqlalchemy import create_engine

DB_USER = "stock_user"
DB_PASSWORD = "stock_password"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "stocks"

engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)