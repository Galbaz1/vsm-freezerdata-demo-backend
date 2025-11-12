<!-- ca71edda-5954-48e4-8847-390f58d462a4 8b80c09e-a618-4a6d-922b-43283176c491 -->
# Fix Diagram Search in searchmanualsby_smido

Fix diagram fetching in [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) to use correct collection names with intelligent fallback and performance optimization.

## Problem Analysis

**Root Cause**: Collection name mismatch

- Code searches: `VSM_Diagram` (DOES NOT EXIST)
- Reality: `VSM_DiagramUserFacing` (8 objects) + `VSM_DiagramAgentInternal` (8 objects)
- Result: Always returns "0 related diagrams"

**Reference**: [`.cursor/rules/agent.mdc`](.cursor/rules/agent.mdc) line 42: _"VSM_Diagram doesn't exist"_

## Expected Result

**BEFORE**:

- Searches non-existent `VSM_Diagram` → 0 diagrams
- Users see no visual aids

**AFTER**:

- Searches both `VSM_DiagramUserFacing` AND `VSM_DiagramAgentInternal`
- Falls back to SMIDO phase filtering if `related_diagram_ids` empty
- Batch fetches for performance (<500ms for 10 diagrams)
- Returns relevant diagrams (UserFacing for M, both for other phases)

## Implementation Strategy (4 Phases)

### Phase 1: Discovery & Verification (MANDATORY FIRST)

**Purpose**: Understand actual data structure before coding

**Step 1a: Verify Collections Exist**

**MANDATORY REFERENCE**: [`scripts/test_diagram_upload_simple.py`](scripts/test_diagram_upload_simple.py) lines 30-45

**Command**:

```bash
source .venv/bin/activate
python3 scripts/test_diagram_upload_simple.py
```

**Expected Output**:

```
✅ VSM_DiagramUserFacing: 8 diagrams
✅ VSM_DiagramAgentInternal: 8 diagrams
```

**If FAILS**: Diagrams not uploaded, this task blocked. Escalate.

**Step 1b: Check related_diagram_ids Population**

**MANDATORY**: Understand linking mechanism

**Command**:

```bash
python3 -c "
import asyncio
from elysia.util.client import ClientManager

async def check():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        coll = client.collections.get('VSM_ManualSections')
        results = await coll.query.fetch_objects(limit=50)
        
        with_ids = [obj for obj in results.objects 
                    if obj.properties.get('related_diagram_ids')]
        
        print(f'Sections with diagram IDs: {len(with_ids)}/50')
        print(f'Population rate: {len(with_ids)/50*100:.1f}%')
        
        # Show examples
        for obj in with_ids[:5]:
            ids = obj.properties.get('related_diagram_ids', [])
            title = obj.properties.get('title', 'Unknown')[:50]
            print(f'  \"{title}\": {ids}')
        
        # Check if empty
        if len(with_ids) == 0:
            print('\\n⚠️  WARNING: related_diagram_ids NOT populated!')
            print('   Will need fallback strategy (SMIDO phase matching)')

asyncio.run(check())
"
```

**Possible Outcomes**:

- **High population (>50%)**: Use `related_diagram_ids` as primary strategy
- **Low/Zero population**: Use SMIDO phase fallback (implemented in Step 2b)

**Step 1c: Inspect Diagram Schema**

**MANDATORY REFERENCE**: [`docs/archive/moved_docs/docs/review/weaviate_diagram_collections_analysis.md`](docs/archive/moved_docs/docs/review/weaviate_diagram_collections_analysis.md) lines 10-49

**What to verify**:

1. `VSM_DiagramUserFacing` has: `diagram_id`, `smido_phases`, `mermaid_code`, `agent_diagram_id`
2. `VSM_DiagramAgentInternal` has: `diagram_id`, `smido_phases`, `mermaid_code`
3. Both have filterable `smido_phases` (TEXT_ARRAY)

**Command**:

```bash
python3 -c "
import asyncio
from elysia.util.client import ClientManager

async def check():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        # Check UserFacing
        coll = client.collections.get('VSM_DiagramUserFacing')
        result = await coll.query.fetch_objects(limit=1)
        if result.objects:
            print('UserFacing properties:', list(result.objects[0].properties.keys()))
        
        # Check AgentInternal  
        coll = client.collections.get('VSM_DiagramAgentInternal')
        result = await coll.query.fetch_objects(limit=1)
        if result.objects:
            print('AgentInternal properties:', list(result.objects[0].properties.keys()))

asyncio.run(check())
"
```

**Decision Point**: After Phase 1, choose implementation strategy based on `related_diagram_ids` population rate.

---

### Phase 2: Implementation (Choose Strategy)

**Step 2a: Fix Collection Names (ALWAYS REQUIRED)**

**Location**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 160-189

**MANDATORY REFERENCE**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 160-189 (current implementation)

**Change**:

```python
# BEFORE (lines 165)
if await client.collections.exists("VSM_Diagram"):

# AFTER
user_exists = await client.collections.exists("VSM_DiagramUserFacing")
agent_exists = await client.collections.exists("VSM_DiagramAgentInternal")

if user_exists or agent_exists:
```

