# Light Review Existing Diffs

## Overview
Perform a lightweight review over current working diffs to flag obvious issues and improvement opportunities.

## Steps
1. **Scan diffs (GitHub MCP preferred)**
   - **If GitHub MCP available**: Use `mcp_GitHub_get_pull_request_diff` for PR reviews
   - **Fallback**: Local `git diff` for working directory changes
   - Identify large or risky changes (security, migrations, public APIs)
   - Note TODOs, commented code, or dead code

2. **Quality checks**
   - Enforce naming, small functions, and consistent patterns
   - Suggest refactors when complexity is high

3. **Tests & docs**
   - Verify relevant tests exist and pass
   - Ensure README/docs updated when behavior changes

## Checklist
- [ ] No debug logs or print statements
- [ ] No commented-out code left behind
- [ ] Public APIs documented and typed
- [ ] Tests cover critical paths


