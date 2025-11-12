# Telemetry Schema Documentation

## Overview

This document provides a detailed schema analysis of the telemetry data from the freezer cooling installation (asset 135_1570).

**Primary file analyzed**: `135_1570_cleaned_with_flags.parquet` (785,398 rows × 15 columns)

---

## Index Column

### `timestamp` (DatetimeIndex)

- **Type**: datetime64[ns]
- **Range**: 2024-07-21 14:03:00 to 2026-01-01 00:00:00
- **Duration**: ~528 days (1.4 years)
- **Sampling interval**: 1 minute
- **Description**: Timestamp for each measurement, serving as the DataFrame index

---

## Sensor Columns

### 1. `sGekoeldeRuimte` (Cooled Room Temperature)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Temperature in the cooled/frozen room (the product space)
- **Statistics**:
  - Min: -37.5°C
  - Max: 0.0°C
  - Mean: -33.27°C
  - Median: -34.2°C
  - Std dev: 5.46°C
  - Missing: 3.71%
- **Typical range**: -37.5°C to -30°C (normal freezer operation)
- **Anomaly indicators**: Values approaching 0°C indicate serious temperature issues

### 2. `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` (Secondary Temperature Sensor)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Secondary/backup temperature sensor for the cooled room
- **Statistics**:
  - Min: -37.5°C
  - Max: 0.0°C
  - Mean: -34.13°C
  - Median: -34.2°C
  - Std dev: 1.08°C (notably lower than primary sensor)
  - Missing: 6.14%
- **Notes**:
  - Lower standard deviation suggests this may be a more stable sensor or located in a less turbulent zone
  - The naming pattern suggests it's from a standardized sensor protocol
  - Higher missing rate (6.14% vs 3.71%) suggests possible redundancy or intermittent use

### 3. `sHeetgasLeiding` (Hot Gas Line Temperature)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Temperature in the hot gas discharge line from the compressor
- **Statistics**:
  - Min: 20.0°C
  - Max: 77.5°C
  - Mean: 49.82°C
  - Median: 52.8°C
  - Std dev: 9.05°C
  - Missing: 3.72%
- **Typical range**: 45-65°C (normal compressor operation)
- **Significance**:
  - Indicates compressor activity and health
  - Very low values (<30°C) suggest compressor not running or major issues
  - Very high values (>70°C) suggest overheating or high load conditions

### 4. `sVloeistofleiding` (Liquid Line Temperature)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Temperature in the liquid refrigerant line (after condenser, before expansion valve)
- **Statistics**:
  - Min: 20.0°C
  - Max: 50.0°C
  - Mean: 33.67°C
  - Median: 34.2°C
  - Std dev: 2.52°C (very stable)
  - Missing: 3.71%
- **Typical range**: 30-40°C
- **Significance**:
  - Should be close to ambient or slightly warmer
  - High stability (low std dev) is expected in normal operation

### 5. `sZuigleiding` (Suction Line Temperature)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Temperature in the suction line (returning from evaporator to compressor)
- **Statistics**:
  - Min: 20.0°C
  - Max: 40.0°C
  - Mean: 31.10°C
  - Median: 31.5°C
  - Std dev: 2.60°C
  - Missing: 3.71%
- **Typical range**: 28-35°C
- **Significance**:
  - Should be cool but above freezing
  - Indicates evaporator performance and superheat

### 6. `sOmgeving` (Ambient Temperature)

- **Type**: float64
- **Unit**: Degrees Celsius (°C)
- **Physical meaning**: Ambient/environmental temperature around the installation
- **Statistics**:
  - Min: -10.0°C
  - Max: 50.0°C
  - Mean: 29.71°C
  - Median: 29.4°C
  - Std dev: 3.58°C
  - Missing: 3.72%
- **Typical range**: 15-35°C (indoor installation) or -10-40°C (outdoor)
- **Significance**:
  - Affects cooling capacity and efficiency
  - High ambient temps increase load on the system

---

## Status/Connectivity Columns

### 7. `sDeurcontact` (Door Contact)

- **Type**: float64 (treated as boolean: 0.0=closed, 1.0=open)
- **Unit**: Dimensionless (0 or 1)
- **Physical meaning**: Door open/closed status sensor
- **Statistics**:
  - Min: 0.0
  - Max: 1.0
  - Mean: 0.0265 (door open ~2.65% of the time)
  - Unique values: 13 (mostly 0.0 and 1.0, some noise values)
  - Value distribution:
    - Closed (0.0): 736,143 measurements (97.4%)
    - Open (1.0): 20,063 measurements (2.6%)
    - Other values: 10 measurements (noise/transitions)
  - Missing: 3.71%
