# Synthetic Data Strategy for VSM Demo

**Created**: November 11, 2024  
**Purpose**: Document synthetic/fake data requirements and integration with data upload strategy  
**Status**: 📝 Strategy Document

---

## Executive Summary

Agent tools require synthetic data for pattern matching and context. This document defines synthetic data requirements based on agent architecture tool needs.

---

## Findings: Synthetic Data References

### 1. FD_* Collections (MVP/Test Data)

**Location**: `scripts/seed_assets_alarms.py`

**Current State**: ✅ **Already Implemented**

These are **synthetic test collections** used for MVP/demo purposes:

| Collection | Purpose | Synthetic Data |
|------------|---------|----------------|
| **FD_Assets** | Asset metadata | 1 synthetic freezer ("FZ-123", "Industrial Freezer 135-1570") |
| **FD_Alarms** | Alarm records | 2 synthetic alarms (E305, E102) |
| **FD_Cases** | Case studies | 1 synthetic case (CASE-001) |

**Status**: These are **separate from VSM_* collections** and serve as:
- Elysia framework testing
- Demo scenarios
- MVP validation

**Action**: ✅ **No action needed** - These are intentionally separate and already seeded.

---

### 2. Synthetic WorldState/Context (C, W)

**Location**: `todo.md` line 11

**Reference**: 
> "- Synthetic WorldState/Context (C, W) rondom de installatie"

**What This Means**:
- **C (Context)**: Synthetic context data about the installation (location, environment, operational history)
- **W (WorldState)**: Synthetic WorldState snapshots for common failure modes

**Current Status**: ❌ **NOT ADDRESSED** in data upload strategy

**Why Needed**:
- Agent needs context about the installation (not just telemetry)
- WorldState snapshots for fast lookup of common failure patterns
- Demo scenarios require realistic context data

**Gap**: Our `DATA_UPLOAD_STRATEGY.md` focuses on **real data** (telemetry events, manuals, vlogs) but doesn't mention:
- Synthetic installation context
- Pre-computed WorldState snapshots
- Synthetic troubleshooting cases

---

### 3. TroubleshootingCases Collection (Optional)

**Location**: `docs/data/data_analysis_summary.md` line 246

**Reference**:
> "`TroubleshootingCases` | Synthetic or real case studies combining all data types | Holistic case-based reasoning"

**Current Status**: ⏳ **PLANNED but not implemented**

**What This Means**:
- Combined case studies that integrate:
  - Telemetry events
  - Manual sections
  - Vlog clips
  - WorldState patterns
- Can be **synthetic** (for demo) or **real** (from actual incidents)

**Gap**: Not included in our upload strategy.

---

### 4. Synthetic Scenarios

**Location**: `todo.md` line 225

**Reference**:
> "Lees in `data/data_analysis_summary.md` welke synthetic scenario's zijn gedefinieerd (bv. 'condenser fan failure', 'liquid line blockage', etc.)"

**Current Status**: ⚠️ **Mentioned but not explicitly defined**

**What This Means**:
- Demo scenarios need synthetic data to:
  - Fill gaps in real data
  - Create reproducible test cases
  - Demonstrate specific failure modes

**Gap**: No explicit synthetic scenario definitions found.

---

## Required Synthetic Data

### Tool Requirements Matrix

| Agent Tool | Needs Synthetic Data | Type | Priority |
|------------|---------------------|------|----------|
| ComputeWorldState | No | - | - |
| QueryTelemetryEvents | No | - | - |
| SearchManualsBySMIDO | No | - | - |
| QueryVlogCases | No | - | - |
| GetAlarms | No | - | - |
| **GetAssetHealth** | **Yes** | Installation Context | HIGH |
| **AnalyzeSensorPattern** | **Yes** | WorldState Snapshots | HIGH |

### 1. Installation Context (C) - GetAssetHealth Tool

**Purpose**: Static design/commissioning data for comparing WorldState (W) against design specs

**Manual Reference**: "gegevens bij inbedrijfstelling" (commissioning data) - baseline for detecting "uit balans"

**Data Needed** (Context C):

