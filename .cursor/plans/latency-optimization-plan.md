# VSM Latency Optimization Plan

**Goal**: Reduce latency for both base model (decision agent) and complex model (tool execution) routes by 50-70%.

**Current Pain Points**:
- Decision agent (gemini-2.5-flash) takes ~2-5 seconds per decision
- Complex model (gemini-2.5-pro) tools take ~5-15 seconds per call
- Long context inputs (collection schemas, environment, tool descriptions)
- Multiple LLM calls per user query (decision + tool + summarization)

---

## Strategy Overview

### Tier 1: Quick Wins (0-2 days) - Target 30% latency reduction
1. Implement `run_if_true` for get_current_status (bypass decision LLM)
2. Cache WorldState computations
3. Disable chain-of-thought for base model decisions
4. Reduce tool descriptions verbosity

### Tier 2: Structural Optimizations (3-5 days) - Target additional 20% reduction
5. Minimize collection schemas in context
6. Implement environment pruning
7. Optimize preprocessing payload mappings
8. Batch Weaviate queries

### Tier 3: Advanced (1-2 weeks) - Target additional 20% reduction
9. Implement parallel tool execution
10. Add request-level caching
11. Optimize agent prompts (shorter, more directive)
12. Consider model downgrade for non-critical paths

---

## Research Insights from Exa (Nov 2025)

**Key Findings**:
1. **Gemini Context Caching** reduces latency by **43-44%** for repeated contexts (3.7s → 2.1s)
2. **Batch API** for non-real-time workloads (up to 24h processing, 50% cost reduction)
3. **Hybrid Search** in Weaviate can be optimized with alpha tuning (0.5 default, tune per collection)
4. **DSPy asyncify** enables parallel LLM calls with `async_max_workers=4` (default: 8)
5. **Streaming responses** with `generate_content_stream` reduces time-to-first-token by 50%
6. **Weaviate reciprocal rank fusion (RRF)** formula: 1/(RANK + 60) for hybrid search
7. **Connection pooling** + **DNS caching** reduces API overhead by 20-30%

**Sources**: Google Blog (Gemini 2.5), Weaviate docs (Hybrid Search), DSPy docs (asyncify), Research benchmarks (Context caching)

---

## Tier 1: Quick Wins (30-50% reduction)

### 1.1 Gemini Context Caching (NEW - HIGHEST IMPACT)

**Problem**: Agent description + collection schemas + tool descriptions are sent with EVERY request (~5000+ tokens).

**Solution**: Use Gemini's Context Caching API to cache static context.

**Benchmark**: 43.6% latency reduction (3773ms → 2127ms in production tests)

**Implementation**:
```python
# elysia/config.py or features/vsm_tree/smido_tree.py

from google import genai
from google.genai import types
import datetime

class VSMContextCache:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.cache = None
        self._cache_ttl = 3600  # 1 hour (reduce cost, context rarely changes)
    
    def create_or_update_cache(self, tree):
        """
        Cache static context that doesn't change per query:
        - Agent description (system instruction)
        - Collection schemas (preprocessed)
        - Tool descriptions
        """
        # Combine static context
        system_instruction = tree.agent_description + "\n\n" + tree.style
        
        # Get collection schemas (if enabled)
        collection_context = self._get_collection_schemas()
        
        # Get tool descriptions
        tool_context = self._get_tool_descriptions(tree)
        
        # Create cached content
        cache_config = types.CreateCachedContentConfig(
            model="models/gemini-2.5-flash-001",
            display_name="vsm_smido_context",
            system_instruction=system_instruction,
            contents=[
                {"role": "user", "parts": [{"text": collection_context}]},
                {"role": "user", "parts": [{"text": tool_context}]}
            ],
            ttl=f"{self._cache_ttl}s",
        )
        
        if self.cache:
            # Update existing cache
            self.cache = self.client.caches.update(
                name=self.cache.name,
                config=cache_config
            )
        else:
            # Create new cache
            self.cache = self.client.caches.create(config=cache_config)
        
        return self.cache.name
    
    def _get_collection_schemas(self):
        """Get preprocessed Weaviate collection schemas."""
        # TODO: Implement based on Elysia's schema system
        return "Collection schemas: VSM_ManualSections, VSM_ManualImage, VSM_TelemetryEvent, ..."
    
    def _get_tool_descriptions(self, tree):
        """Get all tool descriptions from the tree."""
        tools = tree.decision_nodes["base"].options
        descriptions = []
        for tool in tools:
            descriptions.append(f"Tool: {tool.name}\n{tool.description}")
        return "\n\n".join(descriptions)

# Usage in create_vsm_tree:
def create_vsm_tree(...):
    tree = Tree(...)
    
    # Create context cache
    cache_manager = VSMContextCache()
    cache_name = cache_manager.create_or_update_cache(tree)
    
    # Configure DSPy LMs to use cache
    dspy.settings.configure(
        lm=dspy.LM(
            "gemini/gemini-2.5-flash",
            cache=True,
            cached_content=cache_name  # Use the cache!
        )
    )
    
    return tree
```

