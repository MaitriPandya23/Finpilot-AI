FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY forecasting.py anomaly_detector.py run_pipeline.py ./

ENTRYPOINT ["python", "run_pipeline.py"]
