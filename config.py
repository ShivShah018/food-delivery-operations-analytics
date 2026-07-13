"""
Project-wide configuration.

All paths, constants, and DB credentials are centralized here.
Change a value once; every script reflects the change.
"""

import os
from pathlib import Path

# ── Project Root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent

# ── Data Directories ──────────────────────────────────────────
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR    = PROJECT_ROOT / "data" / "cleaned"
PROC_DIR     = PROJECT_ROOT / "data" / "processed"
LOG_DIR      = PROJECT_ROOT / "logs"
SCREENSHOTS  = PROJECT_ROOT / "screenshots"
REPORTS_DIR  = PROJECT_ROOT / "reports"
SQL_DIR      = PROJECT_ROOT / "sql"

for d in [RAW_DIR, CLEAN_DIR, PROC_DIR, LOG_DIR, SCREENSHOTS]:
    d.mkdir(parents=True, exist_ok=True)

# ── File Names ─────────────────────────────────────────────────
RAW_FILES = {
    "customers": "customers.csv",
    "restaurants": "restaurants.csv",
    "drivers": "drivers.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "delivery_logs": "delivery_logs.csv",
}

CLEAN_FILES = {
    k: v.replace(".csv", "_clean.csv") for k, v in RAW_FILES.items()
}

PROC_FILES = {
    "customer_features": "customer_features.csv",
    "restaurant_features": "restaurant_features.csv",
    "driver_features": "driver_features.csv",
    "daily_metrics": "daily_metrics.csv",
    "monthly_metrics": "monthly_metrics.csv",
}

# ── Data Generation Constants ──────────────────────────────────
GEN_CONFIG = {
    "n_customers": 12_000,
    "n_restaurants": 250,
    "n_drivers": 800,
    "total_orders": 65_000,
    "start_date": "2022-01-01",
    "end_date": "2025-06-30",
    "seed": 42,
}

# ── RFM Segmentation Thresholds ───────────────────────────────
# Business-defined cutoffs.  These should be reviewed quarterly
# as the customer base grows and spending patterns shift.
RFM_THRESHOLDS = {
    "platinum": {"min_orders": 25, "min_spend": 15000},
    "gold":     {"min_orders": 10, "min_spend": 5000},
    "at_risk_days": 90,        # no order in 90 days
    "churned_days": 180,       # no order in 180 days
}

# ── Delivery Performance Threshold ─────────────────────────────
ON_TIME_CUTOFF_MINUTES = 40

# ── MySQL Connection ───────────────────────────────────────────
# Override via environment variables in production / CI.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "swiftdash_analytics"),
}

# ── Logging ────────────────────────────────────────────────────
LOG_FILE = LOG_DIR / "pipeline.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
