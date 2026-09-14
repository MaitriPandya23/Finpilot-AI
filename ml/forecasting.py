"""
Finpilot-AI Prophet Revenue Forecasting Service
Trains Meta Prophet time-series models on historical daily revenue
extracted from PostgreSQL and persists 30-60 day forecast predictions
with confidence intervals back to the warehouse.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
try:

    from sqlalchemy import create_engine, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None
    text = None

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finpilot_user:finpilot_pass@localhost:5432/finpilot"
)


# Robust Prophet import with statistical fallback
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Notice: 'prophet' library not found. Will use statistical trend & seasonality fallback.")


def fetch_historical_revenue(engine) -> pd.DataFrame:
    """Queries daily aggregated revenue from fact_sales + dim_date."""
    query = """
        SELECT
            d.date_actual AS ds,
            COALESCE(SUM(f.total_amount), 0.0) AS y,
            COUNT(f.sales_key) AS order_count
        FROM dim_date d
        LEFT JOIN fact_sales f ON d.date_key = f.date_key
        WHERE d.date_actual <= CURRENT_DATE
        GROUP BY d.date_actual
        HAVING SUM(f.total_amount) > 0
        ORDER BY d.date_actual ASC;
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            df["ds"] = pd.to_datetime(df["ds"])
            df["y"] = df["y"].astype(float)
            return df
    except Exception as e:
        print(f"Database query warning: {e}")
        return pd.DataFrame()


def generate_synthetic_history(days: int = 180) -> pd.DataFrame:
    """Generates synthetic daily revenue for cold-start bootstrapping."""
    print("Generating synthetic historical baseline for initial model training...")
    end_dt = datetime.now().date()
    start_dt = end_dt - timedelta(days=days)
    dates = pd.date_range(start=start_dt, end=end_dt, freq="D")

    base_rev = 15000.0
    trend = np.linspace(0, 5000, len(dates))
    # Weekly seasonality (higher weekends)
    day_of_week = dates.dayofweek
    seasonality = np.where(day_of_week >= 5, 4500, 0)
    noise = np.random.normal(0, 1200, len(dates))

    y = base_rev + trend + seasonality + noise
    y = np.maximum(y, 1000.0)

    return pd.DataFrame({"ds": dates, "y": np.round(y, 2)})


def run_forecasting(engine, periods: int = 30, use_synthetic_fallback: bool = True):
    """Executes Prophet training and inserts future predictions into ml_forecasts."""
    print(f"\n============================================================")
    print(f" Finpilot-AI Revenue Forecasting Pipeline")
    print(f" Forecast Horizon : {periods} days")
    print(f" Model Engine     : {'Meta Prophet' if PROPHET_AVAILABLE else 'Statistical Trend Baseline'}")
    print(f"============================================================")

    t0 = time.time()
    df_hist = fetch_historical_revenue(engine)

    if len(df_hist) < 14:
        print(f"Insufficient historical data in PostgreSQL ({len(df_hist)} days).")
        if use_synthetic_fallback:
            df_hist = generate_synthetic_history(days=180)
        else:
            print("Aborting forecast. Please ingest more transaction data.")
            return

    print(f"Training on {len(df_hist)} historical days (Range: {df_hist['ds'].min().date()} to {df_hist['ds'].max().date()})...")

    if PROPHET_AVAILABLE:
        # Train Meta Prophet
        model = Prophet(
            yearly_seasonality=True if len(df_hist) > 365 else False,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95,  # 95% confidence intervals
        )
        model.fit(df_hist[["ds", "y"]])

        future = model.make_future_dataframe(periods=periods, freq="D")
        forecast = model.predict(future)

        # Filter to only the predicted future horizon
        forecast_future = forecast.iloc[-periods:][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
    else:
        # Robust polynomial + weekly seasonality projection
        last_date = df_hist["ds"].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, periods + 1)]

        x = np.arange(len(df_hist))
        poly = np.polyfit(x, df_hist["y"], deg=1)
        future_x = np.arange(len(df_hist), len(df_hist) + periods)
        trend_proj = np.polyval(poly, future_x)

        # Weekly pattern adjustment
        dow_mean = df_hist.groupby(df_hist["ds"].dt.dayofweek)["y"].mean()
        overall_mean = df_hist["y"].mean()
        dow_effect = {d: (dow_mean.get(d, overall_mean) - overall_mean) for d in range(7)}

        yhat = []
        yhat_lower = []
        yhat_upper = []
        std_err = df_hist["y"].std()

        for d, t_val in zip(future_dates, trend_proj):
            val = t_val + dow_effect.get(d.dayofweek, 0)
            yhat.append(round(max(val, 500.0), 2))
            yhat_lower.append(round(max(val - 1.96 * std_err, 200.0), 2))
            yhat_upper.append(round(val + 1.96 * std_err, 2))

        forecast_future = pd.DataFrame({
            "ds": future_dates,
            "yhat": yhat,
            "yhat_lower": yhat_lower,
            "yhat_upper": yhat_upper,
        })

    forecast_future["yhat"] = forecast_future["yhat"].round(2)
    forecast_future["yhat_lower"] = forecast_future["yhat_lower"].round(2)
    forecast_future["yhat_upper"] = forecast_future["yhat_upper"].round(2)
    forecast_future["model_version"] = "prophet_v1"
    forecast_future["generated_at"] = datetime.utcnow()

    # Save to PostgreSQL if available
    if engine and SQLALCHEMY_AVAILABLE:
        print(f"Writing {len(forecast_future)} forecast records to 'ml_forecasts' table...")
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM ml_forecasts WHERE ds >= CURRENT_DATE"))
                forecast_future.to_sql("ml_forecasts", con=conn, if_exists="append", index=False)
            print(f"Forecast successfully persisted! (Horizon: {periods} days, Elapsed: {time.time() - t0:.2f}s)")
        except Exception as e:
            print(f"Database persistence skipped/failed: {e}")
    else:
        print("\n--- Prophet Forecast Projections (First 5 Days) ---")
        for _, r in forecast_future.head(5).iterrows():
            print(f"[{r['ds'].strftime('%Y-%m-%d')}] Expected: ${r['yhat']:,.2f} | 95% Corridor: [${r['yhat_lower']:,.2f} - ${r['yhat_upper']:,.2f}]")
        print(f"Demo forecast generated in {time.time() - t0:.2f}s!")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Revenue Forecasting")
    parser.add_argument("--db-url", type=str, default=DEFAULT_DB_URL, help="PostgreSQL connection string")
    parser.add_argument("--periods", type=int, default=30, help="Days to forecast ahead (default: 30)")
    parser.add_argument("--demo", action="store_true", help="Run in standalone demo mode without connecting to database")
    args = parser.parse_args()

    engine = create_engine(args.db_url) if (SQLALCHEMY_AVAILABLE and not args.demo) else None
    run_forecasting(engine, periods=args.periods)


if __name__ == "__main__":
    main()

