"""
Script to analyze telemetry parquet files and generate schema documentation
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

def analyze_parquet_file(filepath):
    """Analyze a single parquet file and return schema info"""
    df = pd.read_parquet(filepath)

    results = {
        "filepath": str(filepath),
        "filename": Path(filepath).name,
        "row_count": len(df),
        "columns": {}
    }

    for col in df.columns:
        col_info = {
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "missing_percent": round(float(df[col].isna().sum() / len(df) * 100), 2)
        }

        # For numeric columns, add stats
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["min"] = float(df[col].min()) if not df[col].isna().all() else None
            col_info["max"] = float(df[col].max()) if not df[col].isna().all() else None
            col_info["mean"] = float(df[col].mean()) if not df[col].isna().all() else None
            col_info["median"] = float(df[col].median()) if not df[col].isna().all() else None
            col_info["std"] = float(df[col].std()) if not df[col].isna().all() else None

        # For categorical/object/bool, add value counts
        if df[col].dtype in ['object', 'bool', 'category'] or df[col].nunique() < 20:
            col_info["unique_values"] = int(df[col].nunique())
            value_counts = df[col].value_counts().head(10).to_dict()
            # Convert numpy types to Python types for JSON serialization
            col_info["value_counts"] = {str(k): int(v) for k, v in value_counts.items()}

        results["columns"][col] = col_info

    # Time range analysis if timestamp column exists
    timestamp_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if timestamp_cols:
        results["timestamp_columns"] = timestamp_cols
        for ts_col in timestamp_cols:
            if pd.api.types.is_datetime64_any_dtype(df[ts_col]):
                results[f"{ts_col}_range"] = {
                    "min": str(df[ts_col].min()),
                    "max": str(df[ts_col].max()),
                    "span_days": (df[ts_col].max() - df[ts_col].min()).days
                }

    return results, df

def main():
    # Define file paths
    base_path = Path(__file__).parent.parent / "features" / "telemetry" / "timeseries_freezerdata"

    files_to_analyze = [
        base_path / "135_1570_cleaned.parquet",
        base_path / "135_1570_cleaned_with_flags.parquet"
    ]

    all_results = {}

    for filepath in files_to_analyze:
        if filepath.exists():
            print(f"\nAnalyzing {filepath.name}...")
            results, df = analyze_parquet_file(filepath)
            all_results[filepath.name] = results

            # Print summary
            print(f"  Rows: {results['row_count']}")
            print(f"  Columns: {len(results['columns'])}")
            if 'timestamp_columns' in results:
                print(f"  Timestamp columns: {results['timestamp_columns']}")
        else:
            print(f"File not found: {filepath}")

    # Save results to JSON
    output_path = Path(__file__).parent.parent / "docs" / "data" / "telemetry_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to {output_path}")

    # Also load and preview the cleaned_with_flags version
    flags_file = base_path / "135_1570_cleaned_with_flags.parquet"
    if flags_file.exists():
        df_flags = pd.read_parquet(flags_file)
        print("\n" + "="*80)
        print("DETAILED ANALYSIS: cleaned_with_flags")
        print("="*80)
        print(f"\nDataFrame shape: {df_flags.shape}")
        print(f"\nColumn names:")
        for col in df_flags.columns:
            print(f"  - {col}")

        print(f"\nFirst few rows:")
        print(df_flags.head(10))

        print(f"\nData types:")
        print(df_flags.dtypes)

        print(f"\nBasic statistics:")
        print(df_flags.describe())

        # Flag analysis
        flag_cols = [col for col in df_flags.columns if '_flag_' in col.lower()]
        if flag_cols:
            print(f"\n" + "="*80)
            print(f"FLAG COLUMNS ANALYSIS ({len(flag_cols)} flags found)")
            print("="*80)
            for flag_col in flag_cols:
                print(f"\n{flag_col}:")
                print(f"  Type: {df_flags[flag_col].dtype}")
                print(f"  Value counts:")
                print(df_flags[flag_col].value_counts())
                if df_flags[flag_col].dtype == bool or df_flags[flag_col].nunique() == 2:
                    true_pct = (df_flags[flag_col].sum() / len(df_flags) * 100)
                    print(f"  True percentage: {true_pct:.2f}%")

if __name__ == "__main__":
    main()
