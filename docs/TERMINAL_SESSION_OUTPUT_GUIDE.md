# Terminal Session Output Guide

When you start a conversation in Elysia, the User ID and Conversation ID are automatically printed to the terminal in a clear, easy-to-copy format.

## What Changed

Previously, session IDs were only available in debug logs. Now they are:

✅ **Printed prominently** in colored panels  
✅ **Easy to copy** - just select and copy from terminal  
✅ **Shown at the right time** - when you need them  
✅ **Include helpful commands** - showing how to access the data  

## Terminal Output Examples

### User Initialization

When you open the frontend for the first time:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Session Started                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ New User Created                          ┃
┃ User ID: 550e8400-e29b-41d4-a716-4466554 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Conversation Creation

When you start a new conversation:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              New Session                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ New Conversation Created                        ┃
┃ User ID: 550e8400-e29b-41d4-a716-446655440000  ┃
┃ Conversation ID: 123e4567-e89b-12d3-a456-426   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Get session data:                              ┃
┃ python3 scripts/get_tree_session_data.py \    ┃
┃   550e8400-e29b-41d4-a716-446655440000 \      ┃
┃   123e4567-e89b-12d3-a456-426614174000        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Session Resumption

When you open an existing conversation:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃             Existing Session                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Conversation Resumed                            ┃
┃ User ID: 550e8400-e29b-41d4-a716-446655440000  ┃
┃ Conversation ID: 123e4567-e89b-12d3-a456-426   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## How to Use the IDs

### Option 1: Using the Script

The terminal helpfully shows the command to run:

```bash
python3 scripts/get_tree_session_data.py <user_id> <conversation_id>
```

This gives you instant access to all session data.

### Option 2: In Your Python Code

```python
from elysia.api.services.user import UserManager
from elysia.api.dependencies.common import get_user_manager

user_manager = get_user_manager()
user = await user_manager.get_user_local("<user_id>")
tree = user["tree_manager"].get_tree("<conversation_id>")

# Access tree data
print(tree.tree)  # Tree structure
print(tree.tree_data.conversation_history)  # Messages
```

### Option 3: Via API Endpoints

```bash
# Get tree structure
curl http://localhost:8000/init/tree/<user_id>/<conversation_id>

# Get frontend payloads
curl http://localhost:8000/db/<user_id>/load_tree/<conversation_id>
```

## Color Coding

The panels use colors to indicate:

- 🟢 **Green**: New session or conversation created
- 🔵 **Blue**: Existing session or conversation resumed
- 🔷 **Cyan**: Helpful information or commands

## Tips for Finding the IDs

1. **Look for colored panels** - They stand out in the terminal
2. **Copy immediately** - IDs are shown when sessions are created
3. **Unique format** - Panels are clearly distinguished from other output
4. **Include helpful hints** - The "Get session data:" panel shows the exact command

## Accessing Terminal Output

The output appears in the terminal where you ran:

```bash
elysia start
```

If you don't see it:

1. Check that Elysia is running (you should see "Uvicorn running on...")
2. Make sure you're looking at the right terminal window
3. The output appears when the frontend makes API calls
4. Check logs if you set `LOGGING_LEVEL=DEBUG`

## Example: Complete Workflow

```bash
# Terminal 1: Start Elysia
$ elysia start
INFO:     Uvicorn running on http://localhost:8000

# [At this point, open http://localhost:8000 in your browser]

# The terminal shows:
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃              New Session                        ┃
# ┃ New Conversation Created                        ┃
# ┃ User ID: 550e8400-e29b-41d4-a716-446655440000  ┃
# ┃ Conversation ID: 123e4567-e89b-12d3-a456-426   ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# Terminal 2: Use the IDs
$ python3 scripts/get_tree_session_data.py \
  550e8400-e29b-41d4-a716-446655440000 \
  123e4567-e89b-12d3-a456-426614174000

📊 SESSION SUMMARY
================================================================================
User ID: 550e8400-e29b-41d4-a716-446655440000
Conversation ID: 123e4567-e89b-12d3-a456-426614174000
...
```

## Files Changed

### `/elysia/api/routes/init.py`

- `POST /init/user/{user_id}` - Now prints user ID when initializing
- `POST /init/tree/{user_id}/{conversation_id}` - Now prints user ID and conversation ID

Each endpoint displays a clear panel with the IDs and helpful instructions.

## Documentation

See also:
- [QUICK_START_BACKEND_ACCESS.md](QUICK_START_BACKEND_ACCESS.md) - Step-by-step guide
- [ACCESSING_TREE_SESSION_DATA.md](ACCESSING_TREE_SESSION_DATA.md) - Detailed API reference
- [SESSION_ID_OUTPUT.md](SESSION_ID_OUTPUT.md) - What the output looks like

## Implementation Details

The terminal output uses the `rich` library for formatting:

```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel(
    f"[bold green]New User Created[/bold green]\n"
    f"[yellow]User ID:[/yellow] {user_id}",
    border_style="green",
    padding=(1, 2),
    title="[bold]Session Started[/bold]"
))
```

The panels are:
- **Clearly visible** - Stand out from normal logs
- **Properly formatted** - Bold titles and colored text
- **Easy to copy** - Just select and copy the IDs
- **Informative** - Include the session state (new/resumed)

## Future Improvements

Potential enhancements:
- QR code with session URL (could link directly to session)
- Option to save IDs to a file automatically
- Session history in the frontend
- Direct "Open in terminal" button in frontend