**Trade-offs**:
- **Pro**: 44% latency reduction on ALL decision steps
- **Pro**: 60% cost reduction on cached tokens (Gemini pricing: cached tokens are 75% cheaper)
- **Con**: First request after cache expiry takes ~4s (cache creation time)
- **Con**: Cache updates needed if tools/schemas change (rare in production)

**Files**:
- `features/vsm_tree/context_cache.py`: New file for cache management
- `features/vsm_tree/smido_tree.py`: Integrate cache_manager
- `elysia/config.py`: Add cache TTL config

**Expected Gain**: -1.6 seconds per decision (44% reduction) ← **BIGGEST WIN**

**Test**:
```bash
python3 scripts/test_context_caching.py
# First call: ~4s (cache creation)
# Second call: ~2s (cache hit)
# Verify: response.usage_metadata.cached_content_token_count > 0
```

**Production Monitoring**:
```python
# Log cache hit rate
if response.usage_metadata.cached_content_token_count > 0:
    logger.info(f"Cache HIT: {response.usage_metadata.cached_content_token_count} tokens cached")
else:
    logger.warning("Cache MISS: Consider refreshing cache")
```

---

### 1.2 Streaming Responses (NEW - UX WIN)

**Problem**: User waits for complete LLM response before seeing anything.

**Solution**: Stream responses to frontend (time-to-first-token is 50% faster).

**Benchmark**: First token in 1-2s vs 4-5s for full response

**Implementation**:
```python
# elysia/api/custom_tools.py

from google import genai

@tool(status="Analyzing...", branch_id="base")
async def get_asset_health(
    asset_id: str = "135_1570",
    tree_data=None,
    complex_lm=None,
    **kwargs
):
    """..."""
    # Compute WorldState (fast, <500ms)
    worldstate = engine.compute_worldstate(asset_id, timestamp)
    
    # Stream LLM analysis instead of waiting for full response
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    prompt = f"Analyze this WorldState for 'uit balans' conditions:\n{worldstate}"
    
    stream = client.models.generate_content_stream(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            cached_content=tree_data.environment.hidden_environment.get("cache_name"),
            temperature=0.1
        )
    )
    
    # Yield Status updates as tokens arrive
    partial_text = ""
    for chunk in stream:
        if chunk.text:
            partial_text += chunk.text
            yield Status(f"Analysis: {partial_text[:100]}...")  # Show progress
    
    # Final Result
    yield Result(
        objects=[{"analysis": partial_text, "worldstate": worldstate}],
        payload_type="document",
        metadata={"source": "get_asset_health"}
    )
```

**Trade-offs**:
- **Pro**: User sees progress immediately (perceived latency ↓ 60%)
- **Pro**: Can cancel long-running requests early
- **Con**: Slightly more complex error handling
- **Con**: Not compatible with DSPy ChainOfThought (requires custom implementation)

**Expected Gain**: Perceived latency -2-3 seconds (first token in 1-2s)

---

### 1.3 Implement `run_if_true` for get_current_status

**Problem**: Every conversation starts with decision LLM choosing `get_current_status`, adding 2-3 seconds overhead.

**Solution**: Use `run_if_true` method to automatically run on first message.

