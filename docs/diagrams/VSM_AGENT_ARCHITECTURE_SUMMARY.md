# VSM Agent Architecture - Quick Summary

**Date**: January 11, 2025  
**Status**: Proposed Architecture  
**Full Documentation**: See `VSM_AGENT_ARCHITECTURE_MOTIVATION.md`

---

## Architecture Overview

The VSM agent architecture **intelligently extends Elysia** with VSM-specific layers for SMIDO methodology, WorldState computation, and multi-source data integration.

### Core Strategy: "Part Adding, Part Replacing"

- **✅ REUSE**: Elysia Tree engine, tool system, DSPy integration, Weaviate client
- **✅ ADD**: SMIDO orchestrator, WorldState engine, VSM domain tools
- **✅ ENHANCE**: Context management, hybrid data architecture

---

## Architecture Diagram

See `vsm_agent_architecture.mermaid` for complete visual diagram.

**Key Layers**:
1. **User Interface** - VSM Dashboard (extends Elysia frontend)
2. **VSM Orchestration** - SMIDO workflow coordination
3. **SMIDO Decision Tree** - M→T→I→D→O mapped to Elysia DecisionNodes
4. **VSM Domain Tools** - 7 custom tools for troubleshooting
5. **Elysia Core** - Reused tree engine, query tool, DSPy
6. **Data Computation** - WorldState engine, parquet reader
7. **Weaviate Collections** - Semantic search (manuals, vlogs, incidents)
8. **Local Data Storage** - Raw data (parquet, JSONL, videos)
9. **LLM Layer** - DSPy with multi-model routing

---

## Key Design Decisions

### 1. Extend Elysia Tree (Don't Replace)
- **Why**: Elysia's tree engine handles recursion, error recovery, tool orchestration perfectly
- **How**: Create VSM Tree instance that extends `elysia.Tree` with SMIDO initialization

### 2. SMIDO as Decision Nodes
- **Why**: Direct mapping to Elysia's decision tree structure
- **How**: Each SMIDO phase (M, T, I, D, O) is a DecisionNode with specific tools

### 3. Hybrid Data Architecture
- **Weaviate**: Semantic search (discovery) - ~1000 incidents, ~240 manual sections
- **Parquet**: Time-series computation (WorldState) - 785K datapoints
- **Why**: Each tool uses the right data source for its purpose

### 4. WorldState (W) vs Context (C) Split
- **W (WorldState)**: Dynamic state (sensors, observations, measurements) - computed on-demand
- **C (Context)**: Static design data (commissioning parameters, schemas, history) - stored in FD_Assets
- **Balance Check**: Compare W vs C to detect "uit balans" (operating outside design parameters)

### 5. VSM Domain Tools (7 tools)
- **Real Data**: ComputeWorldState, QueryTelemetryEvents, SearchManualsBySMIDO, QueryVlogCases, GetAlarms
- **Need Synthetic**: GetAssetHealth (needs C), AnalyzeSensorPattern (needs reference patterns)
- **Key Concept**: GetAssetHealth compares W vs C, AnalyzeSensorPattern detects "uit balans" patterns

---

## SMIDO Workflow Mapping

```
SMIDO Phase              →  Elysia DecisionNode  →  Tools  →  Data (W/C)
─────────────────────────────────────────────────────────────────────────────────────────
M - Melding              →  M_Node              →  GetAlarms, GetAssetHealth  →  W+C
T - Technisch            →  T_Node              →  GetAssetHealth, SearchManuals  →  W+C
I - Installatie          →  I_Node              →  SearchManuals (schemas)  →  C
D - Diagnose (4 P's)     →  D_Node (branch)     →  
  ├─ P1: Power           →  P1_Node            →  GetAlarms, ComputeWorldState  →  W
  ├─ P2: Procesinstellingen → P2_Node          →  SearchManuals, GetAssetHealth  →  C (compare)
  ├─ P3: Procesparameters   → P3_Node          →  ComputeWorldState, AnalyzeSensorPattern  →  W vs Snapshots
  └─ P4: Productinput       → P4_Node          →  QueryTelemetryEvents, AnalyzeSensorPattern  →  W (external)
O - Onderdelen           →  O_Node              →  QueryVlogCases, SearchManuals  →  W+manuals
```

**W = WorldState** (dynamic): Current sensors, technician observations, measurements  
**C = Context** (static): Design parameters, commissioning data, schemas, normal values

---

## Data Flow Example: A3 "Frozen Evaporator" Scenario

1. **User Query**: "Koelcel bereikt temperatuur niet"
2. **M_Node**: Collect symptoms → GetAlarms → Active alarms found
3. **T_Node**: Visual check → No obvious defect
4. **I_Node**: Technician familiar → Skip to D
5. **D_Node → P3_Node**: 
   - ComputeWorldState → Reads parquet, computes features
   - Detects: `flag_main_temp_high=True`, `flag_suction_extreme=True`
   - AnalyzeSensorPattern → Detects frozen evaporator pattern
6. **O_Node**:
   - QueryVlogCases → Finds A3 case (frozen evaporator)
   - SearchManualsBySMIDO → Finds manual page ~7 ("Koelproces uit balans")
7. **Solution**: Manual defrost + clean air ducts + calibrate thermostat

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- Extend Elysia Tree with VSM initialization
- Create SMIDO DecisionNodes
- Implement Context Manager
- Create basic VSM tools (stubs)

### Phase 2: Data Integration (Week 3-4)
- Implement WorldState Engine
- Create Parquet Reader
- Import data to Weaviate
- Implement event detection

### Phase 3: Tool Implementation (Week 5-6)
- Implement all 7 VSM tools
- Integrate with Elysia Query tool
- Test tool execution

### Phase 4: SMIDO Workflow (Week 7-8)
- Implement SMIDO Orchestrator
- Connect SMIDO nodes with tools
- Test SMIDO workflow (A3 scenario)

### Phase 5: Demo & Polish (Week 9-10)
- Create demo scenarios
- UI enhancements
- Performance optimization
- Documentation

---

## Success Criteria

- ✅ Agent follows SMIDO methodology (M→T→I→D→O)
- ✅ Agent computes WorldState features on-demand
- ✅ Agent finds relevant manuals, vlogs, incidents
- ✅ Agent provides actionable troubleshooting guidance
- ✅ A3 scenario: Correctly identifies frozen evaporator
- ✅ Performance: WorldState < 500ms, Weaviate < 200ms

---

## Key Files

- **Architecture Diagram**: `docs/diagrams/vsm_agent_architecture.mermaid`
- **Full Motivation**: `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md`
- **This Summary**: `docs/diagrams/VSM_AGENT_ARCHITECTURE_SUMMARY.md`

---

## Next Steps

1. Review architecture with team
2. Validate design decisions
3. Begin Phase 1 implementation
4. Test with A3 scenario

