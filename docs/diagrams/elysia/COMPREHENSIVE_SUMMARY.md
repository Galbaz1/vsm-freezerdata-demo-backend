# Elysia Framework: Comprehensive Technical Summary

**Date**: November 11, 2025  
**Source**: Official Weaviate Elysia Repository  
**Documentation Type**: Low-Level Technical Architecture

---

## Executive Summary

Elysia is an open-source, decision tree-based agentic RAG framework developed by Weaviate. Unlike traditional agentic systems where all tools are available at runtime, Elysia uses a pre-defined tree structure where each node is orchestrated by a decision agent with full context awareness. The system combines intelligent decision-making, dynamic data display, and comprehensive data analysis to create a transparent, self-healing AI assistant.

---

## Core Architecture

### Three Pillars

#### 1. Decision Tree Architecture
- **Pre-defined tree structure** with nodes and branches (not flat tool access)
- **Decision agent per node** evaluates past actions, future possibilities, and current context
- **Global context awareness** through TreeData object shared across all nodes
- **Advanced error handling** with impossible flags, retry logic, and self-healing
- **Transparent reasoning** visible in real-time through frontend visualization
- **Recursion control** with configurable limits (default 3-5 iterations)

#### 2. Dynamic Display Types
- **7+ display formats**: table, document, product card, ticket, conversation, message, chart, generic
- **AI-driven selection**: LLM analyzes data structure and recommends best format
- **Property mapping**: Automatic mapping from data fields to frontend display schemas
- **User override**: Manual adjustment of display types and mappings
- **Future extensibility**: Plan to add action capabilities (book hotel, reply to message, add to cart)

#### 3. Data Awareness & Analysis
- **Automatic collection analysis**: LLM examines structure, samples data, generates metadata
- **Property descriptions**: AI-generated descriptions for each field
- **Collection summaries**: High-level overview of dataset purpose and content
- **Example queries**: Pre-generated example questions users might ask
- **Named vector detection**: Identifies and catalogs all vector search options
- **Display type suggestions**: Recommends appropriate visualizations
- **Metadata storage**: All analysis stored in `ELYSIA_METADATA__` Weaviate collection

---

## Component Breakdown

### 1. Tree Class
**Location**: `elysia/tree/tree.py`

**Primary Responsibilities**:
- Orchestrates entire decision tree execution
- Manages decision nodes and tool registry
- Maintains global state (TreeData, Environment)
- Handles recursion and completion logic
- Tracks performance metrics and token usage
- Exports/imports tree state to/from Weaviate

**Key Methods**:
- `async_run()`: Main execution loop (async generator)
- `run()`: Synchronous wrapper for async_run
- `add_tool()`, `remove_tool()`: Tool management
- `add_branch()`, `remove_branch()`: Branch management
- `export_to_json()`, `import_from_json()`: Serialization
- `export_to_weaviate()`, `import_from_weaviate()`: Persistence

**Initialization Modes**:
1. **one_branch** (default): Single flat branch with all tools
2. **multi_branch**: Hierarchical structure (base → search sub-branch)
3. **empty**: No tools/branches, manual construction required

### 2. TreeData Class
**Location**: `elysia/tree/objects.py`

**Purpose**: Global state container shared across all nodes and tools

**Contains**:
- `environment`: Store of all retrieved objects and results
- `atlas`: Style, agent description, end goal, datetime reference
- `collection_data`: Collection schemas and metadata
- `conversation_history`: User/assistant message log
- `tasks_completed`: LLM-visible task execution log
- `errors`: Self-healing error storage by tool name
- `num_trees_completed`: Recursion counter
- `recursion_limit`: Maximum iterations (default 3-5)

**Key Features**:
- `tasks_completed_string()`: Formats task log for LLM prompts
- `output_collection_metadata()`: Returns collection schemas
- `output_collection_return_types()`: Returns display type mappings
- JSON serialization/deserialization support

### 3. Environment Class
**Location**: `elysia/tree/objects.py`

**Structure**:
```python
{
    "tool_name": {
        "result_name": [
            {
                "metadata": dict,  # Query info, time taken, etc.
                "objects": list[dict]  # Retrieved objects with _REF_ID
            }
        ]
    }
}
```

**Dual Storage**:
1. **environment**: Visible to LLM in prompts
2. **hidden_environment**: Hidden from LLM, used for inter-tool data passing

