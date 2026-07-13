"""
Load cleaned CSV files into MySQL.

Requires:
  - MySQL 8.0+ running at DB_CONFIG.host
  - Database & tables already created (run sql/01_schema.sql)
  - .env file for credentials (optional)
"""

import sys
import logging
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import CLEAN_DIR, DB_CONFIG, CLEAN_FILES, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("load_to_mysql")

FILES_TABLES = [
    ("customers", "customers"),
    ("restaurants", "restaurants"),
    ("drivers", "drivers"),
    ("orders", "orders"),
    ("order_items", "order_items"),
    ("delivery_logs", "delivery_logs"),
]


def _connection_str() -> str:
    return (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


def clear_tables(engine):
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for _, table in reversed(FILES_TABLES):
            conn.execute(text(f"TRUNCATE TABLE {table}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    logger.info("All tables truncated")


def load_data(engine):
    for key, table in FILES_TABLES:
        path = CLEAN_DIR / CLEAN_FILES[key]
        if not path.exists():
            logger.warning("File not found, skipping: %s", path)
            continue
        try:
            df = pd.read_csv(path)
            df.to_sql(table, con=engine, if_exists="append", index=False, method="multi", chunksize=5000)
            logger.info("Loaded %s -> %s (%s rows)", path.name, table, len(df))
        except Exception as exc:
            logger.error("Failed loading %s: %s", path.name, exc)
            raise


def main():
    logger.info("=" * 50)
    logger.info("START: MySQL load")
    logger.info("=" * 50)

    try:
        engine = create_engine(_connection_str())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to %s:%s/%s", DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["database"])
    except Exception as exc:
        logger.error("MySQL connection failed: %s", exc)
        print("ERROR: Could not connect to MySQL. Check DB_CONFIG in config.py and ensure the server is running.")
        print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}, DB: {DB_CONFIG['database']}")
        return

    clear_tables(engine)
    load_data(engine)

    logger.info("=" * 50)
    logger.info("MySQL load complete.")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
