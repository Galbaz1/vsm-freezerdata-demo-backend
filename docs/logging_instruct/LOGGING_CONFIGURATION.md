# Logging Configuration

## Overview

The application now writes detailed logs to files in the `logs/` folder instead of flooding the terminal. The terminal displays only important information (startup messages and errors), while all debug and info logs are written to files.

## Log Files

When you run `elysia start`, logs are written to:

- **`logs/elysia.log`** - All application logs (DEBUG and above)
- **`logs/uvicorn.log`** - HTTP access and server logs (INFO and above)

## Terminal Output

The terminal will show:
- Startup information (including where logs are being written)
- Error messages (ERROR and CRITICAL level only)
- Minimal INFO messages from the server

## Usage

### Start with Default Settings

```bash
elysia start
```

This starts the server with:
- Host: `localhost`
- Port: `8000`
- Reload: `True` (auto-reload on file changes)
- Log level for console: `info` (only shows INFO, WARNING, ERROR, CRITICAL in terminal)

### Adjust Log Level for Terminal

To see more verbose output in the terminal (DEBUG level):

```bash
elysia start --log-level debug
```

To see less output (WARNING level only):

```bash
elysia start --log-level warning
```

Available levels: `debug`, `info`, `warning`, `error`

### View Logs in Real-Time

**Watch application logs:**

```bash
tail -f logs/elysia.log
```

**Watch HTTP access logs:**

```bash
tail -f logs/uvicorn.log
```

**Watch both simultaneously:**

```bash
tail -f logs/elysia.log logs/uvicorn.log
```

### Search Logs

**Find errors:**

```bash
grep ERROR logs/elysia.log
```

**Find a specific user's activity:**

```bash
grep "user_id" logs/elysia.log
```

**Find logs from a specific time:**

```bash
grep "2024-11-12 14:" logs/elysia.log
```

## Log Format

All logs follow this format:

```
2024-11-12 14:30:45,123 | elysia.api.app | INFO | Health check requested
```

Components:
- **Timestamp**: `YYYY-MM-DD HH:MM:SS,ms`
- **Logger name**: Module/component that logged the message
- **Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Message**: The log message

## During Frontend Chat

When using the VSM agent in the frontend, the terminal stays clean. All:
- Query processing logs
- Tool execution logs
- LLM interaction logs
- WebSocket message logs

...are written to `logs/elysia.log`.

To follow what's happening in real-time:

```bash
tail -f logs/elysia.log | grep "tool\|query\|decision"
```

## Log Retention

Logs append to the same files across sessions. To start fresh:

```bash
rm logs/elysia.log logs/uvicorn.log
```

Or manually archive old logs:

```bash
mkdir -p logs/archive
mv logs/elysia.log logs/archive/elysia_$(date +%Y%m%d_%H%M%S).log
```

## Troubleshooting

### Logs not appearing

1. Check that `logs/` directory exists:
   ```bash
   ls -la logs/
   ```

2. Check permissions:
   ```bash
   touch logs/test.txt && rm logs/test.txt
   ```

3. Restart the server

### Terminal still flooded

Make sure you're running the latest code. The logging configuration is in `elysia/api/cli.py`.

### Finding specific events

All session events are also logged to `logs/sessions.jsonl` and structured session files in `logs/sessions/` (created by the application).

## Frontend Configuration

The frontend doesn't generate terminal output directly. However, you can monitor:

1. **HTTP traffic**: Check `logs/uvicorn.log` for all requests and responses
2. **WebSocket messages**: Check `logs/elysia.log` for query processing
3. **LLM interactions**: Check `logs/elysia.log` for DSPy/model logs

