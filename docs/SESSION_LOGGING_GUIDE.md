# Session Logging Guide

Elysia now maintains a clean terminal while creating detailed session logs in the `logs/` directory. This keeps your workspace organized and provides a complete audit trail of all sessions.

## Overview

**Terminal:** Only shows minimal, essential information
**Logs:** Complete, structured session data saved to files

## Log Directory Structure

```
logs/
├── sessions.jsonl              # Global log of all sessions (append-only)
├── users/                      # User session logs
│   ├── user_id_1_20250112_120000.json
│   └── user_id_2_20250112_120530.json
└── sessions/                   # Conversation session logs
    ├── user_id_1/
    │   ├── conv_id_1_20250112_120030.json
    │   └── conv_id_2_20250112_125000.json
    └── user_id_2/
        └── conv_id_3_20250112_120530.json
```

## Terminal Output

When you initialize a session, you'll see minimal output showing where the log was written:

```
👤 User Session
New user created
Logged to: logs/users/user_abc_20250112_120000.json

💬 Conversation
New conversation created
User:         user_abc
Conversation: conv_123
Log:          logs/sessions/user_abc/conv_123_20250112_120030.json
Access:       python3 scripts/get_tree_session_data.py user_abc conv_123
```

This is much cleaner than the previous approach, keeping your terminal focused on actual application output.

## Log File Contents

### User Session Log

**File:** `logs/users/user_id_<timestamp>.json`

```json
{
  "timestamp": "2025-01-12T12:00:00.123456",
  "event_type": "user_session",
  "status": "new_user",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "log_file": "logs/users/550e8400-e29b-41d4-a716-446655440000_20250112_120000.json"
}
```

### Conversation Session Log

**File:** `logs/sessions/user_id/conversation_id_<timestamp>.json`

```json
{
  "timestamp": "2025-01-12T12:00:30.654321",
  "event_type": "conversation_session",
  "status": "new_conversation",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "log_file": "logs/sessions/550e8400-e29b-41d4-a716-446655440000/123e4567-e89b-12d3-a456-426614174000_20250112_120030.json",
  "access_command": "python3 scripts/get_tree_session_data.py 550e8400-e29b-41d4-a716-446655440000 123e4567-e89b-12d3-a456-426614174000"
}
```

### Global Sessions Log

**File:** `logs/sessions.jsonl`

Append-only log with one JSON entry per line. Useful for auditing all sessions:

```jsonl
{"timestamp": "2025-01-12T12:00:00.123456", "event_type": "user_session", "status": "new_user", "user_id": "550e8400-e29b-41d4-a716-446655440000", "log_file": "logs/users/550e8400-e29b-41d4-a716-446655440000_20250112_120000.json"}
{"timestamp": "2025-01-12T12:00:30.654321", "event_type": "conversation_session", "status": "new_conversation", "user_id": "550e8400-e29b-41d4-a716-446655440000", "conversation_id": "123e4567-e89b-12d3-a456-426614174000", "log_file": "logs/sessions/550e8400-e29b-41d4-a716-446655440000/123e4567-e89b-12d3-a456-426614174000_20250112_120030.json", "access_command": "python3 scripts/get_tree_session_data.py 550e8400-e29b-41d4-a716-446655440000 123e4567-e89b-12d3-a456-426614174000"}
```

## Using the Logs

### Querying All Sessions

```bash
# View all sessions (pretty-printed)
cat logs/sessions.jsonl | jq '.'

# Find sessions for a specific user
cat logs/sessions.jsonl | jq 'select(.user_id == "user_abc")'

# Find sessions from today
cat logs/sessions.jsonl | jq 'select(.timestamp | startswith("2025-01-12"))'

# List all conversations for a user
ls logs/sessions/user_abc/
```

### Accessing Session Data

The log files include the access command needed to get full session data:

```bash
# From the log file
python3 scripts/get_tree_session_data.py 550e8400-e29b-41d4-a716-446655440000 123e4567-e89b-12d3-a456-426614174000
```

### Analyzing Session Logs

```python
import json
from pathlib import Path

# Read all sessions
sessions_log = Path("logs/sessions.jsonl")
sessions = []

with open(sessions_log) as f:
    for line in f:
        if line.strip():
            sessions.append(json.loads(line))

# Find user's sessions
user_sessions = [s for s in sessions if s["user_id"] == "user_abc"]
print(f"User has {len(user_sessions)} sessions")

# Find recent conversations
conversations = [s for s in sessions if s["event_type"] == "conversation_session"]
print(f"Total conversations: {len(conversations)}")
```

## Implementation

### SessionLogger Class

Located in `elysia/api/utils/session_logger.py`, provides:

- **`log_user_session(user_id, is_new)`** - Log user initialization
- **`log_conversation_session(user_id, conversation_id, is_new)`** - Log conversation initialization
- **`get_session_info(user_id, conversation_id)`** - Retrieve session info from log file
- **`get_all_sessions(user_id)`** - Get all sessions from global log
- **`print_session_location(log_entry)`** - Print minimal terminal output

### Usage in Code

```python
from elysia.api.utils.session_logger import get_session_logger

session_logger = get_session_logger()

# Log a new user session
log_entry = session_logger.log_user_session("user_123", is_new=True)
session_logger.print_session_location(log_entry)

# Log a new conversation
log_entry = session_logger.log_conversation_session("user_123", "conv_456", is_new=True)
session_logger.print_session_location(log_entry)

# Get session info
info = session_logger.get_session_info("user_123", "conv_456")
print(info["access_command"])  # Get the command to access session data
```

## Benefits

✅ **Clean Terminal** - Only essential information displayed  
✅ **Complete Audit Trail** - All sessions logged to files  
✅ **Easy Querying** - JSONL format allows filtering and analysis  
✅ **Structured Organization** - Logs organized by user and conversation  
✅ **Timestamps** - All events timestamped for correlation  
✅ **Access Commands** - Logs include ready-to-run commands  
✅ **Git-Ignored** - Logs directory not committed to version control  

## Workflow

1. **Start Elysia**
   ```bash
   elysia start
   ```

2. **Open Frontend**
   ```
   http://localhost:8000
   ```

3. **Terminal shows minimal output**
   ```
   💬 Conversation
   New conversation created
   User:         user_abc
   Conversation: conv_123
   Log:          logs/sessions/user_abc/conv_123_20250112_120030.json
   Access:       python3 scripts/get_tree_session_data.py user_abc conv_123
   ```

4. **Access Session Data**
   ```bash
   python3 scripts/get_tree_session_data.py user_abc conv_123
   ```

5. **Query Logs for Audit**
   ```bash
   cat logs/sessions.jsonl | jq '.[] | select(.status == "new_conversation")'
   ```

## Notes

- Logs are created in a `logs/` directory at the project root
- The `logs/` directory is in `.gitignore` and not committed
- Each session gets its own timestamped log file
- Global `sessions.jsonl` provides complete audit trail
- Minimal terminal output keeps stdout clean for application messages

