"""
SwiftDash — synthetic data generation.

Produces 6 relational CSV files (customers, restaurants, drivers,
orders, order_items, delivery_logs) with realistic distributions.
"""

import sys
import logging
import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import RAW_DIR, GEN_CONFIG, ON_TIME_CUTOFF_MINUTES, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("generate_data")

SEED = GEN_CONFIG["seed"]
np.random.seed(SEED)
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

START_DATE = datetime.strptime(GEN_CONFIG["start_date"], "%Y-%m-%d")
END_DATE = datetime.strptime(GEN_CONFIG["end_date"], "%Y-%m-%d")
DAYS_RANGE = (END_DATE - START_DATE).days

N_CUSTOMERS = GEN_CONFIG["n_customers"]
N_RESTAURANTS = GEN_CONFIG["n_restaurants"]
N_DRIVERS = GEN_CONFIG["n_drivers"]
TOTAL_ORDERS = GEN_CONFIG["total_orders"]

# ── static data ────────────────────────────────────────────────
INDIAN_CITIES = [
    ("Mumbai", 19.0760, 72.8777), ("Delhi", 28.7041, 77.1025),
    ("Bangalore", 12.9716, 77.5946), ("Hyderabad", 17.3850, 78.4867),
    ("Chennai", 13.0827, 80.2707), ("Kolkata", 22.5726, 88.3639),
    ("Pune", 18.5204, 73.8567), ("Ahmedabad", 23.0225, 72.5714),
    ("Jaipur", 26.9124, 75.7873), ("Lucknow", 26.8467, 80.9462),
    ("Surat", 21.1702, 72.8311), ("Chandigarh", 30.7333, 76.7794),
    ("Bhopal", 23.2599, 77.4126), ("Indore", 22.7196, 75.8577),
    ("Coimbatore", 11.0168, 76.9558),
]

CUISINE_TYPES = [
    "North Indian", "South Indian", "Chinese", "Italian", "Fast Food",
    "Bakery", "Desserts", "Beverages", "Continental", "Mughlai",
    "Street Food", "Healthy", "Seafood", "Korean", "Japanese",
]

ITEM_MENU = {c: [f"{c} Item {i}" for i in range(1, 6)] for c in CUISINE_TYPES}

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet", "COD"]
TRAFFIC = ["Low", "Moderate", "High", "Gridlock"]
WEATHER = ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Foggy"]


def _city():
    return random.choice(INDIAN_CITIES)


def _order_datetime():
    d = START_DATE + timedelta(days=random.randint(0, DAYS_RANGE))
    h = random.choices(range(24), weights=[2,1,1,1,1,2,4,6,8,6,5,7,8,6,5,4,5,7,10,12,10,8,5,3])[0]
    return d.replace(hour=h, minute=random.randint(0, 59), second=random.randint(0, 59))


# ── table generators ───────────────────────────────────────────
def gen_customers(n):
    rows = []
    for i in range(1, n + 1):
        cn, lat, lng = _city()
        age = random.choices([random.randint(18, 27), random.randint(27, 40),
                              random.randint(40, 55), random.randint(55, 75)],
                             weights=[0.35, 0.35, 0.20, 0.10])[0]
        rows.append((f"CUST_{i:05d}", fake.name(), age,
                     random.choices(["Male", "Female", "Other"], weights=[0.48, 0.48, 0.04])[0],
                     cn, round(lat + random.uniform(-0.05, 0.05), 6),
                     round(lng + random.uniform(-0.05, 0.05), 6),
                     fake.phone_number(), fake.email(),
                     fake.date_between(start_date=datetime(2020, 1, 1), end_date=END_DATE),
                     random.choices([True, False], weights=[0.85, 0.15])[0]))
    return pd.DataFrame(rows, columns=["customer_id", "name", "age", "gender", "city",
                                       "latitude", "longitude", "phone", "email",
                                       "signup_date", "is_active"])