**Implementation**:
```python
# elysia/api/custom_tools.py

@tool(status="Quick status check...", branch_id="base")
async def get_current_status(
    asset_id: str = "135_1570",
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """..."""
    # Existing implementation
    ...

# Add run_if_true method
async def get_current_status_run_if_true(
    tree_data,
    base_lm,
    complex_lm,
    client_manager,
) -> tuple[bool, dict]:
    """
    Auto-run on first message if no environment data exists yet.
    Bypasses LLM decision for fast initial status.
    """
    # Run if: first message + environment empty
    is_first_message = len(tree_data.conversation_history) <= 1
    env_empty = tree_data.environment.is_empty()
    
    if is_first_message and env_empty:
        return (True, {"asset_id": "135_1570"})
    
    return (False, {})
```

**Files**:
- `elysia/api/custom_tools.py`: Add run_if_true method to get_current_status
- Convert from `@tool` decorator to `Tool` class to support run_if_true

**Expected Gain**: -2 seconds on first message (bypasses decision LLM)

**Test**:
```bash
python3 scripts/test_quick_status_flow.py
# Verify: status appears before decision agent runs
```

---

### 1.2 Cache WorldState Computations

**Problem**: `compute_worldstate` recalculates 58 features every call, even for same timestamp.

**Solution**: In-memory cache with 5-minute TTL.

**Implementation**:
```python
# features/telemetry_vsm/src/worldstate_engine.py

from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

class WorldStateEngine:
    def __init__(self, parquet_path: str):
        self.parquet_path = parquet_path
        self._cache = {}  # {cache_key: (worldstate, timestamp)}
        self._cache_ttl = 300  # 5 minutes
    
    def _get_cache_key(self, asset_id: str, timestamp: datetime, window_minutes: int) -> str:
        """Generate cache key from parameters."""
        key_str = f"{asset_id}_{timestamp.isoformat()}_{window_minutes}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_timestamp: datetime) -> bool:
        """Check if cache entry is still valid."""
        return (datetime.now() - cached_timestamp).total_seconds() < self._cache_ttl
    
    def compute_worldstate(
        self,
        asset_id: str,
        timestamp: datetime,
        window_minutes: int = 60
    ) -> dict:
        """
        Compute WorldState with caching.
        Cache key: asset_id + timestamp + window_minutes
        TTL: 5 minutes
        """
        cache_key = self._get_cache_key(asset_id, timestamp, window_minutes)
        
        # Check cache
        if cache_key in self._cache:
            worldstate, cached_time = self._cache[cache_key]
            if self._is_cache_valid(cached_time):
                return worldstate  # Cache hit!
        
        # Cache miss - compute
        worldstate = self._compute_worldstate_uncached(asset_id, timestamp, window_minutes)
        
        # Store in cache
        self._cache[cache_key] = (worldstate, datetime.now())
        
        # Cleanup old entries (keep max 100 entries)
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        return worldstate
    
    def _compute_worldstate_uncached(self, asset_id, timestamp, window_minutes):
        """Original computation logic (existing code)."""
        # Move existing compute_worldstate logic here
        ...
```

**Files**:
- `features/telemetry_vsm/src/worldstate_engine.py`: Add caching layer
- `tests/requires_env/test_worldstate_cache.py`: Add cache tests

**Expected Gain**: -300ms on repeated worldstate calls (85% of compute time)

**Test**:
```python
# Test cache hit
engine = WorldStateEngine("...")
ts = datetime(2024, 1, 15, 12, 0, 0)

start = time.time()
ws1 = engine.compute_worldstate("135_1570", ts, 60)
time1 = time.time() - start
print(f"First call: {time1:.3f}s")  # ~400ms

start = time.time()
ws2 = engine.compute_worldstate("135_1570", ts, 60)
time2 = time.time() - start
print(f"Cached call: {time2:.3f}s")  # ~5ms

assert ws1 == ws2
assert time2 < 0.05  # <50ms
```

---

### 1.3 Disable Chain-of-Thought for Base Model

**Problem**: Base model (decision agent) outputs reasoning steps, adding tokens and latency.

**Solution**: Use experimental flag to disable reasoning for base model only.

