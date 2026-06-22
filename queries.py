import pandas as pd

# --- Load Datasets ---
providers = pd.read_csv('RAW DATA/providers_data.csv')
claims = pd.read_csv('RAW DATA/claims_data.csv')
food_listings = pd.read_csv('RAW DATA/food_listings_data.csv')
receivers = pd.read_csv('RAW DATA/receivers_data.csv')

# Force data column matrices to lowercase matching the database tables
providers.columns = [c.lower() for c in providers.columns]
claims.columns = [c.lower() for c in claims.columns]
food_listings.columns = [c.lower() for c in food_listings.columns]
receivers.columns = [c.lower() for c in receivers.columns]

# --- Overview Metrics Helpers (For App.py Home Page) ---
def total_quantity_available():
    return int(food_listings["quantity"].sum())

def claim_status_breakdown():
    df = claims["status"].value_counts().reset_index()
    df.columns = ["status", "claim_count"]
    return df

def food_type_distribution():
    df = food_listings["food_type"].value_counts().reset_index()
    df.columns = ["food_type", "listing_count"]
    return df

def expiring_unclaimed_food(limit=10):
    completed_ids = claims[claims["status"].str.lower() == "completed"]["food_id"]
    unclaimed = food_listings[~food_listings["food_id"].isin(completed_ids)].copy()
    unclaimed["expiry_date"] = pd.to_datetime(unclaimed["expiry_date"])
    unclaimed = unclaimed.sort_values(by="expiry_date", ascending=True)
    return unclaimed.head(limit)

# --- The 15 Core Queries Structured For The Analytics Page ---
def get_city_provider_receiver_counts():
    prov_counts = providers.groupby("city")["provider_id"].nunique().reset_index(name="providers")
    rec_counts = receivers.groupby("city")["receiver_id"].nunique().reset_index(name="receivers")
    df_city_split = pd.merge(prov_counts, rec_counts, on="city", how="outer").fillna(0)
    df_city_split["total_presence"] = df_city_split["providers"] + df_city_split["receivers"]
    return df_city_split.sort_values(by="total_presence", ascending=False)

def get_provider_type_contributions():
    return food_listings.groupby("provider_type")["quantity"].sum().reset_index(name="listing_count").rename(columns={"provider_type": "food_type"}).sort_values(by="listing_count", ascending=False)

def provider_contacts_by_city(city_name):
    return providers[providers["city"] == city_name][["name", "type", "address", "contact"]]

def get_top_receivers_by_quantity():
    completed_claims = claims[claims["status"].str.lower() == "completed"]
    m_rec = completed_claims.merge(receivers, on="receiver_id").merge(food_listings, on="food_id")
    return m_rec.groupby("name")["quantity"].sum().reset_index(name="claim_count").rename(columns={"name": "meal_type"}).sort_values(by="claim_count", ascending=False).head(10)

def get_total_food_available_summary():
    return pd.DataFrame([{"Metric": "Total Food Quantity Available", "Value": total_quantity_available()}])

def get_top_listing_cities():
    df = food_listings["location"].value_counts().reset_index(name="listing_count")
    return df.rename(columns={"location": "city"}).head(10)

def get_common_food_types():
    df = food_listings["food_type"].value_counts().reset_index(name="listing_count")
    return df.rename(columns={"food_type": "food_type"})

def get_claims_per_food_item():
    return food_listings.merge(claims, on="food_id", how="left").groupby(["food_id", "food_name"]).size().reset_index(name="Claim_Count").sort_values(by="Claim_Count", ascending=False).head(15)

def get_top_providers_by_successful_claims():
    completed_claims = claims[claims["status"].str.lower() == "completed"]
    m_prov = completed_claims.merge(receivers, on="receiver_id", suffixes=('', '_rec')).merge(food_listings, on="food_id").merge(providers, on="provider_id", suffixes=('', '_prov'))
    return m_prov.groupby("name_prov").size().reset_index(name="completed_claims").sort_values(by="completed_claims", ascending=False).head(10)

def get_claim_status_percentages():
    df = claims["status"].value_counts(normalize=True).reset_index()
    df.columns = ["status", "percentage"]
    df["percentage"] = (df["percentage"] * 100).round(2)
    return df

def get_average_quantity_per_receiver():
    completed_claims = claims[claims["status"].str.lower() == "completed"]
    m_rec = completed_claims.merge(receivers, on="receiver_id").merge(food_listings, on="food_id")
    avg_val = m_rec.groupby("receiver_id")["quantity"].sum().mean()
    return pd.DataFrame([{"Metric": "Average Quantity Claimed Per Receiver", "Value": round(avg_val, 2)}])

def get_most_claimed_meal_types():
    df = claims.merge(food_listings, on="food_id").groupby("meal_type").size().reset_index(name="claim_count")
    return df.rename(columns={"meal_type": "meal_type"}).sort_values(by="claim_count", ascending=False)

def get_total_donations_by_provider():
    return food_listings.merge(providers, on="provider_id").groupby("name")["quantity"].sum().reset_index(name="Total_Donated_Quantity").sort_values(by="Total_Donated_Quantity", ascending=False).head(15)

def get_monthly_claims_trend():
    df_claims = claims.copy()
    df_claims["timestamp"] = pd.to_datetime(df_claims["timestamp"])
    df_claims["month"] = df_claims["timestamp"].dt.to_period("M").astype(str)
    return df_claims.groupby("month").size().reset_index(name="claim_count").sort_values("month")

def get_daily_claims_trend():
    df_claims = claims.copy()
    df_claims["timestamp"] = pd.to_datetime(df_claims["timestamp"])
    df_claims["month"] = df_claims["timestamp"].dt.date.astype(str)
    return df_claims.groupby("month").size().reset_index(name="claim_count").sort_values("month")

# --- Query Registry Mapping Table ---
QUERY_REGISTRY = {
    "1. Providers & Receivers Split by City": get_city_provider_receiver_counts,
    "2. Food Volume Contributed by Provider Type": get_provider_type_contributions,
    "4. Top Receivers by Quantity Claimed": get_top_receivers_by_quantity,
    "5. Summary of Total Food Available": get_total_food_available_summary,
    "6. Top Cities by Number of Listings": get_top_listing_cities,
    "7. Most Common Food Types Distribution": get_common_food_types,
    "8. Total Claims made per Food Item": get_claims_per_food_item,
    "9. Top Providers by Successful Claims": get_top_providers_by_successful_claims,
    "10. Proportion of Claims by Status": get_claim_status_percentages,
    "11. Average Food Claim Size per Receiver": get_average_quantity_per_receiver,
    "12. Distribution of Most Claimed Meal Types": get_most_claimed_meal_types,
    "13. Total Quantity Donated per Provider": get_total_donations_by_provider,
    "14. Month-over-Month Trend of Claims Volume": get_monthly_claims_trend,
    "15. Day-over-Day Detailed Claims Trend": get_daily_claims_trend
}