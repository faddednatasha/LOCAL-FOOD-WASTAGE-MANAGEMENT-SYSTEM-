import pathlib
import pandas as pd

# ============================================================
# STEP 1a: LOAD — just read the raw CSVs
# ============================================================

def load_raw_data() -> dict[str, pd.DataFrame]:
    """Read all four CSVs from ./data and return them untouched."""
    print("Loading raw CSVs from ./data ...")
    raw = {
        "providers": pd.read_csv(DATA_DIR / "providers_data.csv"),
        "receivers": pd.read_csv(DATA_DIR / "receivers_data.csv"),
        "food_listings": pd.read_csv(DATA_DIR / "food_listings_data.csv"),
        "claims": pd.read_csv(DATA_DIR / "claims_data.csv"),
    }
    for name, df in raw.items():
        print(f"  -> {name}: {len(df)} raw rows, columns: {list(df.columns)}")
    return raw


# ============================================================
# STEP 1b: CLEAN — one function per table
# ============================================================

def clean_providers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["name"] = df["name"].str.strip()
    df["type"] = df["type"].str.strip()
    df["city"] = df["city"].str.strip()
    df["address"] = df["address"].str.strip()
    df["contact"] = df["contact"].str.strip()
    df = df.drop_duplicates(subset="provider_id")
    return df


def clean_receivers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    for col in ["name", "type", "city", "contact"]:
        df[col] = df[col].str.strip()
    df = df.drop_duplicates(subset="receiver_id")
    return df


def clean_food_listings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["food_name"] = df["food_name"].str.strip()
    df["food_type"] = df["food_type"].str.strip()
    df["meal_type"] = df["meal_type"].str.strip()
    df["location"] = df["location"].str.strip()
    df["provider_type"] = df["provider_type"].str.strip()
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce").dt.date
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df = df.drop_duplicates(subset="food_id")
    df = df.dropna(subset=["expiry_date"])  # drop rows where date parsing failed
    return df


def clean_claims(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df["status"] = df["status"].str.strip().str.title()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.drop_duplicates(subset="claim_id")
    df = df.dropna(subset=["timestamp"])
    return df


def clean_all(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Apply the matching clean_* function to each raw table."""
    print("Cleaning data...")
    cleaned = {
        "providers": clean_providers(raw["providers"]),
        "receivers": clean_receivers(raw["receivers"]),
        "food_listings": clean_food_listings(raw["food_listings"]),
        "claims": clean_claims(raw["claims"]),
    }

    # Drop orphaned foreign keys (rows pointing at IDs that don't exist elsewhere)
    cleaned["food_listings"] = cleaned["food_listings"][
        cleaned["food_listings"]["provider_id"].isin(cleaned["providers"]["provider_id"])
    ]
    cleaned["claims"] = cleaned["claims"][
        cleaned["claims"]["food_id"].isin(cleaned["food_listings"]["food_id"])
        & cleaned["claims"]["receiver_id"].isin(cleaned["receivers"]["receiver_id"])
    ]

    for name, df in cleaned.items():
        print(f"  -> {name}: {len(df)} rows after cleaning")
    return cleaned


# ============================================================
# STEP 1c: SAVE — write cleaned CSVs 
# ============================================================

def save_cleaned(cleaned: dict[str, pd.DataFrame]) -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Saving cleaned CSVs to {CLEANED_DIR} ...")
    for name, df in cleaned.items():
        out_path = CLEANED_DIR / f"Cleaned_{name}.csv"
        df.to_csv(out_path, index=False)
        print(f"  -> wrote {out_path} ({len(df)} rows)")


def main() -> None:
    raw = load_raw_data()       # Step 1a: load
    cleaned = clean_all(raw)    # Step 1b: clean
    save_cleaned(cleaned)        # Step 1c: save to disk
    print("Done. Cleaned CSVs are ready in ./data/cleaned/")

# Load raw data and display its head for review
raw_dataframes = load_raw_data()

print("--- Raw Providers Data ---")
display(raw_dataframes['providers'].head())

print("--- Raw Receivers Data ---")
display(raw_dataframes['receivers'].head())

print("--- Raw Food Listings Data ---")
display(raw_dataframes['food_listings'].head())

print("--- Raw Claims Data ---")
display(raw_dataframes['claims'].head())

# Execute the main cleaning and saving process
main()

# Displaying cleaned data
print('--- Displaying cleaned providers data ---')
cleaned_providers_df = pd.read_csv(CLEANED_DIR / 'Cleaned_providers.csv')
display(cleaned_providers_df.head())

print('--- Displaying cleaned receivers data ---')
cleaned_receivers_df = pd.read_csv(CLEANED_DIR / 'Cleaned_receivers.csv')
display(cleaned_receivers_df.head())

print('--- Displaying cleaned food listings data ---')
cleaned_food_listings_df = pd.read_csv(CLEANED_DIR / 'Cleaned_food_listings.csv')
display(cleaned_food_listings_df.head())

print('--- Displaying cleaned claims data ---')
cleaned_claims_df = pd.read_csv(CLEANED_DIR / 'Cleaned_claims.csv')
display(cleaned_claims_df.head())

import shutil
import google.colab.files

# Create a zip archive of the cleaned files
archive_name = 'cleaned_data'
shutil.make_archive(archive_name, 'zip', CLEANED_DIR)

# Download the zip file
google.colab.files.download(f'{archive_name}.zip')
print(f"Downloaded {archive_name}.zip containing all cleaned CSVs.")