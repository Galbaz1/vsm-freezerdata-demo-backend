# Logging - Quick Start

## TL;DR

✅ **Terminal is now clean** - Logs go to `logs/` folder instead

## Start the Server

```bash
elysia start
```

That's it! The terminal will show only startup info and errors.

## View Logs

```bash
# Follow application logs in real-time
tail -f logs/elysia.log

# Follow HTTP requests
tail -f logs/uvicorn.log

# Search for errors
grep ERROR logs/elysia.log

# Search for a specific user
grep "user_123" logs/elysia.log
```

## Options

```bash
# Debug level in terminal (verbose)
elysia start --log-level debug

# Warning level in terminal (minimal)
elysia start --log-level warning

# Different port
elysia start --port 8080
```

## Log Files

- `logs/elysia.log` - All application logs
- `logs/uvicorn.log` - HTTP access logs
- `logs/sessions.jsonl` - Session records
- `logs/sessions/` - Detailed session files

## That's it!

No more flooded terminal during frontend chat. ✨

For detailed info, see: [docs/LOGGING_CONFIGURATION.md](docs/LOGGING_CONFIGURATION.md)

