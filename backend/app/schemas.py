"""
Pydantic Schemas for Finpilot-AI API Data Contracts
"""

from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class CategoryRevenue(BaseModel):
    category: str
    revenue: float
    percentage: float
    units_sold: int


class ShopRevenue(BaseModel):
    shop_id: str
    shop_name: str
    tier: str
    revenue: float
    transactions: int


class RevenueSummaryResponse(BaseModel):
    total_revenue: float = Field(..., description="Total aggregate net revenue in USD")
    gross_revenue: Optional[float] = Field(None, description="Gross sales revenue before returns")
    returns_amount: Optional[float] = Field(None, description="Total returns and refunds amount")
    total_orders: int = Field(..., description="Total transaction volume")
    avg_order_value: float = Field(..., description="Average Basket Value")
    total_units_sold: int = Field(..., description="Total items sold")
    growth_percentage: float = Field(..., description="Period-over-period growth")
    top_categories: List[CategoryRevenue]
    top_shops: List[ShopRevenue]
    is_demo: bool = Field(False, description="True if using cold-start demo fallback")


class TrendPoint(BaseModel):
    date: str
    revenue: float
    order_count: int
    avg_order_value: float


class TrendsResponse(BaseModel):
    timeframe: str
    data_points: List[TrendPoint]
    total_points: int
    is_demo: bool = Field(False, description="True if using cold-start demo fallback")


class ForecastPoint(BaseModel):
    date: str
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastResponse(BaseModel):
    model_version: str
    forecast_horizon_days: int
    generated_at: str
    forecast_data: List[ForecastPoint]
    is_demo: bool = Field(False, description="True if using cold-start demo fallback")


class AnomalyItem(BaseModel):
    anomaly_id: int
    transaction_id: str
    date: str
    shop_id: str
    total_amount: float
    anomaly_score: float
    severity: str
    reason: str


class AnomaliesResponse(BaseModel):
    total_anomalies: int
    critical_count: int
    warning_count: int
    items: List[AnomalyItem]
    is_demo: bool = Field(False, description="True if using cold-start demo fallback")


class RecommendationItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    impact: str
    priority: str
    metric: str
    action_label: str


class RecommendationsResponse(BaseModel):
    generated_at: str
    recommendations: List[RecommendationItem]
    is_demo: bool = Field(False, description="True if using cold-start demo fallback")


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    database_dialect: Optional[str] = None
    version: str
    services: Optional[Dict[str, str]] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None
    schema_detected: Optional[str] = "Canonical Finpilot"
    total_rows: int = 0
    valid_rows: int = 0
    inserted_rows: int = 0
    rejected_rows: int = 0
    duplicate_count: int = 0
    return_count: int = 0
    quality_score: float = 0.0
    detected_columns: List[str] = Field(default_factory=list)
    missing_required_columns: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sample_preview: List[Dict] = Field(default_factory=list)