```json
{
  "installation_id": "135_1570",
  "location": "Training Facility, Warehouse A",
  "model": "Industrial Freezer 135-1570",
  "capacity_liters": 1500,
  
  "commissioning_data": {
    "target_temp": -33.0,
    "evaporator_temp_design": -38.0,
    "suction_pressure_design": 1.2,
    "discharge_pressure_design": 14.5,
    "superheat_design": 5.0,
    "subcooling_design": 3.0,
    "ambient_design_max": 32.0,
    "product_load_max_kg_per_hour": 150
  },
  
  "components": {
    "compressor": {"model": "XYZ-123", "capacity_kW": 2.5},
    "evaporator": {"type": "forced_air", "defrost_type": "electric", "fans": 3},
    "condenser": {"type": "air_cooled", "fans": 2, "design_ambient_max": 32},
    "expansion_valve": {"type": "TXV", "capacity": "matched"}
  },
  
  "control_settings": {
    "defrost_interval_hours": 6,
    "defrost_duration_minutes": 20,
    "thermostat_setpoint": -33.0,
    "hp_pressostat_cutout": 16.0,
    "lp_pressostat_cutout": 0.8
  }
}
```

**Storage**: Enrich `FD_Assets` (already exists)

**Rationale**: 
- GetAssetHealth compares W (current) against C (design)
- Manual explicitly references "gegevens bij inbedrijfstelling" for comparison
- Implements "balans" concept: system operating within design parameters?

---

### 2. WorldState Snapshots (AnalyzeSensorPattern Tool)

**Purpose**: Reference patterns for "uit balans" (out of balance) detection - typical WorldState for each failure mode

**Manual Reference**: "Koelproces uit balans" section - system balance concept

**Data Needed**:

```json
{
  "snapshot_id": "ws_frozen_evaporator_001",
  "failure_mode": "ingevroren_verdamper",
  "worldstate": {
    "current_state": {
      "room_temp": -12.5,
      "hot_gas_temp": 28.0,
      "suction_temp": -15.0,
      "liquid_temp": 25.0
    },
    "trends_30m": {
      "room_temp_trend": 2.8,
      "door_open_ratio": 0.0
    },
    "flags": {
      "main_temp_high": true,
      "suction_extreme": true,
      "hot_gas_low": true
    },
    "health_scores": {
      "cooling_performance": 25,
      "compressor_health": 40
    }
  },
  "typical_pattern": "Room temp rising, evaporator frozen, defrost not working",
  "related_failure_modes": ["slecht_ontdooien", "te_hoge_temperatuur"]
}
```

**Storage**: Create `VSM_WorldStateSnapshot` collection

**Rationale**:
- AnalyzeSensorPattern needs fast semantic matching: "Is current W similar to known failure pattern?"
- Manual states: **"Een storing betekent dus niet altijd dat er een component defect is"** - faults can be system imbalance
- Snapshots represent typical W for each "uit balans" scenario

---

### 3. Synthetic Troubleshooting Cases (Optional)

**Purpose**: Demo scenarios only - NOT required by agent tools

**Data Needed** (for demos only):

```json
{
  "case_id": "SYNTH_A3_FROZEN_EVAPORATOR",
  "title": "Synthetic Case: Frozen Evaporator (Demo Scenario)",
  "type": "synthetic",
  "scenario": "A3 - Ingevroren Verdamper",
  "problem": "Koelcel bereikt temperatuur niet, verdamper volledig bevroren",
  "root_cause": "Defrost cycle malfunction + vervuilde luchtkanalen",
  "solution": "Manual defrost + clean air ducts + calibrate thermostat",
  "smido_steps": ["melding", "technisch", "installatie_vertrouwd", "3P_procesparameters", "ketens_onderdelen"],
  "data_sources": {
    "telemetry_event_id": "evt_2024_10_15_1430",
    "manual_section_ids": ["storingzoeken_smido_melding_001", "storingzoeken_koelproces_uit_balans"],
    "vlog_case_id": "A3",
    "worldstate_snapshot_id": "ws_frozen_evaporator_001"
  },
  "workflow": [
    {
      "smido_step": "melding",
      "actions": ["Collect symptoms", "Check current temperature"],
      "tools_used": ["ComputeWorldState", "QueryTelemetryEvents"]
    },
    {
      "smido_step": "technisch",
      "actions": ["Visual inspection", "Check evaporator condition"],
      "tools_used": ["QueryManualSections"]
    }
  ]
}
```

