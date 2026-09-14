# Finpilot-AI / Data Warehouse

PostgreSQL Relational Data Warehouse implementing a Kimball Star Schema with dimension tables, a high-volume sales fact table, and machine learning tables for revenue forecasts and anomaly scores.

## Star Schema Architecture

```
                 ┌───────────────────┐
                 │     dim_date      │
                 ├───────────────────┤
                 │ PK  date_key      │
                 │     date_actual   │
                 │     year, month   │
                 └─────────┬─────────┘
                           │
 ┌─────────────────┐       │       ┌──────────────────┐
 │    dim_shop     │       │       │   dim_product    │
 ├─────────────────┤       │       ├──────────────────┤
 │ PK  shop_key    │◄──────┼──────►│ PK  product_key  │
 │     shop_id     │       │       │     product_name │
 │     location    │       │       │     category     │
 └─────────────────┘       │       └──────────────────┘
                           ▼
                 ┌───────────────────┐
                 │    fact_sales     │
                 ├───────────────────┤
                 │ PK  sales_key     │
                 │ FK  date_key      │
                 │ FK  shop_key      │
                 │ FK  product_key   │
                 │ FK  customer_key  │
                 │     quantity      │
                 │     unit_price    │
                 │     total_amount  │
                 └─────────▲─────────┘
                           │
                 ┌─────────┴─────────┐
                 │   dim_customer    │
                 ├───────────────────┤
                 │ PK  customer_key  │
                 │     customer_id   │
                 │     segment       │
                 └───────────────────┘
```

## Setup & Loading

### 1. Initialize Schema
The schema is automatically applied on first boot of PostgreSQL via Docker Compose (`./warehouse/schema.sql`).
To apply manually:
```bash
psql -h localhost -U finpilot_user -d finpilot -f schema.sql
```

### 2. Run Gold Loader
```bash
pip install -r requirements.txt

# Load from Gold Parquet or CSV
python load_gold.py --source ../data-generator/output/retail_transactions.csv --max-rows 100000
```
