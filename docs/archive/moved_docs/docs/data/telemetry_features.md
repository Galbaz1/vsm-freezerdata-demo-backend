# WorldState Features Proposal

## Overview

This document proposes a set of **WorldState features** to be computed from the telemetry data. These features will be used by the Elysia agent to understand the current state of the cooling installation and perform diagnostics according to the SMIDO methodology.

The features are organized into categories:
1. **Current State** - Instantaneous values
2. **Historical Trends** - Aggregated over time windows
3. **Incident Indicators** - Boolean flags and derived alerts
4. **System Health Metrics** - Derived health scores
5. **Context Features** - Environmental and operational context

---

## 1. Current State Features (Instantaneous)

These features represent the most recent measurement values.

| Feature Name | Description | Source Column(s) | Unit |
|--------------|-------------|------------------|------|
| `current_room_temp` | Current temperature in cooled room | `sGekoeldeRuimte` | °C |
| `current_room_temp_secondary` | Current secondary sensor reading | `p:42_s:_a:standard_n:Gekoelderuimte(2)_inactive` | °C |
| `current_hot_gas_temp` | Current hot gas line temperature | `sHeetgasLeiding` | °C |
| `current_liquid_temp` | Current liquid line temperature | `sVloeistofleiding` | °C |
| `current_suction_temp` | Current suction line temperature | `sZuigleiding` | °C |
| `current_ambient_temp` | Current ambient temperature | `sOmgeving` | °C |
| `current_door_open` | Door currently open (boolean) | `sDeurcontact` | bool |
| `current_rssi` | Current signal strength | `sRSSI` | dBm |
| `current_battery` | Current battery level | `sBattery` | % |

**Implementation notes**:
- Use the most recent non-null value
- For `current_door_open`: convert float to bool (threshold 0.5)
- Time window: latest measurement (t=0)

---

## 2. Historical Trend Features

These features aggregate data over specified time windows to capture system behavior patterns.

### 2.1 Short-term trends (last 30 minutes)

| Feature Name | Description | Source | Calculation | Unit |
|--------------|-------------|--------|-------------|------|
| `room_temp_min_30m` | Minimum room temp in last 30 min | `sGekoeldeRuimte` | min() | °C |
| `room_temp_max_30m` | Maximum room temp in last 30 min | `sGekoeldeRuimte` | max() | °C |
| `room_temp_mean_30m` | Mean room temp in last 30 min | `sGekoeldeRuimte` | mean() | °C |
| `room_temp_std_30m` | Std dev room temp in last 30 min | `sGekoeldeRuimte` | std() | °C |
| `room_temp_delta_30m` | Change in room temp over 30 min | `sGekoeldeRuimte` | current - 30min_ago | °C |
| `door_open_ratio_30m` | Fraction of time door was open | `sDeurcontact` | mean() | 0-1 |
| `door_open_count_30m` | Number of door opening events | `sDeurcontact` | transitions 0→1 | count |

### 2.2 Medium-term trends (last 2 hours)

| Feature Name | Description | Source | Calculation | Unit |
|--------------|-------------|--------|-------------|------|
| `room_temp_min_2h` | Minimum room temp in last 2h | `sGekoeldeRuimte` | min() | °C |
| `room_temp_max_2h` | Maximum room temp in last 2h | `sGekoeldeRuimte` | max() | °C |
| `room_temp_mean_2h` | Mean room temp in last 2h | `sGekoeldeRuimte` | mean() | °C |
| `room_temp_trend_2h` | Linear trend (warming/cooling rate) | `sGekoeldeRuimte` | linear regression slope | °C/hour |
| `hot_gas_mean_2h` | Mean hot gas temp (compressor activity) | `sHeetgasLeiding` | mean() | °C |
| `hot_gas_std_2h` | Std dev hot gas (cycling indicator) | `sHeetgasLeiding` | std() | °C |
| `ambient_mean_2h` | Mean ambient temperature | `sOmgeving` | mean() | °C |
| `door_open_ratio_2h` | Fraction of time door was open | `sDeurcontact` | mean() | 0-1 |

### 2.3 Long-term trends (last 24 hours)

| Feature Name | Description | Source | Calculation | Unit |
|--------------|-------------|--------|-------------|------|
| `room_temp_min_24h` | Minimum room temp in last 24h | `sGekoeldeRuimte` | min() | °C |
| `room_temp_max_24h` | Maximum room temp in last 24h | `sGekoeldeRuimte` | max() | °C |
| `room_temp_mean_24h` | Mean room temp in last 24h | `sGekoeldeRuimte` | mean() | °C |
| `temp_violations_24h` | Hours with temp > -18°C | `sGekoeldeRuimte` | count(temp > -18) / 60 | hours |
| `compressor_runtime_24h` | Estimated compressor runtime | `sHeetgasLeiding` | hours(temp > 35°C) | hours |
| `compressor_cycle_count_24h` | Number of compressor cycles | `sHeetgasLeiding` | transitions low→high | count |
| `door_open_ratio_24h` | Fraction of time door was open | `sDeurcontact` | mean() | 0-1 |
| `door_open_total_24h` | Total door opening events | `sDeurcontact` | transitions 0→1 | count |

