# show_diagram Tool

## Purpose

Display user-facing diagrams (PNG) to technicians while loading corresponding complex Mermaid diagrams internally for agent understanding.

## Usage

```python
show_diagram(diagram_id: str)
```

## Available Diagrams

| Diagram ID | Purpose | When to Use |
|------------|---------|-------------|
| `smido_overview` | 5-phase SMIDO workflow | "What is SMIDO?" / Overview request |
| `diagnose_4ps` | 4 P's checklist | "What should I check?" (D phase) |
| `basic_cycle` | Refrigeration cycle basics | "How does it work?" (I phase) |
| `measurement_points` | Where to measure P/T | "Where do I measure?" (P3 phase) |
| `system_balance` | "Uit balans" concept | "What does 'out of balance' mean?" |
| `pressostat_settings` | Pressostat adjustment | "How to adjust pressostat?" (P2 phase) |
| `troubleshooting_template` | Response format | Formatting troubleshooting output |
| `frozen_evaporator` | A3 case example | "Show me a similar case" |

## How It Works

1. **Fetches user-facing diagram** from `VSM_DiagramUserFacing` collection
2. **Fetches agent-internal diagram** from `VSM_DiagramAgentInternal` collection using `agent_diagram_id` link
3. **Stores complex Mermaid** in `tree_data.environment.hidden_environment` for agent context
4. **Returns PNG URL** in Result object for frontend display

## Return Value

```python
Result(
    objects=[{
        "diagram_id": "smido_overview",
        "png_url": "/static/diagrams/smido_overview.png",
        "title": "SMIDO Overview",
        "description": "Show 5 main phases to technician",
        "when_to_show": "\"What is SMIDO?\" / Overview request",
        "png_width": 1200,
        "png_height": 800,
    }],
    payload_type="diagram",
    metadata={
        "agent_mermaid_loaded": True,
        "agent_diagram_id": "smido_main_flowchart",
        "agent_title": "SMIDO Main Flowchart - Complete M→T→I→D→O Workflow",
    }
)
```

## Agent Context

The complex Mermaid diagram is stored in the tree environment:

```python
tree_data.environment.hidden_environment[f"diagram_{diagram_id}_mermaid"] = mermaid_code
tree_data.environment.hidden_environment[f"diagram_{diagram_id}_agent_title"] = agent_title
```

This allows the agent to reference the detailed diagram logic while the user sees the simple visual.

## Example Interactions

### M Phase (Melding)
```
User: "Wat is SMIDO?"
Agent: [calls show_diagram("smido_overview")]
       "Dit is de SMIDO methodologie - 5 fasen van storing tot oplossing..."
```

### I Phase (Installatie)
```
User: "Hoe werkt het systeem?"
Agent: [calls show_diagram("basic_cycle")]
       "Het koelsysteem werkt in een kringloop: Compressor → Condensor → Expansieventiel → Verdamper..."
```

### P2 Phase (Procesinstellingen)
```
User: "Hoe pas ik de pressostaat aan?"
Agent: [calls show_diagram("pressostat_settings")]
       "Je ziet hier de START en DIFF instellingen. START is de uitschakeldruk..."
```

### P3 Phase (Procesparameters)
```
User: "Waar moet ik meten?"
Agent: [calls show_diagram("measurement_points")]
       "Meet bij deze 4 punten: P1/T1 na compressor, P2 na condensor..."
```

## Integration

The tool is automatically added to relevant SMIDO branches via bootstrap:

- `smido_melding` - Overview
- `smido_technisch` - Visual check
- `smido_installatie` - System basics
- `smido_p2_procesinstellingen` - Settings
- `smido_p3_procesparameters` - Measurements
- `smido_onderdelen` - Cases

## Frontend Display

The frontend receives a Result with `payload_type="diagram"` containing:
- PNG URL (relative path: `/static/diagrams/{diagram_id}.png`)
- Diagram metadata (title, description)
- Dimensions (width, height)

The frontend should render the PNG using an `<img>` tag with the provided URL.

## Error Handling

- If diagram not found: Returns Error with message
- If collections missing: Returns Error indicating collections need to be uploaded
- If agent diagram missing: Returns Error but still returns user-facing diagram

