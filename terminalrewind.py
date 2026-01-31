#!/usr/bin/env python3
"""
TerminalRewind - Command+Z for Your Terminal

A powerful terminal session recorder that captures every command with full
context: timestamps, working directories, exit codes, outputs, and file
changes. Enables replay, search, rollback, and agent handoff for complete
terminal session management.

Features:
- Records commands with full metadata (timestamp, cwd, exit code, output)
- Tracks file changes made by commands (create, modify, delete)
- Instant replay and search of command history
- Smart rollback with file backup/restore
- Agent handoff via comprehensive session export
- Cross-platform (Windows, Linux, macOS)

Author: ATLAS (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0.0
Date: January 31, 2026
License: MIT
"""

import argparse
import datetime
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


# ============================================================================
# CONFIGURATION
# ============================================================================

VERSION = "1.0.0"
DEFAULT_DB_NAME = "terminalrewind.db"


def get_default_db_path() -> Path:
    """Get the default database path based on platform."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "TerminalRewind" / DEFAULT_DB_NAME


def get_backup_dir() -> Path:
    """Get the backup directory for file snapshots."""
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "TerminalRewind" / "backups"


# ============================================================================
# DATABASE SCHEMA AND OPERATIONS
# ============================================================================

class TerminalRewindDB:
    """SQLite database manager for TerminalRewind."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        self.db_path = db_path or get_default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Commands table - stores every recorded command
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                command TEXT NOT NULL,
                cwd TEXT NOT NULL,
                exit_code INTEGER,
                output TEXT,
                error_output TEXT,
                duration_ms INTEGER,
                platform TEXT,
                shell TEXT,
                user TEXT,
                hostname TEXT,
                tags TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # File changes table - tracks files affected by commands
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                change_type TEXT NOT NULL,  -- 'created', 'modified', 'deleted'
                old_hash TEXT,
                new_hash TEXT,
                old_size INTEGER,
                new_size INTEGER,
                backup_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (command_id) REFERENCES commands(id)
            )
        """)
        
        # Sessions table - groups commands by session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                command_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                cwd_start TEXT,
                agent_name TEXT,
                metadata TEXT
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_session ON commands(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_timestamp ON commands(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_commands_command ON commands(command)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_changes_command ON file_changes(command_id)")
        
        # Enable FTS5 for full-text search on commands
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS commands_fts USING fts5(
                command,
                output,
                content='commands',
                content_rowid='id'
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def record_command(self, session_id: str, command: str, cwd: str,
                      exit_code: Optional[int] = None, output: Optional[str] = None,
                      error_output: Optional[str] = None, duration_ms: Optional[int] = None,
                      tags: Optional[List[str]] = None, notes: Optional[str] = None) -> int:
        """Record a command execution."""
        cursor = self.conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO commands (
                session_id, timestamp, command, cwd, exit_code, output,
                error_output, duration_ms, platform, shell, user, hostname, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, timestamp, command, cwd, exit_code, output,
            error_output, duration_ms, platform.system(),
            os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")),
            os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            platform.node(),
            json.dumps(tags) if tags else None,
            notes
        ))
        
        command_id = cursor.lastrowid
        
        # Update FTS index
        cursor.execute("""
            INSERT INTO commands_fts(rowid, command, output) VALUES (?, ?, ?)
        """, (command_id, command, output or ""))
        
        # Update session stats
        cursor.execute("""
            UPDATE sessions SET
                command_count = command_count + 1,
                success_count = success_count + CASE WHEN ? = 0 THEN 1 ELSE 0 END,
                error_count = error_count + CASE WHEN ? != 0 THEN 1 ELSE 0 END
            WHERE id = ?
        """, (exit_code, exit_code, session_id))
        
        self.conn.commit()
        return command_id
    
    def record_file_change(self, command_id: int, file_path: str,
                          change_type: str, old_hash: Optional[str] = None,
                          new_hash: Optional[str] = None, old_size: Optional[int] = None,
                          new_size: Optional[int] = None, backup_path: Optional[str] = None):
        """Record a file change associated with a command."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO file_changes (
                command_id, file_path, change_type, old_hash, new_hash,
                old_size, new_size, backup_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (command_id, file_path, change_type, old_hash, new_hash,
              old_size, new_size, backup_path))
        self.conn.commit()
    
    def start_session(self, session_id: str, name: Optional[str] = None,
                     description: Optional[str] = None, agent_name: Optional[str] = None,
                     metadata: Optional[Dict] = None) -> str:
        """Start a new recording session."""
        cursor = self.conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cwd = os.getcwd()
        
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (
                id, name, description, started_at, cwd_start, agent_name, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, name, description, timestamp, cwd,
            agent_name, json.dumps(metadata) if metadata else None
        ))
        self.conn.commit()
        return session_id
    
    def end_session(self, session_id: str):
        """End a recording session."""
        cursor = self.conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute("""
            UPDATE sessions SET ended_at = ? WHERE id = ?
        """, (timestamp, session_id))
        self.conn.commit()
    
    def get_commands(self, session_id: Optional[str] = None, limit: int = 50,
                    since: Optional[str] = None, with_errors: bool = False,
                    search: Optional[str] = None) -> List[Dict]:
        """Retrieve recorded commands with filters."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM commands WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        
        if with_errors:
            query += " AND exit_code != 0"
        
        if search:
            # Use FTS search
            query = """
                SELECT c.* FROM commands c
                JOIN commands_fts fts ON c.id = fts.rowid
                WHERE commands_fts MATCH ?
            """
            params = [search]
            if session_id:
                query += " AND c.session_id = ?"
                params.append(session_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_command_by_id(self, command_id: int) -> Optional[Dict]:
        """Get a specific command by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM commands WHERE id = ?", (command_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_file_changes(self, command_id: int) -> List[Dict]:
        """Get file changes for a specific command."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM file_changes WHERE command_id = ?
        """, (command_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_sessions(self, limit: int = 20) -> List[Dict]:
        """Get recent sessions."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a specific session."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_last_command(self) -> Optional[Dict]:
        """Get the most recent command."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM commands ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_stats(self) -> Dict:
        """Get overall statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM commands")
        total_commands = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM commands WHERE exit_code = 0")
        successful_commands = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM commands WHERE exit_code != 0")
        failed_commands = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_changes")
        total_file_changes = cursor.fetchone()[0]
        
        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "success_rate": round(successful_commands / total_commands * 100, 1) if total_commands > 0 else 0,
            "total_sessions": total_sessions,
            "total_file_changes": total_file_changes,
            "database_path": str(self.db_path),
            "database_size_kb": round(self.db_path.stat().st_size / 1024, 2) if self.db_path.exists() else 0
        }


# ============================================================================
# FILE TRACKING AND BACKUP
# ============================================================================

class FileTracker:
    """Tracks file changes and manages backups for rollback."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize file tracker."""
        self.backup_dir = backup_dir or get_backup_dir()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._watched_files: Dict[str, Tuple[Optional[str], Optional[int]]] = {}
    
    @staticmethod
    def get_file_hash(file_path: Path) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        if not file_path.exists() or not file_path.is_file():
            return None
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, PermissionError):
            return None
    
    @staticmethod
    def get_file_size(file_path: Path) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return file_path.stat().st_size if file_path.exists() else None
        except (IOError, PermissionError):
            return None
    
    def snapshot_directory(self, directory: Path) -> Dict[str, Tuple[Optional[str], Optional[int]]]:
        """Take a snapshot of all files in a directory."""
        snapshot = {}
        if not directory.exists():
            return snapshot
        
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    rel_path = str(item.relative_to(directory))
                    snapshot[rel_path] = (
                        self.get_file_hash(item),
                        self.get_file_size(item)
                    )
        except (IOError, PermissionError):
            pass
        
        return snapshot
    
    def watch_files(self, file_paths: List[Path]):
        """Start watching specific files for changes."""
        self._watched_files.clear()
        for file_path in file_paths:
            path = Path(file_path)
            self._watched_files[str(path)] = (
                self.get_file_hash(path),
                self.get_file_size(path)
            )
    
    def watch_directory(self, directory: Path):
        """Watch all files in a directory."""
        self._watched_files = self.snapshot_directory(directory)
    
    def detect_changes(self, directory: Optional[Path] = None) -> List[Dict]:
        """Detect changes since watch started."""
        changes = []
        current_snapshot = self.snapshot_directory(directory) if directory else {}
        
        # If we have a directory, compare snapshots
        if directory:
            # Check for modified and deleted files
            for rel_path, (old_hash, old_size) in self._watched_files.items():
                full_path = directory / rel_path
                if rel_path in current_snapshot:
                    new_hash, new_size = current_snapshot[rel_path]
                    if old_hash != new_hash:
                        changes.append({
                            "path": str(full_path),
                            "type": "modified",
                            "old_hash": old_hash,
                            "new_hash": new_hash,
                            "old_size": old_size,
                            "new_size": new_size
                        })
                else:
                    changes.append({
                        "path": str(full_path),
                        "type": "deleted",
                        "old_hash": old_hash,
                        "old_size": old_size
                    })
            
            # Check for created files
            for rel_path, (new_hash, new_size) in current_snapshot.items():
                if rel_path not in self._watched_files:
                    full_path = directory / rel_path
                    changes.append({
                        "path": str(full_path),
                        "type": "created",
                        "new_hash": new_hash,
                        "new_size": new_size
                    })
        else:
            # Check watched files individually
            for path_str, (old_hash, old_size) in self._watched_files.items():
                path = Path(path_str)
                new_hash = self.get_file_hash(path)
                new_size = self.get_file_size(path)
                
                if old_hash is None and new_hash is not None:
                    changes.append({
                        "path": path_str,
                        "type": "created",
                        "new_hash": new_hash,
                        "new_size": new_size
                    })
                elif old_hash is not None and new_hash is None:
                    changes.append({
                        "path": path_str,
                        "type": "deleted",
                        "old_hash": old_hash,
                        "old_size": old_size
                    })
                elif old_hash != new_hash:
                    changes.append({
                        "path": path_str,
                        "type": "modified",
                        "old_hash": old_hash,
                        "new_hash": new_hash,
                        "old_size": old_size,
                        "new_size": new_size
                    })
        
        return changes
    
    def backup_file(self, file_path: Path, command_id: int) -> Optional[str]:
        """Create a backup of a file before modification."""
        if not file_path.exists():
            return None
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"cmd_{command_id}_{timestamp}_{file_path.name}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except (IOError, PermissionError):
            return None
    
    def restore_file(self, backup_path: str, original_path: str) -> bool:
        """Restore a file from backup."""
        backup = Path(backup_path)
        original = Path(original_path)
        
        if not backup.exists():
            return False
        
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, original)
            return True
        except (IOError, PermissionError):
            return False
    
    def cleanup_old_backups(self, days: int = 7):
        """Remove backups older than specified days."""
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                try:
                    mtime = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if mtime < cutoff:
                        backup_file.unlink()
                except (IOError, PermissionError):
                    pass


