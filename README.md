# 🚀 Finpilot-AI

> **Autonomous Enterprise Big Data & AI Business Intelligence Platform for Retail and E-Commerce**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2.3-black.svg?style=flat&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-7.4.0-231F20.svg?style=flat&logo=apachekafka)](https://kafka.apache.org)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.1-E25A1C.svg?style=flat&logo=apachespark)](https://spark.apache.org)
[![MinIO](https://img.shields.io/badge/MinIO-RELEASE-C72C48.svg?style=flat&logo=minio)](https://min.io)
[![Prophet](https://img.shields.io/badge/ML-Meta_Prophet-blue.svg)](https://facebook.github.io/prophet/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation_Forest-F7931E.svg?style=flat&logo=scikit-learn)](https://scikit-learn.org)

Finpilot-AI is a retail analytics and intelligence platform. It provides executive KPI metrics, interactive revenue trends, machine-learning revenue forecasting, automated sales anomaly detection, and business recommendations.

---

## 🧭 Architecture & Workflow Priority

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRIMARY USER WORKFLOW                          │
│                                                                        │
│   CSV Upload (Drag & Drop or API) ──► Validation & Schema Normalizer   │
│   (Canonical Finpilot OR Kaggle)       (BOM/UTF-8, Types, Returns)     │
│                     │                                                  │
│                     ▼                                                  │
│   Kimball Star Schema Data Warehouse (PostgreSQL or SQLite)            │
│   ├── fact_sales (idempotent, return-aware, gross/net reconciliation)  │
│   └── dim_date, dim_shop, dim_product, dim_customer                    │
│                     │                                                  │
│                     ▼                                                  │
│   Analytics & ML Engines ──────────► Next.js Executive Dashboard       │
│   (Prophet + Fallback, Isolation      (KPIs, Trends, Anomaly Audits,   │
│    Forest, Recommendations)            Forecasting, Real-time Refresh) │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                   OPTIONAL BIG DATA WORKFLOWS                          │
│                                                                        │
│   Kafka Streaming:  POS Generator ──► Producer ──► Consumer ──► MinIO  │
│   PySpark Lakehouse: Bronze JSON ──► Silver Parquet ──► Gold Analytics │
└────────────────────────────────────────────────────────────────────────┘
```

> **Important**:
> **CSV Upload is the primary, zero-dependency workflow**. You can run and demonstrate the entire platform locally using SQLite without needing Docker, Kafka, PySpark, MinIO, or cloud credentials.
> Apache Kafka and PySpark/MinIO are **optional big-data pipelines** that can be started and tested independently.

---

## 📋 Prerequisites

| Component | Minimum Version | Required For |
| :--- | :--- | :--- |
| **Python** | 3.10+ | Backend API, Data Generator, ML Models |
| **Node.js** | 18+ (with npm) | Next.js Frontend Dashboard |
| **Docker & Compose** *(Optional)* | Docker 24+, Compose v2+ | Full-stack containerized deployment |
| **Java / Spark** *(Optional)* | Java 11+, Spark 3.5+ | Distributed Lakehouse ETL |

---

## ⚡ Quickstart: Local Zero-Dependency Setup (Recommended for Demo)

Run the backend and frontend locally in seconds using SQLite:

### 1. Configure Local Environment
```bash
# Clone or navigate to the repository
cd Finpilot-AI

# Create your local environment file
cp .env.example .env
```
For local zero-dependency mode, SQLite is enabled by default (`sqlite:///./finpilot_local.db`).

### 2. Start the Backend API
```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Start FastAPI server on port 8000
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Start the Frontend Dashboard
```bash
# Open a new terminal
cd frontend
npm install
npm run dev
```
* Executive Dashboard: [http://localhost:3000](http://localhost:3000)

---

## 📥 Primary Workflow: CSV Upload & Validation

### Features:
1. **Interactive Modal**: Click **"Upload CSV"** in the top header. Supports Drag-and-Drop and File Browser.
2. **Dual-Schema Detection**:
   * **Canonical Finpilot**: `transaction_id, date, shop_id, product, category, quantity, unit_price, total, customer_id, payment_mode, cost_price`
   * **Kaggle Online Retail**: `InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country`
3. **Robust Quality Checks**:
   * UTF-8 and BOM-encoded CSV handling.
   * Row-level numeric constraints, future-date guards, and unreadable date detection.
   * Deduplication within the file and against existing warehouse records.
   * Returns and cancellations (`quantity < 0` or invoice starting with `'C'`) are preserved for accurate Net Revenue calculation (`Net Revenue = Gross Sales - Returns`).
4. **Instant Dashboard Refresh**: Ingestion triggers immediate re-querying of all KPI cards, trend charts, forecast models, and anomaly tables without manual page reload.

### Downloadable Templates & Samples:
* Download sample dataset: `GET /upload/sample`
* Download blank header template: `GET /upload/template`
* Or click **"Download Sample CSV"** inside the Upload Modal.

### Uploading via CLI:
```bash
# Canonical Finpilot Sample
curl -X POST -F "file=@data-generator/kaggle_online_retail_sample.csv" http://localhost:8000/upload
```

---

## 📊 Genuine Kaggle Online Retail Dataset Support

Finpilot-AI natively ingests the official public **Kaggle Online Retail Dataset**:
[https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset](https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset)

### Step-by-Step Instructions:

#### 1. Download Official Dataset
* **Via Kaggle CLI**:
  ```bash
  kaggle datasets download -d lakshmi25npathi/online-retail-dataset
  unzip online-retail-dataset.zip
  ```
* **Via Browser**:
  1. Visit [Kaggle Online Retail Dataset](https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset).
  2. Click **Download** (requires Kaggle account).
  3. Extract `Online Retail.xlsx`.

#### 2. Convert Excel to Production-Ready CSV
The original Kaggle distribution is an Excel file (`.xlsx`). Use the verified converter script:
```bash
python3 data-generator/convert_kaggle_retail.py \
  --input "Online Retail.xlsx" \
  --output "data-generator/output/kaggle_online_retail.csv"
```
To generate a lightweight 5,000-row sample for quick testing:
```bash
python3 data-generator/convert_kaggle_retail.py \
  --input "Online Retail.xlsx" \
  --output "data-generator/output/kaggle_sample.csv" \
  --sample 5000
```

#### 3. Upload and Ingest
* Drag & drop `kaggle_online_retail.csv` into the dashboard modal, or use curl:
```bash
curl -X POST -F "file=@data-generator/output/kaggle_online_retail.csv" http://localhost:8000/upload
```

#### Verified Kaggle Schema Mapping & Handling:
| Kaggle Field | Canonical Warehouse Field | Handling & Transformations |
| :--- | :--- | :--- |
| `InvoiceNo` | `transaction_id` | Composite key `{InvoiceNo}_{StockCode}_{index}` ensures multi-item invoices are not falsely deduplicated. |
| `InvoiceDate` | `date` / `timestamp` | Flexible date parsing into ANSI ISO timestamps and `dim_date` foreign keys. |
| `Description` | `product` | Blank descriptions are automatically mapped to `SKU_{StockCode}` or `General Merchandise`. |
| `Quantity` | `quantity` | Negative quantities (e.g. cancellations `C536379`) are preserved as returns in net revenue calculations. |
| `UnitPrice` | `unit_price` | Monetary values rounded to 2 decimal places. |
| `CustomerID` | `customer_id` | Treated as data identifier (not PII). Blank/missing values mapped to `CUST_ANONYMOUS`. |
| `Country` | `shop_id` | Mapped to geographic retail store codes (`SHOP_UNITED_KINGDOM`, `SHOP_FRANCE`, etc.). |

A curated reference sample with documented provenance is included at [`data-generator/kaggle_online_retail_sample.csv`](data-generator/kaggle_online_retail_sample.csv).

---

## 🤖 Running the Machine Learning Pipeline

The ML pipeline executes Prophet revenue forecasting and Isolation Forest anomaly detection against the warehouse:

```bash
# Run against local SQLite database
python3 ml/run_pipeline.py

# Run with custom parameters
python3 ml/run_pipeline.py --forecast-days 30 --contamination 0.015

# Run in standalone synthetic demo mode
python3 ml/run_pipeline.py --demo
```

### ML Engine Features:
* **Meta Prophet Forecaster**: Learns daily, weekly, and annual seasonality curves. If `prophet` is not installed, it falls back to a linear trend & day-of-week seasonality projection with confidence bands.
* **Isolation Forest Anomaly Detector**: Evaluates transaction amounts, quantities, unit prices, and store volumes to identify statistical outliers.
* **Idempotent Updates**: Safely updates `ml_forecasts` and `ml_anomalies` without duplicating rows.

---

## 🌊 Optional: Apache Kafka Streaming Pipeline

The Kafka streaming path is an optional high-velocity pipeline:

```
POS / CSV Source ──► Kafka Producer ──► 'retail.transactions.raw' ──► Consumer ──► MinIO Bronze
```

### Running Kafka Separately:

```bash
# 1. Start Zookeeper & Kafka via Docker
docker compose up -d zookeeper kafka

# 2. In Terminal A: Start the MinIO Consumer
cd ingestion
python3 consumer.py --bootstrap-servers localhost:29092 --batch-size 5000

# 3. In Terminal B: Start the Streaming Producer
cd ingestion
python3 producer.py --bootstrap-servers localhost:29092 --live-mock-count 10000
```

* Consumer group commits offsets only after successful batch writes.
* Clean error reporting if brokers are unavailable.
* Producer keys messages by `shop_id` for partition ordering.

---

## ⚡ Optional: PySpark Medallion Lakehouse & MinIO

The PySpark lakehouse pipeline processes Bronze raw data into Silver Parquet tables and Gold business aggregates:

```bash
# 1. Start MinIO Object Storage
docker compose up -d minio

# 2. Run PySpark Medallion ETL
cd etl
# Run with local filesystem (no MinIO required):
python3 spark_etl.py --local-mode \
  --bronze-path ../data-generator/output/retail_transactions.csv \
  --silver-path ./data/silver/ \
  --gold-path ./data/gold/
```

* S3A credentials and endpoint are read from environment variables.
* Deduplication and schema enforcement happen in the Silver layer.
* Gold layer compiles `fact_sales`, `daily_shop_metrics`, and `customer_summary`.

---

## 🧪 Automated Testing

Finpilot-AI includes a comprehensive test suite covering CSV validation, schema normalization, Kaggle datasets, returns, database idempotency, health endpoints, and date validation:

```bash
# Run the entire test suite
python3 -m pytest backend/tests -v
```

### Test Coverage Highlights:
* `test_upload_valid_csv_and_warehouse_ingestion`: Full ingestion into fact and dimension tables.
* `test_upload_idempotency_duplicate_handling`: Duplicate uploads do not inflate revenue totals.
* `test_upload_kaggle_online_retail_sample`: Verifies Kaggle schema, return handling, and Net vs Gross revenue reconciliation.
* `test_revenue_date_validation`: Validates date formats and start/end boundaries.
* `test_health_check_endpoint`: Verifies dialect and service health reporting.
* `test_clean_csv`, `test_duplicates`, `test_bad_dates`, `test_negative_and_zero_values`: Data quality constraints.

---

## 🐳 Full Containerized Deployment (Docker Compose)

To run the entire multi-service stack together:

```bash
# Setup environment
cp .env.example .env

# Build and start all services
docker compose up --build -d
```

### Service Directory:
| Service | Role | URL | Default Credentials |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js Dashboard | [http://localhost:3000](http://localhost:3000) | - |
| **Backend API** | FastAPI Gateway | [http://localhost:8000](http://localhost:8000) | - |
| **Swagger Docs** | Interactive API | [http://localhost:8000/docs](http://localhost:8000/docs) | - |
| **PostgreSQL** | Relational Warehouse | `localhost:5432` | `finpilot_user` / `finpilot_pass` |
| **MinIO Console**| S3 Storage Web UI | [http://localhost:9001](http://localhost:9001) | `admin` / `admin12345` |
| **Kafka Broker**| Message Broker | `localhost:29092` | - |

---

## ⚠️ Known Limitations & Operational Notes

1. **Docker PyPI Timeout**: When building the backend Docker image in high-latency network environments, pip packages may experience timeouts. The Dockerfile includes `--default-timeout=120 --retries 5` to mitigate this.
2. **Prophet Dependency**: Installing `prophet` locally requires C++ compilers (`pystan` / `cmdstanpy`). When omitted, Finpilot-AI automatically runs its built-in statistical fallback without error.
3. **Database Dialect Transparency**: Finpilot-AI explicitly connects to either PostgreSQL (production) or SQLite (local development) via `DATABASE_URL`. It does not silently fall back from a broken PostgreSQL instance to SQLite, preventing unexpected data isolation.
4. **Customer Data Privacy**: Customer identifiers (`customer_id` / `CustomerID`) are strictly handled as analytical surrogate data identifiers, never as personal identifiable information (PII).
