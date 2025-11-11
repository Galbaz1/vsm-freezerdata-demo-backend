# VSM Agent Architecture - Design Motivation & Rationale

**Date**: January 11, 2025  
**Status**: Proposed Architecture  
**Diagram**: `vsm_agent_architecture.mermaid`

---

## Executive Summary

This document proposes a **hybrid architecture** that intelligently builds on Elysia's decision tree framework while adding VSM-specific layers for SMIDO methodology, WorldState computation, and multi-source data integration. The design follows a **"part adding, part replacing"** strategy that maximizes reuse of Elysia's proven components while introducing domain-specific intelligence.

---

## Core Design Principles

### 1. **Build on Elysia's Strengths**
- ✅ **Reuse**: Decision tree engine, tool system, DSPy integration, Weaviate client
- ✅ **Extend**: Add VSM-specific tools and SMIDO decision nodes
- ✅ **Enhance**: WorldState computation layer, context management

### 2. **SMIDO Methodology as First-Class Citizen**
- ✅ **Native Integration**: SMIDO steps map directly to Elysia DecisionNodes
- ✅ **Structured Workflow**: M→T→I→D→O enforced by tree structure
- ✅ **Transparent Reasoning**: Each SMIDO step visible in tree visualization

### 3. **Hybrid Data Architecture**
- ✅ **Semantic Search**: Weaviate for discovery (manuals, vlogs, incidents)
- ✅ **Time-Series Efficiency**: Parquet for WorldState computation
- ✅ **Cross-Linking**: Relationships between telemetry, manuals, vlogs

### 4. **Intelligent Context Management**
- ✅ **WorldState Engine**: Computes 60+ features on-demand from parquet
- ✅ **Context Accumulation**: User input + telemetry + historical data
- ✅ **Progressive Disclosure**: Show relevant info at each SMIDO step

---

## Architecture Layers Explained

### Layer 1: User Interface Layer
**Purpose**: Entry point for junior technicians

**Components**:
- VSM Dashboard UI (extends Elysia frontend)
- Natural language query interface
- SMIDO workflow visualization

**Design Choice**: Extend Elysia's existing frontend rather than rebuild. The tree visualization already shows decision paths - we enhance it with SMIDO-specific labels and progress indicators.

---

### Layer 2: VSM Agent Orchestration Layer
**Purpose**: Coordinates SMIDO workflow and context management

**Components**:

#### VSM Tree Instance
- **Extends**: `elysia.Tree`
- **Adds**: SMIDO-specific initialization, custom branch structure
- **Reuses**: All Elysia core functionality (async_run, tool execution, error handling)

**Why Extend vs Replace?**
- Elysia's tree engine is battle-tested and handles recursion, error recovery, and tool orchestration perfectly
- We add SMIDO-specific logic without rewriting core functionality
- Maintains compatibility with Elysia ecosystem (preprocessing, feedback system, etc.)

#### SMIDO Orchestrator
- **New Component**: Coordinates SMIDO workflow progression
- **Responsibilities**:
  - Tracks current SMIDO phase (M→T→I→D→O)
  - Manages phase transitions based on tool results
  - Enforces SMIDO methodology rules
- **Integration**: Works with Elysia DecisionNodes to guide decision-making

**Why Separate Component?**
- SMIDO logic is domain-specific and shouldn't pollute Elysia core
- Allows for future SMIDO variants or methodology updates
- Makes SMIDO workflow testable independently

#### Context Manager
- **New Component**: Manages WorldState + user input + historical context
- **Responsibilities**:
  - Accumulates context across SMIDO phases
  - Merges user-reported symptoms with telemetry data
  - Provides unified context to decision agents
- **Integration**: Populates `TreeData.environment` with structured context

**Why New Component?**
- VSM needs richer context than generic RAG (WorldState features, sensor patterns, historical incidents)
- Separates context logic from tree execution logic
- Enables context reuse across multiple troubleshooting sessions

---

### Layer 3: SMIDO Decision Tree (Elysia Decision Nodes)
**Purpose**: Map SMIDO methodology to Elysia's decision tree structure

**Mapping Strategy**:

```
SMIDO Phase          →  Elysia DecisionNode
─────────────────────────────────────────────
M - Melding          →  M_Node (root)
T - Technisch         →  T_Node
I - Installatie      →  I_Node
D - Diagnose         →  D_Node (branch)
  ├─ P1: Power       →  P1_Node
  ├─ P2: Settings    →  P2_Node
  ├─ P3: Parameters  →  P3_Node
  └─ P4: Product     →  P4_Node
O - Onderdelen       →  O_Node
```

