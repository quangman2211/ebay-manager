#!/usr/bin/env python3
"""
Debug CSV column parsing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.csv_service import CSVProcessor
from app.schemas import DataType

if __name__ == "__main__":
    # Read the order CSV
    with open('../Docs/DATA/ebay-order.csv', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Original CSV content (first 500 chars):")
    print(repr(content[:500]))
    print("\n" + "="*50 + "\n")
    
    # Process with our CSV processor
    records, errors = CSVProcessor.process_csv_file(content, DataType.ORDER)
    
    print(f"Errors: {errors}")
    print(f"Records found: {len(records)}")
    
    if records:
        print(f"First record keys: {list(records[0].keys())[:10]}")
        print(f"First record: {dict(list(records[0].items())[:5])}")
    
    # Also try the raw pandas parsing to debug
    import pandas as pd
    from io import StringIO
    
    print("\n" + "="*50 + "\n")
    print("Raw pandas parsing:")
    
    df = pd.read_csv(StringIO(content))
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()[:10]}")
    
    # Try skipping empty rows
    df_clean = df.dropna(how='all')
    print(f"After removing empty rows - Shape: {df_clean.shape}")
    if len(df_clean) > 0:
        print(f"First row: {df_clean.iloc[0].tolist()[:10]}")