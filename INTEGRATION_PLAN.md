# TerminalRewind - Integration Plan

## 🎯 INTEGRATION GOALS

This document outlines how TerminalRewind integrates with:
1. Team Brain agents (Forge, Atlas, Clio, Nexus, Bolt)
2. Existing Team Brain tools
3. BCH (Beacon Command Hub) - future integration
4. Logan's workflows

---

## 📦 BCH INTEGRATION

### Overview

TerminalRewind can be integrated with BCH to provide terminal session visibility across all agents and channels.

### BCH Commands (Future)

```
@terminal show                    # Show recent terminal activity
@terminal session <agent>         # View specific agent's session
@terminal handoff <to_agent>      # Generate and send handoff
@terminal search <pattern>        # Search terminal history
```

### Implementation Steps

1. **Add API endpoint** to BCH backend for terminal queries
2. **Create command handlers** in BCH for terminal commands
3. **WebSocket updates** for real-time terminal activity feed
4. **Dashboard widget** showing terminal session status

### Integration Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Agent Session  │     │  TerminalRewind │     │      BCH        │
│                 │────▶│                 │────▶│                 │
│  CLI Commands   │     │  SQLite DB      │     │  WebSocket API  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Team Brain     │
                        │  Dashboard      │
                        └─────────────────┘
```

---

## 🤖 AI AGENT INTEGRATION

### Integration Matrix

| Agent | Use Case | Integration Method | Priority |
|-------|----------|-------------------|----------|
| **Forge** | Review session handoffs, orchestrate multi-agent work | CLI + Python | HIGH |
| **Atlas** | Track tool builds, debug failures | CLI + Python | HIGH |
| **Clio** | CLI expert, primary terminal user | CLI | HIGH |
| **Nexus** | Cross-platform coordination | Python API | MEDIUM |
| **Bolt** | Task execution tracking | CLI | MEDIUM |
| **IRIS** | Desktop agent, requested tool | CLI + Python | HIGH |
| **Porter** | Mobile context, receive handoffs | JSON Export | LOW |

### Agent-Specific Workflows

---

#### Forge (Orchestrator / Reviewer)

**Primary Use Case:** Review agent terminal sessions, coordinate handoffs, debug failures across agents.

**Integration Steps:**
1. Start of session: Check for pending handoffs via Synapse
2. Review incoming handoffs: `trewind export --for-agent FORGE`
3. Orchestrate work: Assign tasks with session context
4. End of session: Export summary for next orchestrator

**Example Workflow:**

```python
# Forge session start - check for handoffs
from terminalrewind import TerminalRewindDB, SessionExporter
from synapselink import check_synapse

db = TerminalRewindDB()
exporter = SessionExporter(db)

# Check if Atlas left a handoff
handoffs = check_synapse(to="FORGE", type="terminal_handoff")
if handoffs:
    print("Atlas handed off terminal session:")
    print(handoffs[0].content)

# During review - check specific session
sessions = db.get_sessions(limit=10)
for s in sessions:
    if s['agent_name'] == 'ATLAS':
        print(f"Atlas session: {s['command_count']} commands, {s['error_count']} errors")
```

**CLI Usage:**

```bash
# Review Atlas's recent work
trewind show --session atlas_20260131 --verbose

# Search for errors in any session
trewind search "error" --limit 50

# Export summary for Synapse
trewind export --format markdown > forge_review.md
```

---

#### Atlas (Executor / Builder)

**Primary Use Case:** Track tool builds, record development sessions, debug test failures.

**Integration Steps:**
1. Start session: `trewind start --name "Tool Build: XYZ" --agent ATLAS`
2. Track all commands during build
3. On error: Use history to debug
4. End session: Export for Forge review

**Example Workflow:**

```python
from terminalrewind import CommandRecorder, TerminalRewindDB
from synapselink import quick_send

db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start tool build session
recorder.start_session(name="TerminalRewind Build", agent_name="ATLAS")

