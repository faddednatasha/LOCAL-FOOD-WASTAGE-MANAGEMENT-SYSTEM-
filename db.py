import os
import pathlib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = "sqlite:///food_waste_db.sqlite"

def get_engine():
    """Return a SQLAlchemy engine."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)

engine = get_engine()

def auto_initialize_sqlite():
    """Automatically builds the database tables if they do not exist yet on Streamlit Cloud."""
    schema_file = pathlib.Path(__file__).parent / "SQL" / "schema.sql"
    
    if not schema_file.exists():
        return
        
    # Check if a core table already exists
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM food_listings LIMIT 1"))
            # If this succeeds, the database is already built!
            return 
    except Exception:
        # If it fails, the database is empty or missing tables. Let's create them!
        print("Empty database detected. Initializing database schema on Streamlit Cloud...")
        with engine.begin() as conn:
            sql_script = schema_file.read_text()
            statements = [s.strip() for s in sql_script.split(";") if s.strip()]
            for stmt in statements:
                try:
                    conn.exec_driver_sql(stmt)
                except Exception:
                    pass

def test_connection() -> bool:
    """Quick health check used by app.py that automatically handles first-time setup."""
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        
        # Run the auto-setup check right here!
        auto_initialize_sqlite()
        return True
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return False

if __name__ == "__main__":
    if test_connection():
        print("Connected and initialized successfully!")
    else:
        print("Connection failed.")
