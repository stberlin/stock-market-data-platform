import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("STOCK_DB_USER")
DB_PASSWORD = os.getenv("STOCK_DB_PASSWORD")
DB_HOST = os.getenv("STOCK_DB_HOST")
DB_PORT = os.getenv("STOCK_DB_PORT")
DB_NAME = os.getenv("STOCK_DB_NAME")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)
