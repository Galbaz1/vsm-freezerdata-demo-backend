# Address GitHub PR Comments

## Overview
Read open review comments on the current branch's pull request and apply fixes, then push updates.

## Steps
1. **Fetch PR context (GitHub MCP preferred)**
   - **If GitHub MCP available**: Use `mcp_GitHub_get_pull_request_comments` to list unresolved comments
   - **Fallback**: Manual GitHub web interface review
   - Optional: Trigger Bugbot by commenting `cursor review` on the PR

2. **Apply fixes**
   - Navigate to referenced files/lines
   - Implement requested changes

3. **Verification**
   - Run tests and lints
   - Ensure no regressions introduced

4. **Update PR**
   - Commit with "Address review comments"
   - Push branch and re-request review
   - Prompt: Re-run Bugbot now? (y/N) — if yes, comment `cursor review` again

## Tips
- Link each fix to the specific comment
- Batch small fixes into a single commit where appropriate
- Use `cursor review verbose=true` for detailed Bugbot logs


