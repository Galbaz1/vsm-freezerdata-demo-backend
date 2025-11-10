# Exploratory Data Analysis & Data Cleaning
## Freezer Telemetry Dataset (135_1570)

This folder contains comprehensive exploratory data analysis (EDA) and data cleaning documentation for the freezer telemetry dataset covering 528 days of operation (Oct 2022 - Apr 2024).

---

## Quick Start

### For Data Scientists / Analysts

**Use this file for analysis:**
```python
import pandas as pd
df = pd.read_parquet('features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet')
```

**Key facts:**
- ✅ 785,398 records at 1-minute intervals
- ✅ All outliers handled (2.24% of data)
- ✅ Validated against physical constraints
- ✅ Ready for ML/statistical modeling
- ✅ ~3.7% missing values (acceptable for IoT)

### For Auditors / Compliance

**Review these documents:**
1. [DATA_CLEANING_LOG.md](DATA_CLEANING_LOG.md) - Complete audit trail
2. `135_1570_cleaned_with_flags.parquet` - Data with outlier flags
3. [cleaning_summary.json](cleaning_summary.json) - Machine-readable metadata

---

## Documentation Files

### 📊 Analysis Reports

| File | Description | Purpose |
|------|-------------|---------|
| [EDA_REPORT.md](EDA_REPORT.md) | Comprehensive exploratory data analysis | Understand dataset characteristics |
| [OUTLIER_ANALYSIS.md](OUTLIER_ANALYSIS.md) | Detailed outlier investigation | Justify cleaning decisions |
| [DATA_CLEANING_LOG.md](DATA_CLEANING_LOG.md) | Complete data cleaning documentation | Audit trail & reproducibility |
| [cleaning_summary.json](cleaning_summary.json) | Machine-readable cleaning metadata | Programmatic access |

### 📈 Visualizations

| File | Description |
|------|-------------|
| [eda_timeseries.png](eda_timeseries.png) | Time series plots of main sensors |
| [eda_distributions.png](eda_distributions.png) | Value distributions (histograms) |
| [eda_correlation.png](eda_correlation.png) | Correlation heatmap |
| [eda_temporal_patterns.png](eda_temporal_patterns.png) | Hourly/daily patterns |
| [eda_boxplots.png](eda_boxplots.png) | Outlier detection via box plots |
| [outlier_analysis.png](outlier_analysis.png) | Detailed outlier visualization |
| [cleaning_before_after.png](cleaning_before_after.png) | Before/after comparison |
| [cleaning_statistics_table.png](cleaning_statistics_table.png) | Statistical comparison table |

---

## Key Findings

### Dataset Overview

```
Records:        785,398
Time Period:    2022-10-20 to 2024-04-01 (528 days)
Frequency:      1-minute intervals
Sensors:        9 (temperature, door, signal, battery)
Data Quality:   Good (after cleaning)
```

### Critical Issues Found & Resolved

| Issue | Severity | Records | Action Taken |
|-------|----------|---------|--------------|
| **Sensor error code (882.6°C)** | 🔴 CRITICAL | 4,126 | Replaced with NaN |
| **Impossible freezer temps (>0°C)** | 🔴 CRITICAL | 4,239 | Capped at 0°C |
| **Sensor readings during shutdown** | 🟡 MODERATE | ~9,000 | Capped to operational ranges |
| **Short communication gaps** | 🟢 MINOR | ~18,715 | Interpolated (≤5 min) |

### Main Temperature Statistics

| Sensor | Original | Cleaned | Improvement |
|--------|----------|---------|-------------|
| **Main Freezer** | -33.84°C ± 4.07°C | -33.27°C ± 5.46°C | ✅ Outliers removed |
| **Secondary Freezer** | -29.00°C ± **68.39°C** | -34.13°C ± **1.15°C** | ✅ **98% std reduction** |
| **Hot Gas Line** | 50.40°C ± 8.16°C | 49.82°C ± 9.05°C | ✅ Valid range |

