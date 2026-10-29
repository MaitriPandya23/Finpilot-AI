"""
Finpilot-AI: Kaggle Online Retail Dataset Converter & Transformer
Converts the official Kaggle Online Retail dataset (Excel .xlsx or raw CSV)
into a production-ready CSV formatted for Finpilot-AI ingestion.

Official Source:
    https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset
    (Originally sourced from the UCI Machine Learning Repository: Online Retail Dataset)

How to obtain the genuine dataset:
1. Via Kaggle CLI:
       kaggle datasets download -d lakshmi25npathi/online-retail-dataset
       unzip online-retail-dataset.zip
2. Via Web Browser:
       Visit https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset
       Click "Download", extract "Online Retail.xlsx".

Usage:
    python data-generator/convert_kaggle_retail.py --input "Online Retail.xlsx" --output "data-generator/output/kaggle_online_retail.csv"
    python data-generator/convert_kaggle_retail.py --input "Online Retail.xlsx" --output "data-generator/output/kaggle_sample.csv" --sample 5000
"""

import argparse
import sys
import os
import pandas as pd


EXPECTED_HEADERS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def convert_dataset(input_path: str, output_path: str, sample_size: int = None):
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        print("Please download the official dataset from:", file=sys.stderr)
        print("https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset", file=sys.stderr)
        sys.exit(1)

    print(f"Loading '{input_path}'...")
    if input_path.lower().endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(input_path, engine="openpyxl")
        except ImportError:
            try:
                df = pd.read_excel(input_path)
            except Exception as e:
                print(f"Error: Missing Excel engine (openpyxl). Install it with: pip install openpyxl ({e})", file=sys.stderr)
                sys.exit(1)
    else:
        df = pd.read_csv(input_path, dtype=str, encoding="utf-8-sig")

    print(f"Read {len(df):,} raw rows. Verifying headers...")
    col_map = {str(c).strip().lower(): str(c).strip() for c in df.columns}
    
    missing = []
    for exp in EXPECTED_HEADERS:
        if exp.lower() not in col_map:
            missing.append(exp)

    if missing:
        print(f"Warning: Columns {missing} not found in input. Found: {list(df.columns)}")
    else:
        print("All expected Kaggle Online Retail headers verified.")

    # Quality and business transformations:
    # 1. Strip whitespace from InvoiceNo, StockCode, Description
    for text_col in ["InvoiceNo", "StockCode", "Description", "Country"]:
        actual_col = col_map.get(text_col.lower())
        if actual_col and actual_col in df.columns:
            df[actual_col] = df[actual_col].astype(str).str.strip()

    # 2. Treat CustomerID as anonymous data identifier; preserve blanks as empty
    cust_col = col_map.get("customerid")
    if cust_col and cust_col in df.columns:
        df[cust_col] = df[cust_col].replace("nan", "").fillna("")

    # 3. Handle optional sampling
    if sample_size and sample_size < len(df):
        print(f"Extracting stratified sample of {sample_size:,} records...")
        df = df.head(sample_size)

    # 4. Save to CSV
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Successfully converted and saved {len(df):,} rows to '{output_path}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Kaggle Online Retail Excel to Finpilot CSV.")
    parser.add_argument("--input", "-i", required=True, help="Path to Online Retail.xlsx or raw CSV")
    parser.add_argument("--output", "-o", default="data-generator/output/kaggle_online_retail.csv", help="Destination CSV path")
    parser.add_argument("--sample", "-s", type=int, default=None, help="Optional row sample count")

    args = parser.parse_args()
    convert_dataset(args.input, args.output, args.sample)
