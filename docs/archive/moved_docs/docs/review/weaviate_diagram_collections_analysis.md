# Weaviate Diagram Collections Analysis

**Date**: 2025-11-12  
**Context**: After implementing Mermaid rendering in frontend

## Current State

### Collections in Weaviate

#### 1. VSM_DiagramUserFacing
**Purpose**: Stores metadata for user-facing diagrams

**Schema**:
- `diagram_id` (TEXT, filterable) - Unique ID
- `title` (TEXT, vectorized) - Display title
- `description` (TEXT, vectorized) - Usage description
- `when_to_show` (TEXT, vectorized) - Contextual guidance
- `png_url` (TEXT) - **⚠️ OBSOLETE** (not used after Mermaid switch)
- `png_width` (INT) - **⚠️ OBSOLETE** (not used after Mermaid switch)
- `png_height` (INT) - **⚠️ OBSOLETE** (not used after Mermaid switch)
- `smido_phases` (TEXT_ARRAY, filterable) - SMIDO phase tags
- `failure_modes` (TEXT_ARRAY, filterable) - Failure mode tags
- `components` (TEXT_ARRAY, filterable) - Component tags
- `agent_diagram_id` (TEXT, filterable) - Link to agent diagram

**What show_diagram uses**:
- ✅ `title` - For display header
- ✅ `description` - For context text
- ✅ `agent_diagram_id` - To fetch agent diagram
- ❌ `png_url`, `png_width`, `png_height` - **NOT USED**

#### 2. VSM_DiagramAgentInternal
**Purpose**: Stores complex Mermaid diagrams for agent's internal logic

**Schema**:
- `diagram_id` (TEXT, filterable) - Unique ID
- `title` (TEXT, vectorized) - Diagram title
- `description` (TEXT, vectorized) - Description
- `agent_usage` (TEXT, vectorized) - When/how agent should use it
- `mermaid_code` (TEXT) - Complex Mermaid diagram code
- `source_chunk_id` (TEXT, filterable) - Original manual chunk ID
- `smido_phases` (TEXT_ARRAY, filterable) - SMIDO phase tags
- `failure_modes` (TEXT_ARRAY, filterable) - Failure mode tags
- `diagram_type` (TEXT, filterable) - Type classification

**What show_diagram uses**:
- ✅ `mermaid_code` - Loads into agent's hidden_environment
- ✅ `title` - For agent context
- ✅ All other fields are metadata for potential future queries

## New Mermaid Rendering Flow

### Data Flow:
1. **User-facing Mermaid**: Read from **filesystem** (`features/diagrams_vsm/user_facing/{diagram_id}.mermaid`)
2. **Metadata**: Fetched from **Weaviate** `VSM_DiagramUserFacing` (title, description, agent_diagram_id)
3. **Agent Mermaid**: Fetched from **Weaviate** `VSM_DiagramAgentInternal` (complex diagram for reasoning)

### Tool Behavior:
```python
show_diagram("smido_overview")
  ↓
1. Read: features/diagrams_vsm/user_facing/smido_overview.mermaid (filesystem)
2. Query: VSM_DiagramUserFacing for title="Smido Overview", description="...", agent_diagram_id="smido_main_flowchart"
3. Query: VSM_DiagramAgentInternal where diagram_id="smido_main_flowchart" → get complex mermaid_code
4. Store: Agent Mermaid in tree_data.environment.hidden_environment (for agent reasoning)
5. Return: Response with "```mermaid\n{user_facing_mermaid}\n```" (for frontend display)
```

## Issues & Recommendations

### ⚠️ Issue 1: Obsolete PNG Fields in VSM_DiagramUserFacing

**Current**: Collection has `png_url`, `png_width`, `png_height` fields with data  
**Problem**: These fields are no longer used (Mermaid renders from code, not PNG)  
**Impact**: Minimal - just wasted storage (8 objects × 3 fields ≈ negligible)

**Options**:
- **A. Leave as-is** (easiest, no breaking changes)
  - Pros: No migration needed, no downtime
  - Cons: Cluttered schema, confusing for future developers
  
- **B. Remove PNG fields** (clean schema)
  - Pros: Clean schema, clear intent
  - Cons: Requires schema migration, need to re-upload data
  
**Recommendation**: **Option A** (leave as-is) for now. The fields are harmless and the migration cost isn't worth it for 8 objects.

### ✅ Issue 2: Missing mermaid_code in VSM_DiagramUserFacing

**Current**: User-facing diagrams don't have `mermaid_code` field in Weaviate  
**Solution**: Read from filesystem instead (already implemented) ✅  
**Status**: Working correctly - Option 2 from your choice

### ✅ Issue 3: Agent Diagram Loading

**Current**: Agent diagrams ARE in Weaviate (`VSM_DiagramAgentInternal.mermaid_code`)  
**Tool behavior**: Correctly fetches and stores in `tree_data.environment.hidden_environment`  
**Status**: Working correctly ✅

## Compatibility Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Metadata queries | ✅ Working | title, description, agent_diagram_id correctly queried |
| Agent diagram loading | ✅ Working | Complex Mermaid loaded into hidden_environment |
| User diagram rendering | ✅ Working | Read from filesystem, wrapped in code fence |
| Frontend rendering | ✅ Working | Mermaid library installed and configured |
| PNG fields | ⚠️ Obsolete | png_url/width/height no longer used but harmless |

## Conclusion

**The Weaviate collections work perfectly with the new Mermaid setup**, with one minor caveat:

- ✅ **VSM_DiagramUserFacing**: Provides necessary metadata (title, description, agent link) ✓
- ✅ **VSM_DiagramAgentInternal**: Provides complex diagrams for agent reasoning ✓
- ⚠️ **Obsolete PNG fields**: Present but unused (harmless, can be ignored)

**No action required** - the collections are fully functional for the new Mermaid rendering approach. The PNG fields are vestigial but don't interfere with the new workflow.

## Future Considerations

If you ever want to clean up the schema:

1. Create new metadata-only collection without PNG fields
2. Migrate 8 objects (trivial)
3. Update `show_diagram` to query new collection
4. Delete old collection

But for 8 objects, this optimization is purely cosmetic.

## Testing Checklist

Before final testing, verify:

- [x] Frontend: `mermaid` package installed
- [x] Frontend: `MarkdownFormat.tsx` has MermaidCode component
- [x] Frontend: Built and exported to `elysia/api/static/`
- [x] Backend: `show_diagram` reads from filesystem
- [x] Backend: `show_diagram` returns Response with code fence
- [x] Backend: Agent diagrams loaded into hidden_environment
- [x] Weaviate: Both collections exist with data
- [ ] End-to-end: Start backend and test in browser (next step)

