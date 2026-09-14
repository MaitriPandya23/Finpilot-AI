"""
Finpilot-AI ML Pipeline Runner
Executes both Prophet revenue forecasting and Isolation Forest anomaly
detection, updating warehouse intelligence tables.
"""

import argparse
import os
import sys
import time
try:

    from sqlalchemy import create_engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None

from forecasting import run_forecasting
from anomaly_detector import run_anomaly_detection

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finpilot_user:finpilot_pass@localhost:5432/finpilot"
)


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI ML Engine Runner")
    parser.add_argument("--db-url", type=str, default=DEFAULT_DB_URL, help="PostgreSQL connection string")
    parser.add_argument("--forecast-days", type=int, default=30, help="Forecast horizon in days")
    parser.add_argument("--anomaly-sample", type=int, default=50_000, help="Sample size for anomaly detection")
    parser.add_argument("--contamination", type=float, default=0.015, help="Anomaly contamination rate")
    parser.add_argument("--demo", action="store_true", help="Run in standalone demo mode without connecting to database")

    args = parser.parse_args()
    print("Initializing Finpilot-AI Machine Learning Engine...")
    engine = create_engine(args.db_url) if (SQLALCHEMY_AVAILABLE and not args.demo) else None


    t_start = time.time()
    print("\n>>> Stage 1: Running Revenue Time-Series Forecast (Prophet)...")
    run_forecasting(engine, periods=args.forecast_days)

    print("\n>>> Stage 2: Running Isolation Forest Anomaly Detection...")
    run_anomaly_detection(engine, sample_size=args.anomaly_sample, contamination=args.contamination)

    print(f"\n============================================================")
    print(f" ML Pipeline completed successfully in {time.time() - t_start:.2f}s!")
    print(f"============================================================")


if __name__ == "__main__":
    main()
