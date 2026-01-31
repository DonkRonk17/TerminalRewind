#!/usr/bin/env python3
"""
Comprehensive test suite for TerminalRewind.

Tests cover:
- Database operations
- Command recording
- File tracking
- Session management
- Export functionality
- Rollback operations
- Edge cases

Run: python test_terminalrewind.py
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from terminalrewind import (
    TerminalRewindDB,
    FileTracker,
    CommandRecorder,
    SessionExporter,
    RollbackManager,
    VERSION
)


class TestTerminalRewindDB(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = TerminalRewindDB(self.db_path)
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test database initializes correctly."""
        self.assertTrue(self.db_path.exists())
        self.assertIsNotNone(self.db.conn)
    
    def test_schema_created(self):
        """Test all tables are created."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        
        self.assertIn("commands", tables)
        self.assertIn("file_changes", tables)
        self.assertIn("sessions", tables)
    
    def test_start_session(self):
        """Test starting a new session."""
        session_id = self.db.start_session(
            session_id="test_session_001",
            name="Test Session",
            agent_name="ATLAS"
        )
        
        self.assertEqual(session_id, "test_session_001")
        
        session = self.db.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session["name"], "Test Session")
        self.assertEqual(session["agent_name"], "ATLAS")
    
    def test_record_command(self):
        """Test recording a command."""
        self.db.start_session(session_id="test_session")
        
        command_id = self.db.record_command(
            session_id="test_session",
            command="ls -la",
            cwd="/home/user",
            exit_code=0,
            output="total 100\ndrwxr-xr-x...",
            duration_ms=50
        )
        
        self.assertIsNotNone(command_id)
        self.assertGreater(command_id, 0)
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertEqual(cmd["command"], "ls -la")
        self.assertEqual(cmd["exit_code"], 0)
    
    def test_record_file_change(self):
        """Test recording file changes."""
        self.db.start_session(session_id="test_session")
        command_id = self.db.record_command(
            session_id="test_session",
            command="touch newfile.txt",
            cwd="/home/user"
        )
        
        self.db.record_file_change(
            command_id=command_id,
            file_path="/home/user/newfile.txt",
            change_type="created",
            new_hash="abc123",
            new_size=0
        )
        
        changes = self.db.get_file_changes(command_id)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["change_type"], "created")
    
    def test_get_commands_with_filters(self):
        """Test filtering commands."""
        self.db.start_session(session_id="test_session")
        
        # Record successful command
        self.db.record_command(
            session_id="test_session",
            command="echo hello",
            cwd="/home/user",
            exit_code=0
        )
        
        # Record failed command
        self.db.record_command(
            session_id="test_session",
            command="invalid_command",
            cwd="/home/user",
            exit_code=127
        )
        
        # Get all commands
        all_cmds = self.db.get_commands(session_id="test_session")
        self.assertEqual(len(all_cmds), 2)
        
        # Get only errors
        error_cmds = self.db.get_commands(session_id="test_session", with_errors=True)
        self.assertEqual(len(error_cmds), 1)
        self.assertEqual(error_cmds[0]["exit_code"], 127)
    
    def test_get_last_command(self):
        """Test getting the most recent command."""
        self.db.start_session(session_id="test_session")
        
        self.db.record_command(
            session_id="test_session",
            command="first_command",
            cwd="/home/user"
        )
        
        time.sleep(0.01)  # Ensure different timestamps
        
        self.db.record_command(
            session_id="test_session",
            command="second_command",
            cwd="/home/user"
        )
        
        last_cmd = self.db.get_last_command()
        self.assertEqual(last_cmd["command"], "second_command")
    
    def test_get_stats(self):
        """Test statistics gathering."""
        self.db.start_session(session_id="test_session")
        
        for i in range(5):
            self.db.record_command(
                session_id="test_session",
                command=f"command_{i}",
                cwd="/home/user",
                exit_code=0 if i < 4 else 1
            )
        
        stats = self.db.get_stats()
        self.assertEqual(stats["total_commands"], 5)
        self.assertEqual(stats["successful_commands"], 4)
        self.assertEqual(stats["failed_commands"], 1)
        self.assertEqual(stats["success_rate"], 80.0)
    
    def test_end_session(self):
        """Test ending a session."""
        self.db.start_session(session_id="test_session")
        
        session_before = self.db.get_session("test_session")
        self.assertIsNone(session_before["ended_at"])
        
        self.db.end_session("test_session")
        
        session_after = self.db.get_session("test_session")
        self.assertIsNotNone(session_after["ended_at"])


class TestFileTracker(unittest.TestCase):
    """Test file tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"
        self.tracker = FileTracker(self.backup_dir)
        
        # Create test files
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("original content")
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_file_hash(self):
        """Test file hashing."""
        hash1 = self.tracker.get_file_hash(self.test_file)
        self.assertIsNotNone(hash1)
        self.assertEqual(len(hash1), 32)  # MD5 hash length
        
        # Same content = same hash
        hash2 = self.tracker.get_file_hash(self.test_file)
        self.assertEqual(hash1, hash2)
        
        # Different content = different hash
        self.test_file.write_text("modified content")
        hash3 = self.tracker.get_file_hash(self.test_file)
        self.assertNotEqual(hash1, hash3)
    
    def test_get_file_hash_nonexistent(self):
        """Test hashing nonexistent file."""
        hash_result = self.tracker.get_file_hash(self.temp_dir / "nonexistent.txt")
        self.assertIsNone(hash_result)
    
    def test_watch_and_detect_modification(self):
        """Test detecting file modifications."""
        self.tracker.watch_files([self.test_file])
        
        # Modify the file
        self.test_file.write_text("modified content")
        
        changes = self.tracker.detect_changes()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["type"], "modified")
    
    def test_watch_and_detect_deletion(self):
        """Test detecting file deletion."""
        self.tracker.watch_files([self.test_file])
        
        # Delete the file
        self.test_file.unlink()
        
        changes = self.tracker.detect_changes()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["type"], "deleted")
    
    def test_directory_snapshot(self):
        """Test directory snapshot."""
        # Create multiple files
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        subdir = self.temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        snapshot = self.tracker.snapshot_directory(self.temp_dir)
        
        # Should include all files
        self.assertIn("file1.txt", snapshot)
        self.assertIn("file2.txt", snapshot)
    
    def test_backup_and_restore(self):
        """Test file backup and restore."""
        original_content = self.test_file.read_text()
        
        # Backup the file
        backup_path = self.tracker.backup_file(self.test_file, command_id=1)
        self.assertIsNotNone(backup_path)
        self.assertTrue(Path(backup_path).exists())
        
        # Modify the original
        self.test_file.write_text("modified content")
        self.assertNotEqual(self.test_file.read_text(), original_content)
        
        # Restore from backup
        success = self.tracker.restore_file(backup_path, str(self.test_file))
        self.assertTrue(success)
        self.assertEqual(self.test_file.read_text(), original_content)


