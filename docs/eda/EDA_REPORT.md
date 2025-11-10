# Exploratory Data Analysis Report
## Freezer Telemetry Dataset (135_1570)

---

## Executive Summary

This report presents a comprehensive exploratory data analysis of freezer telemetry data collected over a period of **528 days** from **2022-10-20 16:02:00** to **2024-04-01 01:59:00**.

**Key Findings:**
- Dataset contains **785,398** observations across **9** sensor variables
- Time series data collected at **1-minute intervals**
- Overall data quality is **good** with ~6% missing values after numeric conversion
- Strong correlations detected between temperature and battery level (-0.878)
- Cooled room maintains stable temperature around **-33.84°C** (industrial freezer range)
- Minimal daily/weekly seasonality patterns detected

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| **Total Records** | 785,398 |
| **Time Period** | 2022-10-20 16:02:00 to 2024-04-01 01:59:00 |
| **Duration** | 528 days |
| **Number of Variables** | 9 |
| **Sampling Frequency** | ~1 minute |
| **Memory Usage** | 59.92 MB |

---

## 2. Variable Descriptions

| Variable | Description | Type |
|----------|-------------|------|
| `sGekoeldeRuimte` | Cooled room temperature (main freezer) | Temperature (°C) |
| `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` | Secondary cooled room sensor | Temperature (°C) |
| `sHeetgasLeiding` | Hot gas line temperature | Temperature (°C) |
| `sVloeistofleiding` | Liquid line temperature | Temperature (°C) |
| `sZuigleiding` | Suction line temperature | Temperature (°C) |
| `sOmgeving` | Ambient/environment temperature | Temperature (°C) |
| `sDeurcontact` | Door contact sensor | Binary (0/1) |
| `sRSSI` | Signal strength | dBm |
| `sBattery` | Battery level | Percentage (%) |

---

## 3. Data Quality Assessment

### Missing Values

| Variable | Missing Count | Missing % |
|----------|---------------|----------|
| `sGekoeldeRuimte` | 47,854 | 6.09% |
| `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` | 47,897 | 6.10% |
| `sHeetgasLeiding` | 47,905 | 6.10% |
| `sVloeistofleiding` | 47,845 | 6.09% |
| `sZuigleiding` | 47,851 | 6.09% |
| `sOmgeving` | 48,112 | 6.13% |
| `sDeurcontact` | 45,359 | 5.78% |
| `sRSSI` | 32,219 | 4.10% |
| `sBattery` | 45,355 | 5.77% |

**Assessment:** Missing values are consistent across all sensors (~6%), likely due to transmission issues or sensor downtime. This is acceptable for IoT sensor data.

---

## 4. Descriptive Statistics

### Temperature Sensors

| Sensor | Min (°C) | Mean (°C) | Median (°C) | Max (°C) | Std Dev |
|--------|----------|-----------|-------------|----------|----------|
| `sGekoeldeRuimte` | -37.50 | -33.84 | -34.20 | 56.40 | 4.07 |
| `sHeetgasLeiding` | 11.60 | 50.40 | 53.10 | 77.50 | 8.16 |
| `sVloeistofleiding` | 11.90 | 33.93 | 34.30 | 84.70 | 1.78 |
| `sZuigleiding` | 11.70 | 31.31 | 31.60 | 57.50 | 2.20 |
| `sOmgeving` | -35.20 | 29.94 | 29.50 | 71.20 | 3.20 |

### System Sensors

| Sensor | Min | Mean | Median | Max | Std Dev |
|--------|-----|------|--------|-----|---------|
| `sDeurcontact` | 0.00 | 0.01 | 0.00 | 1.00 | 0.08 |
| `sRSSI` | -115.00 | -80.68 | -82.00 | 0.00 | 5.10 |
| `sBattery` | 0.00 | 99.59 | 100.00 | 100.00 | 5.20 |

---

## 5. Key Insights

### 5.1 Temperature Behavior
- **Main freezer temperature** (sGekoeldeRuimte): Maintains stable operation at **-33.84°C ± 4.07°C**
- Operating range: -37.5°C to 56.4°C (outliers suggest possible defrost cycles or sensor errors)
- **Hot gas line**: Average 50.4°C, indicating active refrigeration system
- **Liquid/suction lines**: Stable around 33-34°C, normal operation

### 5.2 Correlation Analysis