**Design Choices**:

1. **One DecisionNode per SMIDO Phase**
   - ✅ Clear separation of concerns
   - ✅ Each node has specific instruction and available tools
   - ✅ Enables phase-specific reasoning prompts

2. **D_Node as Branch Node**
   - ✅ 3 P's are parallel checks (can be done in any order)
   - ✅ Agent decides which P to check first based on symptoms
   - ✅ More flexible than strict sequential flow

3. **Reuse Elysia DecisionNode Class**
   - ✅ No need to reinvent decision logic
   - ✅ Inherits error handling, retry logic, reasoning chain
   - ✅ Compatible with Elysia's visualization

**Why Not Replace DecisionNode?**
- Elysia's DecisionNode handles LLM interaction, validation, retry logic perfectly
- We only customize the instruction and options per SMIDO phase
- Maintains compatibility with Elysia's feedback system

---

### Layer 4: VSM Domain Tools (Elysia Tools)
**Purpose**: Domain-specific operations for troubleshooting

**Tool Design Pattern**:

All VSM tools follow Elysia's Tool interface:
```python
@tool(tree=vsm_tree, branch_id="smido_diagnose")
async def compute_worldstate(
    asset_id: str,
    timestamp: str,
    window_minutes: int = 60,
    tree_data: TreeData = None
):
    yield Status("Computing WorldState features...")
    # Read from parquet, compute features
    worldstate = compute_features(asset_id, timestamp, window_minutes)
    yield Result(objects=[worldstate], metadata={"source": "worldstate_engine"})
```

**VSM Tools**:

1. **ComputeWorldState Tool**
   - **Purpose**: Compute 60+ features from telemetry parquet
   - **Data Source**: Local parquet files (not Weaviate)
   - **Why Separate Tool?**: WorldState computation is expensive and domain-specific. Better to compute on-demand than store all features in Weaviate.

2. **QueryTelemetryEvents Tool**
   - **Purpose**: Find similar historical incidents
   - **Data Source**: VSM_TelemetryEvent (Weaviate)
   - **Why Separate Tool?**: Extends Elysia's Query tool with telemetry-specific filters (failure_mode, severity, time range)

3. **SearchManualsBySMIDO Tool**
   - **Purpose**: Find manual sections + diagrams relevant to current SMIDO phase
   - **Data Source**: VSM_ManualSections, VSM_Diagram (Weaviate)
   - **Why Separate Tool?**: SMIDO-aware filtering + returns visual diagrams alongside text

4. **QueryVlogCases Tool**
   - **Purpose**: Find similar troubleshooting cases from videos
   - **Data Source**: VSM_VlogCase, VSM_VlogClip (Weaviate), .mov files (local)
   - **Why Separate Tool?**: Vlog-specific search (problem matching, component matching)

5. **GetAlarms Tool**
   - **Purpose**: Retrieve active alarms for asset
   - **Data Source**: VSM_TelemetryEvent or FD_Alarms (Weaviate)
   - **Why Separate Tool?**: Alarm-specific logic (severity filtering, acknowledgment status)

6. **GetAssetHealth Tool**
   - **Purpose**: Health summary (current state + recent trends)
   - **Data Source**: Multiple (WorldState + Weaviate)
   - **Why Separate Tool?**: Aggregates multiple data sources into single health view

7. **AnalyzeSensorPattern Tool**
   - **Purpose**: Compare current state against known failure patterns
   - **Data Source**: VSM_WorldStateSnapshot (Weaviate), Parquet (via WorldState Engine)
   - **Why Separate Tool?**: Pattern matching requires reference data (synthetic snapshots)

**Tool Data Dependencies**:
- **Real Data Only**: ComputeWorldState, QueryTelemetryEvents, SearchManualsBySMIDO, QueryVlogCases, GetAlarms
- **Needs Synthetic**: GetAssetHealth (installation context), AnalyzeSensorPattern (reference patterns)

**Why Not Just Use Elysia's Query Tool?**
- Elysia's Query tool is generic and doesn't understand SMIDO or WorldState
- VSM tools add domain logic (SMIDO filtering, WorldState computation, pattern matching)
- Better separation: generic in Elysia core, domain in VSM layer

---

### Layer 5: Elysia Core (Reused)
**Purpose**: Leverage Elysia's proven components

**What We Reuse**:

1. **Elysia Tree Engine**
   - ✅ Decision orchestration
   - ✅ Tool execution loop
   - ✅ Error handling and retry logic
   - ✅ Recursion control
   - ✅ Tree visualization

