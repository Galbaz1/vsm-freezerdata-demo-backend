# VSM Agent Implementation Plans

**Date**: November 11, 2024  
**Status**: Ready for Parallel Development  
**Phase 1 Status**: ✅ COMPLETE (Data uploaded to Weaviate)

---

## Plan Overview

7 implementation plans for building the complete VSM agent on top of Elysia framework.

---

## Parallelization Matrix

| Plan | Name | Can Start | Depends On | Est. Time |
|------|------|-----------|------------|-----------|
| **1** | WorldState Engine | ✅ Immediately | None | 2-3h |
| **2** | Simple Query Tools | ✅ Immediately | None | 2h |
| **3** | SearchManuals Tool | ✅ Immediately | None | 2h |
| **4** | Advanced Diagnostic Tools | After Plan 1 | WorldState Engine | 3h |
| **5** | SMIDO Nodes | ✅ Immediately | None (tools added later) | 3h |
| **6** | Orchestrator + Context | After 1-5 | All tools + nodes | 4h |
| **7** | A3 End-to-End Test | After 1-6 | Complete system | 2-3h |

**Total Sequential Time**: ~18-20 hours  
**Total Parallel Time**: ~10-12 hours (3 rounds of parallelization)

---

## Development Rounds

### Round 1: Independent Foundations (Parallel)

Develop simultaneously:
- **Branch 1**: WorldState Engine + Tool
- **Branch 2**: Simple Query Tools (GetAlarms, QueryTelemetryEvents, QueryVlogCases)
- **Branch 3**: SearchManualsBySMIDO Tool
- **Branch 5**: SMIDO Nodes (structure only, tools added later)

**Time**: ~3 hours parallel

---

### Round 2: Dependent Implementations

After Round 1 complete:
- **Branch 4**: Advanced Diagnostic Tools (needs WorldState Engine from Branch 1)

**Time**: ~3 hours

---

### Round 3: Integration

After Rounds 1-2 complete:
- **Branch 6**: SMIDO Orchestrator + Context Manager (needs all tools + nodes)

**Time**: ~4 hours

---

### Round 4: Validation

After Round 3 complete:
- **Branch 7**: A3 Scenario End-to-End Test

**Time**: ~2-3 hours

---

## Merge Order & Testing

See `00_MERGE_STRATEGY_AND_TESTING.md` for detailed merge sequence and post-merge tests.

**Critical Merge Order**:
1. Merge Branch 1 (WorldState Engine) → Test performance <500ms
2. Merge Branch 2 (Simple Tools) → Test Weaviate queries
3. Merge Branch 3 (SearchManuals) → Test opgave filtering
4. Merge Branch 4 (Advanced Tools) → Test W vs C comparison
5. Merge Branch 5 (SMIDO Nodes) → Test 4 P's structure
6. Merge Branch 6 (Orchestrator) → Test M→T→I→D→O flow
7. Merge Branch 7 (A3 Test) → Final integration test

---

## Plan Details

### Plan 1: WorldState Engine + ComputeWorldState Tool
**File**: `01_worldstate_engine_and_tool.md`

**Creates**:
- `features/telemetry_vsm/src/worldstate_engine.py` (60+ feature computation)
- ComputeWorldState tool in `elysia/api/custom_tools.py`

**Key Features**:
- Computes current state, trends (30m, 2h, 24h), flags, health scores
- On-demand computation from 785K row parquet
- Performance target: <500ms for 60min window

**Tests**: WorldState computation, tool registration, performance

---

### Plan 2: Simple Query Tools
**File**: `02_simple_query_tools.md`

**Creates**:
- GetAlarms tool (query VSM_TelemetryEvent by severity)
- QueryTelemetryEvents tool (find historical incidents)
- QueryVlogCases tool (find similar troubleshooting cases)

**Key Features**:
- Weaviate queries with Filter API
- Failure mode and component filtering
- Returns A3 case when querying "frozen evaporator"

**Tests**: Weaviate queries, A3 case retrieval, filter correctness

---