**Key Methods**:
- `add()`: Add Result object automatically
- `add_objects()`: Manually add objects
- `remove()`, `replace()`: Modify stored data
- `find()`: Retrieve by tool_name and result_name
- `is_empty()`: Check if any data stored (excluding SelfInfo)

**Duplicate Handling**: 
- Objects get unique `_REF_ID`
- Duplicates marked with original `_REF_ID` + `[repeat]` flag

### 4. DecisionNode Class
**Location**: `elysia/tree/util.py`

**Purpose**: Represents a decision point in the tree

**Properties**:
- `id`: Unique identifier (e.g., "base", "search", "base.query")
- `instruction`: What should the agent decide at this node?
- `options`: Dict of available actions/branches
- `root`: Is this the root node?

**Option Structure**:
```python
{
    "option_id": {
        "description": str,      # What does this option do?
        "inputs": dict,          # Required input schema
        "action": Tool | None,   # Tool to execute (None = branch)
        "end": bool,            # Can end conversation here?
        "status": str,          # Status message while running
        "next": DecisionNode | None  # Next node if branch
    }
}
```

**Decision Process**:
1. Check if only one option (auto-select if true)
2. Build prompt with available options and context
3. Wrap in AssertedModule for validation
4. LLM generates decision
5. Validate choice is in available options
6. Retry with feedback if validation fails (max 2-3 times)
7. Return Decision object

### 5. Tool System
**Base Class**: `elysia/objects.py`

**Required Methods**:
- `__init__()`: Define name, description, inputs, end flag
- `async __call__()`: Main execution (must be async generator)
- `async is_tool_available()`: Check if tool can be used (optional)
- `async run_if_true()`: Auto-execute if condition met (optional)

**Yield Types**:
- `Result/Retrieval`: Data objects
- `Response/Text`: Text messages
- `Status`: Progress updates
- `Error`: Error feedback for self-healing
- `TrainingUpdate`: Feedback system data
- `TreeUpdate`: Tree state changes

**Built-in Tools**:
1. **Query**: Hybrid/semantic/keyword search with dynamic filtering
2. **Aggregate**: GroupBy, statistics, metrics calculation
3. **Visualise**: Chart generation
4. **CitedSummarizer**: Summarize with citations
5. **FakeTextResponse**: End conversation with text
6. **ForcedTextResponse**: Automatic final response
7. **SummariseItems**: Conditional summarization of retrieved items

**Custom Tool Creation**:
```python
@tool(tree=tree, branch_id="base", end=True)
async def my_tool(param1: str, param2: int = 10, tree_data: TreeData = None):
    yield Status("Working...")
    result = do_something(param1, param2)
    yield Result(objects=[result], metadata={"source": "my_tool"})
```

### 6. DSPy Integration
**Location**: `elysia/util/elysia_chain_of_thought.py`

**Purpose**: Custom DSPy module for LLM interactions

**Key Features**:
- Extends `dspy.Module`
- Dynamic prompt building with context
- Multi-model routing (base vs complex)
- Few-shot learning with feedback examples
- Signature system for structured I/O

**ElysiaChainOfThought**:
```python
module = ElysiaChainOfThought(
    signature=DecisionPrompt,
    tree_data=tree_data,
    environment=True,        # Include environment in prompt
    collection_schemas=True,  # Include schemas
    tasks_completed=True,     # Include task log
    message_update=True,      # Include message field
    reasoning=True           # Include reasoning field
)
```

**Multi-Model Strategy**:
- **base_lm**: Fast, small models for decision agents, simple tasks
- **complex_lm**: Large models for query generation, complex analysis
- Configured via Settings (BASE_MODEL, COMPLEX_MODEL)

### 7. Query Tool (Detailed)
**Location**: `elysia/tools/retrieval/query.py`

**Execution Flow**:
1. Get collection schemas from TreeData
2. Check if collections are vectorized
3. Build QueryCreatorPrompt with context
4. LLM generates QueryOutput objects
5. Validate collection names and filters
6. Evaluate if chunking needed per collection
7. If chunking: Create chunks, query chunks
8. If no chunking: Query original collection directly
9. Format results based on display_type
10. Apply mappings for frontend
11. Check if summarization needed
12. Yield retrieval objects or add to hidden_environment

