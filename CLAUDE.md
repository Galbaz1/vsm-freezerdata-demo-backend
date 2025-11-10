# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Elysia** is an open-source agentic RAG platform built on Weaviate. It uses a decision tree architecture where LLM-powered agents dynamically select and execute tools based on context. Unlike traditional ReAct/function-calling agents, Elysia pre-defines a tree structure where the LLM only decides which branch to take at each node, providing predictable execution paths and easier debugging.

## Development Setup

### Python Environment

This project requires Python 3.11-3.12. Use conda or venv:

```bash
# Using conda (recommended)
conda create -n vsm-hva python=3.12
conda activate vsm-hva

# Install for development
pip install -e ".[dev]"
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required for local development:**
- `WCD_URL` / `WCD_API_KEY`: Weaviate Cloud cluster credentials
- OR `WEAVIATE_IS_LOCAL=True`: Connect to localhost:8080/50051
- Model provider API key (e.g., `OPENROUTER_API_KEY`, `OPENAI_API_KEY`)
- `BASE_MODEL` / `COMPLEX_MODEL`: Model identifiers
- `BASE_PROVIDER` / `COMPLEX_PROVIDER`: Provider names (e.g., `openrouter/google`)

**Optional:**
- Vectorizer API keys (match your Weaviate collection vectorizers)
- Custom Weaviate connection via `WEAVIATE_IS_CUSTOM`, `CUSTOM_HTTP_HOST`, etc.

### Running the Application

```bash
# Start FastAPI backend (serves both API and Next.js frontend)
elysia start

# Specify port
elysia start --port 8080

# CLI usage (Python API)
python -c "from elysia import Tree; tree = Tree(); tree('Your query here')"
```

## Testing

Tests are split into two categories:

### 1. No Requirements Tests (`tests/no_reqs/`)

Tests that don't require API keys or external services. **These must pass for all contributions.**

```bash
# Run all no_reqs tests
pytest tests/no_reqs/ -v

# Run all no_reqs tests with coverage report
pytest tests/no_reqs/ --cov=elysia --cov-report=html --cov-report=term

# Run specific test file
pytest tests/no_reqs/general/test_tree_nr.py -v

# Run specific test function
pytest tests/no_reqs/general/test_tree_nr.py::test_function_name -v

# Run tests matching a pattern
pytest tests/no_reqs/ -k "test_tree" -v

# Show test output in real-time
pytest tests/no_reqs/ -v -s
```

Coverage reports are generated in `htmlcov/index.html`.

### 2. Environment-Required Tests (`tests/requires_env/`)

Tests that require Weaviate cluster + LLM API keys. **These will cost credits to run.** Not required for contributions - the Elysia team will run these.

```bash
# Run env tests (requires WCD_URL, WCD_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY)
pytest tests/requires_env/ -v
```

### CI/CD

GitHub Actions runs `pytest --ignore=tests/requires_env` on PRs to main/dev/release branches.

## Architecture

### Core Components

1. **Tree (`elysia/tree/tree.py`)**: Central orchestrator, entry point, manages execution flow
2. **DecisionNode (`elysia/tree/util.py`)**: Individual decision points with options/branches
3. **Tool (`elysia/objects.py`)**: Base class for all actions (query, aggregate, visualize, etc.)
4. **Environment (`elysia/tree/objects.py`)**: Shared context/memory across all decisions
5. **TreeData (`elysia/tree/objects.py`)**: Container passed to tools (environment, collections, settings, history)
6. **Settings (`elysia/config.py`)**: Manages models, API keys, Weaviate connection
7. **ClientManager (`elysia/util/client.py`)**: Thread-safe Weaviate connection pooling

### Tree Execution Flow

```
User Query → FastAPI WebSocket → UserManager → TreeManager → Tree
    ↓
Tree.async_run():
  1. Load Settings (models, API keys via ElysiaKeyManager)
  2. Initialize TreeData (environment, collections metadata, conversation history)
  3. Loop through DecisionNodes:
     a. Filter available vs unavailable tools (via is_tool_available())
     b. Build prompt with environment context + available actions
     c. LLM decision (via DSPy) → Decision object
     d. Execute Tool.__call__() (async generator):
        - Yield Status/Update objects
        - Query Weaviate via ClientManager
        - Process results
        - Yield Result/Error objects
     e. Update Environment with results
     f. Check completion criteria
  4. Recursively restart if goal not achieved (up to recursion_limit)
  5. Stream all yields to WebSocket → Frontend
```

### Tree Initialization Modes

- `one_branch`: Single decision layer, all tools at root (default)
- `multi_branch`: Hierarchical structure with base→search branching
- `empty`: Start with no tools, build custom tree
- `default`: Alias for one_branch

### Tool System

**Built-in Tools:**
- `Query`: Semantic/keyword/hybrid search with filters (`elysia/tools/retrieval/query.py`)
- `Aggregate`: GroupBy operations, statistics (`elysia/tools/retrieval/aggregate.py`)
- `Visualise`: Chart generation (`elysia/tools/visualisation/visualise.py`)
- `CitedSummarizer`: Text responses with citations (`elysia/tools/text/text.py`)

**Creating Custom Tools:**

Via decorator:
```python
from elysia import tool, Tree

