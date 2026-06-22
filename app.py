from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

import crud
import queries as q
from db import engine, test_connection

st.set_page_config(
    page_title="Local Food Wastage Management System",
    page_icon="🥗",
    layout="wide",
)

GREEN = "#2F5233"
GOLD = "#C98A1D"
PLOTLY_COLORS = [GREEN, GOLD, "#6B8F71", "#8C5E2A", "#A3B18A"]

st.markdown(
    """
    <style>
    h1, h2, h3 { font-weight: 700; }
    .stMetric { background-color: #EAEFE8; padding: 0.6rem; border-radius: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def distinct_values(table: str, column: str) -> list:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT DISTINCT {column} FROM {table} ORDER BY {column}")).fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------- sidebar
st.sidebar.title("🥗 Food Wastage MS")
page = st.sidebar.radio(
    "Go to",
    ["Overview", "Browse & Claim Food", "Directory", "Manage Data", "Analytics"],
)

if not test_connection():
    st.error(
        "Can't reach the database. Check your `.env` file (DB_HOST / DB_USER / "
        "DB_PASSWORD / DB_NAME) and confirm PostgreSQL is running."
    )
    st.stop()

# ============================================================ OVERVIEW
if page == "Overview":
    st.title("Local Food Wastage Management System")
    st.caption("Connecting surplus food from providers to the people and organizations who need it.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Food listings", f"{len(crud.read_table('food_listings', 100000)):,}")
    c2.metric("Total quantity available", f"{q.total_quantity_available():,} units")
    c3.metric("Registered providers", f"{len(crud.read_table('providers', 100000)):,}")
    c4.metric("Registered receivers", f"{len(crud.read_table('receivers', 100000)):,}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Claims by status")
        status_df = q.claim_status_breakdown()
        fig = px.pie(status_df, names="status", values="claim_count", color_discrete_sequence=PLOTLY_COLORS, hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Food type mix")
        type_df = q.food_type_distribution()
        fig = px.bar(type_df, x="food_type", y="listing_count", color_discrete_sequence=[GREEN])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Food at the highest risk of being wasted")
    st.caption("Earliest-expiring listings that have never received a completed claim.")
    st.dataframe(q.expiring_unclaimed_food(10), use_container_width=True, hide_index=True)

# ============================================================ BROWSE & CLAIM
elif page == "Browse & Claim Food":
    st.title("Browse available food")

    with st.expander("Filters", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        cities = ["All"] + distinct_values("food_listings", "location")
        food_types = ["All"] + distinct_values("food_listings", "food_type")
        meal_types = ["All"] + distinct_values("food_listings", "meal_type")
        provider_types = ["All"] + distinct_values("food_listings", "provider_type")

        city_f = fc1.selectbox("City", cities)
        food_type_f = fc2.selectbox("Food type", food_types)
        meal_type_f = fc3.selectbox("Meal type", meal_types)
        provider_type_f = fc4.selectbox("Provider type", provider_types)

    sql = """
        SELECT f.food_id, f.food_name, f.quantity, f.expiry_date, f.location,
               f.food_type, f.meal_type, f.provider_type, p.name AS provider_name, p.contact
        FROM food_listings f
        JOIN providers p ON p.provider_id = f.provider_id
        WHERE (:city = 'All' OR f.location = :city)
          AND (:food_type = 'All' OR f.food_type = :food_type)
          AND (:meal_type = 'All' OR f.meal_type = :meal_type)
          AND (:provider_type = 'All' OR f.provider_type = :provider_type)
        ORDER BY f.expiry_date ASC
    """
    with engine.connect() as conn:
        results = pd.read_sql(
            text(sql), conn,
            params={"city": city_f, "food_type": food_type_f, "meal_type": meal_type_f, "provider_type": provider_type_f},
        )

    st.write(f"**{len(results)}** listings match your filters.")
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.subheader("File a claim")
    if results.empty:
        st.info("No listings match the current filters, so there's nothing to claim yet.")
    else:
        with st.form("claim_form"):
            food_choice = st.selectbox(
                "Food item",
                results["food_id"],
                format_func=lambda fid: f"#{fid} — {results.loc[results.food_id == fid, 'food_name'].iloc[0]}",
            )
            receivers_df = crud.read_table("receivers", 100000)
            receiver_choice = st.selectbox(
                "Receiver",
                receivers_df["receiver_id"],
                format_func=lambda rid: f"#{rid} — {receivers_df.loc[receivers_df.receiver_id == rid, 'name'].iloc[0]}",
            )
            submitted = st.form_submit_button("Claim this food")
            if submitted:
                claim_id = crud.add_claim(int(food_choice), int(receiver_choice), status="Pending")
                st.success(f"Claim #{claim_id} created with status Pending.")

# ============================================================ DIRECTORY
elif page == "Directory":
    st.title("Provider & receiver directory")
    tab1, tab2 = st.tabs(["Providers", "Receivers"])

    with tab1:
        cities = ["All"] + distinct_values("providers", "city")
        city_choice = st.selectbox("Filter by city", cities, key="prov_city")
        df = crud.read_table("providers", 100000)
        if city_choice != "All":
            df = df[df["city"] == city_choice]
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        cities = ["All"] + distinct_values("receivers", "city")
        city_choice2 = st.selectbox("Filter by city", cities, key="recv_city")
        df2 = crud.read_table("receivers", 100000)
        if city_choice2 != "All":
            df2 = df2[df2["city"] == city_choice2]
        st.dataframe(df2, use_container_width=True, hide_index=True)

# ============================================================ MANAGE DATA
elif page == "Manage Data":
    st.title("Manage data")
    tab_food, tab_prov, tab_recv, tab_claims = st.tabs(["Food listings", "Providers", "Receivers", "Claims"])

    # ---- Food listings ----
    with tab_food:
        st.subheader("Add a food listing")
        with st.form("add_food"):
            col1, col2, col3 = st.columns(3)
            food_name = col1.text_input("Food name")
            quantity = col2.number_input("Quantity", min_value=1, step=1)
            expiry = col3.date_input("Expiry date", value=date.today())
            providers_df = crud.read_table("providers", 100000)
            provider_choice = st.selectbox(
                "Provider",
                providers_df["provider_id"],
                format_func=lambda pid: f"#{pid} — {providers_df.loc[providers_df.provider_id == pid, 'name'].iloc[0]}",
            )
            col4, col5, col6 = st.columns(3)
            provider_type = col4.text_input("Provider type", value="Restaurant")
            location = col5.text_input("Location (city)")
            food_type = col6.selectbox("Food type", ["Vegetarian", "Vegan", "Non-Vegetarian"])
            meal_type = st.selectbox("Meal type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            if st.form_submit_button("Add listing"):
                if food_name and location:
                    fid = crud.add_food_listing(
                        food_name, int(quantity), expiry, int(provider_choice),
                        provider_type, location, food_type, meal_type,
                    )
                    st.success(f"Added listing #{fid}.")
                else:
                    st.warning("Food name and location are required.")

        st.subheader("Existing listings")
        food_df = crud.read_table("food_listings", 200)
        st.dataframe(food_df, use_container_width=True, hide_index=True)
        del_id = st.number_input("Food ID to delete", min_value=0, step=1, key="del_food")
        if st.button("Delete listing", key="del_food_btn") and del_id:
            crud.delete_food_listing(int(del_id))
            st.success(f"Deleted listing #{int(del_id)}.")
            st.rerun()

    # ---- Providers ----
    with tab_prov:
        st.subheader("Add a provider")
        with st.form("add_provider"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name")
            type_ = col2.text_input("Type", value="Restaurant")
            address = st.text_input("Address")
            col3, col4 = st.columns(2)
            city = col3.text_input("City")
            contact = col4.text_input("Contact")
            if st.form_submit_button("Add provider"):
                if name and city:
                    pid = crud.add_provider(name, type_, address, city, contact)
                    st.success(f"Added provider #{pid}.")
                else:
                    st.warning("Name and city are required.")

        st.subheader("Existing providers")
        st.dataframe(crud.read_table("providers", 200), use_container_width=True, hide_index=True)
        del_pid = st.number_input("Provider ID to delete", min_value=0, step=1, key="del_prov")
        if st.button("Delete provider", key="del_prov_btn") and del_pid:
            crud.delete_provider(int(del_pid))
            st.success(f"Deleted provider #{int(del_pid)}.")
            st.rerun()

    # ---- Receivers ----
    with tab_recv:
        st.subheader("Add a receiver")
        with st.form("add_receiver"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name", key="recv_name")
            type_ = col2.text_input("Type", value="NGO", key="recv_type")
            col3, col4 = st.columns(2)
            city = col3.text_input("City", key="recv_city_add")
            contact = col4.text_input("Contact", key="recv_contact")
            if st.form_submit_button("Add receiver"):
                if name and city:
                    rid = crud.add_receiver(name, type_, city, contact)
                    st.success(f"Added receiver #{rid}.")
                else:
                    st.warning("Name and city are required.")

        st.subheader("Existing receivers")
        st.dataframe(crud.read_table("receivers", 200), use_container_width=True, hide_index=True)
        del_rid = st.number_input("Receiver ID to delete", min_value=0, step=1, key="del_recv")
        if st.button("Delete receiver", key="del_recv_btn") and del_rid:
            crud.delete_receiver(int(del_rid))
            st.success(f"Deleted receiver #{int(del_rid)}.")
            st.rerun()

    # ---- Claims ----
    with tab_claims:
        st.subheader("Update a claim's status")
        claims_df = crud.read_table("claims", 200)
        st.dataframe(claims_df, use_container_width=True, hide_index=True)
        col1, col2, col3 = st.columns(3)
        claim_id = col1.number_input("Claim ID", min_value=0, step=1)
        new_status = col2.selectbox("New status", ["Pending", "Completed", "Cancelled"])
        if col3.button("Update status") and claim_id:
            crud.update_claim_status(int(claim_id), new_status)
            st.success(f"Claim #{int(claim_id)} set to {new_status}.")
            st.rerun()

        del_cid = st.number_input("Claim ID to delete", min_value=0, step=1, key="del_claim")
        if st.button("Delete claim", key="del_claim_btn") and del_cid:
            crud.delete_claim(int(del_cid))
            st.success(f"Deleted claim #{int(del_cid)}.")
            st.rerun()

# ============================================================ ANALYTICS
elif page == "Analytics":
    st.title("Analytics — the 15 required queries")

    choice = st.selectbox("Pick a query", list(q.QUERY_REGISTRY.keys()))
    df = q.QUERY_REGISTRY[choice]()
    st.dataframe(df, use_container_width=True, hide_index=True)

    # A couple of these queries are naturally chart-friendly; show one when relevant.
    if "city" in df.columns and "listing_count" in df.columns:
        st.plotly_chart(px.bar(df, x="city", y="listing_count", color_discrete_sequence=[GREEN]), use_container_width=True)
    elif "food_type" in df.columns and "listing_count" in df.columns:
        st.plotly_chart(px.pie(df, names="food_type", values="listing_count", color_discrete_sequence=PLOTLY_COLORS), use_container_width=True)
    elif "meal_type" in df.columns and "claim_count" in df.columns:
        st.plotly_chart(px.bar(df, x="meal_type", y="claim_count", color_discrete_sequence=[GOLD]), use_container_width=True)
    elif "status" in df.columns and "percentage" in df.columns:
        st.plotly_chart(px.pie(df, names="status", values="percentage", color_discrete_sequence=PLOTLY_COLORS), use_container_width=True)
    elif "month" in df.columns and "claim_count" in df.columns:
        st.plotly_chart(px.line(df, x="month", y="claim_count", markers=True), use_container_width=True)

    st.divider()
    st.subheader("Query 3 — provider contacts in a specific city")
    city = st.selectbox("City", distinct_values("providers", "city"), key="q3_city")
    st.dataframe(q.provider_contacts_by_city(city), use_container_width=True, hide_index=True)
