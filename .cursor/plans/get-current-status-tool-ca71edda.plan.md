<!-- ca71edda-5954-48e4-8847-390f58d462a4 07968d79-1d53-4717-bbdd-396f4472c5fd -->
# Rewrite VSM Bootstrap - Flat Root Architecture (Modular)

Completely rewrite [`features/vsm_tree/bootstrap.py`](features/vsm_tree/bootstrap.py) using 4 focused, modular functions to implement Weaviate's flat root philosophy.

## Expected Result

**BEFORE**: Deep hierarchy (M→T→I→D[P1-P4]→O), 9 branches, NO native tools, 400+ lines

**AFTER**: Flat root with 12 tools, post-tool chains, native tools integrated, ~200 lines

**Tree structure:**

```
base (root) — 12 tools visible
├── get_current_status, get_alarms, compute_worldstate, etc.
├── query, aggregate, visualise (native)
├── Post-tool chains: get_alarms → [health, manuals]
└── Post-tool chains: compute_worldstate → [analyze, visualise]
```

---

## Task 1: Read and Internalize Weaviate's one_branch Pattern

**MANDATORY REFERENCE**: [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 250-266

**What to do**:

1. Read `one_branch_init()` function completely
2. Note the pattern: ALL tools at `branch_id="base"`
3. Note the root instruction style: "Decide based on tools available and their descriptions"
4. Count tools: 5 tools (CitedSummarizer, FakeTextResponse, Aggregate, Query, Visualise)
5. Note `from_tool_ids` usage: SummariseItems after query (line 266)

**Success**: You can explain Weaviate's one_branch pattern without looking at code

---

## Task 2: Read multi_branch Pattern for Comparison

**MANDATORY REFERENCE**: [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 214-248

**What to do**:

1. Read `multi_branch_init()` completely
2. Identify the structure: `base` branch → `search` sub-branch
3. Count depth: 2 levels max (root + 1 sub-branch)
4. Note how tools are split: text tools at base, data tools in search
5. Compare with VSM current (5+ levels) - VSM violates this pattern

**Success**: You understand WHY VSM needs to change (5 levels → 2 levels max)

---

## Task 3: Study from_tool_ids Pattern

**MANDATORY REFERENCES**:

- [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 684-727 (add_tool implementation)
- [`docs/offical/Advanced/advanced_tool_construction.md`](docs/offical/Advanced/advanced_tool_construction.md) lines 181-189

**What to do**:

1. Read how `from_tool_ids` creates new branches dynamically
2. Understand: `from_tool_ids=["query"]` means "run after query completes"
3. Note: multiple parents allowed (line 217 in IMPROVED_VSM_BRANCHING_STRATEGY.md)
4. Example: `tree.add_tool(Visualise, branch_id="base", from_tool_ids=["compute_worldstate", "query"])`

**Success**: You can explain how post-tool chains replace pre-defined branches

---

## Task 4: Review VSM Strategy Document

**MANDATORY REFERENCE**: [`docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md`](docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md) lines 70-223

**What to do**:

1. Read the complete bootstrap code example (lines 72-223)
2. Identify the 4 sections: Root instruction, Root tools, Post-tool chains, Visualization chains
3. Note specific tool chains: get_alarms → [get_asset_health, search_manuals] (lines 146-162)
4. Note multi-parent visualise: after 4 different tools (lines 217-222)

**Success**: You have the complete reference implementation in mind

---

## Task 5: Create _register_root_tools() Function

**MANDATORY PATTERN**: Follow [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 261-265 (one_branch tool registration)

**What to write**:

```python
def _register_root_tools(tree: Tree) -> None:
    """Register all core tools at base root following one_branch pattern."""
    # Import 8 VSM tools from elysia.api.custom_tools
    # Import 4 native: Query, Aggregate, CitedSummarizer, FakeTextResponse
    # Add EVERY tool with branch_id="base" (NO from_tool_ids here)
    # Order: Always-available first, then VSM tools, then native tools
```

**Files to reference while coding**:

- VSM tool imports: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 48-1106 (all @tool definitions)
- Native tool imports: [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 6-13 (import statements)

**Success**: Function adds exactly 12 tools, all at branch_id="base"

---

## Task 6: Create _add_smido_post_tool_chains() Function

**MANDATORY PATTERN**: Follow [`elysia/tree/tree.py`](elysia/tree/tree.py) line 248 (SummariseItems with from_tool_ids)

**MANDATORY REFERENCE**: [`docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md`](docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md) lines 144-214

**What to write**:

```python
def _add_smido_post_tool_chains(tree: Tree) -> None:
    """Add SMIDO workflow chains using from_tool_ids pattern."""
    # M flow: After get_alarms completes
    tree.add_tool(get_asset_health, branch_id="base", from_tool_ids=["get_alarms"])
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["get_alarms"])
    
    # P3 flow: After compute_worldstate completes
    tree.add_tool(analyze_sensor_pattern, branch_id="base", from_tool_ids=["compute_worldstate"])
    
    # O flow: After query_vlog_cases completes
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["query_vlog_cases"])
    tree.add_tool(Aggregate, branch_id="base", from_tool_ids=["query_vlog_cases"])
```

**Reference implementation**: Lines 177-214 of IMPROVED_VSM_BRANCHING_STRATEGY.md

**Success**: 3 SMIDO flows implemented (M, P3, O) using from_tool_ids

---

## Task 7: Create _add_visualization_chains() Function

**MANDATORY PATTERN**: Multi-parent from_tool_ids (Visualise after multiple tools)

**MANDATORY REFERENCE**: [`docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md`](docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md) lines 217-222

**What to write**:

```python
def _add_visualization_chains(tree: Tree) -> None:
    """Make Visualise available after any data-producing tool."""
    from elysia.tools.visualisation.visualise import Visualise
    
    # Multi-parent pattern: Visualise available after 4 different tools
    data_tools = ["compute_worldstate", "get_asset_health", "query", "aggregate"]
    for tool_id in data_tools:
        tree.add_tool(Visualise, branch_id="base", from_tool_ids=[tool_id])
```

**Why this pattern**: Visualization is cross-cutting, not SMIDO-specific

**Success**: Visualise added 4 times with different from_tool_ids

---

## Task 8: Create _set_root_instruction() Function

**MANDATORY PATTERN**: Follow [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 254-258 (one_branch instruction)

**MANDATORY REFERENCE**: [`docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md`](docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md) lines 93-121

**What to write**:

```python
def _set_root_instruction(tree: Tree) -> None:
    """Set clear root instruction following one_branch style."""
    tree.decision_nodes["base"].instruction = """
Choose tool based on user's immediate need.
Decide based on tools available and their descriptions.
Read them thoroughly and match actions to user prompt.

**Quick checks**: get_current_status, get_alarms
**Deep analysis**: compute_worldstate, get_asset_health, analyze_sensor_pattern
**Search knowledge**: search_manuals_by_smido, query_vlog_cases, query
**Statistics**: aggregate
**Visualization**: visualise (after data tools)
**Communicate**: cited_summarize, text_response

After a tool completes, more tools may become available.
"""
```

**Key principle**: NO keyword detection. Trust LLM to read tool descriptions.

**Success**: Instruction groups tools by purpose, <20 lines, mirrors one_branch style

---

## Task 9: Rewrite vsm_smido_bootstrap() Orchestrator

**MANDATORY PATTERN**: Simple orchestrator calling helper functions

**What to write**:

```python
def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
    """
    Bootstrap VSM following Weaviate's one_branch flat root pattern.
    
    Replaces deep SMIDO hierarchy with:
    - Flat root (all 12 tools visible at base)
    - Post-tool chains for SMIDO flows
    - Native Elysia tools integrated
    """
    logger.info("Bootstrapping VSM with flat root architecture...")
    
    # 1. Register all tools at base (one_branch pattern)
    _register_root_tools(tree)
    
    # 2. Add SMIDO workflow chains (from_tool_ids pattern)
    _add_smido_post_tool_chains(tree)
    
    # 3. Add visualization chains (multi-parent pattern)
    _add_visualization_chains(tree)
    
    # 4. Set clear root instruction
    _set_root_instruction(tree)
    
    logger.info(f"VSM flat root bootstrapped: {len(tree.decision_nodes['base'].options)} tools at root")
```

**Success**: Orchestrator is <25 lines, calls 4 functions, logs result

---

## Task 10: Delete Hierarchical Branch Functions

**Files to modify**: [`features/vsm_tree/smido_tree.py`](features/vsm_tree/smido_tree.py)

**What to delete**: Lines ~100-517

- `_add_m_branch()` (lines ~101-142)
- `_add_t_branch()` (lines ~144-177)
- `_add_i_branch()` (lines ~180-230)
- `_add_d_branch()` (lines ~232-380, includes P1-P4)
- `_add_o_branch()` (lines ~382-425)
- `_assign_tools_to_branches()` (lines ~428-517)

**What to keep**:

- Lines 1-99: Imports, docstring, `create_vsm_tree()`
- Update `create_vsm_tree()`: Remove calls to deleted functions (lines 75-82)

**Success**: smido_tree.py reduced from ~520 lines to ~100 lines

---

## Task 11: Remove branch_id from Tool Decorators

**Files to modify**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py)

**MANDATORY REFERENCE**: [`elysia/objects.py`](elysia/objects.py) lines 257-264 (@tool decorator signature)

**What to change**: Find all `@tool(branch_id=...)` decorators and remove `branch_id` parameter

**Tools to update** (search for these):

- `search_manuals_by_smido` (line ~48)
- `get_alarms` (search pattern: `@tool.*branch_id`)
- `get_asset_health`
- `compute_worldstate`
- `query_telemetry_events`
- `query_vlog_cases`
- `analyze_sensor_pattern`
- `get_current_status`

**Pattern**:

```python
# BEFORE
@tool(status="Searching manuals...", branch_id="smido_installatie")

# AFTER
@tool(status="Searching manuals...")
```

**Why**: Tools are branch-agnostic. Bootstrap assigns branch placement.

**Success**: Zero `branch_id` parameters in @tool decorators

---

## Task 12: Comprehensive Testing and Validation

**Test 1 - Bootstrap Structure** (MANDATORY):

```bash
python3 -c "
from features.vsm_tree.bootstrap import bootstrap_tree
from elysia import Tree
t = Tree(branch_initialisation='empty')
bootstrap_tree(t, ['vsm_smido'], {})
print(f'Tools at root: {len(t.decision_nodes[\"base\"].options)}')
assert len(t.decision_nodes['base'].options) == 12, 'Expected 12 tools at root'
print('✅ Bootstrap structure valid')
"
```

**Test 2 - Quick Status Flow**:

```bash
pytest scripts/test_quick_status_flow.py -v
# Expected: PASS, <200ms
```

**Test 3 - A3 SMIDO Scenario**:

```bash
python3 scripts/test_plan7_full_tree.py
# Expected: PASS, frozen evaporator diagnosis completes
```

**Test 4 - Manual Tests** (via Elysia UI):

1. Start Elysia: `elysia start`
2. Ask: "Hoeveel manual sections zijn er?" → Verify `aggregate` or `query` available
3. Request alarms → After `get_alarms`, verify `get_asset_health` available
4. Request WorldState → After `compute_worldstate`, verify `analyze_sensor_pattern` + `visualise` available

**Success**: All 4 test categories pass

---

## Reference Documents (READ BEFORE CODING)

**MANDATORY READING ORDER**:

1. [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 250-266 (one_branch pattern)
2. [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 214-248 (multi_branch pattern)
3. [`elysia/tree/tree.py`](elysia/tree/tree.py) lines 684-727 (from_tool_ids implementation)
4. [`docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md`](docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md) lines 70-223 (VSM implementation)
5. [`docs/offical/Advanced/advanced_tool_construction.md`](docs/offical/Advanced/advanced_tool_construction.md) lines 181-189 (from_tool_ids usage)

**ALWAYS cross-reference**: When implementing a pattern, have the official Elysia code open side-by-side.

---

## Success Criteria

**Code Quality**:

- ✅ Bootstrap: 4 focused functions (~50 lines each) + orchestrator (~20 lines) = ~220 lines
- ✅ Each function follows official Elysia pattern exactly
- ✅ smido_tree.py reduced from 520 to ~100 lines
- ✅ Zero branch_id in @tool decorators

**Functionality**:

- ✅ 12 tools at root (verified by bootstrap structure test)
- ✅ Post-tool chains work (manual test verification)
- ✅ Status <200ms (test_quick_status_flow.py)
- ✅ A3 scenario passes (test_plan7_full_tree.py)

**Architecture**:

- ✅ Follows one_branch pattern (flat root, all tools at base)
- ✅ Follows from_tool_ids pattern (post-tool chains)
- ✅ Max 2 tree levels (root → post-tool)
- ✅ No keyword detection

### To-dos

- [ ] Add imports for 5 native Elysia tools (Query, Aggregate, Visualise, CitedSummarizer, FakeTextResponse) to bootstrap.py
- [ ] Rewrite vsm_smido_bootstrap() to register all 12 tools at base root (flat pattern, no hierarchical branches)
- [ ] Implement post-tool chains using from_tool_ids for SMIDO flows (get_alarms→health, compute_worldstate→analyze, etc.)
- [ ] Write clear root instruction grouping tools by purpose, no keyword detection, trust LLM to read descriptions
- [ ] Delete/comment out 6 hierarchical branch functions in smido_tree.py (_add_m_branch, _add_t_branch, etc.)
- [ ] Run test_quick_status_flow.py to verify get_current_status still works (<100ms)
- [ ] Run test_plan7_full_tree.py to verify A3 scenario still completes correctly with new flat architecture
- [ ] Manual test: verify Query, Aggregate, and Visualise are now available and selectable by the agent