**Storage**:
- Option A: Add to `VSM_VlogCase` with `type="synthetic"`
- Option B: Create `VSM_TroubleshootingCase` collection
- Option C: Store in local JSON files for demo scenarios

**Recommendation**: **Option A** - Extend `VSM_VlogCase` with synthetic flag, or **Option B** - Create separate collection for clarity.

---

## Agent Integration

### Tool → Synthetic Data Usage

#### AnalyzeSensorPattern Tool
```python
async def analyze_sensor_pattern(current_worldstate, tree_data):
    # Query VSM_WorldStateSnapshot for similar patterns
    similar_patterns = query_snapshots(
        failure_modes=detect_failure_modes(current_worldstate),
        similarity_threshold=0.8
    )
    # Compare current state to reference patterns
    return pattern_analysis(current_worldstate, similar_patterns)
```

#### GetAssetHealth Tool
```python
async def get_asset_health(asset_id, tree_data):
    # Get Context (C) - design parameters from commissioning
    context = get_asset_context(asset_id)  # FD_Assets enriched
    # Compute WorldState (W) - current operating state
    worldstate = compute_worldstate(asset_id, now())
    # Compare W vs C - implements "balans" concept
    return balance_analysis(
        current=worldstate,
        design=context.commissioning_data,
        question="Is system operating within design parameters?"
    )
```

**Key Insight**: Manual's "gegevens bij inbedrijfstelling" (commissioning data) is what we call Context (C). GetAssetHealth implements the balance check: W vs C.

## Schema Definitions

### VSM_WorldStateSnapshot

**Purpose**: Reference patterns for AnalyzeSensorPattern tool

**Schema**:
```python
properties = [
    Property(name="snapshot_id", data_type=DataType.TEXT, filterable=True),
    Property(name="failure_mode", data_type=DataType.TEXT, filterable=True),
    Property(name="worldstate_json", data_type=DataType.TEXT),  # Full WorldState JSON
    Property(name="typical_pattern", data_type=DataType.TEXT),  # Vectorized
    Property(name="related_failure_modes", data_type=DataType.TEXT_ARRAY),
    Property(name="is_synthetic", data_type=DataType.BOOL, filterable=True),
]
```

**Size Estimate**: ~20-30 snapshots × ~2KB = **40-60 KB**

**Upload Priority**: **HIGH** (AnalyzeSensorPattern depends on it)

**Generation**: Extract from real events + manual descriptions of failure modes

---

#### 2. VSM_TroubleshootingCase (Optional - Demo Only)

**Purpose**: Complete case studies (synthetic or real) combining all data types

**Schema**:
```python
properties = [
    Property(name="case_id", data_type=DataType.TEXT, filterable=True),
    Property(name="title", data_type=DataType.TEXT),  # Vectorized
    Property(name="type", data_type=DataType.TEXT, filterable=True),  # "synthetic" or "real"
    Property(name="scenario", data_type=DataType.TEXT, filterable=True),  # "A3", "A1", etc.
    Property(name="problem", data_type=DataType.TEXT),  # Vectorized
    Property(name="root_cause", data_type=DataType.TEXT),  # Vectorized
    Property(name="solution", data_type=DataType.TEXT),  # Vectorized
    Property(name="smido_steps", data_type=DataType.TEXT_ARRAY, filterable=True),
    Property(name="data_sources", data_type=DataType.OBJECT),  # JSON with references
    Property(name="workflow", data_type=DataType.OBJECT),  # JSON with SMIDO workflow
]
```

**Size Estimate**: ~5-10 cases × ~3KB = **15-30 KB**

**Upload Priority**: **Low** (demo scenarios only, not used by agent tools)

---

### Updated Upload Sequence

See `DATA_UPLOAD_STRATEGY.md` for complete sequence. Synthetic data added in Phase 2:

**Phase 2: Synthetic Data (Agent References)**
1. **VSM_WorldStateSnapshot** - HIGH priority
   - Generate from real events (5-10 patterns for A1-A5 scenarios)
   - Required by AnalyzeSensorPattern tool
   
2. **Enrich FD_Assets** - HIGH priority
   - Add installation context for asset "135_1570"
   - Required by GetAssetHealth tool

---

## Implementation Plan

### Step 1: Generate WorldState Snapshots