### Strong Correlations Detected

- Main ↔ Secondary Freezer: **0.960** (redundancy)
- Temperature ↔ Battery: **-0.878** (drain during cooling)
- Door Contact ↔ Temperature: **0.852** (expected)
- Hot Gas ↔ Ambient: **0.754** (normal behavior)

---

## Data Files

### Production Data (Use This)

**File:** `features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet`

**Columns:**
- `sGekoeldeRuimte` - Main freezer temperature (°C)
- `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` - Secondary freezer (°C)
- `sHeetgasLeiding` - Hot gas line temperature (°C)
- `sVloeistofleiding` - Liquid line temperature (°C)
- `sZuigleiding` - Suction line temperature (°C)
- `sOmgeving` - Ambient temperature (°C)
- `sDeurcontact` - Door contact sensor (0/1)
- `sRSSI` - Signal strength (dBm)
- `sBattery` - Battery level (%)

**Quality:**
- ✅ All outliers handled
- ✅ Validated ranges
- ✅ Production-ready
- ✅ 3.71% missing values

### Audit Trail Data

**File:** `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet`

**Additional Columns:**
- `_flag_secondary_error_code` - Marks 882.6°C values
- `_flag_main_temp_high` - Marks positive temps
- `_flag_hot_gas_low` - Marks <20°C readings
- `_flag_liquid_extreme` - Marks liquid line outliers
- `_flag_suction_extreme` - Marks suction line outliers
- `_flag_ambient_extreme` - Marks ambient outliers

**Use for:**
- Auditing cleaning decisions
- Investigating outlier patterns
- Reversing specific operations
- Compliance documentation

### Original Data (Archived)

**File:** `features/telemetry/timeseries_freezerdata/135_1570.parquet`

**Status:** Preserved for reference, do not use for analysis

---

## Cleaning Pipeline Summary

### Steps Performed

1. ✅ **Initial Assessment** - Documented baseline statistics
2. ✅ **Outlier Flagging** - Marked 17,576 outliers (2.24%)
3. ✅ **Error Code Removal** - Replaced 882.6°C with NaN
4. ✅ **Range Capping** - Applied physical constraints
5. ✅ **Gap Interpolation** - Filled short gaps (≤5 min)
6. ✅ **Validation** - Verified all ranges
7. ✅ **Documentation** - Created comprehensive logs

### Impact

**Data Quality:**
- Outliers: 2.24% → 0.00% ✅
- Missing: 6.09% → 3.71% ✅
- Invalid ranges: 6 columns → 0 columns ✅
- Std deviation: 68.39°C → 1.15°C (secondary) ✅

**Modeling Readiness:**
- Linear models: ✅ Ready
- Time series: ✅ Ready
- ML algorithms: ✅ Ready
- Statistical analysis: ✅ Ready

---

## Use Cases

### ✅ Ready For

1. **Time Series Forecasting**
   - ARIMA, Prophet, LSTM models
   - Temperature prediction
   - Anomaly detection

2. **Statistical Analysis**
   - Reliable means, medians, correlations
   - Hypothesis testing
   - Regression analysis

3. **Machine Learning**
   - Classification (normal vs. anomaly)
   - Clustering (operational states)
   - Feature engineering

4. **Operational Monitoring**
   - Dashboard creation
   - Alert systems
   - Performance metrics

5. **Predictive Maintenance**
   - Equipment health scoring
   - Failure prediction
   - Maintenance scheduling

6. **Energy Optimization**
   - Consumption analysis
   - Efficiency improvements
   - Cost reduction

### ⚠️ Considerations

1. **Missing Values:** 3.71% remain after cleaning
   - Mostly from long communication gaps (>5 min)
   - Consider forward-fill or model-specific handling
   - Not in continuous blocks (safe for most models)

2. **Outlier Flags:** Review for your specific use case
   - Some capped values might be legitimate extremes
   - Consider context (e.g., defrost cycles)
   - Flags available in audit file

