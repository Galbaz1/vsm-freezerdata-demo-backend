# Dutch Follow-Up Suggestions Implementation

## Problem

The frontend was showing **English follow-up suggestions** despite the VSM agent being configured to operate in Dutch. This was caused by hardcoded English context in the suggestion generation system.

## Root Cause

The follow-up suggestions feature in Elysia used a hardcoded English context string in `elysia/tree/util.py`:

```python
context = (
    "System context: You are an agentic RAG service querying or aggregating information from Weaviate collections..."
)
```

This context was sent to the LLM to generate suggestions, overriding the agent's configured language and style.

## Solution Architecture

We made the suggestions context **configurable** at the agent level, following the same pattern as `agent_description`, `style`, and `end_goal`:

### Flow

1. **`Atlas` class** (`elysia/tree/objects.py`) - Added `suggestions_context` field
2. **`Tree` class** (`elysia/tree/tree.py`) - Accepts `suggestions_context` parameter in `__init__()`
3. **`Config` class** (`elysia/api/utils/config.py`) - Stores `suggestions_context` in config
4. **`TreeManager`** (`elysia/api/services/tree.py`) - Passes `suggestions_context` to Tree
5. **API route** (`elysia/api/routes/utils.py`) - Uses `tree.tree_data.atlas.suggestions_context` when calling suggestions
6. **VSM tree** (`features/vsm_tree/smido_tree.py`) - Defines Dutch context
7. **Seed script** (`scripts/seed_default_config.py`) - Extracts and seeds Dutch context to Weaviate

## Dutch Context for VSM

The VSM-specific suggestions context is defined in `features/vsm_tree/smido_tree.py`:

```python
suggestions_context = """Systeemcontext: Je bent een Virtual Service Mechanic (VSM) die een junior koelmonteur begeleidt via de SMIDO methodiek bij het diagnosticeren van koelinstallatie storingen.

Genereer vervolgvragen die:
- Aansluiten bij de SMIDO fase waar de monteur zich bevindt (M→T→I→D→O)
- De monteur helpen dieper te diagnosticeren of aanvullende data te verzamelen
- Verwijzen naar beschikbare data: sensordata (real-time + historisch), manuals, schemas, eerdere cases (vlogs)
- Natuurlijk en praktisch zijn voor een monteur op locatie
- In helder Nederlands gesteld zijn

Vermijd vragen die:
- Te technisch/complex zijn voor een junior monteur
- Niet beantwoord kunnen worden met de beschikbare data
- Vereisen dat de VSM fysiek aanwezig is (de VSM is op afstand)

Voorbeeld vervolgvragen:
- "Wat is de huidige status van de koelcel?" (M fase)
- "Zijn er actieve alarmen op dit moment?" (M fase)
- "Welke sensordata zie ik van het afgelopen uur?" (P3 fase)
- "Zijn er vergelijkbare cases in de vlog database?" (O fase)
"""
```

## Files Modified

### Core Elysia Framework

1. **`elysia/tree/objects.py`**
   - Added `suggestions_context` field to `Atlas` class

2. **`elysia/tree/tree.py`**
   - Added `suggestions_context` parameter to `Tree.__init__()`
   - Stores in `self.tree_data.atlas.suggestions_context`

3. **`elysia/api/utils/config.py`**
   - Added `suggestions_context` to `Config.__init__()`
   - Added to `to_json()` and `from_json()` methods

4. **`elysia/api/services/tree.py`**
   - Added `suggestions_context` parameter to `update_config()`
   - Passes to Tree in `add_tree()`
   - Added `change_suggestions_context()` method

5. **`elysia/api/routes/utils.py`**
   - Modified `/follow_up_suggestions` endpoint to use `tree.tree_data.atlas.suggestions_context`

### VSM-Specific

6. **`features/vsm_tree/smido_tree.py`**
   - Defined Dutch `suggestions_context` variable
   - Passed to Tree constructor

7. **`scripts/seed_default_config.py`**
   - Extracts `suggestions_context` from VSM tree
   - Adds to config item for Weaviate
   - Adds `suggestions_context` property to ELYSIA_CONFIG__ schema
   - Includes in schema validation checks

## Weaviate Schema Update

The `ELYSIA_CONFIG__` collection now includes a `suggestions_context` property (TEXT type). The seed script automatically adds this property if it's missing from existing collections.

## Testing

To test the implementation:

```bash
# 1. Activate environment
conda activate vsm-hva

# 2. Re-seed config with Dutch suggestions context
python3 scripts/seed_default_config.py

# 3. Start Elysia
elysia start

# 4. Open browser
# Navigate to http://localhost:8000
# Interact with the agent and observe follow-up suggestions in Dutch
```

## Expected Behavior

**Before:**
- Frontend showed English suggestions like:
  - "What are the most recent alarms?"
  - "Show me sensor data trends"
  - "Find similar cases"

**After:**
- Frontend shows Dutch suggestions like:
  - "Wat is de huidige status van de koelcel?"
  - "Zijn er actieve alarmen op dit moment?"
  - "Welke sensordata zie ik van het afgelopen uur?"
  - "Zijn er vergelijkbare cases in de vlog database?"

## Fallback Behavior

If `suggestions_context` is empty or not configured:
- The system falls back to the default English RAG context (in `elysia/tree/util.py`)
- This ensures backward compatibility with non-VSM agents

## Design Principles

1. **No breaking changes** - Empty context defaults to existing behavior
2. **Follows existing patterns** - Uses same config pattern as `style`, `agent_description`, `end_goal`
3. **Language-agnostic** - Can be used for any language, not just Dutch
4. **Domain-specific** - Can be customized per agent type (VSM, medical, legal, etc.)

## Future Enhancements

- Add `num_suggestions` to config (currently hardcoded to 2)
- Add language detection to auto-generate appropriate context
- Add suggestion templates per SMIDO phase
- Track suggestion click-through rates for optimization