2. **Query Tool**
   - ✅ Used by VSM tools for Weaviate queries
   - ✅ Hybrid/semantic/keyword search
   - ✅ Dynamic filtering and sorting

3. **Aggregate Tool**
   - ✅ Used for statistics (e.g., alarm counts, incident frequencies)

4. **Text Response Tool**
   - ✅ Final answer generation
   - ✅ SMIDO-formatted responses

5. **TreeData/Environment**
   - ✅ Global state management
   - ✅ Context accumulation across SMIDO phases
   - ✅ Tool result storage

6. **DSPy Integration**
   - ✅ LLM interaction framework
   - ✅ Multi-model routing (base vs complex)
   - ✅ Few-shot learning with feedback

**What We Don't Change**:
- Core tree execution logic
- Tool execution pattern (async generators)
- Error handling mechanisms
- Feedback system
- Preprocessing pipeline

**Why This Approach?**
- Elysia core is well-tested and handles complex scenarios
- No need to reinvent the wheel
- Maintains compatibility with Elysia ecosystem
- Focuses our effort on VSM-specific logic

---

### Layer 6: Data Computation Layer
**Purpose**: Efficient computation of WorldState features and pattern detection

**Components**:

#### WorldState Engine
- **Purpose**: Compute 60+ features from telemetry parquet
- **Input**: asset_id, timestamp, window_minutes
- **Output**: Structured WorldState dict
- **Why Separate Engine?**: 
  - Feature computation is complex (60+ features, multiple time windows)
  - Better to compute on-demand than store all features
  - Can be reused by multiple tools

#### Parquet Reader
- **Purpose**: Efficient time-window queries on parquet files
- **Why Not Weaviate?**: 
  - Parquet is optimized for time-series queries (785K rows)
  - Weaviate is optimized for semantic search (not time-series)
  - Hybrid approach: Weaviate for discovery, parquet for computation

#### Event Detector
- **Purpose**: Detect incidents from telemetry flags
- **Output**: Event metadata for Weaviate import
- **Why Separate?**: Event detection logic is domain-specific

#### Pattern Analyzer
- **Purpose**: Detect patterns (cycling, drift, spikes)
- **Integration**: Used by AnalyzeSensorPattern tool
- **Why Separate?**: Pattern detection is complex domain logic

**Design Choice: Hybrid Data Architecture**

```
Discovery (Weaviate)          Computation (Parquet)
─────────────────────          ───────────────────
VSM_TelemetryEvent            Telemetry Parquet
  ↓                              ↓
~1000 incidents             785K datapoints
Semantic search              Time-window queries
WorldState metadata          Raw sensor data
```

**Why This Split?**
- **Weaviate**: Best for semantic search ("find incidents similar to frozen evaporator")
- **Parquet**: Best for time-series computation ("compute 30min trends")
- **Hybrid**: Agent queries Weaviate for discovery, reads parquet for detailed analysis

---

### Layer 7: Weaviate Collections (Semantic Search)
**Purpose**: Store searchable, semantic data for RAG

**Collections**:

1. **VSM_ManualSections** (~240 sections)
   - Logical sections (grouped from 922 chunks)
   - SMIDO-tagged, failure mode tagged
   - Vectorized for semantic search

2. **VSM_TelemetryEvent** (~1000 incidents)
   - Aggregated incidents (not all 785K datapoints)
   - WorldState metadata (min/max/mean per sensor)
   - Failure mode, severity, components

3. **VSM_VlogCase** (5 cases)
   - Aggregated cases (A1-A5)
   - Problem→Solution workflows
   - SMIDO step mapping

4. **VSM_VlogClip** (15 clips)
   - Individual video clips
   - Timestamps, transcripts, components

5. **VSM_Diagram** (9 diagrams)
   - Mermaid logic diagrams
   - Linked to manual sections
   - Used by SearchManualsBySMIDO

6. **VSM_WorldStateSnapshot** (5-10 patterns)
   - Reference patterns for failure modes
   - Used by AnalyzeSensorPattern
   - Synthetic (generated from real events)

**Design Choice: Aggregated vs Raw**

- **Weaviate**: Aggregated metadata (events, sections, cases)
- **Local Files**: Raw data (parquet, JSONL, videos)

**Why?**
- Weaviate is for discovery and semantic matching
- Raw data is for detailed analysis and computation
- Prevents storing 785K objects in Weaviate (costly, slow)

---

### Layer 8: Local Data Storage (Raw Data)
**Purpose**: Store raw data for detailed analysis

**Files**:

1. **Telemetry Parquet** (785K rows)
   - 1-minute intervals, 2.2 years
   - Efficient for time-window queries
   - Used by WorldState Engine

