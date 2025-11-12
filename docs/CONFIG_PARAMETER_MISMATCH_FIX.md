# Config Parameter Mismatch Fix

**Date:** November 12, 2025  
**Issue:** `ValueError: Invalid branch initialisation: ['vsm_smido']`  
**Root Cause:** Missing `suggestions_context` parameter causing positional argument mismatch

---

## Problem Summary

When starting Elysia, new conversations failed with:

```python
ValueError: Invalid branch initialisation: ['vsm_smido']
```

The config values appeared swapped:
- `branch_initialisation`: `['vsm_smido']` (should be `"empty"` string)
- `feature_bootstrappers`: `[]` (should be `['vsm_smido']` list)

---

## Root Cause Analysis

### Investigation Steps

1. **Checked seed script** ✅ - Config was seeded correctly with:
   - `branch_initialisation = "empty"`
   - `feature_bootstrappers = ["vsm_smido"]`

2. **Checked Weaviate storage** ✅ - Values stored correctly in database:
   ```python
   branch_initialisation: "empty" (type: str)
   feature_bootstrappers: ["vsm_smido"] (type: list)
   use_elysia_collections: True (type: bool)
   ```

3. **Checked Config.from_json()** ✅ - Loading from Weaviate worked correctly

4. **Found the bug** ❌ - **Positional argument mismatch** between `UserManager.update_config()` and `TreeManager.update_config()`

### The Bug

**UserManager.update_config()** (`elysia/api/services/user.py:104-128`) was **missing** the `suggestions_context` parameter.

**Before Fix:**
```python
async def update_config(
    self,
    user_id: str,
    conversation_id: str | None = None,
    config_id: str | None = None,
    config_name: str | None = None,
    settings: dict[str, Any] | None = None,
    style: str | None = None,
    agent_description: str | None = None,
    end_goal: str | None = None,
    branch_initialisation: str | None = None,  # Position 9
    feature_bootstrappers: list[str] | None = None,  # Position 10
):
    # ...
    local_user["tree_manager"].update_config(
        conversation_id,          # Position 1
        config_id,                # Position 2
        config_name,              # Position 3
        settings,                 # Position 4
        style,                    # Position 5
        agent_description,        # Position 6
        end_goal,                 # Position 7
        branch_initialisation,    # Position 8 ❌ Goes to suggestions_context slot!
        feature_bootstrappers,    # Position 9 ❌ Goes to branch_initialisation slot!
    )
```

**TreeManager.update_config()** (`elysia/api/services/tree.py:66-78`) expected:
```python
def update_config(
    self,
    conversation_id: str | None = None,       # Position 1
    config_id: str | None = None,             # Position 2
    config_name: str | None = None,           # Position 3
    settings: dict[str, Any] | None = None,   # Position 4
    style: str | None = None,                 # Position 5
    agent_description: str | None = None,     # Position 6
    end_goal: str | None = None,              # Position 7
    suggestions_context: str | None = None,   # Position 8 ⚠️ EXPECTED HERE
    branch_initialisation: BranchInitType | None = None,  # Position 9
    feature_bootstrappers: list[str] | None = None,       # Position 10
):
```

**Result:** All parameters after `end_goal` were shifted by one position:
- `branch_initialisation` value → went to `suggestions_context` slot
- `feature_bootstrappers` value → went to `branch_initialisation` slot  
- Nothing → went to `feature_bootstrappers` slot (defaulted to `[]`)

---

## The Fix

### Files Modified

1. **`elysia/api/services/user.py`**
   - Added `suggestions_context` parameter to `UserManager.update_config()`
   - Added it to the call to `TreeManager.update_config()`

2. **`elysia/api/routes/init.py`**
   - Added `suggestions_context=default_config.suggestions_context` when calling `update_config()`

3. **`elysia/api/routes/user_config.py`** (2 locations)
   - Added `suggestions_context=data.config.get("suggestions_context")` (line 364)
   - Added `suggestions_context=renamed_config.get("suggestions_context")` (line 670)

### After Fix

**UserManager.update_config()** now has:
```python
async def update_config(
    self,
    user_id: str,
    conversation_id: str | None = None,
    config_id: str | None = None,
    config_name: str | None = None,
    settings: dict[str, Any] | None = None,
    style: str | None = None,
    agent_description: str | None = None,
    end_goal: str | None = None,
    suggestions_context: str | None = None,  # ✅ ADDED
    branch_initialisation: str | None = None,
    feature_bootstrappers: list[str] | None = None,
):
    local_user = await self.get_user_local(user_id)
    local_user["tree_manager"].update_config(
        conversation_id,
        config_id,
        config_name,
        settings,
        style,
        agent_description,
        end_goal,
        suggestions_context,       # ✅ ADDED
        branch_initialisation,     # ✅ Now in correct position
        feature_bootstrappers,     # ✅ Now in correct position
    )
```

---

## Verification

After the fix, the config should load correctly:
- ✅ `branch_initialisation = "empty"` (string)
- ✅ `feature_bootstrappers = ["vsm_smido"]` (list)
- ✅ `use_elysia_collections = True` (boolean)
- ✅ Tree initialization should succeed without errors

---

## Testing

**Restart Elysia and verify:**

```bash
conda activate vsm-hva
elysia start
```

Expected behavior:
1. No `ValueError` errors
2. Config loads with correct values
3. SMIDO tree bootstrapper runs automatically
4. All 9 branches + 8 tools are loaded

---

## Lessons Learned

1. **Always use keyword arguments** for functions with many optional parameters
2. **Positional arguments are fragile** - parameter order changes cause silent bugs
3. **Test parameter alignment** between wrapper functions and the functions they call
4. **Missing parameters** in wrapper functions cause all subsequent positional args to shift

---

## Related Files

- `scripts/seed_default_config.py` - Config seeding (already fixed with `use_elysia_collections`)
- `scripts/check_and_fix_schema.py` - Schema diagnostic tool
- `scripts/debug_config_loading.py` - Config loading debugger (helped identify the issue)