**Implementation notes**:
- Use pandas rolling windows or group-by aggregations
- Handle missing data: require minimum 80% data availability in window
- For cycle counting: use threshold-based state detection

---

## 3. Incident Indicator Features

These features directly relate to failure modes and anomalies.

### 3.1 Current Flags (from data)

| Feature Name | Description | Source | Type |
|--------------|-------------|--------|------|
| `flag_secondary_error` | Secondary error code present | `_flag_secondary_error_code` | bool |
| `flag_main_temp_high` | Main temperature too high | `_flag_main_temp_high` | bool |
| `flag_hot_gas_low` | Hot gas temp too low | `_flag_hot_gas_low` | bool |
| `flag_liquid_extreme` | Liquid line temp extreme | `_flag_liquid_extreme` | bool |
| `flag_suction_extreme` | Suction line temp extreme | `_flag_suction_extreme` | bool |
| `flag_ambient_extreme` | Ambient temp extreme | `_flag_ambient_extreme` | bool |

### 3.2 Derived Incident Features

| Feature Name | Description | Calculation | Type | Time Window |
|--------------|-------------|-------------|------|-------------|
| `is_temp_critical` | Room temp above critical threshold | `current_room_temp > -10` | bool | current |
| `is_temp_warning` | Room temp above warning threshold | `current_room_temp > -18` | bool | current |
| `is_temp_rising` | Temperature trending upward | `room_temp_trend_2h > 0.5` | bool | 2h |
| `is_compressor_inactive` | Compressor appears off/failed | `current_hot_gas_temp < 30` | bool | current |
| `is_door_stuck_open` | Door open for extended period | `door_open_ratio_30m > 0.8` | bool | 30m |
| `has_recent_errors` | Any flags in last 2 hours | any flag = True | bool | 2h |
| `error_duration_current` | Minutes since first error flag | time since first True flag | minutes | current |
| `is_ambient_high` | Ambient temp stressing system | `current_ambient_temp > 35` | bool | current |
| `is_sensor_communication_poor` | Weak signal or low battery | `current_rssi < -90 OR current_battery < 20` | bool | current |

**Implementation notes**:
- Thresholds are based on typical freezer operation
- May need adjustment based on specific installation requirements
- `is_temp_critical`: -10°C chosen as it indicates complete loss of freezing
- `is_temp_warning`: -18°C is typical freezer specification

---

## 4. System Health Metrics (Derived Scores)

These are composite features that assess overall system health.

| Feature Name | Description | Calculation Method | Range | Unit |
|--------------|-------------|-------------------|-------|------|
| `cooling_performance_score` | How well system maintains target temp | Based on deviation from -34°C and trend | 0-100 | score |
| `compressor_health_score` | Compressor operational health | Based on hot gas temps, cycling behavior | 0-100 | score |
| `system_stability_score` | Overall system stability | Based on std devs and flag frequency | 0-100 | score |
| `data_quality_score` | Sensor data reliability | Based on RSSI, battery, missing data | 0-100 | score |

### 4.1 Cooling Performance Score

```
cooling_performance_score = 100 * (1 - weighted_factors)

where weighted_factors combines:
- Deviation from target (-34°C): weight 0.4
- Temperature rising trend: weight 0.3
- Recent flag activations: weight 0.2
- Ambient stress factor: weight 0.1
```

### 4.2 Compressor Health Score

```
compressor_health_score = 100 * (1 - weighted_factors)

where weighted_factors combines:
- Hot gas temp deviation from 50°C: weight 0.3
- Excessive cycling (>10 cycles/hour): weight 0.3
- Low hot gas temp (<35°C): weight 0.3
- Hot gas high variability: weight 0.1
```

**Implementation notes**:
- Scores should be capped at 0 (min) and 100 (max)
- Use sigmoid or linear interpolation for smooth scoring
- These are heuristic-based; could be replaced with ML models later

---

## 5. Context Features

These provide additional context for decision-making.

| Feature Name | Description | Source/Calculation | Type |
|--------------|-------------|-------------------|------|
| `timestamp_current` | Current measurement timestamp | index | datetime |
| `time_since_last_measurement` | Data freshness indicator | current_time - last_timestamp | minutes |
| `hour_of_day` | Hour (for usage patterns) | timestamp.hour | 0-23 |
| `day_of_week` | Day (for usage patterns) | timestamp.dayofweek | 0-6 |
| `is_business_hours` | Typical business hours | hour_of_day in [8-18] and day_of_week in [0-4] | bool |
| `time_since_last_door_event` | Time since last door interaction | minutes since last door transition | minutes |
| `sensor_data_age_max` | Oldest data in window | max(time_since_measurement) for any null | minutes |

**Implementation notes**:
- Useful for contextualizing anomalies (e.g., door usage patterns)
- May reveal operational patterns (higher usage during business hours)
- `is_business_hours`: assumes Mon-Fri 8am-6pm; adjust as needed

---

## 6. Feature Groups for SMIDO Steps

Features are logically grouped to support each SMIDO diagnostic step:

