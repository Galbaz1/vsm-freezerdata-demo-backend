#!/usr/bin/env python3
"""
View and query session logs.

Provides utilities for viewing, filtering, and analyzing session logs stored
in the logs/ directory.

Usage:
    python3 scripts/view_session_logs.py --list-users
    python3 scripts/view_session_logs.py --user <user_id>
    python3 scripts/view_session_logs.py --recent <n>
    python3 scripts/view_session_logs.py --summary
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse


def load_sessions_log() -> List[Dict[str, Any]]:
    """Load all sessions from the global sessions log."""
    sessions_log = Path("logs/sessions.jsonl")
    sessions = []
    
    if not sessions_log.exists():
        print("No sessions log found at logs/sessions.jsonl")
        return sessions
    
    with open(sessions_log, "r") as f:
        for line in f:
            if line.strip():
                sessions.append(json.loads(line))
    
    return sessions


def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def print_session(session: Dict[str, Any], include_log_file: bool = True):
    """Print a formatted session entry."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    if session["event_type"] == "user_session":
        status_color = "green" if session["status"] == "new_user" else "blue"
        status_text = "👤 New User" if session["status"] == "new_user" else "👤 Returning User"
        
        console.print(f"\n[{status_color}]{status_text}[/]")
        console.print(f"  User ID:  {session['user_id']}")
        console.print(f"  Time:     {format_timestamp(session['timestamp'])}")
        if include_log_file:
            console.print(f"  Log:      {session['log_file']}")
    
    elif session["event_type"] == "conversation_session":
        status_color = "green" if session["status"] == "new_conversation" else "blue"
        status_text = "💬 New Conversation" if session["status"] == "new_conversation" else "💬 Resumed Conversation"
        
        console.print(f"\n[{status_color}]{status_text}[/]")
        console.print(f"  User ID:         {session['user_id']}")
        console.print(f"  Conversation ID: {session['conversation_id']}")
        console.print(f"  Time:            {format_timestamp(session['timestamp'])}")
        if include_log_file:
            console.print(f"  Log:             {session['log_file']}")
        console.print(f"  [cyan]Access:          {session['access_command']}[/cyan]")


def cmd_list_users(sessions: List[Dict[str, Any]]):
    """List all unique users."""
    from rich.console import Console
    
    console = Console()
    users = {}
    
    for session in sessions:
        user_id = session["user_id"]
        if user_id not in users:
            users[user_id] = {"count": 0, "first_seen": session["timestamp"], "last_seen": session["timestamp"]}
        
        users[user_id]["count"] += 1
        if session["timestamp"] > users[user_id]["last_seen"]:
            users[user_id]["last_seen"] = session["timestamp"]
    
    if not users:
        console.print("[yellow]No sessions found[/]")
        return
    
    console.print(f"\n[bold]Users ({len(users)})[/bold]\n")
    
    for user_id, info in sorted(users.items()):
        console.print(f"  {user_id}")
        console.print(f"    Sessions: {info['count']}")
        console.print(f"    First:    {format_timestamp(info['first_seen'])}")
        console.print(f"    Last:     {format_timestamp(info['last_seen'])}\n")


def cmd_user_sessions(sessions: List[Dict[str, Any]], user_id: str):
    """Show all sessions for a specific user."""
    from rich.console import Console
    
    console = Console()
    user_sessions = [s for s in sessions if s["user_id"] == user_id]
    
    if not user_sessions:
        console.print(f"[yellow]No sessions found for user: {user_id}[/]")
        return
    
    console.print(f"\n[bold]Sessions for user: {user_id}[/bold]")
    
    for session in user_sessions:
        print_session(session, include_log_file=False)
    
    console.print()


def cmd_recent_sessions(sessions: List[Dict[str, Any]], count: int = 10):
    """Show most recent sessions."""
    from rich.console import Console
    
    console = Console()
    recent = sorted(sessions, key=lambda s: s["timestamp"], reverse=True)[:count]
    
    if not recent:
        console.print("[yellow]No sessions found[/]")
        return
    
    console.print(f"\n[bold]Last {min(count, len(sessions))} sessions[/bold]")
    
    for session in recent:
        print_session(session, include_log_file=False)
    
    console.print()


def cmd_summary(sessions: List[Dict[str, Any]]):
    """Print summary statistics."""
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    if not sessions:
        console.print("[yellow]No sessions found[/]")
        return
    
    # Count statistics
    unique_users = len(set(s["user_id"] for s in sessions))
    new_users = len([s for s in sessions if s["event_type"] == "user_session" and s["status"] == "new_user"])
    returning_users = len([s for s in sessions if s["event_type"] == "user_session" and s["status"] == "returning_user"])
    new_conversations = len([s for s in sessions if s["event_type"] == "conversation_session" and s["status"] == "new_conversation"])
    resumed_conversations = len([s for s in sessions if s["event_type"] == "conversation_session" and s["status"] == "resumed_conversation"])
    
    # Time range
    earliest = min(sessions, key=lambda s: s["timestamp"])["timestamp"]
    latest = max(sessions, key=lambda s: s["timestamp"])["timestamp"]
    
    # Today's stats
    today = datetime.now().date().isoformat()
    today_sessions = [s for s in sessions if s["timestamp"].startswith(today)]
    
    summary_text = f"""
[bold]Session Statistics[/bold]

[yellow]Overall[/yellow]
  Total sessions:     {len(sessions)}
  Unique users:       {unique_users}
  Date range:         {format_timestamp(earliest)} to {format_timestamp(latest)}

[yellow]User Sessions[/yellow]
  New users:          {new_users}
  Returning users:    {returning_users}

[yellow]Conversations[/yellow]
  New conversations:  {new_conversations}
  Resumed:            {resumed_conversations}

[yellow]Today[/yellow]
  Sessions today:     {len(today_sessions)}
"""
    
    console.print(Panel(summary_text.strip(), border_style="cyan", padding=(1, 2)))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View and query session logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/view_session_logs.py --list-users
  python3 scripts/view_session_logs.py --user <user_id>
  python3 scripts/view_session_logs.py --recent 20
  python3 scripts/view_session_logs.py --summary
        """
    )
    
    parser.add_argument(
        "--list-users",
        action="store_true",
        help="List all users and their session counts"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        help="Show all sessions for a specific user"
    )
    
    parser.add_argument(
        "--recent",
        type=int,
        nargs="?",
        const=10,
        help="Show N most recent sessions (default: 10)"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics"
    )
    
    args = parser.parse_args()
    
    # Load all sessions
    sessions = load_sessions_log()
    
    if not sessions:
        print("No sessions found. Start Elysia and create a conversation.")
        sys.exit(1)
    
    # Execute command
    if args.list_users:
        cmd_list_users(sessions)
    elif args.user:
        cmd_user_sessions(sessions, args.user)
    elif args.recent is not None:
        cmd_recent_sessions(sessions, args.recent)
    elif args.summary:
        cmd_summary(sessions)
    else:
        # Default: show summary
        cmd_summary(sessions)


if __name__ == "__main__":
    main()