**Implementation**:
```python
# elysia/config.py or seed_default_config.py

from elysia import configure

configure(
    base_use_reasoning=False,      # ← NEW: Disable for decision agent
    complex_use_reasoning=True,    # Keep for tool LLM calls
)
```

**Trade-off**: Slightly less transparent decisions, but decision agent rarely needs complex reasoning (tool descriptions are clear).

**Files**:
- `scripts/seed_default_config.py`: Add configure() call
- `features/vsm_tree/smido_tree.py`: Add configure() in create_vsm_tree

**Expected Gain**: -20% output tokens → ~1 second on decision steps

**Test**:
```bash
elysia start
# Check decision logs - reasoning field should be absent
```

**Monitoring**: Watch for decision quality degradation (can re-enable if needed).

---

### 1.4 Reduce Tool Description Verbosity

**Problem**: Each tool has 20-50 line docstrings → large context for decision agent.

**Solution**: Split into short description (for LLM) + detailed docstring (for humans).

**Current** (search_manuals_by_smido):
```python
"""
Search manual sections filtered by SMIDO step, with optional diagram inclusion.

Source: VSM_ManualSections collection (167 sections from 3 manuals)
Diagrams: VSM_DiagramUserFacing (8) + VSM_DiagramAgentInternal (8)

Args:
    query: Natural language query to search for in manual sections. If empty, uses filter-only search.
    smido_step: SMIDO methodology step to filter by. Options: melding, technisch, installatie_vertrouwd, 
                3P_power, 3P_procesinstellingen, 3P_procesparameters, 3P_productinput, ketens_onderdelen.
    failure_mode: Filter by specific failure mode (e.g., "ingevroren_verdamper", "te_hoge_temperatuur").
    component: Filter by component name (e.g., "verdamper", "compressor", "pressostaat").
    include_diagrams: Whether to fetch and return related Mermaid diagrams. Default: True.
    include_test_content: Whether to include test content (opgave). Default: False (filters out test content).
    limit: Maximum number of manual sections to return. Default: 5.

Returns:
    - Manual sections (text) matching the query and filters
    - Related diagrams (Mermaid code) if include_diagrams=True

Automatically filters out test content (opgave) unless include_test_content=True.

Used in: I (Installatie), P2 (Procesinstellingen), O (Onderdelen) nodes
"""
```

**Optimized** (for LLM):
```python
@tool(
    status="Searching SMIDO manuals...",
    branch_id="base",
    description="Search 167 manual sections by SMIDO step, component, or failure mode. Returns text + diagrams."
)
async def search_manuals_by_smido(
    query: str = "",
    smido_step: str = None,  # melding, technisch, 3P_power, 3P_procesinstellingen, etc.
    component: str = None,   # verdamper, compressor, etc.
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    HUMAN DOCS (not sent to LLM):
    Full detailed docstring here for developers...
    """
```

**Pattern**: Use `@tool(description="...")` for LLM-facing text, keep full docstring for code docs.

**Files**:
- `elysia/api/custom_tools.py`: Update all 13 VSM tools
- Each tool: Add short `description` parameter to @tool decorator

**Expected Gain**: -1500 tokens per decision → ~500ms

**Test**:
```python
# Verify tool.description is short
from elysia.api.custom_tools import search_manuals_by_smido
assert len(search_manuals_by_smido.description) < 150
```

---

## Tier 2: Structural Optimizations (20% reduction)

### 2.1 Minimize Collection Schemas in Context

**Problem**: All collection schemas (9 collections × ~20 properties) sent to decision agent.

**Solution**: Only include schemas for collections used by currently available tools.

**Implementation**:
```python
# Elysia internals modification (if accessible)
# OR: Disable use_elysia_collections for VSM

# In features/vsm_tree/smido_tree.py
tree = Tree(
    branch_initialisation="empty",
    use_elysia_collections=False,  # ← Disable automatic schema inclusion
    ...
)
```

**Trade-off**: Native `query` and `aggregate` tools won't have schema hints → need to add manual schema docs to tool descriptions.

**Alternative**: Keep schemas only for collections with >100 objects (VSM_ManualSections, VSM_ManualImage).

**Expected Gain**: -2000 tokens per decision → ~600ms

---

### 2.2 Implement Environment Pruning

