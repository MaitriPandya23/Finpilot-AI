"""
Finpilot-AI Lakehouse PySpark ETL Pipeline
Implements the Medallion Lakehouse Architecture:
- Bronze -> Silver: Ingests raw data from MinIO bronze bucket, deduplicates,
  casts schemas, validates totals, and writes Parquet to silver bucket.
- Silver -> Gold: Aggregates business metrics into Gold Parquet tables
  (Fact sales, daily shop metrics, category analytics, customer summaries).
"""

import argparse
import os
import sys
import time
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    TimestampType,
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "admin12345")


def init_spark_session(app_name: str = "Finpilot-Medallion-ETL", local_mode: bool = False) -> SparkSession:
    """Configures SparkSession with Hadoop S3A connector for MinIO."""
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.sql.shuffle.partitions", "8")
    )

    if not local_mode:
        # Hadoop AWS S3A configurations for MinIO
        clean_endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        builder = (
            builder
            .config("spark.hadoop.fs.s3a.endpoint", f"http://{clean_endpoint}")
            .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
            .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    print(f"Initialized SparkSession: Version {spark.version}")
    return spark


def get_raw_schema() -> StructType:
    """Defines the raw transaction schema."""
    return StructType([
        StructField("transaction_id", StringType(), False),
        StructField("date", StringType(), True),
        StructField("shop_id", StringType(), True),
        StructField("product", StringType(), True),
        StructField("category", StringType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("unit_price", DoubleType(), True),
        StructField("total", DoubleType(), True),
        StructField("customer_id", StringType(), True),
        StructField("payment_mode", StringType(), True),
    ])


def bronze_to_silver(spark: SparkSession, bronze_path: str, silver_path: str):
    """
    Cleanses, deduplicates, and validates raw Bronze data and stores
    it in partitioned Parquet files in Silver layer.
    """
    print(f"\n============================================================")
    print(f" [ETL Stage 1] Bronze -> Silver")
    print(f" Source: {bronze_path}")
    print(f" Target: {silver_path}")
    print(f"============================================================")

    # Ingest bronze raw data (supports both JSON and CSV)
    try:
        if bronze_path.endswith(".csv") or "csv" in bronze_path:
            df_bronze = spark.read.option("header", "true").schema(get_raw_schema()).csv(bronze_path)
        else:
            df_bronze = spark.read.json(bronze_path)
    except Exception as e:
        print(f"Error reading bronze path: {e}")
        # Fallback to csv if json empty
        df_bronze = spark.read.option("header", "true").schema(get_raw_schema()).csv(bronze_path)

    raw_count = df_bronze.count()
    print(f"Ingested {raw_count:,} raw records from Bronze.")

    # Data Cleansing & Deduplication
    df_cleaned = (
        df_bronze
        # Filter null or missing transaction IDs
        .filter(F.col("transaction_id").isNotNull())
        # Deduplicate on transaction_id
        .dropDuplicates(["transaction_id"])
        # Timestamp parsing
        .withColumn("timestamp", F.to_timestamp(F.col("date"), "yyyy-MM-dd HH:mm:ss"))
        .withColumn("date_only", F.to_date(F.col("timestamp")))
        # Type enforcement
        .withColumn("quantity", F.col("quantity").cast(IntegerType()))
        .withColumn("unit_price", F.round(F.col("unit_price").cast(DoubleType()), 2))
        .withColumn("total", F.round(F.col("total").cast(DoubleType()), 2))
        # Total integrity validation (recalculate if variance is noticeable)
        .withColumn(
            "validated_total",
            F.when(
                F.abs(F.col("quantity") * F.col("unit_price") - F.col("total")) < 0.05,
                F.col("total")
            ).otherwise(F.round(F.col("quantity") * F.col("unit_price"), 2))
        )
        .drop("total")
        .withColumnRenamed("validated_total", "total")
        # Impute missing string values with defaults
        .na.fill({
            "category": "Uncategorized",
            "shop_id": "SHOP_UNKNOWN",
            "customer_id": "CUST_GUEST",
            "payment_mode": "Cash"
        })
        # Date partition keys
        .withColumn("year", F.year(F.col("date_only")))
        .withColumn("month", F.month(F.col("date_only")))
    )

    clean_count = df_cleaned.count()
    print(f"Cleansed & Deduplicated: {clean_count:,} records (Removed {raw_count - clean_count:,} duplicates/invalid).")

    # Write to Silver Parquet partitioned by year & month
    (
        df_cleaned.write
        .mode("overwrite")
        .partitionBy("year", "month")
        .parquet(silver_path)
    )
    print(f"Successfully written Silver Parquet to: {silver_path}")
    return df_cleaned


def silver_to_gold(spark: SparkSession, silver_path: str, gold_base_path: str):
    """
    Computes business aggregates and dimensional models from Silver data,
    saving to Gold Parquet tables.
    """
    print(f"\n============================================================")
    print(f" [ETL Stage 2] Silver -> Gold")
    print(f" Source: {silver_path}")
    print(f" Target: {gold_base_path}")
    print(f"============================================================")

    df_silver = spark.read.parquet(silver_path)

    # 1. Gold Fact Sales
    gold_fact_path = f"{gold_base_path}/fact_sales"
    (
        df_silver
        .select(
            "transaction_id",
            "timestamp",
            "date_only",
            "shop_id",
            "product",
            "category",
            "quantity",
            "unit_price",
            "total",
            "customer_id",
            "payment_mode",
            "year",
            "month"
        )
        .write
        .mode("overwrite")
        .partitionBy("year", "month")
        .parquet(gold_fact_path)
    )
    print(f"Saved Gold Fact Sales -> {gold_fact_path}")

    # 2. Gold Daily Shop Metrics (BI Aggregation)
    gold_shop_path = f"{gold_base_path}/daily_shop_metrics"
    df_daily_shop = (
        df_silver.groupBy("date_only", "shop_id")
        .agg(
            F.round(F.sum("total"), 2).alias("total_revenue"),
            F.count("transaction_id").alias("transaction_count"),
            F.sum("quantity").alias("total_units_sold"),
            F.round(F.avg("total"), 2).alias("avg_order_value"),
            F.countDistinct("customer_id").alias("unique_customers"),
        )
        .orderBy(F.col("date_only").desc(), F.col("total_revenue").desc())
    )
    df_daily_shop.write.mode("overwrite").parquet(gold_shop_path)
    print(f"Saved Gold Daily Shop Metrics -> {gold_shop_path}")

    # 3. Gold Category & Product Analytics
    gold_product_path = f"{gold_base_path}/product_category_metrics"
    df_cat_metrics = (
        df_silver.groupBy("category", "product")
        .agg(
            F.round(F.sum("total"), 2).alias("total_revenue"),
            F.sum("quantity").alias("units_sold"),
            F.round(F.avg("unit_price"), 2).alias("avg_selling_price"),
            F.count("transaction_id").alias("order_count"),
        )
        .orderBy(F.col("total_revenue").desc())
    )
    df_cat_metrics.write.mode("overwrite").parquet(gold_product_path)
    print(f"Saved Gold Product Category Metrics -> {gold_product_path}")

    # 4. Gold Customer Analytics (Loyalty & RFM proxy)
    gold_cust_path = f"{gold_base_path}/customer_summary"
    df_cust_summary = (
        df_silver.groupBy("customer_id")
        .agg(
            F.round(F.sum("total"), 2).alias("lifetime_spend"),
            F.count("transaction_id").alias("total_orders"),
            F.round(F.avg("total"), 2).alias("avg_spend_per_order"),
            F.min("date_only").alias("first_purchase_date"),
            F.max("date_only").alias("last_purchase_date"),
        )
        .orderBy(F.col("lifetime_spend").desc())
    )
    df_cust_summary.write.mode("overwrite").parquet(gold_cust_path)
    print(f"Saved Gold Customer Analytics -> {gold_cust_path}")

    print("\nGold Layer successfully compiled!")


def main():
    parser = argparse.ArgumentParser(description="Finpilot-AI PySpark Medallion Lakehouse ETL")
    parser.add_argument("--bronze-path", type=str, default="s3a://bronze/raw_transactions/", help="Input bronze storage path")
    parser.add_argument("--silver-path", type=str, default="s3a://silver/transactions/", help="Target silver storage path")
    parser.add_argument("--gold-path", type=str, default="s3a://gold/", help="Target gold base directory")
    parser.add_argument("--local-mode", action="store_true", help="Run with local file system paths instead of MinIO S3A")

    args = parser.parse_args()

    t_start = time.time()
    spark = init_spark_session(local_mode=args.local_mode)

    try:
        bronze_to_silver(spark, args.bronze_path, args.silver_path)
        silver_to_gold(spark, args.silver_path, args.gold_path)
        print(f"\nETL Pipeline Execution Finished in {time.time() - t_start:.2f} seconds!")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
