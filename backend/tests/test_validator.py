"""
Pytest Test Suite for Finpilot-AI CSV Ingestion Validator
Validates file-level and row-level quality constraints across expected business CSV patterns.
"""

import io
import pytest
from app.services.validator import validate_csv, ValidationResult, REQUIRED_COLUMNS


@pytest.fixture
def clean_csv_content() -> str:
    """Returns a pristine sample CSV with required and optional fields."""
    return (
        "transaction_id,date,shop_id,product,category,quantity,unit_price,total,customer_id,payment_mode,cost_price\n"
        "TXN_001,2024-06-15 10:30:00,SHOP_001,Wireless Mouse,Electronics,2,25.00,50.00,CUST_001,Credit Card,15.00\n"
        "TXN_002,2024-06-15 11:15:00,SHOP_001,Cotton T-Shirt,Apparel,1,20.00,20.00,CUST_002,Debit Card,8.50\n"
        "TXN_003,2024-06-16 14:00:00,SHOP_002,Coffee Maker,Home & Kitchen,1,80.00,80.00,CUST_003,Cash,45.00\n"
        "TXN_004,2024-06-16 16:45:00,SHOP_003,Yoga Mat,Sports & Outdoors,3,30.00,90.00,CUST_004,UPI,12.00\n"
        "TXN_005,2024-06-17 09:20:00,SHOP_002,Face Cleanser,Beauty,2,15.00,30.00,CUST_005,Credit Card,6.00\n"
    )


def test_clean_csv(clean_csv_content):
    """Clean CSV should pass with 100% quality score, no errors, and no missing required columns."""
    result = validate_csv(clean_csv_content)
    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    assert result.total_rows == 5
    assert result.valid_rows == 5
    assert result.duplicate_count == 0
    assert result.quality_score == 100.0
    assert result.missing_required_columns == []
    assert len(result.sample_preview) == 5
    assert result.sample_preview[0]["transaction_id"] == "TXN_001"


def test_missing_required_column():
    """Omitting a required column (e.g., 'product') must mark result as invalid."""
    csv_data = (
        "transaction_id,date,quantity,unit_price,total\n"
        "TXN_001,2024-06-15,1,50.00,50.00\n"
    )
    result = validate_csv(csv_data)
    assert result.is_valid is False
    assert "product" in result.missing_required_columns
    assert any("Missing required column(s)" in w for w in result.warnings)


def test_missing_optional_cost_price():
    """Missing 'cost_price' should remain valid, but issue a warning for profit analytics."""
    csv_data = (
        "transaction_id,date,product,category,quantity,unit_price,total\n"
        "TXN_001,2024-06-15,Keyboard,Electronics,1,100.00,100.00\n"
        "TXN_002,2024-06-16,Monitor,Electronics,1,300.00,300.00\n"
    )
    result = validate_csv(csv_data)
    assert result.is_valid is True
    assert result.total_rows == 2
    assert result.valid_rows == 2
    assert result.quality_score == 100.0
    assert any("cost_price" in w for w in result.warnings)


def test_duplicates():
    """Duplicate transaction IDs should be counted and excluded from valid rows."""
    csv_data = (
        "transaction_id,date,product,quantity,unit_price,total\n"
        "TXN_DUP,2024-06-15,Mouse,1,25.00,25.00\n"
        "TXN_DUP,2024-06-15,Mouse,1,25.00,25.00\n"
        "TXN_UNIQUE,2024-06-16,Keyboard,1,75.00,75.00\n"
    )
    result = validate_csv(csv_data)
    assert result.total_rows == 3
    assert result.duplicate_count == 1
    assert result.valid_rows == 2
    assert result.quality_score == 66.7
    assert any("duplicate transaction ID" in w for w in result.warnings)


