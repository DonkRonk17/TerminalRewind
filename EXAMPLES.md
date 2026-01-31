# TerminalRewind - Usage Examples

Quick navigation:
- [Example 1: Basic Command Logging](#example-1-basic-command-logging)
- [Example 2: Session Management](#example-2-session-management)
- [Example 3: Viewing Command History](#example-3-viewing-command-history)
- [Example 4: Searching Commands](#example-4-searching-commands)
- [Example 5: File Change Tracking](#example-5-file-change-tracking)
- [Example 6: Rollback Operations](#example-6-rollback-operations)
- [Example 7: Agent Handoff Export](#example-7-agent-handoff-export)
- [Example 8: JSON Export for Analysis](#example-8-json-export-for-analysis)
- [Example 9: Error Debugging Workflow](#example-9-error-debugging-workflow)
- [Example 10: Complete Session Workflow](#example-10-complete-session-workflow)
- [Example 11: Integration with Python Scripts](#example-11-integration-with-python-scripts)
- [Example 12: Statistics and Analytics](#example-12-statistics-and-analytics)

---

## Example 1: Basic Command Logging

**Scenario:** Recording commands as you work in the terminal.

**Steps:**

```bash
# Log a successful command
trewind log "git status" --exit-code 0

# Log a command with output
trewind log "ls -la" --exit-code 0 --output "total 16
drwxr-xr-x  4 user  user  128 Jan 31 10:00 .
drwxr-xr-x 10 user  user  320 Jan 31 09:00 ..
-rw-r--r--  1 user  user 1234 Jan 31 10:00 README.md"

# Log a failed command
trewind log "npm test" --exit-code 1 --error "2 tests failed"

# Log with working directory
trewind log "make build" --exit-code 0 --cwd "/home/user/project"
```

**Expected Output:**
```
[OK] Logged command (ID: 1)
[OK] Logged command (ID: 2)
[OK] Logged command (ID: 3)
[OK] Logged command (ID: 4)
```

**What You Learned:**
- How to log commands that have already been executed
- Including exit codes, outputs, and errors
- Specifying working directory

---

## Example 2: Session Management

**Scenario:** Organizing work into logical sessions.

**Steps:**

```bash
# Start a named session
trewind start --name "Bug Fix #123"

# Output: [OK] Session started: 20260131_100000_Bug_Fix__123

# Log some commands
trewind log "git checkout -b bugfix/123" --exit-code 0
trewind log "git status" --exit-code 0
trewind log "npm test" --exit-code 0

# End the session
trewind end

# Output: [OK] Session ended: 20260131_100000_Bug_Fix__123

# View all sessions
trewind sessions
```

**Expected Output:**
```
=== Sessions (3) ===

[20260131_100000_Bug_Fix__123] Bug Fix #123
    Started: 2026-01-31 10:00:00 | Ended: 2026-01-31 10:30:00
    Commands: 3 | Errors: 0

[20260131_090000] (unnamed)
    Started: 2026-01-31 09:00:00 | Ended: [active]
    Commands: 15 | Errors: 2
```

**What You Learned:**
- How to create named sessions
- Session tracking with statistics
- How to view session history

---

## Example 3: Viewing Command History

**Scenario:** Reviewing what commands were executed.

**Steps:**

```bash
# Show last 20 commands (default)
trewind show

# Show last 50 commands
trewind show --limit 50

# Show commands from last 10 minutes
trewind show --since "10 minutes ago"

# Show commands from last hour
trewind show --since "1 hour ago"

# Show only failed commands
trewind show --errors

# Show with verbose details
trewind show --verbose
```

**Expected Output:**
```
=== Recent Commands (20) ===

[OK] [2026-01-31 10:30:00] npm test
[OK] [2026-01-31 10:29:45] git status
[X:1] [2026-01-31 10:28:30] (125ms) invalid_command
    Error: command not found
[OK] [2026-01-31 10:28:00] git checkout -b feature
...
```

**What You Learned:**
- How to view recent command history
- Filtering by time and status
- Verbose mode for detailed info

---

## Example 4: Searching Commands

**Scenario:** Finding specific commands in history.

**Steps:**

```bash
# Search for npm commands
trewind search "npm"

# Search for git commits
trewind search "git commit"

# Search with verbose output
trewind search "install" --verbose

# Limit search results
trewind search "error" --limit 10
```

**Expected Output:**
```
=== Search Results for 'npm' (5) ===

[OK] [2026-01-31 10:30:00] npm test
[OK] [2026-01-31 10:25:00] npm install axios
[X:1] [2026-01-31 10:20:00] npm run build
    Output: Error: Cannot find module...
[OK] [2026-01-31 10:15:00] npm init -y
[OK] [2026-01-31 10:10:00] npm --version
```

**What You Learned:**
- Full-text search across commands and outputs
- Finding relevant commands quickly
- Verbose mode shows output snippets

---

## Example 5: File Change Tracking

**Scenario:** Tracking which files are modified by commands.

**Steps:**

```bash
# Record a command and track file changes
trewind record "echo 'hello' > test.txt" --execute --track-files

# View the command with file changes
trewind show --verbose --limit 1
```

**Expected Output:**
```
[OK] Recorded command (ID: 42)
[OK] Command executed successfully
hello

=== Recent Commands (1) ===

[OK] [2026-01-31 10:35:00] echo 'hello' > test.txt
    [+] ./test.txt (created)
```

**What You Learned:**
- How to track file changes
- Created/modified/deleted tracking
- Automatic backup for rollback

---

## Example 6: Rollback Operations

**Scenario:** Undoing a destructive command.

**Steps:**

```bash
# First, create a file and record it
echo "important data" > important.txt
trewind record "rm important.txt" --execute --track-files

# Oops! We didn't mean to delete it
# Preview what rollback would do
trewind undo --dry-run

# Actually rollback
trewind undo --apply

# Verify file is restored
cat important.txt
```

**Expected Output:**
```
[DRY RUN] [OK] Rollback would be successful

Actions:
  [OK] restore: ./important.txt

[!] This was a dry run. Use --apply to actually perform rollback.
```

After `--apply`:
```
[OK] Rollback successful

Actions:
  [OK] restore: ./important.txt
```

**What You Learned:**
- How to preview rollback with dry run
- How to actually restore files
- Safety net for destructive commands

---

## Example 7: Agent Handoff Export

**Scenario:** Handing off work to another AI agent.

**Steps:**

```bash
# ATLAS completes some work
trewind start --name "Feature Implementation" --agent ATLAS

trewind log "git clone https://github.com/user/repo.git" --exit-code 0 --output "Cloning into 'repo'..."
trewind log "cd repo && npm install" --exit-code 0 --output "added 500 packages"
trewind log "npm run build" --exit-code 1 --error "TypeScript error in src/index.ts"

trewind end

# Export for CLIO to continue
trewind export --for-agent CLIO > handoff_to_clio.md

cat handoff_to_clio.md
```

**Expected Output:**
```markdown
# Agent Handoff Package for CLIO

## Context Summary

This terminal session is being handed off to **CLIO**.
**Total Commands:** 3
**Successful:** 2
**Errors:** 1
**Last Directory:** `/home/user/repo`
**Previous Agent:** ATLAS

## What Happened

1. [OK] `git clone https://github.com/user/repo.git`
2. [OK] `cd repo && npm install`
3. [X] `npm run build`

## Key Observations

- [!] Recent errors detected - review error outputs below
- Session involved 2 different directories

## Errors (if any)

**Command:** `npm run build`
**Exit Code:** 1
```
TypeScript error in src/index.ts
```

---
*Generated by TerminalRewind v1.0.0*
```

**What You Learned:**
- How to create agent handoff packages
- Complete context transfer between agents
- Error highlighting for quick issue identification

---

## Example 8: JSON Export for Analysis

**Scenario:** Exporting session data for programmatic analysis.

**Steps:**

```bash
# Export as JSON
trewind export --format json > session.json

# Pretty print to see structure
python -m json.tool session.json | head -50
```

**Expected Output:**
```json
{
  "export_timestamp": "2026-01-31T10:40:00.000000",
  "export_version": "1.0.0",
  "session": {
    "id": "20260131_100000",
    "name": "Feature Implementation",
    "started_at": "2026-01-31T10:00:00",
    "ended_at": "2026-01-31T10:35:00",
    "command_count": 15,
    "agent_name": "ATLAS"
  },
  "commands": [
    {
      "id": 1,
      "timestamp": "2026-01-31T10:00:05",
      "command": "git status",
      "cwd": "/home/user/project",
      "exit_code": 0,
      "output": "On branch main...",
      "duration_ms": 45,
      "file_changes": []
    }
  ],
  "stats": {
    "total_commands": 15,
    "successful_commands": 13,
    "failed_commands": 2,
    "success_rate": 86.7
  }
}
```

**What You Learned:**
- JSON export for programmatic access
- Complete session metadata
- Statistics included in export

---

## Example 9: Error Debugging Workflow

**Scenario:** A build fails and you need to find out why.

**Steps:**

```bash
# 1. First, see recent errors
trewind show --errors --since "1 hour ago"

# 2. Search for the specific error type
trewind search "TypeError" --verbose

# 3. Find what changed recently
trewind show --since "30 minutes ago" --verbose

# 4. Export for detailed analysis
trewind export --format markdown --since "1 hour ago" > debug_session.md
```

**Expected Output:**
```
=== Recent Errors ===

[X:1] [2026-01-31 10:28:30] npm run build
    Error: TypeError: Cannot read property 'map' of undefined

[X:127] [2026-01-31 10:20:15] node script.js
    Error: Cannot find module './config'
```

**What You Learned:**
- How to filter by errors
- Time-based filtering for debugging
- Combining search with verbose output

---

## Example 10: Complete Session Workflow

**Scenario:** A full work session from start to finish.

**Steps:**

```bash
# 1. Start the session
trewind start --name "API Implementation" --agent ATLAS

# 2. Work through the task, logging each step
trewind log "git pull origin main" --exit-code 0 --output "Already up to date."
trewind log "npm install express" --exit-code 0 --output "added 57 packages"
trewind log "mkdir src && touch src/server.js" --exit-code 0
trewind record "node src/server.js" --execute --track-files

# 3. Handle errors
trewind log "npm test" --exit-code 1 --error "Error: No tests found"

# 4. Fix and retry
trewind log "npm install --save-dev jest" --exit-code 0
trewind log "npm test" --exit-code 0 --output "Test Suites: 1 passed"

# 5. Commit the work
trewind log "git add -A && git commit -m 'Add API server'" --exit-code 0

# 6. End the session
trewind end

# 7. View statistics
trewind stats

# 8. Export for documentation
trewind export --format markdown > api_implementation_log.md
```

**Expected Output:**
```
=== TerminalRewind Statistics ===

Total Commands:     8
Successful:         7
Failed:             1
Success Rate:       87.5%
Total Sessions:     5
File Changes:       3

Database:           ~/.local/share/TerminalRewind/terminalrewind.db
Database Size:      156.78 KB
```

**What You Learned:**
- Complete workflow from start to finish
- Combining different recording methods
- Documentation generation

---

## Example 11: Integration with Python Scripts

**Scenario:** Using TerminalRewind programmatically.

**Steps:**

```python
#!/usr/bin/env python3
"""Example: Using TerminalRewind in Python scripts."""

from terminalrewind import (
    TerminalRewindDB,
    CommandRecorder,
    SessionExporter
)

# Initialize
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start a session
recorder.start_session(name="Automated Build", agent_name="BUILD_AGENT")

# Record commands
recorder.log(
    command="python setup.py build",
    exit_code=0,
    output="Building wheel...\nDone!",
    duration_ms=5230
)

recorder.log(
    command="pytest tests/",
    exit_code=0,
    output="42 passed, 0 failed"
)

# End session
recorder.end_session()

# Export results
exporter = SessionExporter(db)
report = exporter.to_markdown()
print(report)

# Get statistics
stats = db.get_stats()
print(f"\nSession Success Rate: {stats['success_rate']}%")

db.close()
```

**Expected Output:**
```
# Terminal Session Export

**Exported:** 2026-01-31 10:45:00
**Commands:** 2
**Session:** Automated Build
**Agent:** BUILD_AGENT

---

## Commands

### 1. [OK] `python setup.py build`

- **Time:** 2026-01-31 10:45:00
- **Directory:** `/home/user`
- **Duration:** 5230ms

**Output:**
```
Building wheel...
Done!
```

### 2. [OK] `pytest tests/`

- **Time:** 2026-01-31 10:45:05
- **Directory:** `/home/user`

**Output:**
```
42 passed, 0 failed
```

Session Success Rate: 100.0%
```

**What You Learned:**
- Python API for TerminalRewind
- Programmatic recording and export
- Integration into build scripts

---

## Example 12: Statistics and Analytics

**Scenario:** Understanding your terminal usage patterns.

**Steps:**

```bash
# View overall statistics
trewind stats

# See all sessions
trewind sessions --limit 20

# Export for trend analysis
trewind export --format json --limit 1000 > all_commands.json

# Analyze with Python
python3 << 'EOF'
import json

with open('all_commands.json') as f:
    data = json.load(f)

commands = data['commands']
print(f"Total commands: {len(commands)}")

# Most common commands
from collections import Counter
cmd_starts = [c['command'].split()[0] for c in commands if c['command']]
top_cmds = Counter(cmd_starts).most_common(10)

print("\nTop 10 command prefixes:")
for cmd, count in top_cmds:
    print(f"  {cmd}: {count}")

# Success rate over time
errors = [c for c in commands if c['exit_code'] and c['exit_code'] != 0]
print(f"\nTotal errors: {len(errors)}")
EOF
```

**Expected Output:**
```
=== TerminalRewind Statistics ===

Total Commands:     1,234
Successful:         1,180
Failed:             54
Success Rate:       95.6%
Total Sessions:     47
File Changes:       892

Database:           ~/.local/share/TerminalRewind/terminalrewind.db
Database Size:      2.34 MB

---

Total commands: 1000

Top 10 command prefixes:
  git: 287
  npm: 156
  cd: 134
  ls: 98
  python: 87
  cat: 65
  mkdir: 43
  echo: 41
  rm: 38
  curl: 31

Total errors: 42
```

**What You Learned:**
- Statistics for understanding patterns
- Exporting for custom analysis
- Identifying common commands and error rates

---

## Tips and Best Practices

### 1. Start Sessions with Meaningful Names
```bash
trewind start --name "Task-123: Fix login bug"
# Better than: trewind start
```

### 2. Always Include Exit Codes
```bash
trewind log "command" --exit-code $?
# Captures actual exit code
```

### 3. Track Files for Destructive Commands
```bash
trewind record "rm -rf build/" --execute --track-files
# Enables rollback if needed
```

### 4. Use Agent Names for Multi-Agent Work
```bash
trewind start --agent ATLAS
# Makes handoffs clearer
```

### 5. Export Before Long Breaks
```bash
trewind export --format markdown > session_backup.md
# Preserves context for later
```

---

**Last Updated:** January 31, 2026  
**Maintained By:** ATLAS (Team Brain)