**Script**: `features/telemetry_vsm/src/generate_worldstate_snapshots.py`

**Process**:
1. For each vlog case (A1-A5):
   - Find corresponding telemetry event in parquet
   - Compute WorldState at event peak
   - Extract "uit balans" factors (which design parameter violated?)
2. Add manual-described patterns:
   - "Condensatietemperatuur te hoog" (from balance section)
   - "Oververhitting te klein" (from balance section)
   - "Warmtebelasting te hoog" (from balance section)
3. Output: 8-12 reference snapshots (5 from vlogs + 3-7 from manual)

**Balance Factors** (from manual page 11):
- Koellast en koelvermogen mismatch
- Verdampercapaciteit vs temperatuur
- Compressorcapaciteit mismatch
- Condensorcapaciteit vs temperatuur
- Smoorventielcapaciteit
- Koudemiddel charge (too much/too little)

---

### Step 2: Enrich FD_Assets with Commissioning Data

**Script**: `features/integration_vsm/src/enrich_fd_assets.py`

**Process**:
1. Load existing FD_Assets collection
2. Add "gegevens bij inbedrijfstelling" (commissioning/design data):
   - Design temperatures and pressures (evaporator, condenser, suction, discharge)
   - Component capacities (compressor, evaporator, condenser matched)
   - Design operating limits (superheat, subcooling, ambient max, load max)
   - Control settings (defrost interval, thermostat setpoint, pressostat cutouts)
3. This becomes Context (C) that GetAssetHealth uses to check if W is within design limits

**No Alternative**: Must use FD_Assets (GetAssetHealth tool queries this collection).

---

### Step 3: Create Synthetic Troubleshooting Cases (Optional)

**Script**: `features/integration_vsm/src/create_synthetic_cases.py`

**Process**:
1. For each demo scenario (A1-A5):
   - Combine related telemetry events, manual sections, vlogs
   - Create complete workflow with SMIDO steps
   - Generate synthetic case object
2. Upload to `VSM_TroubleshootingCase` OR add to `VSM_VlogCase` with `type="synthetic"`

---

## Integration with Existing Strategy

### Updates to `DATA_UPLOAD_STRATEGY.md`

**Add Section**: "Synthetic Data & Context"

**Key Points**:
1. **FD_* collections** are separate MVP collections (already seeded)
2. **VSM_WorldStateSnapshot** collection for pattern matching
3. **FD_Assets enrichment** for installation context
4. **Synthetic troubleshooting cases** (optional, can use VSM_VlogCase)

**Cross-References**:
- Link WorldState snapshots to telemetry events
- Link synthetic cases to real data sources
- Use snapshots for fast pattern matching in agent queries

---

## Recommendations

### Immediate Actions

1. ✅ **Acknowledge FD_* collections** - Document that these are intentionally separate MVP collections
2. ⏳ **Create VSM_WorldStateSnapshot collection** - High value for agent pattern matching
3. ⏳ **Enrich FD_Assets** - Add VSM-specific installation context
4. ⏳ **Generate snapshots for A3 scenario** - Priority for demo

### Future Considerations

1. **Synthetic Troubleshooting Cases** - Can be added later if needed for demo
2. **More WorldState Snapshots** - Generate as more failure modes are identified
3. **Synthetic Telemetry Events** - Only if needed for testing (real events preferred)

---

## Summary

**Agent Tool Requirements**:
- **GetAssetHealth**: Needs C (design/commissioning data) → Enrich FD_Assets
- **AnalyzeSensorPattern**: Needs reference patterns → VSM_WorldStateSnapshot
- **Other 5 tools**: Real data only (no synthetic needed)

**Implementation Priority**:
1. **HIGH**: Enrich FD_Assets with commissioning data (C) - GetAssetHealth blocked
2. **HIGH**: Generate 8-12 WorldState snapshots - AnalyzeSensorPattern blocked
3. Upload as Phase 2 (after core collections)

**Key Insights from Manual**:
- "3-P's" section lists **4 P's** (including Productinput)
- "Balans" concept: compare W (current) vs C (design) - not all faults are broken components
- "Gegevens bij inbedrijfstelling" = commissioning data = our Context (C)

---

**Status**: ✅ Integrated with agent architecture  
**Priority**: HIGH (both tools blocked without synthetic data)

