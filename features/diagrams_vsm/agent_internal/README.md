# Agent Internal Diagrams

**Purpose**: Complex diagrams for agent decision-making and logic (NOT shown to users)

These diagrams are used internally by the agent for parsing into decision trees, understanding workflow logic, and making decisions. They are NOT optimized for user display.

---

## Diagrams

| File | Purpose | Nodes | Agent Use |
|------|---------|-------|-----------|
| `smido_main_flowchart.mermaid` | Complete M→T→I→D→O workflow | 30+ | Decision tree structure |
| `smido_3ps_diagnosis.mermaid` | Detailed 4 P's breakdown | 20+ | Diagnosis logic |
| `smido_frozen_evaporator_example.mermaid` | A3 case study (detailed) | 15+ | Pattern matching |
| `balance_diagram.mermaid` | System balance relationships | 15+ | "Uit balans" concept |
| `pressostat_adjustment_logic.mermaid` | Detailed adjustment logic | 12+ | P2 phase logic |
| `schematic_with_instrumentation.mermaid` | Full system with sensors | 12+ | P3 phase logic |
| `troubleshooting_table_flow.mermaid` | Detailed response format | 8 | Output formatting |
| `basic_refrigeration_cycle.mermaid` | Full cycle with zones | 10+ | System understanding |
| `smido_data_integration.mermaid` | Architecture diagram | 15+ | System architecture |

---

## Usage

The agent uses these diagrams to:
- Build decision tree structure
- Parse workflow logic
- Understand complete SMIDO methodology
- Make intelligent decisions
- Generate context-aware responses

**These are NOT shown to technicians in the UI.**

For user-facing diagrams, see: `../user_facing/`
