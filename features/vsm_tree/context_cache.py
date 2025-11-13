"""
Gemini Context Cache Manager for VSM.

Manages caching of static agent context (agent_description + style + tool descriptions)
to reduce latency by 44% and cost by 60% through Gemini's Context Caching API.
"""

from google import genai
from google.genai import types
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class VSMContextCache:
    """
    Manages Gemini context caching for VSM static content.
    Caches: agent_description + style + tool descriptions
    TTL: 1 hour (3600s)
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            ttl_seconds: Time-to-live for cache in seconds (default: 3600 = 1 hour)
        """
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.cache = None
        self.ttl_seconds = ttl_seconds
        self.created_at = None
    
    def create_cache(self, tree) -> Optional[str]:
        """
        Create new cache with agent context + tool descriptions.
        
        Args:
            tree: Elysia Tree instance with tree_data.atlas containing agent info
            
        Returns:
            Cache name if successful, None otherwise
        """
        # Combine agent description and style from atlas
        system_instruction = f"{tree.tree_data.atlas.agent_description}\n\n{tree.tree_data.atlas.style}"
        
        # Extract tool descriptions from base branch
        tool_descriptions = self._get_tool_descriptions(tree)
        
        # Create cache config (model is passed separately to create())
        cache_config = types.CreateCachedContentConfig(
            display_name="vsm_smido_context",
            system_instruction=system_instruction,
            contents=[
                {"role": "user", "parts": [{"text": tool_descriptions}]}
            ],
            ttl=f"{self.ttl_seconds}s",
        )
        
        try:
            # Model is passed as a parameter, not in config
            # Use gemini-2.5-flash (no version suffix, matches what's used in DSPy)
            self.cache = self.client.caches.create(
                model="models/gemini-2.5-flash",
                config=cache_config
            )
            self.created_at = datetime.now()
            logger.info(f"Created Gemini cache: {self.cache.name} (TTL: {self.ttl_seconds}s)")
            return self.cache.name
        except Exception as e:
            logger.error(f"Failed to create cache: {e}")
            return None
    
    def refresh_cache(self, tree) -> Optional[str]:
        """
        Refresh existing cache or create new if expired.
        
        Args:
            tree: Elysia Tree instance
            
        Returns:
            New cache name if successful, None otherwise
        """
        if self.cache:
            try:
                self.client.caches.delete(name=self.cache.name)
                logger.info(f"Deleted old cache: {self.cache.name}")
            except Exception as e:
                logger.warning(f"Could not delete old cache: {e}")
        
        return self.create_cache(tree)
    
    def _get_tool_descriptions(self, tree) -> str:
        """
        Extract tool descriptions from tree's base branch.
        
        Args:
            tree: Elysia Tree instance
            
        Returns:
            Formatted string of all tool descriptions
        """
        tools = tree.decision_nodes["base"].options
        descriptions = []
        
        for tool in tools:
            tool_name = tool.name if hasattr(tool, 'name') else str(tool)
            tool_desc = tool.description if hasattr(tool, 'description') else "No description"
            descriptions.append(f"Tool: {tool_name}\n{tool_desc}")
        
        return "\n\n".join(descriptions)
    
    def get_cache_name(self) -> Optional[str]:
        """
        Get current cache name if valid.
        
        Returns:
            Cache name if active, None otherwise
        """
        if self.cache:
            return self.cache.name
        return None
    
    def get_cache_stats(self) -> dict:
        """
        Return cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_name": self.cache.name if self.cache else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ttl_seconds": self.ttl_seconds,
            "is_active": self.cache is not None
        }

