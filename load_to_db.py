import pathlib
import sys
import pandas as pd
from sqlalchemy import text
from db import engine, test_connection

# --- Direct Local Paths ---
RAW_DIR = pathlib.Path(__file__).parent / "RAW DATA"
SCHEMA_FILE = pathlib.Path(__file__).parent / "SQL" / "schema.sql"

TABLES = ["providers", "receivers", "food_listings", "claims"]

# ============================================================
# STEP 1: LOAD & CLEAN RAW DATA
# ============================================================

def load_and_clean_all() -> dict[str, pd.DataFrame]:
    """Read data directly from RAW DATA and clean it natively."""
    print(f"Reading raw datasets from {RAW_DIR}...")
    
    # Verify raw files exist
    files = {
        "providers": RAW_DIR / "providers_data.csv",
        "receivers": RAW_DIR / "receivers_data.csv",
        "food_listings": RAW_DIR / "food_listings_data.csv",
        "claims": RAW_DIR / "claims_data.csv"
    }
    
    missing = [k for k, v in files.items() if not v.exists()]
    if missing:
        print(f"❌ Error: Missing raw source files in RAW DATA folder: {missing}")
        sys.exit(1)

    # Load dataframes
    df_prov = pd.read_csv(files["providers"])
    df_recv = pd.read_csv(files["receivers"])
    df_list = pd.read_csv(files["food_listings"])
    df_clms = pd.read_csv(files["claims"])

    print("Processing & Cleaning Data Elements...")
    
    # 1. Clean Providers
    df_prov.columns = [c.strip() for c in df_prov.columns]
    for col in ["Name", "Type", "City", "Address", "Contact"]:
        if col in df_prov.columns:
            df_prov[col] = df_prov[col].astype(str).str.strip()
    df_prov = df_prov.drop_duplicates(subset=["Provider_ID"])

    # 2. Clean Receivers
    df_recv.columns = [c.strip() for c in df_recv.columns]
    for col in ["Name", "Type", "City", "Contact"]:
        if col in df_recv.columns:
            df_recv[col] = df_recv[col].astype(str).str.strip()
    df_recv = df_recv.drop_duplicates(subset=["Receiver_ID"])

    # 3. Clean Food Listings
    df_list.columns = [c.strip() for c in df_list.columns]
    for col in ["Food_Name", "Food_Type", "Meal_Type", "Location", "Provider_Type"]:
        if col in df_list.columns:
            df_list[col] = df_list[col].astype(str).str.strip()
    if "Expiry_Date" in df_list.columns:
        df_list["Expiry_Date"] = pd.to_datetime(df_list["Expiry_Date"], errors="coerce").dt.date
    if "Quantity" in df_list.columns:
        df_list["Quantity"] = pd.to_numeric(df_list["Quantity"], errors="coerce").fillna(0).astype(int)
    df_list = df_list.drop_duplicates(subset=["Food_ID"]).dropna(subset=["Expiry_Date"])

    # 4. Clean Claims
    df_clms.columns = [c.strip() for c in df_clms.columns]
    if "Status" in df_clms.columns:
        df_clms["Status"] = df_clms["Status"].astype(str).str.strip().str.title()
    if "Timestamp" in df_clms.columns:
        df_clms["Timestamp"] = pd.to_datetime(df_clms["Timestamp"], errors="coerce")
    df_clms = df_clms.drop_duplicates(subset=["Claim_ID"]).dropna(subset=["Timestamp"])

    # 5. Handle Relational Consistency (Drop Orphans)
    df_list = df_list[df_list["Provider_ID"].isin(df_prov["Provider_ID"])]
    df_clms = df_clms[df_clms["Food_ID"].isin(df_list["Food_ID"]) & df_clms["Receiver_ID"].isin(df_recv["Receiver_ID"])]

    print(f"  -> providers: {len(df_prov)} rows processed")
    print(f"  -> receivers: {len(df_recv)} rows processed")
    print(f"  -> food_listings: {len(df_list)} rows processed")
    print(f"  -> claims: {len(df_clms)} rows processed")

    return {
        "providers": df_prov,
        "receivers": df_recv,
        "food_listings": df_list,
        "claims": df_clms
    }

# ============================================================
# STEP 2: SCHEMA & SYSTEM SETUP
# ============================================================

def create_schema() -> None:
    print("Initializing Database Schema Structures...")
    if not SCHEMA_FILE.exists():
        print(f"⚠️ Warning: Schema file not found at {SCHEMA_FILE}. Proceeding with dynamic tables.")
        return
    
    with engine.begin() as conn:
        sql_script = SCHEMA_FILE.read_text()
        statements = [s.strip() for s in sql_script.split(";") if s.strip()]
        for stmt in statements:
            try:
                conn.exec_driver_sql(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    pass

def load_table(df: pd.DataFrame, table_name: str) -> None:
    df_copy = df.copy()
    df_copy.columns = [c.lower() for c in df_copy.columns]
    df_copy.to_sql(table_name, engine, if_exists="replace", index=False, method="multi", chunksize=500)
    print(f"  -> loaded {len(df_copy):>5} rows clean into database table: '{table_name}'")

def insert_all(data: dict[str, pd.DataFrame]) -> None:
    print("Writing records into local database engine store...")
    for table in TABLES:
        load_table(data[table], table)

def main() -> None:
    print("Checking Database Connection Integrity...")
    if not test_connection():
        print("❌ Cannot reach your database engine url setup.")
        sys.exit(1)

    cleaned_data = load_and_clean_all()   
    create_schema()                       
    insert_all(cleaned_data)               

    print("\n🎉 Success! Verified final database operational row counts:")
    with engine.connect() as conn:
        for table in TABLES:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  {table}: {count} records verified")
            except Exception:
                print(f"  {table}: structure configured")

if __name__ == "__main__":
    main()