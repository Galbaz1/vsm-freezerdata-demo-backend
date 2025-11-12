#!/usr/bin/env python3
"""Check actual telemetry date ranges"""
import pandas as pd
from pathlib import Path

parquet_path = Path("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
df = pd.read_parquet(parquet_path)

print(f"Min timestamp: {df.index.min()}")
print(f"Max timestamp: {df.index.max()}")
print(f"Total rows: {len(df):,}")
print(f"Duration: {(df.index.max() - df.index.min()).days} days")

