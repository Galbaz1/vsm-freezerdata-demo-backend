# Logging Configuration Changes - Summary

## Problem
The terminal was flooded with verbose logging output during:
- `elysia start` server startup
- Frontend chat interactions with the VSM agent

## Solution
Configured dual-handler logging:
1. **File handler**: ALL logs (DEBUG+) → `logs/elysia.log`
2. **Console handler**: Only important logs (INFO+) → Terminal

HTTP access logs are separately written to `logs/uvicorn.log`.

## Files Modified

### 1. `elysia/api/core/log.py`
**Changes:**
- Added `Path` import for logs directory management
- Created `LOGS_DIR` that auto-creates `logs/` folder
- Split logging handlers:
  - `FileHandler`: DEBUG level, writes to `logs/elysia.log`
  - `RichHandler` (console): INFO level, displays in terminal
- File format: `timestamp | logger_name | level | message`

**Key code:**
```python
file_handler = logging.FileHandler(LOGS_DIR / "elysia.log")
file_handler.setLevel(logging.DEBUG)

console_handler = RichHandler(rich_tracebacks=True, markup=True)
console_handler.setLevel(logging.INFO)

logging.basicConfig(handlers=[file_handler, console_handler])
```

### 2. `elysia/api/cli.py`
**Changes:**
- Added Uvicorn-specific logging configuration dictionary
- Configured Uvicorn to write to `logs/uvicorn.log`
- Uvicorn access logs isolated to file only (not console)
- Added `--log-level` option to `elysia start` command
- Added startup message showing where logs are being written

**New behavior:**
```bash
$ elysia start
📝 Logging to:
   logs/elysia.log (application logs)
   logs/uvicorn.log (HTTP access logs)
🖥️  Frontend: http://localhost:8000
```

**New option:**
```bash
elysia start --log-level debug     # Debug level in terminal
elysia start --log-level warning   # Only warnings and errors in terminal
```

## What Happens Now

### Terminal Output (Before)
- ❌ Thousands of lines per minute during startup
- ❌ Every request logged
- ❌ Every DSPy decision logged
- ❌ Every Weaviate query logged

### Terminal Output (After)
- ✅ Clean startup message
- ✅ Only errors and important info shown
- ✅ All details available in `logs/elysia.log`
- ✅ Optional: `--log-level debug` for verbose terminal output

## Usage

### Start the server with clean terminal
```bash
elysia start
```

### View all logs
```bash
tail -f logs/elysia.log
```

### View HTTP access logs
```bash
tail -f logs/uvicorn.log
```

### Find specific events
```bash
grep "ERROR\|WARNING" logs/elysia.log
grep "user_123" logs/elysia.log
grep "tool_name" logs/elysia.log
```

## Benefits

1. **Clean terminal** - Only critical information shown
2. **Complete audit trail** - All logs preserved in files
3. **Better debugging** - Logs are searchable and persistent
4. **No performance impact** - Logging to file is efficient
5. **Flexible control** - Adjust terminal verbosity with `--log-level`
6. **Session tracking** - Sessions also logged separately in `logs/sessions.jsonl`

## Log File Locations

```
logs/
├── elysia.log           # All application logs (DEBUG+)
├── uvicorn.log          # HTTP server logs (INFO+)
├── sessions.jsonl       # User/conversation session records
├── sessions/
│   ├── user_id_1/
│   │   ├── conversation_id_1_timestamp.json
│   │   └── conversation_id_2_timestamp.json
│   └── user_id_2/
│       └── ...
└── users/
    └── user_id_timestamp.json
```

## For Frontend Chat Sessions

When a user is chatting with the VSM agent in the frontend:
- Terminal remains clean ✅
- All conversation logs go to `logs/elysia.log` ✅
- Session metadata goes to `logs/sessions.jsonl` ✅
- HTTP requests go to `logs/uvicorn.log` ✅

To monitor in real-time:
```bash
tail -f logs/elysia.log | grep -i "query\|decision\|tool"
```

## Backward Compatibility

- Existing code works unchanged
- `logger.info()`, `logger.debug()`, etc. still work
- All loggers automatically use the new configuration
- No changes needed to application code

## Next Steps (Optional)

If needed, can add:
- Log rotation (automatic archive old logs)
- Structured logging (JSON format for parsing)
- Syslog integration
- Remote log aggregation

