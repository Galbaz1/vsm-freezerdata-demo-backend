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


# Register VSM SMIDO bootstrapper
def _register_vsm_smido_bootstrapper():
    """Register the VSM SMIDO bootstrapper."""
    from features.vsm_tree.smido_tree import (
        _add_m_branch,
        _add_t_branch,
        _add_i_branch,
        _add_d_branch,
        _add_o_branch,
        _assign_tools_to_branches
    )
    
    def vsm_smido_bootstrap(tree: Tree, context: Dict[str, Any]) -> None:
        """
        Bootstrap VSM SMIDO tree structure.
        
        Adds all SMIDO branches (M→T→I→D[P1,P2,P3,P4]→O) and assigns tools.
        """
        logger.info("Bootstrapping VSM SMIDO tree structure...")
        
        # Add SMIDO branches (M→T→I→D→O)
        _add_m_branch(tree)
        _add_t_branch(tree)
        _add_i_branch(tree)
        _add_d_branch(tree)  # Includes P1-P4 sub-branches
        _add_o_branch(tree)
        
        # Assign tools to branches
        _assign_tools_to_branches(tree)
        
        logger.info("VSM SMIDO tree structure bootstrapped successfully")
    
    register_bootstrapper("vsm_smido", vsm_smido_bootstrap)


# Auto-register VSM SMIDO bootstrapper on module import
_register_vsm_smido_bootstrapper()