**Query Output Structure**:
```python
{
    "target_collections": ["CollectionName"],
    "search_query": "semantic search text",
    "search_type": "hybrid" | "semantic" | "keyword" | "filter_only",
    "filters": Filter(...),  # Weaviate Filter object
    "limit": 10,
    "sort_by": [{"property": "date", "order": "desc"}],
    "alpha": 0.5  # For hybrid search
}
```

**Chunking Logic**:
- Criteria: display_type=="document" AND content_field_mean > 400 tokens AND search_type != "filter_only"
- Process: Query unchunked with 3× limit → Chunk documents → Store in `ELYSIA_CHUNKED_*` → Query chunks
- Benefits: Storage savings, on-demand processing, better retrieval

### 8. Feedback System
**Storage**: `ELYSIA_FEEDBACK__` Weaviate collection

**Workflow**:
1. User query executes
2. System checks USE_FEEDBACK flag
3. If enabled: Vector search for similar past queries with positive ratings
4. Filter by user_id and model name
5. Retrieve top k examples
6. Format as DSPy few-shot examples
7. Include in LLM prompt
8. After execution, store TrainingUpdate
9. User rates response (👍/👎)
10. If positive, store input/output in feedback collection

**Benefits**:
- Smaller models achieve better results over time
- User-specific personalization
- Cost reduction through model downgrading
- Consistent output formatting

### 9. Preprocessing Pipeline
**Function**: `elysia/preprocessing/collection.py::preprocess()`

**Steps**:
1. Connect to Weaviate collection
2. Sample up to 50 objects
3. Analyze schema and properties
4. Calculate statistics (mean, min, max, unique values)
5. LLM generates property descriptions
6. LLM generates collection summary
7. LLM generates example queries
8. LLM recommends display types
9. LLM creates property mappings for each display type
10. Store all metadata in `ELYSIA_METADATA__`

**Metadata Structure**:
```python
{
    "name": "CollectionName",
    "summary": "AI-generated summary",
    "fields": [
        {
            "name": "field_name",
            "type": "text" | "number" | "boolean" | "uuid" | "date",
            "description": "AI-generated description",
            "mean": 45.2,  # For numeric/text length
            "range": [min, max],  # For numeric
            "groups": {"value1": count1, "value2": count2}  # For categorical
        }
    ],
    "mappings": {
        "table": {"frontend_field": "data_field", ...},
        "document": {...}
    },
    "length": 1000,  # Object count
    "vectorizer": "text2vec-openai",
    "named_vectors": [
        {
            "name": "default",
            "enabled": true,
            "source_properties": ["title", "content"]
        }
    ],
    "index_properties": {
        "isNullIndexed": true,
        "isLengthIndexed": false,
        "isTimestampIndexed": true
    }
}
```

---

## Execution Flow

### Main Loop (tree.async_run)

1. **Initialization** (_first_run=True):
   - Soft reset (clear temporary state)
   - Validate LM settings
   - Load collection metadata from Weaviate
   - Remove empty branches
   - Update conversation history

2. **Tree Traversal Loop**:
   ```
   While not complete:
       a. Get available tools at current node
       b. Check run_if_true rules (auto-execute tools)
       c. Decision agent chooses action/branch
       d. Execute tool if action exists:
          - Start tracking
          - Call tool.__call__() async generator
          - For each yielded result:
            * Evaluate result type
            * Update environment if Result
            * Store error if Error
            * Send to frontend via Returner
          - End tracking
          - Clear errors if successful
       e. Check if end of branch:
          - If has next node AND not completed: continue
          - If end of branch OR completed: break
   ```

3. **Completion Check**:
   - Reached text_response?
   - impossible flag set?
   - end_actions flag set?
   - Recursion limit reached?

4. **End of Tree**:
   - If completed: Save history, yield Completed, close clients
   - If not completed AND under recursion limit: Recursively call async_run (start from root again)
   - If at recursion limit: Force completion with warning

### Error Handling & Self-Healing

**Error Storage**:
```python
tree_data.errors = {
    "tool_name": [
        "Error message 1",
        "Error message 2"
    ]
}
```

**Self-Healing Process**:
1. Tool yields Error object
2. Tree stores in tree_data.errors[tool_name]
3. Error visible to next decision agent
4. Agent can:
   - Retry same tool with corrections
   - Try different tool/approach
   - Mark task as impossible
