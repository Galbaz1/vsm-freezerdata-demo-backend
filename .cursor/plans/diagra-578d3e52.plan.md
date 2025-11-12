<!-- 578d3e52-5d62-49ba-9547-37c6598b24cc 7ade19df-0aaa-4c0e-86ba-c9b62f6003dd -->
# Add Mermaid Diagram Rendering to Elysia Frontend

## Overview

Enable native Mermaid diagram rendering in the Elysia frontend by adding the `remark-mermaidjs` plugin, then update the `show_diagram` tool to return user-facing Mermaid code (read from filesystem) in a Response object.

## Implementation Steps

### 1. Frontend Changes

**Install Mermaid Plugin**

- Navigate to [elysia-frontend-main](elysia-frontend-main)
- Run: `npm install remark-mermaidjs`

**Update MarkdownFormat Component**

- File: [elysia-frontend-main/app/components/chat/components/MarkdownFormat.tsx](elysia-frontend-main/app/components/chat/components/MarkdownFormat.tsx)
- Line 6: Add import: `import remarkMermaid from 'remark-mermaidjs';`
- Line 206: Update plugins: `remarkPlugins={[remarkGfm, remarkMermaid]}`
- Line 171: Change `prose-img:hidden` to `prose-img:max-w-full prose-img:h-auto` (enable images for other use cases)

**Build and Export**

- Run: `npm run assemble:clean` (builds to `out/` then copies to `../elysia/api/static/`)
- This replaces the current static frontend with Mermaid-enabled version

### 2. Backend Changes

**Update show_diagram Tool**

- File: [elysia/api/custom_tools.py](elysia/api/custom_tools.py)
- Current implementation returns `Result` with PNG URLs and product mapping
- New implementation:

  1. Fetch user-facing diagram metadata from `VSM_DiagramUserFacing` (get `agent_diagram_id`)
  2. Read user-facing Mermaid code from filesystem: `features/diagrams_vsm/user_facing/{diagram_id}.mermaid`
  3. Fetch agent-internal Mermaid from `VSM_DiagramAgentInternal` 
  4. Store agent Mermaid in `tree_data.environment.hidden_environment` (for agent context)
  5. Return user Mermaid in `Response` with markdown code fence:
````python
yield Response(
    text=f"```mermaid\n{user_facing_mermaid}\n```\n\n**{title}**: {description}"
)
````


**Key Implementation Details**:

- Use `Path(__file__).parent.parent.parent / "features/diagrams_vsm/user_facing"` to locate files
- Read `.mermaid` file content as text
- Wrap in triple backtick mermaid code fence for markdown rendering
- Keep agent diagram in hidden_environment for reasoning

### 3. Verification

**Test the Flow**:

1. Start backend: `elysia start`
2. Clear browser cache (Cmd+Shift+R)
3. Ask: "Wat is SMIDO?"
4. Verify: Rendered Mermaid diagram appears (not PNG)
5. Check: Agent can reference complex diagram in hidden_environment

**Expected Behavior**:

- Frontend receives Response with Mermaid code block
- react-markdown + remark-mermaidjs renders diagram
- Diagram is responsive and properly sized
- Agent uses complex diagram for reasoning

### 4. Cleanup (Optional)

**Remove Unused Assets**:

- PNGs in `elysia/api/static/diagrams/` (no longer needed)
- Thumbnail directory `elysia/api/static/diagrams/thumbs/`

**Note**: Keep PNG generation scripts for potential future use or fallback scenarios.

## Files Modified

**Frontend**:

- [elysia-frontend-main/package.json](elysia-frontend-main/package.json) - Add dependency
- [elysia-frontend-main/app/components/chat/components/MarkdownFormat.tsx](elysia-frontend-main/app/components/chat/components/MarkdownFormat.tsx) - Add Mermaid plugin

**Backend**:

- [elysia/api/custom_tools.py](elysia/api/custom_tools.py) - Rewrite show_diagram to use Response + filesystem reads

**Generated**:

- [elysia/api/static/](elysia/api/static/) - Entire directory replaced by new build

## Benefits

- No sizing/cropping issues (Mermaid renders responsively)
- No PNG maintenance (source of truth is .mermaid files)
- Dynamic rendering (can update diagrams without rebuild)
- Simpler data flow (read from filesystem, not Weaviate PNG URLs)
- Agent still gets complex diagrams for reasoning

### To-dos

- [ ] Install remark-mermaidjs in elysia-frontend-main
- [ ] Update MarkdownFormat.tsx to add Mermaid rendering and enable images
- [ ] Run npm run assemble:clean to build and export to elysia/api/static
- [ ] Update show_diagram tool to read .mermaid files and return Response with code fence
- [ ] Start backend and test diagram rendering in browser