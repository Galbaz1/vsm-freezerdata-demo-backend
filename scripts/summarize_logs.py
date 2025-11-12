#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "elysia" / "logs"
APP_LOG = LOG_DIR / "elysia.log"
UVICORN_LOG = LOG_DIR / "uvicorn.log"
OUT = LOG_DIR / "summary.md"

LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

log_line_re = re.compile(r"^(?P<ts>\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}[^|]*) \\| (?P<logger>[^|]+) \\| (?P<level>[^|]+) \\| (?P<msg>.*)$")
http_re = re.compile(r'"(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) (?P<path>[^ ]+) [^"]+" (?P<status>\\d{3})')

def read_lines(path: Path):
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except Exception:
        return []

def parse_counts(lines):
    by_level = Counter()
    by_logger = Counter()
    recent_warnings = Counter()
    recent_errors = Counter()
    for line in lines:
        m = log_line_re.match(line.strip())
        if not m:
            continue
        level = m.group("level").strip()
        logger = m.group("logger").strip()
        msg = m.group("msg").strip()
        by_level[level] += 1
        by_logger[logger] += 1
        if level == "WARNING":
            recent_warnings[msg] += 1
        elif level in ("ERROR", "CRITICAL"):
            recent_errors[msg] += 1
    return by_level, by_logger, recent_warnings, recent_errors

def parse_http(lines):
    by_status = Counter()
    by_path = Counter()
    for line in lines:
        m = http_re.search(line)
        if not m:
            continue
        status = m.group("status")
        path = m.group("path")
        by_status[status] += 1
        # collapse dynamic ids
        path_norm = re.sub(r"/[0-9a-fA-F\\-]{8,}", "/:id", path)
        by_path[path_norm] += 1
    return by_status, by_path

def section(title):
    return f"### {title}\\n\\n"

def top_items(counter: Counter, n=10):
    return "\\n".join(f"- {k} ×{v}" for k, v in counter.most_common(n)) or "_None_"

def write_summary(app_lines, uv_lines):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    app_lv, app_loggers, app_warn, app_err = parse_counts(app_lines)
    http_status, http_paths = parse_http(uv_lines)

    chunks = []
    chunks.append(f"# Log Summary ({now})\\n")

    chunks.append(section("Levels (application log)"))
    chunks.append(top_items(app_lv, 10) + "\\n")

    chunks.append(section("Top loggers (application log)"))
    chunks.append(top_items(app_loggers, 10) + "\\n")

    chunks.append(section("Recent warnings (deduped)"))
    chunks.append(top_items(app_warn, 10) + "\\n")

    chunks.append(section("Recent errors (deduped)"))
    chunks.append(top_items(app_err, 10) + "\\n")

    chunks.append(section("HTTP status counts"))
    chunks.append(top_items(http_status, 10) + "\\n")

    chunks.append(section("Top endpoints (normalized)"))
    chunks.append(top_items(http_paths, 10) + "\\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\\n".join(chunks), encoding="utf-8")
    print(f"Wrote {OUT}")

def main():
    app_lines = read_lines(APP_LOG)
    uv_lines = read_lines(UVICORN_LOG)
    write_summary(app_lines, uv_lines)

if __name__ == "__main__":
    main()