tree = Tree()

@tool(tree=tree)
async def my_tool(x: int, y: int) -> int:
    """Tool description shown to LLM"""
    return x + y
```

Via subclass:
```python
from elysia.objects import Tool, Result

class MyTool(Tool):
    def __init__(self, param: str):
        self.param = param

    async def __call__(self, tree_data, x: int):
        # Yield Status/Update/Result/Error objects
        yield Result(objects=[{"result": x + 1}])

    def is_tool_available(self, tree_data):
        return True  # Or conditional logic

tree.add_tool(MyTool, branch_id="base")
```

### Preprocessing Collections

Weaviate collections must be preprocessed before use:

```python
from elysia.preprocessing.collection import preprocess

# Analyze collection structure, generate metadata
preprocess(collection_names=["YourCollection"])

# Stored in ELYSIA_METADATA__ collection
```

This generates:
- Field descriptions, types, ranges, categorical groups
- Collection summary (LLM-generated)
- Return type mappings (how to display data in frontend)
- Suggested prompts

### Multi-Tenant Architecture

- `UserManager`: Manages multiple users, each with a `TreeManager`
- `TreeManager`: Manages multiple conversations (Trees) per user
- `ClientManager`: Thread-safe Weaviate connections with auto-restart
- `ElysiaKeyManager`: Context manager for isolated API keys per Tree

### Key Design Patterns

1. **Decision Tree as Control Flow**: Pre-defined tree structure, LLM selects branch (not arbitrary tool calling)
2. **Environment as Shared Context**: All tools write to shared Environment, visible to subsequent decisions
3. **Self-Healing with Assertions**: `AssertedModule` wraps decisions to retry on invalid outputs
4. **Async Generators for Streaming**: Tools yield incrementally, enabling real-time WebSocket updates
5. **Lazy Loading**: Models loaded per-call (`low_memory=True`) or cached (`low_memory=False`)
6. **Metaclass-Based Tool Registration**: AST parsing extracts metadata from `__init__` methods

## Directory Structure

```
elysia/
├── tree/           # Core tree logic, decision nodes, execution flow
├── tools/          # Built-in tools (retrieval, text, visualization, postprocessing)
├── api/            # FastAPI app, routes, services, dependencies, middleware
│   ├── services/   # UserManager, TreeManager, session management
│   ├── routes/     # WebSocket endpoints, REST routes
│   └── app.py      # Main FastAPI application
├── preprocessing/  # Collection analysis, metadata generation
├── util/           # ClientManager, parsing, async utilities
├── objects.py      # Base classes: Tool, Return, Result, Status, Error, Update
└── config.py       # Settings, model loading, ElysiaKeyManager

tests/
├── no_reqs/        # Tests with no external dependencies (must pass)
└── requires_env/   # Tests requiring API keys + Weaviate (optional)

features/
├── extraction/     # Standalone PDF processing pipeline (LandingAI ADE)
│   ├── src/       # process_pdfs.py - main extraction script
│   ├── source_files/  # Input PDFs
│   └── production_output/  # Processed artifacts
└── telemetry/      # Telemetry features
```

## Common Tasks

### Running Specific Tests
```bash
# All no_reqs tests (fastest, free)
pytest tests/no_reqs/ -v

# With coverage
pytest tests/no_reqs/ --cov=elysia --cov-report=html --cov-report=term

# Specific test file
pytest tests/no_reqs/general/test_tree_nr.py -v

# Specific test function
pytest tests/no_reqs/general/test_tree_nr.py::test_function_name -v

# Run tests matching a pattern
pytest tests/no_reqs/ -k "test_tree" -v

# API-specific tests
pytest tests/no_reqs/api/ -v

# Show test output in real-time
pytest tests/no_reqs/ -v -s
```

### Adding a New Tool

1. Create tool file in `elysia/tools/` (or custom location)
2. Subclass `Tool` or use `@tool` decorator
3. Implement `async def __call__(self, tree_data, **kwargs)` as async generator
4. Optionally implement `is_tool_available()` and `get_default_inputs()`
5. Register: `tree.add_tool(MyTool, branch_id="base")`
6. Add tests in `tests/no_reqs/general/test_tools_nr.py`

### Modifying Decision Node Logic

Edit `elysia/tree/util.py:DecisionNode.decide()`:
- Modify prompt construction
- Change decision selection logic
- Adjust self-healing behavior (AssertedModule)

### Changing Model Configuration

Edit `elysia/config.py`:
- Modify `Settings._load_models()` for DSPy model loading
- Update `ElysiaKeyManager` for new API providers
- Adjust `smart_setup()` for auto-configuration logic

### Adding API Endpoints

1. Create route file in `elysia/api/routes/`
2. Register in `elysia/api/app.py`
3. Add dependency injection via `elysia/api/dependencies.py`
4. Add tests in `tests/no_reqs/api/`

## PDF Processing Pipeline (features/extraction/)

A standalone pipeline for extracting structured data from technical PDFs, separate from the main Elysia package. This pipeline uses LandingAI's Advanced Document Extraction (ADE) API.

### Setup

```bash
cd features/extraction
pip install -r requirements.txt
export VISION_AGENT_API_KEY='your-landingai-key'
```

### Usage

```bash
# Process PDF (auto-batches if >45MB or >45 pages)
python src/process_pdfs.py source_files/manual.pdf

