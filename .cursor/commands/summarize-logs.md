name: logs
description: Summarize backend logs (application + uvicorn) with actionable insights
prompt: |
  Summarize the backend logs to help a developer quickly understand current issues and traffic:
  - Read: elysia/logs/elysia.log and elysia/logs/uvicorn.log
  - Produce:
    1) Level counts (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    2) Top recent warnings and errors (deduped, with counts)
    3) HTTP status histogram and top endpoints (normalized)
    4) Any Pydantic/Litellm/Weaviate errors worth attention
    5) Concrete follow-ups
  Keep the output concise, bullet-first, and human-readable.


