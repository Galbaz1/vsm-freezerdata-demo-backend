# Accessing Tree Session Data Programmatically

This guide explains how to access the same tree visualization and session data that the frontend sees, programmatically from the backend.

## Overview

The Elysia backend stores all session data in the `Tree` object. You can access:

1. **Tree Structure** (`tree.tree`) - The hierarchical decision tree structure used for visualization
2. **Frontend Payloads** (`tree.returner.store`) - All messages sent to the frontend (tree updates, results, text, etc.)
3. **Conversation History** (`tree.tree_data.conversation_history`) - User and assistant messages
4. **Environment** (`tree.tree_data.environment`) - All objects retrieved by tools
5. **Decision History** (`tree.decision_history`) - The path of decisions made through the tree
6. **Tasks Completed** (`tree.tree_data.tasks_completed`) - Detailed task execution with reasoning

## Quick Access Pattern

```python
from elysia.api.services.user import UserManager
from elysia.api.dependencies.common import get_user_manager

# Get the user manager (singleton)
user_manager: UserManager = get_user_manager()

# Get user and tree
user = await user_manager.get_user_local(user_id)
tree_manager = user["tree_manager"]
tree = tree_manager.get_tree(conversation_id)

# Access tree structure (for visualization)
tree_structure = tree.tree
# This is the same structure the frontend uses for the tree view

# Access all frontend payloads
frontend_payloads = tree.returner.store
# Contains: user_prompt, tree_update, result, text, status, error, completed

# Access conversation history
conversation_history = tree.tree_data.conversation_history
# Format: [{"role": "user"|"assistant", "content": "..."}, ...]

# Access environment (retrieved objects)
environment = tree.tree_data.environment.environment
# Format: {"tool_name": {"result_name": [{"metadata": {...}, "objects": [...]}]}}

# Access decision history
decision_history = tree.decision_history
# Format: [[function_name1, function_name2, ...], [next_iteration], ...]

# Filter tree updates
tree_updates = [
    payload for payload in frontend_payloads 
    if payload.get("type") == "tree_update"
]
```

## Tree Structure Format

The `tree.tree` dictionary has the following structure (same as frontend visualization):

```python
{
    "name": "Branch Name",
    "id": "branch_id",
    "description": "Branch description",
    "instruction": "Instruction for this branch",
    "reasoning": "Reasoning (if available)",
    "branch": True,  # True for branches, False for tools
    "options": {
        "option_id": {
            "name": "Option Name",
            "id": "option_id",
            "description": "Option description",
            "instruction": "",
            "reasoning": "",
            "branch": False,  # or True if it leads to another branch
            "options": {}  # Nested options if branch=True
        },
        ...
    }
}
```

## Frontend Payload Types

The `tree.returner.store` contains all payloads sent to the frontend. Each payload has:

```python
{
    "type": "user_prompt" | "tree_update" | "result" | "text" | "status" | "error" | "completed",
    "id": "uuid",
    "user_id": "user_id",
    "conversation_id": "conversation_id",
    "query_id": "query_id",
    "payload": {
        # Type-specific payload data
    }
}
```

### Tree Update Payload

Tree updates show navigation through the decision tree:

```python
{
    "type": "tree_update",
    "payload": {
        "from_node": "previous_branch_id",
        "to_node": "next_branch_or_tool_id",
        "reasoning": "Why this decision was made",
        "reset_tree": False,  # True if tree structure changed
        "tree_index": 0  # Iteration number
    }
}
```

## Example: Extract Tree Navigation Path

```python
async def get_tree_navigation_path(user_id: str, conversation_id: str):
    """Extract the complete navigation path through the tree."""
    user_manager = get_user_manager()
    user = await user_manager.get_user_local(user_id)
    tree = user["tree_manager"].get_tree(conversation_id)
    
    tree_updates = [
        payload for payload in tree.returner.store 
        if payload.get("type") == "tree_update"
    ]
    
    path = []
    for update in tree_updates:
        payload = update.get("payload", {})
        path.append({
            "from": payload.get("from_node"),
            "to": payload.get("to_node"),
            "reasoning": payload.get("reasoning", ""),
            "timestamp": update.get("id")  # UUID can be used as timestamp proxy
        })
    
    return path
```

## Example: Get Current Tree State

```python
async def get_current_tree_state(user_id: str, conversation_id: str):
    """Get the current state of the tree (last node, conversation, etc.)."""
    user_manager = get_user_manager()
    user = await user_manager.get_user_local(user_id)
    tree = user["tree_manager"].get_tree(conversation_id)
    
    # Get last tree update to see current position
    tree_updates = [
        payload for payload in tree.returner.store 
        if payload.get("type") == "tree_update"
    ]
    
    current_node = None
    if tree_updates:
        last_update = tree_updates[-1]
        current_node = last_update.get("payload", {}).get("to_node")
    
    return {
        "current_node": current_node,
        "conversation_history": tree.tree_data.conversation_history,
        "num_trees_completed": tree.tree_data.num_trees_completed,
        "recursion_limit": tree.tree_data.recursion_limit,
        "tree_structure": tree.tree,
    }
```

## Example: Export Session Data

```python
async def export_session_data(user_id: str, conversation_id: str, output_file: str):
    """Export all session data to JSON file."""
    user_manager = get_user_manager()
    user = await user_manager.get_user_local(user_id)
    tree = user["tree_manager"].get_tree(conversation_id)
    
    data = {
        "metadata": {
            "user_id": tree.user_id,
            "conversation_id": tree.conversation_id,
            "conversation_title": tree.conversation_title,
            "num_trees_completed": tree.tree_data.num_trees_completed,
        },
        "tree_structure": tree.tree,
        "conversation_history": tree.tree_data.conversation_history,
        "decision_history": tree.decision_history,
        "frontend_payloads": tree.returner.store,
        "environment_keys": list(tree.tree_data.environment.environment.keys()),
    }
    
    import json
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    return output_file
```

## Using the Script

A ready-to-use script is available:

```bash
source .venv/bin/activate
python3 scripts/get_tree_session_data.py <user_id> <conversation_id>
```

This will:
- Print a summary of the session
- Display the tree structure
- Show conversation history
- List tree navigation path
- Save full data to JSON file

## API Endpoint Access

You can also access this via existing API endpoints:

- `GET /init/tree/{user_id}/{conversation_id}` - Returns `tree.tree` structure
- `GET /db/{user_id}/load_tree/{conversation_id}` - Returns `tree.returner.store` (frontend rebuild)

However, for programmatic access within the backend, using the `UserManager` and `TreeManager` directly is more efficient.

## Notes

- **Tree Structure**: The `tree.tree` property is reconstructed whenever branches/tools are added/removed. It represents the current tree structure, not the historical path.

- **Frontend Payloads**: The `tree.returner.store` contains the complete history of all messages sent to the frontend, in chronological order.

- **Tree Updates**: Filter `tree.returner.store` by `type == "tree_update"` to get the navigation path through the tree.

- **Environment**: The environment contains all objects retrieved by tools. It's organized by tool name and result name.

- **Session Persistence**: Trees are stored in memory by default. To persist, use `tree.export_to_weaviate()` or `tree.export_to_json()`.