# Record commands as we work
recorder.log("git init", exit_code=0)
recorder.log("python terminalrewind.py --version", exit_code=0, output="v1.0.0")
recorder.log("python test_terminalrewind.py", exit_code=0, output="42 tests passed")

# End session and notify
recorder.end_session()

# Send handoff to Forge
exporter = SessionExporter(db)
handoff = exporter.for_agent("FORGE")
quick_send("FORGE", "TerminalRewind Build Complete", handoff)
```

**CLI Usage:**

```bash
# Start build session
trewind start --name "TerminalRewind Build" --agent ATLAS

# Log commands as you work
trewind log "python terminalrewind.py --help" --exit-code 0
trewind log "python test_terminalrewind.py" --exit-code 0 --output "42 tests passed"

# End and export
trewind end
trewind export --for-agent FORGE > handoff.md
```

---

#### Clio (Linux / CLI Expert)

**Primary Use Case:** Heavy CLI usage, system administration, debugging.

**Platform Considerations:**
- Primary platform: Ubuntu/Linux
- Uses bash/zsh extensively
- System-level commands

**Integration Steps:**
1. Automatic session logging for all terminal work
2. Quick search for command patterns
3. Export for documentation

**Example Workflow:**

```bash
# Clio session - heavy CLI work
trewind start --name "Server Setup" --agent CLIO

# Log system commands
trewind log "apt-get update" --exit-code 0
trewind log "apt-get install nginx" --exit-code 0
trewind log "systemctl start nginx" --exit-code 0
trewind log "curl localhost" --exit-code 0 --output "Welcome to nginx!"

# Search for previous similar work
trewind search "nginx"

# Export for documentation
trewind export --format markdown > server_setup_guide.md
```

**Linux-Specific Features:**
- Track package installations
- System service management
- Permission changes
- Network configurations

---

#### Nexus (Multi-Platform Agent)

**Primary Use Case:** Cross-platform coordination, ensuring commands work everywhere.

**Platform Considerations:**
- Works on Windows, Linux, macOS
- Tests cross-platform compatibility
- Documents platform differences

**Example Workflow:**

```python
import platform
from terminalrewind import CommandRecorder, TerminalRewindDB

db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start with platform awareness
recorder.start_session(
    name=f"Cross-Platform Test ({platform.system()})",
    agent_name="NEXUS"
)

# Record platform-specific commands
if platform.system() == "Windows":
    recorder.log("dir", exit_code=0)
else:
    recorder.log("ls -la", exit_code=0)

# Export with platform info
exporter = SessionExporter(db)
export = exporter.to_json()
# JSON includes platform field for analysis
```

---

#### Bolt (Free Executor)

**Primary Use Case:** Execute tasks from queue, track progress without API costs.

**Cost Considerations:**
- Zero external dependencies = free execution
- SQLite storage = no cloud costs
- CLI interface = no API calls

**Example Workflow:**

```bash
# Bolt receives task from queue
trewind start --name "Task from Queue: #123" --agent BOLT

# Execute task commands
trewind record "npm install" --execute --track-files
trewind record "npm test" --execute

# Export results
trewind export --format json > task_123_results.json

trewind end
```

---

## 🔗 INTEGRATION WITH OTHER TEAM BRAIN TOOLS

### With AgentHealth

**Correlation Use Case:** Track terminal activity alongside agent health metrics.

**Integration Pattern:**

```python
from agenthealth import AgentHealth
from terminalrewind import CommandRecorder, TerminalRewindDB

health = AgentHealth()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Use shared session_id
session_id = "build_session_001"

health.start_session("ATLAS", session_id=session_id)
recorder.start_session(name="Build Session", agent_name="ATLAS")

try:
    # Do work
    recorder.log("make build", exit_code=0)
    health.heartbeat("ATLAS", status="active")
    
except Exception as e:
    # Log error to both systems
    recorder.log("build failed", exit_code=1, error_output=str(e))
    health.log_error("ATLAS", str(e))
    
finally:
    health.end_session("ATLAS", session_id=session_id)
    recorder.end_session()
