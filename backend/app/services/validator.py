"""
Finpilot-AI CSV Data Ingestion & Schema Normalization Validator
Performs robust file-level and row-level quality validation for business CSV uploads.
Supports Canonical Finpilot, Kaggle Online Retail, and Generic Retail schemas.
"""

from io import BytesIO, StringIO
import os
import re
from typing import Union, IO, List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

MIN_QUALITY_SCORE = 50.0
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_ROW_COUNT = 1_000_000

# Canonical Finpilot Schema definition
REQUIRED_COLUMNS: List[str] = [
    "transaction_id",
    "date",
    "product",
    "quantity",
    "unit_price",
    "total",
]

OPTIONAL_COLUMNS: List[str] = [
    "cost_price",
    "category",
    "shop_id",
    "customer_id",
    "payment_mode",
    "stock_code",
]

# Field aliases for automatic column mapping (case/whitespace/punctuation-insensitive)
FIELD_ALIASES: Dict[str, List[str]] = {
    "transaction_id": [
        "transactionid", "transaction_id", "txnid", "txn_id",
        "invoiceno", "invoice_no", "invoice", "invoicenumber", "orderid", "order_id"
    ],
    "date": [
        "date", "invoicedate", "invoice_date", "timestamp", "transactiondate",
        "transaction_date", "datetime", "createdat", "created_at"
    ],
    "product": [
        "product", "description", "itemdescription", "item_description",
        "productname", "product_name", "item"
    ],
    "quantity": [
        "quantity", "qty", "units", "quantitypurchased"
    ],
    "unit_price": [
        "unitprice", "unit_price", "price", "rate", "itemprice", "item_price"
    ],
    "total": [
        "total", "totalamount", "total_amount", "amount", "sales", "linetotal", "line_total", "totalprice"
    ],
    "stock_code": [
        "stockcode", "stock_code", "productcode", "product_code", "sku", "itemcode"
    ],
    "customer_id": [
        "customerid", "customer_id", "custid", "cust_id", "clientid", "client_id"
    ],
    "shop_id": [
        "shopid", "shop_id", "country", "storeid", "store_id", "location", "store"
    ],
    "category": [
        "category", "productcategory", "product_category", "dept", "department"
    ],
    "payment_mode": [
        "paymentmode", "payment_mode", "paymentmethod", "payment_method", "payment"
    ],
    "cost_price": [
        "costprice", "cost_price", "cost", "unitcost", "unit_cost"
    ],
}


def normalize_col_name(col: str) -> str:
    """Strips UTF-8 BOM, whitespace, quotes, and non-alphanumeric characters."""
    cleaned = str(col).replace("\ufeff", "").strip().lower()
    return re.sub(r"[^a-z0-9]", "", cleaned)


class ValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    duplicate_count: int
    return_count: int = 0
    quality_score: float  # 0.0-100.0, rounded to 1 decimal
    detected_columns: list[str]
    schema_detected: str = "Canonical Finpilot"
    missing_required_columns: list[str]
    warnings: list[str]
    sample_preview: list[dict]  # first 5 rows