2. **Manual JSONL** (922 chunks)
   - Source data (audit trail)
   - Used for section grouping

3. **Vlog .mov Files** (15 videos, 21.7 MB)
   - Video playback
   - Not stored in Weaviate (too large)

**Why Keep Raw Data?**
- ComputeWorldState needs 785K datapoints for on-demand feature computation
- Parquet optimized for time-window queries (not Weaviate)
- Efficient storage and audit trail

---

### Layer 9: LLM Layer (DSPy)
**Purpose**: LLM interaction for decision-making and analysis

**Components**:

1. **Base LM** (gemini-1.5-flash)
   - Fast decisions at SMIDO nodes
   - Tool selection
   - Simple reasoning

2. **Complex LM** (gemini-1.5-pro)
   - Deep analysis (WorldState interpretation)
   - Complex query generation
   - Final answer synthesis

3. **Feedback System**
   - Few-shot learning
   - User-specific personalization
   - Successful troubleshooting patterns

**Design Choice: Multi-Model Routing**

- **Base LM**: SMIDO node decisions (fast, cheap)
- **Complex LM**: WorldState analysis, final answers (accurate, expensive)

**Why?**
- Optimizes cost and latency
- Base LM sufficient for structured decisions (SMIDO workflow)
- Complex LM needed for nuanced analysis (interpreting sensor patterns)

---

## Key Architectural Decisions

### Decision 1: Extend vs Replace Elysia Tree
**Choice**: Extend  
**Rationale**:
- Elysia's tree engine handles complex scenarios (recursion, error recovery, tool orchestration)
- No need to reinvent proven functionality
- Maintains compatibility with Elysia ecosystem

**Trade-offs**:
- ✅ Pros: Faster development, proven reliability, ecosystem compatibility
- ⚠️ Cons: Must work within Elysia's constraints, less control over core logic

---

### Decision 2: SMIDO as Decision Nodes vs Separate Workflow Engine
**Choice**: SMIDO as Decision Nodes  
**Rationale**:
- Direct mapping: SMIDO phase → DecisionNode
- Leverages Elysia's decision logic (LLM interaction, validation, retry)
- Transparent reasoning (visible in tree visualization)

**Trade-offs**:
- ✅ Pros: Native integration, transparent reasoning, leverages Elysia features
- ⚠️ Cons: Must express SMIDO as decision tree (some phases are more sequential than tree-like)

---

### Decision 3: Hybrid Data Architecture (Weaviate + Parquet)
**Choice**: Hybrid  
**Rationale**:
- Weaviate: Best for semantic search (discovery)
- Parquet: Best for time-series computation (WorldState)
- Each tool uses the right data source for its purpose

**Trade-offs**:
- ✅ Pros: Optimal performance for each use case, cost-effective
- ⚠️ Cons: Two data sources to maintain, need synchronization logic

---

### Decision 4: WorldState Computation On-Demand vs Pre-computed
**Choice**: On-Demand  
**Rationale**:
- 60+ features × 785K datapoints = too much to pre-compute
- On-demand computation allows flexible time windows
- Parquet is efficient for time-window queries

**Trade-offs**:
- ✅ Pros: Flexible, storage-efficient, can compute any time window
- ⚠️ Cons: Computation cost per query, must optimize WorldState Engine

---

### Decision 5: VSM Tools vs Generic Elysia Tools
**Choice**: VSM Tools  
**Rationale**:
- Domain-specific logic (SMIDO filtering, WorldState computation, pattern detection)
- Better separation of concerns
- Easier to test and maintain

**Trade-offs**:
- ✅ Pros: Domain-specific logic, better testability, clearer responsibilities
- ⚠️ Cons: More tools to maintain, potential code duplication

---

## Integration Points

### 1. SMIDO Orchestrator ↔ Elysia Tree
- **Interface**: SMIDO Orchestrator sets DecisionNode instructions based on current phase
- **Data Flow**: Orchestrator → TreeData → DecisionNode prompts
- **Challenge**: Ensuring SMIDO workflow is enforced while allowing agent flexibility

### 2. WorldState Engine ↔ VSM Tools
- **Interface**: Tools call WorldState Engine with asset_id, timestamp, window
- **Data Flow**: Tool → WorldState Engine → Parquet Reader → Features → Tool
- **Challenge**: Efficient computation, caching strategies

### 3. VSM Tools ↔ Elysia Query Tool
- **Interface**: VSM tools use Elysia Query tool for Weaviate queries
- **Data Flow**: VSM Tool → Elysia Query → Weaviate → Results → VSM Tool
- **Challenge**: Adding SMIDO-specific filters while reusing Query tool logic