- **Significance**:
  - Prolonged door-open periods increase temperature
  - Can indicate operational issues or user behavior patterns

### 8. `sRSSI` (Signal Strength)

- **Type**: float64
- **Unit**: dBm (decibels relative to one milliwatt)
- **Physical meaning**: Wireless signal strength indicator for sensor communication
- **Statistics**:
  - Min: -115.0 dBm
  - Max: 0.0 dBm
  - Mean: -80.67 dBm
  - Median: -82.0 dBm
  - Std dev: 5.10 dBm
  - Missing: 3.79%
- **Signal quality interpretation**:
  - Excellent: -30 to -67 dBm
  - Good: -68 to -79 dBm
  - Fair: -80 to -89 dBm (mean is in this range)
  - Poor: -90 to -115 dBm
- **Significance**: Low RSSI may indicate communication reliability issues

### 9. `sBattery` (Battery Level)

- **Type**: float64
- **Unit**: Percentage (0-100)
- **Physical meaning**: Battery charge level for wireless sensors
- **Statistics**:
  - Min: 0.0%
  - Max: 100.0%
  - Mean: 98.40%
  - Median: 100.0%
  - Std dev: 10.25%
  - Missing: 3.72%
- **Significance**:
  - Generally very high (>95% average)
  - May indicate well-maintained or recently charged sensor system
  - Low battery periods could correlate with data quality issues

---

## Flag Columns (Anomaly Indicators)

All flags are of type `bool` with 0% missing values.

### 10. `_flag_secondary_error_code`

- **Type**: bool
- **True frequency**: 4,126 occurrences (0.53% of data)
- **Description**: Indicates presence of secondary error codes
- **Likely trigger**: System-level errors or warnings

### 11. `_flag_main_temp_high`

- **Type**: bool
- **True frequency**: 4,239 occurrences (0.54% of data)
- **Description**: Main temperature (room) is too high
- **Likely trigger**: `sGekoeldeRuimte` exceeds threshold (probably > -18°C or approaching 0°C)
- **Significance**: **Primary indicator of cooling failure or insufficient capacity**

### 12. `_flag_hot_gas_low`

- **Type**: bool
- **True frequency**: 3,085 occurrences (0.39% of data)
- **Description**: Hot gas line temperature is unusually low
- **Likely trigger**: `sHeetgasLeiding` < 30-35°C
- **Significance**: Indicates compressor not running or refrigerant issues

### 13. `_flag_liquid_extreme`

- **Type**: bool
- **True frequency**: 3,021 occurrences (0.38% of data)
- **Description**: Liquid line temperature is outside normal range
- **Likely trigger**: `sVloeistofleiding` outside 25-45°C range
- **Significance**: May indicate condenser problems or extreme ambient conditions

### 14. `_flag_suction_extreme`

- **Type**: bool
- **True frequency**: 3,094 occurrences (0.39% of data)
- **Description**: Suction line temperature is outside normal range
- **Likely trigger**: `sZuigleiding` outside 25-40°C range
- **Significance**: May indicate evaporator problems or superheat issues

### 15. `_flag_ambient_extreme`

- **Type**: bool
- **True frequency**: 11 occurrences (0.00% of data - extremely rare)
- **Description**: Ambient temperature is extreme
- **Likely trigger**: `sOmgeving` < 5°C or > 45°C
- **Significance**: Indicates extreme environmental conditions

---

## Data Quality Notes

1. **Missing data**: Fairly consistent at ~3.7% across most sensors
2. **Temporal consistency**: 1-minute sampling rate maintained throughout 2+ years
3. **Flag correlation**: Multiple flags often trigger simultaneously during incidents
4. **Sensor naming**: Dutch naming convention (s = sensor)
   - Gekoelde Ruimte = Cooled Room
   - Heetgas Leiding = Hot Gas Line
   - Vloeistof Leiding = Liquid Line
   - Zuig Leiding = Suction Line
   - Omgeving = Ambient/Environment
   - Deurcontact = Door Contact

---

## Key Findings for WorldState Features

1. **Primary health indicator**: `sGekoeldeRuimte` and `_flag_main_temp_high`
2. **Compressor health**: `sHeetgasLeiding` and `_flag_hot_gas_low`
3. **System balance**: Relationship between hot gas, liquid, and suction temps
4. **External factors**: `sOmgeving` (ambient) and `sDeurcontact` (door usage)
5. **Data reliability**: `sRSSI` and `sBattery` for data quality assessment
6. **Incident frequency**: ~0.4-0.5% of time shows anomaly flags (rare but present)
