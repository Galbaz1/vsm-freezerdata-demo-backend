# Improved VSM Branching Strategy

**Date**: November 12, 2025  
**Based on**: [Elysia blog](https://weaviate.io/blog/elysia-agentic-rag), Elysia official docs, VSM requirements

---

## Problem Statement

1. **Current**: VSM uses `branch_initialisation="empty"` → NO native Elysia tools
2. **Missing**: query, aggregate, visualise, cited_summarize (powerful, tested tools)
3. **Need**: Fast path for status checks (<200ms)
4. **Constraint**: Must maintain SMIDO methodology integrity

---

## Key Insights from [Elysia Blog](https://weaviate.io/blog/elysia-agentic-rag)

> "Unlike simple agentic platforms which have access to all possible tools at runtime, Elysia has a pre-defined web of possible nodes, each with a corresponding action."

**Principle**: Tools available ONLY when relevant (not all tools everywhere)

> "Other tools can remain invisible until certain conditions are met, only appearing as options when they're relevant to the current state."

**Principle**: Use `is_tool_available()` for conditional access

> "Tools can be configured to run automatically based on specific criteria"

**Principle**: Use `run_if_true()` for automatic execution (fast path!)

---

## Proposed Architecture: **Flat Root + Conditional Availability**

```
Root (smido_base)
│
├── FAST PATH (auto-executes if detected)
│   └── get_current_status
│       └── run_if_true: status keywords → instant response
│
├── SMIDO WORKFLOW (available when problem reported)
│   ├── smido_melding (M)
│   │   ├── get_alarms
│   │   ├── get_asset_health
│   │   └── query (native, conditional)
│   ├── smido_technisch (T)
│   │   └── get_asset_health
│   ├── smido_installatie (I)
│   │   ├── search_manuals_by_smido
│   │   └── query (native, for flexible search)
│   ├── smido_diagnose (D)
│   │   ├── P1 (Power): get_alarms
│   │   ├── P2 (Settings): search_manuals, get_asset_health, aggregate
│   │   ├── P3 (Parameters): compute_worldstate, analyze_pattern, visualise
│   │   ├── P4 (Input): compute_worldstate, query_events, aggregate
│   └── smido_onderdelen (O)
│       ├── query_vlog_cases
│       ├── search_manuals
│       └── aggregate (for component stats)
│
├── ALWAYS AVAILABLE (at root)
│   ├── cited_summarize (native, when environment has data)
│   └── text_response (native, fallback)
│
└── POST-TOOL CHAIN (after specific tools)
    └── visualise (after compute_worldstate/get_asset_health)
        └── from_tool_ids=["compute_worldstate", "get_asset_health"]
```

**Key Principles**:
1. **Minimal per state**: Each SMIDO branch has 2-4 tools MAX
2. **Smart availability**: Tools appear only when relevant
3. **Tool chaining**: visualise available AFTER data-generating tools
4. **Fast path**: get_current_status auto-runs, bypasses tree

---

## Implementation

### Bootstrap Function (Complete Rewrite)

```python
def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
    """
    Bootstrap VSM with flat root + conditional tool availability.
    Combines SMIDO methodology with native Elysia tools.
    """
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    from elysia.api.custom_tools import (
        get_current_status,  # Fast path (NEW)
        get_alarms,
        get_asset_health,
        compute_worldstate,
        query_telemetry_events,
        search_manuals_by_smido,
        query_vlog_cases,
        analyze_sensor_pattern
    )
    
    # ===== ROOT BRANCH INSTRUCTION =====
    tree.decision_nodes["base"].instruction = """
    Analyze user intent and choose appropriate path:
    
    **Fast Status** (get_current_status auto-runs if keywords detected):
    - "wat is status", "hoe gaat het", "current state"
    
    **SMIDO Troubleshooting** (use smido_melding branch):
    - User reports problem: "storing", "werkt niet", "temperatuur te hoog"
    - Unknown symptoms need systematic diagnosis
    - Full M→T→I→D→O workflow
    
    **Direct Query** (use query/aggregate):
    - Specific questions: "hoeveel alarms", "zoek X in manual"
    - Statistical questions: "gemiddelde temperatuur", "aantal events"
    - No troubleshooting needed
    
    **Visualize** (use visualise, only after data retrieved):
    - "chart", "plot", "grafiek"
    - Requires data in environment
    
    **Text Response** (use text_response):
    - Greetings, clarifications, explanations
    - No data needed
    
    CRITICAL: Choose MINIMAL tool set. Don't show all options.
    Only show tools relevant to detected intent.
    """
    
    # ===== FAST PATH: Auto-run status check =====
    tree.add_tool(get_current_status, branch_id="base", root=True)
    
    # ===== SMIDO BRANCHES =====
    # M - Melding
    tree.add_branch(
        branch_id="smido_melding",
        from_branch_id="base",
        root=False,
        instruction="...",  # Keep existing M instruction
        description="SMIDO Melding: symptom collection, urgency assessment",
        status="Verzamel melding..."
    )
    tree.add_tool(get_alarms, branch_id="smido_melding")
    tree.add_tool(get_asset_health, branch_id="smido_melding")
    tree.add_tool(Query, branch_id="smido_melding")  # Native for flexible search
    tree.add_tool(Aggregate, branch_id="smido_melding")  # Native for counts
    
    # T - Technisch
    tree.add_branch(
        branch_id="smido_technisch",
        from_branch_id="smido_melding",
        instruction="...",  # Keep existing T instruction
        description="SMIDO Technisch: visual inspection",
        status="Technische check..."
    )
    tree.add_tool(get_asset_health, branch_id="smido_technisch")
    tree.add_tool(Query, branch_id="smido_technisch")
    
    # I - Installatie
    tree.add_branch(
        branch_id="smido_installatie",
        from_branch_id="smido_technisch",
        instruction="...",  # Keep existing I instruction
        description="SMIDO Installatie: schema familiarity",
        status="Check installatie kennis..."
    )
    tree.add_tool(search_manuals_by_smido, branch_id="smido_installatie")
    tree.add_tool(Query, branch_id="smido_installatie")  # For flexible manual search
    
    # D - Diagnose (parent)
    tree.add_branch(
        branch_id="smido_diagnose",
        from_branch_id="smido_installatie",
        instruction="...",  # Keep existing D instruction
        description="SMIDO Diagnose: systematic 4 P's check",
        status="Start diagnose..."
    )
    
    # D → P1 (Power)
    tree.add_branch(
        branch_id="smido_p1_power",
        from_branch_id="smido_diagnose",
        instruction="...",
        description="P1: Electrical checks",
        status="Check voeding..."
    )
    tree.add_tool(get_alarms, branch_id="smido_p1_power")
    tree.add_tool(Query, branch_id="smido_p1_power")
    
    # D → P2 (Procesinstellingen)
    tree.add_branch(
        branch_id="smido_p2_procesinstellingen",
        from_branch_id="smido_diagnose",
        instruction="...",
        description="P2: Settings vs design",
        status="Check instellingen..."
    )
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(get_asset_health, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(Query, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(Aggregate, branch_id="smido_p2_procesinstellingen")
    
    # D → P3 (Procesparameters)
    tree.add_branch(
        branch_id="smido_p3_procesparameters",
        from_branch_id="smido_diagnose",
        instruction="...",
        description="P3: Measurements vs design",
        status="Analyseer parameters..."
    )
    tree.add_tool(compute_worldstate, branch_id="smido_p3_procesparameters")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p3_procesparameters")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p3_procesparameters")
    tree.add_tool(Visualise, branch_id="smido_p3_procesparameters")  # Chart temps/pressures
    tree.add_tool(Aggregate, branch_id="smido_p3_procesparameters")  # Stats
    
    # D → P4 (Productinput)
    tree.add_branch(
        branch_id="smido_p4_productinput",
        from_branch_id="smido_diagnose",
        instruction="...",
        description="P4: Environmental conditions",
        status="Check omgevingscondities..."
    )
    tree.add_tool(compute_worldstate, branch_id="smido_p4_productinput")
    tree.add_tool(query_telemetry_events, branch_id="smido_p4_productinput")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p4_productinput")
    tree.add_tool(Aggregate, branch_id="smido_p4_productinput")
    
    # O - Onderdelen
    tree.add_branch(
        branch_id="smido_onderdelen",
        from_branch_id="smido_diagnose",
        instruction="...",
        description="SMIDO Onderdelen: component isolation",
        status="Isoleer componenten..."
    )
    tree.add_tool(query_vlog_cases, branch_id="smido_onderdelen")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_onderdelen")
    tree.add_tool(query_telemetry_events, branch_id="smido_onderdelen")
    tree.add_tool(Query, branch_id="smido_onderdelen")  # Flexible search
    
    # ===== ALWAYS AVAILABLE (ROOT) =====
    tree.add_tool(CitedSummarizer, branch_id="base")
    tree.add_tool(FakeTextResponse, branch_id="base")
    
    # ===== POST-TOOL CHAINING =====
    # Visualise available after data-generating tools
    tree.add_tool(
        Visualise, 
        branch_id="smido_p3_procesparameters",
        from_tool_ids=["compute_worldstate"]
    )
```

---

## Benefits of This Approach

| Feature | Current | Proposed |
|---------|---------|----------|
| Fast status path | ❌ | ✅ Auto-run via `run_if_true` |
| SMIDO methodology | ✅ | ✅ Preserved |
| Native query tool | ❌ | ✅ Added to all branches |
| Native aggregate | ❌ | ✅ Added where useful |
| Visualization | ❌ | ✅ In P3, P4 (data-heavy phases) |
| Tool clutter | N/A | ✅ Minimal (2-5 per branch) |
| Intent detection | ❌ | ✅ Root instruction |
| Flexibility | ⚠️ | ✅ Best of both worlds |

---

## Example User Flows

### Flow 1: Status Check (FAST PATH)
```
User: "Wat is de huidige status van de machine?"
Agent: get_current_status runs automatically (run_if_true)
  → <200ms response with 5 sensors + flags
  → "Wil je diagnose?" → END (no SMIDO unless requested)
```

### Flow 2: Problem Report (SMIDO)
```
User: "Koelcel bereikt temperatuur niet"
Agent: Detects problem → smido_melding branch
  → get_alarms, get_asset_health
  → Continues M→T→I→D→O
  → visualise in P3 (temp trends)
  → query_vlog_cases in O
```

### Flow 3: Direct Query
```
User: "Hoeveel critical alarms zijn er vandaag?"
Agent: Detects query intent → aggregate (native)
  → Query VSM_TelemetryEvent with filter
  → Return count → END
```

### Flow 4: Manual Lookup
```
User: "Wat zegt de manual over defrost cycles?"
Agent: Detects search intent → query (native) or search_manuals_by_smido
  → Search VSM_ManualSections
  → cited_summarize → END
```

### Flow 5: Visualization Request
```
User: "Show me temperature trend last 24 hours"
Agent: compute_worldstate (P3 tool)
  → visualise (available after compute_worldstate)
  → Chart temps → cited_summarize → END
```

---

## Tool Availability Matrix

| Tool | Root | M | T | I | D(P1) | D(P2) | D(P3) | D(P4) | O | Condition |
|------|------|---|---|---|-------|-------|-------|-------|---|-----------|
| get_current_status | ✅ | - | - | - | - | - | - | - | - | run_if_true |
| text_response | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Always |
| cited_summarize | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Always |
| query | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | When needed |
| aggregate | ✅ | ✅ | - | - | - | ✅ | ✅ | ✅ | - | Stats needed |
| visualise | - | - | - | - | - | - | ✅ | ✅ | - | After data tools |
| get_alarms | - | ✅ | - | - | ✅ | - | - | - | - | SMIDO only |
| get_asset_health | - | ✅ | ✅ | - | - | ✅ | - | - | - | SMIDO only |
| compute_worldstate | - | - | - | - | - | - | ✅ | ✅ | - | SMIDO only |
| search_manuals_by_smido | - | - | - | ✅ | - | ✅ | ✅ | - | ✅ | SMIDO only |
| query_telemetry_events | - | - | - | - | - | - | - | ✅ | ✅ | SMIDO only |
| query_vlog_cases | - | - | - | - | - | - | - | - | ✅ | SMIDO only |
| analyze_sensor_pattern | - | - | - | - | - | - | ✅ | ✅ | - | SMIDO only |

**Total tools at root**: 14 (7 VSM + 6 native + forced_text_response)  
**Average tools per decision**: 3-5 (conditional availability reduces clutter)

---

## Implementation Code

```python
# File: features/vsm_tree/bootstrap.py

def _register_vsm_smido_bootstrapper():
    """Register improved VSM SMIDO bootstrapper with native tools."""
    from features.vsm_tree.smido_tree import (
        _add_m_branch,
        _add_t_branch,
        _add_i_branch,
        _add_d_branch,
        _add_o_branch,
    )
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    
    def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
        """Bootstrap VSM SMIDO + native Elysia tools."""
        logger.info("Bootstrapping VSM SMIDO with native tools...")
        
        # Update root instruction for intent detection
        tree.decision_nodes["base"].instruction = """
        Detect intent en kies pad:
        
        1. STATUS: "wat is status", "hoe gaat het" 
           → get_current_status (auto-runs)
        2. STORING: "werkt niet", "probleem", "temperatuur te hoog"
           → SMIDO workflow (M→T→I→D→O)
        3. VRAAG: "hoeveel", "zoek", "show"
           → query/aggregate
        4. VISUALISATIE: "chart", "plot" (na data ophalen)
           → visualise
        5. GESPREK: groeten, uitleg
           → text_response
        
        Kies MINIMAAL aantal tools per beslispunt.
        """
        
        # Add SMIDO branches
        _add_m_branch(tree)
        _add_t_branch(tree)
        _add_i_branch(tree)
        _add_d_branch(tree)
        _add_o_branch(tree)
        
        # Assign tools (custom + native)
        _assign_tools_with_native(tree)
        
        # Always available at root
        tree.add_tool(CitedSummarizer, branch_id="base")
        tree.add_tool(FakeTextResponse, branch_id="base")
        
        logger.info("VSM SMIDO + native tools bootstrapped")
    
    register_bootstrapper("vsm_smido", vsm_smido_bootstrap)


def _assign_tools_with_native(tree: Tree):
    """Assign VSM custom + native Elysia tools to branches."""
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.visualisation.visualise import Visualise
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
    
    # === ROOT: Fast path ===
    tree.add_tool(get_current_status, branch_id="base", root=True)
    
    # === M - Melding ===
    tree.add_tool(get_alarms, branch_id="smido_melding")
    tree.add_tool(get_asset_health, branch_id="smido_melding")
    tree.add_tool(Query, branch_id="smido_melding")  # Flexible Weaviate search
    tree.add_tool(Aggregate, branch_id="smido_melding")  # Count alarms by severity
    
    # === T - Technisch ===
    tree.add_tool(get_asset_health, branch_id="smido_technisch")
    tree.add_tool(Query, branch_id="smido_technisch")
    
    # === I - Installatie ===
    tree.add_tool(search_manuals_by_smido, branch_id="smido_installatie")
    tree.add_tool(Query, branch_id="smido_installatie")  # Alternative to search_manuals
    
    # === D → P1 (Power) ===
    tree.add_tool(get_alarms, branch_id="smido_p1_power")
    tree.add_tool(Query, branch_id="smido_p1_power")
    
    # === D → P2 (Procesinstellingen) ===
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(get_asset_health, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(Aggregate, branch_id="smido_p2_procesinstellingen")  # Settings stats
    tree.add_tool(Query, branch_id="smido_p2_procesinstellingen")
    
    # === D → P3 (Procesparameters) ===
    tree.add_tool(compute_worldstate, branch_id="smido_p3_procesparameters")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p3_procesparameters")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p3_procesparameters")
    tree.add_tool(Visualise, branch_id="smido_p3_procesparameters")  # Chart temps
    tree.add_tool(Aggregate, branch_id="smido_p3_procesparameters")  # Sensor stats
    tree.add_tool(Query, branch_id="smido_p3_procesparameters")
    
    # === D → P4 (Productinput) ===
    tree.add_tool(compute_worldstate, branch_id="smido_p4_productinput")
    tree.add_tool(query_telemetry_events, branch_id="smido_p4_productinput")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p4_productinput")
    tree.add_tool(Aggregate, branch_id="smido_p4_productinput")  # Environmental stats
    tree.add_tool(Visualise, branch_id="smido_p4_productinput")
    
    # === O - Onderdelen ===
    tree.add_tool(query_vlog_cases, branch_id="smido_onderdelen")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_onderdelen")
    tree.add_tool(query_telemetry_events, branch_id="smido_onderdelen")
    tree.add_tool(Aggregate, branch_id="smido_onderdelen")  # Component failure stats
    tree.add_tool(Query, branch_id="smido_onderdelen")
```

---

## Migration Steps

1. ✅ **Design approved** (this document)
2. [ ] **Update bootstrap.py** - Add native tools with conditions
3. [ ] **Implement get_current_status** with `run_if_true` method
4. [ ] **Test fast path** - Verify <200ms status responses
5. [ ] **Test SMIDO flow** - Verify M→T→I→D→O still works
6. [ ] **Test native tools** - Query/aggregate/visualise in each phase
7. [ ] **Update agent.mdc** - Document new tool availability

**Estimated Effort**: 4-6 hours

---

## Expected Improvements

### Performance
- **Status queries**: 2-3 min → <200ms (via fast path)
- **Specific queries**: NEW capability (direct aggregate/query)
- **SMIDO flow**: Same (3-5 min for full diagnosis)

### Capabilities
- ✅ Chart temperature trends (visualise)
- ✅ Count alarms by type (aggregate)
- ✅ Flexible manual search (query)
- ✅ Statistical analysis (aggregate)
- ✅ Fast status check (get_current_status + run_if_true)

### User Experience
- ✅ Intent-based routing
- ✅ Minimal tool clutter per decision
- ✅ Natural query support ("hoeveel alarms?")
- ✅ Maintains SMIDO for full troubleshooting

---

## Critical Success Factors

1. **get_current_status must have run_if_true** - Auto-detects status keywords
2. **Tool descriptions must be precise** - Agent chooses correct tool per intent
3. **visualise only after data tools** - Use `from_tool_ids` or `is_tool_available`
4. **Root instruction must guide intent** - Clear routing logic
5. **Test all paths** - Status, SMIDO, query, visualize independently

---

## Conclusion

**Recommended approach**: Flat root with conditional tool availability

**Why**:
- Minimal tools per state (2-5 vs all 14)
- Preserves SMIDO integrity
- Adds native Elysia power (query, aggregate, visualise)
- Enables fast path via `run_if_true`
- Follows Elysia design philosophy from blog

**Next**: Implement in `features/vsm_tree/bootstrap.py` and test all flows.

---

**References**:
- [Elysia Blog: Agentic RAG](https://weaviate.io/blog/elysia-agentic-rag)
- Elysia Docs: `docs/offical/Advanced/advanced_tool_construction.md`
- Elysia Docs: `docs/offical/start_here/creating_tools.md`
