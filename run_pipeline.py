#!/usr/bin/env python3
"""
Pipeline orchestrator — runs every stage in sequence.

Usage:
    python run_pipeline.py          # full pipeline
    python run_pipeline.py --skip-db  # skip MySQL load
"""

import sys
import argparse
import subprocess
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)
logger = logging.getLogger("pipeline")

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"

STAGES = [
    ("generate_data",       "Data generation"),
    ("clean_data",          "Data cleaning"),
    ("feature_engineering", "Feature engineering"),
    ("generate_visualizations", "EDA visualizations"),
]


def run_stage(module: str, label: str) -> bool:
    logger.info(">>> STAGE: %s (%s)", label, module)
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / f"{module}.py")],
            capture_output=True, text=True, check=True,
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                logger.info("  %s", line)
        logger.info(">>> %s — OK", label)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error(">>> %s — FAILED (exit code %s)", label, exc.returncode)
        if exc.stderr:
            for line in exc.stderr.strip().split("\n"):
                logger.error("  %s", line)
        return False


def main():
    parser = argparse.ArgumentParser(description="SwiftDash pipeline runner")
    parser.add_argument("--skip-db", action="store_true", help="Skip MySQL load step")
    args = parser.parse_args()

    print("=" * 55)
    print("  SwiftDash — Pipeline Runner")
    print("=" * 55)
    logger.info("Pipeline started (skip_db=%s)", args.skip_db)

    all_ok = True
    for module, label in STAGES:
        ok = run_stage(module, label)
        status = "PASS" if ok else "FAIL"
        symbol = "[PASS]" if ok else "[FAIL]"
        print(f"  {symbol} {label}")
        if not ok:
            all_ok = False
            break

    if all_ok and not args.skip_db:
        ok = run_stage("load_to_mysql", "MySQL load")
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] MySQL load")
        all_ok = all_ok and ok

    print("=" * 55)
    if all_ok:
        print("  [PASS] Pipeline completed successfully.")
        logger.info("Pipeline completed successfully.")
    else:
        print("  [FAIL] Pipeline failed -- check logs/pipeline.log for details.")
        logger.warning("Pipeline terminated with errors.")
    print("=" * 55)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
