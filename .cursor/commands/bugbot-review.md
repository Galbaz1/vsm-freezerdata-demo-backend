# Bugbot Review

## Overview
Trigger and manage Bugbot reviews on pull requests.

## Steps
1. **Trigger review**
   - Comment `cursor review` on the PR
   - Optional verbose logs: `cursor review verbose=true`

2. **When to run**
   - After opening a PR
   - After pushing updates addressing feedback
   - Before requesting final approval

3. **Tips**
   - Use clear PR descriptions for better analysis
   - Re-run after significant changes
   - Combine with `address-github-pr-comments.md` for fixes