5. If tool succeeds, clear its error list

**Impossible Flag**:
- Set when data mismatch detected
- Set when repeated failures occur
- Set when LLM determines task cannot be completed
- Forces immediate completion

---

## Backend (FastAPI)

### Application Structure
**File**: `elysia/api/app.py`

**Components**:
- FastAPI app with lifespan management
- CORS middleware (allow all)
- Error handlers (HTTP, validation, general)
- Static file serving (Next.js frontend as HTML)
- WebSocket support for real-time streaming
- Background scheduler for cleanup tasks

**Key Routes**:
- `/init`: Initialization endpoints (settings, collections, metadata)
- `/ws/query`: WebSocket for query streaming
- `/ws/preprocess`: WebSocket for preprocessing progress
- `/collections`: Collection CRUD operations
- `/user/config`: User configuration management
- `/tree/config`: Tree state management
- `/feedback`: Feedback submission and retrieval
- `/api/health`: Health check

**Lifespan Events**:
- Startup: Initialize UserManager, start AsyncIOScheduler
- Background jobs: check_timeouts (29s), check_restart_clients (31s), output_resources (1103s)
- Shutdown: Stop scheduler, close all Weaviate clients

**Static Serving**:
- Next.js build served as static HTML
- `/_next/`: JavaScript bundles, CSS, fonts
- `/static/`: Other static assets
- `/`: Serves index.html

### User & Tree Management
**Location**: `elysia/api/services/user.py`

**UserManager**:
- Singleton managing all user sessions
- Creates TreeManager per user
- Manages ClientManager per user
- Handles timeouts and cleanup

**TreeManager**:
- Creates Tree instances per conversation
- Manages active queries
- Stores conversation history
- Exports/imports tree state

**ClientManager**:
- Manages Weaviate async client connections
- Connection pooling
- Automatic reconnection
- Client lifecycle management

---

## Frontend Integration

### Communication Protocol
**WebSocket Streaming**:
- Client connects to `/ws/query`
- Sends JSON message with query and settings
- Server streams results as JSON objects
- Each message has:
  ```json
  {
      "type": "result" | "text" | "status" | "error" | "tree_update" | "completed",
      "id": "uuid",
      "user_id": "uuid",
      "conversation_id": "uuid",
      "query_id": "uuid",
      "payload": {...}
  }
  ```

### Result Types
1. **result**: Retrieved data objects
   - Includes display type
   - Includes metadata
   - Includes mapped properties for frontend

2. **text**: Text responses
   - Assistant messages
   - Streaming or complete

3. **status**: Progress updates
   - "Querying..."
   - "Chunking X objects..."
   - "Retrieved X objects..."

4. **tree_update**: Tree state changes
   - from_node, to_node
   - reasoning (if enabled)
   - reset_tree flag

5. **completed**: Query finished
   - Signals end of stream

6. **error**: Error occurred
   - Feedback for self-healing
   - Error message

### Tree Visualization
- Real-time display of decision tree structure
- Nodes show: name, instruction, reasoning
- Highlights current node
- Shows entire decision path
- Updates as tree traverses

---

## Advanced Features

### 1. Chunk-On-Demand
**Benefit**: Reduces storage by 80-90% compared to pre-chunking

**Process**:
1. Query determines relevance at document level
2. If documents are large (>400 tokens) and relevant, chunk them
3. Store chunks in parallel `ELYSIA_CHUNKED_*` collection with cross-references
4. Query chunks instead of full documents
5. Reuse chunks for future similar queries

**Implementation**:
- AsyncCollectionChunker manages process
- Chunks ~500 tokens with ~50 token overlap
- Cross-reference via "isChunked" property
- Quantized storage for efficiency

### 2. Feedback System
**Storage**: User-specific examples in Weaviate

**Learning Mechanism**:
1. Store successful query patterns
2. Vector search for similar contexts
3. Use as few-shot examples
4. Improve smaller model performance
5. Reduce costs over time

**Personalization**:
- Each user has own feedback collection
- Examples don't cross-contaminate
- Adapts to individual preferences

### 3. Self-Healing Errors
**Mechanism**:
- Errors stored per tool name
- Visible to decision agent
- Agent decides to retry or pivot
- Automatic correction attempts
- Prevents infinite loops with max tries

