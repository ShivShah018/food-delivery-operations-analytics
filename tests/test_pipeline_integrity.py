"""
Pipeline integrity tests — run against actual cleaned data.

These tests verify that the pipeline produces expected output shapes
and no critical data loss occurs.

Run:  pytest tests/test_pipeline_integrity.py -v
"""

import pandas as pd
from pathlib import Path

CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "cleaned"
PROC_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


class TestDataExists:
    def test_cleaned_customers_exist(self):
        assert (CLEAN_DIR / "customers_clean.csv").exists()

    def test_cleaned_orders_exist(self):
        assert (CLEAN_DIR / "orders_clean.csv").exists()

    def test_cleaned_restaurants_exist(self):
        assert (CLEAN_DIR / "restaurants_clean.csv").exists()

    def test_cleaned_drivers_exist(self):
        assert (CLEAN_DIR / "drivers_clean.csv").exists()

    def test_processed_features_exist(self):
        assert (PROC_DIR / "customer_features.csv").exists()


class TestRowCounts:
    @classmethod
    def setup_class(cls):
        cls.customers = pd.read_csv(CLEAN_DIR / "customers_clean.csv")
        cls.orders = pd.read_csv(CLEAN_DIR / "orders_clean.csv")
        cls.restaurants = pd.read_csv(CLEAN_DIR / "restaurants_clean.csv")
        cls.drivers = pd.read_csv(CLEAN_DIR / "drivers_clean.csv")
        cls.delivery = pd.read_csv(CLEAN_DIR / "delivery_logs_clean.csv")
        cls.order_items = pd.read_csv(CLEAN_DIR / "order_items_clean.csv")

    def test_customers_nonempty(self):
        assert len(self.customers) > 0

    def test_orders_nonempty(self):
        assert len(self.orders) > 0

    def test_orders_gt_customers(self):
        assert len(self.orders) > len(self.customers)

    def test_order_items_gt_orders(self):
        assert len(self.order_items) > len(self.orders)

    def test_delivery_logs_reasonable(self):
        # should be roughly 90% of orders (10% cancelled)
        ratio = len(self.delivery) / len(self.orders)
        assert 0.75 < ratio < 0.95


class TestNoNullKeys:
    @classmethod
    def setup_class(cls):
        cls.orders = pd.read_csv(CLEAN_DIR / "orders_clean.csv")
        cls.customers = pd.read_csv(CLEAN_DIR / "customers_clean.csv")
        cls.restaurants = pd.read_csv(CLEAN_DIR / "restaurants_clean.csv")

    def test_orders_have_customer_ids(self):
        assert self.orders["customer_id"].notna().all()

    def test_orders_have_restaurant_ids(self):
        assert self.orders["restaurant_id"].notna().all()

    def test_customer_ids_unique(self):
        assert self.customers["customer_id"].is_unique

    def test_restaurant_ids_unique(self):
        assert self.restaurants["restaurant_id"].is_unique


class TestForeignKeyIntegrity:
    @classmethod
    def setup_class(cls):
        cls.orders = pd.read_csv(CLEAN_DIR / "orders_clean.csv")
        cls.customers = pd.read_csv(CLEAN_DIR / "customers_clean.csv")
        cls.restaurants = pd.read_csv(CLEAN_DIR / "restaurants_clean.csv")

    def test_all_customers_exist_in_customers_table(self):
        missing = set(self.orders["customer_id"].unique()) - set(self.customers["customer_id"])
        assert len(missing) == 0, f"Missing customer_ids: {missing}"

    def test_all_restaurants_exist_in_restaurants_table(self):
        missing = set(self.orders["restaurant_id"].unique()) - set(self.restaurants["restaurant_id"])
        assert len(missing) == 0, f"Missing restaurant_ids: {missing}"
