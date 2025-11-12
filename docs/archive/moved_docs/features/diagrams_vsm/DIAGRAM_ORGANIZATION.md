# VSM Diagram Organization

**Date**: 2025-01-11  
**Purpose**: Clarify which diagrams are for users vs agent internal use

---

## Folder Structure

```
features/diagrams_vsm/
│
├── user_facing/               ← Simple diagrams shown to technicians
│   ├── smido_overview.mermaid      (8 nodes, LR layout)
│   ├── basic_cycle.mermaid         (4 nodes, circular)
│   └── README.md
│
├── agent_internal/            ← Complex diagrams for agent logic
│   ├── smido_main_flowchart.mermaid       (30+ nodes, TD)
│   ├── smido_3ps_diagnosis.mermaid        (20+ nodes, TD)
│   ├── smido_frozen_evaporator_example.mermaid (15+ nodes, TD)
│   ├── balance_diagram.mermaid            (15+ nodes, graph)
│   ├── pressostat_adjustment_logic.mermaid (12+ nodes, TD)
│   ├── schematic_with_instrumentation.mermaid (12+ nodes, TD)
│   ├── troubleshooting_table_flow.mermaid (8 nodes, LR)
│   ├── basic_refrigeration_cycle.mermaid  (10+ nodes, graph)
│   ├── smido_data_integration.mermaid     (15+ nodes, TD)
│   └── README.md
│
├── vsm_diagrams_only/         ← DEPRECATED (being replaced)
│   └── [old diagrams - to be removed]
│
├── output/                    ← Generated metadata for Weaviate
│   └── diagrams_metadata.jsonl
│
├── USER_FACING_DIAGRAM_STANDARDS.md  ← Standards document
└── DIAGRAM_ORGANIZATION.md            ← This file
```

---

## Key Principles

### User-Facing Diagrams

**Characteristics**:
- ✅ Landscape (LR) or square layout
- ✅ 8-15 nodes maximum
- ✅ Simple, clean, professional
- ✅ One clear message
- ✅ Quick to understand (5-10 seconds)

**When to show**:
- "What is SMIDO?" → `smido_overview.mermaid`
- "How does the system work?" → `basic_cycle.mermaid`
- "I don't understand" → User-facing diagrams

**NOT shown to users**:
- Complex decision trees
- Detailed workflows
- Technical architecture diagrams

### Agent-Internal Diagrams

**Characteristics**:
- ✅ Can be complex (30+ nodes)
- ✅ Can use TD (Top-Down) layout
- ✅ Detailed decision logic
- ✅ Complete workflows
- ✅ Technical details

**Agent uses for**:
- Building decision tree structure
- Parsing into graph for logic
- Understanding complete SMIDO workflow
- Knowing all decision points
- Generating responses

**NOT shown to users**:
- Too complex
- Overwhelming
- Not optimized for screen display

---

## Migration Plan

### Phase 1: Create User-Facing (DONE)
- ✅ Created `user_facing/` folder
- ✅ Created `smido_overview.mermaid` (simple, LR, 8 nodes)
- ✅ Created `basic_cycle.mermaid` (simple, circular, 4 nodes)
- ✅ Created standards document

### Phase 2: Organize Agent-Internal (DONE)
- ✅ Created `agent_internal/` folder
- ✅ Copied existing complex diagrams
- ✅ Documented purpose of each

### Phase 3: Update Agent Logic (TODO)
- [ ] Update `SearchManualsBySMIDO` tool to distinguish user vs agent diagrams
- [ ] Add `diagram_type` field to Weaviate metadata (`user_facing` vs `agent_internal`)
- [ ] Update agent prompts to show user-facing diagrams
- [ ] Keep agent-internal diagrams for decision logic only

### Phase 4: Update Weaviate (TODO)
- [ ] Re-upload diagrams with correct `diagram_type` metadata
- [ ] Update queries to filter by `diagram_type`
- [ ] Ensure frontend only receives `user_facing` diagrams

### Phase 5: Cleanup (TODO)
- [ ] Remove `vsm_diagrams_only/` folder
- [ ] Update all documentation references
- [ ] Verify all diagrams are in correct folders

---

## Agent Usage Pattern

```python
# Agent loads internal diagram for logic
internal = load_diagram("agent_internal/smido_main_flowchart.mermaid")
decision_tree = parse_to_tree(internal)

# But shows simple diagram to user
user_diagram = get_diagram("user_facing/smido_overview.mermaid")
show_to_technician(user_diagram)
```

---

## Weaviate Metadata

### User-Facing Diagrams

```json
{
  "diagram_id": "smido_overview",
  "diagram_type": "user_facing",
  "title": "SMIDO Overview",
  "layout": "LR",
  "complexity": "simple",
  "node_count": 8,
  "when_to_show": "What is SMIDO? / Overview request",
  "mermaid_code": "..."
}
```

### Agent-Internal Diagrams

```json
{
  "diagram_id": "smido_main_flowchart",
  "diagram_type": "agent_internal",
  "title": "SMIDO Main Flowchart - Complete",
  "layout": "TD",
  "complexity": "complex",
  "node_count": 30,
  "agent_usage": "PRIMARY decision tree structure",
  "mermaid_code": "..."
}
```

---

**Status**: Phase 1 & 2 complete, Phases 3-5 TODO

