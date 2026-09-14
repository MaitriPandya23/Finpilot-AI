"""
Finpilot-AI Kafka Producer
Publishes retail transactions to Kafka topic 'retail.transactions.raw'.
Supports streaming from a generated CSV file or on-the-fly streaming generation.
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "retail.transactions.raw")
DEFAULT_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")


def create_kafka_producer(bootstrap_servers: str, max_retries: int = 10, retry_interval: int = 3):
    """Initializes KafkaProducer with connection retry mechanism."""
    servers = bootstrap_servers.split(",")
    print(f"Connecting to Kafka brokers at: {servers}")
    for attempt in range(1, max_retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks=1,
                compression_type="gzip",
                batch_size=32768,  # 32KB
                linger_ms=20,
            )
            print("Successfully connected to Kafka cluster!")
            return producer
        except NoBrokersAvailable:
            print(f"[{attempt}/{max_retries}] Kafka broker unavailable, retrying in {retry_interval}s...")
            time.sleep(retry_interval)
    raise ConnectionError(f"Could not connect to Kafka brokers at {bootstrap_servers} after {max_retries} attempts.")


def stream_from_csv(producer: KafkaProducer, topic: str, csv_path: str, max_messages: int = None, rate_limit: int = 0):
    """Streams records from a generated CSV file into Kafka."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    print(f"Publishing records from: {csv_path} to topic: '{topic}'")
    sent_count = 0
    t0 = time.time()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Type casting for JSON payload
            payload = {
                "transaction_id": row["transaction_id"],
                "date": row["date"],
                "shop_id": row["shop_id"],
                "product": row["product"],
                "category": row["category"],
                "quantity": int(row["quantity"]),
                "unit_price": float(row["unit_price"]),
                "total": float(row["total"]),
                "customer_id": row["customer_id"],
                "payment_mode": row["payment_mode"],
            }
            # Key by shop_id or customer_id for partition ordering
            producer.send(topic, key=payload["shop_id"], value=payload)
            sent_count += 1

            if sent_count % 10_000 == 0:
                elapsed = time.time() - t0
                speed = sent_count / max(elapsed, 0.001)
                print(f"Produced: {sent_count:,} events | Speed: {speed:,.0f} msg/s")

            if max_messages and sent_count >= max_messages:
                break

            if rate_limit > 0 and sent_count % rate_limit == 0:
                time.sleep(1.0)

    producer.flush()
    total_elapsed = time.time() - t0
    print(f"\nCompleted! Total produced: {sent_count:,} messages in {total_elapsed:.2f}s ({sent_count / max(total_elapsed, 0.001):,.0f} msg/s)")


def stream_mock_live(producer: KafkaProducer, topic: str, count: int = 5000, delay_ms: int = 10):
    """Generates and streams synthetic transactions on the fly."""
    print(f"Streaming {count:,} real-time synthetic transactions to '{topic}'...")
    categories = {
        "Electronics": ["Ergonomic Mouse", "4K Monitor", "Mechanical Keyboard", "Smart Watch"],
        "Apparel": ["Running Shoes", "Organic Cotton Tee", "Stretch Jeans", "Fleece Hoodie"],
        "Home & Kitchen": ["Air Fryer", "Drip Coffee Maker", "Chef Knife", "Ceramic Skillet"],
    }
    shops = [f"SHOP_{i:03d}" for i in range(1, 11)]
    payments = ["Credit Card", "Debit Card", "UPI", "Cash", "Digital Wallet"]

    t0 = time.time()
    for i in range(1, count + 1):
        cat = random.choice(list(categories.keys()))
        prod = random.choice(categories[cat])
        qty = random.randint(1, 5)
        price = round(random.uniform(15.0, 350.0), 2)
        total = round(qty * price, 2)
        shop = random.choice(shops)

        payload = {
            "transaction_id": f"TXN_STREAM_{i:08d}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "shop_id": shop,
            "product": prod,
            "category": cat,
            "quantity": qty,
            "unit_price": price,
            "total": total,
            "customer_id": f"CUST_{random.randint(1, 2000):06d}",
            "payment_mode": random.choice(payments),
        }

        producer.send(topic, key=shop, value=payload)
        if i % 1000 == 0:
            print(f"Streamed {i:,} live messages...")

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    producer.flush()
    print(f"Live stream of {count:,} messages completed in {time.time() - t0:.2f}s!")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Kafka Producer")
    parser.add_argument("--bootstrap-servers", type=str, default=DEFAULT_BOOTSTRAP_SERVERS, help="Kafka broker host:port")
    parser.add_argument("--topic", type=str, default=KAFKA_TOPIC, help="Kafka topic name")
    parser.add_argument("--input-file", type=str, default="", help="Path to retail_transactions.csv")
    parser.add_argument("--max-messages", type=int, default=None, help="Limit total messages sent")
    parser.add_argument("--live-mock-count", type=int, default=0, help="Stream N live mock transactions instead of CSV")
    parser.add_argument("--rate-limit", type=int, default=0, help="Max messages per second (0 for unthrottled)")

    args = parser.parse_args()
    producer = create_kafka_producer(args.bootstrap_servers)

    if args.live_mock_count > 0:
        stream_mock_live(producer, args.topic, count=args.live_mock_count)
    elif args.input_file and os.path.exists(args.input_file):
        stream_from_csv(producer, args.topic, args.input_file, args.max_messages, args.rate_limit)
    else:
        # Check default path from data-generator
        default_csv = os.path.join(os.path.dirname(__file__), "..", "data-generator", "output", "retail_transactions.csv")
        if os.path.exists(default_csv):
            stream_from_csv(producer, args.topic, default_csv, args.max_messages, args.rate_limit)
        else:
            print(f"No input CSV found at '{args.input_file}' or default generator path.")
            print("Falling back to live stream simulation (10,000 transactions)...")
            stream_mock_live(producer, args.topic, count=10000, delay_ms=0)


if __name__ == "__main__":
    main()
