# VSM Project - Critical Knowledge & Learnings

**Purpose**: Key technical insights, solutions to problems, and critical knowledge for developers

---

## 🔑 Critical Technical Knowledge

### 1. Weaviate v4 API (MUST USE CORRECTLY)

**❌ OLD (Deprecated)**:
```python
# Don't use dict syntax
filters = {"path": ["smido_step"], "operator": "Equal", "valueText": "power"}
```

**✅ NEW (Correct)**:
```python
from weaviate.classes.query import Filter
filters = Filter.by_property("smido_step").equal("power")
```

**Complex Filters**:
```python
# AND
filter = Filter.by_property("smido_step").equal("diagnose") & \
         Filter.by_property("content_type").not_equal("opgave")

# OR
filter = Filter.by_property("failure_mode").contains_any(["frozen_evap", "high_temp"])
```

**Named Vectors**:
```python
# Use Configure.Vectors (not Configure.NamedVectors)
from weaviate.classes.config import Configure

collection = client.collections.create(
    name="VSM_ManualSections",
    vectorizer_config=Configure.Vectorizer.text2vec_weaviate()
)
```

---

### 2. Gemini Model Configuration (CRITICAL)

**❌ WRONG (Creates Double Prefix)**:
```bash
COMPLEX_MODEL=gemini/gemini-2.5-pro  # NO! Don't include gemini/ prefix
COMPLEX_PROVIDER=google              # NO! Use gemini not google
# Results in: google/gemini/gemini-2.5-pro (invalid)
```

**✅ CORRECT**:
```bash
COMPLEX_MODEL=gemini-2.5-pro   # NO prefix in model name
COMPLEX_PROVIDER=gemini        # Use "gemini" as provider
# Results in: gemini/gemini-2.5-pro (valid, routes to Google AI Studio)
```

**Why?**: Elysia's `load_lm()` concatenates `{provider}/{model}`. Provider `gemini` + model `gemini-2.5-pro` = `gemini/gemini-2.5-pro` which routes to Google AI Studio using `GOOGLE_API_KEY`.

---

### 3. Elysia Tool Pattern (Async Generators)

**✅ CORRECT Pattern**:
```python
from elysia import tool, Result, Status, Error

@tool(status="Processing...", branch_id="smido_melding")
async def my_tool(
    param: str,
    tree_data=None,        # Auto-injected
    client_manager=None,   # Auto-injected
    **kwargs               # Required!
):
    """Tool description for LLM."""
    
    # 1. Validate inputs
    if not client_manager:
        yield Error("Client manager not available")
        return
    
    # 2. Yield status updates
    yield Status("Querying database...")
    
    # 3. Do work
    result = do_work(param)
    
    # 4. Store in environment (optional)
    if tree_data:
        tree_data.environment["my_result"] = result
    
    # 5. Yield result
    yield Result(objects=[result], metadata={"source": "my_tool"})
```

**Common Mistakes**:
- ❌ Forget `**kwargs` → Tool won't receive injected params
- ❌ Forget `yield` → Results don't stream to frontend
- ❌ Return instead of yield → Generator protocol broken
- ❌ Don't check `client_manager.is_client` → Fails if Weaviate not configured

---

### 4. WorldState Engine Pattern

**✅ Efficient Lazy Loading**:
```python
class WorldStateEngine:
    def __init__(self, parquet_path: str):
        self.parquet_path = Path(parquet_path)
        self._df = None  # Lazy load!
    
    def _load_data(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.read_parquet(self.parquet_path)
        return self._df
```

**Why**: Loading 785K rows takes ~800ms. Lazy load ensures one-time cost per session.

**Performance Tips**:
- Use `mask = (df.index >= start) & (df.index <= end)` for boolean indexing
- Avoid duplicate index with `.copy()` after slicing
- Handle NaN with `pd.notna(val)` checks
- Use `.iloc[-1]` for latest value (fastest)

---

### 5. Bootstrap System (Auto-Load Tree)

**Pattern**:
```python
# 1. Register bootstrapper
from features.vsm_tree.bootstrap import register_bootstrapper

def my_bootstrap(tree: Tree, context: dict):
    # Add branches
    tree.add_branch(branch_id="my_branch", root=True, ...)
    # Add tools
    tree.add_tool(my_tool, branch_id="my_branch")

register_bootstrapper("my_feature", my_bootstrap)

# 2. Configure tree
config = Config(
    branch_initialisation="empty",
    feature_bootstrappers=["my_feature"]  # Auto-applies on tree creation
)

# 3. Bootstrap runs automatically
tree_manager = TreeManager(user_id="user_123", config=config)
tree_manager.add_tree("conv_456")  # Bootstrap applied here!
```

