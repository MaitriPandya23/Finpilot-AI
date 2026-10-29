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
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:

    from sqlalchemy import create_engine
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None

from forecasting import run_forecasting
from anomaly_detector import run_anomaly_detection

def get_default_db_url() -> str:
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    root_db = os.path.join(repo_root, "finpilot_local.db")
    if os.path.exists(root_db):
        return f"sqlite:///{root_db}"
    cur_db = os.path.abspath("finpilot_local.db")
    if os.path.exists(cur_db):
        return f"sqlite:///{cur_db}"
    return f"sqlite:///{root_db}"


DEFAULT_DB_URL = get_default_db_url()


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI ML Engine Runner")
    parser.add_argument("--db-url", type=str, default=DEFAULT_DB_URL, help="Database connection string (SQLite or PostgreSQL)")
    parser.add_argument("--forecast-days", type=int, default=30, help="Forecast horizon in days")
    parser.add_argument("--anomaly-sample", type=int, default=50_000, help="Sample size for anomaly detection")
    parser.add_argument("--contamination", type=float, default=0.015, help="Anomaly contamination rate")
    parser.add_argument("--demo", action="store_true", help="Run in standalone demo mode without connecting to database")

    args = parser.parse_args()
    print("Initializing Finpilot-AI Machine Learning Engine...")
    
    engine = None
    if SQLALCHEMY_AVAILABLE and not args.demo:
        try:
            candidate_engine = create_engine(args.db_url)
            with candidate_engine.connect() as conn:
                pass
            engine = candidate_engine
            print(f"Connected to database engine ({engine.dialect.name}).")
        except Exception as conn_err:
            print(f"Notice: Database connection at {args.db_url} unavailable ({conn_err}). Running in demo mode.")
            engine = None


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
