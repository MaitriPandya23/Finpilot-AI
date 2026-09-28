"""
Finpilot-AI CSV Data Ingestion Validator
Performs robust file-level and row-level data quality validation for business CSV uploads.
"""

from io import BytesIO, StringIO
import os
from typing import Union, IO, List
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from pydantic import BaseModel

MIN_QUALITY_SCORE = 50.0

# Required columns without which relational modeling, core financials, and ML fail
REQUIRED_COLUMNS: List[str] = [
    "transaction_id",
    "date",
    "product",
    "quantity",
    "unit_price",
    "total",
]

# Optional business columns that provide enriched analytics when present
OPTIONAL_COLUMNS: List[str] = [
    "cost_price",
    "category",
    "shop_id",
    "customer_id",
    "payment_mode",
]


class ValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    duplicate_count: int
    quality_score: float  # 0.0-100.0, rounded to 1 decimal
    detected_columns: list[str]
    missing_required_columns: list[str]
    warnings: list[str]
    sample_preview: list[dict]  # first 5 rows


def validate_csv(source: Union[str, bytes, IO]) -> ValidationResult:
    """
    Validates a CSV file or buffer against Finpilot-AI data quality standards.

    Guards against:
    - Empty files and unparseable CSV content
    - Missing required structural columns
    - Row-level missing required values
    - Duplicate transaction IDs
    - Invalid and future dates
    - Non-positive quantities and negative prices/totals
    - Computes a 0.0-100.0 Data Quality Score
    - Emits human-readable warnings for non-technical users
    """
    warnings: List[str] = []

    # 1. File-level guards: parse source safely without raising exceptions
    try:
        if isinstance(source, bytes):
            if len(source.strip()) == 0:
                return ValidationResult(
                    is_valid=False,
                    total_rows=0,
                    valid_rows=0,
                    duplicate_count=0,
                    quality_score=0.0,
                    detected_columns=[],
                    missing_required_columns=REQUIRED_COLUMNS.copy(),
                    warnings=["Uploaded file is empty (0 bytes)."],
                    sample_preview=[],
                )
            df = pd.read_csv(BytesIO(source), dtype=str)
        elif isinstance(source, str):
            if os.path.isfile(source):
                if os.path.getsize(source) == 0:
                    return ValidationResult(
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        duplicate_count=0,
                        quality_score=0.0,
                        detected_columns=[],
                        missing_required_columns=REQUIRED_COLUMNS.copy(),
                        warnings=["Uploaded file is empty (0 bytes)."],
                        sample_preview=[],
                    )
                df = pd.read_csv(source, dtype=str)
            else:
                if not source.strip():
                    return ValidationResult(
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        duplicate_count=0,
                        quality_score=0.0,
                        detected_columns=[],
                        missing_required_columns=REQUIRED_COLUMNS.copy(),
                        warnings=["Uploaded CSV content is empty."],
                        sample_preview=[],
                    )
                df = pd.read_csv(StringIO(source), dtype=str)
        else:
            # IO or file-like object
            if hasattr(source, "seek") and hasattr(source, "tell"):
                pos = source.tell()
                peek = source.read(1)
                source.seek(pos)
                if not peek:
                    return ValidationResult(
                        is_valid=False,
                        total_rows=0,
                        valid_rows=0,
                        duplicate_count=0,
                        quality_score=0.0,
                        detected_columns=[],
                        missing_required_columns=REQUIRED_COLUMNS.copy(),
                        warnings=["Uploaded file stream is empty."],
                        sample_preview=[],
                    )
            df = pd.read_csv(source, dtype=str)

    except pd.errors.EmptyDataError:
        return ValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            duplicate_count=0,
            quality_score=0.0,
            detected_columns=[],
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
            quality_score=0.0,
            detected_columns=[],
            missing_required_columns=REQUIRED_COLUMNS.copy(),
            warnings=[f"Unable to read CSV file: {str(e)}"],
            sample_preview=[],
        )

    # Clean header names
    df.columns = [str(col).strip() for col in df.columns]
    detected_columns = list(df.columns)

    # 2. Check for empty rows
    total_rows = len(df)
    missing_required = [col for col in REQUIRED_COLUMNS if col not in detected_columns]

    if total_rows == 0:
        if missing_required:
            warnings.append(f"Missing required column(s): {', '.join(missing_required)}.")
        warnings.append("CSV file contains column headers but no transaction data rows.")
        return ValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            duplicate_count=0,
            quality_score=0.0,
            detected_columns=detected_columns,
            missing_required_columns=missing_required,
            warnings=warnings,
            sample_preview=[],
        )

    # 3. Column set validations
    if missing_required:
        warnings.append(f"Missing required column(s): {', '.join(missing_required)}.")

    if "cost_price" not in detected_columns:
        warnings.append(
            "Optional column 'cost_price' is missing; profit margin and cost analytics will be unavailable."
        )

    known_columns = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
    extra_columns = [col for col in detected_columns if col not in known_columns]
    if extra_columns:
        warnings.append(
            f"Unexpected extra column(s) detected: {', '.join(extra_columns)} (will be safely ignored)."
        )

    # Track invalid rows across all checks
    is_invalid = pd.Series(False, index=df.index)

    # 4. Row-level check: Null/empty in required fields
    present_required = [col for col in REQUIRED_COLUMNS if col in detected_columns]
    for col in present_required:
        null_mask = (
            df[col].isna()
            | (df[col].astype(str).str.strip() == "")
            | (df[col].astype(str).str.strip().str.lower().isin(["nan", "null", "none"]))
        )
        if null_mask.any():
            cnt = int(null_mask.sum())
            is_invalid |= null_mask
            warnings.append(f"{cnt} row(s) have missing or empty '{col}'.")

    # 5. Row-level check: Duplicate transaction_id
    duplicate_count = 0
    if "transaction_id" in detected_columns:
        dup_mask = df.duplicated(subset=["transaction_id"], keep="first")
        if dup_mask.any():
            duplicate_count = int(dup_mask.sum())
            is_invalid |= dup_mask
            warnings.append(
                f"{duplicate_count} duplicate transaction ID(s) detected and excluded."
            )

    # 6. Row-level check: Date unparseable and future dates
    if "date" in detected_columns:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce", format="mixed")
        unparseable_mask = (
            parsed_dates.isna()
            & df["date"].notna()
            & (df["date"].astype(str).str.strip() != "")
        )
        if unparseable_mask.any():
            cnt = int(unparseable_mask.sum())
            is_invalid |= unparseable_mask
            warnings.append(f"{cnt} row(s) have an unreadable date format.")

        # Future date detection (UTC with 1-day allowance for local timezone variances)
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

    # 7. Row-level check: Quantity <= 0 or non-numeric
    if "quantity" in detected_columns:
        numeric_qty = pd.to_numeric(df["quantity"], errors="coerce")
        has_qty_value = df["quantity"].notna() & (df["quantity"].astype(str).str.strip() != "")
        bad_qty_mask = has_qty_value & (numeric_qty.isna() | (numeric_qty <= 0))
        if bad_qty_mask.any():
            cnt = int(bad_qty_mask.sum())
            is_invalid |= bad_qty_mask
            warnings.append(
                f"{cnt} row(s) have invalid quantity (must be a number greater than 0)."
            )

    # 8. Row-level check: Unit price < 0 or non-numeric
    if "unit_price" in detected_columns:
        numeric_price = pd.to_numeric(df["unit_price"], errors="coerce")
        has_price_value = df["unit_price"].notna() & (df["unit_price"].astype(str).str.strip() != "")
        bad_price_mask = has_price_value & (numeric_price.isna() | (numeric_price < 0))
        if bad_price_mask.any():
            cnt = int(bad_price_mask.sum())
            is_invalid |= bad_price_mask
            warnings.append(
                f"{cnt} row(s) have invalid unit price (must be a non-negative number)."
            )

    # 9. Row-level check: Negative total or non-numeric total
    if "total" in detected_columns:
        numeric_total = pd.to_numeric(df["total"], errors="coerce")
        has_total_value = df["total"].notna() & (df["total"].astype(str).str.strip() != "")
        bad_total_mask = has_total_value & (numeric_total.isna() | (numeric_total < 0))
        if bad_total_mask.any():
            cnt = int(bad_total_mask.sum())
            is_invalid |= bad_total_mask
            warnings.append(f"{cnt} row(s) have negative or invalid total amount.")

    # 10. Check total variance vs quantity * unit_price (WARNING only, not invalid)
    if all(col in detected_columns for col in ["quantity", "unit_price", "total"]):
        numeric_qty = pd.to_numeric(df["quantity"], errors="coerce")
        numeric_price = pd.to_numeric(df["unit_price"], errors="coerce")
        numeric_total = pd.to_numeric(df["total"], errors="coerce")
        valid_math = numeric_qty.notna() & numeric_price.notna() & numeric_total.notna()
        if valid_math.any():
            calc_diff = (
                numeric_qty[valid_math] * numeric_price[valid_math]
                - numeric_total[valid_math]
            ).abs()
            mismatch_mask = calc_diff > 0.05
            if mismatch_mask.any():
                cnt = int(mismatch_mask.sum())
                warnings.append(
                    f"{cnt} row(s) have total amount variance with quantity × unit price (tolerance 0.05; will be recalculated in ETL)."
                )

    # 11. Final valid row count & quality score calculation
    valid_rows = int((~is_invalid).sum())
    quality_score = round((valid_rows / total_rows) * 100, 1)

    is_valid = (
        len(missing_required) == 0
        and valid_rows > 0
        and quality_score >= MIN_QUALITY_SCORE
    )

    # 12. First 5 rows preview (handling NaN to None conversion)
    sample_preview = (
        df.head(5)
        .replace({np.nan: None})
        .to_dict(orient="records")
    )

    return ValidationResult(
        is_valid=is_valid,
        total_rows=total_rows,
        valid_rows=valid_rows,
        duplicate_count=duplicate_count,
        quality_score=quality_score,
        detected_columns=detected_columns,
        missing_required_columns=missing_required,
        warnings=warnings,
        sample_preview=sample_preview,
    )