**Problem**: Environment grows with every tool result → older results clutter context.

**Solution**: Prune environment after 3 tool calls, keeping only last 2 results.

**Implementation**:
```python
# New tool: environment_pruner (runs via run_if_true)

@tool(status="Cleaning up...", branch_id="base")
async def prune_environment(tree_data=None, **kwargs):
    """Remove old tool results from environment to reduce context size."""
    # Keep only last 2 tool results
    if len(tree_data.environment.items) > 2:
        while len(tree_data.environment.items) > 2:
            # Remove oldest item
            oldest_tool = tree_data.environment.items[0].tool_name
            oldest_name = tree_data.environment.items[0].name
            tree_data.environment.remove(oldest_tool, oldest_name, index=0)
        
        yield Status("Cleaned up old results")
    
    yield Response("")  # No user message

async def prune_environment_run_if_true(tree_data, **kwargs):
    """Auto-prune if environment has >2 items."""
    should_prune = len(tree_data.environment.items) > 2
    return (should_prune, {})
```

**Files**:
- `elysia/api/custom_tools.py`: Add prune_environment tool
- `features/vsm_tree/bootstrap.py`: Register tool at base

**Expected Gain**: -1000 tokens per decision after 3rd tool → ~300ms

---

### 2.3 Optimize Preprocessing Payload Mappings

**Problem**: Preprocessing creates duplicate fields (e.g., title → document_title) for frontend compatibility.

**Solution**: Use minimal preprocessing - only map required fields, skip optional ones.

**Review**: Check `scripts/preprocess_collections.py` for unnecessary field mappings.

**Expected Gain**: -100ms on collection queries (minor)

---

### 2.4 Batch Weaviate Queries + Hybrid Search Tuning (ENHANCED)

**Problem**: 
1. Sequential Weaviate queries (manuals → diagrams)
2. Default hybrid search alpha=0.5 may not be optimal for each collection
3. No connection pooling → repeated connection overhead

**Solution**: Parallel queries + alpha tuning + connection pooling

**Implementation**:
```python
# elysia/api/custom_tools.py

import asyncio
from weaviate.classes.query import Filter

# Tuned alpha values per collection (based on Weaviate research)
HYBRID_ALPHA_TUNING = {
    "VSM_ManualSections": 0.7,  # Favor BM25 (exact keyword matches for technical terms)
    "VSM_ManualImage": 0.3,      # Favor vector (semantic similarity for image descriptions)
    "VSM_TelemetryEvent": 0.5,   # Balanced
    "VSM_VlogCase": 0.6,         # Slightly favor BM25 (case titles)
}

@tool(status="Searching SMIDO manuals...", branch_id="base")
async def search_manuals_by_smido(
    query: str = "",
    smido_step: str = None,
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """..."""
    async with client_manager.connect_to_async_client() as client:
        # Get collections
        manual_coll = client.collections.get("VSM_ManualSections")
        diagram_coll = client.collections.get("VSM_DiagramUserFacing")
        
        # Build filters
        filters = []
        if smido_step:
            filters.append(Filter.by_property("smido_step").equal(smido_step))
        if not kwargs.get("include_test_content", False):
            filters.append(Filter.by_property("content_type").not_equal("opgave"))
        
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        
        # **PARALLEL QUERIES** with tuned alpha
        manual_task = manual_coll.query.hybrid(
            query=query,
            filters=combined_filter,
            limit=limit,
            alpha=HYBRID_ALPHA_TUNING["VSM_ManualSections"]  # Tuned!
        )
        
        diagram_task = diagram_coll.query.hybrid(
            query=query,
            filters=Filter.by_property("smido_phases").contains_any([smido_step]) if smido_step else None,
            limit=2,
            alpha=0.5  # Diagrams: balanced
        )
        
        # Execute in parallel
        manual_results, diagram_results = await asyncio.gather(
            manual_task, 
            diagram_task,
            return_exceptions=True  # Don't fail if one query fails
        )
        
        # Process results...
        yield Result(...)
```

**Alpha Tuning Rationale** (from Weaviate research):
- **High alpha (0.7-0.9)**: Favor BM25 for exact keyword matches (technical documentation)
- **Low alpha (0.1-0.3)**: Favor vector search for semantic similarity (image descriptions, user questions)
- **Balanced (0.5)**: Equal weight (general text search)

