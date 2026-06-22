import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # loads variables from a .env file in the project root, if present

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "food_waste_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = "sqlite:///food_waste_db.sqlite"


def get_engine():
    """Return a SQLAlchemy engine. pool_pre_ping avoids stale-connection errors."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


# A module-level engine that Streamlit / scripts can import directly.
engine = get_engine()


def test_connection() -> bool:
    """Quick health check used by load_data.py and the Streamlit sidebar."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Database connection failed: {exc}")
        return False


if __name__ == "__main__":
    if test_connection():
        print(f"Connected successfully to {DB_NAME} at {DB_HOST}:{DB_PORT}")
    else:
        print("Connection failed - check your .env file.")