def detect_and_normalize_schema(df: pd.DataFrame) -> Tuple[str, pd.DataFrame, List[str]]:
    """
    Detects whether incoming dataset is Canonical Finpilot, Kaggle Online Retail, or Generic.
    Maps fields to canonical column names: transaction_id, date, product, quantity, unit_price, total.
    Derives total = quantity * unit_price if total is not present in source.
    """
    warnings: List[str] = []
    raw_cols = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    df.columns = raw_cols

    # Build clean name -> original raw column mapping
    col_lookup: Dict[str, str] = {}
    for c in raw_cols:
        norm = normalize_col_name(c)
        if norm and norm not in col_lookup:
            col_lookup[norm] = c

    # Match each canonical field against raw columns
    mapped_cols: Dict[str, str] = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            norm_alias = normalize_col_name(alias)
            if norm_alias in col_lookup:
                mapped_cols[field] = col_lookup[norm_alias]
                break

    # Determine schema type
    has_invoice = False
    if "transaction_id" in mapped_cols:
        inv_clean = normalize_col_name(mapped_cols["transaction_id"])
        has_invoice = any(k in inv_clean for k in ["invoice", "invoiceno"])

    is_kaggle = (
        has_invoice
        or "stock_code" in mapped_cols
        or (
            "shop_id" in mapped_cols
            and normalize_col_name(mapped_cols["shop_id"]) == "country"
        )
    )

    is_canonical = (
        "transaction_id" in mapped_cols
        and normalize_col_name(mapped_cols["transaction_id"]) in ["transactionid", "txnid"]
        and "total" in mapped_cols
    )

    if is_kaggle:
        schema_name = "Kaggle Online Retail"
    elif is_canonical:
        schema_name = "Canonical Finpilot"
    else:
        can_derive = (
            "transaction_id" in mapped_cols
            and "date" in mapped_cols
            and "product" in mapped_cols
            and "quantity" in mapped_cols
            and "unit_price" in mapped_cols
        )
        schema_name = "Generic Mapped Retail" if can_derive else "Unsupported Schema"

    norm_df = pd.DataFrame(index=df.index)

    # 1. transaction_id
    if "transaction_id" in mapped_cols:
        raw_inv = df[mapped_cols["transaction_id"]].astype(str).str.strip()
        if schema_name == "Kaggle Online Retail":
            # Kaggle invoices can have multiple line items.
            # Use deterministic composite key: Invoice_StockCode_LineWithinInvoice
            stock_col = mapped_cols.get("stock_code")
            if stock_col:
                stock_series = df[stock_col].fillna("SKU").astype(str).str.strip()
            else:
                stock_series = pd.Series("ITEM", index=df.index)
            line_nums = (df.groupby(mapped_cols["transaction_id"]).cumcount() + 1).astype(str)
            norm_df["transaction_id"] = raw_inv + "_" + stock_series + "_" + line_nums
        else:
            norm_df["transaction_id"] = raw_inv

    # 2. date
    if "date" in mapped_cols:
        norm_df["date"] = df[mapped_cols["date"]].astype(str).str.strip()

    # 3. product
    if "product" in mapped_cols:
        prod_series = df[mapped_cols["product"]].fillna("").astype(str).str.strip()
        stock_col = mapped_cols.get("stock_code")
        if stock_col:
            stock_series = df[stock_col].fillna("").astype(str).str.strip()
            blank_mask = prod_series.isna() | (prod_series == "") | prod_series.str.lower().isin(["nan", "null", "none"])
            prod_series = prod_series.mask(blank_mask, "SKU_" + stock_series)
        blank_mask2 = prod_series.isna() | (prod_series == "") | prod_series.str.lower().isin(["nan", "null", "none", "sku_"])
        norm_df["product"] = prod_series.mask(blank_mask2, "General Merchandise")

    # 4. quantity (support signed quantities for returns/cancellations)
    if "quantity" in mapped_cols:
        qty_series = pd.to_numeric(df[mapped_cols["quantity"]], errors="coerce").fillna(0)
        # Check if invoice starts with C (cancellation/credit note)
        if "transaction_id" in mapped_cols:
            orig_inv = df[mapped_cols["transaction_id"]].astype(str).str.strip()
            is_cancel = orig_inv.str.startswith(("C", "c"))
            qty_series = qty_series.mask(is_cancel & (qty_series > 0), -qty_series)
        norm_df["quantity"] = qty_series.astype(int).astype(str)

    # 5. unit_price
    if "unit_price" in mapped_cols:
        price_series = pd.to_numeric(df[mapped_cols["unit_price"]], errors="coerce").fillna(0.0)
        norm_df["unit_price"] = price_series.round(2).astype(str)

    # 6. total (use source total if present, or calculate total = quantity * unit_price)
    if "total" in mapped_cols:
        norm_df["total"] = df[mapped_cols["total"]].astype(str).str.strip()
    elif "quantity" in norm_df.columns and "unit_price" in norm_df.columns:
        q_num = pd.to_numeric(norm_df["quantity"], errors="coerce").fillna(0)
        p_num = pd.to_numeric(norm_df["unit_price"], errors="coerce").fillna(0.0)
        norm_df["total"] = (q_num * p_num).round(2).astype(str)

    # Optional fields
    if "customer_id" in mapped_cols:
        cust = df[mapped_cols["customer_id"]].fillna("").astype(str).str.strip()
        norm_df["customer_id"] = (
            cust.replace("", "CUST_ANONYMOUS")
            .replace("nan", "CUST_ANONYMOUS")
            .replace("None", "CUST_ANONYMOUS")
        )
    else:
        norm_df["customer_id"] = "CUST_ANONYMOUS"

    if "shop_id" in mapped_cols:
        raw_shop = df[mapped_cols["shop_id"]].fillna("Global").astype(str).str.strip()
        norm_df["shop_id"] = raw_shop.apply(
            lambda s: s if s.startswith("SHOP_") else f"SHOP_{re.sub(r'[^A-Z0-9]', '_', s.upper())}"
        )
    else:
        norm_df["shop_id"] = "SHOP_001"

    if "category" in mapped_cols:
        norm_df["category"] = df[mapped_cols["category"]].fillna("Retail Goods").astype(str).str.strip()
    else:
        norm_df["category"] = "Retail Goods"

    if "payment_mode" in mapped_cols:
        norm_df["payment_mode"] = df[mapped_cols["payment_mode"]].fillna("Credit Card").astype(str).str.strip()
    else:
        norm_df["payment_mode"] = "Credit Card"

    if "cost_price" in mapped_cols:
        norm_df["cost_price"] = df[mapped_cols["cost_price"]].astype(str).str.strip()

    if "stock_code" in mapped_cols:
        norm_df["stock_code"] = df[mapped_cols["stock_code"]].astype(str).str.strip()

    # Informative schema mapping warning
    if schema_name == "Kaggle Online Retail":
        warnings.append(
            f"Detected and mapped Kaggle Online Retail schema ({', '.join(df.columns)}) to canonical warehouse model."
        )
    elif schema_name == "Generic Mapped Retail":
        warnings.append(
            f"Mapped source retail format ({', '.join(df.columns)}) to canonical warehouse model."
        )

    # Check for genuine unexpected extra columns (columns that were NOT recognized by any alias)
    recognized_raw_cols = set(mapped_cols.values())
    unrecognized = [c for c in raw_cols if c not in recognized_raw_cols]
    if unrecognized:
        warnings.append(
            f"Unexpected extra column(s) detected: {', '.join(unrecognized)} (will be safely ignored during warehouse load)."
        )

    return schema_name, norm_df, warnings