# ============================================================================
# COMMAND RECORDER
# ============================================================================

class CommandRecorder:
    """Records command execution with full context."""
    
    def __init__(self, db: Optional[TerminalRewindDB] = None):
        """Initialize recorder."""
        self.db = db or TerminalRewindDB()
        self.file_tracker = FileTracker()
        self.current_session_id: Optional[str] = None
    
    def start_session(self, name: Optional[str] = None, agent_name: Optional[str] = None) -> str:
        """Start a new recording session."""
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if name:
            session_id = f"{session_id}_{name.replace(' ', '_')[:20]}"
        
        self.current_session_id = self.db.start_session(
            session_id=session_id,
            name=name,
            agent_name=agent_name
        )
        return self.current_session_id
    
    def end_session(self):
        """End the current recording session."""
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
            self.current_session_id = None
    
    def record(self, command: str, cwd: Optional[str] = None,
              track_files: Optional[List[str]] = None,
              track_cwd: bool = False,
              execute: bool = False) -> int:
        """
        Record a command execution.
        
        Args:
            command: The command that was/will be executed
            cwd: Working directory (defaults to current)
            track_files: List of file paths to track for changes
            track_cwd: Track all files in current working directory
            execute: If True, actually execute the command and capture output
        """
        if not self.current_session_id:
            self.start_session()
        
        cwd = cwd or os.getcwd()
        
        # Set up file tracking
        if track_files:
            self.file_tracker.watch_files([Path(f) for f in track_files])
        elif track_cwd:
            self.file_tracker.watch_directory(Path(cwd))
        
        # Execute command if requested
        exit_code = None
        output = None
        error_output = None
        duration_ms = None
        
        if execute:
            start_time = time.time()
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    timeout=300  # 5 minute timeout
                )
                exit_code = result.returncode
                output = result.stdout[:100000] if result.stdout else None  # Limit output size
                error_output = result.stderr[:10000] if result.stderr else None
            except subprocess.TimeoutExpired:
                exit_code = -1
                error_output = "Command timed out after 5 minutes"
            except Exception as e:
                exit_code = -1
                error_output = str(e)
            
            duration_ms = int((time.time() - start_time) * 1000)
        
        # Record the command
        command_id = self.db.record_command(
            session_id=self.current_session_id,
            command=command,
            cwd=cwd,
            exit_code=exit_code,
            output=output,
            error_output=error_output,
            duration_ms=duration_ms
        )
        
        # Detect and record file changes
        if track_files or track_cwd:
            changes = self.file_tracker.detect_changes(
                Path(cwd) if track_cwd else None
            )
            for change in changes:
                # Create backup for modified/deleted files
                backup_path = None
                if change["type"] in ("modified", "deleted"):
                    backup_path = self.file_tracker.backup_file(
                        Path(change["path"]), command_id
                    )
                
                self.db.record_file_change(
                    command_id=command_id,
                    file_path=change["path"],
                    change_type=change["type"],
                    old_hash=change.get("old_hash"),
                    new_hash=change.get("new_hash"),
                    old_size=change.get("old_size"),
                    new_size=change.get("new_size"),
                    backup_path=backup_path
                )
        
        return command_id
    
    def log(self, command: str, exit_code: int = 0,
            output: Optional[str] = None, error_output: Optional[str] = None,
            cwd: Optional[str] = None, duration_ms: Optional[int] = None) -> int:
        """
        Log a command that has already been executed (manual recording).
        
        Useful for shell integration or manual logging.
        """
        if not self.current_session_id:
            self.start_session()
        
        return self.db.record_command(
            session_id=self.current_session_id,
            command=command,
            cwd=cwd or os.getcwd(),
            exit_code=exit_code,
            output=output,
            error_output=error_output,
            duration_ms=duration_ms
        )


