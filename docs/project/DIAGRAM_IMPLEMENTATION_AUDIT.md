# Diagram Implementation Audit - Current vs Expected

**Date**: Nov 13, 2025  
**Issue**: Diagrams niet zichtbaar in frontend, worden niet gevonden door tools

---

## Executive Summary

**Problem**: Diagrams worden niet getoond aan user, ondanks:
- ✅ 16 diagrams in Weaviate (8 UserFacing + 8 AgentInternal)
- ✅ PNG files in `/static/diagrams/` (8 files, 14-29 KB each)
- ✅ Mermaid code in AgentInternal diagrams
- ❌ UserFacing diagrams missing mermaid_code
- ❌ PNG URLs not used
- ❌ Tools return diagrams maar frontend rendert niet

---

## 1. Data Layer Analysis

### Source JSONL Files

**user_facing_diagrams.jsonl**:
```json
{
  "diagram_id": "smido_overview",
  "title": "Smido Overview",
  "png_url": "/static/diagrams/smido_overview.png",  ✅ PRESENT
  "png_width": 1126,
  "png_height": 228,
  "mermaid_code": NOT IN SOURCE,  ❌ MISSING
  "smido_phases": [],
  "agent_diagram_id": "smido_main_flowchart"
}
```

**agent_internal_diagrams.jsonl**:
```json
{
  "diagram_id": "smido_main_flowchart",
  "title": "SMIDO Main Flowchart",
  "mermaid_code": "flowchart LR...",  ✅ PRESENT (2418 chars)
  "smido_phases": ["melding", "technisch", ...],
  "diagram_type": "flowchart"
}
```

**Design Intent**:
- **UserFacing**: Simple PNG images voor technicians (M phase)
  - Show via `<img src="/static/diagrams/smido_overview.png">`
- **AgentInternal**: Complex Mermaid flowcharts voor agent reasoning
  - Render via `<ReactMarkdown>` with mermaid support

### Weaviate State (Current)

**VSM_DiagramUserFacing** (8 diagrams):
```python
{
  "diagram_id": "frozen_evaporator",
  "title": "Frozen Evaporator",
  "smido_phases": [],  # Empty!
  "mermaid_code": "",  # EMPTY - missing from upload!
  "png_url": ???       # NOT CHECKED if uploaded
}
```

**VSM_DiagramAgentInternal** (8 diagrams):
```python
{
  "diagram_id": "pressostat_adjustment_logic",
  "title": "Pressostat Adjustment Logic - LP & HP Settings",
  "smido_phases": ["procesinstellingen"],  ✅ POPULATED
  "mermaid_code": "flowchart TD\nsubgraph...",  ✅ PRESENT (2418 chars)
}
```

**Key Issue**: UserFacing diagrams uploaded **without** `png_url` or have empty `mermaid_code`

---

## 2. Tool Layer Analysis

### search_manuals_by_smido (lines 160-261)

**Current behavior**:
1. Searches diagrams by `related_diagram_ids` (if populated in manual sections)
2. Fallback: Searches by `smido_phases` tags
3. **Only uses AgentInternal** for phase matching (UserFacing has empty smido_phases)
4. Outputs diagrams as **Response** with Mermaid markdown (lines 244-259)

**Problems**:
- UserFacing diagrams have **empty smido_phases** → never returned by fallback
- UserFacing diagrams **missing mermaid_code** → if found, won't render
- Should use **PNG URLs** for UserFacing, not Mermaid code

### show_diagram (lines 1184-1361, user-added)

**Current behavior**:
1. Fetch by `diagram_id` OR `smido_step`
2. Tries UserFacing first, then AgentInternal
3. Extracts `mermaid_code` and outputs as **Response** with markdown
4. Also yields **Result** with diagram objects

**Problems**:
- UserFacing diagrams have NO mermaid_code → yields Error "no Mermaid code"
- Doesn't use `png_url` field for UserFacing diagrams
- Should handle two types: PNG (UserFacing) vs Mermaid (AgentInternal)

---

## 3. Static File Layer

### PNG Files Available

Location: `elysia/api/static/diagrams/`

```
smido_overview.png            25.9 KB  ✅ EXISTS
diagnose_4ps.png              25.4 KB  ✅ EXISTS
basic_cycle.png               24.2 KB  ✅ EXISTS
measurement_points.png        14.8 KB  ✅ EXISTS
pressostat_settings.png       19.9 KB  ✅ EXISTS
system_balance.png            29.3 KB  ✅ EXISTS
frozen_evaporator.png         21.2 KB  ✅ EXISTS
troubleshooting_template.png  23.2 KB  ✅ EXISTS
```

**Accessibility**: 
- URLs: `http://localhost:8000/static/diagrams/{filename}.png`
- Should work (same pattern as manual_images)

---

## 4. Frontend Layer

### Mermaid Rendering

**Current**: Frontend rendert Mermaid via ReactMarkdown + remark-gfm