def validate_csv(source: Union[str, bytes, IO]) -> ValidationResult:
    """
    Validates a CSV file or buffer against Finpilot-AI data quality standards.
    Supports Canonical Finpilot, Kaggle Online Retail, and Generic Retail schemas.
    """
    warnings: List[str] = []

    # 1. Parse source safely handling UTF-8 and BOM
    try:
        if isinstance(source, bytes):
            if len(source.strip()) == 0:
                return ValidationResult(
                    is_valid=False,
                    total_rows=0,
                    valid_rows=0,
                    duplicate_count=0,
                    return_count=0,
                    quality_score=0.0,
                    detected_columns=[],
                    schema_detected="Unknown",
                    missing_required_columns=REQUIRED_COLUMNS.copy(),
                    warnings=["Uploaded file is empty (0 bytes)."],
                    sample_preview=[],
                )
            if len(source) > MAX_FILE_SIZE_BYTES:
                return ValidationResult(
                    is_valid=False,
                    total_rows=0,
                    valid_rows=0,
                    duplicate_count=0,
                    return_count=0,
                    quality_score=0.0,
                    detected_columns=[],
                    schema_detected="Unknown",
                    missing_required_columns=[],
                    warnings=[f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."],
                    sample_preview=[],
                )
            df = pd.read_csv(BytesIO(source), dtype=str, encoding="utf-8-sig")
        elif isinstance(source, str):
            if os.path.isfile(source):
                if os.path.getsize(source) == 0:
                    return ValidationResult(
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        duplicate_count=0,
                        return_count=0,
                        quality_score=0.0,
                        detected_columns=[],
                        schema_detected="Unknown",
                        missing_required_columns=REQUIRED_COLUMNS.copy(),
                        warnings=["Uploaded file is empty (0 bytes)."],
                        sample_preview=[],
                    )
                df = pd.read_csv(source, dtype=str, encoding="utf-8-sig")
            else:
                if not source.strip():
                    return ValidationResult(
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        duplicate_count=0,
                        return_count=0,
                        quality_score=0.0,
                        detected_columns=[],
                        schema_detected="Unknown",
                        missing_required_columns=REQUIRED_COLUMNS.copy(),
                        warnings=["Uploaded CSV content is empty."],
                        sample_preview=[],
                    )
                df = pd.read_csv(StringIO(source), dtype=str, encoding="utf-8-sig")
        else:
            df = pd.read_csv(source, dtype=str, encoding="utf-8-sig")

    except pd.errors.EmptyDataError:
        return ValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            duplicate_count=0,
            return_count=0,
            quality_score=0.0,
            detected_columns=[],
            schema_detected="Unknown",
            missing_required_columns=REQUIRED_COLUMNS.copy(),
            warnings=["File contains no readable data or column headers."],
            sample_preview=[],
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            duplicate_count=0,
            return_count=0,
            quality_score=0.0,
            detected_columns=[],
            schema_detected="Unknown",
            missing_required_columns=REQUIRED_COLUMNS.copy(),
            warnings=[f"Unable to parse CSV file: {str(e)}"],
            sample_preview=[],
        )

    # Clean header names
    df.columns = [str(col).replace("\ufeff", "").strip() for col in df.columns]
    detected_columns = list(df.columns)
    total_rows = len(df)

    if total_rows == 0:
        return ValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            duplicate_count=0,
            return_count=0,
            quality_score=0.0,
            detected_columns=detected_columns,
            schema_detected="Empty",
            missing_required_columns=REQUIRED_COLUMNS.copy(),
            warnings=["CSV file contains column headers but no transaction data rows."],
            sample_preview=[],
        )

    # Detect schema & normalize columns
    schema_name, norm_df, schema_warnings = detect_and_normalize_schema(df)
    warnings.extend(schema_warnings)

    norm_columns = list(norm_df.columns)
    missing_required = [col for col in REQUIRED_COLUMNS if col not in norm_columns]

    if missing_required:
        warnings.append(
            f"Missing required column(s): {', '.join(missing_required)}. "
            f"Please ensure CSV includes transaction identifier, date, product description, quantity, and unit price."
        )
        return ValidationResult(
            is_valid=False,
            total_rows=total_rows,
            valid_rows=0,
            duplicate_count=0,
            return_count=0,
            quality_score=0.0,
            detected_columns=detected_columns,
            schema_detected=schema_name,
            missing_required_columns=missing_required,
            warnings=warnings,
            sample_preview=[],
        )

    # Row-level validity mask
    is_invalid = pd.Series(False, index=norm_df.index)

    # 1. Null/empty in required fields
    for col in REQUIRED_COLUMNS:
        null_mask = (
            norm_df[col].isna()
            | (norm_df[col].astype(str).str.strip() == "")
            | (norm_df[col].astype(str).str.strip().str.lower().isin(["nan", "null", "none"]))
        )
        if null_mask.any():
            cnt = int(null_mask.sum())
            is_invalid |= null_mask
            warnings.append(f"{cnt} row(s) have missing or empty '{col}'.")

    # 2. Duplicate detection
    duplicate_count = 0
    if schema_name == "Kaggle Online Retail":
        dup_mask = df.duplicated(keep="first")
    else:
        dup_mask = norm_df.duplicated(subset=["transaction_id"], keep="first")

    if dup_mask.any():
        duplicate_count = int(dup_mask.sum())
        is_invalid |= dup_mask
        warnings.append(f"{duplicate_count} duplicate transaction ID(s) / record(s) detected and excluded.")

    # 3. Date validation & future date guard
    parsed_dates = pd.to_datetime(norm_df["date"], errors="coerce", format="mixed")
    unparseable_mask = (
        parsed_dates.isna()
        & norm_df["date"].notna()
        & (norm_df["date"].astype(str).str.strip() != "")
    )
    if unparseable_mask.any():
        cnt = int(unparseable_mask.sum())
        is_invalid |= unparseable_mask
        warnings.append(f"{cnt} row(s) have an unreadable date format.")

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    future_cutoff = now_naive + pd.Timedelta(days=1)
    if parsed_dates.dt.tz is not None:
        parsed_dates_naive = parsed_dates.dt.tz_convert(None)
    else:
        parsed_dates_naive = parsed_dates

    future_mask = (parsed_dates_naive > future_cutoff) & parsed_dates.notna()
    if future_mask.any():
        cnt = int(future_mask.sum())
        is_invalid |= future_mask
        warnings.append(f"{cnt} row(s) have future dates beyond today.")

    # 4. Numeric validity & returns/cancellation recognition
    numeric_qty = pd.to_numeric(norm_df["quantity"], errors="coerce")
    numeric_price = pd.to_numeric(norm_df["unit_price"], errors="coerce")
    numeric_total = pd.to_numeric(norm_df["total"], errors="coerce")

    # In retail: quantity < 0 represents returns/cancellations
    return_mask = (numeric_qty < 0) | norm_df["transaction_id"].astype(str).str.startswith(("C", "c"))
    return_count = int(return_mask.sum())
    if return_count > 0:
        warnings.append(f"{return_count} return/cancellation transaction(s) detected and accounted for in net revenue.")

    # Invalid quantity (non-numeric, or zero)
    if schema_name in ["Kaggle Online Retail", "Generic Mapped Retail"]:
        bad_qty_mask = numeric_qty.isna() | (numeric_qty == 0)
    else:
        bad_qty_mask = numeric_qty.isna() | (numeric_qty <= 0)

    if bad_qty_mask.any():
        cnt = int(bad_qty_mask.sum())
        is_invalid |= bad_qty_mask
        warnings.append(f"{cnt} row(s) have invalid quantity (must be non-zero numeric).")

    # Invalid unit price (negative or non-numeric)
    bad_price_mask = numeric_price.isna() | (numeric_price < 0)
    if bad_price_mask.any():
        cnt = int(bad_price_mask.sum())
        is_invalid |= bad_price_mask
        warnings.append(f"{cnt} row(s) have invalid unit price (must be a non-negative number).")

    # Total check for canonical schema
    if schema_name == "Canonical Finpilot":
        bad_total_mask = numeric_total.isna() | (numeric_total < 0)
        if bad_total_mask.any():
            cnt = int(bad_total_mask.sum())
            is_invalid |= bad_total_mask
            warnings.append(f"{cnt} row(s) have negative or invalid total amount.")

        if "cost_price" not in detected_columns:
            warnings.append("Optional column 'cost_price' is missing; profit margin and cost analytics will be unavailable.")

        # Variance check between total and quantity * unit_price
        expected_total = numeric_qty * numeric_price
        variance_mask = (abs(numeric_total - expected_total) > 0.05) & (~is_invalid)
        if variance_mask.any():
            cnt = int(variance_mask.sum())
            warnings.append(f"{cnt} row(s) have total amount variance from quantity * unit_price.")

    # 5. Final quality score calculation
    valid_rows = int((~is_invalid).sum())
    quality_score = round((valid_rows / max(total_rows, 1)) * 100, 1)

    is_valid = (
        len(missing_required) == 0
        and valid_rows > 0
        and quality_score >= MIN_QUALITY_SCORE
    )

    sample_preview = (
        norm_df.head(5)
        .replace({np.nan: None})
        .to_dict(orient="records")
    )

    return ValidationResult(
        is_valid=is_valid,
        total_rows=total_rows,
        valid_rows=valid_rows,
        duplicate_count=duplicate_count,
        return_count=return_count,
        quality_score=quality_score,
        detected_columns=detected_columns,
        schema_detected=schema_name,
        missing_required_columns=missing_required,
        warnings=warnings,
        sample_preview=sample_preview,
    )