3. **Time Period:** Oct 2022 - Apr 2024
   - Covers fall, winter, spring (no summer)
   - Seasonal patterns may be incomplete
   - Consider when generalizing

---

## Recommendations

### For Analysis

1. **Load cleaned data:**
   ```python
   df = pd.read_parquet('features/telemetry/timeseries_freezerdata/135_1570_cleaned.parquet')
   ```

2. **Handle remaining missing values:**
   ```python
   # Option 1: Forward fill (time series)
   df = df.fillna(method='ffill')

   # Option 2: Drop (if <5% missing)
   df = df.dropna()

   # Option 3: Model-based imputation
   from sklearn.impute import KNNImputer
   imputer = KNNImputer(n_neighbors=5)
   df_filled = imputer.fit_transform(df)
   ```

3. **Check correlations before modeling:**
   - Main & secondary freezer are highly correlated (0.96)
   - Consider dropping one for multicollinearity

4. **Use domain knowledge:**
   - Freezer should be ≤-20°C for proper operation
   - Door opens cause temporary temperature spikes
   - Battery drain correlates with compressor activity

### For Future Data Collection

1. **Real-time validation:** Reject values outside ranges at source
2. **Error code logging:** Track and explain codes like 882.6
3. **Metadata:** Record maintenance, defrost cycles, shutdowns
4. **Sensor redundancy:** Maintain backup sensors
5. **Communication reliability:** Address Oct-Nov 2022 issues

---

## Reproducibility

### Full cleaning pipeline code available in:
- [DATA_CLEANING_LOG.md](DATA_CLEANING_LOG.md) (Section 9)

### Requirements:
```
pandas >= 2.0.0
numpy >= 1.24.0
pyarrow >= 12.0.0
matplotlib >= 3.7.0 (for visualizations)
```

### Validation:
All cleaned data passed validation against physical constraints:
```python
# Validation ranges
expected_ranges = {
    'sGekoeldeRuimte': (-50, 0),
    'p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive': (-50, 0),
    'sHeetgasLeiding': (20, 80),
    'sVloeistofleiding': (20, 50),
    'sZuigleiding': (20, 40),
    'sOmgeving': (-10, 50),
    'sDeurcontact': (0, 1),
    'sRSSI': (-120, 0),
    'sBattery': (0, 100)
}
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-11-10 | 1.0 | Initial EDA and data cleaning completed |

---

## Contact & Support

**Questions about the analysis?**
- Review [EDA_REPORT.md](EDA_REPORT.md) for methodology
- Check [OUTLIER_ANALYSIS.md](OUTLIER_ANALYSIS.md) for justification
- Read [DATA_CLEANING_LOG.md](DATA_CLEANING_LOG.md) for details

**Questions about data quality?**
- Examine flag columns in audit file
- Review before/after visualizations
- Check cleaning_summary.json

**Need to reverse cleaning?**
- Original data preserved: `135_1570.parquet`
- Flags identify all modified records
- Code provided for reproducibility

---

## Quick Reference Card

| Need | File/Section |
|------|--------------|
| 🎯 **Production data** | `135_1570_cleaned.parquet` |
| 📊 **What was cleaned** | [DATA_CLEANING_LOG.md](DATA_CLEANING_LOG.md) |
| 🔍 **Why it was cleaned** | [OUTLIER_ANALYSIS.md](OUTLIER_ANALYSIS.md) |
| 📈 **Data characteristics** | [EDA_REPORT.md](EDA_REPORT.md) |
| 🔄 **Reproduce cleaning** | DATA_CLEANING_LOG.md Section 9 |
| 🚩 **Audit trail** | `135_1570_cleaned_with_flags.parquet` |
| 📉 **Before/after viz** | cleaning_before_after.png |
| ✅ **Validation status** | All checks passed ✓ |

---

**Status:** ✅ Analysis Complete | ✅ Data Cleaned | ✅ Validated | ✅ Production-Ready

**Last Updated:** 2024-11-10
