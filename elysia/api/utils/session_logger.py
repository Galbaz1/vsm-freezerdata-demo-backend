"""
Session logging utility for tracking user and conversation sessions.

Creates structured log files in the logs/ directory, keeping the terminal clean
and maintaining a complete audit trail of all sessions.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class SessionLogger:
    """Logs session information to structured JSON files in logs/ directory."""
    
    LOG_DIR = Path(__file__).parent.parent.parent / "logs"
    SESSIONS_LOG = LOG_DIR / "sessions.jsonl"
    
    def __init__(self):
        """Initialize the session logger."""
        self.log_dir = self.LOG_DIR
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Ensure logs directory exists."""
        self.log_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_session_log_path(self, user_id: str, conversation_id: Optional[str] = None) -> Path:
        """Generate a log file path for a session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if conversation_id:
            # Conversation log: logs/sessions/user_id/conversation_id_timestamp.json
            session_dir = self.log_dir / "sessions" / user_id
            session_dir.mkdir(exist_ok=True, parents=True)
            filename = f"{conversation_id}_{timestamp}.json"
            return session_dir / filename
        else:
            # User log: logs/users/user_id_timestamp.json
            user_dir = self.log_dir / "users"
            user_dir.mkdir(exist_ok=True, parents=True)
            filename = f"{user_id}_{timestamp}.json"
            return user_dir / filename
    
    def log_user_session(
        self,
        user_id: str,
        is_new: bool = False,
    ) -> Dict[str, Any]:
        """Log a user session initialization.
        
        Args:
            user_id: The user ID
            is_new: Whether this is a new user or returning
            
        Returns:
            Dictionary containing log file path and session info
        """
        log_path = self._get_session_log_path(user_id)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "user_session",
            "status": "new_user" if is_new else "returning_user",
            "user_id": user_id,
            "log_file": str(log_path),
        }
        
        # Write to user session log
        with open(log_path, "w") as f:
            json.dump(log_entry, f, indent=2)
        
        # Append to global sessions log
        self._append_to_sessions_log(log_entry)
        
        return log_entry
    
    def log_conversation_session(
        self,
        user_id: str,
        conversation_id: str,
        is_new: bool = False,
    ) -> Dict[str, Any]:
        """Log a conversation session initialization.
        
        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            is_new: Whether this is a new conversation or resuming
            
        Returns:
            Dictionary containing log file path and session info
        """
        log_path = self._get_session_log_path(user_id, conversation_id)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "conversation_session",
            "status": "new_conversation" if is_new else "resumed_conversation",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "log_file": str(log_path),
            "access_command": f"python3 scripts/get_tree_session_data.py {user_id} {conversation_id}",
        }
        
        # Write to conversation session log
        with open(log_path, "w") as f:
            json.dump(log_entry, f, indent=2)
        
        # Append to global sessions log
        self._append_to_sessions_log(log_entry)
        
        return log_entry
    
    def _append_to_sessions_log(self, log_entry: Dict[str, Any]):
        """Append entry to global sessions JSONL log."""
        # Ensure file exists
        self.SESSIONS_LOG.parent.mkdir(exist_ok=True, parents=True)
        
        # Append as JSONL (one JSON object per line)
        with open(self.SESSIONS_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_session_info(self, user_id: str, conversation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get session info from log file.
        
        Args:
            user_id: The user ID
            conversation_id: Optional conversation ID
            
        Returns:
            Dictionary with session info, or None if not found
        """
        log_path = self._get_session_log_path(user_id, conversation_id)
        
        if log_path.exists():
            with open(log_path, "r") as f:
                return json.load(f)
        
        return None
    
    def get_all_sessions(self, user_id: Optional[str] = None) -> list:
        """Get all sessions from the global sessions log.
        
        Args:
            user_id: Optional filter by user ID
            
        Returns:
            List of session entries
        """
        sessions = []
        
        if not self.SESSIONS_LOG.exists():
            return sessions
        
        with open(self.SESSIONS_LOG, "r") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if user_id is None or entry.get("user_id") == user_id:
                        sessions.append(entry)
        
        return sessions
    
    def print_session_location(self, log_entry: Dict[str, Any]):
        """Print a minimal message about where the session was logged.
        
        Args:
            log_entry: The log entry dictionary
        """
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        if log_entry["event_type"] == "user_session":
            event_type = "👤 User Session"
            status = log_entry["status"]
            log_file = log_entry["log_file"]
            
            console.print(Panel(
                f"[{('green' if status == 'new_user' else 'blue')}]"
                f"{status.replace('_', ' ').title()}[/]\n"
                f"[dim]Logged to: {log_file}[/dim]",
                border_style="green" if status == "new_user" else "blue",
                padding=(0, 1),
                title=event_type
            ))
        
        elif log_entry["event_type"] == "conversation_session":
            event_type = "💬 Conversation"
            status = log_entry["status"]
            log_file = log_entry["log_file"]
            user_id = log_entry["user_id"]
            conversation_id = log_entry["conversation_id"]
            access_cmd = log_entry["access_command"]
            
            console.print(Panel(
                f"[{('green' if status == 'new_conversation' else 'blue')}]"
                f"{status.replace('_', ' ').title()}[/]\n"
                f"[dim]User:        {user_id}[/dim]\n"
                f"[dim]Conversation: {conversation_id}[/dim]\n"
                f"[dim]Log:         {log_file}[/dim]\n"
                f"[cyan]Access:      {access_cmd}[/cyan]",
                border_style="green" if status == "new_conversation" else "blue",
                padding=(0, 1),
                title=event_type
            ))


# Singleton instance
_session_logger = None


def get_session_logger() -> SessionLogger:
    """Get or create the singleton session logger."""
    global _session_logger
    if _session_logger is None:
        _session_logger = SessionLogger()
    return _session_logger

