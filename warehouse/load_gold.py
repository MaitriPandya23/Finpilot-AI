"""
Finpilot-AI Warehouse Gold Loader
Reads Gold Parquet / CSV datasets and loads them into PostgreSQL
following the Kimball Star Schema (dim_date, dim_shop, dim_product,
dim_customer, and fact_sales).
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finpilot_user:finpilot_pass@localhost:5432/finpilot"
)


def get_engine(db_url: str):
    """Initializes SQLAlchemy database engine with pool tuning."""
    engine = create_engine(db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    return engine


def populate_dim_date(engine, start_date: str = "2024-01-01", end_date: str = "2026-12-31"):
    """Pre-populates the Date Dimension table for high-performance time intelligence."""
    print("Checking & populating dim_date...")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

    dates = []
    curr = start_dt
    while curr <= end_dt:
        date_key = int(curr.strftime("%Y%m%d"))
        dates.append({
            "date_key": date_key,
            "date_actual": curr,
            "day_of_week": curr.isoweekday(),
            "day_name": curr.strftime("%A"),
            "day_of_month": curr.day,
            "month": curr.month,
            "month_name": curr.strftime("%B"),
            "quarter": (curr.month - 1) // 3 + 1,
            "year": curr.year,
            "is_weekend": curr.isoweekday() in [6, 7],
        })
        curr += timedelta(days=1)

    df_dates = pd.DataFrame(dates)
    with engine.begin() as conn:
        # Check existing count
        existing = conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()
        if existing == 0:
            df_dates.to_sql("dim_date", con=conn, if_exists="append", index=False)
            print(f"Inserted {len(df_dates):,} dates into dim_date.")
        else:
            print(f"dim_date already populated with {existing:,} dates.")


def load_dataset_to_warehouse(engine, source_path: str, chunk_size: int = 50_000, max_rows: int = None):
    """
    Ingests Gold Parquet (or CSV fallback), resolves surrogate keys,
    and bulk loads the star schema fact and dimensions.
    """
    print(f"\n============================================================")
    print(f" Finpilot-AI Star Schema Warehouse Loader")
    print(f" Source Data : {source_path}")
    print(f" Database    : {engine.url.render_as_string(hide_password=True)}")
    print(f"============================================================")

    t0 = time.time()
    populate_dim_date(engine)

    # 1. Load Data
    print(f"Reading source data from {source_path}...")
    if os.path.isdir(source_path) or source_path.endswith(".parquet"):
        df_source = pd.read_parquet(source_path)
    elif source_path.endswith(".csv"):
        df_source = pd.read_csv(source_path, nrows=max_rows)
    else:
        # Directory of parquet files
        df_source = pd.read_parquet(source_path)

    if max_rows and len(df_source) > max_rows:
        df_source = df_source.iloc[:max_rows]

    total_rows = len(df_source)
    print(f"Loaded {total_rows:,} records into memory for warehouse transformation.")

    # 2. Upsert Dimensions
    with engine.begin() as conn:
        print("Synchronizing dim_shop...")
        unique_shops = df_source[["shop_id"]].drop_duplicates()
        for _, row in unique_shops.iterrows():
            s_id = row["shop_id"]
            conn.execute(
                text("""
                    INSERT INTO dim_shop (shop_id, shop_name, location, city, tier)
                    VALUES (:s_id, :s_name, 'Metro Mall', 'New York', 'Tier 1')
                    ON CONFLICT (shop_id) DO NOTHING
                """),
                {"s_id": s_id, "s_name": f"Finpilot Store {s_id.replace('SHOP_', '')}"}
            )

        print("Synchronizing dim_product...")
        unique_products = df_source[["product", "category", "unit_price"]].groupby(["product", "category"]).agg({"unit_price": "mean"}).reset_index()
        for _, row in unique_products.iterrows():
            conn.execute(
                text("""
                    INSERT INTO dim_product (product_name, category, default_unit_price)
                    VALUES (:p_name, :cat, :price)
                    ON CONFLICT (product_name, category) DO UPDATE
                    SET default_unit_price = EXCLUDED.default_unit_price
                """),
                {"p_name": row["product"], "cat": row["category"], "price": float(row["unit_price"])}
            )

        print("Synchronizing dim_customer...")
        unique_custs = df_source[["customer_id"]].drop_duplicates()
        # Batch insert customers in chunks of 5,000
        cust_list = unique_custs["customer_id"].tolist()
        for i in range(0, len(cust_list), 5000):
            batch = [{"c_id": cid, "c_name": f"Customer {cid.replace('CUST_', '')}"} for cid in cust_list[i:i+5000]]
            conn.execute(
                text("""
                    INSERT INTO dim_customer (customer_id, customer_name, segment, loyalty_tier)
                    VALUES (:c_id, :c_name, 'Retail Buyer', 'Silver')
                    ON CONFLICT (customer_id) DO NOTHING
                """),
                batch
            )

        # 3. Retrieve Surrogate Key Lookup Mappings
        print("Fetching surrogate dimension keys...")
        shop_map = dict(conn.execute(text("SELECT shop_id, shop_key FROM dim_shop")).fetchall())
        product_map = {f"{row[0]}|||{row[1]}": row[2] for row in conn.execute(text("SELECT product_name, category, product_key FROM dim_product")).fetchall()}
        customer_map = dict(conn.execute(text("SELECT customer_id, customer_key FROM dim_customer")).fetchall())

    # 4. Transform Fact Records
    print("Mapping fact records to dimensional keys...")
    df_source["timestamp"] = pd.to_datetime(df_source["date"])
    df_source["date_key"] = df_source["timestamp"].dt.strftime("%Y%m%d").astype(int)
    df_source["shop_key"] = df_source["shop_id"].map(shop_map)
    df_source["prod_lookup"] = df_source["product"] + "|||" + df_source["category"]
    df_source["product_key"] = df_source["prod_lookup"].map(product_map)
    df_source["customer_key"] = df_source["customer_id"].map(customer_map)

    # Filter any unmapped records
    valid_facts = df_source.dropna(subset=["shop_key", "product_key", "customer_key", "date_key"])

    fact_records = pd.DataFrame({
        "transaction_id": valid_facts["transaction_id"],
        "date_key": valid_facts["date_key"].astype(int),
        "shop_key": valid_facts["shop_key"].astype(int),
        "product_key": valid_facts["product_key"].astype(int),
        "customer_key": valid_facts["customer_key"].astype(int),
        "transaction_timestamp": valid_facts["timestamp"],
        "quantity": valid_facts["quantity"].astype(int),
        "unit_price": valid_facts["unit_price"].astype(float),
        "total_amount": valid_facts["total"].astype(float),
        "payment_mode": valid_facts["payment_mode"],
    })

    # 5. Chunked Insertion into fact_sales
    print(f"Loading {len(fact_records):,} fact records into fact_sales (chunk size: {chunk_size:,})...")
    with engine.begin() as conn:
        for idx in range(0, len(fact_records), chunk_size):
            chunk = fact_records.iloc[idx : idx + chunk_size]
            chunk.to_sql("fact_sales", con=conn, if_exists="append", index=False, method="multi")
            print(f"Inserted chunk {idx // chunk_size + 1}: rows {idx:,} to {idx + len(chunk):,}")

    elapsed = time.time() - t0
    print(f"\nWarehouse load completed in {elapsed:.2f}s ({len(fact_records) / max(elapsed, 0.001):,.0f} rows/s)!")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Gold Parquet to PostgreSQL Star Schema Loader")
    parser.add_argument("--db-url", type=str, default=DEFAULT_DB_URL, help="PostgreSQL connection string")
    parser.add_argument("--source", type=str, default="", help="Path to Gold Parquet or CSV dataset")
    parser.add_argument("--chunk-size", type=int, default=25_000, help="Batch size for fact table inserts")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit total rows to load (useful for testing)")

    args = parser.parse_args()
    engine = get_engine(args.db_url)

    source_path = args.source
    if not source_path:
        # Try finding parquet or csv in standard project locations
        candidates = [
            "etl/data/gold/fact_sales",
            "data-generator/output/retail_transactions.csv",
            "../data-generator/output/retail_transactions.csv",
        ]
        for c in candidates:
            if os.path.exists(c):
                source_path = c
                break

    if not source_path or not os.path.exists(source_path):
        print(f"Source file/folder '{source_path}' not found. Please specify --source <path>")
        sys.exit(1)

    load_dataset_to_warehouse(engine, source_path, chunk_size=args.chunk_size, max_rows=args.max_rows)


if __name__ == "__main__":
    main()
