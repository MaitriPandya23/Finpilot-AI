# Finpilot-AI

> **AI-Powered Big Data Business Intelligence Platform for Retail & Small Businesses**

Finpilot-AI is a comprehensive end-to-end Big Data BI monorepo covering the entire data engineering and AI lifecycle: synthetic transaction simulation at scale (2M–5M+ rows), real-time streaming via Apache Kafka, Lakehouse data transformation using PySpark and MinIO (Bronze/Silver/Gold), relational star-schema warehousing with PostgreSQL, predictive and prescriptive analytics (Meta Prophet + Scikit-Learn Isolation Forest), an asynchronous FastAPI backend gateway, and an executive Next.js + TypeScript dashboard.

---

## 🏛️ Monorepo Structure

```
finpilot-ai/
├── data-generator/      # High-speed synthetic transaction generator (Faker, numpy)
│   ├── generate.py      # Chunked streaming generator (2M-5M rows)
│   ├── requirements.txt # Dependencies
│   └── Dockerfile
├── ingestion/           # Real-time event streaming pipeline (Kafka + MinIO)
│   ├── producer.py      # Publishes transaction stream to Kafka
│   ├── consumer.py      # Micro-batches Kafka stream into MinIO bronze bucket
│   ├── requirements.txt # Dependencies
│   └── Dockerfile
├── etl/                 # PySpark Medallion Lakehouse engine
│   ├── spark_etl.py     # Bronze -> Silver (cleaning) -> Gold (aggregations)
│   ├── requirements.txt # PySpark, PyArrow, Boto3
│   └── Dockerfile
├── warehouse/           # Relational Star Schema Data Warehouse
│   ├── schema.sql       # PostgreSQL DDL (fact_sales, dim_*, ml_*)
│   ├── load_gold.py     # SQLAlchemy loader for Gold Parquet datasets
│   └── requirements.txt # SQLAlchemy, psycopg2-binary, pyarrow
├── ml/                  # Machine Learning Engine
│   ├── forecasting.py   # Meta Prophet daily revenue forecasting model
│   ├── anomaly_detector.py # Isolation Forest transaction anomaly detection
│   ├── run_pipeline.py  # Orchestrator running both models
│   ├── requirements.txt # prophet, scikit-learn, pandas
│   └── Dockerfile
├── backend/             # FastAPI REST API Gateway
│   ├── app/
│   │   ├── main.py      # API entrypoint, CORS, lifespan
│   │   ├── database.py  # SQLAlchemy engine & session pool
│   │   ├── models.py    # ORM models for Star Schema & ML tables
│   │   ├── schemas.py   # Pydantic validation contracts
│   │   └── routers/     # /revenue, /trends, /forecast, /anomalies, /recommendations
│   ├── requirements.txt # fastapi, uvicorn, sqlalchemy
│   └── Dockerfile
├── frontend/            # Executive Next.js 14+ TypeScript Dashboard
│   ├── src/
│   │   ├── app/         # App router (page.tsx, layout.tsx, globals.css)
│   │   ├── components/  # KPICards, TrendsChart, ForecastChart, AnomalyTable, etc.
│   │   └── lib/api.ts   # Resilient typed API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml   # Multi-service infrastructure orchestration
└── .env.example         # Shared configuration variables
```

---

## 🚀 Quickstart: Docker Compose Orchestration

Launch the full stack with a single command:

```bash
# 1. Clone & prepare environment
cp .env.example .env

# 2. Build and start all infrastructure and applications
docker compose up --build -d
```

### Services & Port Mappings
| Service | Technology | Port | Access URL |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 14 + TypeScript | `3000` | [http://localhost:3000](http://localhost:3000) |
| **Backend API** | FastAPI + Uvicorn | `8000` | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **PostgreSQL** | PostgreSQL 16 (Star Schema) | `5432` | `localhost:5432` |
| **MinIO API** | S3-compatible Object Storage | `9000` | `localhost:9000` |
| **MinIO Console**| Web Browser UI | `9001` | [http://localhost:9001](http://localhost:9001) (`admin` / `admin12345`) |
| **Kafka Broker**| Confluent Kafka | `29092` | `localhost:29092` |
| **Zookeeper** | Zookeeper Coordinator | `2181` | `localhost:2181` |

---

## 🔄 End-to-End Pipeline Execution Guide

### 1. Data Generation (2M–5M Transactions)
Generates high-throughput realistic transactions with customer repeat purchase behavior (Zipfian distribution):
```bash
cd data-generator
pip install -r requirements.txt
python generate.py --rows 2000000 --output output/retail_transactions.csv
```

### 2. Streaming Ingestion (Kafka to MinIO Bronze)
Start the consumer in one terminal, then stream data via the producer in another:
```bash
cd ingestion
pip install -r requirements.txt

# Terminal A: Start MinIO Bronze Consumer
python consumer.py --bootstrap-servers localhost:29092 --batch-size 10000

# Terminal B: Start Kafka Producer
python producer.py --bootstrap-servers localhost:29092 --input-file ../data-generator/output/retail_transactions.csv
```

### 3. Medallion Lakehouse PySpark ETL
Cleanses raw events and computes business aggregations:
```bash
cd etl
pip install -r requirements.txt

# Execute Bronze -> Silver -> Gold
python spark_etl.py --bronze-path s3a://bronze/raw_transactions/ --silver-path s3a://silver/transactions/ --gold-path s3a://gold/

# Or run in local file mode:
python spark_etl.py --local-mode --bronze-path ../data-generator/output/retail_transactions.csv --silver-path ./data/silver/transactions/ --gold-path ./data/gold/
```

### 4. Load Data into PostgreSQL Star Schema
Ingests Gold Parquet datasets into the relational warehouse:
```bash
cd warehouse
pip install -r requirements.txt
python load_gold.py --source ../etl/data/gold/fact_sales
```

### 5. Run Machine Learning Pipeline
Trains Meta Prophet for revenue forecasts and Isolation Forest for anomaly detection:
```bash
cd ml
pip install -r requirements.txt
python run_pipeline.py --forecast-days 30 --anomaly-sample 50000
```

### 6. Run Backend & Frontend Locally
```bash
# Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (Next.js)
cd frontend
npm install
npm run dev
```

---

## 📊 Business Intelligence & ML Capabilities

1. **Executive KPI Dashboard**: Immediate visibility into Gross Revenue, Total Orders, Average Basket Value (AOV), and Flagged Risk Alerts.
2. **Prophet Revenue Forecasting**: Automated time-series forecasting capturing weekly cycles, holiday shifts, and providing a 95% Bayesian confidence corridor.
3. **Isolation Forest Anomaly Detection**: Unsupervised detection identifying extreme ticket values, unusual bulk purchases, and suspicious payment modes.
4. **Prescriptive AI Engine**: Recommends high-impact operational decisions including inventory replenishment warnings and revenue optimization bundles.