def test_bad_dates():
    """Unreadable dates and future dates beyond tomorrow must be flagged."""
    csv_data = (
        "transaction_id,date,product,quantity,unit_price,total\n"
        "TXN_001,invalid-date-string,Mouse,1,25.00,25.00\n"
        "TXN_002,2099-12-31 00:00:00,Keyboard,1,75.00,75.00\n"
        "TXN_003,2024-06-15 12:00:00,Monitor,1,250.00,250.00\n"
    )
    result = validate_csv(csv_data)
    assert result.total_rows == 3
    assert result.valid_rows == 1
    assert any("unreadable date" in w for w in result.warnings)
    assert any("future dates" in w for w in result.warnings)


def test_negative_and_zero_values():
    """Quantity <= 0, unit_price < 0, and total < 0 must be flagged as invalid."""
    csv_data = (
        "transaction_id,date,product,quantity,unit_price,total\n"
        "TXN_001,2024-06-15,Mouse,-2,25.00,50.00\n"
        "TXN_002,2024-06-15,Keyboard,0,75.00,0.00\n"
        "TXN_003,2024-06-15,Headphones,1,-50.00,50.00\n"
        "TXN_004,2024-06-15,Webcam,1,40.00,-40.00\n"
        "TXN_005,2024-06-15,Monitor,1,200.00,200.00\n"
    )
    result = validate_csv(csv_data)
    assert result.total_rows == 5
    assert result.valid_rows == 1  # Only TXN_005 is valid
    assert result.quality_score == 20.0
    assert result.is_valid is False  # Fails 50% minimum quality threshold
    assert any("invalid quantity" in w for w in result.warnings)
    assert any("invalid unit price" in w for w in result.warnings)
    assert any("negative or invalid total" in w for w in result.warnings)


def test_empty_file():
    """Empty inputs (string, bytes, or headers-only) must return is_valid=False without raising exceptions."""
    # 1. Completely empty string
    res_empty = validate_csv("")
    assert res_empty.is_valid is False
    assert res_empty.total_rows == 0
    assert res_empty.quality_score == 0.0

    # 2. Empty bytes
    res_bytes = validate_csv(b"")
    assert res_bytes.is_valid is False
    assert res_bytes.total_rows == 0

    # 3. Header only (no rows)
    res_header_only = validate_csv("transaction_id,date,product,quantity,unit_price,total\n")
    assert res_header_only.is_valid is False
    assert res_header_only.total_rows == 0
    assert any("no transaction data rows" in w for w in res_header_only.warnings)


def test_extra_columns():
    """Unexpected extra columns should not invalidate the CSV; they trigger a warning."""
    csv_data = (
        "transaction_id,date,product,quantity,unit_price,total,warehouse_aisle,cashier_name\n"
        "TXN_001,2024-06-15,Mouse,1,25.00,25.00,Aisle-4,John\n"
        "TXN_002,2024-06-16,Keyboard,1,75.00,75.00,Aisle-2,Sarah\n"
    )
    result = validate_csv(csv_data)
    assert result.is_valid is True
    assert result.total_rows == 2
    assert result.valid_rows == 2
    assert any("Unexpected extra column(s)" in w for w in result.warnings)
    assert "warehouse_aisle" in str(result.warnings)


def test_total_mismatch_warning():
    """A discrepancy between total and quantity * unit_price issues a warning without discarding row."""
    csv_data = (
        "transaction_id,date,product,quantity,unit_price,total\n"
        "TXN_001,2024-06-15,Mouse,2,25.00,60.00\n"  # 2 * 25 != 60 (diff = 10 > 0.05)
    )
    result = validate_csv(csv_data)
    assert result.is_valid is True
    assert result.total_rows == 1
    assert result.valid_rows == 1
    assert any("total amount variance" in w for w in result.warnings)


def test_bytes_and_stream_inputs(clean_csv_content):
    """Validator must accept both raw bytes and IO stream inputs seamlessly."""
    # Bytes input
    res_bytes = validate_csv(clean_csv_content.encode("utf-8"))
    assert res_bytes.is_valid is True
    assert res_bytes.total_rows == 5

    # StringIO input
    stream = io.StringIO(clean_csv_content)
    res_stream = validate_csv(stream)
    assert res_stream.is_valid is True
    assert res_stream.total_rows == 5