```

### With SynapseLink

**Notification Use Case:** Send terminal session summaries via Synapse.

**Integration Pattern:**

```python
from synapselink import quick_send
from terminalrewind import SessionExporter, TerminalRewindDB

db = TerminalRewindDB()
exporter = SessionExporter(db)

# Complete work
# ...

# Notify team with session summary
session_summary = exporter.to_markdown(limit=10)
quick_send(
    "FORGE,CLIO",
    "Terminal Session Complete",
    session_summary,
    priority="NORMAL"
)

# Or send full handoff
handoff = exporter.for_agent("CLIO")
quick_send(
    "CLIO",
    "Handoff: Build Session Complete",
    handoff,
    priority="NORMAL"
)
```

### With TaskQueuePro

**Task Management Use Case:** Track terminal sessions per task.

**Integration Pattern:**

```python
from taskqueuepro import TaskQueuePro
from terminalrewind import CommandRecorder, SessionExporter, TerminalRewindDB

queue = TaskQueuePro()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Get task from queue
task = queue.get_next_task()

# Start terminal session for this task
recorder.start_session(
    name=f"Task {task.id}: {task.title}",
    agent_name="ATLAS"
)

try:
    # Execute task
    recorder.log("npm install", exit_code=0)
    recorder.log("npm test", exit_code=0)
    
    # Export session as task artifact
    exporter = SessionExporter(db)
    session_log = exporter.to_markdown()
    
    # Complete task with artifacts
    queue.complete_task(task.id, artifacts={"terminal_log": session_log})
    
except Exception as e:
    queue.fail_task(task.id, error=str(e))
    
finally:
    recorder.end_session()
```

### With MemoryBridge

**Context Persistence Use Case:** Save terminal sessions to memory core.

**Integration Pattern:**

```python
from memorybridge import MemoryBridge
from terminalrewind import SessionExporter, TerminalRewindDB

memory = MemoryBridge()
db = TerminalRewindDB()
exporter = SessionExporter(db)

# After completing important work
session_data = exporter.to_json()

# Save to memory core
memory.set(
    f"terminal_sessions/{session_id}",
    session_data,
    metadata={"agent": "ATLAS", "type": "terminal_session"}
)
memory.sync()

# Later, retrieve for context
previous_session = memory.get(f"terminal_sessions/{session_id}")
```

### With SessionReplay

**Debugging Use Case:** Correlate SessionReplay events with terminal commands.

**Integration Pattern:**

```python
from sessionreplay import SessionReplay
from terminalrewind import CommandRecorder, TerminalRewindDB

replay = SessionReplay()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start both with same session ID
session_id = "debug_session_001"
replay.start_session("ATLAS", task="Debugging")
recorder.start_session(name="Debug Session", agent_name="ATLAS")

# Log to both
replay.log_input(session_id, "Running diagnostic command")
recorder.log("python diagnose.py", exit_code=0, output="Issue found: ...")
replay.log_output(session_id, "Diagnosis complete")

# End both
replay.end_session(session_id, status="COMPLETED")
recorder.end_session()
```

### With ContextCompressor

**Token Optimization Use Case:** Compress terminal outputs before sharing.

**Integration Pattern:**

```python
from contextcompressor import ContextCompressor
from terminalrewind import SessionExporter, TerminalRewindDB

compressor = ContextCompressor()
db = TerminalRewindDB()
exporter = SessionExporter(db)

# Get session export
full_export = exporter.to_markdown(limit=100)

# Compress for token-limited contexts
compressed = compressor.compress_text(
    full_export,
    query="key commands and errors",
    method="summary"
)

print(f"Original: {len(full_export)} chars")
print(f"Compressed: {len(compressed.compressed_text)} chars")
print(f"Savings: {compressed.estimated_token_savings} tokens")

# Use compressed version for AI context
```

### With ConfigManager

**Configuration Use Case:** Centralize TerminalRewind settings.

**Integration Pattern:**

```python
from configmanager import ConfigManager
from terminalrewind import TerminalRewindDB

config = ConfigManager()

