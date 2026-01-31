# TerminalRewind - Integration Examples

## 🎯 INTEGRATION PHILOSOPHY

TerminalRewind is designed to work seamlessly with other Team Brain tools. This document provides **copy-paste-ready code examples** for common integration patterns.

---

## 📚 TABLE OF CONTENTS

1. [Pattern 1: TerminalRewind + AgentHealth](#pattern-1-terminalrewind--agenthealth)
2. [Pattern 2: TerminalRewind + SynapseLink](#pattern-2-terminalrewind--synapselink)
3. [Pattern 3: TerminalRewind + TaskQueuePro](#pattern-3-terminalrewind--taskqueuepro)
4. [Pattern 4: TerminalRewind + MemoryBridge](#pattern-4-terminalrewind--memorybridge)
5. [Pattern 5: TerminalRewind + SessionReplay](#pattern-5-terminalrewind--sessionreplay)
6. [Pattern 6: TerminalRewind + ContextCompressor](#pattern-6-terminalrewind--contextcompressor)
7. [Pattern 7: TerminalRewind + ConfigManager](#pattern-7-terminalrewind--configmanager)
8. [Pattern 8: TerminalRewind + ErrorRecovery](#pattern-8-terminalrewind--errorrecovery)
9. [Pattern 9: Multi-Tool Workflow](#pattern-9-multi-tool-workflow)
10. [Pattern 10: Full Team Brain Stack](#pattern-10-full-team-brain-stack)

---

## Pattern 1: TerminalRewind + AgentHealth

**Use Case:** Correlate terminal activity with agent health monitoring

**Why:** Understand how terminal operations affect agent performance and detect issues early

**Code:**

```python
from agenthealth import AgentHealth
from terminalrewind import TerminalRewindDB, CommandRecorder

# Initialize both tools
health = AgentHealth()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start session with shared context
session_id = "build_session_001"
agent_name = "ATLAS"

health.start_session(agent_name, session_id=session_id)
recorder.start_session(name="Build Session", agent_name=agent_name)

try:
    # Do work with health monitoring
    health.heartbeat(agent_name, status="active")
    
    recorder.log(
        command="npm install",
        exit_code=0,
        output="added 500 packages"
    )
    
    health.heartbeat(agent_name, status="processing")
    
    recorder.log(
        command="npm test",
        exit_code=0,
        output="42 tests passed"
    )
    
    # Success
    health.heartbeat(agent_name, status="completed")
    
except Exception as e:
    # Log error to both systems
    recorder.log(
        command="failed_operation",
        exit_code=1,
        error_output=str(e)
    )
    health.log_error(agent_name, str(e))
    
finally:
    health.end_session(agent_name, session_id=session_id)
    recorder.end_session()
    db.close()
```

**Result:** Correlated health and terminal data for comprehensive debugging

---

## Pattern 2: TerminalRewind + SynapseLink

**Use Case:** Notify Team Brain when terminal sessions complete

**Why:** Keep team informed of agent activities automatically

**Code:**

```python
from synapselink import quick_send
from terminalrewind import TerminalRewindDB, SessionExporter

db = TerminalRewindDB()
exporter = SessionExporter(db)

# After completing work...

# Option 1: Send summary
session_summary = exporter.to_markdown(limit=10)
quick_send(
    "FORGE,CLIO",
    "Terminal Session Complete",
    session_summary,
    priority="NORMAL"
)

# Option 2: Send full handoff
handoff = exporter.for_agent("CLIO")
quick_send(
    "CLIO",
    "Handoff: Build Session Complete",
    handoff,
    priority="NORMAL"
)

# Option 3: Alert on errors
commands = db.get_commands(with_errors=True, limit=5)
if commands:
    error_summary = "\n".join([
        f"- `{c['command']}`: {c['error_output'][:100]}"
        for c in commands
    ])
    quick_send(
        "FORGE,LOGAN",
        "[!] Terminal Errors Detected",
        f"Recent errors:\n{error_summary}",
        priority="HIGH"
    )

db.close()
```

**Result:** Team stays informed without manual status updates

---

## Pattern 3: TerminalRewind + TaskQueuePro

**Use Case:** Manage terminal sessions per task

**Why:** Track which commands belong to which task for organized workflows

**Code:**

```python
from taskqueuepro import TaskQueuePro
from terminalrewind import TerminalRewindDB, CommandRecorder, SessionExporter

queue = TaskQueuePro()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Get task from queue
task = queue.get_next_task()
print(f"Processing: {task.title}")

# Start terminal session for this task
recorder.start_session(
    name=f"Task {task.id}: {task.title}",
    agent_name="ATLAS"
)

# Mark task as in-progress
queue.start_task(task.id)

try:
    # Execute task commands
    recorder.log("npm install", exit_code=0, output="done")
    recorder.log("npm test", exit_code=0, output="passed")
    
    # Export session as task artifact
    exporter = SessionExporter(db)
    session_log = exporter.to_markdown()
    
    # Complete task with terminal log
    queue.complete_task(
        task.id,
        result={
            "status": "success",
            "terminal_log": session_log
        }
    )
    
except Exception as e:
    queue.fail_task(task.id, error=str(e))
    
finally:
    recorder.end_session()
    db.close()
```

**Result:** Centralized task tracking with terminal context

---

## Pattern 4: TerminalRewind + MemoryBridge

**Use Case:** Persist terminal sessions to memory core

**Why:** Maintain long-term history of important terminal work

**Code:**

```python
from memorybridge import MemoryBridge
from terminalrewind import TerminalRewindDB, SessionExporter

memory = MemoryBridge()
db = TerminalRewindDB()
exporter = SessionExporter(db)

# After completing important work
session_data = exporter.to_json()

# Save to memory core
session_id = "build_20260131"
memory.set(
    f"terminal_sessions/{session_id}",
    session_data,
    metadata={
        "agent": "ATLAS",
        "type": "terminal_session",
        "date": "2026-01-31"
    }
)
memory.sync()

# Later, retrieve for context
previous_session = memory.get(f"terminal_sessions/{session_id}")
if previous_session:
    print("Found previous session context")
    # Use for context in new session

db.close()
```

**Result:** Historical terminal data persisted in memory core

---

## Pattern 5: TerminalRewind + SessionReplay

**Use Case:** Record terminal sessions for debugging replay

**Why:** Correlate AI session events with terminal commands

**Code:**

```python
from sessionreplay import SessionReplay
from terminalrewind import TerminalRewindDB, CommandRecorder

replay = SessionReplay()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Start both with same session context
session_id = "debug_session_001"

replay.start_session("ATLAS", task="Debugging Build")
recorder.start_session(name="Debug Session", agent_name="ATLAS")

# Log to both systems
replay.log_input(session_id, "Running diagnostic command")
recorder.log(
    command="python diagnose.py",
    exit_code=0,
    output="Issue found: missing dependency"
)
replay.log_output(session_id, "Diagnosis complete: missing dependency")

# More work...
replay.log_input(session_id, "Installing missing dependency")
recorder.log(
    command="pip install missing-package",
    exit_code=0
)
replay.log_output(session_id, "Dependency installed")

# End both
replay.end_session(session_id, status="COMPLETED")
recorder.end_session()

db.close()
```

**Result:** Full session replay available with terminal context

---

## Pattern 6: TerminalRewind + ContextCompressor

**Use Case:** Compress terminal outputs for token-limited contexts

**Why:** Share terminal history without exceeding context limits

**Code:**

```python
from contextcompressor import ContextCompressor
from terminalrewind import TerminalRewindDB, SessionExporter

compressor = ContextCompressor()
db = TerminalRewindDB()
exporter = SessionExporter(db)

# Get full session export
full_export = exporter.to_markdown(limit=100)
print(f"Original size: {len(full_export)} chars")

# Compress for token-limited AI context
compressed = compressor.compress_text(
    full_export,
    query="key commands and errors",
    method="summary"
)

print(f"Compressed size: {len(compressed.compressed_text)} chars")
print(f"Token savings: ~{compressed.estimated_token_savings} tokens")

# Use compressed version when context is limited
context_for_ai = f"""
Terminal Session Summary:
{compressed.compressed_text}

Please continue the task based on this context.
"""

db.close()
```

**Result:** 60-80% token savings on large terminal outputs

---

## Pattern 7: TerminalRewind + ConfigManager

**Use Case:** Centralize TerminalRewind settings

**Why:** Share configuration across tools and agents

**Code:**

```python
from configmanager import ConfigManager
from pathlib import Path
from terminalrewind import TerminalRewindDB, CommandRecorder

config = ConfigManager()

# Load TerminalRewind configuration
tr_config = config.get("terminalrewind", {
    "database_path": "~/.local/share/TerminalRewind/terminalrewind.db",
    "backup_dir": "~/.local/share/TerminalRewind/backups",
    "backup_days": 7,
    "max_output_size": 100000,
    "default_agent": "ATLAS"
})

# Initialize with config
db_path = Path(tr_config["database_path"]).expanduser()
db = TerminalRewindDB(db_path)
recorder = CommandRecorder(db)

# Use default agent from config
recorder.start_session(
    name="Configured Session",
    agent_name=tr_config.get("default_agent", "UNKNOWN")
)

# ... work ...

recorder.end_session()

# Update config if needed
if recorder.current_session_id:
    config.set("terminalrewind.last_session", recorder.current_session_id)
    config.save()

db.close()
```

**Result:** Centralized configuration management

---

## Pattern 8: TerminalRewind + ErrorRecovery

**Use Case:** Integrate terminal rollback with error recovery

**Why:** Coordinated recovery from failed operations

**Code:**

```python
from errorrecovery import ErrorRecovery
from terminalrewind import TerminalRewindDB, CommandRecorder, RollbackManager

recovery = ErrorRecovery()
db = TerminalRewindDB()
recorder = CommandRecorder(db)
rollback = RollbackManager(db)

recorder.start_session(name="Risky Operation", agent_name="ATLAS")

try:
    # Dangerous operation with file tracking
    command_id = recorder.record(
        command="rm -rf build/ && npm run build",
        execute=True,
        track_cwd=True
    )
    
    # Check if command failed
    cmd = db.get_command_by_id(command_id)
    if cmd['exit_code'] != 0:
        raise Exception(f"Build failed: {cmd['error_output']}")
        
except Exception as e:
    print(f"Error occurred: {e}")
    
    # Attempt file rollback
    result = rollback.rollback_last(dry_run=False)
    if result['success']:
        print("Files rolled back successfully")
    
    # Log to error recovery
    recovery.log_recovery_attempt(
        error=str(e),
        recovery_action="file_rollback",
        success=result['success']
    )
    
finally:
    recorder.end_session()
    db.close()
```

**Result:** Coordinated error recovery with file restoration

---

## Pattern 9: Multi-Tool Workflow

**Use Case:** Complete workflow using multiple tools together

**Why:** Demonstrate real production scenario

**Code:**

```python
from taskqueuepro import TaskQueuePro
from sessionreplay import SessionReplay
from agenthealth import AgentHealth
from synapselink import quick_send
from terminalrewind import TerminalRewindDB, CommandRecorder, SessionExporter

# Initialize all tools
queue = TaskQueuePro()
replay = SessionReplay()
health = AgentHealth()
db = TerminalRewindDB()
recorder = CommandRecorder(db)

# Get task
task = queue.get_next_task()
session_id = f"task_{task.id}"

# Start all tracking
health.start_session("ATLAS", session_id=session_id)
replay.start_session("ATLAS", task=task.title)
recorder.start_session(name=f"Task: {task.title}", agent_name="ATLAS")
queue.start_task(task.id)

try:
    # Execute with full tracking
    health.heartbeat("ATLAS", status="processing")
    replay.log_input(session_id, "Starting task execution")
    
    recorder.log("npm install", exit_code=0, output="done")
    health.heartbeat("ATLAS", status="testing")
    
    recorder.log("npm test", exit_code=0, output="passed")
    replay.log_output(session_id, "Tests passed")
    
    # Success path
    exporter = SessionExporter(db)
    terminal_log = exporter.to_markdown()
    
    queue.complete_task(task.id, result={"terminal_log": terminal_log})
    replay.end_session(session_id, status="COMPLETED")
    health.end_session("ATLAS", session_id=session_id, status="success")
    
    # Notify team
    quick_send("TEAM", f"Task {task.id} Complete", terminal_log[:1000])
    
except Exception as e:
    # Failure path
    recorder.log("failed", exit_code=1, error_output=str(e))
    queue.fail_task(task.id, error=str(e))
    replay.log_error(session_id, str(e))
    replay.end_session(session_id, status="FAILED")
    health.log_error("ATLAS", str(e))
    health.end_session("ATLAS", session_id=session_id, status="failed")
    
    # Alert team
    quick_send("FORGE,LOGAN", f"Task {task.id} Failed", str(e), priority="HIGH")
    
finally:
    recorder.end_session()
    db.close()
```

**Result:** Fully instrumented, coordinated workflow

---

## Pattern 10: Full Team Brain Stack

**Use Case:** Ultimate integration - all tools working together

**Why:** Production-grade agent operation

**Code:**

```python
#!/usr/bin/env python3
"""
Full Team Brain Stack Integration Example
Complete agent session with all monitoring and tracking
"""

from pathlib import Path
import json

# Import all Team Brain tools
from agenthealth import AgentHealth
from synapselink import quick_send
from taskqueuepro import TaskQueuePro
from memorybridge import MemoryBridge
from configmanager import ConfigManager
from sessionreplay import SessionReplay
from terminalrewind import TerminalRewindDB, CommandRecorder, SessionExporter


def run_full_stack_session(task_title: str, agent_name: str = "ATLAS"):
    """Run a complete session with full Team Brain integration."""
    
    # Initialize all tools
    config = ConfigManager()
    health = AgentHealth()
    replay = SessionReplay()
    memory = MemoryBridge()
    queue = TaskQueuePro()
    db = TerminalRewindDB()
    recorder = CommandRecorder(db)
    exporter = SessionExporter(db)
    
    # Generate shared session ID
    import datetime
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Start all systems
    print(f"[*] Starting full stack session: {session_id}")
    
    health.start_session(agent_name, session_id=session_id)
    replay.start_session(agent_name, task=task_title)
    recorder.start_session(name=task_title, agent_name=agent_name)
    
    try:
        # Phase 1: Setup
        health.heartbeat(agent_name, status="initializing")
        replay.log_input(session_id, "Starting setup phase")
        recorder.log("echo 'Starting setup'", exit_code=0)
        
        # Phase 2: Main work
        health.heartbeat(agent_name, status="processing")
        replay.log_input(session_id, "Executing main task")
        
        # Simulate work
        recorder.log("python main_task.py", exit_code=0, output="Task completed")
        
        # Phase 3: Validation
        health.heartbeat(agent_name, status="validating")
        replay.log_input(session_id, "Running validation")
        recorder.log("python validate.py", exit_code=0, output="All checks passed")
        
        # Success - export and save
        terminal_log = exporter.to_markdown()
        json_export = exporter.to_json()
        
        # Save to memory
        memory.set(f"sessions/{session_id}", {
            "terminal_log": json_export,
            "status": "success",
            "agent": agent_name
        })
        memory.sync()
        
        # End all systems
        replay.end_session(session_id, status="COMPLETED")
        health.end_session(agent_name, session_id=session_id, status="success")
        
        # Notify team
        quick_send(
            "TEAM",
            f"[{agent_name}] Session Complete: {task_title}",
            f"Session {session_id} completed successfully.\n\n{terminal_log[:500]}...",
            priority="NORMAL"
        )
        
        print(f"[OK] Session {session_id} completed successfully")
        return {"success": True, "session_id": session_id}
        
    except Exception as e:
        # Error handling
        print(f"[X] Error: {e}")
        
        recorder.log("error", exit_code=1, error_output=str(e))
        replay.log_error(session_id, str(e))
        replay.end_session(session_id, status="FAILED")
        health.log_error(agent_name, str(e))
        health.end_session(agent_name, session_id=session_id, status="failed")
        
        # Alert
        quick_send(
            "FORGE,LOGAN",
            f"[{agent_name}] Session FAILED: {task_title}",
            f"Session {session_id} failed: {e}",
            priority="HIGH"
        )
        
        return {"success": False, "session_id": session_id, "error": str(e)}
        
    finally:
        recorder.end_session()
        db.close()


if __name__ == "__main__":
    result = run_full_stack_session(
        task_title="Full Stack Integration Test",
        agent_name="ATLAS"
    )
    print(json.dumps(result, indent=2))
```

**Result:** Production-ready agent session with complete observability

---

## 📊 RECOMMENDED INTEGRATION PRIORITY

**Week 1 (Essential):**
1. [x] AgentHealth - Health correlation
2. [x] SynapseLink - Team notifications
3. [x] SessionReplay - Debugging

**Week 2 (Productivity):**
4. [ ] TaskQueuePro - Task management
5. [ ] MemoryBridge - Data persistence
6. [ ] ConfigManager - Configuration

**Week 3 (Advanced):**
7. [ ] ContextCompressor - Token optimization
8. [ ] ErrorRecovery - Coordinated recovery
9. [ ] Full stack integration

---

## 🔧 TROUBLESHOOTING INTEGRATIONS

**Import Errors:**

```python
# Ensure all tools are in Python path
import sys
from pathlib import Path

# Add AutoProjects to path
autoprojects = Path.home() / "OneDrive/Documents/AutoProjects"
sys.path.insert(0, str(autoprojects))

# Now import
from terminalrewind import TerminalRewindDB
```

**Version Conflicts:**

```bash
# Check versions
trewind --version

# Update if needed
cd AutoProjects/TerminalRewind
git pull origin main
pip install -e .
```

**Database Locked:**

```python
# Always close connections
try:
    db = TerminalRewindDB()
    # ... work ...
finally:
    db.close()

# Or use context manager pattern
# (future enhancement)
```

**Configuration Issues:**

```python
# Reset to defaults
from configmanager import ConfigManager
config = ConfigManager()
config.delete("terminalrewind")
config.save()
```

---

**Last Updated:** January 31, 2026  
**Maintained By:** ATLAS (Team Brain)
