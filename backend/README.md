# Finpilot-AI / Backend Gateway

High-performance REST API built with FastAPI and SQLAlchemy, serving executive analytics, historical trends, Prophet forecasts, and Isolation Forest anomaly reports.

## Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /revenue` | `GET` | Overall revenue KPIs, AOV, category mix, and shop rankings. Supports `?start_date=&end_date=` |
| `GET /trends` | `GET` | Chronological revenue & transaction volume time-series. Supports `?timeframe=daily\|weekly\|monthly&limit=60` |
| `GET /forecast` | `GET` | Predictive revenue curve with 95% confidence intervals (`yhat`, `yhat_lower`, `yhat_upper`). Supports `?horizon_days=30` |
| `GET /anomalies` | `GET` | Flagged transactions, anomaly scores, severity ratings (`Critical`, `Warning`), and diagnostic reasons. Supports `?severity=&limit=` |
| `GET /recommendations` | `GET` | AI-driven prescriptive actions (restock warnings, fraud audits, pricing opportunities). |
| `GET /health` | `GET` | System health check and database connectivity status. |
| `GET /docs` | `GET` | Interactive Swagger UI API documentation. |

## Running Locally

```bash
pip install -r requirements.txt

# Run development server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker
```bash
docker build -t finpilot-backend .
docker run -p 8000:8000 --network finpilot-network finpilot-backend
```