# Load TerminalRewind config
tr_config = config.get("terminalrewind", {
    "database_path": "~/.local/share/TerminalRewind/terminalrewind.db",
    "backup_days": 7,
    "max_output_size": 100000,
    "default_agent": None
})

# Initialize with config
from pathlib import Path
db = TerminalRewindDB(Path(tr_config["database_path"]).expanduser())
```

---

## 🚀 ADOPTION ROADMAP

### Phase 1: Core Adoption (Week 1)

**Goal:** All agents aware and can use basic features

**Steps:**
1. [x] Tool deployed to GitHub
2. [ ] Quick-start guides sent via Synapse
3. [ ] Each agent tests basic workflow
4. [ ] Feedback collected

**Success Criteria:**
- All 5+ agents have used tool at least once
- No blocking issues reported

### Phase 2: Integration (Week 2-3)

**Goal:** Integrated into daily workflows

**Steps:**
1. [ ] Add to agent startup routines
2. [ ] Create integration examples with existing tools
3. [ ] Update agent-specific workflows
4. [ ] Monitor usage patterns

**Success Criteria:**
- Used daily by at least 3 agents
- Integration examples tested

### Phase 3: Optimization (Week 4+)

**Goal:** Optimized and fully adopted

**Steps:**
1. [ ] Collect efficiency metrics
2. [ ] Implement v1.1 improvements
3. [ ] Create advanced workflow examples
4. [ ] Full Team Brain ecosystem integration

**Success Criteria:**
- Measurable time savings on debugging
- Positive feedback from all agents
- v1.1 improvements identified

---

## 📊 SUCCESS METRICS

**Adoption Metrics:**
- Number of agents using tool: Track
- Daily usage count: Track
- Sessions recorded: Track
- Handoffs generated: Track

**Efficiency Metrics:**
- Time saved on debugging: Estimate 30+ min/incident
- Context transfer quality: Measure handoff completeness
- Error reproduction time: Track reduction

**Quality Metrics:**
- Bug reports: Track
- Feature requests: Track
- User satisfaction: Qualitative feedback

---

## 🛠️ TECHNICAL INTEGRATION DETAILS

### Import Paths

```python
# Standard import
from terminalrewind import TerminalRewindDB, CommandRecorder, SessionExporter

# Specific imports
from terminalrewind import (
    TerminalRewindDB,
    FileTracker,
    CommandRecorder,
    SessionExporter,
    RollbackManager,
    VERSION
)
```

### Configuration Integration

**Config File:** `~/.terminalrewindrc` (optional)

```json
{
  "database_path": "~/.local/share/TerminalRewind/terminalrewind.db",
  "backup_dir": "~/.local/share/TerminalRewind/backups",
  "backup_days": 7,
  "max_output_size": 100000,
  "default_agent": "ATLAS"
}
```

### Error Handling Integration

**Standardized Error Codes:**
- 0: Success
- 1: General error
- 2: Database error
- 3: File not found
- 4: Permission denied
- 5: Invalid input

### Logging Integration

**Log Format:** Compatible with Team Brain standard

**Log Location:** `~/.teambrain/logs/terminalrewind.log`

---

## 🔧 MAINTENANCE & SUPPORT

### Update Strategy

- Minor updates (v1.x): As needed
- Major updates (v2.0+): Quarterly
- Bug fixes: Immediate

### Support Channels

- GitHub Issues: Bug reports
- Synapse: Team Brain discussions
- Direct to Builder: Complex issues

### Known Limitations

- File rollback limited to tracked operations
- Large outputs truncated (100KB default)
- SQLite single-writer limitation

### Planned Improvements

- v1.1: Shell integration (auto-capture)
- v1.2: TUI interface
- v2.0: Distributed sessions

---

## 📚 ADDITIONAL RESOURCES

- Main Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Quick Start Guides: [QUICK_START_GUIDES.md](QUICK_START_GUIDES.md)
- Integration Examples: [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)
- GitHub: https://github.com/DonkRonk17/TerminalRewind

---

**Last Updated:** January 31, 2026  
**Maintained By:** ATLAS (Team Brain)
