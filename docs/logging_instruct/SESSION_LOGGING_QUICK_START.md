# Session Logging Quick Start

Elysia automatically logs all user and conversation sessions to the `logs/` directory, keeping your terminal clean while maintaining a complete audit trail.

## What Happens Automatically

When you start a conversation in the frontend:

1. **Terminal shows:** Minimal info panel (~2 lines)
2. **Logs directory creates:** Detailed JSON log file
3. **Global log updated:** Entry added to `logs/sessions.jsonl`
4. **Access command provided:** Ready-to-copy command to get session data

## Example Terminal Output

```
💬 Conversation
New conversation created
User:         user_abc
Conversation: conv_123
Log:          logs/sessions/user_abc/conv_123_20250112_120030.json
Access:       python3 scripts/get_tree_session_data.py user_abc conv_123
```

That's it! Clean, focused, informative.

## Finding Your Sessions

### View all users
```bash
python3 scripts/view_session_logs.py --list-users
```

Output:
```
Users (3)

  user_abc
    Sessions: 5
    First:    2025-01-12 12:00:00
    Last:     2025-01-12 14:30:45

  user_xyz
    Sessions: 2
    First:    2025-01-12 13:15:00
    Last:     2025-01-12 13:45:30
```

### View sessions for a user
```bash
python3 scripts/view_session_logs.py --user user_abc
```

### View recent sessions
```bash
python3 scripts/view_session_logs.py --recent 20
```

### View summary statistics
```bash
python3 scripts/view_session_logs.py --summary
```

Output:
```
Session Statistics

Overall
  Total sessions:     47
  Unique users:       8
  Date range:         2025-01-12 12:00:00 to 2025-01-12 15:45:23

User Sessions
  New users:          3
  Returning users:    12

Conversations
  New conversations:  32
  Resumed:            5

Today
  Sessions today:     47
```

## Log File Locations

### User sessions
```
logs/users/
├── user_abc_20250112_120000.json
├── user_abc_20250112_140530.json
└── user_xyz_20250112_131500.json
```

### Conversation sessions
```
logs/sessions/
├── user_abc/
│   ├── conv_123_20250112_120030.json
│   ├── conv_456_20250112_125000.json
│   └── conv_789_20250112_143045.json
└── user_xyz/
    └── conv_999_20250112_131530.json
```

### Global audit log
```
logs/sessions.jsonl  # One entry per line (append-only)
```

## Accessing Session Data

The log files contain the command needed:

```bash
# From log file:
# "access_command": "python3 scripts/get_tree_session_data.py user_abc conv_123"

# Run it:
python3 scripts/get_tree_session_data.py user_abc conv_123
```

This gives you:
- Tree structure (for visualization)
- Conversation history
- Decision history (navigation path)
- Environment (retrieved objects)
- And saves full data to JSON

## Querying Logs Programmatically

### Find all new users today
```bash
cat logs/sessions.jsonl | jq '.[] | select(.event_type == "user_session" and .status == "new_user" and .timestamp | startswith("2025-01-12"))'
```

### Find all conversations for a user
```bash
cat logs/sessions.jsonl | jq '.[] | select(.event_type == "conversation_session" and .user_id == "user_abc")'
```

### Count sessions per user
```bash
cat logs/sessions.jsonl | jq '.user_id' -r | sort | uniq -c
```

## In Python

```python
from pathlib import Path
import json

# Load all sessions
sessions_log = Path("logs/sessions.jsonl")
sessions = []

with open(sessions_log) as f:
    for line in f:
        if line.strip():
            sessions.append(json.loads(line))

# Analyze
new_conversations = [s for s in sessions 
                    if s["event_type"] == "conversation_session" 
                    and s["status"] == "new_conversation"]
print(f"New conversations today: {len(new_conversations)}")

# Get access command
conv = new_conversations[0]
print(conv["access_command"])
```

## Log File Format

### User Session
```json
{
  "timestamp": "2025-01-12T12:00:00.123456",
  "event_type": "user_session",
  "status": "new_user",
  "user_id": "user_abc",
  "log_file": "logs/users/user_abc_20250112_120000.json"
}
```

### Conversation Session
```json
{
  "timestamp": "2025-01-12T12:00:30.654321",
  "event_type": "conversation_session",
  "status": "new_conversation",
  "user_id": "user_abc",
  "conversation_id": "conv_123",
  "log_file": "logs/sessions/user_abc/conv_123_20250112_120030.json",
  "access_command": "python3 scripts/get_tree_session_data.py user_abc conv_123"
}
```

## Benefits

✅ **Clean Terminal** - No cluttered output
✅ **Complete Logging** - All sessions recorded
✅ **Audit Trail** - Full history in `sessions.jsonl`
✅ **Easy Querying** - JSON and JSONL formats
✅ **Organized** - Structured by user and conversation
✅ **Timestamped** - All events dated and timed
✅ **Ready Commands** - Access commands included

## Common Tasks

### Get IDs from frontend
- Open frontend and create conversation
- Look for minimal info panel in terminal
- Copy the access command

### Access full session data
```bash
python3 scripts/get_tree_session_data.py <user_id> <conversation_id>
```

### Check how many conversations a user has
```bash
python3 scripts/view_session_logs.py --user <user_id> | grep -c "Conversation"
```

### List all sessions from last hour
```bash
# Using jq to filter by timestamp
cat logs/sessions.jsonl | jq 'select(.timestamp > now - 3600)'
```

### Export all sessions to CSV
```bash
python3 scripts/view_session_logs.py --summary
# Then import logs/sessions.jsonl into your analysis tool
```

## Notes

- Logs directory is in `.gitignore` and won't be committed
- Each session gets its own timestamped file
- Global `sessions.jsonl` can grow large; you can archive it
- Access commands are ready to copy from log files
- All timestamps are ISO format (easily parseable)

For detailed logging configuration, see [SESSION_LOGGING_GUIDE.md](SESSION_LOGGING_GUIDE.md)

