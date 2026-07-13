"""
Feature engineering pipeline.

Builds customer RFM features, restaurant / driver performance
metrics, and daily / monthly time-series aggregations.
"""

import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CLEAN_DIR, PROC_DIR, RAW_FILES, CLEAN_FILES, PROC_FILES, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, RFM_THRESHOLDS

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("feature_engineering")


def _load_clean(name: str) -> pd.DataFrame:
    path = CLEAN_DIR / CLEAN_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Missing cleaned file: {path}")
    return pd.read_csv(path)


def _save_processed(df: pd.DataFrame, key: str):
    path = PROC_DIR / PROC_FILES[key]
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved %s (%s rows)", PROC_FILES[key], len(df))


# ── Customer Feature Engineering ────────────────────────────────
def build_customer_features(orders: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    delivered = orders[orders["order_status"].isin(["Delivered", "Refunded"])].copy()
    delivered["order_date"] = pd.to_datetime(delivered["order_date"])
    ref_date = delivered["order_date"].max()

    rfm = delivered.groupby("customer_id").agg(
        recency_days=("order_date", lambda x: (ref_date - x.max()).days),
        frequency=("order_id", "count"),
        monetary=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
        avg_discount_used=("discount", "mean"),
        preferred_payment=("payment_method", lambda x: x.mode().iloc[0] if not x.mode().empty else "UPI"),
        cuisine_variety=("restaurant_id", "nunique"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
    ).reset_index()

    # Guard: if no orders exist, return customers with default values
    if rfm.empty:
        rfm = customers[["customer_id"]].copy()
        rfm["recency_days"] = 999
        rfm["frequency"] = 0
        rfm["monetary"] = 0.0
        rfm["avg_order_value"] = 0.0
        rfm["avg_discount_used"] = 0.0
        rfm["preferred_payment"] = "UPI"
        rfm["cuisine_variety"] = 0
        rfm["first_order_date"] = pd.NaT
        rfm["last_order_date"] = pd.NaT
        rfm["days_since_first"] = 0
        rfm["customer_segment"] = "New"
        rfm["customer_tenure_months"] = 0
        rfm["avg_order_frequency_days"] = 0
        result = customers.merge(rfm, on="customer_id", how="left")
        for col in ["recency_days", "frequency", "monetary", "avg_order_value",
                    "avg_discount_used", "days_since_first", "customer_tenure_months",
                    "avg_order_frequency_days", "cuisine_variety"]:
            result[col] = result[col].fillna(0)
        result["customer_segment"] = result["customer_segment"].fillna("New")
        result["preferred_payment"] = result["preferred_payment"].fillna("UPI")
        return result

    rfm["days_since_first"] = (ref_date - rfm["first_order_date"]).dt.days
    rfm["recency_days"] = rfm["recency_days"].astype(int)

    # ── Segment assignment ─────────────────────────────────────
    # Thresholds defined in config.py; review quarterly.
    p = RFM_THRESHOLDS["platinum"]
    g = RFM_THRESHOLDS["gold"]

    conditions = [
        (rfm["frequency"] >= p["min_orders"]) & (rfm["monetary"] >= p["min_spend"]),
        (rfm["frequency"] >= g["min_orders"]) & (rfm["monetary"] >= g["min_spend"]),
        rfm["recency_days"] <= RFM_THRESHOLDS["at_risk_days"],
        rfm["recency_days"] <= RFM_THRESHOLDS["churned_days"],
    ]
    labels = ["Platinum", "Gold", "Silver", "At Risk"]
    rfm["customer_segment"] = np.select(conditions, labels, default="Churned")
    rfm.loc[rfm["frequency"] == 0, "customer_segment"] = "New"

    rfm["customer_tenure_months"] = (rfm["days_since_first"].clip(0) // 30).fillna(0).astype(int)
    rfm["avg_order_frequency_days"] = pd.Series(
        np.where(rfm["frequency"] > 1, rfm["days_since_first"] / rfm["frequency"], 0),
        index=rfm.index,
    ).fillna(0).astype(int)

    result = customers.merge(rfm, on="customer_id", how="left")
    fill_cols = ["recency_days", "frequency", "monetary", "avg_order_value",
                 "avg_discount_used", "days_since_first", "customer_tenure_months",
                 "avg_order_frequency_days", "cuisine_variety"]
    for col in fill_cols:
        result[col] = result[col].fillna(0)
    result["customer_segment"] = result["customer_segment"].fillna("New")
    result["preferred_payment"] = result["preferred_payment"].fillna("UPI")
    result["first_order_date"] = result["first_order_date"].fillna(result["signup_date"])
    result["last_order_date"] = result["last_order_date"].fillna(result["signup_date"])

    logger.info("Customer features built: %s rows, %s segments", len(result), result["customer_segment"].nunique())
    return result


# ── Restaurant Feature Engineering ─────────────────────────────
def build_restaurant_features(orders: pd.DataFrame, order_items: pd.DataFrame, restaurants: pd.DataFrame) -> pd.DataFrame:
    delivered = orders[orders["order_status"].isin(["Delivered", "Refunded"])]

    perf = delivered.groupby("restaurant_id").agg(
        total_orders=("order_id", "count"),
        total_revenue=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
        total_discount=("discount", "sum"),
        unique_customers=("customer_id", "nunique"),
    ).reset_index()

    items = order_items.groupby("order_id")["quantity"].sum().reset_index()
    delivered = delivered.merge(items, on="order_id", how="left", suffixes=("", "_sum"))
    items_per_rest = delivered.groupby("restaurant_id")["quantity"].mean().reset_index()
    items_per_rest.columns = ["restaurant_id", "avg_items_per_order"]

    perf = perf.merge(items_per_rest, on="restaurant_id", how="left")
    result = restaurants.merge(perf, on="restaurant_id", how="left")
    for col in ["total_orders", "total_revenue", "avg_order_value", "total_discount",
                "unique_customers", "avg_items_per_order"]:
        result[col] = result[col].fillna(0)

    # Cancellation rate uses ALL orders, merged to result (not perf)
    # so restaurants with 0 delivered orders still get a correct rate.
    cancel = orders.groupby("restaurant_id")["order_status"].apply(
        lambda x: (x == "Cancelled").mean()
    ).reset_index(name="cancellation_rate")
    result = result.merge(cancel, on="restaurant_id", how="left")
    result["cancellation_rate"] = result["cancellation_rate"].fillna(0)

    result["revenue_per_customer"] = np.divide(
        result["total_revenue"], result["unique_customers"],
        where=result["unique_customers"] > 0,
        out=np.zeros_like(result["total_revenue"], dtype=float),
    )
    # Quartile-based revenue tier; low-revenue restaurants get 1-day clamp to avoid qcut failure
    try:
        result["revenue_tier"] = pd.qcut(
            result["total_revenue"].clip(lower=1), q=4,
            labels=["Low", "Medium", "High", "Top"],
            duplicates="drop",
        )
    except ValueError:
        # Edge case: too few unique values for 4 quartiles (e.g., single restaurant)
        result["revenue_tier"] = "Medium"
    logger.info("Restaurant features built: %s rows", len(result))
    return result


# ── Driver Feature Engineering ─────────────────────────────────
def build_driver_features(delivery_logs: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    perf = delivery_logs.groupby("driver_id").agg(
        total_deliveries=("delivery_id", "count"),
        avg_travel_time=("travel_time_mins", "mean"),
        avg_distance=("distance_km", "mean"),
        on_time_rate=("is_on_time", "mean"),
    ).reset_index()

    result = drivers.merge(perf, on="driver_id", how="left")
    for col in ["total_deliveries", "avg_travel_time", "avg_distance", "on_time_rate"]:
        result[col] = result[col].fillna(0)

    max_time = result["avg_travel_time"].max() or 1
    result["efficiency_score"] = (
        result["on_time_rate"] * 0.5
        + (1 - result["avg_travel_time"] / max_time) * 0.3
        + result["rating"] / 5.0 * 0.2
    ) * 100

    logger.info("Driver features built: %s rows", len(result))
    return result


# ── Time-series Aggregations ───────────────────────────────────
def build_time_series(orders: pd.DataFrame):
    delivered = orders[orders["order_status"].isin(["Delivered", "Refunded"])].copy()
    delivered["order_date"] = pd.to_datetime(delivered["order_date"])
    delivered["year_month"] = delivered["order_date"].dt.to_period("M").astype(str)

    daily = delivered.groupby("order_date", as_index=False).agg(
        orders_count=("order_id", "nunique"),
        revenue=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
        unique_customers=("customer_id", "nunique"),
        unique_restaurants=("restaurant_id", "nunique"),
    )

    monthly = delivered.groupby("year_month", as_index=False).agg(
        orders_count=("order_id", "nunique"),
        revenue=("total_amount", "sum"),
        avg_order_value=("total_amount", "mean"),
        unique_customers=("customer_id", "nunique"),
        unique_restaurants=("restaurant_id", "nunique"),
        total_discount=("discount", "sum"),
        total_delivery_fee=("delivery_fee", "sum"),
    ).sort_values("year_month")

    logger.info("Time series: %s daily, %s monthly rows", len(daily), len(monthly))
    return daily, monthly


# ── Main ────────────────────────────────────────────────────────
def main():
    logger.info("=" * 50)
    logger.info("START: Feature engineering")
    logger.info("=" * 50)

    try:
        orders = _load_clean("orders")
        customers = _load_clean("customers")
        restaurants = _load_clean("restaurants")
        drivers = _load_clean("drivers")
        order_items = _load_clean("order_items")
        delivery_logs = _load_clean("delivery_logs")
    except FileNotFoundError as e:
        logger.error("Prerequisite cleaned data missing. Run clean_data.py first. %s", e)
        raise

    cf = build_customer_features(orders, customers)
    _save_processed(cf, "customer_features")

    rf = build_restaurant_features(orders, order_items, restaurants)
    _save_processed(rf, "restaurant_features")

    df = build_driver_features(delivery_logs, drivers)
    _save_processed(df, "driver_features")

    daily, monthly = build_time_series(orders)
    _save_processed(daily, "daily_metrics")
    _save_processed(monthly, "monthly_metrics")

    logger.info("=" * 50)
    logger.info("Feature engineering complete.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
