<!-- ca71edda-5954-48e4-8847-390f58d462a4 05f113af-8746-4ec4-9353-8b78a2c172ff -->
# Image Gallery UX + Diagram Fixes

## Overview

Improve manual images UX and fix all diagram display issues to enable complete visual troubleshooting support.

## Part A: Image Gallery UX Improvements

### Issue Analysis (from screenshot)

**Current state**:

- ✅ Images display correctly in 2-column grid
- ✅ Component tags (blue) and manual name visible
- ❌ Description text too long (multiple lines, gray hard to read)
- ❌ Shows 5 images, user wants max 2 by default
- ✅ Dropdown/expand for more exists (need to verify)

### A1: Limit Default Images to 2

**File**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) line ~1213

Change default `limit` parameter:

```python
async def search_manual_images(
    query: str = "",
    smido_step: str = None,
    component: str = None,
    limit: int = 2,  # Was: 5, now: 2
    ...
)
```

### A2: Improve Image Descriptions (Relevant + Readable)

**File**: [`elysia-frontend-main/app/components/chat/displays/Image/ImageGalleryDisplay.tsx`](elysia-frontend-main/app/components/chat/displays/Image/ImageGalleryDisplay.tsx) lines ~46-49

**Current**:

```tsx
<p className="text-sm text-foreground">
  {img.image_description}
</p>
```

**Issues**:

- Full vision model description (can be 100+ chars)
- Low contrast (`text-foreground` = gray)
- Not contextualized to user query

**Fix**:

```tsx
<p className="text-sm text-primary font-medium line-clamp-1">
  {img.component_tags.join(", ") || "Component photo"}
</p>
```

**Alternative** (if want to keep description):

- Truncate to 60 chars
- Better contrast: `text-primary` instead of `text-foreground`
- Line clamp: `line-clamp-1` or `line-clamp-2`

## Part B: Diagram Fixes (All 4 Issues)

### B1: Update show_diagram - Handle PNG and Mermaid

**File**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 1313-1340

**Current** (line 1320-1331):

````python
mermaid_code = props.get("mermaid_code", "")
if mermaid_code:
    markdown = f"**{title}**\n\n```mermaid\n{mermaid_code}\n```"
    yield Response(markdown)
````

**Fix**:

````python
# Check for PNG first (UserFacing diagrams)
png_url = props.get("png_url")
if png_url:
    # Build full URL
    full_url = f"http://localhost:8000{png_url}"
    # Return as markdown image
    markdown = f"**📊 {title}**\n\n"
    if description:
        markdown += f"*{description}*\n\n"
    markdown += f"![{title}]({full_url})"
    yield Response(markdown)

# Fallback to Mermaid (AgentInternal diagrams)
elif mermaid_code:
    markdown = f"**📊 {title}**\n\n"
    if description:
        markdown += f"*{description}*\n\n"
    markdown += f"```mermaid\n{mermaid_code}\n```"
    yield Response(markdown)
else:
    yield Error(f"Diagram '{title}' has neither PNG nor Mermaid code")
````

### B2: Register show_diagram in Bootstrap

**File**: [`features/vsm_tree/bootstrap.py`](features/vsm_tree/bootstrap.py)

**Line ~130**: Add import

```python
from elysia.api.custom_tools import (
    ...
    search_manual_images,
    show_diagram  # ADD THIS
)
```

**Line ~151**: Add to root tools

```python
tree.add_tool(branch_id="base", tool=show_diagram)
```

**Line ~190**: Add to SMIDO chains (optional - after search_manuals)

```python
# I/T flow: After search_manuals completes → offer visual diagrams
tree.add_tool(show_diagram, branch_id="base", from_tool_ids=["search_manuals_by_smido"])
```

### B3: Update search_manuals_by_smido Diagram Output

**File**: [`elysia/api/custom_tools.py`](elysia/api/custom_tools.py) lines 244-259

**Current**:

```python
if diagram_dicts:
    for diagram in diagram_dicts:
        mermaid_code = diagram.get("mermaid_code", "")
        if mermaid_code:
            yield Response(markdown)
```

**Fix** (same dual handling as show_diagram):

````python
if diagram_dicts:
    for diagram in diagram_dicts:
        title = diagram.get("title", "Diagram")
        description = diagram.get("description", "")
        png_url = diagram.get("png_url")
        mermaid_code = diagram.get("mermaid_code", "")
        
        if png_url:
            # UserFacing - PNG image
            full_url = f"http://localhost:8000{png_url}"
            markdown = f"\n\n**📊 {title}**\n\n"
            if description:
                markdown += f"*{description}*\n\n"
            markdown += f"![{title}]({full_url})\n"
            yield Response(markdown)
        elif mermaid_code:
            # AgentInternal - Mermaid
            markdown = f"\n\n**📊 {title}**\n\n"
            if description:
                markdown += f"*{description}*\n\n"
            markdown += f"```mermaid\n{mermaid_code}\n```\n"
            yield Response(markdown)
