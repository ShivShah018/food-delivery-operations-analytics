"""
Data cleaning & validation pipeline.

Reads raw CSVs from RAW_DIR, validates, standardises, and
writes cleaned CSVs to CLEAN_DIR.
"""

import sys
import logging
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import RAW_DIR, CLEAN_DIR, RAW_FILES, CLEAN_FILES, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)
logger = logging.getLogger("clean_data")


# ── helpers ────────────────────────────────────────────────────
def _load(name: str) -> pd.DataFrame:
    path = RAW_DIR / RAW_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Missing raw file: {path}")
    df = pd.read_csv(path)
    logger.info("Loaded %s (%s rows, %s cols)", path.name, len(df), len(df.columns))
    return df


def _save(df: pd.DataFrame, name: str):
    path = CLEAN_DIR / CLEAN_FILES[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved cleaned %s (%s rows)", path.name, len(df))


def _drop_invalid_ids(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=[id_col])
    if before != len(df):
        logger.warning("Dropped %s rows with null %s", before - len(df), id_col)
    return df


# ── cleaning functions ─────────────────────────────────────────
def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(subset=["customer_id"])
    df = _drop_invalid_ids(df, "customer_id")
    df = df.dropna(subset=["name", "city"])
    df["age"] = df["age"].clip(16, 90)
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    df["email"] = df["email"].str.lower().str.strip()
    df["phone"] = df.get("phone", pd.Series(dtype=str)).fillna("")
    df["phone"] = df["phone"].astype(str).str.replace(r"[^\d+]", "", regex=True)
    df["gender"] = df["gender"].str.strip().str.title()
    df["gender"] = df["gender"].where(df["gender"].isin(["Male", "Female", "Other"]), "Other")
    df["city"] = df["city"].str.strip().str.title()
    df["is_active"] = df["is_active"].astype(bool)
    logger.info("customers: %s -> %s rows", before, len(df))
    return df


def clean_restaurants(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["restaurant_id"])
    df = _drop_invalid_ids(df, "restaurant_id")
    df = df.dropna(subset=["name"])
    df["cuisine_type"] = df["cuisine_type"].str.strip().str.title()
    df["city"] = df["city"].str.strip().str.title()
    df["rating"] = df["rating"].clip(1.0, 5.0)
    df["avg_cost_for_two"] = df["avg_cost_for_two"].clip(50, 5000)
    df["preparation_time_mins"] = df["preparation_time_mins"].clip(2, 60).astype(int)
    df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
    df["is_active"] = df["is_active"].astype(bool)
    logger.info("restaurants: %s rows cleaned", len(df))
    return df


def clean_drivers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["driver_id"])
    df = _drop_invalid_ids(df, "driver_id")
    df = df.dropna(subset=["name"])
    df["age"] = df["age"].clip(18, 65)
    df["city"] = df["city"].str.strip().str.title()
    df["vehicle_type"] = df["vehicle_type"].str.strip().str.title()
    df["rating"] = df["rating"].clip(1.0, 5.0)
    df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
    df["is_active"] = df["is_active"].astype(bool)
    logger.info("drivers: %s rows cleaned", len(df))
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"])
    df = _drop_invalid_ids(df, "order_id")
    df = df.dropna(subset=["customer_id", "restaurant_id"])
    df["order_datetime"] = pd.to_datetime(df["order_datetime"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_hour"] = df["order_hour"].clip(0, 23).astype(int)
    for col in ["order_amount", "delivery_fee", "discount", "tax", "platform_fee", "total_amount"]:
        df[col] = df[col].clip(0, None)
    df["surge_multiplier"] = df["surge_multiplier"].clip(1.0, 3.0)
    df["order_status"] = df["order_status"].str.strip().str.title()
    valid = {"Delivered", "Cancelled", "Refunded"}
    df = df[df["order_status"].isin(valid)]
    df["customer_city"] = df["customer_city"].str.strip().str.title()
    df["restaurant_city"] = df["restaurant_city"].str.strip().str.title()
    df["payment_method"] = df["payment_method"].str.strip().str.title()
    logger.info("orders: %s -> %s rows", before, len(df))
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["order_item_id"])
    df = _drop_invalid_ids(df, "order_id")
    df = df.dropna(subset=["item_name"])
    df["quantity"] = df["quantity"].clip(1, 20).astype(int)
    df["unit_price"] = df["unit_price"].clip(5, 2000)
    df["line_total"] = df["line_total"].clip(0, None)
    df["category"] = df["category"].str.strip().str.title()
    df["item_name"] = df["item_name"].str.strip().str.title()
    logger.info("order_items: %s rows cleaned", len(df))
    return df


def clean_delivery_logs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(subset=["delivery_id"])
    df = _drop_invalid_ids(df, "order_id")
    df = df.dropna(subset=["driver_id"])
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"], errors="coerce")
    df["drop_datetime"] = pd.to_datetime(df["drop_datetime"], errors="coerce")
    df["distance_km"] = df["distance_km"].clip(0.1, 50.0)
    df["travel_time_mins"] = df["travel_time_mins"].clip(1, 120).astype(int)
    df["traffic_condition"] = df["traffic_condition"].str.strip().str.title()
    df["weather_condition"] = df["weather_condition"].str.strip().str.title()
    valid_traffic = {"Low", "Moderate", "High", "Gridlock"}
    valid_weather = {"Clear", "Cloudy", "Light Rain", "Heavy Rain", "Foggy"}
    df = df[df["traffic_condition"].isin(valid_traffic)]
    df = df[df["weather_condition"].isin(valid_weather)]
    logger.info("delivery_logs: %s rows cleaned", len(df))
    return df


# ── main ───────────────────────────────────────────────────────
def main():
    logger.info("=" * 50)
    logger.info("START: Data cleaning pipeline")
    logger.info("=" * 50)

    cleaners = [
        ("customers", clean_customers),
        ("restaurants", clean_restaurants),
        ("drivers", clean_drivers),
        ("orders", clean_orders),
        ("order_items", clean_order_items),
        ("delivery_logs", clean_delivery_logs),
    ]

    for name, fn in cleaners:
        try:
            df = _load(name)
            cleaned = fn(df)
            _save(cleaned, name)
        except Exception as exc:
            logger.error("Failed on %s: %s", name, exc)
            raise

    logger.info("=" * 50)
    logger.info("Data cleaning complete.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
