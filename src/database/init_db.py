from src.database.connection import engine
from src.database.models import metadata


def init_db():
    metadata.create_all(engine)
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
