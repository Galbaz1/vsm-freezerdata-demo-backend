# Telemetry Files Overview

## Summary

This document catalogs all telemetry/timeseries data files found in the repository.

## Parquet Files

| Filename | Path | Rows | Columns | Description |
|----------|------|------|---------|-------------|
| `135_1570_cleaned.parquet` | `features/telemetry/timeseries_freezerdata/` | 785,398 | 9 | Basic cleaned telemetry data without flags |
| `135_1570_cleaned_with_flags.parquet` | `features/telemetry/timeseries_freezerdata/` | 785,398 | 15 | Cleaned telemetry data with 6 error/anomaly flags added |

## CSV Files

| Filename | Path | Description |
|----------|------|-------------|
| `135_1570_sample.csv` | `features/telemetry/timeseries_freezerdata/` | Sample CSV version of telemetry data (for quick inspection) |

## File Naming Convention

The naming pattern `135_1570_*` suggests:
- **135**: Likely an asset ID or location identifier
- **1570**: Possibly a sub-system or sensor array identifier
- **cleaned**: Basic data cleaning applied
- **with_flags**: Additional anomaly detection flags included

## Time Range

**Coverage**: July 21, 2024 to January 1, 2026
- **Total duration**: ~528 days (approximately 1.4 years)
- **Sampling rate**: 1 minute intervals
- **Total records**: 785,398 measurements

## Data Quality

- **Missing data**: ~3.7% average across most sensor columns
- **Completeness**: 96.3% overall
- All flag columns have 0% missing values (boolean flags are always populated)

## Asset Information

Based on the data structure:
- **Single asset**: All data appears to be from one freezer/cooling installation (ID: 135_1570)
- **Index**: Data is indexed by timestamp
- No separate asset_id column is needed as this is a single-asset dataset