### Plan 3: SearchManualsBySMIDO Tool
**File**: `03_search_manuals_tool.md`

**Creates**:
- SearchManualsBySMIDO tool (SMIDO-aware manual search)

**Key Features**:
- SMIDO step filtering (power, procesinstellingen, procesparameters, productinput)
- Diagram integration (returns VSM_Diagram with manual sections)
- Opgave filtering (excludes test content by default)

**Tests**: SMIDO filtering, opgave exclusion, diagram retrieval

---

### Plan 4: Advanced Diagnostic Tools
**File**: `04_advanced_diagnostic_tools.md`

**Creates**:
- GetAssetHealth tool (W vs C comparison)
- AnalyzeSensorPattern tool (pattern matching)

**Key Features**:
- Implements "Koelproces uit balans" concept
- Compares WorldState (W) against Context (C)
- Detects out-of-balance factors
- Matches against reference patterns (VSM_WorldStateSnapshot)

**Tests**: W vs C comparison, pattern matching, frozen evaporator detection

**Depends On**: Plan 1 (WorldState Engine)

---

### Plan 5: SMIDO Decision Nodes
**File**: `05_smido_decision_nodes.md`

**Creates**:
- `features/vsm_tree/smido_tree.py` (complete SMIDO tree structure)

**Key Features**:
- 9 branches: M, T, I, D, P1, P2, P3, P4, O
- Proper from_branch_id hierarchy (M→T→I→D→O)
- 4 P's as sub-branches of D (not 3!)
- Tools assigned to correct branches

**Tests**: Tree structure, 4 P's verification, tool assignment

**Note**: Can start in parallel (tools added when they're available)

---

### Plan 6: SMIDO Orchestrator + Context Manager
**File**: `06_smido_orchestrator_and_context.md`

**Creates**:
- `features/vsm_tree/context_manager.py` (W/C separation)
- `features/vsm_tree/smido_orchestrator.py` (phase tracking)

**Key Features**:
- WorldState (W) vs Context (C) separation
- SMIDO phase progression (M→T→I→D→O)
- Phase skip logic (based on context)
- Integration with TreeData.environment

**Tests**: W/C separation, phase transitions, tree integration

**Depends On**: Plans 1-5 (all tools + nodes)

---

### Plan 7: A3 Scenario End-to-End Test
**File**: `07_a3_scenario_end_to_end_test.md`

**Creates**:
- `features/vsm_tree/tests/test_a3_scenario.py` (pytest suite)
- `scripts/demo_a3_scenario.py` (interactive demo)

**Key Features**:
- Complete SMIDO workflow (M→T→I→D→O)
- A3 frozen evaporator scenario
- All tools executed in sequence
- Solution validation

**Tests**: Complete workflow, frozen evaporator detection, solution accuracy

**Depends On**: Plans 1-6 (complete system)

---

## Success Criteria (After All Merges)

**Functional**:
- ✅ Agent follows SMIDO methodology (M→T→I→D→O)
- ✅ Agent computes WorldState features on-demand
- ✅ Agent finds relevant manuals, vlogs, incidents
- ✅ Agent provides actionable troubleshooting guidance

**Quality**:
- ✅ A3 scenario: Correctly identifies frozen evaporator
- ✅ 4 P's (not 3!) properly implemented
- ✅ "Uit balans" concept working (W vs C comparison)
- ✅ Test content (opgave) filterable

**Performance**:
- ✅ WorldState computation <500ms
- ✅ Weaviate queries <200ms
- ✅ End-to-end session <30 seconds

---

## Current Status

**Phase 1** (Data Upload): ✅ COMPLETE
- 221 objects uploaded to Weaviate
- 6 VSM collections created and preprocessed
- Synthetic data (snapshots + commissioning) generated
- Validation passed

**Phase 2** (Tool & Tree Implementation): 📝 READY TO START
- 7 plans created
- Parallelization strategy defined
- Merge order documented
- Tests specified

**Next Action**: Start parallel development of Branches 1, 2, 3, 5


