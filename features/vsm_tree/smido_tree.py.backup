"""
SMIDO Decision Tree - Creates Elysia Tree with SMIDO methodology branches.

SMIDO Flow: M → T → I → D[P1, P2, P3, P4] → O
- M: Melding (Symptom Collection)
- T: Technisch (Quick Technical Check)
- I: Installatie Vertrouwd (Familiarity Check)
- D: Diagnose (4 P's: Power, Procesinstellingen, Procesparameters, Productinput)
- O: Onderdelen Uitsluiten (Component Isolation)
"""

from elysia import Tree
from typing import Tuple, Optional, Union
from features.vsm_tree.context_manager import ContextManager
from features.vsm_tree.smido_orchestrator import SMIDOOrchestrator


def create_vsm_tree(
    with_orchestrator: bool = False,
    asset_id: Optional[str] = None
) -> Union[Tree, Tuple[Tree, SMIDOOrchestrator, ContextManager]]:
    """
    Create VSM tree with SMIDO branches.
    Uses branch_initialisation="empty" to manually construct.
    
    Args:
        with_orchestrator: If True, returns tuple (tree, orchestrator, context_manager)
        asset_id: Optional asset ID for context manager initialization
    
    Returns:
        Tree or Tuple[Tree, SMIDOOrchestrator, ContextManager]: Configured Elysia Tree with SMIDO branches and tools
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
    
    # Add tools to branches
    _assign_tools_to_branches(tree)
    
    if with_orchestrator:
        # Create context manager and orchestrator
        context_manager = ContextManager()
        if asset_id:
            try:
                context_manager.load_context(asset_id)
            except FileNotFoundError:
                # If enrichment file not found, continue without context
                pass
        
        orchestrator = SMIDOOrchestrator(tree, context_manager)
        
        return tree, orchestrator, context_manager
    
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
    Note: Tools must be imported from elysia.api.custom_tools
    """
    from elysia.api.custom_tools import (
        get_alarms,
        get_asset_health,
        compute_worldstate,
        query_telemetry_events,
        search_manuals_by_smido,
        query_vlog_cases,
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