**Connection Pooling** (ClientManager):
```python
# elysia/util/client.py

class ClientManager:
    def __init__(self):
        self._client_pool = None
        self._pool_size = 10  # NEW: Connection pool
    
    async def connect_to_async_client(self):
        """Reuse connections from pool instead of creating new ones."""
        if not self._client_pool:
            self._client_pool = await self._create_pool()
        
        return await self._client_pool.acquire()
    
    async def _create_pool(self):
        # Use aiohttp connection pooling
        connector = aiohttp.TCPConnector(limit=self._pool_size, ttl_dns_cache=300)
        # ...
```

**Files**:
- `elysia/api/custom_tools.py`: Update all tools with parallel queries + alpha tuning
- `elysia/util/client.py`: Add connection pooling

**Expected Gain**: 
- -200ms on multi-query tools (parallel execution)
- -10-15% better relevance (alpha tuning)
- -100ms on repeated queries (connection pooling)

**Test**:
```python
# Test alpha tuning
for alpha in [0.3, 0.5, 0.7, 0.9]:
    results = await collection.query.hybrid(query="verdamper probleem", alpha=alpha, limit=5)
    print(f"Alpha {alpha}: {[r.properties['title'] for r in results.objects]}")
# Pick alpha with best results for your data
```

---

### 2.5 DSPy Async Parallelization (NEW)

**Problem**: DSPy default runs LLM calls sequentially, even when independent.

**Solution**: Use `dspy.asyncify()` + configure `async_max_workers`.

**Benchmark**: 2-3x speedup on multi-tool workflows

**Implementation**:
```python
# features/vsm_tree/smido_tree.py

import dspy

def create_vsm_tree(...):
    # Configure async settings
    dspy.settings.configure(
        lm=dspy.LM("gemini/gemini-2.5-flash", cache=True),
        async_max_workers=4,  # Run 4 LLM calls in parallel (reduce from default 8 to avoid rate limits)
        track_usage=True  # Monitor token usage
    )
    
    tree = Tree(...)
    
    # Make tree async-capable
    tree = dspy.asyncify(tree)
    
    return tree
```

**Usage in Multi-Tool Scenarios**:
```python
# Before: Sequential tool execution (8 seconds total)
status = await tree.run_tool("get_current_status")  # 4s
worldstate = await tree.run_tool("compute_worldstate")  # 4s

# After: Parallel tool execution (4 seconds total)
status_task = tree.run_tool("get_current_status")
worldstate_task = tree.run_tool("compute_worldstate")
status, worldstate = await asyncio.gather(status_task, worldstate_task)  # 4s (50% reduction)
```

**Trade-offs**:
- **Pro**: 50% reduction when tools are independent
- **Con**: Requires careful dependency management (don't parallelize if tool B needs tool A's output)
- **Con**: May hit Gemini rate limits faster (mitigate with async_max_workers=4)

**Expected Gain**: -50% on multi-tool workflows (where applicable)

---

## Tier 3: Advanced Optimizations (20% reduction)

### 3.1 Parallel Tool Execution

**Problem**: If decision agent selects 2 independent tools, they run sequentially.

**Solution**: Modify tree execution to run independent tools in parallel.

**Complexity**: HIGH (requires Elysia core changes)

**Expected Gain**: -50% on multi-tool responses

---

### 3.2 Request-Level Caching

**Problem**: Same queries across different users recalculate everything.

**Solution**: Redis cache for Weaviate query results (1 hour TTL).

**Implementation**:
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

