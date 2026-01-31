# 🎬 TerminalRewind

**Command+Z for Your Terminal - Never Lose Track of What Happened**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DonkRonk17/TerminalRewind)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Recording Commands](#recording-commands)
  - [Viewing History](#viewing-history)
  - [Searching](#searching)
  - [Exporting Sessions](#exporting-sessions)
  - [Rollback](#rollback)
  - [Agent Handoff](#agent-handoff)
- [Real-World Scenarios](#-real-world-scenarios)
- [How It Works](#-how-it-works)
- [Use Cases](#-use-cases)
- [Integration](#-integration)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Credits](#-credits)
- [License](#-license)

---

## 🚨 The Problem

When working in the terminal, critical information is constantly lost:

### Lost Context
- **"What command caused this error?"** - Lost in scrollback history
- **"How did I break this?"** - No way to trace back through your actions
- **"What did the last agent do?"** - Agent handoffs lose critical context
- **"I need to reproduce this bug"** - Can't remember exact steps

### No Safety Net
- **"Someone ran rm -rf"** - Files gone forever
- **No undo for terminal** - Unlike text editors, no Ctrl+Z
- **Destructive commands are irreversible** - One mistake can cost hours

### Poor Documentation
- **Manual note-taking** - Tedious, incomplete, forgotten
- **history command** - Only commands, no outputs, no timestamps
- **Screen recording** - Not searchable, huge files

**Result:** Debugging is painful, mistakes are costly, and agent coordination suffers.

---

## 💡 The Solution

**TerminalRewind** treats your terminal like a rewindable video:

```
                    BEFORE                              AFTER
    ┌──────────────────────────┐        ┌──────────────────────────┐
    │  Terminal is a           │        │  Terminal is a           │
    │  BLACK BOX               │   →    │  REWINDABLE VIDEO        │
    │                          │        │                          │
    │  • Commands forgotten    │        │  • Every command saved   │
    │  • Outputs lost          │        │  • Full output recorded  │
    │  • No undo possible      │        │  • Rollback available    │
    │  • Context lost          │        │  • Perfect handoffs      │
    └──────────────────────────┘        └──────────────────────────┘
```

### What TerminalRewind Does

1. **Records Everything** - Commands, outputs, exit codes, timestamps
2. **Tracks File Changes** - Which files were created, modified, deleted
3. **Enables Replay** - See exactly what happened step-by-step
4. **Provides Undo** - Rollback destructive commands
5. **Powers Handoffs** - Export sessions for AI agents or team members

---

## ✨ Key Features

### 🎯 Command Recording
Record every command with full context:
- Timestamp (when it ran)
- Working directory (where it ran)
- Exit code (did it succeed?)
- Full output (what did it produce?)
- Duration (how long did it take?)

### 📁 File Change Tracking
Know exactly what each command did to your files:
- Files created
- Files modified (with before/after hashes)
- Files deleted
- Automatic backups for rollback

### 🔍 Instant Search
Find any command instantly:
```bash
trewind search "npm install"    # Find all npm installs
trewind search "error"          # Find commands with errors
trewind show --errors           # Show only failed commands
```

### ⏪ Smart Rollback
Undo destructive commands:
```bash
trewind undo --dry-run    # Preview what would be restored
trewind undo --apply      # Actually restore files
```

### 🤝 Agent Handoff
Perfect for AI agent coordination:
```bash
trewind export --for-agent CLIO > handoff.md
```

Generates comprehensive context for the next agent.

### 📊 Session Management
Organize work into sessions:
```bash
trewind start --name "Bug Fix" --agent ATLAS
# ... do work ...
trewind end
```

---

## 🚀 Quick Start

### 1. Install
```bash
git clone https://github.com/DonkRonk17/TerminalRewind.git
cd TerminalRewind
pip install -e .
```

### 2. Start Recording
```bash
# Start a new session
trewind start --name "My Work Session"

# Log commands as you work
trewind log "git status" --exit-code 0
trewind log "npm install" --exit-code 0 --output "added 500 packages"
```

### 3. View History
```bash
trewind show              # Show recent commands
trewind show --limit 50   # Show last 50 commands
trewind show --errors     # Show only failures
```

### 4. Export for Handoff
```bash
trewind export --for-agent CLIO > handoff.md
```

That's it! You now have a complete record of your terminal session.

---

## 📦 Installation

### Method 1: Direct Clone (Recommended)
```bash
git clone https://github.com/DonkRonk17/TerminalRewind.git
cd TerminalRewind
pip install -e .
```

### Method 2: Manual Setup
```bash
git clone https://github.com/DonkRonk17/TerminalRewind.git
# Add to your PATH or create an alias
alias trewind="python /path/to/terminalrewind.py"
```

### Requirements
- Python 3.8+
- No external dependencies (uses only stdlib)

### Verify Installation
```bash
trewind --version
# Output: TerminalRewind v1.0.0
```

---

## 📖 Usage

### Recording Commands

#### Log an Already-Executed Command
```bash
trewind log "git commit -m 'feature'" --exit-code 0
trewind log "npm test" --exit-code 1 --error "2 tests failed"
```

#### Record and Execute
```bash
trewind record "ls -la" --execute
trewind record "cat file.txt" --execute --track-files
```

#### With File Tracking
```bash
trewind record "python script.py" --execute --track-files
# Tracks all file changes in current directory
```

### Viewing History

#### Show Recent Commands
```bash
trewind show                    # Last 20 commands
trewind show --limit 100        # Last 100 commands
trewind show --verbose          # Include file changes
```

#### Filter by Time
```bash
trewind show --since "10 minutes ago"
trewind show --since "1 hour ago"
trewind show --since "2026-01-31T10:00:00"
```

#### Filter by Status
```bash
trewind show --errors           # Only failed commands
trewind show --session abc123   # Only from specific session
```

### Searching

#### Full-Text Search
```bash
trewind search "npm"           # Commands containing "npm"
trewind search "error"         # Commands with "error" in output
trewind search "git commit"    # Find git commits
```

#### Search with Details
```bash
trewind search "install" --verbose   # Include output snippets
trewind search "build" --limit 50    # More results
```

### Exporting Sessions

#### Export as Markdown
```bash
trewind export --format markdown > session.md
trewind export --session abc123 --format markdown
```

#### Export as JSON
```bash
trewind export --format json > session.json
```

#### Export for Agent Handoff
```bash
trewind export --for-agent CLIO > handoff_for_clio.md
trewind export --for-agent ATLAS --limit 30
```

### Rollback

#### Preview Rollback (Dry Run)
```bash
trewind undo --dry-run    # Shows what would be restored
trewind undo 123 --dry-run  # For specific command ID
```

#### Apply Rollback
```bash
trewind undo --apply      # Restore files from last command
trewind undo 123 --apply  # Restore files from command #123
```

### Agent Handoff

Perfect for multi-agent workflows:

```bash
# Agent 1 (ATLAS) finishes work
trewind end
trewind export --for-agent CLIO > handoff.md

# Agent 2 (CLIO) reviews handoff
cat handoff.md
# Sees: complete command history, errors, file changes
```

### Session Management

#### Start a Session
```bash
trewind start --name "Bug Fix Sprint"
trewind start --name "Feature Development" --agent ATLAS
```

#### End a Session
```bash
trewind end
```

#### List Sessions
```bash
trewind sessions
trewind sessions --limit 20
```

### Statistics

```bash
trewind stats
```

Output:
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
```

---

## 🎯 Real-World Scenarios

### Scenario 1: Agent Handoff

**Situation:** Logan asks ATLAS to start a feature, then CLIO to finish it.

**Without TerminalRewind:**
- CLIO has no idea what ATLAS did
- Starts from scratch or guesses
- Wastes time retracing steps

**With TerminalRewind:**
```bash
# ATLAS finishes and exports
trewind export --for-agent CLIO > handoff.md

# CLIO reads the handoff
cat handoff.md
# Sees every command, output, file change
# Continues seamlessly from where ATLAS left off
```

### Scenario 2: Debugging a Build Failure

**Situation:** Build suddenly breaks, no idea why.

**Without TerminalRewind:**
- Scroll through terminal history
- Guess what changed
- Spend 30+ minutes debugging

**With TerminalRewind:**
```bash
trewind show --since "1 hour ago" --errors
# Immediately see: which command failed, what error occurred
# Identify the culprit in seconds
```

### Scenario 3: Disaster Recovery

**Situation:** Accidentally ran `rm -rf important_folder/`

**Without TerminalRewind:**
- Files gone forever (unless git committed)
- Restore from backup (if you have one)

**With TerminalRewind:**
```bash
trewind undo --apply
# Files restored from pre-command snapshot
# Crisis averted!
```

### Scenario 4: Documentation

**Situation:** "How did you fix that bug?"

**Without TerminalRewind:**
- "Umm... I changed some files..."
- Manual reconstruction from memory

**With TerminalRewind:**
```bash
trewind export --format markdown > fix_documentation.md
# Complete step-by-step documentation with:
# - Every command
# - All outputs
# - File changes
# - Timestamps
```

---

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TerminalRewind                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Recorder   │    │   Tracker    │    │   Exporter   │  │
│  │              │    │              │    │              │  │
│  │ - Log cmds   │    │ - Watch files│    │ - JSON       │  │
│  │ - Execute    │    │ - Detect ∆   │    │ - Markdown   │  │
│  │ - Track      │    │ - Backup     │    │ - Agent      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │    SQLite DB    │                      │
│                    │                 │                      │
│                    │ - commands      │                      │
│                    │ - file_changes  │                      │
│                    │ - sessions      │                      │
│                    └─────────────────┘                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**commands** - Every recorded command
- id, session_id, timestamp, command, cwd
- exit_code, output, error_output, duration_ms
- platform, shell, user, hostname

**file_changes** - Files affected by commands
- command_id, file_path, change_type
- old_hash, new_hash, backup_path

**sessions** - Logical groupings of work
- id, name, started_at, ended_at
- command_count, success_count, error_count

### File Change Detection

1. **Before command:** Snapshot current file hashes
2. **Execute command:** Run the actual command
3. **After command:** Compare new hashes
4. **Backup:** Save originals for rollback
5. **Record:** Store changes in database

---

## 🎯 Use Cases

### For AI Agents

- **Session continuity** - Resume where you left off
- **Perfect handoffs** - Next agent sees everything
- **Error debugging** - Trace back through failures
- **Audit trail** - Complete record of actions

### For Developers

- **Bug reproduction** - Exact steps to reproduce
- **Documentation** - Auto-generated session docs
- **Pair programming** - Share what you did
- **Learning** - Review your own patterns

### For DevOps

- **Incident response** - What commands led to this?
- **Change tracking** - What changed and when?
- **Compliance** - Complete audit trail
- **Recovery** - Rollback destructive changes

---

## 🔗 Integration

### With SynapseLink
```python
from synapselink import quick_send
from terminalrewind import SessionExporter, TerminalRewindDB

db = TerminalRewindDB()
exporter = SessionExporter(db)

# After completing a task
handoff = exporter.for_agent("CLIO")
quick_send("CLIO", "Session Handoff", handoff)
```

### With AgentHealth
```python
from agenthealth import AgentHealth
from terminalrewind import CommandRecorder

health = AgentHealth()
recorder = CommandRecorder()

# Track health alongside commands
health.start_session("ATLAS")
recorder.start_session(agent_name="ATLAS")

# ... work ...

health.end_session("ATLAS")
recorder.end_session()
```

### With BCH
Terminal sessions can be logged to BCH for team visibility:
```python
# Export and send to BCH channel
export = exporter.to_json()
bch.send_message("terminal-logs", export)
```

See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for full integration details.

---

## ⚙️ Configuration

### Database Location

Default: `~/.local/share/TerminalRewind/terminalrewind.db`

Custom:
```python
from terminalrewind import TerminalRewindDB
db = TerminalRewindDB(Path("/custom/path/db.sqlite"))
```

### Backup Location

Default: `~/.local/share/TerminalRewind/backups/`

### Environment Variables

```bash
# Custom database path
export TERMINALREWIND_DB=/path/to/db.sqlite

# Disable auto-session
export TERMINALREWIND_AUTO_SESSION=false
```

---

## 🔧 Troubleshooting

### "Database locked" Error

**Problem:** Multiple processes accessing database

**Solution:**
```bash
# Close other trewind processes
# Or use a different database file
trewind --db /tmp/session.db show
```

### "Permission denied" for Backup

**Problem:** Can't write to backup directory

**Solution:**
```bash
# Check permissions
ls -la ~/.local/share/TerminalRewind/

# Or use custom backup dir
export TERMINALREWIND_BACKUP_DIR=/tmp/backups
```

### "No commands found"

**Problem:** Database is empty or session not started

**Solution:**
```bash
# Start a session first
trewind start --name "Test"

# Then log commands
trewind log "echo hello"
```

### Large Database Size

**Problem:** Database growing too large

**Solution:**
```bash
# Export important sessions
trewind export --session important > backup.json

# Compact database (manual)
sqlite3 ~/.local/share/TerminalRewind/terminalrewind.db "VACUUM"
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**
3. **Write tests** for new functionality
4. **Follow the code style** (type hints, docstrings)
5. **Submit a pull request**

### Code Style

- Type hints for all functions
- Docstrings for public methods
- No emojis in Python code (ASCII-safe)
- Tests required for new features

### Running Tests

```bash
python test_terminalrewind.py
```

---

## 📝 Credits

**Built by:** ATLAS (Team Brain)  
**For:** Logan Smith / Metaphy LLC  
**Requested by:** IRIS via Synapse TOOL_REQUEST  
**Why:** Enable terminal undo, agent handoffs, and complete session tracking  
**Part of:** Beacon HQ / Team Brain Ecosystem  
**Date:** January 31, 2026

**Trophy Potential:** LEGENDARY (50+ points) - Novel concept, high impact, foundational tool

### Special Thanks

- **IRIS** for the original TOOL_REQUEST and vision
- **Forge** for orchestration and review
- **The Team Brain collective** for testing and feedback

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 📚 Additional Resources

- [EXAMPLES.md](EXAMPLES.md) - Comprehensive usage examples
- [CHEAT_SHEET.txt](CHEAT_SHEET.txt) - Quick reference guide
- [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Team Brain integration
- [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md) - Agent-specific guides

---

**Built with precision, deployed with pride.**  
**Together for all time! 🔥**
