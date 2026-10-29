"""
Finpilot-AI Database Session and Connection Pooling
Provides explicit database engine initialization, connection health verification,
and session management without silent data-store switching.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("finpilot.database")

# Explicit configuration: defaults to SQLite for local development, or PostgreSQL in Docker/production
DEFAULT_LOCAL_URL = "sqlite:///./finpilot_local.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_LOCAL_URL)
ALLOW_SQLITE_FALLBACK = os.getenv("ALLOW_SQLITE_FALLBACK", "true").lower() in ("true", "1", "yes")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1,
    )

ACTIVE_DATABASE_TYPE = "unknown"
ACTIVE_DATABASE_URL = ""


def _resolve_db_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel_path = url.replace("sqlite:///", "")
        if rel_path.startswith("./"):
            rel_path = rel_path[2:]
        if not os.path.isabs(rel_path):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            abs_path = os.path.abspath(os.path.join(repo_root, rel_path))
            return f"sqlite:///{abs_path}"
    return url


def init_engine():
    global ACTIVE_DATABASE_TYPE, ACTIVE_DATABASE_URL
    url = _resolve_db_url(DATABASE_URL)

    if url.startswith("sqlite"):
        ACTIVE_DATABASE_TYPE = "sqlite"
        ACTIVE_DATABASE_URL = url
        logger.info(f"Explicit SQLite database selected: {url}")
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
        )

    # PostgreSQL configuration
    ACTIVE_DATABASE_TYPE = "postgresql"
    ACTIVE_DATABASE_URL = url
    try:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 3},
        )
        # Verify connection immediately to ensure readiness
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        logger.info("Successfully connected to PostgreSQL warehouse.")
        return engine
    except Exception as e:
        if ALLOW_SQLITE_FALLBACK:
            logger.warning(
                f"PostgreSQL connection failed ({e}). Explicit ALLOW_SQLITE_FALLBACK=true is enabled; using SQLite."
            )
            ACTIVE_DATABASE_TYPE = "sqlite"
            ACTIVE_DATABASE_URL = DEFAULT_LOCAL_URL
            return create_engine(
                DEFAULT_LOCAL_URL,
                connect_args={"check_same_thread": False},
            )
        else:
            masked_url = url
            if "@" in url:
                scheme_user, host_db = url.split("@", 1)
                scheme = scheme_user.split("://")[0]
                masked_url = f"{scheme}://***:***@{host_db}"
            raise ConnectionError(
                f"Unable to connect to configured PostgreSQL database at {masked_url}: {e}. "
                "Ensure PostgreSQL is running, or set DATABASE_URL=sqlite:///./finpilot_local.db "
                "in your .env file for local development."
            ) from e


engine = init_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency providing a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> dict:
    """Verifies live database connectivity and returns metadata without exposing secrets."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return {
            "connected": True,
            "dialect": engine.dialect.name,
            "url_safe": engine.url.render_as_string(hide_password=True),
        }
    except Exception as e:
        return {
            "connected": False,
            "dialect": engine.dialect.name if hasattr(engine, "dialect") else "unknown",
            "error": str(e).split("\n")[0],
        }