**File**: Check `elysia-frontend-main/app/components/chat/RenderChat.tsx`
- Does it render markdown with ```mermaid blocks?
- Is remark-gfm configured?

### Image Display

**For PNG diagrams**: 
- Need to add to RenderDisplay.tsx (like we did for manual_images)
- OR use markdown: `![Diagram](http://localhost:8000/static/diagrams/smido_overview.png)`

---

## 5. Expected vs Actual Behavior

### EXPECTED Behavior

**Scenario 1**: User asks "Toon het SMIDO overzicht diagram"

Agent should:
1. Call `show_diagram(diagram_id="smido_overview")`
2. Fetch from VSM_DiagramUserFacing
3. Get `png_url`: "/static/diagrams/smido_overview.png"
4. Return: `<img>` or markdown `![](png_url)`
5. Frontend displays PNG image

**Scenario 2**: Agent needs complex logic diagram

Agent should:
1. Use VSM_DiagramAgentInternal
2. Get `mermaid_code`
3. Return: Markdown with ```mermaid code block
4. Frontend renders Mermaid flowchart

### ACTUAL Behavior

**Scenario 1** (Current):
1. ✅ Diagrams fetched from Weaviate
2. ❌ UserFacing diagrams have empty `mermaid_code`
3. ❌ `png_url` field not used
4. ❌ Tool yields Error "no Mermaid code"
5. ❌ Nothing shown to user

**Scenario 2** (Current):
1. ✅ AgentInternal diagrams have `mermaid_code`
2. ✅ Markdown with ```mermaid block generated
3. ❓ Frontend renders? (need to verify ReactMarkdown + remark-gfm)
4. ❓ Mermaid CSS/JS loaded?

---

## 6. Root Causes Identified

### Issue 1: UserFacing Diagrams Missing Data

**Source file** (`user_facing_diagrams.jsonl`):
- Has `png_url` field ✅
- NO `mermaid_code` field (by design) ✅

**Weaviate upload**:
- `png_url` NOT uploaded? ❌ (need to verify schema)
- Collection has `mermaid_code` property but it's empty

**Upload script**: Check `features/diagrams_vsm/src/import_diagrams_weaviate.py`
- Did it skip `png_url`?
- Did it upload empty `mermaid_code`?

### Issue 2: Tools Don't Handle PNG URLs

**show_diagram** (line 1320):
- Only checks `mermaid_code`
- Doesn't check `png_url` field
- Should handle both types:
  ```python
  png_url = props.get("png_url")
  if png_url:
      # Return image markdown
      yield Response(f"![{title}]({png_url})")
  elif mermaid_code:
      # Return mermaid markdown
      yield Response(f"```mermaid\n{mermaid_code}\n```")
  ```

**search_manuals_by_smido** (line 248):
- Same issue: only checks `mermaid_code`
- Ignores `png_url`

### Issue 3: Frontend Mermaid Support

**Need to verify**:
1. Does ReactMarkdown render ```mermaid blocks?
2. Is `remark-gfm` or `rehype-mermaid` configured?
3. Is Mermaid.js loaded in the frontend?

**File to check**: `elysia-frontend-main/app/components/chat/RenderChat.tsx`

---

## 7. Proposed Fix Strategy (NO IMPLEMENTATION YET)

### Fix 1: Re-upload UserFacing Diagrams with PNG URLs

1. Verify `features/diagrams_vsm/src/import_diagrams_weaviate.py` includes `png_url` in schema
2. Re-run upload script to populate `png_url` in Weaviate
3. Verify: `png_url` present in VSM_DiagramUserFacing

### Fix 2: Update Tools to Handle Both Types

**show_diagram** and **search_manuals_by_smido**:
```python
# Check for PNG first (UserFacing)
png_url = props.get("png_url")
if png_url:
    # Full URL for display
    full_url = f"http://localhost:8000{png_url}"
    yield Response(f"**{title}**\n\n![{title}]({full_url})\n\n{description}")
    
# Fallback to Mermaid (AgentInternal)
elif mermaid_code:
    yield Response(f"**{title}**\n\n```mermaid\n{mermaid_code}\n```")
```

### Fix 3: Verify Frontend Mermaid Rendering

- Check if ReactMarkdown has mermaid support
- If not, add `react-markdown-mermaid` or `rehype-mermaid`
- Ensure Mermaid.js CSS/JS loaded

### Fix 4: Add show_diagram to Bootstrap

**Currently**: show_diagram exists but NOT registered in bootstrap
**Needed**: Add to `features/vsm_tree/bootstrap.py` root tools

---

## 8. Investigation Results ✅ COMPLETE

**All questions answered**:

1. ✅ **Weaviate schema**: VSM_DiagramUserFacing HAS `png_url` property
   - Schema includes: diagram_id, title, description, png_url, png_width, png_height, etc.
   
2. ✅ **Data population**: png_url IS POPULATED in all 8 UserFacing diagrams
   - frozen_evaporator → /static/diagrams/frozen_evaporator.png
   - smido_overview → /static/diagrams/smido_overview.png
   - All 8/8 have valid png_url paths
   
3. ✅ **Frontend Mermaid**: ReactMarkdown DOES render ```mermaid blocks
   - MarkdownFormat.tsx lines 153-207: Custom MermaidCode component
   - Uses mermaid.render() to generate SVG
   - Package.json: mermaid ^11.12.1, react-markdown ^9.0.1, remark-gfm ^4.0.0
   
4. ❌ **Tool registration**: show_diagram NOT in bootstrap.py
   - Tool exists in custom_tools.py (user added)
   - But NOT imported/registered in bootstrap
   - Agent cannot use it (not in available_options)
   
5. ✅ **PNG accessibility**: Files exist in elysia/api/static/diagrams/
   - 8 PNG files (14-29 KB each)
   - Accessible via /static/diagrams/{filename}.png

---

## 9. Current Files Involved

**Data**:
- `features/diagrams_vsm/output/user_facing_diagrams.jsonl` (8 diagrams, has png_url)
- `features/diagrams_vsm/output/agent_internal_diagrams.jsonl` (8 diagrams, has mermaid_code)
- `elysia/api/static/diagrams/*.png` (8 PNG files)

**Backend**:
- `features/diagrams_vsm/src/import_diagrams_weaviate.py` (upload script)
- `elysia/api/custom_tools.py` (show_diagram + search_manuals_by_smido)
- `features/vsm_tree/bootstrap.py` (tool registration)

**Frontend**:
- `elysia-frontend-main/app/components/chat/RenderChat.tsx` (markdown rendering)
- `elysia-frontend-main/package.json` (check dependencies)

---

## 10. Next Steps (Investigation Phase)

1. Check Weaviate schema for VSM_DiagramUserFacing → verify `png_url` property exists
2. Query one UserFacing diagram → check if `png_url` is populated
3. Check upload script → verify it uploads `png_url` from JSONL
4. Check frontend package.json → verify Mermaid dependencies
5. Check ReactMarkdown config → verify mermaid plugin
6. Manually test PNG URL → `curl http://localhost:8000/static/diagrams/smido_overview.png`
7. Check if show_diagram registered in bootstrap → if not, explains why never called

**Status**: Investigation complete, ready for fix implementation when requested

---

## 11. Summary of Findings

### ✅ WORKING Components

1. **Data Layer**: 
   - Weaviate has both collections (16 diagrams total)
   - UserFacing: png_url populated (8/8) ✅
   - AgentInternal: mermaid_code populated (8/8) ✅
   - PNG files exist in /static/diagrams/ ✅

2. **Frontend Layer**:
   - Mermaid.js ^11.12.1 installed ✅
   - ReactMarkdown configured with Mermaid support ✅
   - Custom MermaidCode component renders ```mermaid blocks ✅

### ❌ BROKEN Components

1. **Tool Layer**:
   - `show_diagram` tool NOT registered in bootstrap ❌
   - Agent cannot call it (not in available_options) ❌
   - Tool only handles Mermaid, ignores `png_url` ❌

2. **search_manuals_by_smido**:
   - Returns diagrams but only with Mermaid code ❌
   - Doesn't use `png_url` for UserFacing diagrams ❌
   - UserFacing diagrams have empty smido_phases → never found by fallback ❌

### 🔧 Required Fixes (In Priority Order)

**Fix 1**: Update `show_diagram` to handle both PNG and Mermaid
```python
png_url = props.get("png_url")
if png_url:
    # UserFacing diagram - return image
    full_url = f"http://localhost:8000{png_url}"
    yield Response(f"![{title}]({full_url})")
elif mermaid_code:
    # AgentInternal diagram - return mermaid
    yield Response(f"```mermaid\n{mermaid_code}\n```")
```

**Fix 2**: Register `show_diagram` in bootstrap.py
```python
from elysia.api.custom_tools import show_diagram
tree.add_tool(branch_id="base", tool=show_diagram)
```

**Fix 3**: Update `search_manuals_by_smido` diagram output (lines 244-259)
- Same dual handling: PNG or Mermaid
- Don't skip UserFacing diagrams

**Fix 4**: Populate UserFacing `smido_phases` in Weaviate
- Currently empty → never found by SMIDO fallback search
- Need to add tags like ["M"], ["I"], etc. based on when_to_show

### Impact After Fixes

**User asks**: "Toon het SMIDO overzicht diagram"
- ✅ Agent calls show_diagram(diagram_id="smido_overview")
- ✅ Fetches from VSM_DiagramUserFacing
- ✅ Gets png_url: "/static/diagrams/smido_overview.png"
- ✅ Returns markdown: ![Smido Overview](/static/diagrams/smido_overview.png)
- ✅ Frontend displays PNG image

**During I phase**: After search_manuals
- ✅ Diagrams fetched with fallback strategy
- ✅ UserFacing: PNG images shown
- ✅ AgentInternal: Mermaid flowcharts rendered
- ✅ Both types visible to technician

