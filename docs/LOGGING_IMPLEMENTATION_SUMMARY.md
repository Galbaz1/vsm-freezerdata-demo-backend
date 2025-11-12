# Session Logging Implementation Summary

## Changes Made

### 1. **New Session Logger Utility** (`elysia/api/utils/session_logger.py`)

- **SessionLogger class** with methods:
  - `log_user_session()` - Log user initialization
  - `log_conversation_session()` - Log conversation initialization
  - `print_session_location()` - Print minimal terminal info
  - `get_session_info()` - Retrieve session info
  - `get_all_sessions()` - Query all sessions

- **Features:**
  - JSON-based logging
  - Organized file structure by user and conversation
  - Global append-only `sessions.jsonl` for audit trail
  - Ready-to-use access commands included in logs

### 2. **Updated API Routes** (`elysia/api/routes/init.py`)

**`POST /init/user/{user_id}`**
- Now calls `session_logger.log_user_session()`
- Prints minimal terminal info showing log location

**`POST /init/tree/{user_id}/{conversation_id}`**
- Now calls `session_logger.log_conversation_session()`
- Prints minimal terminal info with access command

### 3. **New Log Viewer Script** (`scripts/view_session_logs.py`)

Provides utilities for analyzing logs:
- `--list-users` - Show all users
- `--user <id>` - Show sessions for a user
- `--recent <n>` - Show recent sessions
- `--summary` - Show statistics

### 4. **Git Configuration** (`.gitignore`)

Added:
```
logs/
logs/**
```

## File Structure

```
logs/
├── sessions.jsonl              # Global audit log (append-only)
├── users/                      # User session logs
│   └── {user_id}_{timestamp}.json
└── sessions/                   # Conversation logs
    └── {user_id}/
        └── {conversation_id}_{timestamp}.json
```

## Terminal Output

**Before:**
```
[Cluttered with colored panels]
```

**After:**
```
💬 Conversation
New conversation created
User:         user_abc
Conversation: conv_123
Log:          logs/sessions/user_abc/conv_123_20250112_120030.json
Access:       python3 scripts/get_tree_session_data.py user_abc conv_123
```

Minimal, focused, informative.

## Log Entry Format

### User Session
```json
{
  "timestamp": "2025-01-12T12:00:00.123456",
  "event_type": "user_session",
  "status": "new_user",
  "user_id": "user_123",
  "log_file": "logs/users/user_123_20250112_120000.json"
}
```

### Conversation Session
```json
{
  "timestamp": "2025-01-12T12:00:30.654321",
  "event_type": "conversation_session",
  "status": "new_conversation",
  "user_id": "user_123",
  "conversation_id": "conv_456",
  "log_file": "logs/sessions/user_123/conv_456_20250112_120030.json",
  "access_command": "python3 scripts/get_tree_session_data.py user_123 conv_456"
}
```

## Usage Workflow

1. **Start Elysia**
   ```bash
   elysia start
   ```

2. **Open Frontend**
   - Terminal shows minimal info with log location

3. **Access Session Data**
   ```bash
   # Copy command from terminal or log file
   python3 scripts/get_tree_session_data.py user_123 conv_456
   ```

4. **Query Logs**
   ```bash
   # View all users
   python3 scripts/view_session_logs.py --list-users
   
   # View statistics
   python3 scripts/view_session_logs.py --summary
   ```

## Benefits

✅ **Clean Terminal** - Focused output, no log spam
✅ **Complete Audit Trail** - All sessions recorded
✅ **Organized Structure** - Easy to navigate and query
✅ **Ready-to-Run Commands** - Access commands in log files
✅ **Timestamped** - All events dated and timed
✅ **Git-Ignored** - Logs not committed to version control
✅ **Queryable** - JSON and JSONL formats for analysis

## Database Queries

### Show all sessions
```bash
cat logs/sessions.jsonl | jq '.'
```

### Find sessions for a user
```bash
cat logs/sessions.jsonl | jq '.[] | select(.user_id == "user_123")'
```

### Count sessions by type
```bash
cat logs/sessions.jsonl | jq -r '.event_type' | sort | uniq -c
```

### Find all new conversations today
```bash
cat logs/sessions.jsonl | jq '.[] | select(.event_type == "conversation_session" and .status == "new_conversation" and .timestamp | startswith("2025-01-12"))'
```

## Code Integration

### Using SessionLogger in Your Code

```python
from elysia.api.utils.session_logger import get_session_logger

session_logger = get_session_logger()

# Log user session
log_entry = session_logger.log_user_session("user_123", is_new=True)
session_logger.print_session_location(log_entry)

# Log conversation session
log_entry = session_logger.log_conversation_session("user_123", "conv_456", is_new=True)
session_logger.print_session_location(log_entry)

# Get session info
info = session_logger.get_session_info("user_123", "conv_456")
print(info["access_command"])  # Ready-to-use command
```

## Backward Compatibility

- No breaking changes to existing API
- All endpoints work the same
- Only addition is logging side effect
- Terminal output is cleaner (improvement)

## Documentation

- **[SESSION_LOGGING_QUICK_START.md](SESSION_LOGGING_QUICK_START.md)** - Getting started guide
- **[SESSION_LOGGING_GUIDE.md](SESSION_LOGGING_GUIDE.md)** - Detailed documentation
- **[ACCESSING_TREE_SESSION_DATA.md](ACCESSING_TREE_SESSION_DATA.md)** - How to access session data

## Testing

All new utilities tested for:
- Directory creation
- File writing
- JSON serialization
- Terminal output
- Query functionality

## Next Steps

1. Deploy the changes
2. Monitor logs directory growth
3. Consider archiving old logs periodically
4. Analyze session patterns using provided tools

## Notes

- Session logs are append-only by nature
- Recommend periodic archival of `sessions.jsonl`
- Log files are human-readable JSON
- All timestamps in ISO 8601 format
- Ready-to-use access commands included in every log

