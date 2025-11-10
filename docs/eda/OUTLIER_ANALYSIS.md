# Critical Outlier Analysis Report
## Freezer Telemetry Dataset

---

## Executive Summary

**YES - This dataset has critical outliers that ABSOLUTELY require handling before any modeling or analysis.**

### Key Findings

| Issue | Records Affected | Severity | Action Required |
|-------|------------------|----------|-----------------|
| **Secondary freezer error code (882.6°C)** | 4,126 (0.54%) | 🔴 CRITICAL | MUST remove/replace with NaN |
| **Main freezer impossible temps (>10°C)** | 4,202 (0.54%) | 🔴 CRITICAL | MUST cap or remove |
| **Co-occurring errors** | 4,111 (0.52%) | 🔴 CRITICAL | Indicates communication/power issues |
| **Minor outliers (lines/ambient)** | <50 records | 🟡 LOW | Optional - investigate or cap |

---

## 1. Critical Finding: Sensor Error Code

### Secondary Freezer Sensor: 882.6°C

**What we found:**
- Exactly **4,126 readings** show temperature of **882.6°C**
- This value appears consistently (100% of errors are this exact value)
- Physically impossible for a freezer sensor
- Occurs in clusters over 30 days (primarily in Oct-Nov 2022)

**Conclusion:** This is a **sensor error code** or communication failure indicator, NOT a real temperature reading.

**Evidence:**
```
Value: 882.6°C appears 4,126 times
Next highest value: Normal freezer temps around -34°C
Pattern: Appears in continuous blocks during specific time periods
```

### Main Freezer Sensor: Temperatures >10°C

**What we found:**
- 4,202 readings show temperatures above 10°C
- Maximum value: 56.4°C
- Range of outliers: 10°C to 56°C
- **4,111 of these (97.8%) occur simultaneously with the 882.6°C error**

**Conclusion:** These are NOT real temperature excursions but **communication/sensor errors** that affect both sensors simultaneously.

**Evidence:**
```
Co-occurrence rate: 97.8% of main freezer errors happen when secondary shows 882.6°C
Typical freezer operation: -33.84°C ± 4.07°C
Physical impossibility: Freezer cannot reach 56°C without complete system failure
```

---

## 2. Temporal Pattern Analysis

### Error Occurrence Timeline

**Time span:** October 20, 2022 - March 26, 2024
**Error events:** 18 separate incidents
**Affected days:** 30 days total

**Top 5 days with errors:**
| Date | Error Count |
|------|-------------|
| 2022-10-31 | 540 records |
| 2022-10-20 | 309 records |
| 2022-10-24 | 290 records |
| 2022-10-29 | 290 records |
| 2022-10-25 | 289 records |

**Pattern:** Errors occur in continuous blocks (median gap: 5 minutes), suggesting:
- Temporary communication failures
- Power interruptions
- Sensor reset events
- Data transmission issues

---

## 3. Impact on Analysis if NOT Handled

### Statistical Impact

| Metric | With Outliers | Without Outliers | Impact |
|--------|---------------|------------------|---------|
| **Secondary Freezer Mean** | -29.00°C | ~-34°C (estimated) | **Severely skewed** |
| **Correlation with Battery** | -0.867 | ~-0.75 (estimated) | **Artificially inflated** |
| **Standard Deviation** | 68.39°C | ~4°C (estimated) | **17x overestimated** |

### Machine Learning Impact

If outliers are NOT removed:
- ❌ **Linear models** will be completely unreliable
- ❌ **Neural networks** will learn incorrect patterns
- ❌ **Time series forecasting** will be impossible
- ❌ **Anomaly detection** will trigger constant false alarms
- ❌ **Clustering** will create meaningless groups
- ❌ **Feature importance** will be dominated by outliers

### Business Impact

- ❌ Incorrect temperature trends
- ❌ False equipment failure alerts
- ❌ Unreliable energy consumption analysis
- ❌ Invalid maintenance predictions
- ❌ Compliance reporting errors

---

## 4. Recommended Data Cleaning Strategy

### Step 1: Remove Sensor Error Codes (CRITICAL)

```python
# Replace 882.6°C with NaN (clear error code)
df.loc[df['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'] == 882.6,
       'p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'] = np.nan
```

**Rationale:** This is clearly a sensor error code, not a measurement.

### Step 2: Handle Co-Occurring Main Freezer Errors (CRITICAL)

```python
# Option A: Set co-occurring errors to NaN (conservative)
error_mask = df['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'].isna()
df.loc[error_mask & (df['sGekoeldeRuimte'] > 0), 'sGekoeldeRuimte'] = np.nan

# Option B: Cap at physical maximum (0°C for freezer)
df['sGekoeldeRuimte'] = df['sGekoeldeRuimte'].clip(upper=0)
```

**Rationale:** 97.8% of main freezer outliers occur with the 882.6°C error, indicating communication failure.

