# Improved VSM Branching Strategy

**Date**: November 12, 2025  
**Based on**: [Elysia blog](https://weaviate.io/blog/elysia-agentic-rag), Elysia official code, VSM requirements

---

## Key Insight: Weaviate's Philosophy

From analyzing Weaviate's `multi_branch_init()` and `one_branch_init()`:

**They use SIMPLE, FLAT structures**:
- `one_branch`: ALL tools at root (5-6 tools, agent chooses)
- `multi_branch`: Root + search sub-branch (2-level max, clean separation)

**They DON'T**:
- ❌ Create deep hierarchies (no 4-5 level trees)
- ❌ Put all tools everywhere
- ❌ Use complex conditional logic
- ❌ Overcomplicate branching

**Philosophy**: "Branches separate tools into categories, tools do the work"

---

## VSM's Unique Situation

### What Makes VSM Different from Standard Elysia

| Aspect | Standard Elysia | VSM |
|--------|----------------|-----|
| **Use case** | Open-ended search | Structured workflow (SMIDO) |
| **Data** | Weaviate only | Weaviate + Parquet + JSON |
| **Workflow** | User-driven | Methodology-driven (M→T→I→D→O) |
| **Tools** | General (query, aggregate) | Domain-specific (7 custom) |
| **Phases** | None | 5 sequential phases |
| **Fast path** | Not needed | CRITICAL (<200ms status) |

**Conclusion**: VSM needs BOTH Weaviate's simplicity AND workflow structure.

---

## Revised Strategy: **One-Branch + Post-Tool Chains**

Based on Weaviate's `one_branch_init` pattern, adapted for SMIDO:

```
Root (base) - Simple tool menu
├── get_current_status (fast path, run_if_true)
├── text_response (always)
├── cited_summarize (always)
│
├── get_alarms → smido_melding_flow
├── search_manuals_by_smido → choose phase (I/P2/O)
├── query (native) → flexible search
├── aggregate (native) → statistics
│
└── After tools complete:
    ├── compute_worldstate → smido_p3_flow
    ├── query_vlog_cases → smido_o_flow
    └── visualise (from any data tool)
```

**Philosophy**: Flat root with **post-tool branching** (not pre-branching).

---

## Implementation: Weaviate's Pattern Applied to VSM

### Bootstrap Code

```python
def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
    """
    Bootstrap VSM following Weaviate's one_branch pattern.
    Flat root + post-tool SMIDO chains.
    """
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    from elysia.api.custom_tools import (
        get_current_status,  # NEW: fast path
        get_alarms,
        get_asset_health,
        compute_worldstate,
        query_telemetry_events,
        search_manuals_by_smido,
        query_vlog_cases,
        analyze_sensor_pattern
    )
    
    # ===== ROOT INSTRUCTION (one_branch style) =====
    tree.decision_nodes["base"].instruction = """
    Choose tool based on user's immediate need:
    
    **Quick answers** (no data needed):
    - text_response: Groeten, uitleg, bevestigingen
    - cited_summarize: Samenvatting van opgehaalde data
    
    **Status check** (get_current_status auto-runs if detected):
    - "wat is status", "hoe gaat het", "current state"
    
    **Problem/Alert** (starts SMIDO flow):
    - get_alarms: Actieve alarmen ophalen
    - get_asset_health: Systeem gezondheid (W vs C)
    
    **Search/Lookup**:
    - search_manuals_by_smido: Zoek in manuals (SMIDO-gefilterd)
    - query: Flexibele Weaviate search (any collection)
    - aggregate: Tel, groepeer, statistieken
    
    **Deep analysis** (triggers P3 flow):
    - compute_worldstate: Bereken 58 features from parquet
    
    **Solution lookup** (triggers O flow):
    - query_vlog_cases: Vind vergelijkbare cases (A1-A5)
    
    Read tool descriptions carefully. Choose ONE tool that matches user intent.
    After tool completes, more tools may become available.
    """
    
    # ===== TOOLS AT ROOT (Weaviate's one_branch pattern) =====
    # Always available
    tree.add_tool(FakeTextResponse, branch_id="base")
    tree.add_tool(CitedSummarizer, branch_id="base")
    
    # Fast path (auto-runs)
    tree.add_tool(get_current_status, branch_id="base")
    
    # Entry points
    tree.add_tool(get_alarms, branch_id="base")
    tree.add_tool(get_asset_health, branch_id="base")
    tree.add_tool(search_manuals_by_smido, branch_id="base")
    
    # Native tools
    tree.add_tool(Query, branch_id="base")
    tree.add_tool(Aggregate, branch_id="base")
    
    # Data generators
    tree.add_tool(compute_worldstate, branch_id="base")
    tree.add_tool(query_vlog_cases, branch_id="base")
    
    # ===== POST-TOOL CHAINS (SMIDO flows) =====
    
    # After get_alarms → SMIDO M flow
    tree.add_branch(
        branch_id="smido_melding_flow",
        from_branch_id="base",
        instruction="""
        Alarms retrieved. Continue SMIDO Melding:
        - Assess urgency (KRITIEK/HOOG/NORMAAL)
        - Ask about symptoms, timing, products
        - Decide: Fix now (T), Diagnose (continue), or Escalate
        """,
        description="SMIDO M: symptom assessment after alarm check",
        status="Analyseer melding..."
    )
    tree.add_tool(get_asset_health, branch_id="smido_melding_flow")
    tree.add_tool(Query, branch_id="smido_melding_flow")  # Additional search
    # smido_melding_flow → smido_technisch_flow
    
    # After search_manuals (context-dependent routing)
    tree.add_branch(
        branch_id="smido_context_router",
        from_branch_id="base",
        instruction="""
        Manual retrieved. What's next?
        - If schema search → I (Installatie)
        - If settings search → P2 (Procesinstellingen)
        - If component search → O (Onderdelen)
        - If enough info → text_response
        """,
        description="Route to appropriate SMIDO phase",
        status="Route naar juiste fase..."
    )
    
    # After compute_worldstate → P3 flow
    tree.add_branch(
        branch_id="smido_p3_analysis",
        from_branch_id="base",
        instruction="""
        WorldState computed (58 features). Analyze:
        - analyze_sensor_pattern: Match tegen reference patterns
        - visualise: Chart temps/pressures/trends
        - aggregate: Statistics on sensors
        - search_manuals_by_smido: Find P3 guidance
        """,
        description="SMIDO P3: parameter analysis",
        status="Analyseer procesparameters..."
    )
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p3_analysis")
    tree.add_tool(Visualise, branch_id="smido_p3_analysis")
    tree.add_tool(Aggregate, branch_id="smido_p3_analysis")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p3_analysis")
    
    # After query_vlog_cases → O flow
    tree.add_branch(
        branch_id="smido_onderdelen_flow",
        from_branch_id="base",
        instruction="""
        Vlog case found. Provide solution:
        - search_manuals_by_smido: Component repair procedures
        - query_telemetry_events: Historical component failures
        - aggregate: Failure statistics
        - cited_summarize: Complete solution summary
        """,
        description="SMIDO O: component isolation + solution",
        status="Isoleer component..."
    )
    tree.add_tool(search_manuals_by_smido, branch_id="smido_onderdelen_flow")
    tree.add_tool(query_telemetry_events, branch_id="smido_onderdelen_flow")
    tree.add_tool(Aggregate, branch_id="smido_onderdelen_flow")
    tree.add_tool(CitedSummarizer, branch_id="smido_onderdelen_flow")
    
    # Visualise available after ANY data tool
    tree.add_tool(Visualise, branch_id="base", from_tool_ids=[
        "compute_worldstate", 
        "get_asset_health",
        "query",
        "aggregate"
    ])
```

---

## How This Follows Weaviate's Philosophy

### 1. **Flat Root** (like `one_branch`)
- All tools visible at root (agent reads descriptions, chooses)
- No deep pre-branching (3-4 levels)
- Clean, simple decision point

### 2. **Post-Tool Branching** (like `from_tool_ids`)
- Branches appear AFTER tools complete
- Example: `query → query_postprocessing` (Weaviate's pattern)
- VSM: `compute_worldstate → smido_p3_analysis`

### 3. **Tool Chaining** (Elysia's strength)
- `visualise` available after data tools
- SMIDO flows triggered by specific tools
- Natural progression: tool → analysis → next phase

### 4. **Minimal Options Per Decision**
- Root: 9-10 tools (manageable)
- Post-tool branches: 3-5 tools (focused)
- Agent not overwhelmed with 20+ options

---

## Comparison: Current vs Proposed

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Structure** | Deep hierarchy (M→T→I→D[P1-P4]→O) | Flat root + post-tool chains |
| **Root tools** | 0 (empty init) | 10 (mixed VSM + native) |
| **Branching** | Pre-defined SMIDO path | Tool-triggered flows |
| **Native tools** | None | query, aggregate, visualise, summarize |
| **Fast path** | None | get_current_status (run_if_true) |
| **Agent decisions** | Which SMIDO phase? | Which tool for this need? |
| **Flexibility** | Low (rigid SMIDO) | High (tool-driven + SMIDO) |
| **Simplicity** | Complex (9 branches) | Simple (root + 4 flows) |

---

## Example User Flows

### Flow 1: Status Check (FAST PATH)
```
User: "Wat is de status?"
→ get_current_status.run_if_true() detects keywords
→ Auto-runs, <200ms
→ Returns 5 sensors + flags
→ END (forced_text_response if needed)
```

### Flow 2: Simple Query
```
User: "Hoeveel critical alarms?"
→ Root: aggregate chosen
→ Aggregate on VSM_TelemetryEvent
→ Return count
→ text_response → END
```

### Flow 3: Manual Lookup
```
User: "Wat zegt manual over defrost?"
→ Root: search_manuals_by_smido OR query chosen
→ Search VSM_ManualSections
→ cited_summarize → END
```

### Flow 4: Full SMIDO (Triggered Flow)
```
User: "Koelcel bereikt temperatuur niet"
→ Root: get_alarms chosen
→ Alarms found → smido_melding_flow branch appears
→ get_asset_health → smido_technisch_flow
→ search_manuals → smido_context_router
→ compute_worldstate → smido_p3_analysis
→ analyze_sensor_pattern + visualise
→ query_vlog_cases → smido_onderdelen_flow
→ cited_summarize → END
```

### Flow 5: Visualization
```
User: "Show temperature trend last 24 hours"
→ Root: compute_worldstate chosen
→ WorldState computed, added to environment
→ visualise appears (from_tool_ids=["compute_worldstate"])
→ Chart created
→ cited_summarize → END
```

---

## Critical Design Decisions

### 1. **No Pre-Defined M→T→I→D→O Path**

**Instead**: Tools trigger appropriate next phase

**Why**: 
- Weaviate doesn't pre-define paths
- Agent chooses based on context (like `query` vs `aggregate`)
- More flexible for edge cases

**Example**:
- `get_alarms` → M flow (if needed)
- `compute_worldstate` → P3 analysis (direct to diagnosis)
- `query_vlog_cases` → O flow (skip to solution)

### 2. **Flat Root = Fast Agent Decisions**

**Current problem**: Agent navigates M→T→I before any tool execution

**Proposed**: Agent picks tool immediately, SMIDO flows happen AFTER

**Benefit**: 
- Faster first response (no pre-branching overhead)
- Natural tool selection (agent trained on tool descriptions)
- Follows Elysia's design

### 3. **Post-Tool Chains Replace Pre-Branching**

**Weaviate's pattern**:
```python
tree.add_tool(Query, branch_id="search")
tree.add_tool(SummariseItems, branch_id="search", from_tool_ids=["query"])
```

**VSM adaptation**:
```python
tree.add_tool(compute_worldstate, branch_id="base")
tree.add_tool(Visualise, branch_id="base", from_tool_ids=["compute_worldstate"])

tree.add_tool(get_alarms, branch_id="base")
tree.add_branch(
    branch_id="smido_melding_flow",
    from_branch_id="base",
    # Only appears AFTER get_alarms runs
)
```

### 4. **run_if_true for Fast Path**

**Weaviate doesn't use this extensively**, but docs show it's for:
> "Tools can be configured to run automatically based on specific criteria"

**VSM use case**: Perfect for status checks

```python
class GetCurrentStatus(Tool):
    async def run_if_true(self, tree_data, base_lm, complex_lm, client_manager):
        """Auto-run if status keywords in prompt."""
        prompt = tree_data.user_prompt.lower()
        keywords = ["status", "hoe gaat het", "situatie", "toestand"]
        
        if any(kw in prompt for kw in keywords):
            return (True, {})  # Run immediately
        return (False, {})
```

**Benefit**: Bypasses decision tree entirely for status → <200ms

---

## Minimal Tool Matrix (Per Decision Point)

| Decision Point | Available Tools | Count |
|----------------|-----------------|-------|
| **Root (initial)** | get_current_status, get_alarms, get_asset_health, search_manuals, query, aggregate, compute_worldstate, query_vlog_cases, text_response, cited_summarize | 10 |
| **After get_alarms** | get_asset_health, query, text_response, cited_summarize | 4 |
| **After compute_worldstate** | analyze_sensor_pattern, visualise, aggregate, search_manuals, cited_summarize | 5 |
| **After query_vlog_cases** | search_manuals, query_telemetry_events, aggregate, cited_summarize | 4 |
| **After search_manuals** | query, aggregate, text_response, cited_summarize | 4 |

**Average**: 5-6 tools per decision (manageable for LLM)

---

## Complete Implementation

```python
def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
    """Bootstrap VSM with Weaviate's one_branch philosophy."""
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    from elysia.api.custom_tools import (
        get_current_status,
        get_alarms,
        get_asset_health,
        compute_worldstate,
        query_telemetry_events,
        search_manuals_by_smido,
        query_vlog_cases,
        analyze_sensor_pattern
    )
    
    # Update root instruction (Weaviate's clear, simple style)
    tree.decision_nodes["base"].instruction = """
    Choose ONE tool that matches user's immediate request.
    Read tool descriptions thoroughly.
    
    Voor status: get_current_status (auto-runs als gedetecteerd)
    Voor alarmen/problemen: get_alarms of get_asset_health
    Voor zoeken: query (Weaviate), aggregate (statistieken), search_manuals_by_smido
    Voor diepte-analyse: compute_worldstate (sensors), query_vlog_cases (cases)
    Voor antwoorden: text_response, cited_summarize
    
    Tools may enable new tools after completion.
    """
    
    # ===== ALWAYS AVAILABLE =====
    tree.add_tool(FakeTextResponse, branch_id="base")
    tree.add_tool(CitedSummarizer, branch_id="base")
    
    # ===== FAST PATH =====
    tree.add_tool(get_current_status, branch_id="base")  # With run_if_true
    
    # ===== ENTRY TOOLS (trigger flows) =====
    tree.add_tool(get_alarms, branch_id="base")
    tree.add_tool(get_asset_health, branch_id="base")
    tree.add_tool(search_manuals_by_smido, branch_id="base")
    tree.add_tool(query_vlog_cases, branch_id="base")
    tree.add_tool(compute_worldstate, branch_id="base")
    
    # ===== NATIVE SEARCH TOOLS =====
    tree.add_tool(Query, branch_id="base")
    tree.add_tool(Aggregate, branch_id="base")
    
    # ===== POST-TOOL CHAINS =====
    
    # After get_alarms → M flow options
    tree.add_tool(get_asset_health, branch_id="base", from_tool_ids=["get_alarms"])
    tree.add_tool(Query, branch_id="base", from_tool_ids=["get_alarms"])
    
    # After compute_worldstate → P3 analysis
    tree.add_tool(analyze_sensor_pattern, branch_id="base", from_tool_ids=["compute_worldstate"])
    tree.add_tool(Visualise, branch_id="base", from_tool_ids=["compute_worldstate"])
    tree.add_tool(Aggregate, branch_id="base", from_tool_ids=["compute_worldstate"])
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["compute_worldstate"])
    
    # After query_vlog_cases → O flow
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["query_vlog_cases"])
    tree.add_tool(query_telemetry_events, branch_id="base", from_tool_ids=["query_vlog_cases"])
    tree.add_tool(Aggregate, branch_id="base", from_tool_ids=["query_vlog_cases"])
    
    # After search_manuals → flexible follow-up
    tree.add_tool(Query, branch_id="base", from_tool_ids=["search_manuals_by_smido"])
    tree.add_tool(Aggregate, branch_id="base", from_tool_ids=["search_manuals_by_smido"])
    
    # After get_asset_health → follow-up options
    tree.add_tool(compute_worldstate, branch_id="base", from_tool_ids=["get_asset_health"])
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["get_asset_health"])
    tree.add_tool(query_vlog_cases, branch_id="base", from_tool_ids=["get_asset_health"])
    
    # Visualise after ANY data tool
    tree.add_tool(Visualise, branch_id="base", from_tool_ids=[
        "query", "aggregate", "get_asset_health"
    ])
    
    # Summarize always available after data retrieval
    tree.add_tool(CitedSummarizer, branch_id="base", from_tool_ids=[
        "query", "aggregate", "compute_worldstate", "query_vlog_cases",
        "search_manuals_by_smido", "get_alarms", "get_asset_health"
    ])
```

---

## Why This is Better

### Follows Weaviate's Philosophy

✅ **Simple root** (like `one_branch`): All tools at base, clear descriptions  
✅ **Tool-driven flow** (not branch-driven): Agent chooses tool, flow emerges  
✅ **Post-tool chains** (like `from_tool_ids`): Next options appear after completion  
✅ **Minimal per decision**: 4-6 tools per point (not 14)

### Solves VSM Problems

✅ **Fast path**: `get_current_status.run_if_true()` → <200ms  
✅ **Native tools**: query, aggregate, visualise available  
✅ **SMIDO preserved**: Flows emerge from tool sequences  
✅ **Flexible**: Agent can skip phases if appropriate  
✅ **Simple**: Easier to understand and maintain

### Matches VSM Needs

✅ **Domain-specific**: VSM tools are entry points  
✅ **Workflow-aware**: SMIDO flows via post-tool chains  
✅ **Data-hybrid**: Weaviate (query/aggregate) + Parquet (compute_worldstate)  
✅ **Educational**: Agent explains tool choices naturally

---

## Migration from Current SMIDO Tree

### What Changes

**From**: Hierarchical SMIDO branches (M→T→I→D→O)  
**To**: Flat root + tool-triggered flows

**Example transformation**:

**Old**:
```python
_add_m_branch(tree)  # Pre-create M branch
_add_t_branch(tree)  # Pre-create T branch
tree.add_tool(get_alarms, branch_id="smido_melding")
```

**New**:
```python
tree.add_tool(get_alarms, branch_id="base")  # At root
# Flow emerges AFTER get_alarms runs
tree.add_tool(get_asset_health, from_tool_ids=["get_alarms"])
```

### What Stays the Same

✅ **Tool implementations**: All 7 VSM custom tools unchanged  
✅ **Agent persona**: Same Dutch, educational style  
✅ **SMIDO methodology**: Still guides tool sequences  
✅ **Data sources**: Weaviate + Parquet unchanged  
✅ **A3 scenario**: Still works (tool sequence achieves same result)

---

## Expected Improvements

### Performance
- **Status**: 2-3 min → <200ms (run_if_true fast path)
- **Simple queries**: NEW capability (direct query/aggregate)
- **Full diagnosis**: Same 3-5 min (tool sequence, not branch nav)

### UX
- **Clearer choices**: "Choose tool" vs "Navigate to M phase"
- **Natural flow**: Agent explains tool purpose, not branch navigation
- **Flexible paths**: Can skip unnecessary phases
- **Better errors**: Tool-level errors, not branch confusion

### Maintainability
- **Simpler code**: ~200 lines vs ~500 lines
- **Easier to modify**: Add tool at root, define post-chains
- **Follows Elysia patterns**: Standard Weaviate approach
- **Better documentation**: Tool-driven is intuitive

---

## Implementation Steps

1. [ ] Create `get_current_status` with `run_if_true` method
2. [ ] Rewrite `vsm_smido_bootstrap()` with flat root pattern
3. [ ] Remove hierarchical SMIDO branch functions
4. [ ] Add post-tool chains with `from_tool_ids`
5. [ ] Test all flows (status, query, SMIDO, visualize)
6. [ ] Update agent.mdc rule
7. [ ] Update PROJECT_STATUS.md

**Estimated**: 4-6 hours

---

## Conclusion

**Recommended**: Flat root + post-tool chains (Weaviate's `one_branch` philosophy)

**Why**:
1. ✅ Follows Weaviate's proven simple pattern
2. ✅ Adds native tools naturally
3. ✅ Enables fast path via `run_if_true`
4. ✅ Preserves SMIDO methodology (via tool sequences)
5. ✅ Simpler to understand and maintain
6. ✅ More flexible for edge cases

**Key philosophical shift**: 
- **From**: "Navigate branches to find tools"
- **To**: "Choose tools, flows emerge naturally"

This aligns with Elysia's core design: **decision trees guide tool selection, not workflow prescription**.

---

**References**:
- [Elysia Blog: Agentic RAG](https://weaviate.io/blog/elysia-agentic-rag)
- Elysia Code: `elysia/tree/tree.py` (`one_branch_init`, `multi_branch_init`)
- VSM Status: `docs/project/PROJECT_STATUS.md`
- VSM Needs: `docs/project/PROJECT_TODO.md`