async def cached_hybrid_query(collection, query, filters, limit):
    cache_key = f"weaviate:{collection.name}:{query}:{str(filters)}:{limit}"
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Query Weaviate
    result = await collection.query.hybrid(query, filters=filters, limit=limit)
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result
```

**Expected Gain**: -80% on repeated queries

---

### 3.3 Optimize Agent Prompts

**Problem**: agent_description is 100+ lines → included in every decision.

**Solution**: Reduce to 30 lines, move details to tool descriptions.

**Current**: 2000+ characters
**Target**: <800 characters

**Files**:
- `features/vsm_tree/smido_tree.py`: Shorten agent_description
- Move SMIDO flow details to tool descriptions

**Expected Gain**: -500 tokens → ~200ms

---

### 3.4 Model Downgrade for Non-Critical Paths

**Problem**: gemini-2.5-pro is slow for simple operations.

**Solution**: Use gemini-2.5-flash for:
- search_manuals_by_smido (query construction)
- query_vlog_cases (simple retrieval)
- show_alarm_breakdown (data aggregation)

Keep gemini-2.5-pro for:
- compute_worldstate (complex feature engineering)
- get_asset_health (W vs C comparison)
- analyze_sensor_pattern (pattern matching)

**Implementation**:
```python
@tool(
    status="Searching manuals...",
    branch_id="base",
    use_complex_model=False  # ← Use base model instead
)
async def search_manuals_by_smido(...):
    ...
```

**Expected Gain**: -60% latency on simple retrieval tools

---

## Implementation Priority (UPDATED with Exa Research)

### Week 1: Quick Wins (50-60% reduction) ⭐
**Focus**: Gemini-specific optimizations + minimal code changes

- [ ] **Day 1**: 1.1 Gemini Context Caching (-44% latency, -60% cost) ← **START HERE**
  - Create `features/vsm_tree/context_cache.py`
  - Integrate with `create_vsm_tree()`
  - Test cache hit/miss rates
  
- [ ] **Day 2**: 1.2 Streaming Responses (-60% perceived latency)
  - Update `get_asset_health`, `search_manuals_by_smido` to stream
  - Test time-to-first-token
  
- [ ] **Day 3**: 1.3 run_if_true for get_current_status (-2s on first message)
  - Convert @tool to Tool class
  - Add run_if_true method
  
- [ ] **Day 4**: 1.4 WorldState Caching (-300ms on repeated calls)
  - Add `_cache` dict to WorldStateEngine
  - Implement TTL + cleanup logic
  
- [ ] **Day 5**: Test & measure
  - Run `scripts/test_plan7_full_tree.py` with timing
  - Compare before/after metrics
  - Document cache hit rates

**Expected Result**: **6s → 2.5s avg (-58% latency)** 🚀

**Rationale**: Gemini Context Caching alone gives 44% reduction. Combined with streaming (perceived latency) and WorldState caching, we hit 50-60% total reduction with minimal code changes.

---

### Week 2: Structural (additional 15-20% reduction)
**Focus**: Weaviate + DSPy optimizations

- [ ] **Day 6**: 2.4 Weaviate Parallel Queries + Alpha Tuning
  - Add `HYBRID_ALPHA_TUNING` dict
  - Update `search_manuals_by_smido`, `query_vlog_cases` with asyncio.gather
  - Test alpha values (0.3, 0.5, 0.7, 0.9) for relevance
  
- [ ] **Day 7**: 2.5 DSPy Async Parallelization
  - Configure `async_max_workers=4`
  - Test parallel tool execution
  - Monitor rate limits
  
- [ ] **Day 8**: 2.1 Minimize Collection Schemas
  - Set `use_elysia_collections=False` in Tree init
  - Add manual schema docs to tool descriptions (if needed)
  
- [ ] **Day 9**: 2.2 Environment Pruning
  - Create `prune_environment` tool
  - Add run_if_true to auto-prune
  - Test memory impact
  
- [ ] **Day 10**: Test & measure
  - Full integration test
  - Verify no degradation in answer quality
  - Check cache hit rates, parallel execution success rate

**Expected Result**: **2.5s → 2.0s avg (-20% additional)** ✅

**Total After Week 2: 6s → 2s (-67% total latency)** 🎉

---

### Week 3+: Advanced (optional, diminishing returns)
**Only if <2s latency is still not acceptable**

- [ ] 3.1 Parallel Tool Execution (Elysia core changes)
- [ ] 3.2 Redis Caching (infrastructure dependency)
- [ ] 3.3 Optimize Agent Prompts (2000 → 800 chars)
- [ ] 3.4 Model Downgrade for Simple Tools (flash vs pro)

**Expected Result**: **2.0s → 1.5s avg (-25% additional)**

**Total After Week 3: 6s → 1.5s (-75% total latency)**

---

## Updated Success Criteria

### Tier 1 Complete (Week 1):
✅ **First message <3 seconds** (current: ~6s)
✅ **Follow-up <3 seconds** (current: ~8s)
✅ **Cache hit rate >80%** (Gemini context caching)
✅ **No degradation in answer quality**

### Tier 2 Complete (Week 2):
✅ **All queries <2.5 seconds** (p95)
✅ **Weaviate queries <200ms** (parallel + tuned)
✅ **Multi-tool workflows 50% faster** (DSPy async)

### Production Ready:
✅ **p95 latency <2.5 seconds** for any query
✅ **p50 latency <1.5 seconds** 
✅ **Cost reduction 40-60%** (cached tokens)
✅ **Monitoring dashboards** (cache hit rates, latency breakdown)

---

## Key Insights from Research (Nov 2025)

**Game-Changers**:
1. **Gemini Context Caching** is the #1 priority (44% reduction, proven in production)
2. **Streaming** transforms UX even if total latency stays same (perceived speed ↑60%)
3. **Weaviate Alpha Tuning** is free performance (test alpha=0.7 for technical docs)
4. **DSPy asyncify** unlocks parallel execution (2-3x speedup on multi-tool)

**Avoid**:
1. **Batch API** (24h processing, not suitable for real-time chat)
2. **Disabling reasoning** (base_use_reasoning=False causes quality degradation)
3. **Over-caching** (cache TTL >1h causes stale data issues)
4. **Too many parallel workers** (>4 hits Gemini rate limits)

---

## Measurement Strategy

### Baseline Metrics (Before)
```python
# Add timing to scripts/test_plan7_full_tree.py
import time

