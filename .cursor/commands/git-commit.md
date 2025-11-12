
## HARD
- Abort if on branch `main` or `master`.
- Never use force or history rewrite.
- Only run git commands in this repo.
- If nothing staged after add, abort.

## COMMIT MESSAGE (Conventional Commits)
- Derive from BOTH: `git diff --cached` + current chat intent.
- Format: `type(scope): summary` (≤72 chars), then body (≤100 cols), bullets, optional `BREAKING CHANGE:`.
- type ∈ {feat, fix, perf, refactor, docs, test, chore, build, ci, style}. Scope optional.

## STEPS
1) Print:
   - `git status -sb`
   - `BRANCH=$(git rev-parse --abbrev-ref HEAD)`; print it
   - If BRANCH in {main,master} → print "abort: protected branch" and STOP
2) `git add -A`
3) If `git diff --cached --quiet` → print "abort: no staged changes" and STOP
4) Capture patch: `PATCH=$(git diff --cached)`
   - From PATCH + chat: synthesize commit message per policy; echo under `## Commit Message`
5) `git commit -m "<COMMIT_MESSAGE>"`
6) Push:
   - If upstream exists → `git push`
   - Else → `git push -u origin $(git rev-parse --abbrev-ref HEAD)`
7) Print:
   - `git rev-parse --short HEAD`
   - `git rev-parse --abbrev-ref --symbolic-full-name @{u} || echo none`
   - `git log -1 --pretty=fuller`