class TestCommandRecorder(unittest.TestCase):
    """Test command recording."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = TerminalRewindDB(self.db_path)
        self.recorder = CommandRecorder(self.db)
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_start_session(self):
        """Test session auto-start."""
        session_id = self.recorder.start_session(name="Test", agent_name="ATLAS")
        self.assertIsNotNone(session_id)
        self.assertEqual(self.recorder.current_session_id, session_id)
    
    def test_record_with_auto_session(self):
        """Test recording creates session automatically."""
        self.assertIsNone(self.recorder.current_session_id)
        
        command_id = self.recorder.record(
            command="test command",
            cwd="/tmp"
        )
        
        self.assertIsNotNone(self.recorder.current_session_id)
        self.assertIsNotNone(command_id)
    
    def test_log_command(self):
        """Test logging already-executed command."""
        command_id = self.recorder.log(
            command="git status",
            exit_code=0,
            output="On branch main",
            cwd="/home/user/project"
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertEqual(cmd["command"], "git status")
        self.assertEqual(cmd["exit_code"], 0)
        self.assertEqual(cmd["output"], "On branch main")
    
    def test_end_session(self):
        """Test ending session."""
        self.recorder.start_session()
        session_id = self.recorder.current_session_id
        
        self.recorder.end_session()
        self.assertIsNone(self.recorder.current_session_id)
        
        session = self.db.get_session(session_id)
        self.assertIsNotNone(session["ended_at"])


class TestSessionExporter(unittest.TestCase):
    """Test session export functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = TerminalRewindDB(self.db_path)
        self.exporter = SessionExporter(self.db)
        
        # Create test data
        self.db.start_session(
            session_id="test_session",
            name="Export Test",
            agent_name="ATLAS"
        )
        
        for i in range(3):
            self.db.record_command(
                session_id="test_session",
                command=f"command_{i}",
                cwd="/home/user",
                exit_code=0,
                output=f"output_{i}"
            )
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_json(self):
        """Test JSON export."""
        json_output = self.exporter.to_json(session_id="test_session")
        
        data = json.loads(json_output)
        self.assertIn("export_timestamp", data)
        self.assertIn("commands", data)
        self.assertEqual(len(data["commands"]), 3)
    
    def test_export_markdown(self):
        """Test Markdown export."""
        md_output = self.exporter.to_markdown(session_id="test_session")
        
        self.assertIn("# Terminal Session Export", md_output)
        self.assertIn("command_0", md_output)
        self.assertIn("command_1", md_output)
        self.assertIn("command_2", md_output)
    
    def test_export_for_agent(self):
        """Test agent handoff export."""
        handoff = self.exporter.for_agent(
            agent_name="CLIO",
            session_id="test_session"
        )
        
        self.assertIn("# Agent Handoff Package for CLIO", handoff)
        self.assertIn("Context Summary", handoff)
        self.assertIn("What Happened", handoff)
    
    def test_export_without_output(self):
        """Test export with output omitted."""
        json_output = self.exporter.to_json(
            session_id="test_session",
            include_output=False
        )
        
        data = json.loads(json_output)
        for cmd in data["commands"]:
            if cmd["output"]:
                self.assertEqual(cmd["output"], "[output omitted]")


