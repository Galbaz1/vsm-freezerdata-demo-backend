"""
Bootstrap system for automatically registering feature-specific tools and branches.

This module provides a generic bootstrap registry that allows feature modules
to register their tree initialization logic. When a tree is created with
branch_initialisation="empty", registered bootstrappers are invoked to add
branches and tools.

Usage:
    # Register a bootstrapper
    from features.vsm_tree.bootstrap import register_bootstrapper
    
    def my_feature_bootstrap(tree, context):
        # Add branches and tools to tree
        tree.add_branch(...)
        tree.add_tool(...)
    
    register_bootstrapper("my_feature", my_feature_bootstrap)
    
    # Bootstrap is automatically invoked during TreeManager.add_tree()
    # when branch_initialisation="empty" and feature_bootstrappers config is set
"""

from typing import Callable, Dict, Optional, Any
from elysia.tree.tree import Tree
import logging

logger = logging.getLogger(__name__)

# Global registry of bootstrappers
_BOOTSTRAPPER_REGISTRY: Dict[str, Callable[[Tree, Dict[str, Any]], None]] = {}


def register_bootstrapper(name: str, bootstrapper: Callable[[Tree, Dict[str, Any]], None]) -> None:
    """
    Register a bootstrapper function that will be called to initialize a tree.
    
    Args:
        name: Unique identifier for this bootstrapper (e.g., "vsm_smido")
        bootstrapper: Function that takes (tree: Tree, context: dict) and adds branches/tools
    """
    if name in _BOOTSTRAPPER_REGISTRY:
        logger.warning(f"Bootstrapper '{name}' is already registered. Overwriting.")
    
    _BOOTSTRAPPER_REGISTRY[name] = bootstrapper
    logger.debug(f"Registered bootstrapper: {name}")


def get_bootstrapper(name: str) -> Optional[Callable[[Tree, Dict[str, Any]], None]]:
    """
    Get a registered bootstrapper by name.
    
    Args:
        name: Bootstrapper identifier
        
    Returns:
        Bootstrapper function or None if not found
    """
    return _BOOTSTRAPPER_REGISTRY.get(name)


def list_bootstrappers() -> list[str]:
    """
    List all registered bootstrapper names.
    
    Returns:
        List of bootstrapper names
    """
    return list(_BOOTSTRAPPER_REGISTRY.keys())


def bootstrap_tree(tree: Tree, bootstrapper_names: list[str], context: Optional[Dict[str, Any]] = None) -> None:
    """
    Apply registered bootstrappers to a tree.
    
    Args:
        tree: The Tree instance to bootstrap
        bootstrapper_names: List of bootstrapper names to apply
        context: Optional context dict passed to bootstrappers (e.g., user_id, config)
    """
    if context is None:
        context = {}
    
    applied = []
    failed = []
    
    for name in bootstrapper_names:
        bootstrapper = get_bootstrapper(name)
        if bootstrapper is None:
            logger.warning(f"Bootstrapper '{name}' not found. Skipping.")
            failed.append(name)
            continue
        
        try:
            logger.debug(f"Applying bootstrapper: {name}")
            bootstrapper(tree, context)
            applied.append(name)
            logger.info(f"Successfully applied bootstrapper: {name}")
        except Exception as e:
            logger.error(f"Error applying bootstrapper '{name}': {e}", exc_info=True)
            failed.append(name)
    
    if applied:
        logger.info(f"Applied {len(applied)} bootstrapper(s): {', '.join(applied)}")
    if failed:
        logger.warning(f"Failed to apply {len(failed)} bootstrapper(s): {', '.join(failed)}")


# ============================================================================
# VSM SMIDO Flat Root Bootstrap (Weaviate's one_branch Pattern)
# ============================================================================

def _register_root_tools(tree: Tree) -> None:
    """
    Register all core tools at base root following one_branch pattern.
    
    Pattern: elysia/tree/tree.py lines 261-265
    Adds 12 tools total: 8 VSM custom + 4 native (visualise handled separately)
    """
    # Import VSM custom tools
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
    
    # Import native Elysia tools
    from elysia.tools.retrieval.query import Query
    from elysia.tools.retrieval.aggregate import Aggregate
    from elysia.tools.text.text import CitedSummarizer, FakeTextResponse
    
    # Always-available tools (following one_branch pattern)
    tree.add_tool(branch_id="base", tool=CitedSummarizer)
    tree.add_tool(branch_id="base", tool=FakeTextResponse)
    
    # VSM custom tools
    tree.add_tool(branch_id="base", tool=get_current_status)
    tree.add_tool(branch_id="base", tool=get_alarms)
    tree.add_tool(branch_id="base", tool=get_asset_health)
    tree.add_tool(branch_id="base", tool=compute_worldstate)
    tree.add_tool(branch_id="base", tool=query_telemetry_events)
    tree.add_tool(branch_id="base", tool=search_manuals_by_smido)
    tree.add_tool(branch_id="base", tool=query_vlog_cases)
    tree.add_tool(branch_id="base", tool=analyze_sensor_pattern)
    
    # Native tools
    tree.add_tool(branch_id="base", tool=Query, summariser_in_tree=True)
    tree.add_tool(branch_id="base", tool=Aggregate)
    
    logger.debug("Registered 12 tools at base root")


