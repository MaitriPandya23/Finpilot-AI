"""
Finpilot-AI Kafka Consumer
Consumes transactions from Kafka 'retail.transactions.raw' topic,
micro-batches records, and streams raw JSON datasets directly
into MinIO bronze lakehouse storage.
"""

import argparse
import io
import json
import os
import sys
import time
import uuid
from datetime import datetime
import boto3
from botocore.client import Config
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "retail.transactions.raw")
DEFAULT_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")
BRONZE_BUCKET = os.getenv("MINIO_BRONZE_BUCKET", "bronze")


def get_s3_client(endpoint_url: str, access_key: str, secret_key: str):
    """Initializes S3 client configured for MinIO."""
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
    # Ensure bronze bucket exists
    try:
        s3.head_bucket(Bucket=BRONZE_BUCKET)
    except Exception:
        try:
            s3.create_bucket(Bucket=BRONZE_BUCKET)
            print(f"Created MinIO bucket '{BRONZE_BUCKET}'")
        except Exception as e:
            print(f"Note on bucket creation: {e}")
    return s3


def create_kafka_consumer(bootstrap_servers: str, topic: str, group_id: str = "finpilot-bronze-consumer", max_retries: int = 10):
    """Initializes KafkaConsumer with connection retry logic."""
    servers = bootstrap_servers.split(",")
    print(f"Connecting Kafka consumer to brokers: {servers} on topic: {topic}")
    for attempt in range(1, max_retries + 1):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=servers,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                consumer_timeout_ms=10000,  # 10s timeout if idle
            )
            print("Kafka Consumer connected successfully!")
            return consumer
        except NoBrokersAvailable:
            print(f"[{attempt}/{max_retries}] Kafka broker unavailable, retrying in 3s...")
            time.sleep(3)
    raise ConnectionError(f"Failed to connect Kafka consumer to {bootstrap_servers}")


def flush_batch_to_minio(s3_client, bucket: str, batch: list, batch_num: int):
    """Writes a micro-batch of JSON records to MinIO Bronze bucket."""
    if not batch:
        return None

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    object_key = f"raw_transactions/{timestamp_str}_batch_{batch_num}_{uuid.uuid4().hex[:6]}.json"

    # Newline-delimited JSON
    data_stream = io.BytesIO()
    for record in batch:
        data_stream.write((json.dumps(record) + "\n").encode("utf-8"))
    data_stream.seek(0)

    s3_client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=data_stream.getvalue(),
        ContentType="application/x-ndjson",
    )
    size_kb = len(data_stream.getvalue()) / 1024
    print(f"Uploaded batch {batch_num} ({len(batch):,} records, {size_kb:.1f} KB) -> s3://{bucket}/{object_key}")
    return object_key


def run_consumer(
    bootstrap_servers: str,
    topic: str,
    batch_size: int = 10000,
    batch_timeout_sec: float = 5.0,
    max_batches: int = None,
):
    """Main consumer loop buffering records and periodically flushing to MinIO."""
    s3 = get_s3_client(MINIO_ENDPOINT, MINIO_USER, MINIO_PASSWORD)
    consumer = create_kafka_consumer(bootstrap_servers, topic)

    print(f"\n============================================================")
    print(f" Finpilot-AI Bronze Ingestion Consumer")
    print(f" Kafka Topic   : {topic}")
    print(f" MinIO Target  : s3://{BRONZE_BUCKET}/raw_transactions/")
    print(f" Batch Size    : {batch_size:,} records")
    print(f" Max Timeout   : {batch_timeout_sec}s")
    print(f"============================================================\n")

    current_batch = []
    batch_count = 0
    total_consumed = 0
    last_flush_time = time.time()

    try:
        while True:
            poll_records = consumer.poll(timeout_ms=1000)
            now = time.time()

            for topic_partition, records in poll_records.items():
                for record in records:
                    current_batch.append(record.value)
                    total_consumed += 1

                    if len(current_batch) >= batch_size:
                        batch_count += 1
                        flush_batch_to_minio(s3, BRONZE_BUCKET, current_batch, batch_count)
                        consumer.commit()
                        current_batch = []
                        last_flush_time = now

                        if max_batches and batch_count >= max_batches:
                            print(f"Reached maximum batch limit ({max_batches}). Stopping.")
                            return

            # Time-based flush if buffer has items
            if current_batch and (now - last_flush_time >= batch_timeout_sec):
                batch_count += 1
                flush_batch_to_minio(s3, BRONZE_BUCKET, current_batch, batch_count)
                consumer.commit()
                current_batch = []
                last_flush_time = now

                if max_batches and batch_count >= max_batches:
                    print(f"Reached maximum batch limit ({max_batches}). Stopping.")
                    return

    except KeyboardInterrupt:
        print("\nInterrupted by user. Flushing remaining buffer...")
        if current_batch:
            batch_count += 1
            flush_batch_to_minio(s3, BRONZE_BUCKET, current_batch, batch_count)
            consumer.commit()
    finally:
        consumer.close()
        print(f"\nConsumer finished! Total records persisted: {total_consumed:,} across {batch_count} batches.")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI Kafka to MinIO Consumer")
    parser.add_argument("--bootstrap-servers", type=str, default=DEFAULT_BOOTSTRAP_SERVERS, help="Kafka broker host:port")
    parser.add_argument("--topic", type=str, default=KAFKA_TOPIC, help="Kafka topic name")
    parser.add_argument("--batch-size", type=int, default=10000, help="Micro-batch size for MinIO upload")
    parser.add_argument("--timeout", type=float, default=5.0, help="Batch flush timeout in seconds")
    parser.add_argument("--max-batches", type=int, default=None, help="Stop after N batches (useful for jobs)")

    args = parser.parse_args()
    run_consumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        batch_size=args.batch_size,
        batch_timeout_sec=args.timeout,
        max_batches=args.max_batches,
    )


if __name__ == "__main__":
    main()
