# Create, Switch, and Publish a Branch

You are Cursor Agent. Show the user the four common branch types, ask them to pick one (A–D), then create, switch, and publish that branch.

## Step 1 — Present options
Explain briefly:

- **A) Feature branch** – new functionality (base: main, e.g. `feature/login-ui`).
- **B) Bugfix branch** – fix a defect (base: main, e.g. `bugfix/cart-crash`).
- **C) Release branch** – stabilize for a release (base: main, e.g. `release/v1.4`).
- **D) Experiment branch** – prototype/exploration (base: current HEAD, e.g. `experiment/ai-search`).

Ask: *"Choose A, B, C, or D. Optionally add a slug (e.g. `A login-ui`)."*

## Step 2 — Parse choice
- `CHOICE` = A/B/C/D.
- `SLUG` = provided words after choice, kebab-cased; if empty, generate from chat intent.

## Step 3 — Determine base
- A/B/C → base = `main`.
- D → base = current HEAD.

## Step 4 — Name branch
- A → `feature/${SLUG}`
- B → `bugfix/${SLUG}`
- C → `release/${SLUG}` (if not vX.Y form, infer `vX.Y`)
- D → `experiment/${SLUG}`

## Step 5 — Create & switch
- If A/B/C:  
  - `git fetch --prune`  
  - `git switch main`  
  - `git pull --ff-only`  
  - `git switch -c "${BRANCH}"`
- If D:  
  - `git switch -c "${BRANCH}"`

## Step 6 — Publish
- Never push to `main` or `master`.  
- `git push -u origin "${BRANCH}"`
- **Optional**: If GitHub MCP available, can create PR immediately with `mcp_GitHub_create_pull_request`

## Step 7 — Output
Print:  
- `Created & switched to: ${BRANCH}`  
- `Published to: origin/${BRANCH}`  
- Current branch: `git rev-parse --abbrev-ref HEAD`  
- Upstream: `git rev-parse --abbrev-ref --symbolic-full-name @{u} || echo none`