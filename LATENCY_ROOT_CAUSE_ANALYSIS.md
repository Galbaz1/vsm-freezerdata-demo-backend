# Latency Root Cause Analysis

**Date**: Nov 13, 2025
**Issue**: Queries take 20-30 seconds instead of expected 2-3 seconds

---

## 🔍 Discovery: The Real Problem

### Test Results

**Simple query**: "Wat is de status?"

```
Decision History: 2 decisions
  Step 1: get_current_status
  Step 2: text_response

Trees completed: 2 (!)
Total time: 20.09s
```

**Breakdown**:
- Tree 1 (get_current_status): ~10s
- Tree 2 (text_response): ~10s
- Total: ~20s

---

## 🎯 Root Causes Identified

### 1. Multiple Tree Recursions (MAIN ISSUE)

**Problem**: Every query triggers 2 complete tree executions:
1. **Tree 1**: Decision LLM → choose tool → run tool → add to environment
2. **Tree 2**: Decision LLM → choose text_response → format answer → end

**Why this is slow**:
- Each tree = full decision LLM call (~6-10s with current setup)
- 2 trees = 2× LLM calls = 12-20s minimum
- Plus tool execution time
- Plus environment/schema overhead

**Evidence**:
```python
trees_completed: 2           # 2 full recursions
decision_history: [          # 2 separate decisions
    ['get_current_status'],  # Tree 1
    ['text_response']        # Tree 2
]
```

---

### 2. Decision LLM is TOO SLOW (10-15s per call)

**Expected** (from research): ~2-3s with Gemini cache
**Actual**: ~10-15s per decision

**Why**:
- ❌ Gemini cache exists but DSPy doesn't use it (dspy.settings.lm = None)
- ❌ Long context being sent: agent description (2000 chars) + tool descriptions (16×100) + schemas
- ❌ Possibly reasoning/CoT overhead

**Cache verification**:
```
Direct Gemini API WITH cache: 1.43s  ✅
Direct Gemini API NO cache: 10.44s   ❌
Tree query: 20.09s                   ❌❌ (cache not used)
```

---

### 3. Unnecessary text_response Step

**Current flow**:
```
User: "Wat is de status?"
  → Tree 1: get_current_status (returns data)
  → Tree 2: text_response (formats data into text)
  → Response to user
```

**Problem**: The tool already yields a Result with data. Why does it need a second tree for text_response?

**Answer** (from code): Elysia always adds a final text formatting step unless tool has `end=True`

---

## 📋 What Weaviate Docs Say

### Speed Recommendations (from docs/offical/Advanced/local_models.md):

**1. Disable collection schemas** (if not needed):
```python
tree = Tree(use_elysia_collections=False)
```
- Removes preprocessed schema context from every prompt
- Saves: ~1000-2000 tokens per decision
- Trade-off: Query/Aggregate tools need manual schema docs

**2. Disable CoT reasoning** (experimental):
```python
from elysia import configure
configure(
    base_use_reasoning=False,   # For decision agent
    complex_use_reasoning=False # For tool LLMs
)
```
- Reduces output tokens
- Trade-off: Less transparent decisions, possibly lower quality

**3. Simplify tree structure**:
- Flat trees (one_branch) are faster than nested (multi_branch)
- Fewer decision points = fewer LLM calls
- VSM already uses "empty" init with flat root ✅

---

## 🎯 Concrete Problems

### Problem 1: 2 Trees Per Query

**Current**: 
- Query → get_current_status → text_response
- 2 trees = 2 decision LLM calls = 20s

**Solution Options**:

**A) Set tool end=True** (simplest):
```python
@tool(status="...", branch_id="base", end=True)
async def get_current_status(...):
    ...
```
- Skips text_response recursion
- 2 trees → 1 tree
- Expected saving: ~10s (50%)

**B) Combine tool + response**:
- Tool yields both Result AND Response
- But Elysia might still add text_response

**Recommendation**: Try A first (set end=True on get_current_status)

---

### Problem 2: Decision LLM Not Using Cache

**Current**:
- Cache created ✅
- DSPy configured: None ❌
- Cache not passed to LLM calls ❌

**Solution**: Integrate cache with Elysia's LM initialization

**Where to look**:
1. `elysia/tree/tree.py` - Where base_lm/complex_lm are created
2. `elysia/config.py` - Settings initialization
3. How to pass `cached_content` to DSPy LM

**Expected saving**: 44% on decision LLM time (10s → 5.6s)

---

### Problem 3: Long Agent Description

**Current**: 2000+ characters in agent_description + style
**Impact**: Large context even WITH caching
**Solution**: Reduce to 800 characters (from plan)

**Expected saving**: ~500ms per decision

---

## 📊 Expected Impact of Fixes

### Quick Win: Set end=True on get_current_status

**Before**:
- Query → decision 1 (10s) → tool (1s) → decision 2 (10s) → text (1s)
- Total: ~22s

**After**:
- Query → decision 1 (10s) → tool (1s) → end
- Total: ~11s
- **Saving: 50% (11s reduction)**

### Medium Win: Fix DSPy Cache Integration

**Before**: 10s per decision
**After**: 5.6s per decision (44% reduction)
**Saving**: 4.4s × 1 tree = 4.4s

### Combined:

**Current**: 22s
**After Quick Win**: 11s (end=True)
**After Both**: 6.6s (end=True + cache)
**Target**: 2-3s (need more optimizations)

---

## 🚀 Immediate Action Plan

### Priority 1: Set end=True (5 minutes)
```python
# elysia/api/custom_tools.py
@tool(status="...", branch_id="smido_melding", end=True)  # ← Add this
async def get_current_status(...):
```

**Impact**: -50% latency (22s → 11s)

### Priority 2: Fix DSPy Cache (1-2 hours)
- Investigate Elysia LM initialization
- Add cached_content parameter support
- Test cache hit metrics

**Impact**: -44% on decision time (11s → 6.6s)

### Priority 3: Reduce Agent Description (30 minutes)
- 2000 chars → 800 chars
- Move details to tool descriptions

**Impact**: -500ms (6.6s → 6.1s)

### Priority 4: WorldState Caching (1 hour)
- In-memory cache with TTL
- **Impact**: -300ms on repeated calls

---

## 🎓 Key Learnings

1. **Multi-step trees are expensive**: Each "tree" = 1 full decision LLM call
2. **Default behavior adds text_response**: Unless tool has end=True
3. **Cache works but isn't integrated**: DSPy setup missing
4. **16 tools at root is fine**: Flat structure is correct (per Weaviate docs)
5. **Recursion_limit=5**: Allows up to 5 trees per query (we're using 2)

---

## 📝 Conclusion

**Root cause**: 
- ❌ NOT tree complexity (flat structure is correct)
- ❌ NOT too many tools (16 is fine)
- ✅ **Multiple tree recursions** (2 trees = 2 LLM calls = 20s)
- ✅ **Cache not integrated with DSPy** (cache exists but unused)
- ✅ **Long agent description** (2000 chars repeated)

**Biggest quick win**: Set `end=True` on tools that don't need text formatting (-50%)

**Next biggest win**: Integrate cache with DSPy LM calls (-44% on remaining time)