**Critical**: Bootstrap only runs when `branch_initialisation="empty"` AND `feature_bootstrappers` is set.

---

## 🎯 Domain Knowledge (SMIDO & Cooling Systems)

### 1. "Koelproces uit Balans" (OUT OF BALANCE) - CORE CONCEPT

**Critical Understanding**: NOT all failures are broken components!

**Balance Factors** (Manual page 11-12):
- Koellast (cooling load)
- Verdampercapaciteit (evaporator capacity)
- Condensorcapaciteit (condenser capacity)
- Koudemiddel hoeveelheid (refrigerant amount)
- Luchtstroom (airflow)
- Omgevingstemperatuur (ambient temperature)

**Example**: Frozen evaporator
- **Symptom**: Ice on evaporator, temp too high
- **NOT**: Broken evaporator
- **BUT**: System out of balance (defrost cycle not running → ice accumulates)
- **Fix**: Reset timer to automatic (settings), clean air ducts (airflow)

**Prompt Integration**: Mentioned in agent description, D branch, get_asset_health tool, multiple branches.

---

### 2. SMIDO Methodology (4 P's Not 3!)

**Manual Says**: "3 P's" in heading  
**Manual Lists**: 4 items (Power, Procesinstellingen, Procesparameters, Productinput)

**Implementation**: Always use 4 P's:
- **P1 - Power**: Electrical supply (zekeringen, spanning, continuïteit)
- **P2 - Procesinstellingen**: Settings vs design (pressostaat, thermostat, defrost timer, PID)
- **P3 - Procesparameters**: Measurements vs design (drukken, temperaturen, oververhitting, onderkoeling)
- **P4 - Productinput**: External conditions vs design (ambient temp, product load, door usage, condenser airflow)

**Why P4 Matters**: Not a defect - environmental factors outside design (e.g., warm product → extra moisture → faster ice formation)

---

### 3. Agent-User Role Separation (Collaboration Pattern)

**Agent (A)** - Remote senior technician:
- ✅ Has: Sensor data (real-time + historical), manuals, vlog cases, computational tools
- ❌ Lacks: Physical access, visual inspection, customer contact, safety assessment

**User (M)** - On-site junior technician:
- ✅ Has: Physical presence (see/hear/touch), manual actions, customer contact
- ❌ Lacks: Historical analysis, pattern recognition, commissioning data, case database

**Collaboration**: A analyzes data + provides guidance, M observes + executes actions.

**Critical**: Agent must ASK for physical observations, cannot assume visual state.

---

### 4. Conversational Principles

**One Question at a Time**:
```
✅ "Ga naar regelaar. Wat zie je?"
❌ "Check regelaar, meet druk, test ventilator" (too many steps)
```
**Why**: Technician must walk around, don't overload.

**Praise Observations**:
```
✅ "Uitstekend gevonden! Timer staat op 'handmatig' - dát is het probleem."
❌ "Timer is on manual mode."
```
**Why**: Builds confidence, reinforces good diagnostic behavior.

**Explain "Why"**:
```
✅ "We checken P2 omdat regelaar actief is maar verkeerd gedrag vertoont"
❌ "Check P2 settings"
```
**Why**: Educational - technician learns reasoning, not just commands.

---

## 🐛 Problems & Solutions

### Problem: "No module named 'pandas'"
**Date**: Nov 11, 2024  
**Solution**: `pip install pandas==2.3.3 pyarrow==22.0.0`  
**Prevention**: Added to pyproject.toml dependencies  
**Learning**: Always test in fresh venv

### Problem: "google/gemini/gemini-2.5-pro" Invalid Model
**Date**: Nov 11, 2024  
**Root Cause**: Used `COMPLEX_PROVIDER=google` instead of `gemini`  
**Solution**: Change to `COMPLEX_PROVIDER=gemini`, `COMPLEX_MODEL=gemini-2.5-pro` (no prefix)  
**Prevention**: Document model naming convention in .env template  
**Learning**: Elysia's provider/model concatenation needs careful naming

