"""
Finpilot-AI Isolation Forest Anomaly Detection Service
Identifies atypical retail transactions, pricing divergences, and revenue
spikes using Scikit-Learn Isolation Forest, saving flagged anomalies
into PostgreSQL for real-time BI alerting.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from sqlalchemy import create_engine, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None
    text = None

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



def fetch_transactions_for_audit(engine, limit: int = 50_000) -> pd.DataFrame:
    """Extracts recent transaction records with shop and product metadata."""
    query = f"""
        SELECT
            f.transaction_id,
            f.transaction_timestamp,
            s.shop_id,
            p.product_name,
            p.category,
            f.quantity,
            f.unit_price,
            f.total_amount,
            f.payment_mode
        FROM fact_sales f
        JOIN dim_shop s ON f.shop_key = s.shop_key
        JOIN dim_product p ON f.product_key = p.product_key
        ORDER BY f.transaction_timestamp DESC
        LIMIT {limit};
    """
    try:
        with engine.connect() as conn:
            res = conn.execute(text(query))
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
            if not df.empty:
                df["date"] = pd.to_datetime(df["transaction_timestamp"]).dt.date
                df["total_amount"] = df["total_amount"].astype(float)
                df["unit_price"] = df["unit_price"].astype(float)
                df["quantity"] = df["quantity"].astype(int)
            return df
    except Exception as e:
        print(f"Database query warning: {e}")
        return pd.DataFrame()


def generate_synthetic_transactions(n: int = 5000) -> pd.DataFrame:
    """Generates synthetic transactions with deliberate anomalies for cold-start demo."""
    print("Generating synthetic transaction samples with embedded anomalies...")
    dates = [datetime.now().date() - timedelta(days=int(np.random.randint(0, 30))) for _ in range(n)]
    shops = [f"SHOP_{np.random.randint(1, 15):03d}" for _ in range(n)]
    quantities = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.6, 0.2, 0.1, 0.05, 0.05])
    prices = np.round(np.random.uniform(15.0, 150.0, size=n), 2)
    totals = np.round(quantities * prices, 2)

    df = pd.DataFrame({
        "transaction_id": [f"TXN_MOCK_{i:07d}" for i in range(1, n + 1)],
        "date": dates,
        "shop_id": shops,
        "product_name": "Retail Item",
        "category": "Electronics",
        "quantity": quantities,
        "unit_price": prices,
        "total_amount": totals,
        "payment_mode": "Credit Card",
    })

    # Inject deliberate synthetic anomalies (outliers)
    anomaly_indices = np.random.choice(n, size=int(n * 0.02), replace=False)
    for idx in anomaly_indices:
        anomaly_type = np.random.choice(["bulk", "extreme_price", "negative_total"])
        if anomaly_type == "bulk":
            df.at[idx, "quantity"] = 85
            df.at[idx, "total_amount"] = round(85 * df.at[idx, "unit_price"], 2)
        elif anomaly_type == "extreme_price":
            df.at[idx, "unit_price"] = 4999.99
            df.at[idx, "total_amount"] = round(df.at[idx, "quantity"] * 4999.99, 2)

    return df


def classify_reason(row, avg_total: float, avg_qty: float) -> tuple[str, str]:
    """Generates human-readable explanation and severity for the anomaly."""
    reasons = []
    severity = "Warning"

    if row["total_amount"] > avg_total * 6:
        reasons.append(f"Excessive transaction volume (${row['total_amount']:,.2f})")
        severity = "Critical"
    elif row["total_amount"] > avg_total * 3:
        reasons.append(f"Unusually high transaction total (${row['total_amount']:,.2f})")

    if row["quantity"] > avg_qty * 5:
        reasons.append(f"Abnormal bulk purchase quantity ({row['quantity']} units)")
        severity = "Critical"

    if row["unit_price"] > 1000.0:
        reasons.append(f"High-value SKU outlier (${row['unit_price']:,.2f}/unit)")

    if not reasons:
        reasons.append(f"Multivariate behavior outlier (Score: {row['anomaly_score']:.3f})")
        severity = "Moderate"

    return "; ".join(reasons), severity


def run_anomaly_detection(engine, sample_size: int = 50_000, contamination: float = 0.015):
    """Fits Isolation Forest and persists flagged anomalies to PostgreSQL."""
    print(f"\n============================================================")
    print(f" Finpilot-AI Anomaly Detection Pipeline")
    print(f" Algorithm       : Isolation Forest")
    print(f" Contamination   : {contamination * 100:.1f}%")
    print(f" Sample Window   : Up to {sample_size:,} records")
    print(f"============================================================")

    t0 = time.time()
    df = fetch_transactions_for_audit(engine, limit=sample_size)

    if len(df) < 50:
        print("Database contains fewer than 50 records. Running on synthetic demonstration set...")
        df = generate_synthetic_transactions(n=5000)

    # Feature Engineering for Isolation Forest
    features = pd.DataFrame({
        "quantity": df["quantity"].astype(float),
        "unit_price": df["unit_price"].astype(float),
        "total_amount": df["total_amount"].astype(float),
        "log_total": np.log1p(df["total_amount"].clip(lower=0)),
    })

    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=120,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    predictions = iso_forest.fit_predict(features)
    decision_scores = iso_forest.decision_function(features)

    df["is_anomaly"] = predictions == -1
    df["anomaly_score"] = np.round(decision_scores, 4)

    anomalies_df = df[df["is_anomaly"]].copy()
    avg_total = df["total_amount"].mean()
    avg_qty = df["quantity"].mean()

    # Assign reasons and severity
    reasons_severities = [classify_reason(row, avg_total, avg_qty) for _, row in anomalies_df.iterrows()]
    anomalies_df["reason"] = [r[0] for r in reasons_severities]
    anomalies_df["severity"] = [r[1] for r in reasons_severities]
    anomalies_df["detected_at"] = datetime.utcnow()

    # Prepare for database insert
    db_records = anomalies_df[[
        "transaction_id",
        "date",
        "shop_id",
        "total_amount",
        "anomaly_score",
        "is_anomaly",
        "severity",
        "reason",
        "detected_at",
    ]].copy()

    print(f"Detected {len(db_records):,} anomalies ({len(db_records)/len(df)*100:.2f}% of evaluated transactions).")

    # Persist to PostgreSQL / SQLite if available
    if engine and SQLALCHEMY_AVAILABLE:
        try:
            with engine.begin() as conn:
                records = []
                for _, r in db_records.iterrows():
                    dt_val = r["date"]
                    py_dt = dt_val.date() if hasattr(dt_val, "date") and callable(dt_val.date) else dt_val
                    det_val = r["detected_at"]
                    py_det = det_val.to_pydatetime() if hasattr(det_val, "to_pydatetime") else det_val
                    records.append({
                        "transaction_id": str(r["transaction_id"]),
                        "date": py_dt,
                        "shop_id": str(r["shop_id"]),
                        "total_amount": float(r["total_amount"]),
                        "anomaly_score": float(r["anomaly_score"]),
                        "is_anomaly": bool(r["is_anomaly"]),
                        "severity": str(r["severity"]),
                        "reason": str(r["reason"]),
                        "detected_at": py_det,
                    })
                conn.execute(text("""
                    INSERT INTO ml_anomalies (transaction_id, date, shop_id, total_amount, anomaly_score, is_anomaly, severity, reason, detected_at)
                    VALUES (:transaction_id, :date, :shop_id, :total_amount, :anomaly_score, :is_anomaly, :severity, :reason, :detected_at)
                """), records)
            print(f"Anomalies successfully stored in 'ml_anomalies' table! (Elapsed: {time.time() - t0:.2f}s)")
        except Exception as e:
            print(f"Database persistence skipped/failed: {e}")
    else:
        print("\n--- Top Flagged Outliers (Sample Preview) ---")
        for _, r in db_records.head(5).iterrows():
            print(f"[{r['severity']}] {r['transaction_id']} | ${r['total_amount']:,.2f} | Score: {r['anomaly_score']:.3f} | {r['reason']}")
        print(f"Demo run completed in {time.time() - t0:.2f}s!")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Anomaly Detector")
    parser.add_argument("--db-url", type=str, default=DEFAULT_DB_URL, help="Database connection string (SQLite or PostgreSQL)")
    parser.add_argument("--sample-size", type=int, default=50_000, help="Max records to audit")
    parser.add_argument("--contamination", type=float, default=0.015, help="Expected outlier proportion")
    parser.add_argument("--demo", action="store_true", help="Run in standalone demo mode without connecting to database")
    args = parser.parse_args()

    engine = None
    if SQLALCHEMY_AVAILABLE and not args.demo:
        try:
            candidate_engine = create_engine(args.db_url)
            with candidate_engine.connect() as conn:
                pass
            engine = candidate_engine
        except Exception as conn_err:
            print(f"Notice: Database connection at {args.db_url} unavailable ({conn_err}). Running in demo mode.")
            engine = None

    run_anomaly_detection(engine, sample_size=args.sample_size, contamination=args.contamination)



if __name__ == "__main__":
    main()
