"""
SQLAlchemy ORM Models for Finpilot-AI Star Schema & ML Storage
"""

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship
from .database import Base


class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)
    date_actual = Column(Date, unique=True, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String(15), nullable=False)
    day_of_month = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(15), nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)


class DimShop(Base):
    __tablename__ = "dim_shop"

    shop_key = Column(Integer, primary_key=True, autoincrement=True)
    shop_id = Column(String(50), unique=True, nullable=False)
    shop_name = Column(String(100), nullable=False)
    location = Column(String(100))
    city = Column(String(50))
    tier = Column(String(20))


class DimProduct(Base):
    __tablename__ = "dim_product"

    product_key = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)
    default_unit_price = Column(Numeric(10, 2))


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100))
    segment = Column(String(50), default="Regular")
    loyalty_tier = Column(String(20), default="Bronze")


class FactSales(Base):
    __tablename__ = "fact_sales"

    sales_key = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), unique=True, nullable=False)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    shop_key = Column(Integer, ForeignKey("dim_shop.shop_key"), nullable=False)
    product_key = Column(Integer, ForeignKey("dim_product.product_key"), nullable=False)
    customer_key = Column(Integer, ForeignKey("dim_customer.customer_key"), nullable=False)
    transaction_timestamp = Column(DateTime, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_mode = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class MLForecast(Base):
    __tablename__ = "ml_forecasts"

    forecast_id = Column(Integer, primary_key=True, autoincrement=True)
    ds = Column(Date, nullable=False)
    yhat = Column(Numeric(14, 2), nullable=False)
    yhat_lower = Column(Numeric(14, 2), nullable=False)
    yhat_upper = Column(Numeric(14, 2), nullable=False)
    model_version = Column(String(50), default="prophet_v1")
    generated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class MLAnomaly(Base):
    __tablename__ = "ml_anomalies"

    anomaly_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64))
    date = Column(Date, nullable=False)
    shop_id = Column(String(50))
    total_amount = Column(Numeric(12, 2))
    anomaly_score = Column(Numeric(8, 4))
    is_anomaly = Column(Boolean, default=True)
    severity = Column(String(20), default="Warning")
    reason = Column(String(255))
    detected_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
