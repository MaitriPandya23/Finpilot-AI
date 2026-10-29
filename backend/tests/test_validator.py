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


def test_kaggle_online_retail_schema_detection():
    """Validator must detect Kaggle Online Retail schema, map fields, and account for returns."""
    kaggle_csv = (
        "InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,2024-06-01 08:26:00,2.55,17850,United Kingdom\n"
        "536365,71053,WHITE METAL LANTERN,6,2024-06-01 08:26:00,3.39,17850,United Kingdom\n"
        "C536379,D,Discount,-1,2024-06-04 09:41:00,27.50,14527,United Kingdom\n"
        "536373,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,2024-06-03 09:02:00,2.55,,United Kingdom\n"
    )
    res = validate_csv(kaggle_csv)
    assert res.is_valid is True
    assert res.schema_detected == "Kaggle Online Retail"
    assert res.total_rows == 4
    assert res.valid_rows == 4
    assert res.return_count == 1
    assert any("Kaggle Online Retail" in w for w in res.warnings)


def test_kaggle_online_retail_ii_exact_headers():
    """Validator must accept exact Kaggle Online Retail II headers (Invoice, Price, Customer ID)."""
    kaggle_ii = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/10 8:26,2.55,17850,United Kingdom\n"
        "536365,71053,WHITE METAL LANTERN,6,12/1/10 8:26,3.39,17850,United Kingdom\n"
        "C536379,D,Discount,-1,12/1/10 9:41,27.50,14527,United Kingdom\n"
        "536373,85123A,,2,12/1/10 9:02,2.55,,United Kingdom\n"
    )
    res = validate_csv(kaggle_ii)
    assert res.is_valid is True
    assert res.schema_detected == "Kaggle Online Retail"
    assert res.total_rows == 4
    assert res.valid_rows == 4
    assert res.return_count == 1
    assert res.missing_required_columns == []
    # Verify product fallback from empty description to SKU
    assert res.sample_preview[3]["product"] == "SKU_85123A"
    # Verify customer ID fallback from empty to CUST_ANONYMOUS
    assert res.sample_preview[3]["customer_id"] == "CUST_ANONYMOUS"


def test_header_case_and_whitespace_variations():
    """Headers with mixed case, whitespace, and alternate punctuation must map cleanly."""
    varied_csv = (
        "  INVOICE  , Stock Code , description , QTY , Invoice Date , Unit Price , Customer ID , COUNTRY \n"
        "536365,85123A,Heart Light,4,2024-06-01 10:00:00,5.00,12345,France\n"
    )
    res = validate_csv(varied_csv)
    assert res.is_valid is True
    assert res.schema_detected == "Kaggle Online Retail"
    assert res.valid_rows == 1
    assert res.missing_required_columns == []
    assert float(res.sample_preview[0]["total"]) == 20.00


def test_total_calculation_from_quantity_and_price():
    """When source lacks 'total', it must be computed as Quantity * Price."""
    no_total_csv = (
        "transaction_id,date,product,quantity,unit_price\n"
        "TXN_A,2024-06-01,Wireless Mouse,3,25.50\n"
        "TXN_B,2024-06-02,USB Hub,2,15.00\n"
    )
    res = validate_csv(no_total_csv)
    assert res.is_valid is True
    assert res.valid_rows == 2
    assert float(res.sample_preview[0]["total"]) == 76.50
    assert float(res.sample_preview[1]["total"]) == 30.00


def test_negative_quantities_and_returns_in_kaggle():
    """Returns with negative quantities or C invoice prefix must be preserved with negative total."""
    returns_csv = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "536365,85123A,Standard Sale,5,2024-06-01 10:00:00,10.00,17850,United Kingdom\n"
        "C536379,D,Cancelled Item,-2,2024-06-02 10:00:00,15.00,17850,United Kingdom\n"
        "C536380,22139,Return Credit Note,1,2024-06-03 10:00:00,20.00,17850,United Kingdom\n"
    )
    res = validate_csv(returns_csv)
    assert res.is_valid is True
    assert res.total_rows == 3
    assert res.valid_rows == 3
    assert res.return_count == 2
    # C536379: -2 * 15.00 = -30.00
    assert float(res.sample_preview[1]["total"]) == -30.00
    # C536380: cancellation prefix C flips positive qty 1 to -1 -> total -20.00
    assert float(res.sample_preview[2]["total"]) == -20.00


def test_missing_optional_customer_id():
    """Missing Customer ID must assign anonymous fallback without rejecting row."""
    csv_data = (
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        "536365,85123A,Guest Purchase,1,2024-06-01 10:00:00,12.00,,United Kingdom\n"
    )
    res = validate_csv(csv_data)
    assert res.is_valid is True
    assert res.valid_rows == 1
    assert res.sample_preview[0]["customer_id"] == "CUST_ANONYMOUS"


def test_unsupported_csv_schema():
    """A completely unrecognizable CSV schema must fail validation with clear instructions."""
    unsupported_csv = (
        "employee_name,department,salary,hire_date\n"
        "Alice,Engineering,120000,2020-01-15\n"
        "Bob,Marketing,95000,2021-03-20\n"
    )
    res = validate_csv(unsupported_csv)
    assert res.is_valid is False
    assert res.schema_detected == "Unsupported Schema"
    assert "transaction_id" in res.missing_required_columns
    assert "quantity" in res.missing_required_columns
    assert any("Please ensure CSV includes transaction identifier" in w for w in res.warnings)