# ============================================================================
# SESSION EXPORTER
# ============================================================================

class SessionExporter:
    """Export sessions for agent handoff and documentation."""
    
    def __init__(self, db: TerminalRewindDB):
        """Initialize exporter."""
        self.db = db
    
    def to_json(self, session_id: Optional[str] = None, 
                limit: int = 100, include_output: bool = True) -> str:
        """Export session(s) to JSON format."""
        if session_id:
            session = self.db.get_session(session_id)
            commands = self.db.get_commands(session_id=session_id, limit=limit)
        else:
            session = None
            commands = self.db.get_commands(limit=limit)
        
        # Get file changes for each command
        for cmd in commands:
            cmd["file_changes"] = self.db.get_file_changes(cmd["id"])
            if not include_output:
                cmd["output"] = "[output omitted]" if cmd["output"] else None
        
        export_data = {
            "export_timestamp": datetime.datetime.now().isoformat(),
            "export_version": VERSION,
            "session": session,
            "commands": commands,
            "stats": self.db.get_stats()
        }
        
        return json.dumps(export_data, indent=2)
    
    def to_markdown(self, session_id: Optional[str] = None,
                   limit: int = 50, include_output: bool = True) -> str:
        """Export session to Markdown format for documentation."""
        if session_id:
            session = self.db.get_session(session_id)
            commands = self.db.get_commands(session_id=session_id, limit=limit)
        else:
            session = None
            commands = self.db.get_commands(limit=limit)
        
        # Reverse to show oldest first
        commands = list(reversed(commands))
        
        lines = []
        lines.append("# Terminal Session Export")
        lines.append("")
        lines.append(f"**Exported:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Commands:** {len(commands)}")
        
        if session:
            lines.append(f"**Session:** {session.get('name', session['id'])}")
            lines.append(f"**Started:** {session['started_at']}")
            if session.get('agent_name'):
                lines.append(f"**Agent:** {session['agent_name']}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Commands")
        lines.append("")
        
        for i, cmd in enumerate(commands, 1):
            timestamp = cmd['timestamp'][:19].replace('T', ' ')
            exit_status = "[OK]" if cmd['exit_code'] == 0 else f"[ERROR:{cmd['exit_code']}]"
            
            lines.append(f"### {i}. {exit_status} `{cmd['command'][:60]}{'...' if len(cmd['command']) > 60 else ''}`")
            lines.append("")
            lines.append(f"- **Time:** {timestamp}")
            lines.append(f"- **Directory:** `{cmd['cwd']}`")
            if cmd.get('duration_ms'):
                lines.append(f"- **Duration:** {cmd['duration_ms']}ms")
            
            if include_output and cmd.get('output'):
                lines.append("")
                lines.append("**Output:**")
                lines.append("```")
                # Truncate very long outputs
                output = cmd['output'][:2000]
                if len(cmd['output']) > 2000:
                    output += "\n... [truncated]"
                lines.append(output)
                lines.append("```")
            
            if cmd.get('error_output'):
                lines.append("")
                lines.append("**Error:**")
                lines.append("```")
                lines.append(cmd['error_output'][:1000])
                lines.append("```")
            
            # File changes
            file_changes = self.db.get_file_changes(cmd['id'])
            if file_changes:
                lines.append("")
                lines.append("**File Changes:**")
                for fc in file_changes:
                    icon = {"created": "+", "modified": "~", "deleted": "-"}.get(fc['change_type'], "?")
                    lines.append(f"- `{icon}` {fc['file_path']} ({fc['change_type']})")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def for_agent(self, agent_name: str, session_id: Optional[str] = None,
                 limit: int = 50) -> str:
        """
        Export session specifically formatted for AI agent handoff.
        
        Includes context summary and key information for the receiving agent.
        """
        if session_id:
            session = self.db.get_session(session_id)
            commands = self.db.get_commands(session_id=session_id, limit=limit)
        else:
            session = None
            commands = self.db.get_commands(limit=limit)
        
        # Reverse to show chronological order
        commands = list(reversed(commands))
        
        lines = []
        lines.append(f"# Agent Handoff Package for {agent_name}")
        lines.append("")
        lines.append("## Context Summary")
        lines.append("")
        lines.append(f"This terminal session is being handed off to **{agent_name}**.")
        lines.append(f"**Total Commands:** {len(commands)}")
        
        if commands:
            error_count = sum(1 for c in commands if c['exit_code'] and c['exit_code'] != 0)
            lines.append(f"**Successful:** {len(commands) - error_count}")
            lines.append(f"**Errors:** {error_count}")
            lines.append(f"**Last Directory:** `{commands[-1]['cwd']}`")
        
        if session and session.get('agent_name'):
            lines.append(f"**Previous Agent:** {session['agent_name']}")
        
        lines.append("")
        lines.append("## What Happened")
        lines.append("")
        
        # Summarize recent commands
        for i, cmd in enumerate(commands[-10:], 1):  # Last 10 commands
            exit_status = "[OK]" if cmd['exit_code'] == 0 else "[X]"
            lines.append(f"{i}. {exit_status} `{cmd['command'][:80]}`")
        
        lines.append("")
        lines.append("## Key Observations")
        lines.append("")
        
        # Identify patterns
        if any(c['exit_code'] and c['exit_code'] != 0 for c in commands[-5:]):
            lines.append("- [!] Recent errors detected - review error outputs below")
        
        cwd_set = set(c['cwd'] for c in commands)
        if len(cwd_set) > 3:
            lines.append(f"- Session involved {len(cwd_set)} different directories")
        
        # Find any file changes
        all_changes = []
        for cmd in commands:
            all_changes.extend(self.db.get_file_changes(cmd['id']))
        
        if all_changes:
            lines.append(f"- {len(all_changes)} file changes recorded")
            created = sum(1 for c in all_changes if c['change_type'] == 'created')
            modified = sum(1 for c in all_changes if c['change_type'] == 'modified')
            deleted = sum(1 for c in all_changes if c['change_type'] == 'deleted')
            if created:
                lines.append(f"  - {created} files created")
            if modified:
                lines.append(f"  - {modified} files modified")
            if deleted:
                lines.append(f"  - {deleted} files deleted")
        
        lines.append("")
        lines.append("## Full Command History")
        lines.append("")
        lines.append("```")
        for cmd in commands:
            prefix = "[X]" if cmd['exit_code'] and cmd['exit_code'] != 0 else "[OK]"
            lines.append(f"{prefix} [{cmd['timestamp'][:19]}] {cmd['command']}")
        lines.append("```")
        
        lines.append("")
        lines.append("## Errors (if any)")
        lines.append("")
        
        error_cmds = [c for c in commands if c.get('error_output')]
        if error_cmds:
            for cmd in error_cmds[-3:]:  # Last 3 errors
                lines.append(f"**Command:** `{cmd['command'][:60]}`")
                lines.append(f"**Exit Code:** {cmd['exit_code']}")
                lines.append("```")
                lines.append(cmd['error_output'][:500])
                lines.append("```")
                lines.append("")
        else:
            lines.append("No errors recorded.")
        
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by TerminalRewind v{VERSION} at {datetime.datetime.now().isoformat()}*")
        
        return "\n".join(lines)