def gen_restaurants(n):
    rows = []
    for i in range(1, n + 1):
        cn, lat, lng = _city()
        cuisine = random.choice(CUISINE_TYPES)
        rows.append((f"REST_{i:03d}",
                     fake.company() + " " + random.choice(["Kitchen", "Foods", "Eatery", "Bites", "Cafe"]),
                     cuisine, cn, round(lat + random.uniform(-0.02, 0.02), 6),
                     round(lng + random.uniform(-0.02, 0.02), 6),
                     round(random.uniform(1.0, 5.0), 1), random.randint(150, 1200),
                     fake.date_between(start_date=datetime(2019, 1, 1), end_date=datetime(2024, 12, 31)),
                     random.choices([True, False], weights=[0.90, 0.10])[0],
                     int(np.random.gamma(3, 5)) + 5))
    return pd.DataFrame(rows, columns=["restaurant_id", "name", "cuisine_type", "city",
                                       "latitude", "longitude", "rating", "avg_cost_for_two",
                                       "join_date", "is_active", "preparation_time_mins"])


def gen_drivers(n):
    rows = []
    for i in range(1, n + 1):
        cn, lat, lng = _city()
        rows.append((f"DRV_{i:04d}", fake.name(), random.randint(20, 50),
                     cn, round(lat + random.uniform(-0.05, 0.05), 6),
                     round(lng + random.uniform(-0.05, 0.05), 6),
                     random.choices(["Bicycle", "Motorcycle", "Scooter", "Car"], weights=[0.15, 0.50, 0.25, 0.10])[0],
                     round(random.uniform(3.0, 5.0), 1),
                     fake.date_between(start_date=datetime(2020, 6, 1), end_date=datetime(2024, 12, 31)),
                     random.choices([True, False], weights=[0.80, 0.20])[0]))
    return pd.DataFrame(rows, columns=["driver_id", "name", "age", "city", "latitude",
                                       "longitude", "vehicle_type", "rating", "join_date", "is_active"])


def gen_orders(customers, restaurants, drivers, n):
    active_c = customers[customers["is_active"]].to_dict("records")
    active_r = restaurants[restaurants["is_active"]].to_dict("records")
    active_d = drivers[drivers["is_active"]].to_dict("records")
    rows = []
    for i in range(1, n + 1):
        cust = random.choice(active_c)
        rest = random.choice(active_r)
        drv = random.choice(active_d)
        dt = _order_datetime()

        order_amt = round(random.uniform(80, 800), 2)
        del_fee = round(random.choices([0, random.uniform(10, 60)], weights=[0.15, 0.85])[0], 2)
        disc = round(random.choices([0, random.uniform(5, order_amt * 0.3)], weights=[0.6, 0.4])[0], 2)
        surge = 1.0
        if 18 <= dt.hour <= 21 and dt.weekday() >= 5:
            surge = round(random.uniform(1.1, 1.5), 2)
        taxable = order_amt + del_fee
        tax = round(taxable * 0.05, 2)
        plat_fee = round(random.uniform(3, 10), 2)
        total = round((taxable + tax + plat_fee - disc) * surge, 2)

        status = random.choices(["Delivered", "Cancelled", "Delivered", "Delivered", "Refunded"],
                                weights=[0.78, 0.08, 0.10, 0.02, 0.02])[0]
        rating = None
        if status == "Delivered":
            rating = random.choices([random.randint(1, 3), random.randint(4, 5)], weights=[0.15, 0.85])[0]

        rows.append((f"ORD_{i:05d}", cust["customer_id"], rest["restaurant_id"],
                     drv["driver_id"] if status != "Cancelled" else None,
                     dt, dt.date(), dt.hour, dt.strftime("%A"), dt.weekday() >= 5,
                     order_amt, del_fee, disc, tax, plat_fee, surge, total,
                     random.choices(PAYMENT_METHODS, weights=[0.45, 0.20, 0.10, 0.05, 0.10, 0.10])[0],
                     status, cust["city"], rest["city"], rating))
    return pd.DataFrame(rows, columns=["order_id", "customer_id", "restaurant_id", "driver_id",
                                       "order_datetime", "order_date", "order_hour", "weekday",
                                       "is_weekend", "order_amount", "delivery_fee", "discount",
                                       "tax", "platform_fee", "surge_multiplier", "total_amount",
                                       "payment_method", "order_status", "customer_city",
                                       "restaurant_city", "customer_rating"])


