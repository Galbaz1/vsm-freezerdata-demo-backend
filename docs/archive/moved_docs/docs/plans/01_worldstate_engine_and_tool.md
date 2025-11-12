# Plan 1: WorldState Engine + ComputeWorldState Tool

**Priority**: HIGH (Foundational - other tools depend on this)  
**Parallelization**: Can run independently  
**Estimated Time**: 2-3 hours

---

## Objective

Implement the WorldState Engine to compute 60+ features from telemetry parquet data, and create the ComputeWorldState tool that exposes this functionality to the SMIDO decision tree.

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md` (lines 273-289 - WorldState Engine design)
- `docs/diagrams/vsm_agent_architecture.mermaid` (WorldStateEngine, ParquetReader components)

**Data Specifications**:
- `docs/data/telemetry_features.md` (60+ feature definitions)
- `docs/data/telemetry_schema.md` (parquet column definitions)
- `docs/data/SYNTHETIC_DATA_STRATEGY.md` (WorldState W definition, lines 84-88)

**Parquet Data**:
- `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet` (785,398 rows)

**Elysia Tool Pattern**:
- `elysia/api/custom_tools.py` (TellAJoke example, lines 14-44)
- `elysia/objects.py` (Tool class definition, lines 98-149)

**Reference Implementation**:
- `features/telemetry_vsm/src/detect_events.py` (existing event detection - similar pattern)

---

## Implementation Tasks

### Task 1.1: Create WorldState Engine Module

**File**: `features/telemetry_vsm/src/worldstate_engine.py`

**Implementation**:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

class WorldStateEngine:
    """
    Computes 60+ WorldState features from telemetry parquet data.
    Implements on-demand computation for flexible time windows.
    """
    
    def __init__(self, parquet_path: str):
        self.parquet_path = parquet_path
        self._df = None  # Lazy load
    
    def _load_data(self) -> pd.DataFrame:
        """Lazy load parquet file"""
        if self._df is None:
            self._df = pd.read_parquet(self.parquet_path)
        return self._df
    
    def compute_worldstate(
        self,
        asset_id: str,
        timestamp: datetime,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Compute WorldState features for given time window.
        
        Returns dict with:
        - current_state: Latest sensor values
        - trends_30m: 30-minute aggregates
        - trends_2h: 2-hour aggregates
        - trends_24h: 24-hour aggregates (optional)
        - flags: Boolean indicators
        - incidents: Derived incident features
        - health_scores: Composite health metrics
        """
        df = self._load_data()
        
        # Filter time window
        end_time = timestamp
        start_time = timestamp - timedelta(minutes=window_minutes)
        window_df = df[start_time:end_time]
        
        if len(window_df) == 0:
            raise ValueError(f"No data found for time window {start_time} to {end_time}")
        
        # Compute features (implement from telemetry_features.md)
        worldstate = {
            "asset_id": asset_id,
            "timestamp": timestamp.isoformat(),
            "current_state": self._compute_current_state(window_df),
            "trends_30m": self._compute_trends_30m(window_df),
            "trends_2h": self._compute_trends_2h(df, timestamp),
            "flags": self._compute_flags(window_df),
            "incidents": self._compute_incidents(window_df),
            "health_scores": self._compute_health_scores(window_df)
        }
        
        return worldstate
    
    def _compute_current_state(self, df: pd.DataFrame) -> Dict:
        """Latest sensor values - Section 1 from telemetry_features.md"""
        latest = df.iloc[-1]
        return {
            "room_temp": float(latest['sGekoeldeRuimte']),
            "hot_gas_temp": float(latest['sHeetgasLeiding']),
            "liquid_temp": float(latest['sVloeistofleiding']),
            "suction_temp": float(latest['sZuigleiding']),
            "ambient_temp": float(latest['sOmgeving']),
            "door_open": bool(latest['sDeurcontact'] > 0.5),
            "rssi": float(latest['sRSSI']),
            "battery": float(latest['sBattery'])
        }
    
    def _compute_trends_30m(self, df: pd.DataFrame) -> Dict:
        """30-minute aggregates - Section 2.1 from telemetry_features.md"""
        # Implement min/max/mean/std/delta for room temp, door usage
        return {
            "room_temp_min": float(df['sGekoeldeRuimte'].min()),
            "room_temp_max": float(df['sGekoeldeRuimte'].max()),
            "room_temp_mean": float(df['sGekoeldeRuimte'].mean()),
            "room_temp_std": float(df['sGekoeldeRuimte'].std()),
            "room_temp_delta": float(df['sGekoeldeRuimte'].iloc[-1] - df['sGekoeldeRuimte'].iloc[0]),
            "door_open_ratio": float(df['sDeurcontact'].mean()),
            "door_open_count": int((df['sDeurcontact'].diff() > 0).sum())
        }
    
    def _compute_trends_2h(self, full_df: pd.DataFrame, timestamp: datetime) -> Dict:
        """2-hour aggregates - Section 2.2 from telemetry_features.md"""
        # Filter 2-hour window
        start = timestamp - timedelta(hours=2)
        df_2h = full_df[start:timestamp]
        
        if len(df_2h) < 10:
            return {}
        
        return {
            "room_temp_min": float(df_2h['sGekoeldeRuimte'].min()),
            "room_temp_max": float(df_2h['sGekoeldeRuimte'].max()),
            "room_temp_mean": float(df_2h['sGekoeldeRuimte'].mean()),
            "room_temp_trend": self._compute_linear_trend(df_2h['sGekoeldeRuimte']),
            "hot_gas_mean": float(df_2h['sHeetgasLeiding'].mean()),
            "hot_gas_std": float(df_2h['sHeetgasLeiding'].std()),
            "door_open_ratio": float(df_2h['sDeurcontact'].mean())
        }
    
    def _compute_linear_trend(self, series: pd.Series) -> float:
        """Compute linear trend (°C/hour)"""
        if len(series) < 2:
            return 0.0
        x = np.arange(len(series))
        y = series.values
        slope = np.polyfit(x, y, 1)[0]
        return float(slope * 60)  # Convert to °C/hour
    
    def _compute_flags(self, df: pd.DataFrame) -> Dict:
        """Boolean flags - Section 3.1 from telemetry_features.md"""
        latest = df.iloc[-1]
        return {
            "main_temp_high": bool(latest['_flag_main_temp_high']),
            "hot_gas_low": bool(latest['_flag_hot_gas_low']),
            "liquid_extreme": bool(latest['_flag_liquid_extreme']),
            "suction_extreme": bool(latest['_flag_suction_extreme']),
            "ambient_extreme": bool(latest['_flag_ambient_extreme'])
        }
    
    def _compute_incidents(self, df: pd.DataFrame) -> Dict:
        """Derived incidents - Section 3.2 from telemetry_features.md"""
        latest = df.iloc[-1]
        room_temp = latest['sGekoeldeRuimte']
        hot_gas = latest['sHeetgasLeiding']
        trend = self._compute_linear_trend(df['sGekoeldeRuimte'])
        
        return {
            "is_temp_critical": bool(room_temp > -10),
            "is_temp_warning": bool(room_temp > -18),
            "is_temp_rising": bool(trend > 0.5),
            "is_compressor_inactive": bool(hot_gas < 30),
            "is_door_stuck_open": bool(df['sDeurcontact'].mean() > 0.8),
            "has_recent_errors": bool(df[[col for col in df.columns if col.startswith('_flag_')]].any().any())
        }
    
    def _compute_health_scores(self, df: pd.DataFrame) -> Dict:
        """Health scores - Section 4 from telemetry_features.md"""
        room_temp = df['sGekoeldeRuimte'].mean()
        target = -33.0
        
        # Simple scoring (can be enhanced)
        cooling_performance = max(0, min(100, 100 * (1 - abs(room_temp - target) / 20)))
        
        return {
            "cooling_performance": int(cooling_performance),
            "compressor_health": 80,  # Placeholder - enhance later
            "system_stability": 75,  # Placeholder
            "data_quality": 95  # Placeholder
        }
```