````

### B4: Populate UserFacing smido_phases

**Goal**: Make UserFacing diagrams findable by SMIDO fallback search

**Approach**: Update Weaviate objects with phase tags based on `when_to_show` field

**Script**: Create `scripts/tag_user_facing_diagrams.py`

```python
import asyncio
from elysia.util.client import ClientManager
from weaviate.classes.query import Filter

# Mapping based on when_to_show → smido_phases
PHASE_MAPPINGS = {
    "smido_overview": ["M"],  # Overview = Melding phase
    "troubleshooting_template": ["M", "T"],  # Early phases
    "diagnose_4ps": ["I", "P1", "P2", "P3", "P4"],  # Diagnose
    "basic_cycle": ["I"],  # Installation familiarity
    "measurement_points": ["I", "P3"],  # Where to measure
    "system_balance": ["I", "P2", "P3"],  # Balance concept
    "pressostat_settings": ["P1", "P2"],  # Settings
    "frozen_evaporator": ["O"],  # Component troubleshooting
}

async def main():
    cm = ClientManager()
    async with cm.connect_to_async_client() as client:
        coll = client.collections.get('VSM_DiagramUserFacing')
        
        # Get all diagrams
        all_diagrams = await coll.query.fetch_objects(limit=8)
        
        for obj in all_diagrams.objects:
            diagram_id = obj.properties.get('diagram_id')
            
            if diagram_id in PHASE_MAPPINGS:
                new_phases = PHASE_MAPPINGS[diagram_id]
                
                # Update with phase tags
                await coll.data.update(
                    uuid=obj.uuid,
                    properties={"smido_phases": new_phases}
                )
                
                print(f"✅ {diagram_id}: {new_phases}")
    
    await cm.close_clients()

asyncio.run(main())
```

## Part C: Testing

### C1: Test Image Gallery UX

- Ask "toon me een compressor"
- Verify: Only 2 images shown by default
- Verify: Description is 1 line, readable contrast
- Verify: Can expand to see more images

### C2: Test PNG Diagrams

- Ask "toon het SMIDO overzicht diagram"
- Expected: PNG image of smido_overview.png displayed
- Verify: Image renders in markdown

### C3: Test Mermaid Diagrams

- Ask "toon een flowchart van de diagnose stappen"
- Expected: Mermaid flowchart from AgentInternal
- Verify: Mermaid renders with colors/styling

### C4: Test Diagram in Manual Search

- Ask "zoek informatie over procesinstellingen"
- Expected: Manual sections + diagrams (PNG or Mermaid)
- Verify: Diagrams appear after manual text

## Execution Order

1. **A1**: Change default limit 5 → 2 in search_manual_images
2. **A2**: Improve image description (1 line, better contrast)
3. **B1**: Update show_diagram (PNG + Mermaid handling)
4. **B2**: Register show_diagram in bootstrap
5. **B3**: Update search_manuals_by_smido diagram output
6. **B4**: Run tag_user_facing_diagrams.py script
7. **C1-C4**: Test all scenarios
8. Commit all changes

## Files Modified

**Backend** (3 files):

1. `elysia/api/custom_tools.py` (2 tools updated)
2. `features/vsm_tree/bootstrap.py` (register show_diagram)
3. `scripts/tag_user_facing_diagrams.py` (NEW)

**Frontend** (1 file):

1. `elysia-frontend-main/app/components/chat/displays/Image/ImageGalleryDisplay.tsx` (description UX)

## Expected Results

**Image Gallery**:

- Shows 2 images by default (cleaner, faster)
- Description: 1 line, high contrast
- User can expand for more (existing dropdown)

**Diagrams**:

- UserFacing: PNG images display (simple for technicians)
- AgentInternal: Mermaid flowcharts render (complex logic)
- Both findable via search_manuals and show_diagram
- SMIDO fallback works for UserFacing diagrams

### To-dos

- [ ] Copy 233 images to elysia/api/static/manual_images/
- [ ] Enrich image metadata with SMIDO tags and component keywords
- [ ] Create VSM_ManualImage Weaviate collection schema
- [ ] Upload 233 enriched image metadata objects to Weaviate
- [ ] Create search_manual_images custom tool
- [ ] Create ImageGalleryDisplay React component
- [ ] Register image tool in bootstrap.py
- [ ] Preprocess VSM_ManualImage with Dutch prompts
- [ ] Test image search and frontend display
- [ ] Update agent.mdc with VSM_ManualImage collection info