### 4. Context Manager ↔ TreeData
- **Interface**: Context Manager populates TreeData.environment
- **Data Flow**: Context Manager → TreeData.environment → DecisionNode prompts
- **Challenge**: Structuring context for effective LLM reasoning

---

## Comparison with Alternative Architectures

### Alternative 1: Full Custom Agent (No Elysia)
**Why Not?**
- ❌ Reinvents decision tree logic, tool system, LLM integration
- ❌ Loses Elysia's proven error handling, feedback system, preprocessing
- ❌ Much more development effort

**Our Choice**: ✅ Extend Elysia

---

### Alternative 2: Pure Elysia (No VSM Layers)
**Why Not?**
- ❌ No SMIDO methodology enforcement
- ❌ No WorldState computation
- ❌ Generic tools don't understand domain

**Our Choice**: ✅ Add VSM layers

---

### Alternative 3: All Data in Weaviate (No Parquet)
**Why Not?**
- ❌ 785K telemetry objects in Weaviate (costly, slow)
- ❌ Time-series queries inefficient in Weaviate
- ❌ WorldState computation would require querying 785K objects

**Our Choice**: ✅ Hybrid architecture

---

### Alternative 4: Pre-compute All WorldState Features
**Why Not?**
- ❌ 60+ features × 785K datapoints = massive storage
- ❌ Inflexible (can't compute custom time windows)
- ❌ Still need on-demand computation for real-time queries

**Our Choice**: ✅ On-demand computation

---

## Implementation Strategy

### Phase 1: Foundation (Week 1-2)
1. ✅ Extend Elysia Tree with VSM initialization
2. ✅ Create SMIDO DecisionNodes (M, T, I, D, O)
3. ✅ Implement Context Manager
4. ✅ Create basic VSM tools (stubs)

### Phase 2: Data Integration (Week 3-4)
1. ✅ Implement WorldState Engine
2. ✅ Create Parquet Reader
3. ✅ Import real data to Weaviate (VSM_ManualSections, VSM_Diagram, VSM_TelemetryEvent, VSM_VlogCase)
4. ✅ Generate synthetic data (VSM_WorldStateSnapshot, enrich FD_Assets)
5. ✅ Run Elysia preprocessing

### Phase 3: Tool Implementation (Week 5-6)
1. ✅ Implement ComputeWorldState tool
2. ✅ Implement QueryTelemetryEvents tool
3. ✅ Implement SearchManualsBySMIDO tool
4. ✅ Implement QueryVlogCases tool
5. ✅ Implement remaining VSM tools

### Phase 4: SMIDO Workflow (Week 7-8)
1. ✅ Implement SMIDO Orchestrator
2. ✅ Connect SMIDO nodes with tools
3. ✅ Test SMIDO workflow (A3 scenario)
4. ✅ Refine prompts and decision logic

### Phase 5: Demo & Polish (Week 9-10)
1. ✅ Create demo scenarios (A3, A1)
2. ✅ UI enhancements (SMIDO visualization)
3. ✅ Performance optimization
4. ✅ Documentation

---

## Success Criteria

### Functional Requirements
- ✅ Agent follows SMIDO methodology (M→T→I→D→O)
- ✅ Agent computes WorldState features on-demand
- ✅ Agent finds relevant manuals, vlogs, incidents
- ✅ Agent provides actionable troubleshooting guidance

### Performance Requirements
- ✅ WorldState computation < 500ms for 60min window
- ✅ Weaviate queries < 200ms
- ✅ End-to-end troubleshooting session < 30 seconds

### Quality Requirements
- ✅ A3 scenario: Agent correctly identifies frozen evaporator
- ✅ Agent cites relevant manual sections and vlog cases
- ✅ Agent provides SMIDO-structured solution

---

## Conclusion

This architecture **intelligently builds on Elysia** by:

1. **Reusing** proven components (tree engine, tool system, DSPy integration)
2. **Extending** with VSM-specific layers (SMIDO orchestrator, WorldState engine, domain tools)
3. **Enhancing** with hybrid data architecture (Weaviate + Parquet)

The result is a **domain-specific agent** that:
- ✅ Enforces SMIDO methodology
- ✅ Computes rich WorldState features
- ✅ Integrates multiple data sources
- ✅ Provides transparent, actionable guidance

**Key Insight**: We don't replace Elysia - we **extend it intelligently** to serve VSM's specific needs while maintaining compatibility with the Elysia ecosystem.

---

**Next Steps**: Review this architecture, validate design decisions, and proceed with Phase 1 implementation.

