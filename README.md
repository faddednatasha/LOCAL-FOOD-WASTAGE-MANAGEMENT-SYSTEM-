# 🥗 Local Food Wastage Management System
 
A **Streamlit + SQL** web app that connects surplus food from providers (restaurants, caterers, etc.) with receivers (NGOs, individuals) to reduce local food wastage.
 
**🔗 Live App:** [food-waste-management-system-aayushi.streamlit.app](https://food-waste-management-system-aayushi.streamlit.app/)
 
---
 
## ✨ Features
 
- **Overview Dashboard** — key metrics, claim-status breakdown, food-type distribution, and food at risk of expiring unclaimed
- **Browse & Claim Food** — filter listings by city, food type, meal type, and provider type, then file a claim
- **Directory** — browse registered providers and receivers by city
- **Manage Data (CRUD)** — add/delete food listings, providers, receivers; update or delete claim statuses
- **Analytics** — 15 pre-built SQL queries on donation patterns, city activity, and claim trends, with charts
---
 
## 🖥️ Tech Stack
 
Python · Streamlit · Pandas · SQLAlchemy (SQLite) · Plotly
 
---
 
## 📂 Project Structure
 
```
├── app.py               # Streamlit app (UI & pages)
├── crud.py               # Create/Read/Update/Delete helpers
├── db.py                 # DB engine setup + auto-seeding
├── load_to_db.py         # Cleans raw CSVs & loads them into the DB
├── queries.py             # 15 analytical queries used in the Analytics page
├── requirements.txt
├── RAW DATA/               # Original CSV datasets
├── CLEANED DATA/           # Cleaned CSV datasets
├── PREPROCESSING AND CLEANING/  # Data cleaning script
├── EDA/                     # Exploratory data analysis notebook
└── SQL/
    ├── schema.sql          # Table definitions
    └── queries.sql         # Raw SQL for the 15 analytical questions
```
 
---
 
## 🚀 Getting Started
 
```bash
git clone https://github.com/<your-username>/LOCAL-FOOD-WASTAGE-MANAGEMENT-SYSTEM.git
cd LOCAL-FOOD-WASTAGE-MANAGEMENT-SYSTEM
pip install -r requirements.txt
streamlit run app.py
```
 
The app uses a local SQLite database and auto-seeds itself from `RAW DATA/` on first run — no manual setup needed.
 
To rebuild the database from scratch at any time:
 
```bash
python load_to_db.py
```
 
