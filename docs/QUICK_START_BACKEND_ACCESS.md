# Quick Start: Backend Access to Session Data

This guide shows you the quickest way to access your session data after starting a conversation.

## Step-by-Step

### 1. Start Elysia
```bash
source .venv/bin/activate
elysia start
```

You'll see:
```
[INFO] Uvicorn running on http://localhost:8000
```

### 2. Open Frontend
```
Open browser: http://localhost:8000
```

### 3. Watch Terminal for IDs
When you interact with the frontend, you'll see colored panels printed to the terminal:

```
╭────────────────────────────────────────────────────────────╮
│              New Session                                   │
│ New Conversation Created                                   │
│ User ID: 550e8400-e29b-41d4-a716-446655440000             │
│ Conversation ID: 123e4567-e89b-12d3-a456-426614174000     │
╰────────────────────────────────────────────────────────────╯
```

**Copy these IDs!**

### 4. Access Session Data
In another terminal:

```bash
source .venv/bin/activate
python3 scripts/get_tree_session_data.py 550e8400-e29b-41d4-a716-446655440000 123e4567-e89b-12d3-a456-426614174000
```

Replace the IDs with the ones from your terminal output.

## What You Get

The script will output:

1. **Session Summary**
   - User ID, Conversation ID
   - Trees completed
   - Number of messages

2. **Tree Structure** 
   - The hierarchical decision tree (same as frontend visualization)
   - Branch and tool names

3. **Conversation History**
   - All user and assistant messages

4. **Tree Updates** 
   - Navigation path through the tree
   - Reasoning for each decision

5. **Decision History**
   - Tools called in order
   - Iterations of the decision tree

6. **JSON Export**
   - Saved to `tree_session_<user_id>_<conversation_id>.json`

## Example Terminal Output

### Input
```bash
$ python3 scripts/get_tree_session_data.py user_abc conv_123
```

### Output
```
Fetching session data for user 'user_abc', conversation 'conv_123'...
================================================================================

📊 SESSION SUMMARY
================================================================================
User ID: user_abc
Conversation ID: conv_123
Title: Troubleshooting Freezer
Trees completed: 2/5
Frontend payloads: 47
Tree updates: 12
Conversation messages: 18
Decision history iterations: 2

🌳 TREE STRUCTURE (for visualization)
================================================================================
📁 Base
  🔧 Query
  🔧 Aggregate
  🔧 Text Response

💬 CONVERSATION HISTORY
================================================================================
1. [USER]: Hello, what's the issue?
2. [ASSISTANT]: I'd like to understand the symptoms better...
3. [USER]: The refrigerator isn't cooling...
...

🔄 RECENT TREE UPDATES (navigation path)
================================================================================
1. base → query
   Reasoning: User is asking about system state...
2. query → aggregate
   Reasoning: Need to aggregate sensor data...
...

🎯 DECISION HISTORY
================================================================================
Iteration 1: query → retrieve_results
Iteration 2: aggregate → summarize

💾 Saving full data to: tree_session_user_abc_conv_123.json
✅ Done!
```

## Accessing Programmatically

If you want to use the data in your own Python code:

```python
import asyncio
from elysia.api.services.user import UserManager
from elysia.api.dependencies.common import get_user_manager

async def get_session_data():
    user_manager = get_user_manager()
    user = await user_manager.get_user_local("user_abc")
    tree = user["tree_manager"].get_tree("conv_123")
    
    # Tree structure (for visualization)
    print("Tree structure:", tree.tree)
    
    # Conversation history
    print("Messages:", tree.tree_data.conversation_history)
    
    # All frontend updates (tree navigation)
    print("Frontend updates:", tree.returner.store)
    
    # Filter just tree updates
    tree_updates = [
        p for p in tree.returner.store 
        if p.get("type") == "tree_update"
    ]
    print("Tree navigation:", tree_updates)
    
    # All retrieved objects from tools
    print("Environment:", tree.tree_data.environment.environment)
    
    # Tasks completed with reasoning
    print("Tasks:", tree.tree_data.tasks_completed)

asyncio.run(get_session_data())
```

## Troubleshooting

### "Tree not found" error
- Make sure you're using the correct user ID and conversation ID
- They should have been printed to the terminal when you started a new session
- Copy them exactly (including any hyphens or underscores)

### Terminal output not showing
- Check that Elysia is running with INFO logging (default)
- The output prints to `stdout` where Elysia was started
- Check the terminal where you ran `elysia start`

### IDs look different in different places
- **Frontend URL**: May use encoded versions or shortened IDs
- **Terminal output**: Shows the full, canonical ID
- **Use the terminal output IDs** - these are the correct ones for the API

## Next Steps

1. See [ACCESSING_TREE_SESSION_DATA.md](ACCESSING_TREE_SESSION_DATA.md) for detailed API access patterns
2. See [SESSION_ID_OUTPUT.md](SESSION_ID_OUTPUT.md) for what the terminal output looks like
3. Explore the JSON output file to understand session structure
4. Use the Python access patterns to integrate into your own code

## Tips

- **Always start with the script** - It shows you what data is available
- **Check the JSON file** - Useful for understanding the data structure
- **Copy IDs immediately** - They're only printed when the session is created
- **Use in combination** - Script for exploration, Python code for automation

