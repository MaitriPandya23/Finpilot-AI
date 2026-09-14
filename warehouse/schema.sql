-- ==========================================================
-- Finpilot-AI Relational Star Schema DDL (PostgreSQL 16)
-- Dimensional Model optimized for Fast BI Analytics & ML
-- ==========================================================

-- 1. Date Dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT PRIMARY KEY,              -- Format: YYYYMMDD (e.g., 20240615)
    date_actual DATE UNIQUE NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    day_of_month INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_date_actual ON dim_date(date_actual);
CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);

-- 2. Shop Dimension
CREATE TABLE IF NOT EXISTS dim_shop (
    shop_key SERIAL PRIMARY KEY,
    shop_id VARCHAR(50) UNIQUE NOT NULL,
    shop_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    city VARCHAR(50),
    tier VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_dim_shop_id ON dim_shop(shop_id);

-- 3. Product Dimension
CREATE TABLE IF NOT EXISTS dim_product (
    product_key SERIAL PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    default_unit_price NUMERIC(10, 2),
    CONSTRAINT uq_product_category UNIQUE(product_name, category)
);

CREATE INDEX IF NOT EXISTS idx_dim_product_category ON dim_product(category);
CREATE INDEX IF NOT EXISTS idx_dim_product_name ON dim_product(product_name);

-- 4. Customer Dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(100),
    segment VARCHAR(50) DEFAULT 'Regular',
    loyalty_tier VARCHAR(20) DEFAULT 'Bronze'
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_id ON dim_customer(customer_id);

-- 5. Sales Fact Table
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    date_key INT NOT NULL REFERENCES dim_date(date_key),
    shop_key INT NOT NULL REFERENCES dim_shop(shop_key),
    product_key INT NOT NULL REFERENCES dim_product(product_key),
    customer_key INT NOT NULL REFERENCES dim_customer(customer_key),
    transaction_timestamp TIMESTAMP NOT NULL,
    quantity INT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    payment_mode VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date_key ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_shop_key ON fact_sales(shop_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_key ON fact_sales(product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_key ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_timestamp ON fact_sales(transaction_timestamp);

-- 6. ML Forecasts Storage Table
CREATE TABLE IF NOT EXISTS ml_forecasts (
    forecast_id SERIAL PRIMARY KEY,
    ds DATE NOT NULL,
    yhat NUMERIC(14, 2) NOT NULL,
    yhat_lower NUMERIC(14, 2) NOT NULL,
    yhat_upper NUMERIC(14, 2) NOT NULL,
    model_version VARCHAR(50) DEFAULT 'prophet_v1',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_forecasts_ds ON ml_forecasts(ds);

-- 7. ML Anomalies Storage Table
CREATE TABLE IF NOT EXISTS ml_anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64),
    date DATE NOT NULL,
    shop_id VARCHAR(50),
    total_amount NUMERIC(12, 2),
    anomaly_score NUMERIC(8, 4),
    is_anomaly BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) DEFAULT 'Warning',
    reason VARCHAR(255),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_anomalies_date ON ml_anomalies(date);
CREATE INDEX IF NOT EXISTS idx_ml_anomalies_score ON ml_anomalies(anomaly_score);