### 4. Multi-Model Strategy
**Routing Logic**:
- Decision agents: base_lm (fast, cheap)
- Query generation: complex_lm (accurate, expensive)
- Text responses: base_lm
- Aggregations: complex_lm
- Configurable per use case

### 5. Conversation Management
**Storage**: `ELYSIA_CONVERSATIONS__` collection

**Features**:
- Export/import tree state
- Resume conversations
- Conversation history preservation
- Title generation
- Follow-up suggestions

---

## Configuration & Setup

### Settings Object
**Location**: `elysia/config.py`

**Key Properties**:
```python
WCD_URL: str              # Weaviate Cloud URL
WCD_API_KEY: str          # Weaviate API key
API_KEYS: dict            # Provider API keys
BASE_PROVIDER: str        # E.g., "google" / "openai"
BASE_MODEL: str           # E.g., "gemini-1.5-flash"
COMPLEX_PROVIDER: str     # E.g., "google"
COMPLEX_MODEL: str        # E.g., "gemini-1.5-pro"
BASE_USE_REASONING: bool  # Include reasoning in base LM outputs
COMPLEX_USE_REASONING: bool
USE_FEEDBACK: bool        # Enable feedback system
LOGGING_LEVEL: str        # DEBUG, INFO, WARNING, ERROR
```

### Environment Setup
```bash
# Install
pip install elysia-ai

# Start web app
elysia start

# Or use as library
python
>>> from elysia import Tree, preprocess
>>> preprocess("MyCollection")
>>> tree = Tree()
>>> tree("What is Elysia?")
```

### Configuration Methods
1. `.env` file
2. `Settings.smart_setup()` - Interactive CLI
3. `Settings.configure(**kwargs)` - Programmatic
4. Web UI - Settings tab

---

## Performance & Optimization

### Token Usage Tracking
- Separate tracking for base_lm and complex_lm
- Per-tool tracking
- Input/output token counts
- Cost calculation
- Average metrics

### Memory Management
- `low_memory` mode: LMs not cached
- `detailed_memory_usage()` method
- Lazy loading of collections
- Client connection pooling

### Caching
- Collection metadata cached in TreeData
- Chunked collections cached in Weaviate
- Feedback examples cached locally
- Client connections pooled

---

## Key Design Patterns

### 1. Async Generators
- All tools use async generator pattern
- Enables streaming results
- Non-blocking execution
- Frontend real-time updates

### 2. Context Managers
- ElysiaKeyManager for API keys
- ClientManager for Weaviate connections
- Automatic cleanup

### 3. Dependency Injection
- Settings passed to Tree
- TreeData passed to all nodes/tools
- LMs passed at execution time

### 4. Observer Pattern
- TreeReturner observes results
- Frontend subscribes to updates
- Real-time visualization

### 5. Strategy Pattern
- Multiple branch initialization strategies
- Multiple display type strategies
- Multi-model routing strategy

### 6. Factory Pattern
- Tool creation via @tool decorator
- DecisionNode creation via add_branch
- Result object creation

---

## Comparison with Traditional RAG

| Feature | Traditional RAG | Elysia |
|---------|----------------|--------|
| **Tool Access** | All tools available always | Structured tree navigation |
| **Context Awareness** | Per-query context | Global persistent context |
| **Data Display** | Text only | 7+ dynamic formats |
| **Data Understanding** | Blind queries | Full schema awareness |
| **Error Handling** | Fail and retry | Self-healing with feedback |
| **Transparency** | Black box | Full tree visualization |
| **Personalization** | None | User-specific feedback learning |
| **Document Handling** | Pre-chunk everything | Chunk-on-demand |
| **Model Usage** | One model for all | Multi-model routing |

---

## Extension Points for VSM Project

### 1. Custom Tools
Create VSM-specific tools for:
- `compute_worldstate`: Calculate 60+ telemetry features from parquet
- `query_manuals_by_smido`: Search manuals filtered by SMIDO step
- `query_vlog_cases`: Search video case metadata
- `query_telemetry_events`: Search historical incidents
- `analyze_sensor_pattern`: Pattern matching on timeseries