**Tests**:
- Unit tests with sample parquet data
- Verify all 60+ features computed correctly
- Performance test: <500ms for 60min window

---

### Task 1.2: Create ComputeWorldState Tool

**File**: `elysia/api/custom_tools.py` (add to existing file)

**Implementation**:

```python
from elysia import Tool, tool
from elysia.objects import Result, Status
from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
from datetime import datetime

@tool(status="Computing WorldState features from telemetry...", branch_id="smido_diagnose")
async def compute_worldstate(
    asset_id: str,
    timestamp: str = None,
    window_minutes: int = 60,
    tree_data=None,
    **kwargs
):
    """
    Compute WorldState (W) features from telemetry parquet data.
    Returns 60+ features including current state, trends, flags, and health scores.
    
    Used in: P3 (Procesparameters), P4 (Productinput) SMIDO nodes
    """
    yield Status(f"Loading telemetry data for asset {asset_id}...")
    
    # Parse timestamp
    ts = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
    
    # Initialize engine
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    
    yield Status(f"Computing WorldState for {window_minutes}-minute window...")
    
    # Compute features
    worldstate = engine.compute_worldstate(asset_id, ts, window_minutes)
    
    # Store in tree_data environment
    if tree_data:
        tree_data.environment["worldstate"] = worldstate
        tree_data.environment["worldstate_timestamp"] = ts.isoformat()
    
    yield Result(
        objects=[worldstate],
        metadata={
            "source": "worldstate_engine",
            "window_minutes": window_minutes,
            "features_computed": len(worldstate.keys())
        }
    )
```

---

## Verification

**Success Criteria**:
- [ ] WorldStateEngine computes all features from `telemetry_features.md`
- [ ] ComputeWorldState tool callable from Elysia tree
- [ ] WorldState stored in tree_data.environment
- [ ] Performance: <500ms for 60min window
- [ ] Unit tests pass

**Test Command**:
```bash
python3 -c "
from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
from datetime import datetime

engine = WorldStateEngine('features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet')
ws = engine.compute_worldstate('135_1570', datetime(2024, 1, 1, 12, 0), 60)
print(f'Features: {list(ws.keys())}')
print(f'Current room temp: {ws[\"current_state\"][\"room_temp\"]}°C')
"
```

---

## Dependencies

**Required Before**:
- None (foundational task)

**Blocks**:
- GetAssetHealth tool (needs WorldState)
- AnalyzeSensorPattern tool (needs WorldState)

---

## Related Files

**To Create**:
- `features/telemetry_vsm/src/worldstate_engine.py`
- `features/telemetry_vsm/tests/test_worldstate_engine.py`

**To Modify**:
- `elysia/api/custom_tools.py` (add ComputeWorldState tool)

**To Reference**:
- `docs/data/telemetry_features.md` (feature specifications)
- `features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet` (data source)


