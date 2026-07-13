"""
Tests for feature_engineering module.

Run:  pytest tests/test_features.py -v
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.feature_engineering import (
    build_customer_features,
    build_driver_features,
    build_time_series,
)


class TestCustomerFeatures:
    def test_rfm_columns_present(self):
        orders = pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C1"],
            "restaurant_id": ["R1", "R2"],
            "order_date": ["2023-06-01", "2023-07-01"],
            "total_amount": [500, 300],
            "discount": [50, 0],
            "order_status": ["Delivered", "Delivered"],
            "payment_method": ["UPI", "UPI"],
        })
        customers = pd.DataFrame({
            "customer_id": ["C1"],
            "name": ["Alice"],
            "age": [25],
            "gender": ["Female"],
            "city": ["Mumbai"],
            "latitude": [19.0],
            "longitude": [72.8],
            "phone": ["123"],
            "email": ["a@b.com"],
            "signup_date": ["2023-01-01"],
            "is_active": [True],
        })
        result = build_customer_features(orders, customers)
        assert "customer_segment" in result.columns
        assert "monetary" in result.columns
        assert "frequency" in result.columns
        assert "recency_days" in result.columns
        assert result["monetary"].iloc[0] == 800
        assert result["frequency"].iloc[0] == 2

    def test_empty_orders_returns_defaults(self):
        orders = pd.DataFrame(columns=["order_id", "customer_id", "restaurant_id", "order_date",
                                        "total_amount", "discount", "order_status", "payment_method"])
        customers = pd.DataFrame({
            "customer_id": ["C1"],
            "name": ["Bob"],
            "age": [30],
            "gender": ["Male"],
            "city": ["Delhi"],
            "latitude": [28.0],
            "longitude": [77.1],
            "phone": ["456"],
            "email": ["b@c.com"],
            "signup_date": ["2023-01-01"],
            "is_active": [True],
        })
        result = build_customer_features(orders, customers)
        assert result["customer_segment"].iloc[0] == "New"
        assert result["monetary"].iloc[0] == 0


class TestDriverFeatures:
    def test_driver_score_computed(self):
        logs = pd.DataFrame({
            "delivery_id": ["D1", "D2"],
            "order_id": ["O1", "O2"],
            "driver_id": ["DRV1", "DRV1"],
            "pickup_datetime": ["2023-01-01 12:00", "2023-01-02 12:00"],
            "drop_datetime": ["2023-01-01 12:30", "2023-01-02 12:25"],
            "distance_km": [5.0, 6.0],
            "travel_time_mins": [30, 25],
            "traffic_condition": ["Low", "Low"],
            "weather_condition": ["Clear", "Clear"],
            "is_on_time": [True, True],
        })
        drivers = pd.DataFrame({
            "driver_id": ["DRV1"],
            "name": ["Driver1"],
            "age": [30],
            "city": ["Mumbai"],
            "latitude": [19.0],
            "longitude": [72.8],
            "vehicle_type": ["Motorcycle"],
            "rating": [4.5],
            "join_date": ["2022-01-01"],
            "is_active": [True],
        })
        result = build_driver_features(logs, drivers)
        assert "efficiency_score" in result.columns
        assert result["efficiency_score"].iloc[0] > 0


class TestTimeSeries:
    def test_daily_and_monthly_returned(self):
        orders = pd.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "customer_id": ["C1", "C2", "C1"],
            "restaurant_id": ["R1", "R2", "R1"],
            "order_date": ["2023-01-01", "2023-01-01", "2023-02-01"],
            "total_amount": [100, 200, 300],
            "discount": [10, 0, 20],
            "delivery_fee": [30, 20, 25],
            "order_status": ["Delivered", "Delivered", "Delivered"],
        })
        daily, monthly = build_time_series(orders)
        assert len(daily) == 2  # two distinct dates
        assert len(monthly) == 2  # Jan and Feb
        assert daily["revenue"].sum() == 600
