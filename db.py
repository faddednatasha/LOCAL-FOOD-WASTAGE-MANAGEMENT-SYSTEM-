import os
import pathlib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = "sqlite:///food_waste_db.sqlite"

def get_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True)

engine = get_engine()

def auto_seed_database_if_empty():
    """Automatically parses raw data files and injects them if cloud DB is completely fresh."""
    # Local pathing routes
    raw_dir = pathlib.Path(__file__).parent / "RAW DATA"
    schema_file = pathlib.Path(__file__).parent / "SQL" / "schema.sql"
    
    try:
        with engine.connect() as conn:
            # Check if data already exists
            count = conn.execute(text("SELECT COUNT(*) FROM food_listings")).scalar()
            if count > 0:
                return # Database already has data!
    except Exception:
        # Tables don't exist yet, build schema structural layout first
        if schema_file.exists():
            with engine.begin() as conn:
                sql_script = schema_file.read_text()
                for stmt in [s.strip() for s in sql_script.split(";") if s.strip()]:
                    try:
                        conn.exec_driver_sql(stmt)
                    except Exception:
                        pass

    # Read and seed data on-the-fly directly into SQLite tables
    files = {
        "providers": raw_dir / "providers_data.csv",
        "receivers": raw_dir / "receivers_data.csv",
        "food_listings": raw_dir / "food_listings_data.csv",
        "claims": raw_dir / "claims_data.csv"
    }
    
    # Confirm paths exist before seeding data structures
    if not all(p.exists() for p in files.values()):
        return

    print("Seeding SQLite database tables cleanly from data directory files...")
    with engine.begin() as conn:
        for table_name, file_path in files.items():
            df = pd.read_csv(file_path)
            # Force headers to match lower-case configuration expectations
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.drop_duplicates()
            
            # Clean explicit types right before injection to match schema constraints
            if table_name == "food_listings" and "expiry_date" in df.columns:
                df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce").dt.date.astype(str)
            if table_name == "claims" and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date.astype(str)
                
            df.to_sql(table_name, conn, if_exists="replace", index=False)

def test_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        # Run automatic setup validation checks
        auto_seed_database_if_empty()
        return True
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        return False
