"""
Finpilot-AI Synthetic Retail Transaction Generator
Generates realistic retail transaction datasets (2-5 million+ rows)
with streaming chunked I/O to maintain constant low memory footprint.
"""

import argparse
import csv
import os
import random
import sys
import time
from datetime import datetime, timedelta
import numpy as np
# Initialize Faker with optional fallback
try:
    from faker import Faker
    fake = Faker()
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False
    fake = None


# Define Master Product Catalog (Category -> list of (Product Name, base_min_price, base_max_price))
PRODUCT_CATALOG = {
    "Electronics": [
        ("Wireless Ergonomic Mouse", 24.99, 59.99),
        ("Mechanical Gaming Keyboard", 69.99, 149.99),
        ("USB-C Multiport Adapter Hub", 29.99, 79.99),
        ("27-Inch 4K UHD Monitor", 249.99, 449.99),
        ("Active Noise-Cancelling Headphones", 99.99, 299.99),
        ("Smart Fitness Tracker Band", 49.99, 129.99),
        ("Full HD Streaming Webcam", 39.99, 89.99),
        ("Portable External SSD 1TB", 79.99, 159.99),
    ],
    "Apparel": [
        ("Organic Cotton Crew T-Shirt", 14.99, 29.99),
        ("Slim-Fit Stretch Denim Jeans", 39.99, 79.99),
        ("Fleece Zip-Up Hoodie", 34.99, 64.99),
        ("Lightweight Running Sneakers", 49.99, 119.99),
        ("Full-Grain Leather Belt", 22.99, 45.99),
        ("Water-Resistant Windbreaker", 54.99, 109.99),
        ("Merino Wool Cushion Socks 3-Pack", 15.99, 28.99),
    ],
    "Home & Kitchen": [
        ("Programmable Drip Coffee Maker", 39.99, 89.99),
        ("High-Speed Countertop Blender", 49.99, 129.99),
        ("3-Piece Non-Stick Ceramic Skillet Set", 45.99, 99.99),
        ("Digital Air Fryer 5.8 Quart", 69.99, 139.99),
        ("Stainless Steel Electric Kettle", 24.99, 49.99),
        ("Handcrafted Stoneware Mug Set", 19.99, 36.99),
        ("German Steel Chef's Knife 8-Inch", 35.99, 85.99),
    ],
    "Beauty & Personal Care": [
        ("Hydrating Facial Cleanser", 12.99, 26.99),
        ("Hyaluronic Acid Daily Moisturizer", 16.99, 38.99),
        ("Broad Spectrum Mineral Sunscreen SPF50", 14.99, 29.99),
        ("Ionic Ceramic Hair Dryer", 39.99, 99.99),
        ("Sonic Rechargeable Toothbrush", 34.99, 89.99),
        ("Argan Oil Hair Treatment Mask", 15.99, 32.99),
    ],
    "Groceries & Gourmet": [
        ("Cold-Pressed Extra Virgin Olive Oil 1L", 14.99, 28.99),
        ("Single-Origin Arabica Whole Beans 1kg", 18.99, 34.99),
        ("Artisan 72% Dark Chocolate Bar 3-Pack", 9.99, 19.99),
        ("Organic Unsweetened Almond Milk 6-Pack", 11.99, 22.99),
        ("Wildflower Raw Blossom Honey 500g", 8.99, 17.99),
        ("Organic White Quinoa Grain 2kg", 7.99, 15.99),
    ],
    "Sports & Outdoors": [
        ("High-Density Anti-Tear Yoga Mat", 19.99, 42.99),
        ("Insulated Stainless Water Bottle 32oz", 16.99, 32.99),
        ("Heavy-Duty Resistance Bands Set", 14.99, 29.99),
        ("Ultralight 2-Person Backpacking Tent", 89.99, 199.99),
        ("Ergonomic 45L Hiking Backpack", 59.99, 129.99),
    ],
}

# Flatten products for index-based selection
ALL_PRODUCTS = []
for category, items in PRODUCT_CATALOG.items():
    for name, min_p, max_p in items:
        ALL_PRODUCTS.append({
            "product": name,
            "category": category,
            "min_price": min_p,
            "max_price": max_p,
        })

SHOPS = [
    {"shop_id": f"SHOP_{i:03d}", "weight": 1.0 + (i % 5) * 0.4}
    for i in range(1, 26)  # 25 retail shops
]
SHOP_IDS = [s["shop_id"] for s in SHOPS]
SHOP_WEIGHTS = np.array([s["weight"] for s in SHOPS])
SHOP_WEIGHTS /= SHOP_WEIGHTS.sum()

PAYMENT_MODES = ["Credit Card", "Debit Card", "UPI", "Cash", "Digital Wallet"]
PAYMENT_WEIGHTS = [0.42, 0.23, 0.18, 0.07, 0.10]


