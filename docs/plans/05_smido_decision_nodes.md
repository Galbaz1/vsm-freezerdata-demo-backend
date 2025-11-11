# Plan 5: SMIDO Decision Nodes (M, T, I, D, O)

**Priority**: HIGH (Core workflow structure)  
**Parallelization**: Can run in parallel with tool implementation  
**Estimated Time**: 3 hours

---

## Objective

Create Elysia DecisionNodes for each SMIDO phase (M→T→I→D→O) with proper instructions, tool availability, and transition logic. Includes branching for Diagnose phase (4 P's: P1, P2, P3, P4).

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md` (lines 104-147 - SMIDO mapping strategy)
- `docs/diagrams/vsm_agent_architecture.mermaid` (SMIDO nodes and flow)
- `CLAUDE.md` (lines 247-263 - SMIDO methodology)

**SMIDO Methodology**:
- `docs/diagrams/smido_main_flowchart.mermaid` (complete SMIDO flowchart)
- `docs/diagrams/smido_3ps_diagnosis.mermaid` (4 P's detail)
- `docs/diagrams/smido_methodology.md` (if exists)

**Manual Reference**:
- `features/extraction/production_output/storingzoeken-koeltechniek_theorie_179/storingzoeken-koeltechniek_theorie_179.text_chunks.jsonl` (SMIDO section, grep "SMIDO\|melding\|technisch")

**Elysia Tree Pattern**:
- `elysia/tree/tree.py` (Tree class)
- `elysia/tree/objects.py` (DecisionNode if exists)
- `docs/diagrams/elysia/03_decision_tree_structure.mermaid` (Elysia tree architecture)

---

## Implementation Tasks

### Task 5.1: Create VSM Tree with SMIDO Branches

**File**: `features/vsm_tree/smido_tree.py`

**Implementation Spec**:

```python
from elysia import Tree

def create_vsm_tree() -> Tree:
    """
    Create VSM tree with SMIDO branches.
    Uses branch_initialisation="empty" to manually construct.
    """
    tree = Tree(
        branch_initialisation="empty",
        agent_description="You are a Virtual Service Mechanic helping junior technicians troubleshoot cooling installations using the SMIDO methodology.",
        style="Professional, clear, and supportive. Explain technical concepts in simple Dutch terms.",
        end_goal="The technician has identified the root cause and knows how to fix the installation, or all diagnostic options have been exhausted."
    )
    
    # Add SMIDO branches (M→T→I→D→O)
    _add_m_branch(tree)
    _add_t_branch(tree)
    _add_i_branch(tree)
    _add_d_branch(tree)  # Includes P1-P4 sub-branches
    _add_o_branch(tree)
    
    # Add tools to branches (after tools are imported)
    _assign_tools_to_branches(tree)
    
    return tree


def _add_m_branch(tree: Tree):
    """M - MELDING: Symptom collection"""
    tree.add_branch(
        branch_id="smido_melding",
        instruction="""
        You are in the MELDING (Symptom Collection) phase.
        
        Tasks:
        1. Collect symptoms: What is the problem? When did it start?
        2. Assess urgency: Are goods at risk? What is current temperature?
        3. Use GetAlarms to check active alarms
        4. Use GetAssetHealth for health summary
        
        Questions to ask:
        - Is de melding compleet? Waar staat de installatie?
        - Welke symptomen zijn waargenomen?
        - Hoe urgent is de situatie?
        
        Once symptoms are clear, proceed to TECHNISCH phase.
        """,
        description="Collect symptoms and assess urgency",
        root=True,  # M is the root of SMIDO
        status="Collecting symptoms..."
    )
```

def _add_t_branch(tree: Tree):
    """T - TECHNISCH: Visual/audio inspection"""
    tree.add_branch(
        branch_id="smido_technisch",
        instruction="""
        You are in the TECHNISCH (Technical Quick Check) phase.
        
        Tasks:
        1. Ask: Is there a visually/audibly obvious defect?
        2. Check: Loose wires? Strange sounds? Leaks?
        3. If obvious defect → Fix and end
        4. If no obvious defect → Proceed to INSTALLATIE
        
        Guide: Kijk en luister eerst. Direct waarneembaar defect?
        """,
        description="Quick technical inspection for obvious defects",
        from_branch_id="smido_melding",  # T comes after M
        status="Performing technical check..."
    )
```

def _add_i_branch(tree: Tree):
    """I - INSTALLATIE VERTROUWD: Familiarity check"""
    tree.add_branch(
        branch_id="smido_installatie",
        instruction="""
        You are in the INSTALLATIE VERTROUWD phase.
        
        Tasks:
        1. Check technician familiarity with installation
        2. Provide schemas if needed (SearchManualsBySMIDO)
        3. Show component diagrams (basic_refrigeration_cycle)
        
        Questions: Heb je ervaring? Heb je het schema? Ken je de componenten?
        
        Once familiar, proceed to DIAGNOSE (4 P's).
        """,
        description="Verify technician familiarity with installation",
        from_branch_id="smido_technisch",  # I comes after T
        status="Checking installation familiarity..."
    )
```

def _add_d_branch(tree: Tree):
    """
    D - DIAGNOSE: Parent branch for 4 P's
    Creates P1, P2, P3, P4 as sub-branches
    """
    tree.add_branch(
        branch_id="smido_diagnose",
        instruction="""
        You are in the DIAGNOSE phase. Use the 4 P's:
        
        P1 - POWER, P2 - PROCESINSTELLINGEN, P3 - PROCESPARAMETERS, P4 - PRODUCTINPUT
        
        Check systematically or jump to suspected P based on symptoms.
        """,
        description="Systematic diagnosis using 4 P's approach",
        from_branch_id="smido_installatie",  # D comes after I
        status="Starting systematic diagnosis..."
    )

    # P1 - Power
    tree.add_branch(
        branch_id="smido_p1_power",
        instruction="""
        P1 - POWER: Electrical supply checks
        
        Check: Spanning? Zekeringen? Compressor stroomopname?
        Tools: GetAlarms
        """,
        description="Check electrical power supply to all components",
        from_branch_id="smido_diagnose",  # P1 is sub-branch of D
        status="Checking power supply..."
    )
    
    # P2 - Procesinstellingen
    tree.add_branch(
        branch_id="smido_p2_procesinstellingen",
        instruction="""
        P2 - PROCESINSTELLINGEN: Settings vs design
        
        Check: Pressostaat, thermostaat, ontdooitijden, regelaar parameters
        Tools: GetAssetHealth, SearchManualsBySMIDO
        """,
        description="Verify settings match design/commissioning values",
        from_branch_id="smido_diagnose",  # P2 is sub-branch of D
        status="Checking settings vs design..."
    )
    
    # P3 - Procesparameters
    tree.add_branch(
        branch_id="smido_p3_procesparameters",
        instruction="""
        P3 - PROCESPARAMETERS: Measurements vs design
        
        Check: Drukken, temperaturen, oververhitting, onderkoeling
        Tools: ComputeWorldState, AnalyzeSensorPattern, SearchManualsBySMIDO
        """,
        description="Measure and compare process parameters against design",
        from_branch_id="smido_diagnose",  # P3 is sub-branch of D
        status="Measuring process parameters..."
    )
    
    # P4 - Productinput
    tree.add_branch(
        branch_id="smido_p4_productinput",
        instruction="""
        P4 - PRODUCTINPUT: External conditions vs design
        
        Check: Omgevingstemperatuur, belading, deurgebruik, condensor condities
        Tools: ComputeWorldState, QueryTelemetryEvents, AnalyzeSensorPattern
        """,
        description="Check if external conditions are within design parameters",
        from_branch_id="smido_diagnose",  # P4 is sub-branch of D
        status="Checking external conditions..."
    )
```

def _add_o_branch(tree: Tree):
    """O - ONDERDELEN UITSLUITEN: Component isolation"""
    tree.add_branch(
        branch_id="smido_onderdelen",
        instruction="""
        You are in the ONDERDELEN UITSLUITEN (Component Isolation) phase.
        
        All 4 P's checked. Now isolate defective component:
        1. QueryVlogCases - find similar cases
        2. SearchManualsBySMIDO - component procedures
        3. Test component chains
        
        Welke component is defect? Provide repair guidance.
        """,
        description="Isolate defective component and provide repair solution",
        from_branch_id="smido_diagnose",  # O comes after D (all P's)
        status="Isolating defective component..."
    )


def _assign_tools_to_branches(tree: Tree):
    """
    Assign tools to appropriate SMIDO branches.
    Note: Tools must be imported first from elysia.api.custom_tools
    """
    from elysia.api.custom_tools import (
        get_alarms, get_asset_health,
        compute_worldstate, query_telemetry_events,
        search_manuals_by_smido, query_vlog_cases,
        analyze_sensor_pattern
    )
    
    # M - Melding: Alarms + Health check
    tree.add_tool(get_alarms, branch_id="smido_melding")
    tree.add_tool(get_asset_health, branch_id="smido_melding")
    
    # T - Technisch: Health check
    tree.add_tool(get_asset_health, branch_id="smido_technisch")
    
    # I - Installatie: Manual search
    tree.add_tool(search_manuals_by_smido, branch_id="smido_installatie")
    
    # P1 - Power: Alarms
    tree.add_tool(get_alarms, branch_id="smido_p1_power")
    
    # P2 - Procesinstellingen: Manual search + Health
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p2_procesinstellingen")
    tree.add_tool(get_asset_health, branch_id="smido_p2_procesinstellingen")
    
    # P3 - Procesparameters: WorldState + Pattern analysis + Manuals
    tree.add_tool(compute_worldstate, branch_id="smido_p3_procesparameters")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p3_procesparameters")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_p3_procesparameters")
    
    # P4 - Productinput: WorldState + Events + Pattern
    tree.add_tool(compute_worldstate, branch_id="smido_p4_productinput")
    tree.add_tool(query_telemetry_events, branch_id="smido_p4_productinput")
    tree.add_tool(analyze_sensor_pattern, branch_id="smido_p4_productinput")
    
    # O - Onderdelen: Vlogs + Manuals + Events
    tree.add_tool(query_vlog_cases, branch_id="smido_onderdelen")
    tree.add_tool(search_manuals_by_smido, branch_id="smido_onderdelen")
    tree.add_tool(query_telemetry_events, branch_id="smido_onderdelen")
