"""
Cache Management API Routes.

Provides endpoints for managing Gemini context cache:
- POST /cache/refresh - Manually refresh the cache
- GET /cache/stats - Get cache statistics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cache", tags=["cache"])


class CacheRefreshResponse(BaseModel):
    """Response model for cache refresh endpoint."""
    success: bool
    cache_name: str = None
    message: str


@router.post("/refresh", response_model=CacheRefreshResponse)
async def refresh_context_cache():
    """
    Manually refresh the Gemini context cache.
    Use when tools or agent description changes.
    
    Returns:
        CacheRefreshResponse with success status and new cache name
        
    Raises:
        HTTPException: If tree not initialized or cache refresh fails
    """
    try:
        # Import here to avoid circular dependencies
        from elysia.api.services.tree import TreeManager
        
        # Get the tree manager instance
        tree_manager = TreeManager()
        
        # Get the current tree (assumes default tree is used)
        # This will need adjustment based on actual Elysia tree storage mechanism
        tree = tree_manager.get_tree("default")
        
        if not tree:
            raise HTTPException(status_code=500, detail="VSM tree not initialized")
        
        if not hasattr(tree, '_context_cache'):
            raise HTTPException(status_code=500, detail="Context cache not configured")
        
        cache_name = tree._context_cache.refresh_cache(tree)
        
        if cache_name:
            return CacheRefreshResponse(
                success=True,
                cache_name=cache_name,
                message="Cache refreshed successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to refresh cache")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache refresh failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_cache_stats():
    """
    Get current cache statistics.
    
    Returns:
        Dictionary with cache statistics including:
        - cache_name: Current cache identifier
        - created_at: ISO timestamp of cache creation
        - ttl_seconds: Time-to-live in seconds
        - is_active: Whether cache is currently active
        
    Raises:
        HTTPException: If unable to retrieve cache stats
    """
    try:
        # Import here to avoid circular dependencies
        from elysia.api.services.tree import TreeManager
        
        # Get the tree manager instance
        tree_manager = TreeManager()
        
        # Get the current tree
        tree = tree_manager.get_tree("default")
        
        if tree and hasattr(tree, '_context_cache'):
            return tree._context_cache.get_cache_stats()
        else:
            return {
                "error": "Cache not configured",
                "cache_name": None,
                "created_at": None,
                "ttl_seconds": None,
                "is_active": False
            }
    
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