### Problem: Weaviate Query Returns 0 Despite Data Existing
**Date**: Nov 11, 2024  
**Root Cause**: Using old dict filter syntax instead of Filter.by_property()  
**Solution**: Migrate to v4 API `Filter.by_property()` pattern  
**Prevention**: Always use official Weaviate docs for v4  
**Learning**: API deprecation warnings are real - update immediately

### Problem: Tool Doesn't Receive client_manager
**Date**: Nov 11, 2024  
**Root Cause**: Forgot `**kwargs` in function signature  
**Solution**: Always include `**kwargs` in tool signatures  
**Prevention**: Template tool function with all injected params  
**Learning**: Elysia injects params by name, `**kwargs` catches extras

### Problem: Diagram Search Returns 0 Results
**Date**: Nov 12, 2025  
**Status**: ⚠️ OPEN - Under investigation  
**Symptoms**: 9 diagrams in Weaviate, search_manuals_by_smido finds 0  
**Theories**:
1. SMIDO step filter mismatch (diagram smido_step ≠ section smido_step?)
2. related_diagram_ids empty or malformed
3. Query logic error in lines 160-189
**Next Steps**: Debug VSM_Diagram smido_step properties, test Filter queries

### Problem: Status Query Takes 2-3 Minutes
**Date**: Nov 12, 2025  
**Root Cause**: get_current_status tool documented but NOT implemented  
**Symptoms**: Falls back to get_asset_health (parquet read) + search_manuals (unnecessary)  
**Solution Designed**: 
- Pre-seed WorldState cache at tree startup
- get_current_status reads cache (<1ms)
- Returns 5 sensors + flags + trend
- Asks: "Wil je diagnose?"
- STOPS (doesn't auto-route to T/I/D)
**Status**: Solution designed, not yet coded  
**Learning**: "Fast engine ≠ fast UX" - need fast API layer

### Problem: I Phase Asks Repeatedly for Confirmation
**Date**: Nov 12, 2025  
**Root Cause**: No keyword detection for user confirmation  
**Symptoms**: Agent asks 3-4 times "Ben je bekend met systeem?"  
**Solution Needed**:
- Detect: "Ja, ik ken het systeem", "Ik zie de regelaar"
- If user mentions specific components → assume familiar
- Skip to D after first confirmation
**Status**: Open issue  
**Learning**: Need better conversation state tracking

---

## 🎓 Best Practices Discovered

### 1. Tool Docstring Structure
**Pattern That Works**:
```python
"""
One-line summary.

When to use:
- Specific SMIDO phase
- Specific situation

What it does:
- Concrete actions
- Data sources accessed

Output interpretation:
- Field meanings
- How to understand results

How to explain to M:
"Dutch conversational template..."
[after tool runs]
"Dutch response template with [results]..."

Example (A3 frozen evaporator):
Concrete example from vlog case
"""
```

**Why**: LLM gets strategic guidance (when/why), tactical details (what/how), and conversational examples (linguistic patterns).

---

### 2. Branch Instruction Structure
**Pattern That Works**:
```
Je bent in [PHASE] fase - [purpose].

**KRITISCH: [Key Principle]** (if applicable)

Je doel: [objective]

[Checklist / Questions / Strategy]

Tools beschikbaar:
- Tool1: [when to use]
- Tool2: [when to use]

Conversational example ([Case]):
User: "[observation]"
Agent: "[response pattern]"

Ga naar [next phase] wanneer: [transition criteria]
```

**Why**: Gives LLM phase objective, tools strategy, conversational patterns, and clear exit criteria.

---

### 3. Parallel Development Strategy
**What Worked**:
- Plans 1,2,3,5 developed simultaneously
- Each plan has clear boundaries (no dependencies)
- Individual tests before integration
- Merge sequentially (1→2→3→4→5→6→7)

**Critical Success Factor**: Clear interface contracts between components

---

### 4. Synthetic Data Strategy
**Use Cases**:
- **WorldState Snapshots**: Reference patterns for failure modes (13 created)
- **Commissioning Data (Context C)**: Design parameters for balance checks
- **"Today" Data**: Synthetic current state for instant demo

**Benefits**:
- Enables features without waiting for real data
- Consistent demo experience
- Pattern matching without historical incidents

**Implementation**: Create JSONL with same schema as real data, flag with `is_synthetic: true`

---

### 5. Performance Optimization Patterns

**Parquet Reading** (785K rows):
```python
# ❌ SLOW: Load all data
df = pd.read_parquet(path)
window = df[(df.index >= start) & (df.index <= end)]

# ✅ FAST: Lazy load + boolean indexing
class Engine:
    def __init__(self, path):
        self._df = None  # Lazy!
    
    def _load(self):
        if self._df is None:
            self._df = pd.read_parquet(path)
        return self._df
```

**Session Caching**:
```python
# Store in tree environment for reuse
if tree_data:
    tree_data.environment["worldstate"] = worldstate

# Later tools read from cache
cached_ws = tree_data.environment.get("worldstate")
if cached_ws and cached_ws["timestamp"] == requested_timestamp:
    return cached_ws  # No recomputation!
```

---

### 6. Test Content Handling (Opgave Pattern)

**Strategy**: Include but flag, filter by default
```python
# In processing: Flag test content
section["content_type"] = "opgave"  # If "Theorie opgaven" in heading

# In Weaviate: Include all
upload_all_sections()  # Including opgave

# In queries: Filter out by default
filters = Filter.by_property("content_type").not_equal("opgave")

# In tools: Make filterable
async def search_manuals(include_test_content: bool = False, ...):
    if not include_test_content:
        filters.append(Filter.by_property("content_type").not_equal("opgave"))
```

**Benefits**:
- Flexibility for prompt engineering (can include if needed)
- Clean production queries (excludes by default)
- No data loss (all content preserved)

---

## 🔧 Technical Solutions Library

### Solution: Pre-Seed Cache at Tree Startup

**Problem**: First query has cold-start delay  
**Solution**:
```python
def vsm_smido_bootstrap(tree: Tree, context: dict):
    # ... add branches, tools ...
    
    # Pre-seed WorldState cache
    from features.telemetry_vsm.src.worldstate_engine import WorldStateEngine
    from datetime import datetime
    
    engine = WorldStateEngine("features/telemetry/.../parquet")
    now = datetime.now()
    worldstate = engine.compute_worldstate("135_1570", now, 60)
    
    # Store in tree
    tree._initial_worldstate_cache = worldstate
```

**Result**: First user request has instant data, no I/O

---

### Solution: Three-Zone Time Handling

**Problem**: Demo data is historical (2022-2024), users want "current" data  
**Solution**:
```python
from datetime import datetime

def get_timestamp(requested: str = None):
    data_max = datetime(2026, 1, 1, 0, 0, 0)  # After rebase
    
    if requested:
        ts = datetime.fromisoformat(requested)
    else:
        ts = min(datetime.now(), data_max)  # Clamp to data range
    
    is_future = ts > datetime.now()
    is_past = ts < (datetime.now() - timedelta(days=30))
    is_present = not (is_future or is_past)
    
    return ts, is_future, is_past, is_present
```

**Zones**:
- **PAST**: Historical analysis (>30 days ago)
- **PRESENT**: Current state (within last 30 days)
- **FUTURE**: Predictive (beyond today) - simulated from historical patterns

---

### Solution: Null Value Handling in Weaviate

**Problem**: Elysia preprocessing doesn't like null/None values  
**Solution**:
```python
# ❌ DON'T
section = {
    "related_diagram_ids": None,  # Breaks preprocessing
    "components": None
}

# ✅ DO
section = {
    "related_diagram_ids": [],     # Empty array
    "components": [],
    "optional_field": ""           # Empty string for TEXT
}
```

**Learning**: Weaviate handles empty arrays/strings fine, but nulls cause issues in Elysia preprocessing.

---

## 🏗️ Architectural Patterns

### Pattern: Hybrid Data Access

**When to use each**:

**Weaviate** (semantic discovery):
- Incidents: "Find similar failures"
- Manuals: "Search by SMIDO step"
- Vlogs: "Find problem→solution workflows"
- Snapshots: "Match sensor patterns"

**Parquet** (time-series computation):
- WorldState: Calculate 58 features for time window
- Trends: Analyze 30min, 2h, 24h aggregates
- Flags: Detect anomaly patterns

**Enrichment Files** (static reference):
- Context (C): Commissioning data, design parameters
- Schemas: Component specifications

**Pattern**:
```python
# 1. Query Weaviate for discovery
incidents = await query_weaviate("similar to current symptoms")

# 2. Read parquet for detailed analysis
worldstate = engine.compute_worldstate(asset_id, timestamp, 60)

# 3. Load context for comparison
with open("enrichment.json") as f:
    context = json.load(f)

# 4. Compare and analyze
is_uit_balans = compare_w_vs_c(worldstate, context)
```

---

### Pattern: Multi-Model Strategy

**Base Model** (gemini-2.5-flash) for:
- Decision-making (which tool to call)
- Branch navigation (M→T→I→D→O)
- Tool selection
- Response generation

**Complex Model** (gemini-2.5-pro) for:
- Semantic search in manuals
- Pattern analysis across events
- Complex reasoning ("uit balans" detection)
- Multi-step analysis

**Why**: Cost optimization - use expensive model only when needed.

---

## 📚 Critical Code Snippets

### Snippet 1: SMIDO Branch Hierarchy
```python
# Create parent branch
tree.add_branch(
    branch_id="smido_diagnose",
    instruction="Check 4 P's systematically...",
    from_branch_id="smido_installatie",  # D after I
    status="Start diagnose..."
)

# Create sub-branches (P's under D)
tree.add_branch(
    branch_id="smido_p1_power",
    instruction="Check electrical supply...",
    from_branch_id="smido_diagnose",  # P1 under D
    status="Check voeding..."
)

# Repeat for P2, P3, P4
```

**Critical**: P1-P4 are sub-branches OF D, not siblings.

---

### Snippet 2: W vs C Comparison
```python
def compare_w_vs_c(worldstate: dict, context: dict):
    """Compare dynamic WorldState vs static Context."""
    current = worldstate["current_state"]
    design = context["design_parameters"]
    
    deviations = []
    
    # Temperature deviation
    room_temp = current["current_room_temp"]
    target_temp = design["target_temp"]
    deviation = abs(room_temp - target_temp)
    
    if deviation > 5.0:  # >5°C = out of balance
        deviations.append({
            "factor": "room_temperature",
            "current": room_temp,
            "design": target_temp,
            "deviation": deviation,
            "severity": "critical" if deviation > 20 else "high"
        })
    
    # Superheat deviation
    superheat_actual = current["current_hot_gas_temp"] - current["current_suction_temp"]
    superheat_design = design["superheat_design"]
    
    if abs(superheat_actual - superheat_design) > 10:
        deviations.append({"factor": "superheat", ...})
    
    return {
        "is_uit_balans": len(deviations) > 0,
        "out_of_balance_factors": deviations
    }
```

---

### Snippet 3: Few-Shot Learning Integration
```python
# ❌ DON'T: Separate examples file (LLM doesn't see context)
# examples.txt: "User: X, Agent: Y"

# ✅ DO: Embed in branch instructions (immediate context)
instruction = """
Je bent in MELDING fase.

Conversational example (A3):
User: "Koelcel bereikt temperatuur niet"
Agent: "Ik zie in sensor data: actief alarm 'Hoge temperatuur'. 
       Koelcel 0°C, zou -33°C moeten zijn. Welke producten?"
"""
```

**Why**: Inline examples provide immediate linguistic patterns to LLM.

---

## 🚨 Critical Gotchas

### Gotcha 1: DecisionNode Options
```python
# ❌ WRONG: Access decision_nodes directly
for branch in tree.decision_nodes.values():
    print(branch.options)

# ✅ RIGHT: Use tree structure
print(tree.tree)  # Dict representation
for node in tree.tree_data.branches:  # If iterating branches
    ...
```

### Gotcha 2: Async Context Managers
```python
# ❌ WRONG: Sync context
with ClientManager().connect_to_client() as client:
    result = await client.collections.get("X").query...  # Fails!

# ✅ RIGHT: Async context
async with ClientManager().connect_to_async_client() as client:
    result = await client.collections.get("X").query.hybrid(...)
```

### Gotcha 3: Bootstrap Only Runs on "empty"
```python
# ❌ WRONG: Bootstrappers ignored
config = Config(
    branch_initialisation="default",  # NOT empty!
    feature_bootstrappers=["vsm_smido"]
)
# Result: Default tree, bootstrappers NOT applied

# ✅ RIGHT:
config = Config(
    branch_initialisation="empty",  # Required!
    feature_bootstrappers=["vsm_smido"]
)
# Result: Empty tree, bootstrappers applied
```

### Gotcha 4: Tool Must Yield, Not Return
```python
# ❌ WRONG: Return result
async def my_tool(...):
    result = compute()
    return result  # Breaks generator protocol!

# ✅ RIGHT: Yield result
async def my_tool(...):
    result = compute()
    yield Result(objects=[result])
```

---

## 📊 Performance Benchmarks

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| WorldState (60min window) | <500ms | ~400ms | ✅ |
| Weaviate query (hybrid) | <200ms | ~150ms | ✅ |
| get_alarms | <2s | ~2s | ✅ |
| get_asset_health | <10s | 20-30s | ⚠️ |
| compute_worldstate | <15s | 30s+ | ⚠️ |
| Status query (with cache) | <200ms | NOT IMPL | ❌ |
| Full SMIDO workflow | <5min | 3-5min | ✅ |

---

## 🔐 Security Patterns

### API Key Management
```bash
# .env file (not in repo)
GOOGLE_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...
WCD_URL=https://...weaviate.cloud
WCD_API_KEY=...

# .gitignore includes .env
```

### Tool Environment Filtering
```python
# Elysia automatically filters sensitive keys from tool kwargs
# client_manager doesn't expose raw API keys
# Safe to log kwargs for debugging
```

---

## 💡 Innovation Highlights

### 1. Bootstrap Registry System
First implementation of pluggable tree initialization:
- `register_bootstrapper(name, function)`
- Auto-applies on tree creation
- Clean separation: framework vs feature
- **Potential**: Reusable pattern for other Elysia features

### 2. Three-Level Prompting Hierarchy
Agent-level → Branch-level → Tool-level guidance:
- Clear separation of concerns
- Context at appropriate level
- Reusable patterns

### 3. WorldState Engine with On-Demand Computation
- Doesn't pre-aggregate (inflexible)
- Computes features for any time window
- 58 features in <500ms
- **Potential**: Generalizable to other time-series use cases

### 4. "Uit Balans" as Core Philosophy
Integration throughout prompts, tools, data model:
- Not just "broken vs working"
- But "in balance vs out of balance"
- Shifts from component replacement to system tuning
- **Potential**: Applicable to other industrial systems

---

## 🎯 Success Patterns

### Pattern 1: Data-First Development
1. Analyze data thoroughly
2. Design schemas based on real structure
3. Process and clean systematically
4. Validate before upload
5. Test with real queries

**Outcome**: Zero data quality issues in Phase 2

### Pattern 2: Test-Driven Tool Development
1. Write tool spec
2. Write test (expected behavior)
3. Implement tool
4. Run test
5. Iterate until passing

**Outcome**: 18/18 tests passing, no integration issues

### Pattern 3: Conversation Examples from Real Vlogs
1. Process vlogs to get transcripts
2. Extract natural language patterns
3. Embed in branch instructions
4. LLM learns authentic Dutch technical language

**Outcome**: Agent speaks natural Dutch, not translated English

---

## 📖 Critical References

### Weaviate v4 API
- Collections: `client.collections.get("Name")`
- Query: `.query.hybrid(query=str, filters=Filter, limit=int)`
- Filter: `Filter.by_property("field").equal(value)`
- Combine: `filter1 & filter2` (AND), `filter1 | filter2` (OR)

### Elysia Patterns
- Tree: `Tree(branch_initialisation="empty", ...)`
- Branch: `tree.add_branch(branch_id=str, from_branch_id=str, ...)`
- Tool: `@tool(status=str, branch_id=str) async def name(...):`
- Result: `yield Result(objects=list, metadata=dict)`

### DSPy Integration
- Base model for decisions: `tree.base_lm`
- Complex model for reasoning: `tree.complex_lm`
- Context switch: `with dspy.context(lm=model): ...`

---

## 🎓 Lessons for Future Features

### 1. Document Intent, Not Just Implementation
- Docs should say "PLANNED" vs "IMPLEMENTED"
- Status indicators critical
- Avoid ambiguity about what exists

### 2. User Testing Reveals Hidden Issues
- Diagram search broken (found via testing)
- I phase loops (found via testing)
- Status query slow (found via testing)
- **Learning**: Test with real usage patterns early

### 3. Performance Matters More Than Features
- 2-3 min status query unacceptable (even if functional)
- Users want instant answers for simple questions
- **Learning**: Optimize hot paths, not just implement features

### 4. Fast Engine ≠ Fast UX
- WorldState engine is fast (<500ms)
- But without get_current_status tool, UX is slow
- **Learning**: Need fast API layer on fast engine

### 5. Embedded Examples > Separate Files
- Few-shot examples in branch instructions work better
- LLM sees context immediately
- **Learning**: Keep examples close to usage point

---

**Last Updated**: November 12, 2025  
**Purpose**: Living document of critical knowledge  
**Audience**: Current and future developers