```

---

## Verification

**Success Criteria**:
- [ ] All 9 nodes created (M, T, I, D, P1, P2, P3, P4, O)
- [ ] Instructions reference correct SMIDO methodology
- [ ] 4 P's properly implemented (not 3!)
- [ ] Tools assigned to appropriate nodes
- [ ] Tree structure follows M→T→I→D[P1,P2,P3,P4]→O

**Test**:
```python
# Verify tree structure
tree = create_vsm_tree()
branches = tree.get_all_branches()
print(f"Branches: {[b.id for b in branches]}")

# Expected: smido_melding, smido_technisch, smido_installatie, smido_diagnose, 
#           smido_p1_power, smido_p2_procesinstellingen, smido_p3_procesparameters, 
#           smido_p4_productinput, smido_onderdelen
```

---

## Dependencies

**Required Before**:
- ⏳ Tools implemented (Plans 1-4) - for adding to nodes

**Blocks**:
- SMIDO Orchestrator (Plan 6)
- A3 scenario testing

---

## Related Files

**To Create**:
- `features/vsm_tree/smido_nodes.py`
- `features/vsm_tree/__init__.py`
- `features/vsm_tree/tests/test_smido_nodes.py`

**To Reference**:
- `docs/diagrams/smido_main_flowchart.mermaid`
- `docs/diagrams/smido_3ps_diagnosis.mermaid`


