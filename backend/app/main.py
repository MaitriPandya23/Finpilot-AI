"""
Finpilot-AI FastAPI Application Gateway
Main entrypoint exposing Business Intelligence & Machine Learning endpoints.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models  # Ensures all ORM models are registered with Base.metadata
from .schemas import HealthResponse
from .routers import revenue, trends, forecast, anomalies, recommendations, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for resource initialization."""
    print("Starting Finpilot-AI API Server...")
    try:
        # Create tables if not existing (useful for local development)
        Base.metadata.create_all(bind=engine)
        print("Database schema verified.")
    except Exception as e:
        print(f"Schema verification note: {e}")
    yield
    print("Shutting down Finpilot-AI API Server...")


app = FastAPI(
    title="Finpilot-AI BI Platform API",
    description="Big Data Business Intelligence & Predictive Analytics API for Retail Transactions.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000")
origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if "*" not in origins:
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Endpoints directly at root and under /api/v1
app.include_router(revenue.router)
app.include_router(trends.router)
app.include_router(forecast.router)
app.include_router(anomalies.router)
app.include_router(recommendations.router)
app.include_router(upload.router)

app.include_router(revenue.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(forecast.router, prefix="/api/v1")
app.include_router(anomalies.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")


@app.get("/", tags=["System"])
def root():
    return {
        "platform": "Finpilot-AI",
        "description": "AI-powered Big Data BI platform for retail and small businesses",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": [
            "/revenue",
            "/trends",
            "/forecast",
            "/anomalies",
            "/recommendations",
            "/upload",
            "/upload/sample",
            "/upload/template",
            "/health",
        ],
    }


from .database import engine, Base, check_database_health


@app.get("/health", response_model=HealthResponse, tags=["System"])
@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
def health_check():
    db_status = check_database_health()
    is_healthy = db_status.get("connected", False)

    # Optional services probes
    services = {
        "kafka": "optional (offline)",
        "minio": "optional (offline)",
    }

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        database="connected" if is_healthy else "disconnected",
        database_dialect=db_status.get("dialect", "unknown"),
        version="1.0.0",
        services=services,
    )