### 2. Custom Decision Tree
Design SMIDO-specific tree:
```
Root (M - Melding)
├── T - Technical check (vlog/manual search)
├── I - Installation familiar (query asset info)
└── D - Diagnosis branch
    ├── 3P - Power (electrical checks)
    ├── 3P - Procesinstellingen (parameter checks)
    ├── 3P - Procesparameters (compute worldstate)
    └── 3P - Productinput (environmental factors)
```

### 3. Custom Display Types
Add VSM-specific displays:
- Sensor graph with threshold overlays
- SMIDO decision flowchart
- Component diagram with status
- Timeline visualization
- Comparison view (current vs historical)

### 4. Collection Preprocessing
Preprocess VSM collections:
- `VSM_ManualSections`: SMIDO-aware sections
- `VSM_TelemetryEvent`: Historical incidents
- `VSM_VlogCase`: Video troubleshooting cases
- Metadata includes SMIDO tags, failure modes, components

### 5. Integration with Existing Data
Map Elysia concepts to VSM:
- Environment → WorldState features
- Tasks completed → SMIDO step progression
- Errors → Failed diagnostic attempts
- Feedback → Successful troubleshooting patterns

---

## Future Enhancements (Roadmap)

### Planned Features
1. **Custom theming**: Brand-matched UI
2. **Action-capable displays**: Interactive results (book, reply, add to cart)
3. **More display types**: Additional specialized formats
4. **Prompt optimization**: DSPy optimizer integration
5. **Advanced analytics**: Usage patterns, success metrics
6. **Multi-user collaboration**: Shared trees and feedback
7. **Plugin system**: Third-party tool integration

### Experimental Features
- Local model support (already configurable)
- Multi-lingual support
- Voice interaction
- Image/video analysis integration
- Real-time monitoring dashboards

---

## Troubleshooting

### Common Issues

**1. "No tools available to use!"**
- Cause: All tools have `is_tool_available()` returning False
- Solution: Check Weaviate connection, collection names, API keys

**2. "Model picked an action not in available tools"**
- Cause: Assertion failure in DecisionNode
- Solution: Check tool naming, review decision prompt, increase max_tries

**3. "Collection not preprocessed"**
- Cause: Metadata missing from ELYSIA_METADATA__
- Solution: Run `preprocess(collection_name)` first

**4. WebSocket connection failures**
- Cause: CORS issues, client timeout
- Solution: Check CORS settings, increase client_timeout

**5. Out of memory**
- Cause: Large trees, many collections
- Solution: Use `low_memory=True`, reduce collection count

---

## References

### Documentation
- GitHub: https://github.com/weaviate/elysia
- Docs: https://weaviate.github.io/elysia/
- Blog: https://weaviate.io/blog/elysia-agentic-rag
- Demo: https://elysia.weaviate.io

### Key Files
- `elysia/tree/tree.py`: Main Tree class
- `elysia/tree/objects.py`: TreeData, Environment, DecisionNode
- `elysia/tree/util.py`: Decision helpers, AssertedModule
- `elysia/objects.py`: Tool, Result, Return types
- `elysia/tools/retrieval/query.py`: Query tool
- `elysia/api/app.py`: FastAPI application
- `elysia/preprocessing/collection.py`: preprocess()
- `elysia/util/elysia_chain_of_thought.py`: DSPy integration

### Dependencies
- FastAPI: Web framework
- DSPy: LLM interaction framework
- Weaviate Python Client: Vector database
- AsyncIO: Asynchronous execution
- Next.js: Frontend (served as static)
- Rich: Terminal formatting
- Pydantic: Data validation

---

## Conclusion

Elysia represents a significant evolution in agentic RAG systems by combining:
1. Structured decision-making with full transparency
2. Dynamic data presentation beyond text
3. Comprehensive data awareness and analysis
4. Self-healing error handling
5. Personalized learning through feedback
6. On-demand optimization (chunking)
7. Multi-model intelligent routing

For the VSM project, Elysia provides an ideal foundation for building a SMIDO-aware troubleshooting assistant with:
- Transparent decision trees matching SMIDO methodology
- Integration with telemetry, manuals, and video data
- Dynamic display of sensor graphs, diagrams, and timelines
- Self-healing when diagnostic attempts fail
- Learning from successful troubleshooting patterns

The framework's extensibility through custom tools, branches, and display types makes it perfectly suited for domain-specific applications like VSM's freezer troubleshooting use case.