# Test mode (first 20 pages only)
python src/process_pdfs.py --pages 20 source_files/manual.pdf

# Custom output directory
python src/process_pdfs.py --output-dir my_outputs source_files/manual.pdf

# High-DPI assets
python src/process_pdfs.py --asset-dpi 300 source_files/manual.pdf
```

### Features

- **Intelligent batching**: Automatically splits large PDFs into 20-page batches
- **Global page numbering**: Seamless page tracking across batches
- **Multi-language support**: Detects NL and EN content
- **Visual asset extraction**: Crops figures with bounding boxes
- **Page-level artifacts**: Context Engineering-ready page records
- **Table text summaries**: Compact text from HTML tables for embeddings
- **Quality assurance**: Automatic QA checks and warnings
- **Full traceability**: Batch artifacts preserved for debugging

### Output Files

The pipeline generates several artifacts in `production_output/{document}/`:

- `*.text_chunks.jsonl` - Text and table chunks with metadata, language detection
- `*.visual_chunks.jsonl` - Figure chunks with asset paths and descriptions
- `*.pages.jsonl` - Page-level aggregation with all chunk IDs
- `*.meta.json` - Document metadata including batch info
- `*.qa.json` - Quality assurance summary with warnings
- `*.parsed.json` - Merged ADE API responses
- `*.parsed.md` - Full document markdown
- `.batches/` - Intermediate batch artifacts for debugging

These artifacts are designed to be imported into Weaviate collections for retrieval.

## Importing Custom Data

For users needing to import their own data into Weaviate (outside of preprocessing existing collections), see [docs/adding_data.md](docs/adding_data.md). This provides a guided workflow for:

- Setting up Weaviate Cloud connection
- Choosing embedding providers (text2vec-weaviate, OpenAI, Cohere, etc.)
- Creating custom import scripts with proper schema
- Defining collection properties and vectorization settings

**Note**: This is separate from the `preprocess()` function which analyzes existing collections. Use this workflow when you need to bring new data sources into Weaviate.

## Branch Strategy (from CONTRIBUTING.md)

- **main**: Active development, new features
- **dev**: Experimental features
- **release/vX.Y.x**: Bug fixes for specific versions

**PR Guidelines:**
- New features → `main` (prefix: `feature/`)
- Bug fixes → current `release/` branch (prefix: `bugfix/`)
- Urgent fixes → case-by-case (prefix: `hotfix/`)
- Docs → relevant branch (prefix: `docs/`)
- Small changes → `chore/`

**Code Formatting:**
- Uses `black` for Python formatting

## Debugging Tips

### Tree Execution
```python
tree = Tree(debug=True)  # Enables verbose logging
response = tree("Your query", return_mode="full")  # Returns complete execution trace
```

### Client Connection Issues
- Check `WCD_URL` / `WCD_API_KEY` in `.env`
- Verify vectorizer API keys match collection vectorizer (e.g., `OPENAI_API_KEY` for OpenAI vectorizer)
- Test connection: `python -c "from elysia.util.client import ClientManager; ClientManager().connect_to_client()"`

### LLM Errors
- Ensure model exists at provider (e.g., `openrouter/google/gemini-2.0-flash-001`)
- Check API key is valid and has credits
- Try simpler model (e.g., `gpt-4o-mini`) for debugging
- Review `tree_data.errors` for tool-specific errors

### Preprocessing Failures
- Collections must exist in Weaviate before preprocessing
- Ensure enough data (recommend 10+ objects for accurate analysis)
- Check `ELYSIA_METADATA__` collection for stored metadata
- Use `view_preprocessed_collection(collection_name)` to inspect

## Important Notes

- **Tests in `requires_env/` are expensive**: Running full LLM tests will cost credits
- **Collections need preprocessing**: Call `preprocess()` before querying
- **Multi-tenant design**: Each user/conversation is isolated (settings, environment, API keys)
- **Async by design**: Use async/await patterns throughout
- **Streaming results**: Tools should yield incrementally for responsive UX
- **DSPy for LLM calls**: Structured outputs, chain-of-thought, few-shot learning built-in
- **Development artifacts**: Directories like `docs/eda/` and `features/` may contain experimental work or standalone pipelines not part of the main Elysia package
