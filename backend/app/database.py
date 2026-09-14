"""
Finpilot-AI Database Session and Connection Pooling
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finpilot_user:finpilot_pass@localhost:5432/finpilot"
)

# Robust fallback to SQLite in memory if local postgres isn't running
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
except Exception as e:
    print(f"Warning: Primary database connection failed ({e}). Falling back to sqlite.")
    engine = create_engine("sqlite:///./finpilot_local.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency providing a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