### Melding (Initial Report)
- `current_room_temp`
- `flag_main_temp_high`
- `is_temp_critical` / `is_temp_warning`
- `error_duration_current`

### Technisch (Technical Check)
- `current_hot_gas_temp`
- `is_compressor_inactive`
- `compressor_health_score`
- `flag_hot_gas_low`

### Installatie Vertrouwd (Installation Familiarity)
- `room_temp_mean_24h` (baseline)
- `compressor_runtime_24h`
- `ambient_mean_2h`
- Historical patterns

### 3 P's (Power, Process settings, Process parameters, Product input)
- **Power**: `is_compressor_inactive`, `current_hot_gas_temp`
- **Procesinstellingen**: Comparison to baseline (not in raw data)
- **Procesparameters**: `current_liquid_temp`, `current_suction_temp`, system balance
- **Product input**: `door_open_ratio_*`, `is_door_stuck_open`

### Ketens & Onderdelen Uitsluiten (Chains & Components)
- Temperature differentials:
  - `hot_gas_to_liquid_delta` = `current_hot_gas_temp - current_liquid_temp`
  - `liquid_to_suction_delta` = `current_liquid_temp - current_suction_temp`
- Flag patterns:
  - `flag_liquid_extreme`, `flag_suction_extreme`
- Component-specific indicators

---

## 7. Implementation Priorities

### Phase 1 (Essential for MVP demo)
1. All current state features (section 1)
2. Short-term trends - 30 min window (section 2.1)
3. Current flags (section 3.1)
4. Basic derived incident features (section 3.2)

### Phase 2 (Enhanced diagnostics)
1. Medium-term trends - 2 hour window (section 2.2)
2. Long-term trends - 24 hour window (section 2.3)
3. System health scores (section 4)

### Phase 3 (Advanced features)
1. Context features (section 5)
2. ML-based anomaly scores
3. Predictive features

---

## 8. Feature Computation Strategy

### Real-time WorldState Tool

For the Elysia agent's real-time use:

```python
def compute_world_state(asset_id: str, timestamp: datetime) -> WorldState:
    """
    Compute WorldState features for a given asset and time point

    Args:
        asset_id: Asset identifier (e.g., "135_1570")
        timestamp: Point in time for state computation

    Returns:
        WorldState object with all computed features
    """
    # Load relevant time window from parquet
    # Compute features according to sections above
    # Return structured WorldState object
```

### For Incident Detection (Batch)

When creating `Incidents` collection for Weaviate:

```python
def detect_and_create_incidents(df: pd.DataFrame) -> List[Incident]:
    """
    Scan historical data for incident periods

    Incidents are defined as:
    - Continuous periods where one or more flags = True
    - OR room_temp > -18°C for >30 minutes

    For each incident, compute:
    - Start/end time
    - Duration
    - All WorldState features at start, peak, and end
    - Failure mode classification
    """
```

---

## 9. Data Requirements

For each feature computation time window:

| Window | Data Points Needed | Storage (approx) |
|--------|-------------------|------------------|
| Current | 1 measurement | ~200 bytes |
| 30 minutes | 30 measurements | ~6 KB |
| 2 hours | 120 measurements | ~24 KB |
| 24 hours | 1,440 measurements | ~288 KB |

**Total for full WorldState**: ~318 KB per computation

This is feasible for real-time API queries from parquet files given:
- Parquet columnar format (efficient column selection)
- Indexed by timestamp
- Total file size: 785,398 rows ≈ 12 MB per column

---

## 10. Example WorldState JSON Output

```json
{
  "asset_id": "135_1570",
  "timestamp": "2024-12-31T14:30:00Z",
  "current_state": {
    "room_temp": -28.5,
    "hot_gas_temp": 52.3,
    "liquid_temp": 34.1,
    "suction_temp": 31.2,
    "ambient_temp": 24.5,
    "door_open": false,
    "rssi": -78,
    "battery": 100
  },
  "trends_30m": {
    "room_temp_min": -34.2,
    "room_temp_max": -28.5,
    "room_temp_delta": 5.7,
    "door_open_ratio": 0.15
  },
  "trends_2h": {
    "room_temp_trend": 2.8,
    "hot_gas_mean": 51.2,
    "ambient_mean": 25.1
  },
  "flags": {
    "main_temp_high": true,
    "hot_gas_low": false,
    "liquid_extreme": false,
    "suction_extreme": false,
    "ambient_extreme": false
  },
  "incidents": {
    "is_temp_critical": false,
    "is_temp_warning": true,
    "is_temp_rising": true,
    "is_compressor_inactive": false,
    "has_recent_errors": true,
    "error_duration_minutes": 45
  },
  "health_scores": {
    "cooling_performance": 65,
    "compressor_health": 85,
    "system_stability": 70,
    "data_quality": 95
  }
}
```

---

## Next Steps

1. ✅ **Document proposed features** (this document)
2. ⏳ Implement feature computation functions in Python
3. ⏳ Create unit tests with sample data
4. ⏳ Integrate with Elysia as a custom tool
5. ⏳ Validate features against known incidents in historical data