**Step 2b: Implement Dual-Strategy Fetching**

**Strategy A**: If `related_diagram_ids` populated (>50%)

```python
# Fetch by diagram_id (existing logic, but from both collections)
```

**Strategy B**: If `related_diagram_ids` empty or low (<50%)

```python
# Fallback: Fetch by SMIDO phase matching
if smido_step:
    # Map smido_step to smido_phases filter
    phase_map = {
        "melding": ["M", "melding"],
        "technisch": ["T", "technisch"],
        "installatie_vertrouwd": ["I", "installatie"],
        "3P_power": ["D", "P1", "power"],
        "3P_procesinstellingen": ["D", "P2", "procesinstellingen"],
        "3P_procesparameters": ["D", "P3", "procesparameters"],
        "3P_productinput": ["D", "P4", "productinput"],
        "ketens_onderdelen": ["O", "onderdelen"],
    }
    
    if smido_step in phase_map:
        phases = phase_map[smido_step]
        # Fetch diagrams where smido_phases contains ANY of phases
```

**Complete Implementation**:

```python
diagram_objects = []
if include_diagrams:
    yield Status("Fetching related diagrams...")
    
    # Check both collections exist
    user_exists = await client.collections.exists("VSM_DiagramUserFacing")
    agent_exists = await client.collections.exists("VSM_DiagramAgentInternal")
    
    if not (user_exists or agent_exists):
        yield Status("No diagram collections found")
        # Continue without diagrams
    else:
        # Strategy 1: Fetch by related_diagram_ids (if populated)
        diagram_ids = []
        for obj in results.objects:
            related_ids = obj.properties.get("related_diagram_ids", [])
            if related_ids:
                diagram_ids.extend(related_ids)
        
        if diagram_ids:
            # Batch fetch by IDs (PRIMARY STRATEGY)
            unique_ids = list(set(diagram_ids))
            
            if user_exists:
                user_coll = client.collections.get("VSM_DiagramUserFacing")
                # PERFORMANCE: Batch fetch instead of loop
                user_results = await user_coll.query.fetch_objects(
                    filters=Filter.by_property("diagram_id").contains_any(unique_ids),
                    limit=20
                )
                diagram_objects.extend(user_results.objects)
            
            if agent_exists:
                agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                agent_results = await agent_coll.query.fetch_objects(
                    filters=Filter.by_property("diagram_id").contains_any(unique_ids),
                    limit=20
                )
                diagram_objects.extend(agent_results.objects)
        
        # Strategy 2: Fallback to SMIDO phase matching (if no IDs found)
        elif smido_step:
            phase_map = {
                "melding": ["M", "melding"],
                "technisch": ["T", "technisch"],
                "installatie_vertrouwd": ["I", "installatie"],
                "3P_power": ["P1", "power"],
                "3P_procesinstellingen": ["P2", "procesinstellingen"],
                "3P_procesparameters": ["P3", "procesparameters"],
                "3P_productinput": ["P4", "productinput"],
                "ketens_onderdelen": ["O", "onderdelen"],
            }
            
            if smido_step in phase_map:
                phases = phase_map[smido_step]
                
                if user_exists:
                    user_coll = client.collections.get("VSM_DiagramUserFacing")
                    user_results = await user_coll.query.fetch_objects(
                        filters=Filter.by_property("smido_phases").contains_any(phases),
                        limit=5
                    )
                    diagram_objects.extend(user_results.objects)
                
                # Only fetch AgentInternal for non-M phases
                if agent_exists and smido_step != "melding":
                    agent_coll = client.collections.get("VSM_DiagramAgentInternal")
                    agent_results = await agent_coll.query.fetch_objects(
                        filters=Filter.by_property("smido_phases").contains_any(phases),
                        limit=5
                    )
                    diagram_objects.extend(agent_results.objects)
        
        yield Status(f"Found {len(diagram_objects)} related diagrams")
```

**Key Improvements**:

1. ✅ Batch fetching (`contains_any` instead of loop)
2. ✅ Dual strategy (IDs first, phase fallback)
3. ✅ Smart filtering (UserFacing only for M phase)
4. ✅ Performance optimized (<500ms)

---

### Phase 3: Testing & Validation

**Test 1: Collections Accessible**

```bash
python3 scripts/test_diagram_upload_simple.py
# Expected: ✅ Both collections, 8 objects each
```

**Test 2: Diagram Fetching (Unit Test)**

Create: `scripts/test_diagram_fetch.py`

```python
#!/usr/bin/env python3
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

async def test():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        # Test batch fetch
        user_coll = client.collections.get('VSM_DiagramUserFacing')
        
        # Test: Fetch by smido_phases
        result = await user_coll.query.fetch_objects(
            filters=Filter.by_property("smido_phases").contains_any(["M", "melding"]),
            limit=5
        )
        
        print(f'M-phase diagrams: {len(result.objects)}')
        for obj in result.objects:
            print(f'  - {obj.properties.get("title")}')
        
        assert len(result.objects) > 0, "Should find M-phase diagrams"
        print('✅ Diagram fetch test passed')

asyncio.run(test())
```

