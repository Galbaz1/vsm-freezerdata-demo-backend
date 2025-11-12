# User-Facing Diagrams

**Purpose**: Simple, clean diagrams optimized for display in the VSM frontend UI

All diagrams follow the standards in `../USER_FACING_DIAGRAM_STANDARDS.md`

---

## Diagrams

| File | Purpose | Layout | Nodes | When to Show |
|------|---------|--------|-------|--------------|
| `smido_overview.mermaid` | Show 5 main SMIDO phases | LR | 8 | "What is SMIDO?" / Overview |
| `diagnose_4ps.mermaid` | Show 4 P's checklist | TB | 5 | "What should I check?" (D phase) |
| `basic_cycle.mermaid` | Explain refrigeration cycle | Circular | 4 | "How does it work?" (I phase) |
| `measurement_points.mermaid` | Show WHERE to measure P/T | LR | 8 | "Where do I measure?" (P3 phase) |
| `system_balance.mermaid` | Explain "uit balans" concept | LR | 7 | "What is 'out of balance'?" |
| `pressostat_settings.mermaid` | Show pressostat adjustment | TB | 6 | "How to adjust pressostat?" (P2) |
| `troubleshooting_template.mermaid` | Show response format | LR | 3 | Formatting troubleshooting output |
| `frozen_evaporator.mermaid` | Show A3 case example | LR | 6 | "Show me a similar case" |

---

## Design Standards

- **Layout**: Landscape (LR) or square (TB) - NOT tall vertical
- **Complexity**: 3-8 nodes per diagram
- **Text**: 2-3 words per node maximum
- **Colors**: Consistent 4-5 color palette
- **Styling**: Professional, clean, high contrast

For complex decision trees, see: `../agent_internal/`
