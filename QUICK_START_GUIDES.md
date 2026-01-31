# TerminalRewind - Quick Start Guides

## 📖 ABOUT THESE GUIDES

Each Team Brain agent has a **5-minute quick-start guide** tailored to their role and workflows.

**Choose your guide:**
- [Forge (Orchestrator)](#-forge-quick-start)
- [Atlas (Builder)](#-atlas-quick-start)
- [Clio (CLI Expert)](#-clio-quick-start)
- [Nexus (Multi-Platform)](#-nexus-quick-start)
- [Bolt (Free Executor)](#-bolt-quick-start)
- [IRIS (Desktop Agent)](#-iris-quick-start)

---

## 🔥 FORGE QUICK START

**Role:** Orchestrator / Reviewer  
**Time:** 5 minutes  
**Goal:** Review agent terminal sessions and coordinate handoffs

### Step 1: Installation Check

```bash
# Verify TerminalRewind is available
trewind --version

# Expected: TerminalRewind v1.0.0
```

### Step 2: Check Incoming Handoffs

```bash
# See all recent sessions
trewind sessions

# View a specific agent's session
trewind show --session atlas_20260131 --verbose
```

### Step 3: Review Agent Work

```bash
# See what ATLAS did recently
trewind show --limit 30 --verbose

# Search for errors in any session
trewind search "error" --verbose

# View only failed commands
trewind show --errors
```

### Step 4: Coordinate Handoffs

```bash
# Generate handoff for another agent
trewind export --for-agent CLIO > handoff_to_clio.md

# Or send via Synapse (Python)
```

```python
from synapselink import quick_send
from terminalrewind import SessionExporter, TerminalRewindDB

db = TerminalRewindDB()
exporter = SessionExporter(db)
handoff = exporter.for_agent("CLIO")

quick_send("CLIO", "Session Handoff from Forge", handoff)
```

### Common Forge Commands

```bash
# Review recent activity
trewind show --since "1 hour ago"

# Get statistics
trewind stats

# Export for documentation
trewind export --format markdown > session_review.md
```

### Next Steps for Forge

1. Read [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) - Forge section
2. Try [EXAMPLES.md](EXAMPLES.md) - Example 7 (Agent Handoff)
3. Add session review to your orchestration routine

---

## ⚡ ATLAS QUICK START

**Role:** Executor / Builder  
**Time:** 5 minutes  
**Goal:** Track tool builds and debug failures

### Step 1: Installation Check

```bash
python -c "from terminalrewind import CommandRecorder; print('[OK] Ready')"
# Expected: [OK] Ready
```

### Step 2: Start a Build Session

```bash
# Start named session
trewind start --name "Tool Build: TerminalRewind" --agent ATLAS

# Expected: [OK] Session started: 20260131_100000_Tool_Build__TerminalRewind
```

### Step 3: Log Your Work

```bash
# As you work, log each command
trewind log "python terminalrewind.py --version" --exit-code 0 --output "v1.0.0"
trewind log "python test_terminalrewind.py" --exit-code 0 --output "42 tests passed"

# Or execute and record
trewind record "python -m pytest" --execute
```

### Step 4: Debug Failures

```bash
# If something fails, check recent history
trewind show --since "10 minutes ago" --verbose

# Search for specific errors
trewind search "TypeError" --verbose

# View only errors
trewind show --errors
```

### Step 5: Complete and Handoff

```bash
# End session
trewind end

# Export for Forge review
trewind export --for-agent FORGE > build_complete_handoff.md
```

### Common Atlas Commands

```bash
# Track a build
trewind start --name "Building ToolXYZ" --agent ATLAS
trewind log "make build" --exit-code 0
trewind log "make test" --exit-code 0
trewind end

# Debug a failure
trewind show --errors --since "30 minutes ago"
trewind search "failed" --verbose
```

### Next Steps for Atlas

1. Integrate into Holy Grail automation
2. Add to tool build checklist
3. Use for every new tool build

---

## 🐧 CLIO QUICK START

**Role:** Linux / CLI Expert  
**Time:** 5 minutes  
**Goal:** Heavy CLI work with full history

### Step 1: Linux Installation

```bash
# Clone from GitHub
git clone https://github.com/DonkRonk17/TerminalRewind.git
cd TerminalRewind

# Install
pip3 install -e .

# Verify
trewind --version
```

### Step 2: Start CLI Session

```bash
# Start session for CLI work
trewind start --name "System Administration" --agent CLIO
```

### Step 3: Log Your Commands

```bash
# As a CLI expert, you might want to track everything
trewind log "apt-get update" --exit-code 0
trewind log "apt-get install nginx" --exit-code 0
trewind log "systemctl start nginx" --exit-code 0
trewind log "curl localhost" --exit-code 0 --output "Welcome to nginx!"
```

### Step 4: Search and Review

```bash
# Find previous nginx setup
trewind search "nginx"

# View recent system changes
trewind show --since "1 hour ago" --verbose

# Only errors
trewind show --errors
```

### Step 5: Export for Documentation

```bash
# Create documentation from session
trewind export --format markdown > system_setup_guide.md

# Export for team
trewind export --for-agent FORGE > clio_session_summary.md
```

### Common Clio Commands

```bash
# Quick session
trewind start -n "Server Config" -a CLIO
trewind log "command1" -e 0
trewind log "command2" -e 0
trewind end

# Search history
trewind search "docker" --limit 50
trewind search "systemctl" --verbose
```

### Platform-Specific Features

- Track package installations: `apt-get`, `yum`, `dnf`
- System services: `systemctl`, `service`
- Network configs: `iptables`, `netplan`
- User management: `useradd`, `chmod`, `chown`

### Next Steps for Clio

1. Add to ABIOS startup
2. Test on Ubuntu environment
3. Report Linux-specific issues

---

## 🌐 NEXUS QUICK START

**Role:** Multi-Platform Agent  
**Time:** 5 minutes  
**Goal:** Cross-platform terminal tracking

### Step 1: Platform Detection

```python
import platform
from terminalrewind import TerminalRewindDB, CommandRecorder

print(f"Platform: {platform.system()}")  # Windows, Linux, Darwin

db = TerminalRewindDB()
recorder = CommandRecorder(db)
recorder.start_session(
    name=f"Cross-Platform Work ({platform.system()})",
    agent_name="NEXUS"
)
```

### Step 2: Platform-Aware Commands

```bash
# Works on all platforms
trewind start --name "Cross-Platform Test" --agent NEXUS

# Windows
trewind log "dir" --exit-code 0

# Linux/macOS
trewind log "ls -la" --exit-code 0

trewind end
```

### Step 3: Track Platform Differences

```python
import platform
from terminalrewind import CommandRecorder, TerminalRewindDB

db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start with platform tag
recorder.start_session(
    name=f"Test on {platform.system()}",
    agent_name="NEXUS"
)

# Platform-specific commands
if platform.system() == "Windows":
    recorder.log("where python", exit_code=0)
else:
    recorder.log("which python", exit_code=0)

recorder.end_session()
```

### Step 4: Export with Platform Info

```bash
# Export includes platform field
trewind export --format json > session.json
# JSON includes: "platform": "Windows" or "Linux" etc.
```

### Common Nexus Commands

```bash
# Start cross-platform session
trewind start --name "Multi-Platform Testing" --agent NEXUS

# Platform-agnostic Python commands
trewind record "python --version" --execute
trewind record "pip list" --execute

trewind end
```

### Next Steps for Nexus

1. Test on all 3 platforms
2. Report platform-specific issues
3. Add to multi-platform workflows

---

## 🆓 BOLT QUICK START

**Role:** Free Executor (Cline + Grok)  
**Time:** 5 minutes  
**Goal:** Track task execution without API costs

### Step 1: Verify Free Access

```bash
# No API key required!
trewind --version
# Works completely offline and free
```

### Step 2: Task Execution Tracking

```bash
# Receive task from queue
trewind start --name "Task #123: Install Dependencies" --agent BOLT

# Execute and track
trewind record "npm install" --execute
trewind record "npm test" --execute

# Check for errors
trewind show --errors

trewind end
```

### Step 3: Export Results

```bash
# Export task results
trewind export --format json > task_123_results.json

# Or markdown for documentation
trewind export --format markdown > task_123_log.md
```

### Step 4: Batch Processing

```bash
# Process multiple tasks
for task in task_001 task_002 task_003; do
    trewind start --name "$task" --agent BOLT
    trewind record "./process_$task.sh" --execute
    trewind end
    trewind export --format json > "${task}_results.json"
done
```

### Cost Considerations

- **Zero external dependencies** = No API calls
- **SQLite storage** = No cloud costs
- **CLI interface** = No paid services
- **Perfect for high-volume tasks**

### Common Bolt Commands

```bash
# Quick task execution
trewind start -n "Task #X" -a BOLT
trewind record "command" --execute
trewind end
trewind export -f json > result.json
```

### Next Steps for Bolt

1. Add to Cline workflows
2. Use for repetitive tasks
3. Report any issues via Synapse

---

## 🖥️ IRIS QUICK START

**Role:** Desktop Agent (Tool Requester)  
**Time:** 5 minutes  
**Goal:** Desktop development terminal tracking

### Step 1: Windows Setup

```powershell
# Clone and install
git clone https://github.com/DonkRonk17/TerminalRewind.git
cd TerminalRewind
pip install -e .

# Verify
trewind --version
```

### Step 2: Desktop Development Session

```bash
# Start development session
trewind start --name "Desktop App Development" --agent IRIS

# Track development commands
trewind log "npm create tauri-app" --exit-code 0
trewind log "cd app && npm install" --exit-code 0
trewind log "npm run tauri dev" --exit-code 0
```

### Step 3: Track File Changes

```bash
# When modifying files, track changes
trewind record "npm run build" --execute --track-files

# Later, if needed, rollback
trewind undo --dry-run
trewind undo --apply
```

### Step 4: Handoff to Porter (Mobile)

```bash
# When handing off to Porter for mobile work
trewind export --for-agent PORTER > desktop_handoff.md
```

### Common IRIS Commands

```bash
# Desktop development
trewind start -n "BCH Desktop" -a IRIS
trewind log "npm run tauri build" -e 0
trewind end

# Export for team
trewind export --format markdown > session.md
```

### Special Thanks

IRIS requested this tool via Synapse TOOL_REQUEST. The vision:
- Command+Z for terminal
- Agent handoff support
- File rollback capability

**Thank you for the inspiration!**

### Next Steps for IRIS

1. Test with Tauri development
2. Coordinate with Porter for mobile handoffs
3. Report Windows-specific issues

---

## 📚 ADDITIONAL RESOURCES

**For All Agents:**
- Full Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Integration Plan: [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- Cheat Sheet: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Support:**
- GitHub Issues: https://github.com/DonkRonk17/TerminalRewind/issues
- Synapse: Post in THE_SYNAPSE/active/
- Direct: Message ATLAS

---

**Last Updated:** January 31, 2026  
**Maintained By:** ATLAS (Team Brain)
