# Plan 2: Simple Query Tools (GetAlarms, QueryTelemetryEvents, QueryVlogCases)

**Priority**: MEDIUM (Independent, can run in parallel with Plan 1)  
**Parallelization**: Fully independent  
**Estimated Time**: 2 hours

---

## Objective

Implement 3 simple VSM tools that query Weaviate collections for alarms, telemetry events, and vlog cases. These tools extend Elysia's Query tool with domain-specific filtering.

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md` (lines 195-206 - Tool definitions)
- `CLAUDE.md` (lines 509-521 - VSM Tool → Data Mapping table)

**Weaviate Collections**:
- `docs/data/DATA_UPLOAD_STRATEGY.md` (collection schemas):
  - VSM_TelemetryEvent (lines 89-141)
  - VSM_VlogCase (lines 199-230)
  - VSM_VlogClip (lines 239-275)

**Elysia Tool Pattern**:
- `elysia/api/custom_tools.py` (tool examples)
- `elysia/tools/retrieval/query.py` (Query tool - reference for Weaviate queries)

**Weaviate API**:
- `docs/data/WEAVIATE_API_NOTES.md` (Filter.by_property() examples)

---

## Implementation Tasks

### Task 2.1: GetAlarms Tool

**File**: `elysia/api/custom_tools.py` (add to file)

**Purpose**: Retrieve active alarms for asset from VSM_TelemetryEvent

**Implementation Spec**:
```python
@tool(status="Checking active alarms...", branch_id="smido_melding")
async def get_alarms(
    asset_id: str,
    severity: str = "all",  # "critical", "warning", "info", "all"
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Get active alarms for asset from VSM_TelemetryEvent collection.
    Used in: M (Melding), P1 (Power) nodes
    """
    # Query VSM_TelemetryEvent with Filter.by_property()
    # Filter by asset_id and severity
    # Sort by t_start descending
    # Return alarm objects
```

**SMIDO Nodes**: M (Melding), P1 (Power)

---

### Task 2.2: QueryTelemetryEvents Tool

**File**: `elysia/api/custom_tools.py`

**Purpose**: Find similar historical incidents from VSM_TelemetryEvent

**Implementation Spec**:
```python
@tool(status="Searching historical incidents...", branch_id="smido_diagnose")
async def query_telemetry_events(
    failure_mode: str = None,
    components: list = None,
    severity: str = None,
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Query historical telemetry events (similar incidents).
    Uses hybrid search if query provided, filter-only for structured search.
    Used in: P4 (Productinput), O (Onderdelen) nodes
    """
    # Build filters with Filter.by_property()
    # Query VSM_TelemetryEvent
    # Return incident objects with WorldState summaries
```

**SMIDO Nodes**: P4 (Productinput), O (Onderdelen)

---

### Task 2.3: QueryVlogCases Tool

**File**: `elysia/api/custom_tools.py`

**Purpose**: Find similar troubleshooting cases from video logs

**Implementation Spec**:
```python
@tool(status="Searching video case library...", branch_id="smido_onderdelen")
async def query_vlog_cases(
    problem_description: str = None,
    failure_mode: str = None,
    component: str = None,
    smido_step: str = None,
    limit: int = 3,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Query vlog cases for similar problem→solution workflows.
    Returns both VSM_VlogCase (aggregated) and VSM_VlogClip (detailed steps).
    Used in: O (Onderdelen) node
    """
    # Hybrid search on VSM_VlogCase with problem_description
    # Filter by failure_mode, component, smido_step
    # For each case, fetch related clips from VSM_VlogClip
    # Return case + clips with video paths
```

**SMIDO Nodes**: O (Onderdelen)

---

## Verification

**Success Criteria**:
- [ ] GetAlarms retrieves alarms filtered by severity
- [ ] QueryTelemetryEvents finds incidents by failure mode
- [ ] QueryVlogCases returns A3 case when querying "frozen evaporator"
- [ ] All tools integrate with Elysia tree (callable, yield Results)
- [ ] Proper Filter API usage (no deprecation warnings)

**Test Commands**:
```bash
# Test GetAlarms
python3 -c "import asyncio; from elysia.api.custom_tools import get_alarms; ..."

# Test QueryTelemetryEvents  
# Test QueryVlogCases (query for A3)
```

---

## Dependencies

**Required Before**:
- ✅ VSM collections uploaded (VSM_TelemetryEvent, VSM_VlogCase, VSM_VlogClip)
- ✅ Elysia preprocessing complete

**Blocks**:
- SMIDO node implementation (needs tools available)

---

## Related Files

**To Modify**:
- `elysia/api/custom_tools.py` (add 3 tools)

**To Reference**:
- `features/integration_vsm/src/validate_collections.py` (query examples)
- `docs/data/WEAVIATE_API_NOTES.md` (Filter patterns)