**Strong Positive Correlations (r > 0.7):**
- `sGekoeldeRuimte` ↔ `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive`: **0.960**
- `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` ↔ `sDeurcontact`: **0.888**
- `sGekoeldeRuimte` ↔ `sBattery`: **-0.878**
- `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` ↔ `sBattery`: **-0.867**
- `sGekoeldeRuimte` ↔ `sDeurcontact`: **0.852**
- `sVloeistofleiding` ↔ `sZuigleiding`: **0.779**
- `sDeurcontact` ↔ `sBattery`: **-0.765**
- `sHeetgasLeiding` ↔ `sOmgeving`: **0.754**

**Key Observations:**
- Very high correlation (0.960) between two cooled room sensors - redundancy
- Strong negative correlation (-0.878) between temperature and battery suggests battery drain during active cooling
- Door contact strongly correlates with temperature changes (0.852)
- Hot gas line correlates with ambient temperature (0.754) - expected behavior

### 5.3 Outlier Detection

Outliers detected using IQR method (values beyond 1.5 × IQR):

| Variable | Outlier Count | Outlier % |
|----------|---------------|-----------|
| `sGekoeldeRuimte` | 17,991 | 2.29% |
| `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` | 17,991 | 2.29% |
| `sHeetgasLeiding` | 4,018 | 0.51% |
| `sVloeistofleiding` | 5,726 | 0.73% |
| `sZuigleiding` | 9,834 | 1.25% |
| `sOmgeving` | 14,025 | 1.79% |
| `sDeurcontact` | 5,151 | 0.66% |
| `sRSSI` | 20,621 | 2.63% |
| `sBattery` | 5,887 | 0.75% |

**Assessment:** Outlier percentages are low (<3%), indicating stable system operation. Temperature outliers likely represent defrost cycles or door-open events.

### 5.4 Temporal Patterns

**Hourly Patterns:**
- Minimal hour-of-day variation in main temperature (±0.1°C)
- Slight temperature increase during business hours (9am-5pm)
- Battery usage shows minor diurnal pattern

**Weekly Patterns:**
- No significant day-of-week effects detected
- Average temperature varies by only ~0.25°C across the week
- Suggests continuous industrial operation (24/7)

### 5.5 System Health Indicators

**Battery:**
- Mean level: **99.59%** (excellent)
- Remains near 100% for most observations
- Well-maintained power supply

**Signal Strength (RSSI):**
- Mean: **-80.68 dBm** (acceptable for IoT devices)
- Range: -115 to 0 dBm
- Stable connectivity

**Door Contact:**
- Mean: **0.01** (99% closed)
- Door opens are rare events (~1% of time)
- Proper operational procedure

---

## 6. Recommendations

### Data Quality
1. **✓ Good:** Missing values are minimal and consistent
2. **✓ Good:** No systematic data quality issues detected
3. **⚠ Consider:** Investigating temperature outliers >50°C for validation

### System Monitoring
1. **Monitor battery drainage correlation** with cooling cycles for predictive maintenance
2. **Alert on door open events** lasting >5 minutes to prevent temperature excursions
3. **Track RSSI trends** to detect connectivity degradation before failures
4. **Anomaly detection** for temperature deviations >3 standard deviations

### Further Analysis
1. **Predictive modeling:** Forecast temperature based on ambient conditions
2. **Anomaly detection:** Implement real-time algorithms for defrost cycle detection
3. **Energy optimization:** Analyze relationship between temperature setpoints and power consumption
4. **Maintenance prediction:** Use sensor degradation patterns for preventive maintenance

---

## 7. Visualizations Generated

The following visualizations have been created in the `docs/` folder:

1. **eda_timeseries.png** - Time series plots of key sensors over the full period
2. **eda_distributions.png** - Histograms showing value distributions for all variables
3. **eda_correlation.png** - Correlation heatmap showing relationships between variables
4. **eda_temporal_patterns.png** - Hourly and daily patterns in temperature and system metrics
5. **eda_boxplots.png** - Box plots for outlier visualization

---

## 8. Conclusion

This freezer telemetry system demonstrates **excellent operational stability** with:
- Consistent temperature control within industrial freezer specifications
- High data quality with minimal missing values
- Strong system health indicators (battery, connectivity)
- Predictable behavior with minimal temporal variation

The data is **well-suited for:**
- Predictive maintenance modeling
- Anomaly detection algorithms
- Energy efficiency optimization
- Long-term trend analysis

**Next Steps:** Consider implementing real-time monitoring dashboards and automated alert systems based on the patterns identified in this analysis.

---

*Report generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