class TestRollbackManager(unittest.TestCase):
    """Test rollback functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.db = TerminalRewindDB(self.db_path)
        self.rollback = RollbackManager(self.db)
        
        # Create test session and file
        self.db.start_session(session_id="test_session")
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("original content")
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_can_rollback_no_changes(self):
        """Test rollback check with no file changes."""
        command_id = self.db.record_command(
            session_id="test_session",
            command="ls",
            cwd=str(self.temp_dir)
        )
        
        can_rb, reason = self.rollback.can_rollback(command_id)
        self.assertFalse(can_rb)
        self.assertIn("No file changes", reason)
    
    def test_can_rollback_with_backup(self):
        """Test rollback check with backup available."""
        # Record command with file change and backup
        command_id = self.db.record_command(
            session_id="test_session",
            command="modify test.txt",
            cwd=str(self.temp_dir)
        )
        
        # Create backup manually for test
        backup_dir = self.temp_dir / "backups"
        backup_dir.mkdir()
        backup_path = backup_dir / "test_backup.txt"
        backup_path.write_text("original content")
        
        self.db.record_file_change(
            command_id=command_id,
            file_path=str(self.test_file),
            change_type="modified",
            backup_path=str(backup_path)
        )
        
        can_rb, reason = self.rollback.can_rollback(command_id)
        self.assertTrue(can_rb)
    
    def test_rollback_dry_run(self):
        """Test rollback dry run."""
        # Set up rollback scenario
        command_id = self.db.record_command(
            session_id="test_session",
            command="echo test > test.txt",
            cwd=str(self.temp_dir)
        )
        
        backup_dir = self.temp_dir / "backups"
        backup_dir.mkdir()
        backup_path = backup_dir / "test_backup.txt"
        backup_path.write_text("original content")
        
        self.db.record_file_change(
            command_id=command_id,
            file_path=str(self.test_file),
            change_type="modified",
            backup_path=str(backup_path)
        )
        
        # Modify the file
        self.test_file.write_text("modified content")
        
        # Dry run
        result = self.rollback.rollback_command(command_id, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(len(result["actions"]), 1)
        
        # File should not be restored in dry run
        self.assertEqual(self.test_file.read_text(), "modified content")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = TerminalRewindDB(self.db_path)
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_command(self):
        """Test recording empty command."""
        self.db.start_session(session_id="test")
        command_id = self.db.record_command(
            session_id="test",
            command="",
            cwd="/tmp"
        )
        self.assertIsNotNone(command_id)
    
    def test_long_command(self):
        """Test recording very long command."""
        self.db.start_session(session_id="test")
        long_command = "x" * 10000
        command_id = self.db.record_command(
            session_id="test",
            command=long_command,
            cwd="/tmp"
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertEqual(cmd["command"], long_command)
    
    def test_long_output(self):
        """Test recording long output."""
        self.db.start_session(session_id="test")
        long_output = "line\n" * 100000
        command_id = self.db.record_command(
            session_id="test",
            command="cat bigfile",
            cwd="/tmp",
            output=long_output
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertIsNotNone(cmd["output"])
    
    def test_special_characters_in_command(self):
        """Test commands with special characters."""
        self.db.start_session(session_id="test")
        special_cmd = "echo 'hello world' | grep -E \"[a-z]+\" && echo $PATH"
        command_id = self.db.record_command(
            session_id="test",
            command=special_cmd,
            cwd="/tmp"
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertEqual(cmd["command"], special_cmd)
    
    def test_unicode_in_output(self):
        """Test unicode characters in output."""
        self.db.start_session(session_id="test")
        unicode_output = "Hello World"
        command_id = self.db.record_command(
            session_id="test",
            command="echo unicode",
            cwd="/tmp",
            output=unicode_output
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertEqual(cmd["output"], unicode_output)
    
    def test_null_values(self):
        """Test handling null/None values."""
        self.db.start_session(session_id="test")
        command_id = self.db.record_command(
            session_id="test",
            command="test",
            cwd="/tmp",
            exit_code=None,
            output=None,
            error_output=None,
            duration_ms=None
        )
        
        cmd = self.db.get_command_by_id(command_id)
        self.assertIsNone(cmd["exit_code"])
        self.assertIsNone(cmd["output"])
    
    def test_get_nonexistent_session(self):
        """Test getting nonexistent session."""
        session = self.db.get_session("nonexistent_session")
        self.assertIsNone(session)
    
    def test_get_nonexistent_command(self):
        """Test getting nonexistent command."""
        cmd = self.db.get_command_by_id(99999)
        self.assertIsNone(cmd)
    
    def test_stats_empty_db(self):
        """Test stats on empty database."""
        stats = self.db.get_stats()
        self.assertEqual(stats["total_commands"], 0)
        self.assertEqual(stats["success_rate"], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"
        self.db = TerminalRewindDB(self.db_path)
        self.recorder = CommandRecorder(self.db)
    
    def tearDown(self):
        """Clean up after tests."""
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_session_workflow(self):
        """Test complete session workflow."""
        # Start session
        session_id = self.recorder.start_session(
            name="Integration Test",
            agent_name="ATLAS"
        )
        
        # Record multiple commands
        for i in range(5):
            self.recorder.log(
                command=f"echo test_{i}",
                exit_code=0,
                output=f"test_{i}"
            )
        
        # Record a failed command
        self.recorder.log(
            command="invalid_command",
            exit_code=127,
            error_output="command not found"
        )
        
        # End session
        self.recorder.end_session()
        
        # Verify session
        session = self.db.get_session(session_id)
        self.assertIsNotNone(session["ended_at"])
        self.assertEqual(session["command_count"], 6)
        self.assertEqual(session["error_count"], 1)
        
        # Export session
        exporter = SessionExporter(self.db)
        json_export = exporter.to_json(session_id=session_id)
        data = json.loads(json_export)
        self.assertEqual(len(data["commands"]), 6)
    
    def test_agent_handoff_workflow(self):
        """Test agent handoff scenario."""
        # ATLAS starts work
        self.recorder.start_session(name="Atlas Work", agent_name="ATLAS")
        
        self.recorder.log(
            command="git clone repo.git",
            exit_code=0,
            output="Cloning into 'repo'..."
        )
        self.recorder.log(
            command="npm install",
            exit_code=0,
            output="added 500 packages"
        )
        
        session_id = self.recorder.current_session_id
        self.recorder.end_session()
        
        # Export for CLIO
        exporter = SessionExporter(self.db)
        handoff = exporter.for_agent("CLIO", session_id=session_id)
        
        self.assertIn("CLIO", handoff)
        self.assertIn("ATLAS", handoff)
        self.assertIn("git clone", handoff)
        self.assertIn("npm install", handoff)


def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print(f"TESTING: TerminalRewind v{VERSION}")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTerminalRewindDB))
    suite.addTests(loader.loadTestsFromTestCase(TestFileTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandRecorder))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionExporter))
    suite.addTests(loader.loadTestsFromTestCase(TestRollbackManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {result.testsRun} tests")
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
