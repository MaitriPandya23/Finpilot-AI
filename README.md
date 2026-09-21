# 🚀 Finpilot-AI

> **Autonomous Enterprise Big Data & AI Business Intelligence Platform for Retail and E-Commerce**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.3-black.svg?style=flat&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-7.4.0-231F20.svg?style=flat&logo=apachekafka)](https://kafka.apache.org)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.1-E25A1C.svg?style=flat&logo=apachespark)](https://spark.apache.org)
[![MinIO](https://img.shields.io/badge/MinIO-RELEASE-C72C48.svg?style=flat&logo=minio)](https://min.io)
[![Prophet](https://img.shields.io/badge/ML-Meta_Prophet-blue.svg)](https://facebook.github.io/prophet/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation_Forest-F7931E.svg?style=flat&logo=scikit-learn)](https://scikit-learn.org)

Finpilot-AI is an end-to-end, production-grade Big Data Engineering and AI analytics platform. It ingests high-velocity retail transactions at scale (2M–5M+ rows), streams events through **Apache Kafka**, stores raw and refined datasets in a **MinIO S3 Lakehouse** via **PySpark (Bronze ➔ Silver ➔ Gold Medallion architecture)**, loads a Kimball star-schema **PostgreSQL** warehouse, applies **Meta Prophet** for revenue forecasting and **Scikit-Learn Isolation Forest** for fraud/outlier detection, and serves real-time insights through a **FastAPI** gateway to a modern **Next.js 14** executive dashboard.

---

## 🏗️ End-to-End System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph DataGen ["1. Synthetic Transaction Generator"]
        DG["Synthetic Event Generator<br/>(Faker, NumPy, Zipfian)"]
        CSV["retail_transactions.csv<br/>(2M - 5M+ Records)"]
        DG -->|Batch Generation| CSV
    end

    subgraph Streaming ["2. Real-Time Streaming Ingestion"]
        KP["Kafka Producer<br/>(ingestion/producer.py)"]
        KB["Kafka Broker<br/>(Topic: retail-transactions)"]
        KC["Kafka Consumer<br/>(ingestion/consumer.py)"]
        CSV -->|Stream Events| KP
        KP -->|JSON Messages| KB
        KB -->|Micro-Batches| KC
    end

    subgraph Lakehouse ["3. MinIO S3 Medallion Lakehouse"]
        Bronze[("Bronze Bucket<br/>s3a://bronze/raw_transactions/")]
        Silver[("Silver Bucket<br/>s3a://silver/transactions/")]
        Gold[("Gold Bucket<br/>s3a://gold/fact_sales/")]
        SP["PySpark Medallion Engine<br/>(etl/spark_etl.py)"]
        
        KC -->|Flush JSON Batches| Bronze
        Bronze -->|Ingest Raw Data| SP
        SP -->|Schema Validation & Deduplication| Silver
        SP -->|Business Dimensions & Aggregations| Gold
    end

    subgraph Warehouse ["4. Relational Star Schema (PostgreSQL)"]
        LG["Gold Loader<br/>(warehouse/load_gold.py)"]
        PG[("PostgreSQL 16 Warehouse<br/>• fact_sales<br/>• dim_product, dim_shop<br/>• dim_customer, dim_date")]
        Gold -->|Bulk Parquet Ingestion| LG
        LG -->|SQLAlchemy Insert| PG
    end

    subgraph ML ["5. Machine Learning Intelligence Engine"]
        MLP["ML Orchestrator<br/>(ml/run_pipeline.py)"]
        Prophet["Meta Prophet<br/>Time-Series Forecasting"]
        IsoForest["Scikit-Learn<br/>Isolation Forest Anomaly Detection"]
        
        PG -->|Historical Time-Series| MLP
        MLP -->|Fit Daily Revenue| Prophet
        MLP -->|Fit Multi-Feature Outliers| IsoForest
        Prophet -->|Write ml_forecasts (yhat, bounds)| PG
        IsoForest -->|Write ml_anomalies (score, severity)| PG
    end

    subgraph Gateway ["6. Backend REST API Gateway (FastAPI)"]
        API["FastAPI App<br/>(backend/app/main.py)"]
        R1["GET /revenue"]
        R2["GET /trends"]
        R3["GET /forecast"]
        R4["GET /anomalies"]
        R5["GET /recommendations"]
        
        PG <-->|SQLAlchemy ORM + Connection Pooling| API
        API --- R1 & R2 & R3 & R4 & R5
    end

    subgraph Presentation ["7. Executive Presentation Layer (Next.js 14)"]
        FE["Next.js Executive Dashboard<br/>(TypeScript + Tailwind + Recharts)"]
        KPI["KPI Executive Summary<br/>(Revenue, AOV, Volume, Anomalies)"]
        TR["Revenue Trends Chart<br/>(Daily / Weekly / Monthly)"]
        FC["Prophet Forecast Chart<br/>(95% Confidence Corridor)"]
        CAT["Category Mix & Shop Rankings"]
        ANOM["Flagged Outlier Audit Table"]
        REC["Prescriptive AI Recommendations"]
        
        R1 & R2 & R3 & R4 & R5 -->|Live Typed Fetch (api.ts)| FE
        FE --- KPI & TR & FC & CAT & ANOM & REC
    end

    style DataGen fill:#f8fafc,stroke:#64748b,stroke-width:2px;
    style Streaming fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
    style Lakehouse fill:#fefce8,stroke:#eab308,stroke-width:2px;
    style Warehouse fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    style ML fill:#faf5ff,stroke:#a855f7,stroke-width:2px;
    style Gateway fill:#f0fdfa,stroke:#14b8a6,stroke-width:2px;
    style Presentation fill:#fff1f2,stroke:#f43f5e,stroke-width:2px;
```

---

## ✨ Key Platform Features

### 1. High-Throughput Synthetic Data Generation
* **Scale**: Generates anywhere from 100,000 to **5,000,000+** realistic retail transactions in chunked memory-efficient streams.
* **Realistic Consumer Dynamics**: Employs Zipfian distributions for customer IDs to simulate repeat customer loyalty, varied order sizes, seasonal sales spikes, and weekend traffic surges.
* **Outlier Injection**: Automatically seeds intentional pricing glitches, bulk fraud attempts, and payment anomalies for ML validation.

### 2. Event-Driven Streaming Ingestion
* **Apache Kafka**: High-throughput message broker decoupled from the storage layer to handle transaction spikes seamlessly.
* **Streaming Producer**: Emits transaction events serialized as JSON to Kafka topic `retail-transactions`.
* **Micro-Batch Consumer**: Batches incoming messages in configurable chunks (default: 10,000 rows) and flushes them directly into MinIO S3 object storage.

### 3. Medallion Lakehouse Architecture (PySpark + MinIO)
* **Bronze Layer**: Raw, immutable transaction dumps landed directly from the Kafka consumer (`s3a://bronze/raw_transactions/`).
* **Silver Layer**: Cleaned, deduplicated, and typed data with validated timestamps, standardized currencies, and null-filtered fields (`s3a://silver/transactions/`).
* **Gold Layer**: Optimized business dimensions and fact tables aggregated by date, product category, customer segment, and retail store (`s3a://gold/fact_sales/`).
* **Dual Execution Modes**: Supports both distributed S3/MinIO mode and lightweight local-filesystem mode for fast developer onboarding.

### 4. Kimball Star Schema Data Warehouse
* **Engine**: PostgreSQL 16 relational warehouse with indexed foreign keys and partition-ready DDL.
* **Star Schema Entities**:
  * **Fact**: `fact_sales` (transaction amounts, quantities, unit prices, discounts, payment methods, timestamps).
  * **Dimensions**: `dim_date`, `dim_product`, `dim_shop`, `dim_customer`.
  * **ML Entities**: `ml_forecasts`, `ml_anomalies`.
* **Reliable Loader**: Automated loader (`warehouse/load_gold.py`) bulk-upserts Parquet data into PostgreSQL using transactional batches.

### 5. Dual Machine Learning Engines
* **Meta Prophet Revenue Forecaster** (`ml/forecasting.py`):
  * Learns daily, weekly, and annual seasonality curves.
  * Predicts revenue for configurable horizons (7 to 90 days).
  * Outputs expected point estimates (`yhat`) alongside 95% Bayesian confidence bands (`yhat_lower`, `yhat_upper`).
* **Scikit-Learn Isolation Forest Anomaly Detector** (`ml/anomaly_detector.py`):
  * Multi-dimensional feature vector: transaction amount, order quantity, unit price, and transaction hour.
  * Assigns continuous anomaly scores and maps them to actionable severity ratings (`Critical` vs. `Warning`).
  * Generates human-readable diagnostic explanations for auditors.
* **Prescriptive AI Engine** (`backend/app/routers/recommendations.py`):
  * Synthesizes live warehouse analytics and anomaly patterns into prioritized executive action cards (inventory restock alerts, fraud investigation triggers, pricing optimization).

### 6. High-Performance FastAPI Gateway
* **Real Database Prioritization**: Live queries against the PostgreSQL star schema take precedence over all endpoints.
* **Resilient Cold-Start Fallback**: If the database tables are empty on first boot, endpoints seamlessly return representative demo data with an explicit `is_demo: true` marker, preventing dashboard crashes.
* **Comprehensive Endpoint Suite**:
  * `GET /revenue`: Total revenue, order count, AOV, period-over-period growth, category breakdowns, and shop rankings.
  * `GET /trends`: Chronological time-series with dynamic grouping (`daily`, `weekly`, `monthly`).
  * `GET /forecast`: Future revenue curves with 95% confidence intervals.
  * `GET /anomalies`: Flagged outlier transactions filtered by severity and limit.
  * `GET /recommendations`: Dynamic prescriptive operational actions.
  * `GET /health`: Live database connectivity status check.
  * `GET /docs`: Interactive Swagger UI documentation.

### 7. Modern Executive BI Dashboard (Next.js 14)
* **Design & Aesthetics**: Dark slate modern executive palette (`slate-900`/`emerald-500`/`indigo-500`) built with Tailwind CSS.
* **Interactive Visualizations**: Recharts-powered area charts with shaded confidence corridors, multi-bar volume comparisons, and category progress meters.
* **Dynamic Status Badging**: Live header pill showing `Live PostgreSQL Warehouse` or `Cold-Start Demo Mode` based on actual backend data state.
* **Polish & Ergonomics**: Shimmering skeleton loaders during data fetch, responsive layouts, and informative empty-state guides.

---

## 📂 Repository File Layout

```
finpilot-ai/
├── data-generator/           # High-speed synthetic transaction generator
│   ├── generate.py           # Chunked streaming data generator (2M-5M rows)
│   ├── requirements.txt      # Faker, numpy, pandas
│   └── Dockerfile
├── ingestion/                # Event streaming pipeline
│   ├── producer.py           # Reads raw data & streams JSON to Kafka
│   ├── consumer.py           # Consumes Kafka stream & writes Bronze MinIO S3
│   ├── requirements.txt      # kafka-python, boto3
│   └── Dockerfile
├── etl/                      # PySpark Lakehouse ETL engine
│   ├── spark_etl.py          # Bronze ➔ Silver (cleansing) ➔ Gold (star schema)
│   ├── requirements.txt      # pyspark, pyarrow, boto3
│   └── Dockerfile
├── warehouse/                # Relational Data Warehouse
│   ├── schema.sql            # Star schema DDL & indexes for PostgreSQL
│   ├── load_gold.py          # Parquet to PostgreSQL bulk loader
│   └── requirements.txt      # sqlalchemy, psycopg2-binary, pyarrow
├── ml/                       # Machine Learning models
│   ├── forecasting.py        # Meta Prophet revenue forecasting model
│   ├── anomaly_detector.py   # Isolation Forest outlier detection
│   ├── run_pipeline.py       # End-to-end ML training & database writing script
│   ├── requirements.txt      # prophet, scikit-learn, pandas, sqlalchemy
│   └── Dockerfile
├── backend/                  # FastAPI REST API Gateway
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint, CORS & routers
│   │   ├── database.py       # SQLAlchemy engine & session pool
│   │   ├── models.py         # ORM models for star schema & ML tables
│   │   ├── schemas.py        # Pydantic response contracts (with is_demo flags)
│   │   └── routers/          # /revenue, /trends, /forecast, /anomalies, /recommendations
│   ├── requirements.txt      # fastapi, uvicorn, sqlalchemy, psycopg2-binary
│   └── Dockerfile
├── frontend/                 # Executive Next.js 14+ Dashboard
│   ├── src/
│   │   ├── app/              # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   │   ├── components/       # KPICards, TrendsChart, ForecastChart, AnomalyTable, etc.
│   │   └── lib/api.ts        # Typed resilient API client with timeout & fallback
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml        # Orchestrates Postgres, MinIO, Kafka, Zookeeper, Backend, Frontend
└── .env.example              # Environment configuration template
```

---

## ⚡ Quickstart: Docker Compose

You can launch all infrastructure and applications with Docker Compose:

```bash
# 1. Clone repository and navigate to project root
cd /path/to/Finpilot-AI

# 2. Setup environment configuration
cp .env.example .env

# 3. Build and run all services in background
docker compose up --build -d
```

### Services & Port Mappings
| Service | Role | Container Port | Host Port | Web Access URL |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Executive Next.js 14 Dashboard | `3000` | `3000` | [http://localhost:3000](http://localhost:3000) |
| **Backend API** | FastAPI REST Gateway | `8000` | `8000` | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **PostgreSQL** | Star Schema Data Warehouse | `5432` | `5432` | `localhost:5432` (`finpilot` / `finpilot_user`) |
| **MinIO Console**| S3 Storage Web UI | `9001` | `9001` | [http://localhost:9001](http://localhost:9001) (`admin` / `admin12345`) |
| **MinIO API** | S3 API Endpoint | `9000` | `9000` | `http://localhost:9000` |
| **Kafka Broker**| Distributed Event Streaming | `29092` | `29092` | `localhost:29092` |
| **Zookeeper** | Kafka Coordinator | `2181` | `2181` | `localhost:2181` |

---

## 🔄 End-to-End Execution Flow (Data Pipeline ➔ UI)

Follow these steps to populate the warehouse with live data and run ML models from scratch:

### Step 1: Generate Raw Synthetic Transactions
```bash
cd data-generator
pip install -r requirements.txt
python generate.py --rows 500000 --output output/retail_transactions.csv
```

### Step 2: Stream Data Through Kafka to MinIO Bronze
```bash
cd ../ingestion
pip install -r requirements.txt

# Terminal A: Start the MinIO Bronze Consumer
python consumer.py --bootstrap-servers localhost:29092 --batch-size 10000

# Terminal B: Start Streaming Transactions via Kafka Producer
python producer.py --bootstrap-servers localhost:29092 --input-file ../data-generator/output/retail_transactions.csv
```

### Step 3: Run Medallion Lakehouse PySpark ETL (Bronze ➔ Silver ➔ Gold)
```bash
cd ../etl
pip install -r requirements.txt

# Run PySpark transformation
python spark_etl.py --local-mode \
  --bronze-path ../data-generator/output/retail_transactions.csv \
  --silver-path ./data/silver/transactions/ \
  --gold-path ./data/gold/
```

### Step 4: Bulk-Load Gold Datasets into PostgreSQL Star Schema
```bash
cd ../warehouse
pip install -r requirements.txt
python load_gold.py --source ../etl/data/gold/fact_sales
```

### Step 5: Execute the Machine Learning Pipeline
Trains Meta Prophet for revenue forecasts and Isolation Forest for anomaly detection, saving model outputs directly into `ml_forecasts` and `ml_anomalies`:
```bash
cd ../ml
pip install -r requirements.txt
python run_pipeline.py --forecast-days 30 --anomaly-sample 50000
```

### Step 6: View Live Results on the Dashboard
Open [http://localhost:3000](http://localhost:3000) in your browser:
* The status banner in the top header switches from `Cold-Start Demo Mode` to `Live PostgreSQL Warehouse`.
* All KPI cards, trends, forecasts, category distributions, and anomaly tables update to reflect live data from your warehouse.

---

## 📡 API Reference

Interactive Swagger documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

| Method | Route | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/revenue` | Executive KPI aggregates, AOV, category revenue, top shops, and period growth. | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `GET` | `/trends` | Chronological revenue and transaction volume time-series. | `timeframe` (`daily`, `weekly`, `monthly`), `limit` (int) |
| `GET` | `/forecast` | Meta Prophet forecast curves with lower/upper confidence bounds. | `horizon_days` (default: 30) |
| `GET` | `/anomalies` | Transactions flagged by Isolation Forest with score and severity. | `severity` (`Critical`, `Warning`), `limit` (default: 20) |
| `GET` | `/recommendations` | Real-time AI operational action cards (inventory, fraud, pricing). | None |
| `GET` | `/health` | Live database connectivity and health diagnostics. | None |

All response schemas include an `is_demo` boolean indicator indicating whether data is derived from live database records or a cold-start simulation.

---

## 🛠️ Tech Stack Summary

* **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide React, Recharts
* **Backend Gateway**: FastAPI, Uvicorn, SQLAlchemy 2, Pydantic v2
* **Storage & Lakehouse**: PostgreSQL 16, MinIO (S3 compatible), Apache Parquet
* **Big Data & Streaming**: Apache Kafka, PySpark, PyArrow
* **Machine Learning**: Meta Prophet, Scikit-Learn, Pandas, NumPy
* **DevOps**: Docker, Docker Compose
