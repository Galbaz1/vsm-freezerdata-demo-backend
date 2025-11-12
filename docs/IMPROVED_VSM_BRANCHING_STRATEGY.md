# Improved VSM Branching Strategy

**Problem**: Current VSM uses `branch_initialisation="empty"` which excludes all native Elysia tools (query, aggregate, visualise, cited_summarize, summarise_items).

**Solution**: Hybrid branching strategy that combines SMIDO methodology with native Elysia tools.

---

## Proposed Tree Structure

```
Root (smido_base)
├── SMIDO Flow (M→T→I→D→O)  [Domain-specific workflow]
│   ├── Melding
│   ├── Technisch
│   ├── Installatie
│   ├── Diagnose (P1-P4)
│   └── Onderdelen
└── General Tools [Native Elysia capabilities]
    ├── query (direct Weaviate search)
    ├── aggregate (statistics)
    ├── visualise (charts)
    └── cited_summarize (end conversation)
```

---

## Implementation Options

### Option 1: Two-Branch Root (RECOMMENDED)

**Root branch** with two top-level options:
1. **SMIDO workflow** - Structured troubleshooting (M→T→I→D→O)
2. **Direct search** - Quick queries (query/aggregate/visualise)

```python
# Root with choice
tree.add_branch(
    root=True,
    branch_id="smido_base",
    instruction="""
    Choose between:
    - SMIDO workflow: Structured troubleshooting voor storing (gebruik bij onbekende symptomen)
    - Direct search: Snel zoeken in data/manuals (gebruik bij specifieke vraag)
    """,
    status="Analyzing request..."
)

# Branch 1: SMIDO (current structure)
tree.add_branch(
    branch_id="smido_melding",
    from_branch_id="smido_base",
    instruction="...",  # Current M branch instruction
    description="Start SMIDO gestructureerde storingzoeken",
    status="Verzamel melding..."
)
# ... continue with T, I, D, O as before

# Branch 2: Direct tools
tree.add_branch(
    branch_id="direct_search",
    from_branch_id="smido_base",
    instruction="Search manuals, query collections, or analyze data directly",
    description="Direct data access zonder SMIDO flow",
    status="Searching..."
)
tree.add_tool(Query, branch_id="direct_search")
tree.add_tool(Aggregate, branch_id="direct_search")
tree.add_tool(search_manuals_by_smido, branch_id="direct_search")  # Keep VSM custom

# Always available at root
tree.add_tool(Visualise, branch_id="smido_base")
tree.add_tool(CitedSummarizer, branch_id="smido_base")
tree.add_tool(FakeTextResponse, branch_id="smido_base")
```

**Benefits**:
- ✅ Structured SMIDO for full troubleshooting
- ✅ Quick access to Weaviate for ad-hoc queries
- ✅ Agent chooses appropriate path based on user intent

**Use cases**:
- "Start troubleshooting" → SMIDO
- "What does the manual say about defrost?" → Direct search (query)
- "Show me temperature trend" → Direct search (visualise)

---

### Option 2: SMIDO + Native Tools at Every Branch

Add native tools alongside VSM tools at each SMIDO branch:

```python
def _assign_tools_to_branches(tree: Tree):
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    
    # M - Melding: Custom + Native
    tree.add_tool(get_alarms, branch_id="smido_melding")
    tree.add_tool(get_asset_health, branch_id="smido_melding")
    tree.add_tool(Query, branch_id="smido_melding")  # For flexible queries
    tree.add_tool(Aggregate, branch_id="smido_melding")  # For counts/stats
    
    # P3 - Procesparameters: WorldState + Visualize
    tree.add_tool(compute_worldstate, branch_id="smido_p3_procesparameters")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p3_procesparameters")
    tree.add_tool(Visualise, branch_id="smido_p3_procesparameters")  # Chart temps/pressures
    tree.add_tool(Query, branch_id="smido_p3_procesparameters")  # Flexible search
    
    # ... continue for all branches
```

**Benefits**:
- ✅ Native tools available when needed within SMIDO flow
- ✅ Maintains SMIDO structure
- ✅ Agent has flexibility at each phase

**Drawbacks**:
- ⚠️ More decision points (might slow down agent)
- ⚠️ Tool overlap (search_manuals_by_smido vs Query)

---

### Option 3: Add Generic Branch AFTER SMIDO Completion

SMIDO flow completes → agent can choose post-analysis tools:

```python
# After O branch completes
tree.add_branch(
    branch_id="post_smido",
    from_branch_id="smido_onderdelen",
    instruction="SMIDO complete. Now: visualize data, search additional info, or summarize",
    description="Post-SMIDO analysis and presentation",
    status="Analyzing results..."
)
tree.add_tool(Visualise, branch_id="post_smido")
tree.add_tool(Query, branch_id="post_smido")
tree.add_tool(CitedSummarizer, branch_id="post_smido")
```