### Step 3: Handle Remaining Outliers (OPTIONAL)

```python
# Cap extreme values for refrigeration lines
df['sHeetgasLeiding'] = df['sHeetgasLeiding'].clip(lower=15, upper=80)
df['sVloeistofleiding'] = df['sVloeistofleiding'].clip(lower=15, upper=50)
df['sZuigleiding'] = df['sZuigleiding'].clip(lower=15, upper=45)
df['sOmgeving'] = df['sOmgeving'].clip(lower=-10, upper=50)
```

**Rationale:** These are rare (<50 records) and might represent real defrost cycles or environmental extremes.

### Step 4: Handle Missing Values (OPTIONAL)

```python
# Forward fill short gaps (<5 minutes) for continuity
df = df.fillna(method='ffill', limit=5)

# Or interpolate for smooth transitions
df = df.interpolate(method='time', limit=5)
```

**Rationale:** IoT sensors often have brief communication gaps that can be safely interpolated.

---

## 5. Validation After Cleaning

After applying the cleaning steps, verify:

```python
# Check ranges
print(df.describe())

# Verify no extreme outliers remain
assert df['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'].max() < 50
assert df['sGekoeldeRuimte'].max() <= 0

# Check missing value percentage
print(df.isnull().sum() / len(df) * 100)
```

**Expected results:**
- Secondary freezer range: -40°C to 0°C
- Main freezer range: -40°C to 0°C
- Missing values: ~6-7% (was ~6%, added ~1% from cleaning)
- Standard deviation: ~4-5°C (was 68°C for secondary)

---

## 6. Documentation Requirements

When cleaning data, document:

1. **What was removed:** Exact criteria and row counts
2. **Why it was removed:** Justification with evidence
3. **Impact assessment:** Before/after statistics
4. **Reversibility:** Keep original data with cleaning flags

Example documentation:

```python
# Add flag column before cleaning
df['is_outlier_882'] = df['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'] == 882.6
df['is_outlier_main'] = df['sGekoeldeRuimte'] > 0

# Document in metadata
cleaning_log = {
    'date': '2024-11-10',
    'actions': [
        'Removed 4,126 records with 882.6°C error code',
        'Capped 4,202 main freezer readings at 0°C',
        'Reason: Sensor communication error confirmed by co-occurrence analysis'
    ],
    'records_affected': 4,239,
    'percent_affected': 0.54
}
```

---

## 7. Final Recommendation

### ✅ MUST DO (Critical for Data Quality)

1. **Remove/replace 882.6°C readings** → Replace with NaN
2. **Handle co-occurring main freezer errors** → Cap at 0°C or set to NaN
3. **Document all changes** → Maintain audit trail
4. **Validate results** → Verify statistical sanity

### ⚠️ SHOULD DO (Best Practice)

5. **Cap minor outliers** → Prevent extreme values in lines/ambient
6. **Interpolate short gaps** → Improve time series continuity
7. **Create cleaned dataset** → Save as separate file

### 📊 Impact Summary

**Before cleaning:**
- Unusable for statistical analysis
- Will cause model failures
- Cannot trust any results

**After cleaning:**
- Reliable statistical metrics
- Ready for ML modeling
- Trustworthy insights

---

## Appendix: Code Examples

### Complete Cleaning Pipeline

```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_parquet('135_1570.parquet')

# Convert to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Add flags for tracking
df['outlier_flag_secondary'] = df['p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'] == 882.6
df['outlier_flag_main'] = df['sGekoeldeRuimte'] > 0

# STEP 1: Remove sensor error code
df.loc[df['outlier_flag_secondary'],
       'p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive'] = np.nan

# STEP 2: Cap main freezer at physical maximum
df['sGekoeldeRuimte'] = df['sGekoeldeRuimte'].clip(upper=0)

# STEP 3: Cap other sensors (optional)
df['sHeetgasLeiding'] = df['sHeetgasLeiding'].clip(lower=15, upper=80)
df['sVloeistofleiding'] = df['sVloeistofleiding'].clip(lower=15, upper=50)
df['sZuigleiding'] = df['sZuigleiding'].clip(lower=15, upper=45)
df['sOmgeving'] = df['sOmgeving'].clip(lower=-10, upper=50)

# STEP 4: Interpolate short gaps (optional)
df = df.interpolate(method='time', limit=5)

# STEP 5: Validate
print("Validation Results:")
print(df.describe())
print("\nOutliers removed:")
print(f"Secondary: {df['outlier_flag_secondary'].sum()}")
print(f"Main: {df['outlier_flag_main'].sum()}")

# STEP 6: Save cleaned data
df.to_parquet('135_1570_cleaned.parquet')
```

---

**Report Generated:** 2024-11-10
**Analysis Period:** 2022-10-20 to 2024-04-01
**Total Records:** 785,398
**Records Requiring Cleaning:** 4,239 (0.54%)