**Run**: `python3 scripts/test_diagram_fetch.py`

**Test 3: Integration Test (via search_manuals_by_smido)**

Create: `scripts/test_manual_diagram_integration.py`

```python
#!/usr/bin/env python3
import asyncio
from elysia import Tree
from elysia.util.client import ClientManager

async def test():
    tree = Tree(branch_initialisation="empty")
    cm = ClientManager()
    
    # Import tool
    from elysia.api.custom_tools import search_manuals_by_smido
    
    # Call with SMIDO step
    results = []
    async for item in search_manuals_by_smido(
        query="verdamper",
        smido_step="3P_procesparameters",
        include_diagrams=True,
        tree_data=tree.tree_data,
        client_manager=cm
    ):
        results.append(item)
    
    # Check Result object
    from elysia.objects import Result
    result_obj = [r for r in results if isinstance(r, Result)]
    
    if result_obj:
        metadata = result_obj[0].metadata
        diagram_count = metadata.get('diagram_count', 0)
        print(f'Diagrams returned: {diagram_count}')
        
        if diagram_count > 0:
            diagrams = metadata.get('diagrams', [])
            print(f'Diagram details: {len(diagrams)} objects')
            for d in diagrams[:2]:
                print(f'  - {d.get("title")} (ID: {d.get("diagram_id")})')
            print('✅ Integration test PASSED')
        else:
            print('⚠️  No diagrams returned (may be expected if related_diagram_ids empty)')
    
    await cm.close_clients()

asyncio.run(test())
```

**Run**: `python3 scripts/test_manual_diagram_integration.py`

**Expected**: >0 diagrams if either strategy works

---

### Phase 4: Documentation & Cleanup

**Update**: [`.cursor/rules/agent.mdc`](.cursor/rules/agent.mdc)

- Add note: "Diagram search uses dual strategy: related_diagram_ids OR smido_phases fallback"

**Update**: [`docs/project/PROJECT_TODO.md`](docs/project/PROJECT_TODO.md)

- Mark task #2 as completed

---

## Acceptance Criteria (STRICT)

**MUST PASS ALL**:

1. ✅ Code searches `VSM_DiagramUserFacing` (not `VSM_Diagram`)
2. ✅ Code searches `VSM_DiagramAgentInternal` (not `VSM_Diagram`)
3. ✅ Batch fetching implemented (`contains_any`, not loop)
4. ✅ Fallback strategy works if `related_diagram_ids` empty
5. ✅ No errors when either collection missing
6. ✅ `test_diagram_fetch.py` passes
7. ✅ `test_manual_diagram_integration.py` returns >0 diagrams
8. ✅ Performance <500ms for fetching 10 diagrams

## Files to Modify

**Primary**:

- [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 160-189 (~30 lines changed)

**New Test Files**:

- `scripts/test_diagram_fetch.py` (new, ~30 lines)
- `scripts/test_manual_diagram_integration.py` (new, ~40 lines)

## Risk Mitigation

**Risk 1**: Both strategies fail (IDs empty AND phase matching empty)

- **Mitigation**: Return 0 diagrams gracefully, log warning

**Risk 2**: Performance degradation (2 collection queries)

- **Mitigation**: Batch fetching, limit to 20 diagrams total

**Risk 3**: Frontend breaks if metadata format changes

- **Mitigation**: Metadata format unchanged (still `diagrams` array)

## Reference Documents (READ IN ORDER)

1. [`.cursor/rules/agent.mdc`](.cursor/rules/agent.mdc) lines 30-42 - Collection names
2. [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 160-220 - Current code
3. [`docs/archive/moved_docs/docs/review/weaviate_diagram_collections_analysis.md`](docs/archive/moved_docs/docs/review/weaviate_diagram_collections_analysis.md) - Schemas
4. [`scripts/test_diagram_upload_simple.py`](scripts/test_diagram_upload_simple.py) - Validation pattern

### To-dos

- [ ] MANDATORY: Run test_diagram_upload_simple.py to verify both collections exist (8 objects each).
- [ ] MANDATORY: Check related_diagram_ids population rate in VSM_ManualSections (determines primary vs fallback strategy).
- [ ] MANDATORY: Verify both collections have diagram_id, smido_phases, mermaid_code properties.
- [ ] MANDATORY: Read elysia/api/custom_tools.py lines 160-220 to understand current diagram fetching logic.
- [ ] Replace VSM_Diagram with VSM_DiagramUserFacing + VSM_DiagramAgentInternal checks.
- [ ] Replace one-by-one fetching with batch fetch using Filter.contains_any() for performance.
- [ ] Add SMIDO phase matching fallback if related_diagram_ids empty or unpopulated.
- [ ] Create scripts/test_diagram_fetch.py to test direct diagram queries by smido_phases.
- [ ] Create scripts/test_manual_diagram_integration.py to test search_manuals_by_smido with diagrams.
- [ ] Run test_diagram_fetch.py, verify >0 diagrams returned for M-phase query.
- [ ] Run test_manual_diagram_integration.py, verify diagrams in metadata with correct format.
- [ ] Measure diagram fetch time, ensure <500ms for 10 diagrams (batch vs loop improvement).