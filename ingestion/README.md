# Finpilot-AI / Ingestion

Real-time event streaming pipeline powered by Apache Kafka and MinIO S3 object storage.

## Components
1. **Producer (`producer.py`)**: Reads generated transaction batches or generates on-the-fly live transactions, serializes to JSON, and publishes to Kafka topic `retail.transactions.raw`.
2. **Consumer (`consumer.py`)**: Subscribes to `retail.transactions.raw`, micro-batches records (default: 10,000 records or 5s flush), and uploads newline-delimited JSON objects into MinIO Lakehouse `s3://bronze/raw_transactions/`.

## Usage

### 1. Run Kafka Producer
```bash
# Push records from generated CSV file to Kafka
python producer.py --bootstrap-servers localhost:29092 --input-file ../data-generator/output/retail_transactions.csv

# Or stream 10,000 live synthetic transactions for testing
python producer.py --bootstrap-servers localhost:29092 --live-mock-count 10000
```

### 2. Run Kafka to MinIO Consumer
```bash
# Ingest streaming events and save to MinIO bronze bucket
python consumer.py --bootstrap-servers localhost:29092 --batch-size 10000 --timeout 5.0
```

### Docker
```bash
docker build -t finpilot-ingestion .
# Run consumer
docker run --network finpilot-network finpilot-ingestion python consumer.py --bootstrap-servers kafka:9092
```