# ============================================================================
# ROLLBACK MANAGER
# ============================================================================

class RollbackManager:
    """Manages rollback of file changes."""
    
    def __init__(self, db: TerminalRewindDB):
        """Initialize rollback manager."""
        self.db = db
        self.file_tracker = FileTracker()
    
    def can_rollback(self, command_id: int) -> Tuple[bool, str]:
        """Check if a command's file changes can be rolled back."""
        file_changes = self.db.get_file_changes(command_id)
        
        if not file_changes:
            return False, "No file changes recorded for this command"
        
        for fc in file_changes:
            if fc['change_type'] in ('modified', 'deleted'):
                if not fc.get('backup_path'):
                    return False, f"No backup available for {fc['file_path']}"
                if not Path(fc['backup_path']).exists():
                    return False, f"Backup file missing for {fc['file_path']}"
        
        return True, "Rollback is possible"
    
    def rollback_command(self, command_id: int, dry_run: bool = True) -> Dict:
        """
        Rollback file changes made by a command.
        
        Args:
            command_id: ID of the command to rollback
            dry_run: If True, only report what would be done
        
        Returns:
            Dictionary with rollback results
        """
        can_rb, reason = self.can_rollback(command_id)
        if not can_rb:
            return {"success": False, "error": reason, "actions": []}
        
        file_changes = self.db.get_file_changes(command_id)
        actions = []
        
        for fc in file_changes:
            action = {
                "file": fc['file_path'],
                "type": fc['change_type'],
                "status": "pending"
            }
            
            if fc['change_type'] == 'created':
                # Delete the created file
                action["action"] = "delete"
                if not dry_run:
                    try:
                        Path(fc['file_path']).unlink()
                        action["status"] = "success"
                    except Exception as e:
                        action["status"] = "failed"
                        action["error"] = str(e)
            
            elif fc['change_type'] in ('modified', 'deleted'):
                # Restore from backup
                action["action"] = "restore"
                action["backup"] = fc['backup_path']
                if not dry_run:
                    success = self.file_tracker.restore_file(
                        fc['backup_path'], fc['file_path']
                    )
                    action["status"] = "success" if success else "failed"
            
            actions.append(action)
        
        return {
            "success": all(a["status"] != "failed" for a in actions),
            "dry_run": dry_run,
            "command_id": command_id,
            "actions": actions
        }
    
    def rollback_last(self, dry_run: bool = True) -> Dict:
        """Rollback the most recent command with file changes."""
        # Find last command with file changes
        commands = self.db.get_commands(limit=20)
        
        for cmd in commands:
            file_changes = self.db.get_file_changes(cmd['id'])
            if file_changes:
                return self.rollback_command(cmd['id'], dry_run)
        
        return {
            "success": False,
            "error": "No recent commands with file changes found",
            "actions": []
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def format_command_row(cmd: Dict, show_output: bool = False) -> str:
    """Format a command for display."""
    timestamp = cmd['timestamp'][:19].replace('T', ' ')
    status = "[OK]" if cmd['exit_code'] == 0 else f"[X:{cmd['exit_code']}]"
    duration = f" ({cmd['duration_ms']}ms)" if cmd.get('duration_ms') else ""
    
    line = f"{status} [{timestamp}]{duration} {cmd['command'][:60]}"
    if len(cmd['command']) > 60:
        line += "..."
    
    if show_output and cmd.get('output'):
        line += f"\n    Output: {cmd['output'][:100]}..."
    
    return line


def cmd_record(args):
    """Record a command (optionally execute it)."""
    db = TerminalRewindDB()
    recorder = CommandRecorder(db)
    
    if args.session:
        recorder.current_session_id = args.session
    else:
        recorder.start_session(agent_name=args.agent)
    
    command_id = recorder.record(
        command=args.command,
        cwd=args.cwd,
        track_cwd=args.track_files,
        execute=args.execute
    )
    
    print(f"[OK] Recorded command (ID: {command_id})")
    
    if args.execute:
        cmd = db.get_command_by_id(command_id)
        if cmd:
            if cmd['exit_code'] == 0:
                print(f"[OK] Command executed successfully")
                if cmd['output']:
                    print(cmd['output'])
            else:
                print(f"[X] Command failed (exit code: {cmd['exit_code']})")
                if cmd['error_output']:
                    print(cmd['error_output'])
    
    db.close()


def cmd_log(args):
    """Log a command that was already executed."""
    db = TerminalRewindDB()
    recorder = CommandRecorder(db)
    
    if args.session:
        recorder.current_session_id = args.session
    else:
        recorder.start_session(agent_name=args.agent)
    
    command_id = recorder.log(
        command=args.command,
        exit_code=args.exit_code,
        output=args.output,
        error_output=args.error,
        cwd=args.cwd
    )
    
    print(f"[OK] Logged command (ID: {command_id})")
    db.close()


def cmd_show(args):
    """Show recent commands."""
    db = TerminalRewindDB()
    
    since = None
    if args.since:
        # Parse relative time
        try:
            if "minute" in args.since:
                minutes = int(args.since.split()[0])
                since = (datetime.datetime.now() - datetime.timedelta(minutes=minutes)).isoformat()
            elif "hour" in args.since:
                hours = int(args.since.split()[0])
                since = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
            elif "day" in args.since:
                days = int(args.since.split()[0])
                since = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            else:
                since = args.since
        except ValueError:
            since = args.since
    
    commands = db.get_commands(
        session_id=args.session,
        limit=args.limit,
        since=since,
        with_errors=args.errors
    )
    
    if not commands:
        print("No commands found.")
        db.close()
        return
    
    print(f"=== Recent Commands ({len(commands)}) ===\n")
    
    for cmd in reversed(commands):
        print(format_command_row(cmd, args.verbose))
        
        if args.verbose:
            file_changes = db.get_file_changes(cmd['id'])
            if file_changes:
                for fc in file_changes:
                    icon = {"created": "+", "modified": "~", "deleted": "-"}.get(fc['change_type'], "?")
                    print(f"    [{icon}] {fc['file_path']}")
        print()
    
    db.close()


def cmd_search(args):
    """Search commands."""
    db = TerminalRewindDB()
    
    commands = db.get_commands(
        search=args.pattern,
        limit=args.limit
    )
    
    if not commands:
        print(f"No commands matching '{args.pattern}' found.")
        db.close()
        return
    
    print(f"=== Search Results for '{args.pattern}' ({len(commands)}) ===\n")
    
    for cmd in reversed(commands):
        print(format_command_row(cmd, args.verbose))
        if args.verbose and cmd.get('output'):
            # Highlight search term in output
            output = cmd['output'][:200]
            print(f"    Output: {output}")
        print()
    
    db.close()


def cmd_sessions(args):
    """List sessions."""
    db = TerminalRewindDB()
    sessions = db.get_sessions(limit=args.limit)
    
    if not sessions:
        print("No sessions found.")
        db.close()
        return
    
    print(f"=== Sessions ({len(sessions)}) ===\n")
    
    for session in sessions:
        name = session.get('name', session['id'])
        started = session['started_at'][:19].replace('T', ' ')
        ended = session.get('ended_at', 'active')[:19].replace('T', ' ') if session.get('ended_at') else '[active]'
        cmds = session.get('command_count', 0)
        errors = session.get('error_count', 0)
        
        print(f"[{session['id']}] {name}")
        print(f"    Started: {started} | Ended: {ended}")
        print(f"    Commands: {cmds} | Errors: {errors}")
        if session.get('agent_name'):
            print(f"    Agent: {session['agent_name']}")
        print()
    
    db.close()


def cmd_export(args):
    """Export session."""
    db = TerminalRewindDB()
    exporter = SessionExporter(db)
    
    if args.format == "json":
        output = exporter.to_json(
            session_id=args.session,
            limit=args.limit,
            include_output=not args.no_output
        )
    elif args.format == "markdown":
        output = exporter.to_markdown(
            session_id=args.session,
            limit=args.limit,
            include_output=not args.no_output
        )
    elif args.for_agent:
        output = exporter.for_agent(
            agent_name=args.for_agent,
            session_id=args.session,
            limit=args.limit
        )
    else:
        output = exporter.to_markdown(
            session_id=args.session,
            limit=args.limit
        )
    
    if args.output:
        Path(args.output).write_text(output)
        print(f"[OK] Exported to {args.output}")
    else:
        print(output)
    
    db.close()


def cmd_undo(args):
    """Undo/rollback a command's file changes."""
    db = TerminalRewindDB()
    rollback = RollbackManager(db)
    
    if args.command_id:
        result = rollback.rollback_command(args.command_id, dry_run=args.dry_run)
    else:
        result = rollback.rollback_last(dry_run=args.dry_run)
    
    if result['success']:
        mode = "[DRY RUN] " if result.get('dry_run') else ""
        print(f"{mode}[OK] Rollback {'would be ' if result.get('dry_run') else ''}successful")
        print(f"\nActions:")
        for action in result['actions']:
            status = "[OK]" if action['status'] != 'failed' else "[X]"
            print(f"  {status} {action['action']}: {action['file']}")
    else:
        print(f"[X] Rollback failed: {result.get('error', 'Unknown error')}")
    
    if args.dry_run:
        print("\n[!] This was a dry run. Use --apply to actually perform rollback.")
    
    db.close()


def cmd_stats(args):
    """Show statistics."""
    db = TerminalRewindDB()
    stats = db.get_stats()
    
    print("=== TerminalRewind Statistics ===\n")
    print(f"Total Commands:     {stats['total_commands']}")
    print(f"Successful:         {stats['successful_commands']}")
    print(f"Failed:             {stats['failed_commands']}")
    print(f"Success Rate:       {stats['success_rate']}%")
    print(f"Total Sessions:     {stats['total_sessions']}")
    print(f"File Changes:       {stats['total_file_changes']}")
    print(f"\nDatabase:           {stats['database_path']}")
    print(f"Database Size:      {stats['database_size_kb']} KB")
    
    db.close()


def cmd_start(args):
    """Start a new session."""
    db = TerminalRewindDB()
    recorder = CommandRecorder(db)
    
    session_id = recorder.start_session(
        name=args.name,
        agent_name=args.agent
    )
    
    print(f"[OK] Session started: {session_id}")
    print(f"Use 'trewind log <command>' or 'trewind record <command>' to add commands")
    
    db.close()


def cmd_end(args):
    """End the current session."""
    db = TerminalRewindDB()
    
    # Find most recent active session
    sessions = db.get_sessions(limit=1)
    if sessions and not sessions[0].get('ended_at'):
        db.end_session(sessions[0]['id'])
        print(f"[OK] Session ended: {sessions[0]['id']}")
    else:
        print("[!] No active session found")
    
    db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='TerminalRewind - Command+Z for your terminal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  trewind show                    # Show recent commands
  trewind show --since "10 minutes ago"
  trewind search "npm install"    # Search for commands
  trewind record "ls -la" --execute
  trewind log "git commit -m 'test'" --exit-code 0
  trewind export --format markdown > session.md
  trewind export --for-agent CLIO > handoff.md
  trewind undo --dry-run          # Preview rollback
  trewind undo --apply            # Actually rollback

For more information: https://github.com/DonkRonk17/TerminalRewind
        """
    )
    
    parser.add_argument('--version', action='version', version=f'TerminalRewind v{VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # show command
    show_parser = subparsers.add_parser('show', help='Show recent commands')
    show_parser.add_argument('--limit', '-n', type=int, default=20, help='Number of commands to show')
    show_parser.add_argument('--since', '-s', help='Show commands since (e.g., "10 minutes ago")')
    show_parser.add_argument('--session', help='Filter by session ID')
    show_parser.add_argument('--errors', '-e', action='store_true', help='Show only failed commands')
    show_parser.add_argument('--verbose', '-v', action='store_true', help='Show more details')
    show_parser.set_defaults(func=cmd_show)
    
    # search command
    search_parser = subparsers.add_parser('search', help='Search commands')
    search_parser.add_argument('pattern', help='Search pattern')
    search_parser.add_argument('--limit', '-n', type=int, default=20, help='Max results')
    search_parser.add_argument('--verbose', '-v', action='store_true', help='Show output snippets')
    search_parser.set_defaults(func=cmd_search)
    
    # record command
    record_parser = subparsers.add_parser('record', help='Record a command')
    record_parser.add_argument('command', help='Command to record')
    record_parser.add_argument('--execute', '-x', action='store_true', help='Execute the command')
    record_parser.add_argument('--track-files', '-t', action='store_true', help='Track file changes')
    record_parser.add_argument('--cwd', help='Working directory')
    record_parser.add_argument('--session', help='Session ID')
    record_parser.add_argument('--agent', help='Agent name')
    record_parser.set_defaults(func=cmd_record)
    
    # log command
    log_parser = subparsers.add_parser('log', help='Log an already-executed command')
    log_parser.add_argument('command', help='Command that was executed')
    log_parser.add_argument('--exit-code', '-e', type=int, default=0, help='Exit code')
    log_parser.add_argument('--output', '-o', help='Command output')
    log_parser.add_argument('--error', help='Error output')
    log_parser.add_argument('--cwd', help='Working directory')
    log_parser.add_argument('--session', help='Session ID')
    log_parser.add_argument('--agent', help='Agent name')
    log_parser.set_defaults(func=cmd_log)
    
    # sessions command
    sessions_parser = subparsers.add_parser('sessions', help='List sessions')
    sessions_parser.add_argument('--limit', '-n', type=int, default=10, help='Number of sessions')
    sessions_parser.set_defaults(func=cmd_sessions)
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export session')
    export_parser.add_argument('--format', '-f', choices=['json', 'markdown'], default='markdown')
    export_parser.add_argument('--for-agent', help='Format for specific agent handoff')
    export_parser.add_argument('--session', help='Session ID to export')
    export_parser.add_argument('--output', '-o', help='Output file')
    export_parser.add_argument('--limit', '-n', type=int, default=50, help='Max commands')
    export_parser.add_argument('--no-output', action='store_true', help='Exclude command outputs')
    export_parser.set_defaults(func=cmd_export)
    
    # undo command
    undo_parser = subparsers.add_parser('undo', help='Rollback file changes')
    undo_parser.add_argument('command_id', nargs='?', type=int, help='Command ID to rollback')
    undo_parser.add_argument('--dry-run', '-d', action='store_true', default=True, help='Preview only (default)')
    undo_parser.add_argument('--apply', action='store_true', help='Actually perform rollback')
    undo_parser.set_defaults(func=cmd_undo)
    
    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # start command
    start_parser = subparsers.add_parser('start', help='Start a new session')
    start_parser.add_argument('--name', '-n', help='Session name')
    start_parser.add_argument('--agent', '-a', help='Agent name')
    start_parser.set_defaults(func=cmd_start)
    
    # end command
    end_parser = subparsers.add_parser('end', help='End current session')
    end_parser.set_defaults(func=cmd_end)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Handle --apply flag for undo
    if args.command == 'undo' and args.apply:
        args.dry_run = False
    
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
