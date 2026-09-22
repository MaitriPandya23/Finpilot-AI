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
            .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
            .config("spark.hadoop.fs.s3a.fast.upload", "true")
        )

        jar_candidates = [
            "/opt/spark/jars/hadoop-aws-3.3.4.jar",
            "/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar",
        ]
        found_jars = [j for j in jar_candidates if os.path.exists(j)]
        if found_jars:
            builder = (
                builder
                .config("spark.jars", ",".join(found_jars))
                .config("spark.driver.extraClassPath", ":".join(found_jars))
                .config("spark.executor.extraClassPath", ":".join(found_jars))
            )
        else:
            builder = builder.config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")

    spark = builder.getOrCreate()
    if not local_mode:
        sanitize_hadoop_conf(spark)
    spark.sparkContext.setLogLevel("WARN")
    print(f"Initialized SparkSession: Version {spark.version}")
    return spark


def sanitize_hadoop_conf(spark: SparkSession):
    """Sanitizes Hadoop configuration duration strings into numeric values for S3A compatibility."""
    import re
    hconf = spark._jsc.hadoopConfiguration()
    unit_pattern = re.compile(r"^(\d+)(ms|s|m|h|d)$")
    it = hconf.iterator()
    updates = {}
    while it.hasNext():
        e = it.next()
        k, v = e.getKey(), e.getValue().strip()
        m = unit_pattern.match(v)
        if m:
            num, u = int(m.group(1)), m.group(2)
            mult = {"ms": 1, "s": 1000, "m": 60000, "h": 3600000, "d": 86400000}[u]
            if "keepalivetime" in k or "purge.age" in k:
                updates[k] = str(num if u == "s" else num * (mult // 1000))
            else:
                updates[k] = str(num if u == "ms" else num * mult)
    for k, v in updates.items():
        hconf.set(k, v)


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

    # Data Quality Checks
    null_txn_count = df_bronze.filter(F.col("transaction_id").isNull()).count()
    print(f"[DQ Check 1] Missing transaction IDs: {null_txn_count:,}")

    # Check rows failing total == quantity * unit_price check
    failing_math_df = df_bronze.filter(
        (F.col("quantity").isNotNull()) &
        (F.col("unit_price").isNotNull()) &
        (F.col("total").isNotNull()) &
        (F.abs(F.round(F.col("quantity").cast(DoubleType()) * F.col("unit_price").cast(DoubleType()), 2) - F.round(F.col("total").cast(DoubleType()), 2)) >= 0.05)
    )
    failing_math_count = failing_math_df.count()
    print(f"[DQ Check 2] Rows failing (quantity * unit_price == total) variance check: {failing_math_count:,}")

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
    print(f"Successfully written Silver Parquet ({clean_count:,} rows) to: {silver_path}")
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
    silver_count = df_silver.count()
    print(f"Read {silver_count:,} records from Silver.")

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
    print(f"Saved Gold Fact Sales ({silver_count:,} rows) -> {gold_fact_path}")

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
    daily_shop_count = df_daily_shop.count()
    print(f"Saved Gold Daily Shop Metrics ({daily_shop_count:,} rows) -> {gold_shop_path}")

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
    cat_metrics_count = df_cat_metrics.count()
    print(f"Saved Gold Product Category Metrics ({cat_metrics_count:,} rows) -> {gold_product_path}")

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
    cust_summary_count = df_cust_summary.count()
    print(f"Saved Gold Customer Analytics ({cust_summary_count:,} rows) -> {gold_cust_path}")

    print("\nGold Layer successfully compiled!")
    print(f"Summary of Gold Tables:")
    print(f"  - fact_sales: {silver_count:,} rows")
    print(f"  - daily_shop_metrics: {daily_shop_count:,} rows")
    print(f"  - product_category_metrics: {cat_metrics_count:,} rows")
    print(f"  - customer_summary: {cust_summary_count:,} rows")


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