start = time.time()
response = tree("Wat is de status?")
total_time = time.time() - start

print(f"Total: {total_time:.2f}s")
print(f"Decision time: {tree.last_decision_time:.2f}s")
print(f"Tool time: {tree.last_tool_time:.2f}s")
```

**Current Baseline** (estimate):
- First message: ~6 seconds (decision: 2s, get_current_status: 4s)
- Follow-up: ~8 seconds (decision: 2s, compute_worldstate: 6s)

### Target Metrics (After Tier 1+2)
- First message: ~3 seconds (run_if_true: 0s, cached status: 2s)
- Follow-up: ~4 seconds (decision: 1s, cached worldstate: 0.5s, tool: 2.5s)

### Monitoring
```python
# Add to elysia/api/core/log.py
import time

def log_latency(phase: str, duration: float):
    logger.info(f"LATENCY [{phase}]: {duration:.3f}s")

# Use in tree execution:
start = time.time()
decision = await decision_agent.run()
log_latency("decision_agent", time.time() - start)

start = time.time()
result = await tool.run()
log_latency(f"tool_{tool.name}", time.time() - start)
```

---

## Risk Assessment

### Low Risk (Tier 1)
- **1.1 run_if_true**: Safe, documented Elysia pattern
- **1.2 Caching**: Isolated, easy to disable if bugs
- **1.3 Disable reasoning**: Reversible config change

### Medium Risk (Tier 2)
- **2.1 Schema minimization**: May impact query/aggregate quality
- **2.2 Environment pruning**: Could lose important context

### High Risk (Tier 3)
- **3.1 Parallel execution**: Complex, Elysia core changes
- **3.2 Redis**: Infrastructure dependency

**Recommendation**: Start with Tier 1, measure, then proceed to Tier 2 only if needed.

---

## Success Criteria

✅ **Tier 1 Complete**: First message <3 seconds, follow-up <5 seconds
✅ **Tier 2 Complete**: Follow-up <4 seconds consistently
✅ **Production Ready**: p95 latency <5 seconds for any query

**Rollback Plan**: All changes behind feature flags or config options, can revert individually.

---

## Next Steps

1. **Review this plan** - confirm priority and scope
2. **Implement 1.1** - run_if_true for get_current_status (highest impact)
3. **Measure baseline** - add latency logging to test scripts
4. **Iterate** - implement → test → measure → repeat

**Total Estimated Effort**: 2-3 weeks for Tier 1+2 (50% reduction)


