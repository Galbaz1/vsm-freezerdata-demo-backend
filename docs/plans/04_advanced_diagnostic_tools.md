# Plan 4: Advanced Diagnostic Tools (GetAssetHealth, AnalyzeSensorPattern)

**Priority**: HIGH (Critical for "uit balans" detection)  
**Parallelization**: Depends on Plan 1 (WorldState Engine)  
**Estimated Time**: 3 hours

---

## Objective

Implement GetAssetHealth and AnalyzeSensorPattern tools that implement the "Koelproces uit balans" concept by comparing WorldState (W) against Context (C) and detecting known failure patterns.

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md` (lines 197-207 - Tool definitions)
- `docs/data/SYNTHETIC_DATA_STRATEGY.md` (lines 119-168 - Context C definition, lines 264-296 - Tool integration)
- `CLAUDE.md` (lines 362-379 - WorldState W vs Context C definition)

**Manual Context**:
- `features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/storingzoeken-koeltechniek_theorie_179.text_chunks.jsonl` (balance section, grep "balans")

**Data Sources**:
- `features/integration_vsm/output/fd_assets_enrichment.json` (commissioning data - Context C)
- `features/telemetry_vsm/output/worldstate_snapshots.jsonl` (reference patterns)

**WorldState Engine**:
- `features/telemetry_vsm/src/worldstate_engine.py` (from Plan 1)

---

## Implementation Tasks

### Task 4.1: GetAssetHealth Tool

**File**: `elysia/api/custom_tools.py`

**Purpose**: Compare WorldState (W) against Context (C) to detect "uit balans"

**Implementation Spec**:

```python
@tool(status="Computing asset health (W vs C)...", branch_id="smido_diagnose")
async def get_asset_health(
    asset_id: str,
    timestamp: str = None,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Compare WorldState (W) against Context (C) - implements balance check.
    
    Returns:
    - Health summary
    - Out of balance factors
    - Recommended actions
    
    Used in: M (Melding), T (Technisch), P2 (Procesinstellingen) nodes
    """
    yield Status("Loading installation context (C)...")
    
    # 1. Get Context (C) from FD_Assets
    async with client_manager.connect_to_async_client() as client:
        assets = client.collections.get("FD_Assets")
        result = await assets.query.fetch_objects(
            filters=Filter.by_property("asset_id").equal("FZ-123"),
            limit=1
        )
        if not result.objects:
            yield Result(objects=[], metadata={"error": "Asset not found"})
            return
        
        # Parse commissioning data
        asset_props = result.objects[0].properties
        # Note: commissioning_data might be JSON string, parse if needed
    
    yield Status("Computing current WorldState (W)...")
    
    # 2. Compute WorldState (W) - use WorldStateEngine
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    ts = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    worldstate = engine.compute_worldstate(asset_id, ts, 60)
    
    yield Status("Comparing W vs C (balance check)...")
    
    # 3. Compare W vs C - balance check
    # Load commissioning data from enrichment file
    import json
    with open("features/integration_vsm/output/fd_assets_enrichment.json") as f:
        context = json.load(f)
    
    commissioning = context["commissioning_data"]
    balance_params = context["balance_check_parameters"]
    
    # Check if values are within design parameters
    out_of_balance = []
    
    # Room temp check
    current_temp = worldstate["current_state"]["room_temp"]
    target_temp = commissioning["target_temp"]
    if abs(current_temp - target_temp) > 5:
        out_of_balance.append({
            "factor": "room_temperature",
            "current": current_temp,
            "design": target_temp,
            "deviation": current_temp - target_temp,
            "severity": "critical" if current_temp > -10 else "warning"
        })
    
    # Hot gas temp check
    hot_gas = worldstate["current_state"]["hot_gas_temp"]
    if hot_gas < balance_params["hot_gas_temp_min_C"] or hot_gas > balance_params["hot_gas_temp_max_C"]:
        out_of_balance.append({
            "factor": "hot_gas_temperature",
            "current": hot_gas,
            "design_range": f"{balance_params['hot_gas_temp_min_C']}-{balance_params['hot_gas_temp_max_C']}",
            "severity": "warning"
        })
    
    # More checks: suction temp, pressures, etc.
    
    # Generate health summary
    health = {
        "asset_id": asset_id,
        "timestamp": ts.isoformat(),
        "overall_health": "uit_balans" if out_of_balance else "in_balance",
        "out_of_balance_factors": out_of_balance,
        "worldstate": worldstate,
        "commissioning_data": commissioning,
        "recommendations": []
    }
    
    # Generate recommendations based on out-of-balance factors
    if out_of_balance:
        for factor in out_of_balance:
            if factor["factor"] == "room_temperature":
                health["recommendations"].append("Check koelproces balance: temperatuur te hoog")
    
    yield Result(
        objects=[health],
        metadata={"balance_check": "completed", "factors_checked": len(balance_params)}
    )
```

**SMIDO Nodes**: M (Melding), T (Technisch), P2 (Procesinstellingen)

---

### Task 4.2: AnalyzeSensorPattern Tool

**File**: `elysia/api/custom_tools.py`

**Purpose**: Detect if current WorldState matches known "uit balans" patterns

**Implementation Spec**:

```python
@tool(status="Analyzing sensor patterns...", branch_id="smido_diagnose")
async def analyze_sensor_pattern(
    asset_id: str,
    timestamp: str = None,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Match current WorldState against reference patterns (VSM_WorldStateSnapshot).
    Detects if system is "uit balans" and identifies which failure mode.
    
    Used in: P3 (Procesparameters), P4 (Productinput) nodes
    """
    yield Status("Computing current WorldState...")
    
    # 1. Compute current WorldState (W)
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    ts = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
    engine = WorldStateEngine("features/telemetry/timeseries_freezerdata/135_1570_cleaned_with_flags.parquet")
    worldstate = engine.compute_worldstate(asset_id, ts, 60)
    
    yield Status("Querying reference patterns...")
    
    # 2. Query VSM_WorldStateSnapshot for similar patterns
    async with client_manager.connect_to_async_client() as client:
        snapshots = client.collections.get("VSM_WorldStateSnapshot")
        
        # Semantic search on typical_pattern
        ws_summary = f"Room: {worldstate['current_state']['room_temp']}°C, "
        ws_summary += f"HotGas: {worldstate['current_state']['hot_gas_temp']}°C, "
        ws_summary += f"Trend: {worldstate['trends_30m']['room_temp_delta']}°C/30min"
        
        results = await snapshots.query.near_text(
            query=ws_summary,
            limit=3
        )
    
    yield Status(f"Found {len(results.objects)} similar patterns")
    
    # 3. Match patterns - find best match
    matches = []
    for snapshot in results.objects:
        props = snapshot.properties
        match = {
            "snapshot_id": props.get("snapshot_id"),
            "failure_mode": props.get("failure_mode"),
            "typical_pattern": props.get("typical_pattern"),
            "balance_factors": props.get("balance_factors", []),
            "uit_balans_type": props.get("uit_balans_type"),
            "similarity_score": 0.8  # Placeholder - can compute actual similarity
        }
        matches.append(match)
    
    # 4. Generate analysis
    analysis = {
        "current_worldstate": worldstate,
        "matched_patterns": matches,
        "detected_failure_mode": matches[0]["failure_mode"] if matches else None,
        "is_uit_balans": matches[0]["uit_balans_type"] != "in_balance" if matches else False,
        "balance_factors_violated": matches[0]["balance_factors"] if matches else []
    }
    
    yield Result(
        objects=[analysis],
        metadata={"patterns_checked": len(results.objects), "best_match": matches[0]["failure_mode"] if matches else None}
    )
```

**SMIDO Nodes**: P3 (Procesparameters), P4 (Productinput)

---

## Verification

**Success Criteria**:
- [ ] GetAssetHealth compares W vs C correctly
- [ ] Out-of-balance factors identified (room temp, hot gas, pressures)
- [ ] AnalyzeSensorPattern matches frozen evaporator pattern for A3 scenario
- [ ] Both tools integrate with tree_data.environment
- [ ] Recommendations generated based on balance violations

**Test Scenarios**:
```python
# Test 1: A3 frozen evaporator
# Expected: Matches ws_frozen_evaporator_A3 snapshot
# Expected: Out of balance - room temp too high, suction extreme

# Test 2: Normal operation
# Expected: Matches ws_normal_operation snapshot
# Expected: In balance - no violations

# Test 3: High condensation temp (P4 - Productinput)
# Expected: Matches ws_high_condensation_temp snapshot
# Expected: Out of balance - ambient temp issue
```

---

## Dependencies

**Required Before**:
- ✅ VSM_WorldStateSnapshot uploaded (13 snapshots)
- ✅ FD_Assets enriched with commissioning data
- ⏳ WorldState Engine implemented (Plan 1)

**Blocks**:
- P2, P3, P4 node implementation (needs these tools)

---

## Related Files

**To Modify**:
- `elysia/api/custom_tools.py` (add 2 tools)

**To Create**:
- Tests for balance detection

**To Reference**:
- `features/integration_vsm/output/fd_assets_enrichment.json`
- `features/telemetry_vsm/output/worldstate_snapshots.jsonl`
- `docs/diagrams/system/balance_diagram.mermaid` (visual reference for balance concept)


