# Finpilot-AI / Medallion PySpark ETL

Scalable data cleansing, transformation, and dimensional metric aggregation implementing the Medallion Lakehouse architecture over MinIO object storage.

## Architecture

```
[MinIO Bronze: Raw JSON/CSV]
           │
           ▼ (Cleansing, Deduplication, Type Casting, Total Integrity Checks)
[MinIO Silver: Partitioned Parquet (year/month)]
           │
           ▼ (Star-schema Fact extraction & Business Metrics Aggregations)
[MinIO Gold: Parquet Datasets]
   ├── fact_sales/
   ├── daily_shop_metrics/
   ├── product_category_metrics/
   └── customer_summary/
```

## Usage

### Run with MinIO Object Storage
```bash
python spark_etl.py \
  --bronze-path s3a://bronze/raw_transactions/ \
  --silver-path s3a://silver/transactions/ \
  --gold-path s3a://gold/
```

### Run Locally (Direct File Paths)
```bash
python spark_etl.py \
  --local-mode \
  --bronze-path ../data-generator/output/retail_transactions.csv \
  --silver-path ./data/silver/transactions/ \
  --gold-path ./data/gold/
```

### Docker
```bash
docker build -t finpilot-etl .
docker run --network finpilot-network finpilot-etl
```
