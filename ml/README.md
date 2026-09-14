# Finpilot-AI / Machine Learning Engine

Predictive and prescriptive analytics engine powering the Finpilot-AI BI platform.

## Models
1. **Prophet Revenue Forecasting (`forecasting.py`)**:
   - Analyzes historical daily revenue from `fact_sales` and `dim_date`.
   - Incorporates weekly and yearly seasonality plus trend change-points.
   - Outputs 30–60 day future forecast with 95% confidence intervals (`yhat`, `yhat_lower`, `yhat_upper`) stored in `ml_forecasts`.

2. **Isolation Forest Anomaly Detection (`anomaly_detector.py`)**:
   - Detects price-quantity deviations, extreme total transactions, and store volume outliers.
   - Assigns severity ratings (`Critical`, `Warning`, `Moderate`) and human-readable diagnostic explanations stored in `ml_anomalies`.

3. **Orchestrator (`run_pipeline.py`)**:
   - Runs both models sequentially with unified database connection handling.

## Usage

### Local Execution
```bash
pip install -r requirements.txt

# Run full ML pipeline
python run_pipeline.py --forecast-days 30 --anomaly-sample 50000

# Or run individual models
python forecasting.py --periods 45
python anomaly_detector.py --sample-size 25000
```

### Docker
```bash
docker build -t finpilot-ml .
docker run --network finpilot-network -e DATABASE_URL=postgresql://finpilot_user:finpilot_pass@postgres:5432/finpilot finpilot-ml
```
