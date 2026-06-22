import pandas as pd
from sqlalchemy import text

from db import engine


def _next_id(table: str, id_col: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COALESCE(MAX({id_col}), 0) + 1 FROM {table}")).scalar()
    return int(result)


def _execute(sql: str, params: dict) -> None:
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def read_table(table: str, limit: int = 200) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT :limit"), conn, params={"limit": limit})


# ---------------- Food listings ----------------

def add_food_listing(food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type) -> int:
    new_id = _next_id("food_listings", "food_id")
    _execute(
        """INSERT INTO food_listings
           (food_id, food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
           VALUES (:food_id, :food_name, :quantity, :expiry_date, :provider_id, :provider_type, :location, :food_type, :meal_type)""",
        dict(food_id=new_id, food_name=food_name, quantity=quantity, expiry_date=expiry_date,
             provider_id=provider_id, provider_type=provider_type, location=location,
             food_type=food_type, meal_type=meal_type),
    )
    return new_id


def update_food_listing(food_id, food_name, quantity, expiry_date, location, food_type, meal_type) -> None:
    _execute(
        """UPDATE food_listings
           SET food_name = :food_name, quantity = :quantity, expiry_date = :expiry_date,
               location = :location, food_type = :food_type, meal_type = :meal_type
           WHERE food_id = :food_id""",
        dict(food_id=food_id, food_name=food_name, quantity=quantity, expiry_date=expiry_date,
             location=location, food_type=food_type, meal_type=meal_type),
    )


def delete_food_listing(food_id: int) -> None:
    _execute("DELETE FROM food_listings WHERE food_id = :food_id", {"food_id": food_id})


# ---------------- Providers ----------------

def add_provider(name, type_, address, city, contact) -> int:
    new_id = _next_id("providers", "provider_id")
    _execute(
        """INSERT INTO providers (provider_id, name, type, address, city, contact)
           VALUES (:id, :name, :type, :address, :city, :contact)""",
        dict(id=new_id, name=name, type=type_, address=address, city=city, contact=contact),
    )
    return new_id


def delete_provider(provider_id: int) -> None:
    _execute("DELETE FROM providers WHERE provider_id = :id", {"id": provider_id})


# ---------------- Receivers ----------------

def add_receiver(name, type_, city, contact) -> int:
    new_id = _next_id("receivers", "receiver_id")
    _execute(
        """INSERT INTO receivers (receiver_id, name, type, city, contact)
           VALUES (:id, :name, :type, :city, :contact)""",
        dict(id=new_id, name=name, type=type_, city=city, contact=contact),
    )
    return new_id


def delete_receiver(receiver_id: int) -> None:
    _execute("DELETE FROM receivers WHERE receiver_id = :id", {"id": receiver_id})


# ---------------- Claims ----------------

def add_claim(food_id: int, receiver_id: int, status: str = "Pending") -> int:
    new_id = _next_id("claims", "claim_id")
    _execute(
        """INSERT INTO claims (claim_id, food_id, receiver_id, status, timestamp)
           VALUES (:id, :food_id, :receiver_id, :status, NOW())""",
        dict(id=new_id, food_id=food_id, receiver_id=receiver_id, status=status),
    )
    return new_id


def update_claim_status(claim_id: int, status: str) -> None:
    _execute("UPDATE claims SET status = :status WHERE claim_id = :id", {"status": status, "id": claim_id})


def delete_claim(claim_id: int) -> None:
    _execute("DELETE FROM claims WHERE claim_id = :id", {"id": claim_id})
