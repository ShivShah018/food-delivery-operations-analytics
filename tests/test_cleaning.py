"""
Unit tests for the data cleaning module.

Run with:  pytest tests/ -v
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.clean_data import (
    clean_customers,
    clean_restaurants,
    clean_drivers,
    clean_orders,
    clean_order_items,
    clean_delivery_logs,
)


# ── Fixtures ────────────────────────────────────────────────────

def sample_customers():
    return pd.DataFrame({
        "customer_id": ["C1", "C2", "C3", None],
        "name": ["Alice", "Bob", "Charlie", "Dave"],
        "age": [25, 150, -5, 30],
        "gender": ["male", "FEMALE", "Unknown", "female"],
        "city": [" mumbai ", "DELHI ", "bangalore", "pune"],
        "latitude": [19.0, 28.0, 12.9, 18.5],
        "longitude": [72.8, 77.1, 77.5, 73.8],
        "phone": ["+91-98765", " 9876543210 ", np.nan, "+91 98765 43210"],
        "email": ["ALICE@EMAIL.COM", "Bob@Email.com", "charlie@email.com", "dave@email.com"],
        "signup_date": ["2021-01-01", "2022-06-15", "invalid-date", "2023-03-10"],
        "is_active": [True, True, False, True],
    })


def sample_orders():
    return pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4"],
        "customer_id": ["C1", "C2", "C3", None],
        "restaurant_id": ["R1", "R2", "R3", "R4"],
        "driver_id": ["D1", "D2", None, "D4"],
        "order_datetime": ["2023-01-01 12:00", "2023-01-02 13:00", "2023-01-03 14:00", "2023-01-04 15:00"],
        "order_date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "order_hour": [12, 13, 14, 25],
        "weekday": ["Sunday", "Monday", "Tuesday", "Wednesday"],
        "is_weekend": [True, False, False, False],
        "order_amount": [500, -100, 300, 200],
        "delivery_fee": [30, 20, 0, -5],
        "discount": [50, 0, 100, 0],
        "tax": [25, 10, 15, 10],
        "platform_fee": [5, 5, 5, 5],
        "surge_multiplier": [1.0, 1.5, 1.0, 0.5],
        "total_amount": [510, 150, 220, 210],
        "payment_method": ["UPI", "Credit Card", "COD", "Wallet"],
        "order_status": ["Delivered", "Delivered", "Cancelled", "invalid"],
        "customer_city": ["mumbai", "delhi", "bangalore", "pune"],
        "restaurant_city": ["mumbai", "delhi", "bangalore", "pune"],
        "customer_rating": [5.0, 4.0, None, 1.0],
    })


def sample_order_items():
    return pd.DataFrame({
        "order_item_id": [1, 2, 3],
        "order_id": ["O1", "O1", None],
        "item_name": ["Pizza", "Burger", "Fries"],
        "category": ["Italian", "Fast Food", "Fast Food"],
        "quantity": [2, 1, -1],
        "unit_price": [250, 150, -50],
        "line_total": [500, 150, 50],
    })


# ── Tests ───────────────────────────────────────────────────────

class TestCleanCustomers:
    def test_drops_null_ids(self):
        result = clean_customers(sample_customers())
        assert "C1" in result["customer_id"].values
        assert result["customer_id"].notna().all()
        assert not result.empty

    def test_clips_age(self):
        result = clean_customers(sample_customers())
        assert result["age"].max() <= 90
        assert result["age"].min() >= 16

    def test_standardises_gender(self):
        result = clean_customers(sample_customers())
        assert result.loc[result["customer_id"] == "C1", "gender"].iloc[0] == "Male"
        assert result.loc[result["customer_id"] == "C2", "gender"].iloc[0] == "Female"

    def test_unknown_gender_becomes_other(self):
        result = clean_customers(sample_customers())
        assert result.loc[result["customer_id"] == "C3", "gender"].iloc[0] == "Other"

    def test_strips_city_names(self):
        result = clean_customers(sample_customers())
        assert result.loc[result["customer_id"] == "C1", "city"].iloc[0] == "Mumbai"

    def test_signup_date_coerces_invalid(self):
        result = clean_customers(sample_customers())
        assert pd.isna(result.loc[result["customer_id"] == "C3", "signup_date"].iloc[0])


class TestCleanOrders:
    def test_drops_null_order_id(self):
        result = clean_orders(sample_orders())
        assert result["order_id"].notna().all()

    def test_drops_null_customer(self):
        result = clean_orders(sample_orders())
        assert "O4" not in result["order_id"].values  # null customer_id

    def test_clips_hour(self):
        result = clean_orders(sample_orders())
        assert result["order_hour"].max() <= 23

    def test_removes_invalid_status(self):
        result = clean_orders(sample_orders())
        assert "invalid" not in result["order_status"].values

    def test_clips_negative_amount(self):
        result = clean_orders(sample_orders())
        assert (result["order_amount"] >= 0).all()
        assert (result["delivery_fee"] >= 0).all()

    def test_clips_surge(self):
        result = clean_orders(sample_orders())
        assert result["surge_multiplier"].min() >= 1.0


class TestCleanOrderItems:
    def test_drops_null_order_id(self):
        result = clean_order_items(sample_order_items())
        assert result["order_id"].notna().all()

    def test_clips_negative_qty(self):
        result = clean_order_items(sample_order_items())
        assert (result["quantity"] >= 1).all()

    def test_clips_negative_price(self):
        result = clean_order_items(sample_order_items())
        assert result["unit_price"].min() >= 5


class TestCleanRestaurants:
    def test_drops_null_ids(self):
        df = pd.DataFrame({
            "restaurant_id": ["R1", None],
            "name": ["A", "B"],
            "cuisine_type": ["Indian", "Chinese"],
            "city": ["Mumbai", "Delhi"],
            "latitude": [19.0, 28.0],
            "longitude": [72.8, 77.1],
            "rating": [4.0, 3.5],
            "avg_cost_for_two": [500, 300],
            "join_date": ["2022-01-01", "2022-06-01"],
            "is_active": [True, True],
            "preparation_time_mins": [15, 20],
        })
        result = clean_restaurants(df)
        assert len(result) == 1

    def test_clips_rating(self):
        df = pd.DataFrame({
            "restaurant_id": ["R1"],
            "name": ["A"],
            "cuisine_type": ["Indian"],
            "city": ["Mumbai"],
            "latitude": [19.0],
            "longitude": [72.8],
            "rating": [6.0],
            "avg_cost_for_two": [500],
            "join_date": ["2022-01-01"],
            "is_active": [True],
            "preparation_time_mins": [15],
        })
        result = clean_restaurants(df)
        assert result["rating"].iloc[0] == 5.0


class TestCleanDrivers:
    def test_drops_null_ids(self):
        df = pd.DataFrame({
            "driver_id": ["D1", None],
            "name": ["A", "B"],
            "age": [25, 30],
            "city": ["Mumbai", "Delhi"],
            "latitude": [19.0, 28.0],
            "longitude": [72.8, 77.1],
            "vehicle_type": ["Motorcycle", "Car"],
            "rating": [4.5, 3.0],
            "join_date": ["2022-01-01", "2022-06-01"],
            "is_active": [True, False],
        })
        result = clean_drivers(df)
        assert len(result) == 1

    def test_clips_age(self):
        df = pd.DataFrame({
            "driver_id": ["D1", "D2"],
            "name": ["A", "B"],
            "age": [17, 70],
            "city": ["Mumbai", "Delhi"],
            "latitude": [19.0, 28.0],
            "longitude": [72.8, 77.1],
            "vehicle_type": ["Motorcycle", "Car"],
            "rating": [4.0, 4.0],
            "join_date": ["2022-01-01", "2022-06-01"],
            "is_active": [True, True],
        })
        result = clean_drivers(df)
        assert result.loc[result["driver_id"] == "D1", "age"].iloc[0] == 18
        assert result.loc[result["driver_id"] == "D2", "age"].iloc[0] == 65


class TestCleanDeliveryLogs:
    def test_removes_invalid_traffic(self):
        df = pd.DataFrame({
            "delivery_id": ["D1"],
            "order_id": ["O1"],
            "driver_id": ["DRV1"],
            "pickup_datetime": ["2023-01-01 12:00"],
            "drop_datetime": ["2023-01-01 12:30"],
            "distance_km": [5.0],
            "travel_time_mins": [30],
            "traffic_condition": ["Invalid"],
            "weather_condition": ["Clear"],
            "is_on_time": [True],
        })
        result = clean_delivery_logs(df)
        assert result.empty