**Benefits**:
- ✅ Clean SMIDO flow (no tool clutter)
- ✅ Native tools available for post-diagnosis analysis
- ✅ Visualization of findings

**Drawbacks**:
- ⚠️ Can't use native tools DURING SMIDO (only after)

---

## Recommended Approach: OPTION 1 (Two-Branch Root)

**Why**:
1. **Intent Detection**: Agent distinguishes "structured troubleshooting" vs "quick query"
2. **Flexibility**: Users can ask "Show me all alarms" (query) without entering SMIDO
3. **Maintains SMIDO Purity**: Full troubleshooting uses dedicated SMIDO path
4. **Best of Both**: Native tools + VSM custom tools available

**Implementation**:

```python
def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
    """Bootstrap VSM with two-branch root strategy."""
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    
    # Root: Choose between SMIDO or Direct
    # (base branch already created by empty_init)
    tree.decision_nodes["base"].instruction = """
    Choose based on user intent:
    
    **SMIDO workflow** - Use when:
    - User reports a problem/storing ("koelcel werkt niet", "temperatuur te hoog")
    - Unclear symptoms need systematic diagnosis
    - Full troubleshooting needed (M→T→I→D→O)
    
    **Direct search** - Use when:
    - Specific question ("Wat zegt manual over X?")
    - Data query ("Hoeveel alarms?", "Show temperature")
    - Quick lookup without full diagnosis
    
    **Text response** - Use when:
    - No data needed (greetings, clarifications)
    - Summarize existing environment
    """
    
    # Add SMIDO as sub-branch
    tree.add_branch(
        branch_id="smido_melding",
        from_branch_id="base",
        description="Start SMIDO gestructureerde storingzoeken (M→T→I→D→O)",
        instruction="...",  # Current M instruction
        status="Verzamel melding...",
        root=False
    )
    # Continue with T, I, D, O...
    
    # Add direct search branch
    tree.add_branch(
        branch_id="direct_search",
        from_branch_id="base",
        description="Direct data access: query collections, search manuals, analyze stats",
        instruction="""
        Choose tool based on question:
        - query: Search any collection (VSM_*, FD_*)
        - aggregate: Count, statistics, summaries
        - search_manuals_by_smido: Manual search (can use without SMIDO flow)
        - visualise: Create charts from environment data
        """,
        status="Searching...",
        root=False
    )
    tree.add_tool(Query, branch_id="direct_search")
    tree.add_tool(Aggregate, branch_id="direct_search")
    tree.add_tool(search_manuals_by_smido, branch_id="direct_search")
    tree.add_tool(Visualise, branch_id="direct_search")
    
    # Always available at root
    tree.add_tool(CitedSummarizer, branch_id="base")
    tree.add_tool(FakeTextResponse, branch_id="base")
    
    # Continue adding SMIDO tools to their branches as before...
```

---

## Benefits Summary

| Feature | Current | Proposed |
|---------|---------|----------|
| SMIDO workflow | ✅ | ✅ |
| Direct Weaviate query | ❌ | ✅ |
| Visualization | ❌ | ✅ |
| Quick manual lookup | ⚠️ (only via SMIDO) | ✅ (direct) |
| Statistics/aggregation | ⚠️ (custom only) | ✅ (native) |
| Intent detection | ❌ | ✅ |
| Tool count | 7 + forced | 13 total |

---

## Migration Path

1. Update `features/vsm_tree/bootstrap.py` → `vsm_smido_bootstrap()`
2. Modify root branch instruction for two-path choice
3. Add `direct_search` branch with native tools
4. Keep SMIDO branches as-is (already working)
5. Test both paths with real scenarios
6. Update agent.mdc rule file

**Estimated effort**: 2-3 hours

---

## Example User Flows

**Flow 1: Full Troubleshooting**
```
User: "Koelcel bereikt temperatuur niet"
Agent: → SMIDO workflow (M branch)
Tools: get_alarms, get_asset_health, search_manuals_by_smido...
```

**Flow 2: Quick Query**
```
User: "Show me all critical alarms in the last week"
Agent: → Direct search (aggregate on VSM_TelemetryEvent)
Tools: Aggregate (native)
```

**Flow 3: Manual Lookup**
```
User: "Wat staat er in de manual over defrost?"
Agent: → Direct search
Tools: search_manuals_by_smido (no SMIDO filter) or Query (VSM_ManualSections)
```

**Flow 4: Visualization**
```
User: "Show temperature trend for last 24 hours"
Agent: → Direct search → compute_worldstate → visualise
Tools: compute_worldstate, then Visualise (chart)
```

---

## Conclusion

**Option 1 (Two-Branch Root)** provides the best balance:
- Preserves SMIDO methodology for structured troubleshooting
- Adds native Elysia capabilities for flexible queries
- Enables intent-based routing (diagnosis vs lookup)
- Makes system more versatile without breaking existing flows

