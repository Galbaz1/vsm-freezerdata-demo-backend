# Elysia Framework Architecture Documentation

This folder contains comprehensive low-level diagrams documenting the Elysia agentic RAG framework as cloned from the official Weaviate repository.

## Overview

Elysia is a decision tree-based agentic RAG framework that intelligently decides what tools to use, evaluates results, and determines whether to continue processing or complete. It features:

- **Three Pillars**:
  1. Customizable decision-tree architecture
  2. Dynamic data display types
  3. AI data analysis and awareness

- **Core Technologies**:
  - FastAPI backend with Next.js frontend (served as static HTML)
  - DSPy for LLM interactions
  - Weaviate for vector storage and RAG
  - Pure Python core logic ("blood, sweat, and tears" custom logic)

## Documentation Structure

### 1. High-Level Architecture
- `01_system_overview.mermaid` - Overall system architecture
- `02_three_pillars.mermaid` - Core pillars: decision trees, dynamic display, data awareness

### 2. Decision Tree Architecture
- `03_decision_tree_structure.mermaid` - Tree, nodes, and branches
- `04_decision_node_execution.mermaid` - How decisions are made at each node
- `05_tree_lifecycle.mermaid` - Tree initialization to completion
- `06_recursion_and_loops.mermaid` - Recursion handling and loop prevention

### 3. Core Components
- `07_tree_class.mermaid` - Main Tree class structure
- `08_tree_data_objects.mermaid` - TreeData, Environment, Atlas, CollectionData
- `09_decision_node_class.mermaid` - DecisionNode internals
- `10_tool_system.mermaid` - Tool architecture and lifecycle

### 4. Tool System
- `11_tool_execution_flow.mermaid` - Tool call workflow
- `12_query_tool_detail.mermaid` - Query tool (main retrieval tool)
- `13_aggregate_tool.mermaid` - Aggregation tool
- `14_text_response_tools.mermaid` - Text generation tools

### 5. LLM Integration
- `15_dspy_integration.mermaid` - DSPy module usage
- `16_elysia_chain_of_thought.mermaid` - Custom CoT implementation
- `17_model_strategy.mermaid` - Multi-model routing (base vs complex)
- `18_feedback_system.mermaid` - Few-shot learning and feedback loop

### 6. Data Management
- `19_environment_storage.mermaid` - Environment object structure
- `20_collection_preprocessing.mermaid` - Collection analysis and metadata
- `21_result_objects.mermaid` - Result, Retrieval, Text, Update types
- `22_frontend_payloads.mermaid` - Frontend return format

### 7. Advanced Features
- `23_chunk_on_demand.mermaid` - Dynamic document chunking
- `24_error_handling.mermaid` - Self-healing error system
- `25_training_updates.mermaid` - Training data collection
- `26_conversation_management.mermaid` - History and state

### 8. API and Backend
- `27_fastapi_structure.mermaid` - FastAPI routes and middleware
- `28_websocket_streaming.mermaid` - SSE/WebSocket for real-time updates
- `29_user_manager.mermaid` - User and tree management
- `30_client_manager.mermaid` - Weaviate client handling

### 9. Detailed Flows
- `31_query_execution_flow.mermaid` - Complete query flow
- `32_decision_making_flow.mermaid` - Decision agent workflow
- `33_tree_run_sequence.mermaid` - Full tree.run() sequence
- `34_async_generator_pattern.mermaid` - Async/yield pattern

### 10. Integration Points
- `35_weaviate_integration.mermaid` - How Elysia uses Weaviate
- `36_preprocessing_pipeline.mermaid` - Collection preprocessing workflow
- `37_display_type_system.mermaid` - Dynamic display selection
- `38_assertion_feedback_loop.mermaid` - AssertedModule and validation

## Key Concepts

### Decision Tree Architecture
Unlike simple agentic platforms where all tools are available at runtime, Elysia uses a pre-defined web of decision nodes. Each node is orchestrated by a decision agent with global context awareness.

### Dynamic Display Types
Elysia can dynamically choose how to display data (table, product card, document, chart, etc.) based on what makes the most sense for the content and context.

### Data Awareness
Elysia analyzes your Weaviate collections to understand data structure, create summaries, generate metadata, and choose display types - giving it full contextual awareness of your data.

### Error Handling & Self-Healing
Errors are caught and propagated back through the decision tree. The decision agent can make intelligent choices about whether to retry with corrections or try a different approach.

### Feedback System
Each user maintains their own set of feedback examples stored in Weaviate. Elysia uses few-shot learning to improve responses over time.

### Chunk-On-Demand
Instead of pre-chunking all documents, Elysia chunks at query time when documents exceed a token threshold and prove relevant to the query.

## References

- **Blog Post**: https://weaviate.io/blog/elysia-agentic-rag
- **GitHub**: https://github.com/weaviate/elysia
- **Demo**: https://elysia.weaviate.io

## File Naming Convention

Files are numbered sequentially (01-38) to indicate suggested reading order. Each file is self-contained but may reference other diagrams.

**Last Updated**: November 11, 2025

