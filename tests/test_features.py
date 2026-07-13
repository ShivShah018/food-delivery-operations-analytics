"""
Tests for feature_engineering module.

Run:  pytest tests/test_features.py -v
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.feature_engineering import (
    build_customer_features,
    build_restaurant_features,
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


class TestRestaurantFeatures:
    def test_cancellation_rate_computed_from_all_orders(self):
        orders = pd.DataFrame({
            "order_id": ["O1", "O2", "O3", "O4"],
            "restaurant_id": ["R1", "R1", "R1", "R2"],
            "customer_id": ["C1", "C1", "C2", "C3"],
            "total_amount": [100, 200, 300, 400],
            "discount": [0, 0, 0, 0],
            "order_status": ["Delivered", "Cancelled", "Delivered", "Cancelled"],
            "order_date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            "payment_method": ["UPI", "UPI", "UPI", "UPI"],
        })
        order_items = pd.DataFrame({
            "order_id": ["O1", "O2", "O3"],
            "quantity": [2, 1, 3],
        })
        restaurants = pd.DataFrame({
            "restaurant_id": ["R1", "R2"],
            "name": ["R1", "R2"],
            "cuisine_type": ["Indian", "Chinese"],
            "city": ["Mumbai", "Delhi"],
            "rating": [4.0, 3.5],
            "avg_cost_for_two": [500, 400],
            "join_date": ["2022-01-01", "2022-06-01"],
            "is_active": [True, True],
            "preparation_time_mins": [15, 20],
        })
        result = build_restaurant_features(orders, order_items, restaurants)
        r1 = result[result["restaurant_id"] == "R1"].iloc[0]
        r2 = result[result["restaurant_id"] == "R2"].iloc[0]
        # R1: 3 total (2 delivered + 1 cancelled) → 1/3 = 0.333
        assert r1["cancellation_rate"] == pytest.approx(1 / 3, abs=0.01)
        # R2: 1 total (1 cancelled) → 1/1 = 1.0
        assert r2["cancellation_rate"] == 1.0
        assert r1["total_orders"] == 2  # only delivered/refunded count as orders
        assert r2["total_orders"] == 0  # no delivered orders

    def test_restaurant_features_columns_present(self):
        orders = pd.DataFrame({
            "order_id": ["O1"],
            "restaurant_id": ["R1"],
            "customer_id": ["C1"],
            "total_amount": [100],
            "discount": [0],
            "order_status": ["Delivered"],
            "order_date": ["2023-01-01"],
            "payment_method": ["UPI"],
        })
        order_items = pd.DataFrame({
            "order_id": ["O1"],
            "quantity": [2],
        })
        restaurants = pd.DataFrame({
            "restaurant_id": ["R1"],
            "name": ["Test"],
            "cuisine_type": ["Indian"],
            "city": ["Mumbai"],
            "rating": [4.0],
            "avg_cost_for_two": [500],
            "join_date": ["2022-01-01"],
            "is_active": [True],
            "preparation_time_mins": [15],
        })
        result = build_restaurant_features(orders, order_items, restaurants)
        assert "cancellation_rate" in result.columns
        assert "total_orders" in result.columns
        assert "total_revenue" in result.columns
        assert "revenue_tier" in result.columns
