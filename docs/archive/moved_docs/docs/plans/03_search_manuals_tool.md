# Plan 3: SearchManualsBySMIDO Tool (with Diagram Integration)

**Priority**: HIGH (Core tool for all SMIDO phases)  
**Parallelization**: Can run independently  
**Estimated Time**: 2 hours

---

## Objective

Implement SearchManualsBySMIDO tool that queries VSM_ManualSections and VSM_Diagram collections with SMIDO-aware filtering. Returns both text sections AND visual diagrams, with ability to filter out test content (opgave).

---

## Context Files Required

**Architecture**:
- `docs/diagrams/VSM_AGENT_ARCHITECTURE_MOTIVATION.md` (lines 182-186 - Tool definition)
- `CLAUDE.md` (lines 316-319 - Data strategy by tool need)

**Weaviate Collections**:
- `docs/data/manuals_weaviate_design.md` (VSM_ManualSections schema, controlled vocabularies)
- `docs/data/DATA_UPLOAD_STRATEGY.md` (VSM_Diagram schema, lines 283-308)

**Diagram Integration**:
- `docs/diagrams/DIAGRAM_CATALOG.md` (all 9 diagrams with usage guidance)
- `docs/diagrams/DIAGRAMS_FOR_AGENT.md` (agent integration patterns)

**Test Content Filtering**:
- `todo.md` (lines 116-144 - opgave filtering requirements)
- `docs/data/WEAVIATE_API_NOTES.md` (filtering examples)

**Elysia Patterns**:
- `elysia/tools/retrieval/query.py` (Query tool reference)

---

## Implementation Tasks

### Task 3.1: Implement SearchManualsBySMIDO Tool

**File**: `elysia/api/custom_tools.py`

**Implementation Spec**:

```python
@tool(status="Searching SMIDO manuals and diagrams...", branch_id="smido_installatie")
async def search_manuals_by_smido(
    query: str,
    smido_step: str = None,  # melding, technisch, power, procesinstellingen, procesparameters, productinput, ketens_onderdelen
    failure_mode: str = None,
    component: str = None,
    include_diagrams: bool = True,
    include_test_content: bool = False,  # Filter opgave by default
    limit: int = 5,
    tree_data=None,
    client_manager=None,
    **kwargs
):
    """
    Search manual sections filtered by SMIDO step, with optional diagram inclusion.
    
    Returns:
    - Manual sections (text)
    - Related diagrams (Mermaid code) if include_diagrams=True
    
    Automatically filters out test content (opgave) unless include_test_content=True.
    
    Used in: I (Installatie), P2 (Procesinstellingen), O (Onderdelen) nodes
    """
    yield Status("Searching manual sections...")
    
    # Build filters
    filters = []
    
    # SMIDO step filter
    if smido_step:
        filters.append(Filter.by_property("smido_step").equal(smido_step))
    
    # Failure mode filter
    if failure_mode:
        filters.append(Filter.by_property("failure_modes").contains_any([failure_mode]))
    
    # Component filter
    if component:
        filters.append(Filter.by_property("components").contains_any([component]))
    
    # Filter out test content (opgave) by default
    if not include_test_content:
        filters.append(Filter.by_property("content_type").not_equal("opgave"))
    
    # Combine filters
    combined_filter = filters[0]
    for f in filters[1:]:
        combined_filter = combined_filter & f
    
    # Query VSM_ManualSections
    async with client_manager.connect_to_async_client() as client:
        collection = client.collections.get("VSM_ManualSections")
        
        if query:
            # Hybrid search
            results = await collection.query.hybrid(
                query=query,
                filters=combined_filter,
                limit=limit
            )
        else:
            # Filter-only
            results = await collection.query.fetch_objects(
                filters=combined_filter,
                limit=limit
            )
    
    yield Status(f"Found {len(results.objects)} manual sections")
    
    # Get related diagrams if requested
    diagram_objects = []
    if include_diagrams:
        yield Status("Fetching related diagrams...")
        
        # Get diagram IDs from sections
        diagram_ids = []
        for obj in results.objects:
            diagram_ids.extend(obj.properties.get("related_diagram_ids", []))
        
        if diagram_ids:
            diagram_coll = client.collections.get("VSM_Diagram")
            for diagram_id in set(diagram_ids):
                diagram_result = await diagram_coll.query.fetch_objects(
                    filters=Filter.by_property("diagram_id").equal(diagram_id),
                    limit=1
                )
                if diagram_result.objects:
                    diagram_objects.extend(diagram_result.objects)
    
    # Yield results
    yield Result(
        objects=results.objects,
        metadata={
            "diagrams": diagram_objects,
            "smido_step": smido_step,
            "test_content_included": include_test_content,
            "diagram_count": len(diagram_objects)
        }
    )
```

---

### Task 3.2: Diagram Display Enhancement

**File**: Update Elysia frontend to display Mermaid diagrams (if needed)

**Note**: Check if Elysia frontend already supports Mermaid rendering. If not, this is a Phase 5 task.

---

## Verification

**Success Criteria**:
- [ ] Tool queries VSM_ManualSections with SMIDO filtering
- [ ] Test content (opgave) filtered out by default
- [ ] Related diagrams retrieved and returned
- [ ] Query for "frozen evaporator" + smido_step="procesparameters" returns relevant sections
- [ ] Query for "pressostaat" returns pressostat adjustment diagram

**Test Queries**:
```python
# Test 1: P3 query with diagram
search_manuals_by_smido(
    query="Hoe meet ik zuigdruk?",
    smido_step="procesparameters",
    include_diagrams=True
)
# Should return: instrumentation diagram

# Test 2: Opgave filtering
search_manuals_by_smido(
    query="opgave",
    include_test_content=False
)
# Should return: 0 results

# Test 3: A3 frozen evaporator
search_manuals_by_smido(
    query="ingevroren verdamper",
    failure_mode="ingevroren_verdamper",
    include_diagrams=True
)
# Should return: frozen evaporator section + diagram
```

---

## Dependencies

**Required Before**:
- ✅ VSM_ManualSections uploaded
- ✅ VSM_Diagram uploaded
- ✅ Elysia preprocessing complete

**Blocks**:
- I (Installatie) node implementation
- P2 (Procesinstellingen) node implementation
- O (Onderdelen) node implementation

---

## Related Files

**To Modify**:
- `elysia/api/custom_tools.py` (add SearchManualsBySMIDO tool)

**To Reference**:
- `features/manuals_vsm/output/manual_sections_classified.jsonl` (test data)
- `features/diagrams_vsm/output/diagrams_metadata.jsonl` (test data)
- `docs/diagrams/DIAGRAM_CATALOG.md` (diagram usage guidance)


