"""
Pytest Test Suite for Finpilot-AI CSV Upload & Warehouse Ingestion Router
Tests validation, error boundaries, dimensional synchronization, and fact loading.
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models  # noqa: F401

from sqlalchemy.pool import StaticPool

# Create an in-memory SQLite database for isolated test execution
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_download_sample_csv(client):
    """GET /upload/sample should return 200 OK with CSV media type and proper headers."""
    response = client.get("/upload/sample")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    content = response.text
    assert "transaction_id,date,shop_id,product" in content
    assert "TXN_100001" in content


def test_download_template(client):
    """GET /upload/template should return 200 OK with header columns."""
    response = client.get("/upload/template")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    content = response.text
    assert "transaction_id" in content
    assert "product" in content
    assert "quantity" in content
    assert "total" in content


def test_upload_invalid_extension(client):
    """Uploading a non-CSV file should be rejected with HTTP 400."""
    files = {"file": ("data.json", b'{"key": "value"}', "application/json")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Invalid file format" in data["message"]


def test_upload_empty_csv(client):
    """Uploading an empty CSV file should fail validation with HTTP 400."""
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "validation failed" in data["message"].lower()


def test_upload_missing_required_column(client):
    """Uploading CSV missing required 'product' column should fail validation."""
    csv_content = (
        "transaction_id,date,quantity,unit_price,total\n"
        "TXN_999,2024-06-15 10:00:00,1,50.00,50.00\n"
    )
    files = {"file": ("invalid.csv", csv_content.encode("utf-8"), "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "product" in data["missing_required_columns"]


def test_upload_valid_csv_and_warehouse_ingestion(client, test_db):
    """Valid CSV upload should insert rows into fact_sales and synchronize dimensions."""
    csv_content = (
        "transaction_id,date,shop_id,product,category,quantity,unit_price,total,customer_id,payment_mode,cost_price\n"
        "TXN_001,2024-06-15 10:30:00,SHOP_001,Wireless Mouse,Electronics,2,25.00,50.00,CUST_001,Credit Card,15.00\n"
        "TXN_002,2024-06-15 11:15:00,SHOP_001,Cotton T-Shirt,Apparel,1,20.00,20.00,CUST_002,Debit Card,8.50\n"
        "TXN_003,2024-06-16 14:00:00,SHOP_002,Coffee Maker,Home & Kitchen,1,80.00,80.00,CUST_003,Cash,45.00\n"
    )
    files = {"file": ("transactions.csv", csv_content.encode("utf-8"), "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["inserted_rows"] == 3
    assert data["total_rows"] == 3
    assert data["valid_rows"] == 3
    assert data["quality_score"] == 100.0
    assert len(data["sample_preview"]) == 3

    # Verify fact_sales records in the database
    fact_count = test_db.execute(text("SELECT COUNT(*) FROM fact_sales;")).scalar()
    assert fact_count == 3

    # Verify dimensions created
    shop_count = test_db.execute(text("SELECT COUNT(*) FROM dim_shop;")).scalar()
    assert shop_count >= 2

    prod_count = test_db.execute(text("SELECT COUNT(*) FROM dim_product;")).scalar()
    assert prod_count >= 3


def test_upload_idempotency_duplicate_handling(client, test_db):
    """Uploading the same CSV twice should not create duplicate facts or throw errors."""
    csv_content = (
        "transaction_id,date,shop_id,product,category,quantity,unit_price,total,customer_id,payment_mode\n"
        "TXN_D1,2024-06-15 10:30:00,SHOP_001,Mouse,Electronics,1,25.00,25.00,CUST_001,Credit Card\n"
    )
    files = {"file": ("transactions.csv", csv_content.encode("utf-8"), "text/csv")}

    # First upload
    res1 = client.post("/upload", files=files)
    assert res1.status_code == 200
    assert res1.json()["inserted_rows"] == 1

    # Second upload with same transaction_id
    files2 = {"file": ("transactions.csv", csv_content.encode("utf-8"), "text/csv")}
    res2 = client.post("/upload", files=files2)
    assert res2.status_code == 200
    assert res2.json()["inserted_rows"] == 0
    assert "already present" in res2.json()["message"]

    # Verify total rows remained 1
    total = test_db.execute(text("SELECT COUNT(*) FROM fact_sales;")).scalar()
    assert total == 1


def test_upload_transitions_dashboard_to_live_mode(client, test_db):
    """Uploading CSV transitions the dashboard from Cold-Start demo to Live Warehouse."""
    # Before upload, fact_sales is empty -> is_demo should be True
    pre_res = client.get("/revenue")
    assert pre_res.status_code == 200
    assert pre_res.json()["is_demo"] is True

    # Upload clean CSV data
    csv_content = (
        "transaction_id,date,shop_id,product,category,quantity,unit_price,total,customer_id,payment_mode\n"
        "TXN_LIVE_01,2024-06-15 10:00:00,SHOP_001,Gaming Keyboard,Electronics,2,100.00,200.00,CUST_001,Credit Card\n"
        "TXN_LIVE_02,2024-06-15 12:00:00,SHOP_002,Coffee Maker,Home & Kitchen,1,150.00,150.00,CUST_002,UPI\n"
    )
    files = {"file": ("live_data.csv", csv_content.encode("utf-8"), "text/csv")}
    upload_res = client.post("/upload", files=files)
    assert upload_res.status_code == 200
    assert upload_res.json()["success"] is True

    # Now /revenue should return live data with is_demo = False
    post_res = client.get("/revenue")
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["is_demo"] is False
    assert data["total_revenue"] == 350.0
    assert data["total_orders"] == 2


def test_upload_kaggle_online_retail_sample(client, test_db):
    """Kaggle Online Retail dataset with returns and missing customer IDs should ingest correctly."""
    kaggle_content = (
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,2024-06-01 08:26:00,2.50,17850,United Kingdom\n"
        "536365,71053,WHITE METAL LANTERN,4,2024-06-01 08:26:00,3.00,17850,United Kingdom\n"
        "C536379,D,Discount,-1,2024-06-02 09:41:00,7.00,14527,United Kingdom\n"
        "536373,85123A,WHITE HANGING HEART T-LIGHT HOLDER,2,2024-06-03 09:02:00,2.50,,United Kingdom\n"
    )
    files = {"file": ("kaggle_retail.csv", kaggle_content.encode("utf-8"), "text/csv")}
    res = client.post("/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["schema_detected"] == "Kaggle Online Retail"
    assert data["inserted_rows"] == 4
    assert data["return_count"] == 1

    # Verify fact_sales records exist in DB
    facts = test_db.execute(text("SELECT COUNT(*), SUM(total_amount) FROM fact_sales;")).fetchone()
    assert facts[0] == 4
    # Expected net revenue: (6*2.50) + (4*3.00) + (-1*7.00) + (2*2.50) = 15.00 + 12.00 - 7.00 + 5.00 = 25.00
    net_rev = float(facts[1])
    assert abs(net_rev - 25.00) < 0.01

    # Check revenue summary endpoint computes gross and returns correctly
    rev_res = client.get("/revenue")
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["is_demo"] is False
    assert rev_data["total_revenue"] == 25.00
    assert rev_data["gross_revenue"] == 32.00
    assert rev_data["returns_amount"] == 7.00


def test_health_check_endpoint(client):
    """GET /health and /api/v1/health should report database connection and dialect."""
    for path in ["/health", "/api/v1/health"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["database"] == "connected"
        assert data["database_dialect"] == "sqlite"
        assert "kafka" in data["services"]


def test_revenue_date_validation(client, test_db):
    """Invalid date format or start_date > end_date should return HTTP 400."""
    res_bad_format = client.get("/revenue?start_date=2024/06/01")
    assert res_bad_format.status_code == 400
    assert "Invalid start_date format" in res_bad_format.json()["detail"]

    res_inverted = client.get("/revenue?start_date=2024-06-30&end_date=2024-06-01")
    assert res_inverted.status_code == 400
    assert "start_date cannot be after end_date" in res_inverted.json()["detail"]


def test_upload_kaggle_online_retail_ii_variant(client, test_db):
    """Upload Kaggle dataset with 'Invoice', 'Price', and 'Customer ID' column names."""
    content = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/10 8:26,2.55,17850,United Kingdom\n"
        "536365,71053,WHITE METAL LANTERN,6,12/1/10 8:26,3.39,17850,United Kingdom\n"
        "C536379,D,Discount,-1,12/1/10 9:41,27.50,14527,United Kingdom\n"
        "536373,85123A,,2,12/1/10 9:02,2.55,,United Kingdom\n"
    )
    files = {"file": ("online_retail_II.csv", content.encode("utf-8"), "text/csv")}
    res = client.post("/upload", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["schema_detected"] == "Kaggle Online Retail"
    assert data["total_rows"] == 4
    assert data["valid_rows"] == 4
    assert data["inserted_rows"] == 4
    assert data["return_count"] == 1
    assert data["quality_score"] == 100.0


def test_upload_repeated_idempotency_kaggle(client, test_db):
    """Uploading the same Kaggle file twice must not insert duplicate fact_sales records."""
    content = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "536365,85123A,WHITE HANGING HEART,2,12/1/10 8:26,5.00,17850,United Kingdom\n"
        "536366,71053,WHITE LANTERN,1,12/1/10 8:28,10.00,17850,United Kingdom\n"
    )
    # First upload: 2 rows inserted
    files1 = {"file": ("kaggle.csv", content.encode("utf-8"), "text/csv")}
    res1 = client.post("/upload", files=files1)
    assert res1.status_code == 200
    assert res1.json()["inserted_rows"] == 2

    # Second upload of identical file: 0 rows inserted, duplicate_count == 2
    files2 = {"file": ("kaggle.csv", content.encode("utf-8"), "text/csv")}
    res2 = client.post("/upload", files=files2)
    assert res2.status_code == 200
    assert res2.json()["inserted_rows"] == 0
    assert res2.json()["duplicate_count"] == 2
    assert "already present" in res2.json()["message"]

    # Verify fact_sales has exactly 2 records
    total = test_db.execute(text("SELECT COUNT(*) FROM fact_sales;")).scalar()
    assert total == 2


