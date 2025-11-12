# Create PR

## Overview
Create a well-structured pull request with proper description, labels, and reviewers.

## Steps
1. **Prepare branch**
   - Ensure all changes are committed
   - Push branch to remote
   - Verify branch is up to date with main

2. **Create PR (GitHub MCP preferred)**
   - **If GitHub MCP available**: Use `mcp_GitHub_create_pull_request` with structured description
   - **Fallback**: Manual GitHub web interface with template below

3. **Trigger Bugbot review (optional, recommended)**
   - Prompt: Run Bugbot now? (y/N) — if yes, comment `cursor review`
   - For verbose logs: `cursor review verbose=true`
   - Re-run after updates by commenting again

4. **PR Description Template**
   - Summarize changes clearly
   - Include context and motivation
   - List any breaking changes
   - Add screenshots if UI changes

## PR Template
- [ ] Feature A
- [ ] Bug fix B
- [ ] Unit tests pass
- [ ] Manual testing completed


