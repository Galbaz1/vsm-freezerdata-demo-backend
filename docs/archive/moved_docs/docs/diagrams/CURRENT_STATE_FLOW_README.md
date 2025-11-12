# Current State Query - Information Flow Documentation

**Created**: November 12, 2025  
**Status**: Complete analysis of planned vs actual behavior

---

## Quick Navigation

- **📊 Diagram**: [`current_state_info_flow.mermaid`](./current_state_info_flow.mermaid) - Visual flowchart
- **📖 Detailed Explanation**: [`CURRENT_STATE_INFO_FLOW_EXPLANATION.md`](./CURRENT_STATE_INFO_FLOW_EXPLANATION.md) - Step-by-step breakdown
- **🔍 Implementation Guide**: See explanation doc section "Required Implementation"

---

## TL;DR

**Question**: What happens when user asks "What's the current state?"

**Expected Answer**: <200ms response with 5 sensors + flags

**Actual Answer**: 2-3 minutes with unnecessary manuals/diagrams

**Root Cause**: `get_current_status` tool is **documented but not implemented**

---

## Key Findings

### 1. The Fast Path Doesn't Exist (Yet)

**Documented** (in `docs/QUICK_STATUS_IMPLEMENTATION.md`):
```
Tool: get_current_status
File: elysia/api/custom_tools.py (lines 49-178)
Performance: <100ms
```

**Reality**:
```bash
$ grep "get_current_status" elysia/api/custom_tools.py
# No matches found
```

The tool is **planned** but **not coded**.

### 2. System Falls Back to Diagnostic Tools

Without `get_current_status`, LLM chooses next best option:
- `get_asset_health` (reads 785K rows from parquet, computes 60 features)
- Then decides to search manuals (Weaviate query for diagrams)
- Total: 2-3 minutes

### 3. Complete Information Flow Traced

The diagram shows **every layer**:
1. Frontend WebSocket → Backend API
2. UserManager → TreeManager → Tree
3. Tree execution engine (conversation history, branch routing)
4. LLM decision making (DecisionNode + DSPy)
5. Tool execution (planned vs actual)
6. Data layer (cache vs parquet vs Weaviate)
7. Results streaming back to frontend

### 4. Timing Breakdown

**Planned** (with get_current_status):
```
WebSocket (10ms) + Validation (20ms) + Lock (10ms) + Tree setup (10ms) 
+ LLM decision (100ms) + Cache read (<1ms) + Format (10ms) + Send (10ms)
= ~170ms ✅
```

**Current** (fallback to diagnostics):
```
... same overhead (60ms) ...
+ LLM decision (500ms) + Parquet read (800ms) + WorldState compute (400ms)
+ W vs C compare (50ms) + LLM decision #2 (500ms) + Weaviate query (600ms)
+ Format (50ms)
= ~2960ms ❌
```

---

## Architecture Layers (Bottom-Up)

### Layer 7: Data Storage
- **Parquet**: 785K telemetry rows (timeseries)
- **Weaviate**: VSM collections (manuals, diagrams, events)
- **Cache** (planned): Pre-seeded WorldState in `tree._initial_worldstate_cache`

### Layer 6: Data Processing
- **WorldStateEngine**: Computes 60+ features from parquet
- **Asset Health**: W vs C comparison
- **Manual Search**: Hybrid semantic + keyword search

### Layer 5: Tool Execution
- **@tool decorator**: Async generator functions
- **Status yields**: Progress indicators
- **Result yields**: Data objects

### Layer 4: LLM Decision Making
- **DecisionNode**: Formats tools as JSON for LLM
- **DecisionPrompt**: DSPy module with agent description + branch instruction
- **BASE_MODEL**: gemini-2.5-flash chooses which tool to call

### Layer 3: Tree Execution
- **Tree.async_run()**: Main orchestration loop
- **Conversation history**: Tracks user messages + agent responses
- **Branch routing**: M→T→I→D→O flow

### Layer 2: Tree Management
- **TreeManager**: Per-user tree lifecycle
- **UserManager**: Multi-user coordination
- **AsyncIO locks**: Prevent concurrent requests

### Layer 1: API Interface
- **WebSocket endpoint**: Real-time bidirectional communication
- **JSON messages**: Structured query/response format
- **Streaming results**: Yields progress updates

---

## How to Use This Documentation

### If you're implementing get_current_status:

1. Read the **diagram** to understand overall flow
2. Study **Layer 5** (Tool Execution) in the explanation doc
3. Follow the **Required Implementation** section:
   - Create tool in `custom_tools.py`
   - Pre-seed cache in `bootstrap.py`
   - Register tool in `smido_tree.py`
4. Run **test script** to verify

### If you're debugging slow responses:

1. Check **timing breakdown** in explanation doc
2. Identify which layer is slow (LLM? Parquet? Weaviate?)
3. Use **diagram color coding**:
   - 🟨 Yellow dashed = Planned (not yet implemented)
   - 🟥 Red = Current slow path
   - 🟦 Blue = Data layer
   - 🟪 Purple = LLM layer
   - 🟩 Green = Fast operations

### If you're onboarding a new developer:

1. Start with **diagram** (visual overview)
2. Read **TL;DR** section (executive summary)
3. Study **architecture layers** (conceptual model)
4. Dive into **explanation doc** (implementation details)

---

## Related Documentation

- **Agent prompts**: `features/vsm_tree/smido_tree.py` (agent description, branch instructions)
- **Tool definitions**: `elysia/api/custom_tools.py` (all 7 VSM tools)
- **Tree execution**: `elysia/tree/tree.py` (async_run logic)
- **Decision making**: `elysia/tree/util.py` (DecisionNode.__call__)
- **WorldState engine**: `features/telemetry_vsm/src/worldstate_engine.py` (feature computation)
- **Bootstrap system**: `features/vsm_tree/bootstrap.py` (auto-registration)

---

## Files Created

1. **current_state_info_flow.mermaid** - Visual diagram (Mermaid format)
2. **CURRENT_STATE_INFO_FLOW_EXPLANATION.md** - Detailed walkthrough (15+ pages)
3. **CURRENT_STATE_FLOW_README.md** - This navigation guide

All files in: `docs/diagrams/`

---

## Next Steps

To implement the fast path:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Create get_current_status tool
# Edit: elysia/api/custom_tools.py
# (See implementation code in explanation doc)

# 3. Pre-seed cache
# Edit: features/vsm_tree/bootstrap.py
# (Add WorldState generation to vsm_smido_bootstrap)

# 4. Register tool
# Edit: features/vsm_tree/smido_tree.py
# (Add to _assign_tools_to_branches)

# 5. Test
python3 scripts/test_current_status_fast_path.py

# 6. Verify in frontend
elysia start
# Open http://localhost:8000
# Type: "What's the current state?"
# Expected: <200ms response
```

---

## Questions?

- **"Why was this documented but not implemented?"**  
  Phase 1b planning created the design, but implementation was deferred. The documentation exists to guide future work.

- **"Can I just modify get_asset_health to be faster?"**  
  No - get_asset_health is a **diagnostic tool** (W vs C comparison). We need a separate **status tool** for quick checks.

- **"Does this break existing functionality?"**  
  No - this is **additive**. Diagnostic tools continue to work. get_current_status is a new fast path.

- **"What if the cache is stale?"**  
  Tool has fallback: generates synthetic "today" WorldState if cache missing (still <500ms, better than 3 seconds).

---

**End of Documentation**

