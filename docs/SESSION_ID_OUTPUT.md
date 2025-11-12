# Session ID Output

When you start a new session in Elysia, the User ID and Conversation ID are now printed clearly to the terminal in an easy-to-read format.

## What You'll See

### When Starting a New User Session

```
╭─────────────────────────────────────────╮
│          Session Started                │
│                                         │
│ New User Created                        │
│ User ID: user_12345                     │
╰─────────────────────────────────────────╯
```

### When Resuming an Existing User Session

```
╭─────────────────────────────────────────╮
│          Session Resumed                │
│                                         │
│ User Session Restored                   │
│ User ID: user_12345                     │
╰─────────────────────────────────────────╯
```

### When Creating a New Conversation

```
╭────────────────────────────────────────────────────────────╮
│              New Session                                   │
│                                                            │
│ New Conversation Created                                   │
│ User ID: user_12345                                        │
│ Conversation ID: conv_67890                                │
╰────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────╮
│ Get session data:                                          │
│ python3 scripts/get_tree_session_data.py user_12345 conv  │
╰────────────────────────────────────────────────────────────╯
```

### When Resuming an Existing Conversation

```
╭────────────────────────────────────────────────────────────╮
│             Existing Session                               │
│                                                            │
│ Conversation Resumed                                       │
│ User ID: user_12345                                        │
│ Conversation ID: conv_67890                                │
╰────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────╮
│ Get session data:                                          │
│ python3 scripts/get_tree_session_data.py user_12345 conv  │
╰────────────────────────────────────────────────────────────╯
```

## Where These IDs Are Used

These IDs can be used in multiple ways:

### 1. **Command Line Access**

```bash
# Get session data programmatically
python3 scripts/get_tree_session_data.py user_12345 conv_67890
```

This will output:
- Tree structure (for visualization)
- Conversation history
- Decision history (navigation path through tree)
- All frontend payloads
- And save to JSON file

### 2. **In Your Python Code**

```python
from elysia.api.services.user import UserManager
from elysia.api.dependencies.common import get_user_manager

user_manager = get_user_manager()
user = await user_manager.get_user_local("user_12345")
tree = user["tree_manager"].get_tree("conv_67890")

# Access tree data
print(tree.tree)  # Tree structure
print(tree.returner.store)  # Frontend payloads
```

### 3. **In Frontend URLs**

The frontend uses these IDs in the URL:
- `http://localhost:8000?user_id=user_12345&conversation_id=conv_67890`

## Copying the IDs

The output is printed clearly so you can easily:
1. **Copy the User ID** - printed with the user session
2. **Copy the Conversation ID** - printed with each tree/conversation initialization
3. **Copy the suggested command** - ready to paste for accessing session data

## When This Appears

- **User ID**: Printed when the frontend calls `/init/user/{user_id}`
  - Usually when opening the frontend for the first time
  - Or when logging in as a new user

- **Conversation ID**: Printed when the frontend calls `/init/tree/{user_id}/{conversation_id}`
  - When creating a new conversation
  - When resuming an existing conversation
  - Every time you switch conversations

## Example Workflow

1. Open frontend → See user ID printed
2. Start new conversation → See conversation ID printed
3. Copy and run the suggested command to access session data:
   ```bash
   python3 scripts/get_tree_session_data.py user_12345 conv_67890
   ```

This gives you immediate access to all session data programmatically!