def _add_smido_post_tool_chains(tree: Tree) -> None:
    """
    Add SMIDO workflow chains using from_tool_ids pattern.
    
    Pattern: elysia/tree/tree.py line 248 (SummariseItems with from_tool_ids)
    Reference: docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md lines 144-214
    
    Implements 3 SMIDO flows: M (Melding), P3 (Parameters), O (Onderdelen)
    """
    from elysia.api.custom_tools import (
        get_asset_health,
        search_manuals_by_smido,
        analyze_sensor_pattern,
        query_telemetry_events
    )
    from elysia.tools.retrieval.aggregate import Aggregate
    
    # M flow: After get_alarms completes → offer health check + manual search
    tree.add_tool(get_asset_health, branch_id="base", from_tool_ids=["get_alarms"])
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["get_alarms"])
    
    # P3 flow: After compute_worldstate completes → offer pattern analysis
    tree.add_tool(analyze_sensor_pattern, branch_id="base", from_tool_ids=["compute_worldstate"])
    
    # O flow: After query_vlog_cases completes → offer manual + stats
    tree.add_tool(search_manuals_by_smido, branch_id="base", from_tool_ids=["query_vlog_cases"])
    tree.add_tool(Aggregate, branch_id="base", from_tool_ids=["query_vlog_cases"])
    
    logger.debug("Added SMIDO post-tool chains (M, P3, O flows)")


def _add_visualization_chains(tree: Tree) -> None:
    """
    Make Visualise available after any data-producing tool.
    
    Pattern: Multi-parent from_tool_ids
    Reference: docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md lines 217-222
    
    Visualise is cross-cutting, not SMIDO-specific.
    """
    from elysia.tools.visualisation.visualise import Visualise
    
    # Visualise available after these 4 data tools
    data_tool_ids = [
        "compute_worldstate",
        "get_asset_health",
        "query",
        "aggregate"
    ]
    
    for tool_id in data_tool_ids:
        tree.add_tool(Visualise, branch_id="base", from_tool_ids=[tool_id])
    
    logger.debug("Added Visualise chains after 4 data tools")


def _set_root_instruction(tree: Tree) -> None:
    """
    Set clear root instruction following one_branch style.
    
    Pattern: elysia/tree/tree.py lines 254-258
    Reference: docs/project/IMPROVED_VSM_BRANCHING_STRATEGY.md lines 93-121
    
    Key principle: NO keyword detection. Trust LLM to read tool descriptions.
    """
    tree.decision_nodes["base"].instruction = """
Choose tool based on user's immediate need and conversation context.
Decide based on tools available and their descriptions.
Read them thoroughly and match actions to user prompt.

Tool categories for reference:
- Quick status checks: get_current_status, get_alarms, get_asset_health
- Deep analysis: compute_worldstate, analyze_sensor_pattern
- Knowledge search: search_manuals_by_smido, query_vlog_cases, query
- Statistics: aggregate
- Visualization: visualise (after data tools)
- Communication: cited_summarize, text_response

After a tool completes, more tools may become available based on context.
"""
    logger.debug("Set root instruction (one_branch style)")


# Register VSM SMIDO bootstrapper
def _register_vsm_smido_bootstrapper():
    """Register the VSM SMIDO flat root bootstrapper."""
    
    def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
        """
        Bootstrap VSM following Weaviate's one_branch flat root pattern.
        
        Replaces deep SMIDO hierarchy with:
        - Flat root (all 12 tools visible at base)
        - Post-tool chains for SMIDO flows
        - Native Elysia tools integrated
        
        Pattern: elysia/tree/tree.py lines 250-266 (one_branch_init)
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
        
        tool_count = len(tree.decision_nodes['base'].options)
        logger.info(f"VSM flat root bootstrapped: {tool_count} tools at root")
    
    register_bootstrapper("vsm_smido", vsm_smido_bootstrap)


# Auto-register VSM SMIDO bootstrapper on module import
_register_vsm_smido_bootstrapper()