def generate_dataset(
    total_rows: int = 2_000_000,
    chunk_size: int = 100_000,
    output_path: str = "retail_transactions.csv",
    num_customers: int = 75_000,
    start_date: str = "2024-01-01",
    end_date: str = "2025-12-31",
    seed: int = 42,
):
    """
    Generates synthetic retail transaction records and streams them directly
    to a CSV file in chunks.
    """
    random.seed(seed)
    np.random.seed(seed)
    if FAKER_AVAILABLE:
        Faker.seed(seed)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days
    if total_days <= 0:
        raise ValueError("end_date must be strictly after start_date")

    # Pre-generate customer IDs with Zipfian distribution (repeat buyers)
    customer_ids = [f"CUST_{i:06d}" for i in range(1, num_customers + 1)]
    # Zipfian parameter: a=1.3 creates realistic retail repeat purchase skew
    zipf_indices = np.random.zipf(a=1.35, size=chunk_size) - 1
    zipf_indices = np.clip(zipf_indices, 0, num_customers - 1)

    # Ensure target directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"============================================================")
    print(f" Finpilot-AI Synthetic Retail Data Generator")
    print(f" Target rows      : {total_rows:,}")
    print(f" Chunk size       : {chunk_size:,}")
    print(f" Unique customers : {num_customers:,}")
    print(f" Date range       : {start_date} to {end_date}")
    print(f" Output target    : {output_path}")
    print(f"============================================================")

    csv_headers = [
        "transaction_id",
        "date",
        "shop_id",
        "product",
        "category",
        "quantity",
        "unit_price",
        "total",
        "customer_id",
        "payment_mode",
    ]

    t_start = time.time()
    rows_generated = 0
    chunk_count = 0

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        while rows_generated < total_rows:
            current_batch_size = min(chunk_size, total_rows - rows_generated)
            chunk_count += 1
            chunk_start_time = time.time()

            # Vectorized selections for performance
            prod_idx = np.random.randint(0, len(ALL_PRODUCTS), size=current_batch_size)
            chosen_shops = np.random.choice(SHOP_IDS, size=current_batch_size, p=SHOP_WEIGHTS)
            chosen_payments = np.random.choice(PAYMENT_MODES, size=current_batch_size, p=PAYMENT_WEIGHTS)
            quantities = np.random.choice([1, 2, 3, 4, 5, 6, 8, 10], size=current_batch_size, p=[0.55, 0.22, 0.11, 0.05, 0.03, 0.02, 0.01, 0.01])
            random_days = np.random.randint(0, total_days, size=current_batch_size)
            random_seconds = np.random.randint(0, 86400, size=current_batch_size)

            # Zipfian customer sample
            cust_idx = np.random.zipf(a=1.35, size=current_batch_size) - 1
            cust_idx = np.clip(cust_idx, 0, num_customers - 1)

            chunk_rows = []
            for i in range(current_batch_size):
                tx_id = f"TXN_{rows_generated + i + 1:09d}"
                dt = start_dt + timedelta(days=int(random_days[i]), seconds=int(random_seconds[i]))
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

                p_info = ALL_PRODUCTS[prod_idx[i]]
                product_name = p_info["product"]
                category = p_info["category"]

                # Price jitter around base min/max
                unit_price = round(random.uniform(p_info["min_price"], p_info["max_price"]), 2)
                qty = int(quantities[i])
                total = round(qty * unit_price, 2)
                cust_id = customer_ids[cust_idx[i]]
                payment = chosen_payments[i]
                shop = chosen_shops[i]

                chunk_rows.append([
                    tx_id,
                    dt_str,
                    shop,
                    product_name,
                    category,
                    qty,
                    unit_price,
                    total,
                    cust_id,
                    payment,
                ])

            writer.writerows(chunk_rows)
            rows_generated += current_batch_size
            chunk_duration = time.time() - chunk_start_time
            rate = current_batch_size / max(chunk_duration, 0.001)

            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Chunk {chunk_count:03d} | "
                f"Generated: {rows_generated:,} / {total_rows:,} "
                f"({(rows_generated / total_rows) * 100:.1f}%) | "
                f"Speed: {rate:,.0f} rows/s"
            )

    total_time = time.time() - t_start
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nGeneration Completed in {total_time:.2f}s!")
    print(f"Total Rows : {rows_generated:,}")
    print(f"File Size  : {file_size_mb:.2f} MB")
    print(f"Average Throughput: {rows_generated / max(total_time, 0.001):,.0f} rows/s")
    print(f"Saved to   : {os.path.abspath(output_path)}")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Synthetic Retail Data Generator")
    parser.add_argument("--rows", type=int, default=2_000_000, help="Number of rows to generate (default: 2,000,000)")
    parser.add_argument("--chunk-size", type=int, default=100_000, help="Batch chunk size for disk flush (default: 100,000)")
    parser.add_argument("--output", type=str, default="data-generator/output/retail_transactions.csv", help="Output file path")
    parser.add_argument("--customers", type=int, default=50_000, help="Number of unique customer profiles")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2025-12-31", help="End date (YYYY-MM-DD)")

    args = parser.parse_args()
    generate_dataset(
        total_rows=args.rows,
        chunk_size=args.chunk_size,
        output_path=args.output,
        num_customers=args.customers,
        start_date=args.start_date,
        end_date=args.end_date,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