def gen_order_items(orders, restaurants):
    cuisine_map = restaurants.set_index("restaurant_id")["cuisine_type"].to_dict()
    delivered = orders[orders["order_status"] != "Cancelled"]
    rows = []
    oid = 1
    for _, row in delivered.iterrows():
        cuisine = cuisine_map.get(row["restaurant_id"], "Fast Food")
        menu = ITEM_MENU.get(cuisine, ITEM_MENU["Fast Food"])
        n = random.choices([1, 2, 3, 4, 5], weights=[0.30, 0.35, 0.20, 0.10, 0.05])[0]
        selected = random.sample(menu, min(n, len(menu)))
        remaining = row["order_amount"]
        for j, name in enumerate(selected):
            qty = random.choices([1, 2, 3], weights=[0.65, 0.25, 0.10])[0]
            up = round(remaining / qty, 2) if j == len(selected) - 1 else round(random.uniform(50, 350), 2)
            lt = round(qty * up, 2)
            remaining -= lt
            rows.append((oid, row["order_id"], name, cuisine, qty, up, lt))
            oid += 1
    return pd.DataFrame(rows, columns=["order_item_id", "order_id", "item_name", "category",
                                       "quantity", "unit_price", "line_total"])


def gen_delivery_logs(orders):
    delivered = orders[orders["order_status"].isin(["Delivered", "Refunded"])]
    rows = []
    for _, row in delivered.iterrows():
        pickup = row["order_datetime"] + timedelta(minutes=random.randint(0, 20))
        travel = int(np.random.gamma(4, 5)) + 5
        drop = pickup + timedelta(minutes=travel)
        rows.append((f"DEL_{row['order_id']}", row["order_id"], row["driver_id"], pickup, drop,
                     round(random.uniform(0.5, 15.0), 2), travel,
                     random.choices(TRAFFIC, weights=[0.30, 0.35, 0.25, 0.10])[0],
                     random.choices(WEATHER, weights=[0.50, 0.25, 0.15, 0.07, 0.03])[0],
                     travel <= ON_TIME_CUTOFF_MINUTES))
    return pd.DataFrame(rows, columns=["delivery_id", "order_id", "driver_id", "pickup_datetime",
                                       "drop_datetime", "distance_km", "travel_time_mins",
                                       "traffic_condition", "weather_condition", "is_on_time"])


def main():
    logger.info("=" * 50)
    logger.info("START: Data generation")
    logger.info("=" * 50)

    try:
        logger.info("Generating customers (%s)...", N_CUSTOMERS)
        customers = gen_customers(N_CUSTOMERS)
        customers.to_csv(RAW_DIR / "customers.csv", index=False)
        logger.info("  customers: %s rows", len(customers))

        logger.info("Generating restaurants (%s)...", N_RESTAURANTS)
        restaurants = gen_restaurants(N_RESTAURANTS)
        restaurants.to_csv(RAW_DIR / "restaurants.csv", index=False)
        logger.info("  restaurants: %s rows", len(restaurants))

        logger.info("Generating drivers (%s)...", N_DRIVERS)
        drivers = gen_drivers(N_DRIVERS)
        drivers.to_csv(RAW_DIR / "drivers.csv", index=False)
        logger.info("  drivers: %s rows", len(drivers))

        logger.info("Generating orders (%s)...", TOTAL_ORDERS)
        orders = gen_orders(customers, restaurants, drivers, TOTAL_ORDERS)
        orders.to_csv(RAW_DIR / "orders.csv", index=False)
        logger.info("  orders: %s rows", len(orders))

        logger.info("Generating order items & delivery logs...")
        oi = gen_order_items(orders, restaurants)
        oi.to_csv(RAW_DIR / "order_items.csv", index=False)
        logger.info("  order_items: %s rows", len(oi))

        dl = gen_delivery_logs(orders)
        dl.to_csv(RAW_DIR / "delivery_logs.csv", index=False)
        logger.info("  delivery_logs: %s rows", len(dl))

        logger.info("=" * 50)
        logger.info("Data generation complete.")
        logger.info("=" * 50)
    except Exception as exc:
        logger.critical("Data generation failed: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()
