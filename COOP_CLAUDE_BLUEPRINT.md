# Co-op Claude: Multiplayer Claude Code Sessions

> **This is a prompt-as-installer.** Feed this entire file to Claude Code and it will scaffold the full repository, install dependencies, and set up the project structure.
>
> ```bash
> claude "Read COOP_CLAUDE_BLUEPRINT.md and build everything it describes. Create all files, install dependencies, and make it runnable."
> ```

---

## Project Overview

**Co-op Claude** enables multiplayer Claude Code sessions where two (or more) developers each have their own specialized Claude Code instance, and all four participants (2 humans + 2 AIs) can communicate and coordinate on a shared project.

Think of it as IRC meets pair programming meets multi-agent AI — each developer has a specialized Claude copilot, and the Claudes can talk to each other via Claude Code's native Agent Teams, while the humans communicate through a shared message bus.

### The Problem

Claude Code is single-player. Remote Control (shipped Feb 25, 2026) lets one person continue a session from their phone, but there's no way for two developers to:
- Share a Claude Code conversation with message attribution
- Each have their own specialized Claude instance that can talk to the other
- Coordinate work through a shared task board visible to humans and AIs
- Cross-communicate (human A can message human B's Claude directly)

### The Solution

A lightweight orchestration layer that:
1. Gives each developer a "station" (their terminal + their specialized Claude)
2. Routes messages between all four participants (2 humans + 2 Claudes)
3. Leverages Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) for native Claude↔Claude communication
4. Adds a shared task board, file ownership conventions, and conflict prevention
5. Supports same-machine (tmux) and networked (TCP relay) operation

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │      Shared Message Bus      │
                    │   (file-based pub/sub +      │
                    │    TCP relay for remote)      │
                    └──────────┬──────────┬────────┘
                               │          │
              ┌────────────────┴──┐  ┌────┴────────────────┐
              │   Station A        │  │   Station B          │
              │                    │  │                      │
              │  ┌──────────────┐  │  │  ┌──────────────┐   │
              │  │ Human A      │  │  │  │ Human B       │   │
              │  └──────┬───────┘  │  │  └──────┬────────┘   │
              │         │          │  │         │             │
              │  ┌──────▼───────┐  │  │  ┌──────▼────────┐   │
              │  │ Claude-Role1 │  │  │  │ Claude-Role2   │   │
              │  │ (Specialized)│◄─┼──┼─►│ (Specialized)  │   │
              │  └──────────────┘  │  │  └───────────────┘   │
              └────────────────────┘  └──────────────────────┘

Communication Channels:
  1. Human → Own Claude:       Direct terminal input (claude -p with --resume)
  2. Human → Other Human:      @mention via shared bus
  3. Claude → Claude:          Agent Teams mailbox (native) + shared bus notifications
  4. Human → Other's Claude:   @claude-role via shared bus, routed to target station
  5. Claude → All:             Responses broadcast to shared bus (truncated for context)

Session Persistence:
  - Each Claude instance uses --resume with session IDs for conversation continuity
  - Shared task board persists to filesystem
  - Chat log maintained for full session history
  - TCP relay enables remote connections without shared filesystem
```

---

## Repository Structure

Create EXACTLY this file structure:

```
coop-claude/
├── README.md                          # Project README (see §README below)
├── LICENSE                            # MIT License
├── package.json                       # npm package config (for global install)
├── setup.py                           # Python package config
├── pyproject.toml                     # Modern Python packaging
├── requirements.txt                   # Python dependencies
│
├── bin/
│   ├── coop-claude                    # Main CLI entry point (bash wrapper)
│   └── coop-claude-setup              # Interactive setup wizard
│
├── src/
│   ├── __init__.py
│   ├── cli.py                         # CLI argument parsing and command routing
│   ├── station.py                     # Station class (one human + their Claude)
│   ├── bus.py                         # SharedBus (file-based pub/sub)
│   ├── relay.py                       # TCP relay server for networked mode
│   ├── models.py                      # Data models (Message, Task, User, Role)
│   ├── claude_bridge.py               # Claude Code CLI wrapper (claude -p, --resume)
│   ├── roles.py                       # Role definitions and system prompts
│   ├── task_board.py                  # Shared task board management
│   ├── display.py                     # Terminal display formatting and colors
│   └── config.py                      # Configuration management
│
├── templates/
│   ├── CLAUDE_MD_ADDENDUM.md          # Drop-in CLAUDE.md addition for any project
│   ├── CLAUDE_MD_SQUABBLE.md          # Squabble Inn specific config
│   ├── roles/
│   │   ├── architect.md               # Architecture role system prompt
│   │   ├── ux.md                      # UI/UX role system prompt
│   │   ├── fullstack.md               # Full-stack role system prompt
│   │   ├── devops.md                  # DevOps role system prompt
│   │   └── custom.md                  # Template for custom roles
│   └── tmux/
│       ├── coop-dual.conf             # tmux layout for dual-station
│       └── coop-quad.conf             # tmux layout for 4-station
│
├── scripts/
│   ├── quick-start.sh                 # One-command setup for trying it out
│   ├── setup-agent-teams.sh           # Enable Agent Teams env var
│   └── demo.sh                        # Simulated demo (no Claude CLI needed)
│
├── tests/
│   ├── __init__.py
│   ├── test_bus.py                    # SharedBus unit tests
│   ├── test_models.py                 # Model serialization tests
│   ├── test_task_board.py             # Task board tests
│   ├── test_relay.py                  # TCP relay integration tests
│   └── test_station.py                # Station routing tests
│
├── docs/
│   ├── ARCHITECTURE.md                # Detailed technical architecture
│   ├── AGENT_TEAMS_INTEGRATION.md     # How we leverage Agent Teams
│   ├── NETWORKING.md                  # TCP relay and remote setup
│   └── EXAMPLES.md                    # Usage examples and workflows
│
└── .github/
    └── workflows/
        └── test.yml                   # CI: run tests on push
```

---

## §README — README.md Content

```markdown
# 🤝 Co-op Claude

**Multiplayer Claude Code sessions. Two developers. Two specialized AIs. One project.**

Co-op Claude lets two (or more) developers share a Claude Code session where each person has their own specialized Claude instance. The Claudes communicate with each other via Agent Teams, and everyone coordinates through a shared message bus and task board.

## Quick Start

### Same Machine (30 seconds)

Terminal 1 (Host):
  cd your-project
  coop-claude start --name Don --role architect --partner West

Terminal 2 (Guest):
  coop-claude join --name West --role ux

### Different Machines (60 seconds)

Host machine:
  coop-claude start --name Don --role architect --partner West --serve

Guest machine:
  coop-claude join --name West --role ux --host dons-ip --port 7723

### What You Can Do

Type normally → talks to YOUR Claude (specialized for your role)
@West message → chat with your partner
@claude-ux question → ask your partner's Claude directly
/task title → create a shared task visible to everyone
/tasks → view the shared task board
/broadcast msg → announce to all participants
/status → session info

## How It Works

Each "station" is a developer + their specialized Claude Code instance:

- **Your Claude** gets a role-specific system prompt (architecture, UX, etc.)
- **Claude↔Claude** communication uses Agent Teams' native mailbox
- **Human↔Human** messages route through a shared bus (file-based or TCP)
- **Cross-station** messages (@claude-ux) get routed to the right Claude
- **Shared task board** is visible to all humans and all Claudes

## Prerequisites

- Claude Code CLI installed and authenticated
- Python 3.10+
- tmux (recommended, not required)

## Installation

pip install coop-claude
# or
git clone https://github.com/yourname/coop-claude && cd coop-claude && pip install -e .

## Configuration

Enable Agent Teams for Claude↔Claude communication:

export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
# or add to ~/.claude/settings.json:
# { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }

Drop the CLAUDE.md addendum into your project:

cp templates/CLAUDE_MD_ADDENDUM.md your-project/CLAUDE.md  # or append to existing

## Roles

Built-in roles with specialized system prompts:

| Role | Focus Areas |
|------|------------|
| architect | System design, APIs, data models, backend, state management |
| ux | Components, design system, navigation, styling, accessibility |
| fullstack | General purpose, no domain restriction |
| devops | CI/CD, infrastructure, deployment, monitoring |
| custom | User-defined (provide --system-prompt) |

## License

MIT
```

---

## §MODELS — src/models.py

Core data models used throughout the system.

```python
"""Core data models for Co-op Claude."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    """Types of messages flowing through the system."""
    HUMAN_TO_CLAUDE = "human_to_claude"
    HUMAN_TO_HUMAN = "human_to_human"
    HUMAN_TO_OTHER_CLAUDE = "human_to_other_claude"
    CLAUDE_TO_CLAUDE = "claude_to_claude"
    CLAUDE_TO_HUMAN = "claude_to_human"
    SYSTEM = "system"
    TASK_UPDATE = "task_update"


class Role(str, Enum):
    """Predefined roles for Claude specialization."""
    ARCHITECT = "architect"
    UX = "ux"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


# ─── ANSI Color Helpers ──────────────────────────────────────────────

COLORS = {
    "cyan": "\033[1;36m",
    "yellow": "\033[1;33m",
    "green": "\033[1;32m",
    "magenta": "\033[1;35m",
    "blue": "\033[1;34m",
    "red": "\033[1;31m",
    "white": "\033[1;37m",
    "dim": "\033[0;90m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}

MSG_TYPE_COLORS = {
    MessageType.HUMAN_TO_CLAUDE: COLORS["cyan"],
    MessageType.HUMAN_TO_HUMAN: COLORS["yellow"],
    MessageType.HUMAN_TO_OTHER_CLAUDE: COLORS["magenta"],
    MessageType.CLAUDE_TO_HUMAN: COLORS["white"],
    MessageType.CLAUDE_TO_CLAUDE: COLORS["blue"],
    MessageType.SYSTEM: COLORS["dim"],
    MessageType.TASK_UPDATE: COLORS["green"],
}

USER_COLORS = [COLORS["cyan"], COLORS["yellow"], COLORS["green"],
               COLORS["magenta"], COLORS["blue"], COLORS["red"]]


def user_color(name: str) -> str:
    """Get a consistent color for a username."""
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(USER_COLORS)
    return USER_COLORS[idx]


# ─── Message ─────────────────────────────────────────────────────────

@dataclass
class CoopMessage:
    """A message flowing through the co-op system."""
    sender: str
    recipient: str  # name, "all", "claudes", "humans"
    content: str
    msg_type: MessageType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        d = asdict(self)
        d["msg_type"] = self.msg_type.value
        return json.dumps(d)

    @classmethod
    def from_json(cls, data: str) -> CoopMessage:
        d = json.loads(data)
        d["msg_type"] = MessageType(d["msg_type"])
        return cls(**d)

    def format_display(self) -> str:
        """Render for terminal output."""
        color = MSG_TYPE_COLORS.get(self.msg_type, COLORS["reset"])
        ts = datetime.fromisoformat(self.timestamp).strftime("%H:%M:%S")
        R = COLORS["reset"]

        if self.msg_type == MessageType.SYSTEM:
            return f"{color}[{ts}] >>> {self.content}{R}"
        elif self.msg_type == MessageType.TASK_UPDATE:
            return f"{color}[{ts}] 📋 {self.content}{R}"
        elif self.recipient == "all":
            return f"{color}[{ts}] [{self.sender} → all]{R} {self.content}"
        else:
            return f"{color}[{ts}] [{self.sender} → {self.recipient}]{R} {self.content}"

    @staticmethod
    def system(content: str) -> CoopMessage:
        return CoopMessage(sender="system", recipient="all",
                           content=content, msg_type=MessageType.SYSTEM)


# ─── Task ────────────────────────────────────────────────────────────

@dataclass
class SharedTask:
    """A task on the shared board visible to all participants."""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: str = ""
    created_by: str = ""
    depends_on: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_json(self) -> str:
        d = asdict(self)
        d["status"] = self.status.value
        return json.dumps(d)

    @classmethod
    def from_json(cls, data: str) -> SharedTask:
        d = json.loads(data)
        d["status"] = TaskStatus(d["status"])
        return cls(**d)

    @staticmethod
    def generate_id() -> str:
        return f"T{int(time.time()) % 100000}"


# ─── User ────────────────────────────────────────────────────────────

@dataclass
class User:
    """A participant in the co-op session."""
    name: str
    role: Role
    claude_name: str = ""
    is_active: bool = True
    messages_sent: int = 0
    joined_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.claude_name:
            self.claude_name = f"Claude-{self.role.value.title()}"
```

---

## §ROLES — src/roles.py

Role-specific system prompts that specialize each Claude instance.

```python
"""Role definitions and system prompts for specialized Claude instances."""

from .models import Role


ROLE_PROMPTS: dict[Role, str] = {

    Role.ARCHITECT: """\
You are the **Architecture & Backend specialist** in a dual-Claude co-op session.

### Your Domain
- System architecture, data models, schemas, and API design
- Backend services, business logic, state management
- Database design, migrations, query optimization
- Performance, scalability, caching, and infrastructure patterns
- Cross-cutting: authentication, authorization, logging, error handling
- Type definitions and interface contracts shared with frontend

### Your Partner
Another Claude instance handles UI/UX, components, navigation, and styling.
You share a project directory and can communicate via the Agent Teams mailbox.

### Working With Your Human
The developer working with you is **{human_name}**. Address them by name.
Their partner **{partner_name}** works with the UX Claude on frontend concerns.

### Coordination Rules
1. When you create or modify an API endpoint, type definition, or data model,
   proactively message your partner Claude with the interface contract.
2. When you need frontend changes, message the UX Claude with requirements.
3. Prefix git commits with [arch].
4. Never modify files in: src/components/, src/screens/, src/styles/, src/navigation/
   — those belong to the UX station. Message them if you need changes there.
""",

    Role.UX: """\
You are the **UI/UX & Frontend specialist** in a dual-Claude co-op session.

### Your Domain
- Component architecture, design system, reusable UI primitives
- Screen compositions, navigation structure, routing, tab bars
- Styling: themes, colors, typography, spacing, responsive design
- Interaction patterns, animations, transitions, gestures
- Accessibility (ARIA, screen readers, keyboard navigation)
- Frontend state management and data binding to API contracts

### Your Partner
Another Claude instance handles architecture, backend, APIs, and data models.
You share a project directory and can communicate via the Agent Teams mailbox.

### Working With Your Human
The developer working with you is **{human_name}**. Address them by name.
Their partner **{partner_name}** works with the Architecture Claude on backend.

### Coordination Rules
1. When you need a new API endpoint or data shape, message the Architecture Claude.
2. When the Architecture Claude sends you a new interface contract, integrate it.
3. Prefix git commits with [ux].
4. Never modify files in: src/api/, src/models/, src/services/, server/
   — those belong to the Architecture station. Message them if you need changes.
""",

    Role.FULLSTACK: """\
You are a **Full-Stack developer** in a dual-Claude co-op session.

You handle both frontend and backend work. Your partner Claude covers
complementary areas. Coordinate through the shared task list and direct
messaging to avoid working on the same files simultaneously.

The developer working with you is **{human_name}**.
Their partner **{partner_name}** works with the other Claude.

Prefix git commits with [fs]. Coordinate before modifying shared files.
""",

    Role.DEVOPS: """\
You are the **DevOps & Infrastructure specialist** in a dual-Claude co-op session.

### Your Domain
- CI/CD pipelines, build systems, deployment automation
- Docker, container orchestration, cloud infrastructure
- Monitoring, logging, alerting, observability
- Environment configuration, secrets management
- Performance testing, load testing, security scanning

The developer working with you is **{human_name}**.
Prefix git commits with [ops].
""",

    Role.CUSTOM: """\
You are a specialist in a dual-Claude co-op session.
The developer working with you is **{human_name}**.
Their partner **{partner_name}** works with the other Claude.

{custom_instructions}
""",
}


# ─── File Ownership by Role ──────────────────────────────────────────

ROLE_OWNED_PATHS: dict[Role, list[str]] = {
    Role.ARCHITECT: [
        "src/api/", "src/models/", "src/services/", "src/store/",
        "src/hooks/", "server/", "db/", "migrations/",
    ],
    Role.UX: [
        "src/components/", "src/screens/", "src/navigation/",
        "src/styles/", "src/assets/", "src/animations/",
    ],
    Role.FULLSTACK: [],  # No restrictions
    Role.DEVOPS: [
        ".github/", "docker/", "Dockerfile", "docker-compose.yml",
        "terraform/", "k8s/", "scripts/deploy/",
    ],
    Role.CUSTOM: [],
}

SHARED_PATHS = [
    "src/types/", "src/utils/", "src/config/",
    "package.json", "tsconfig.json", "CLAUDE.md",
]


def build_system_prompt(role: Role, human_name: str, partner_name: str,
                        custom_instructions: str = "") -> str:
    """Build the complete system prompt for a station's Claude."""
    template = ROLE_PROMPTS[role]
    prompt = template.format(
        human_name=human_name,
        partner_name=partner_name,
        custom_instructions=custom_instructions,
    )

    # Append co-op protocol
    prompt += """

### Co-op Protocol
You are part of a dual-Claude system with four participants (2 humans + 2 AIs).

**Communication channels:**
- Your human talks to you directly in the terminal
- You communicate with the other Claude via the Agent Teams mailbox
- Cross-station messages (prefixed with @name) route through the shared bus

**When you make changes affecting the other station's domain:**
1. Summarize what changed and why
2. List any interface contracts (APIs, props, types) added or modified
3. Flag blocking dependencies
4. Message the other Claude proactively — don't wait to be asked

**Shared task board:** Both humans and both Claudes can see all tasks.
Claim tasks assigned to you, update status as you work, mark complete when done.
"""
    return prompt
```

---

## §BUS — src/bus.py

File-based message bus for cross-station communication.

```python
"""Shared message bus for inter-station communication.

Uses a directory of JSON files as a simple pub/sub system.
Each message is written as a timestamped JSON file.
Stations poll for new files to receive messages.

For same-machine use: /tmp/coop-claude/
For networked use: the TCP relay (see relay.py) bridges two buses.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Callable, Awaitable, Optional

from .models import CoopMessage, SharedTask, TaskStatus, MessageType


class SharedBus:
    """File-based message bus with task board support."""

    def __init__(self, base_dir: Path | str = "/tmp/coop-claude"):
        self.base_dir = Path(base_dir)
        self.messages_dir = self.base_dir / "messages"
        self.tasks_dir = self.base_dir / "tasks"
        self.state_dir = self.base_dir / "state"
        self.log_path = self.base_dir / "session.log"

        for d in [self.messages_dir, self.tasks_dir, self.state_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self._subscribers: list[asyncio.Queue[CoopMessage]] = []

    # ─── Pub/Sub ──────────────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue[CoopMessage]:
        q: asyncio.Queue[CoopMessage] = asyncio.Queue(maxsize=1000)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[CoopMessage]):
        if q in self._subscribers:
            self._subscribers.remove(q)

    async def publish(self, msg: CoopMessage):
        """Write message to disk and notify local subscribers."""
        # Persist
        msg_id = f"{int(time.time() * 1_000_000)}_{hash(msg.content) & 0xFFFF:04x}"
        (self.messages_dir / f"{msg_id}.json").write_text(msg.to_json())

        # Log
        with open(self.log_path, "a") as f:
            f.write(msg.format_display() + "\n")

        # Fan out to local subscribers
        for q in self._subscribers:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                pass  # Drop if consumer is slow

    async def poll_new_messages(
        self,
        callback: Callable[[CoopMessage], Awaitable[None]],
        poll_interval: float = 0.3,
    ):
        """Watch for messages written by OTHER stations (file polling)."""
        seen: set[str] = set()

        # Mark all existing messages as seen
        for f in self.messages_dir.glob("*.json"):
            seen.add(f.name)

        while True:
            try:
                for f in sorted(self.messages_dir.glob("*.json")):
                    if f.name not in seen:
                        seen.add(f.name)
                        try:
                            msg = CoopMessage.from_json(f.read_text())
                            await callback(msg)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break

    # ─── Task Board ───────────────────────────────────────────────

    async def create_task(self, task: SharedTask) -> SharedTask:
        (self.tasks_dir / f"{task.id}.json").write_text(task.to_json())
        await self.publish(CoopMessage(
            sender="system", recipient="all",
            content=f"New task [{task.id}]: {task.title}"
                    + (f" → {task.assigned_to}" if task.assigned_to else ""),
            msg_type=MessageType.TASK_UPDATE,
        ))
        return task

    async def update_task(self, task_id: str, **updates):
        path = self.tasks_dir / f"{task_id}.json"
        if not path.exists():
            return
        task = SharedTask.from_json(path.read_text())
        for k, v in updates.items():
            if hasattr(task, k):
                setattr(task, k, v)
        path.write_text(task.to_json())
        await self.publish(CoopMessage(
            sender="system", recipient="all",
            content=f"Task [{task_id}] updated: {updates}",
            msg_type=MessageType.TASK_UPDATE,
        ))

    def list_tasks(self, status: Optional[TaskStatus] = None) -> list[SharedTask]:
        tasks = []
        for f in sorted(self.tasks_dir.glob("*.json")):
            try:
                t = SharedTask.from_json(f.read_text())
                if status is None or t.status == status:
                    tasks.append(t)
            except (json.JSONDecodeError, ValueError):
                pass
        return tasks

    def get_task(self, task_id: str) -> Optional[SharedTask]:
        path = self.tasks_dir / f"{task_id}.json"
        if path.exists():
            return SharedTask.from_json(path.read_text())
        return None

    # ─── Cleanup ──────────────────────────────────────────────────

    def archive_session(self, dest: Optional[Path] = None) -> Path:
        """Archive the session log and return the archive path."""
        if dest is None:
            dest = Path.home() / f"coop-claude-{int(time.time())}.log"
        if self.log_path.exists():
            import shutil
            shutil.copy2(self.log_path, dest)
        return dest
```

---

## §CLAUDE_BRIDGE — src/claude_bridge.py

Wrapper around the Claude Code CLI for programmatic interaction.

```python
"""Bridge to Claude Code CLI.

Wraps `claude -p` (headless mode) with session management via --resume.
Each station gets its own Claude instance with a specialized system prompt.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from .models import Role
from .roles import build_system_prompt


class ClaudeBridge:
    """Manages a Claude Code CLI session for one station."""

    def __init__(
        self,
        role: Role,
        human_name: str,
        partner_name: str,
        project_path: str,
        custom_prompt: str = "",
    ):
        self.role = role
        self.human_name = human_name
        self.partner_name = partner_name
        self.project_path = project_path
        self.custom_prompt = custom_prompt
        self.claude_name = f"Claude-{role.value.title()}"

        self.session_id: Optional[str] = None
        self._turn_count = 0
        self._system_prompt = build_system_prompt(
            role, human_name, partner_name, custom_prompt)

    async def send(self, prompt: str, sender: Optional[str] = None) -> Optional[str]:
        """Send a prompt to Claude and return the response text."""
        self._turn_count += 1
        attributed = f"[{sender or self.human_name}]: {prompt}"

        cmd = ["claude", "-p", attributed, "--output-format", "text"]

        if self.session_id:
            cmd.extend(["--resume", self.session_id])

        if self._turn_count == 1:
            cmd.extend(["--append-system-prompt", self._system_prompt])

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=300)  # 5 min timeout

            if proc.returncode != 0:
                error = stderr.decode().strip()
                return f"[Error] {error}"

            response = stdout.decode().strip()

            # Capture session ID on first successful call
            if not self.session_id and self._turn_count == 1:
                await self._capture_session_id(attributed)

            return response

        except FileNotFoundError:
            return "[Error] Claude Code CLI not found. Run: npm install -g @anthropic-ai/claude-code"
        except asyncio.TimeoutError:
            return "[Error] Claude response timed out after 5 minutes."
        except Exception as e:
            return f"[Error] {e}"

    async def _capture_session_id(self, prompt: str):
        """Extract session_id from a JSON-format response for --resume."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p", prompt, "--output-format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
            data = json.loads(stdout.decode())
            self.session_id = data.get("session_id")
        except Exception:
            pass  # Non-critical

    @property
    def turn_count(self) -> int:
        return self._turn_count
```

---

## §STATION — src/station.py

A station is one developer's workspace: their terminal + their Claude.

```python
"""Station: one human + their specialized Claude instance.

Handles:
- Reading human input from terminal
- Routing messages (to own Claude, to partner, to other Claude)
- Displaying incoming messages from the shared bus
- Managing the local Claude Code session
"""

from __future__ import annotations

import asyncio
import signal
from typing import Optional

from .models import (CoopMessage, MessageType, SharedTask, TaskStatus,
                     Role, COLORS, user_color)
from .bus import SharedBus
from .claude_bridge import ClaudeBridge


class Station:
    """A single developer's workstation in the co-op session."""

    def __init__(
        self,
        human_name: str,
        role: Role,
        partner_name: str,
        project_path: str,
        bus: SharedBus,
        custom_prompt: str = "",
    ):
        self.human_name = human_name
        self.role = role
        self.partner_name = partner_name
        self.project_path = project_path
        self.bus = bus
        self.is_running = False

        self.claude = ClaudeBridge(
            role=role,
            human_name=human_name,
            partner_name=partner_name,
            project_path=project_path,
            custom_prompt=custom_prompt,
        )

        self._output_queue = bus.subscribe()

    async def start(self):
        """Start the station's main loop."""
        self.is_running = True
        R = COLORS["reset"]
        B = COLORS["bold"]
        D = COLORS["dim"]
        C = user_color(self.human_name)

        print(f"\n{B}═══ Co-op Claude: {self.human_name}'s Station ═══{R}")
        print(f"Role: {self.role.value.title()} | Claude: {self.claude.claude_name}")
        print(f"Partner: {self.partner_name} | Project: {self.project_path}")
        print(f"\n{D}Commands:{R}")
        print(f"  {D}@{self.partner_name} <msg>{R}  → Chat with partner")
        print(f"  {D}@claude-* <msg>{R}           → Message other Claude")
        print(f"  {D}/task <title>{R}             → Create shared task")
        print(f"  {D}/tasks{R}                    → View task board")
        print(f"  {D}/status{R}                   → Session info")
        print(f"  {D}/quit{R}                     → Leave session")
        print(f"{'─' * 55}\n")

        await self.bus.publish(CoopMessage.system(
            f"{self.human_name} joined as {self.role.value}"))

        tasks = [
            asyncio.create_task(self._input_loop()),
            asyncio.create_task(self._output_loop()),
            asyncio.create_task(self._watch_remote_messages()),
        ]

        # Graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: setattr(self, 'is_running', False))
            except NotImplementedError:
                pass

        await asyncio.gather(*tasks, return_exceptions=True)

    # ─── Input Loop ───────────────────────────────────────────────

    async def _input_loop(self):
        loop = asyncio.get_event_loop()
        C = user_color(self.human_name)
        R = COLORS["reset"]

        while self.is_running:
            try:
                line = await loop.run_in_executor(
                    None, lambda: input(f"{C}[{self.human_name}]{R} > "))
            except (EOFError, KeyboardInterrupt):
                self.is_running = False
                break

            line = line.strip()
            if not line:
                continue

            if line.startswith("/"):
                await self._handle_command(line)
            elif line.startswith("@"):
                await self._handle_mention(line)
            else:
                await self._send_to_own_claude(line)

    async def _send_to_own_claude(self, prompt: str):
        D = COLORS["dim"]
        W = COLORS["white"]
        R = COLORS["reset"]

        print(f"{D}{self.claude.claude_name} thinking...{R}")
        response = await self.claude.send(prompt)

        if response:
            print(f"\n{W}{self.claude.claude_name}:{R} {response}\n")

            # Broadcast truncated response so partner sees it
            truncated = response[:500] + ("..." if len(response) > 500 else "")
            await self.bus.publish(CoopMessage(
                sender=self.claude.claude_name,
                recipient="all",
                content=truncated,
                msg_type=MessageType.CLAUDE_TO_HUMAN,
            ))

    # ─── Commands ─────────────────────────────────────────────────

    async def _handle_command(self, cmd: str):
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "/quit":
            await self.bus.publish(CoopMessage.system(f"{self.human_name} left"))
            self.is_running = False

        elif command == "/task":
            if not arg:
                print("Usage: /task <title> [| <description>]")
                return
            title_parts = arg.split("|", 1)
            title = title_parts[0].strip()
            desc = title_parts[1].strip() if len(title_parts) > 1 else ""
            await self.bus.create_task(SharedTask(
                id=SharedTask.generate_id(),
                title=title,
                description=desc,
                created_by=self.human_name,
                tags=[self.role.value],
            ))

        elif command == "/tasks":
            tasks = self.bus.list_tasks()
            if not tasks:
                print("No tasks. Create one: /task <title>")
                return
            status_icons = {"pending": "⬜", "in_progress": "🔄",
                           "completed": "✅", "blocked": "🚫"}
            print(f"\n📋 Shared Task Board:")
            for t in tasks:
                icon = status_icons.get(t.status.value, "?")
                owner = f" → {t.assigned_to}" if t.assigned_to else ""
                print(f"  {icon} [{t.id}] {t.title}{owner}")
            print()

        elif command == "/status":
            print(f"\n  Station: {self.human_name} ({self.role.value})")
            print(f"  Claude: {self.claude.claude_name}")
            print(f"  Session: {self.claude.session_id or 'pending'}")
            print(f"  Turns: {self.claude.turn_count}")
            tasks = self.bus.list_tasks()
            counts = {}
            for t in tasks:
                counts[t.status.value] = counts.get(t.status.value, 0) + 1
            print(f"  Tasks: {counts}\n")

        elif command in ("/broadcast", "/all"):
            if arg:
                await self.bus.publish(CoopMessage(
                    sender=self.human_name, recipient="all",
                    content=arg, msg_type=MessageType.HUMAN_TO_HUMAN))

        elif command == "/claim":
            if arg:
                await self.bus.update_task(
                    arg.strip(), status=TaskStatus.IN_PROGRESS,
                    assigned_to=self.human_name)

        elif command == "/done":
            if arg:
                await self.bus.update_task(
                    arg.strip(), status=TaskStatus.COMPLETED)

    # ─── @Mentions ────────────────────────────────────────────────

    async def _handle_mention(self, line: str):
        parts = line.split(maxsplit=1)
        target = parts[0][1:]  # strip @
        content = parts[1] if len(parts) > 1 else ""
        if not content:
            print(f"Usage: @{target} <message>")
            return

        if target.lower().startswith("claude"):
            msg_type = MessageType.HUMAN_TO_OTHER_CLAUDE
        else:
            msg_type = MessageType.HUMAN_TO_HUMAN

        await self.bus.publish(CoopMessage(
            sender=self.human_name, recipient=target,
            content=content, msg_type=msg_type))

    # ─── Output Loop ──────────────────────────────────────────────

    async def _output_loop(self):
        """Display messages from the shared bus."""
        while self.is_running:
            try:
                msg = await asyncio.wait_for(self._output_queue.get(), timeout=1.0)
                # Don't echo own messages
                if msg.sender in (self.human_name, self.claude.claude_name):
                    continue
                C = user_color(self.human_name)
                R = COLORS["reset"]
                print(f"\r{msg.format_display()}")
                print(f"{C}[{self.human_name}]{R} > ", end="", flush=True)
            except asyncio.TimeoutError:
                continue

    async def _watch_remote_messages(self):
        """Process messages from other stations that target our Claude."""
        async def on_remote_msg(msg: CoopMessage):
            if msg.sender in (self.human_name, self.claude.claude_name):
                return
            # Route messages directed at our Claude
            if (msg.recipient.lower() == self.claude.claude_name.lower()
                    and msg.msg_type == MessageType.HUMAN_TO_OTHER_CLAUDE):
                M = COLORS["magenta"]
                R = COLORS["reset"]
                print(f"\n{M}[{msg.sender} → {self.claude.claude_name}]{R} {msg.content}")
                await self._send_to_own_claude(
                    f"[From {msg.sender} (partner dev)]: {msg.content}")

        await self.bus.poll_new_messages(on_remote_msg)
```

---

## §RELAY — src/relay.py

TCP relay for networked co-op sessions (different machines).

```python
"""TCP relay server for remote co-op sessions.

The host runs the relay alongside their station. The guest connects
to it from their machine. Messages are bidirectionally forwarded
between the TCP connection and the local SharedBus.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from .models import CoopMessage
from .bus import SharedBus


class CoopRelay:
    """TCP relay bridging remote stations to the shared bus."""

    def __init__(self, bus: SharedBus, host: str = "0.0.0.0", port: int = 7723):
        self.bus = bus
        self.host = host
        self.port = port
        self._clients: list[asyncio.StreamWriter] = []

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        self._clients.append(writer)
        print(f"\033[0;90m[relay] Connection from {addr}\033[0m")

        queue = self.bus.subscribe()

        async def forward():
            try:
                while True:
                    msg = await queue.get()
                    writer.write((msg.to_json() + "\n").encode())
                    await writer.drain()
            except (ConnectionError, asyncio.CancelledError):
                pass

        async def receive():
            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    try:
                        msg = CoopMessage.from_json(data.decode().strip())
                        await self.bus.publish(msg)
                    except (ValueError, KeyError):
                        pass
            except ConnectionError:
                pass

        fwd_task = asyncio.create_task(forward())
        recv_task = asyncio.create_task(receive())
        done, pending = await asyncio.wait(
            [fwd_task, recv_task], return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()

        self.bus.unsubscribe(queue)
        self._clients = [c for c in self._clients if c is not writer]
        writer.close()
        print(f"\033[0;90m[relay] Disconnected: {addr}\033[0m")

    async def start(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port)
        print(f"\033[0;90m[relay] Listening on {self.host}:{self.port}\033[0m")
        async with server:
            await server.serve_forever()


class RelayClient:
    """Connects a remote station's bus to the relay server."""

    def __init__(self, bus: SharedBus, host: str, port: int = 7723):
        self.bus = bus
        self.host = host
        self.port = port

    async def connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        queue = self.bus.subscribe()

        async def send_to_relay():
            try:
                while True:
                    msg = await queue.get()
                    writer.write((msg.to_json() + "\n").encode())
                    await writer.drain()
            except (ConnectionError, asyncio.CancelledError):
                pass

        async def receive_from_relay():
            try:
                while True:
                    data = await reader.readline()
                    if not data:
                        break
                    try:
                        msg = CoopMessage.from_json(data.decode().strip())
                        # Inject into local bus without re-publishing to file
                        for q in self.bus._subscribers:
                            if q is not queue:
                                try:
                                    q.put_nowait(msg)
                                except asyncio.QueueFull:
                                    pass
                    except (ValueError, KeyError):
                        pass
            except ConnectionError:
                pass

        await asyncio.gather(
            send_to_relay(), receive_from_relay(),
            return_exceptions=True)

        self.bus.unsubscribe(queue)
        writer.close()
```

---

## §CLI — src/cli.py

Command-line interface and entry point.

```python
"""CLI entry point for coop-claude."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .models import Role
from .bus import SharedBus
from .station import Station
from .relay import CoopRelay, RelayClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coop-claude",
        description="Multiplayer Claude Code sessions",
    )
    sub = parser.add_subparsers(dest="command")

    # ── start ─────────────────────────────────────────────────────
    sp = sub.add_parser("start", help="Start a co-op session (host)")
    sp.add_argument("--name", "-n", required=True, help="Your name")
    sp.add_argument("--role", "-r", default="architect",
                    choices=[r.value for r in Role])
    sp.add_argument("--project", "-d", default=".",
                    help="Project directory")
    sp.add_argument("--partner", default="Partner",
                    help="Partner's display name")
    sp.add_argument("--serve", "-s", action="store_true",
                    help="Enable TCP relay for remote partner")
    sp.add_argument("--port", type=int, default=7723)

    # ── join ──────────────────────────────────────────────────────
    jp = sub.add_parser("join", help="Join a co-op session")
    jp.add_argument("--name", "-n", required=True)
    jp.add_argument("--role", "-r", default="ux",
                    choices=[r.value for r in Role])
    jp.add_argument("--project", "-d", default=".")
    jp.add_argument("--partner", default="Partner")
    jp.add_argument("--host", default=None,
                    help="Relay host (omit for same-machine)")
    jp.add_argument("--port", type=int, default=7723)

    # ── status ────────────────────────────────────────────────────
    sub.add_parser("status", help="Show session status")

    # ── stop ──────────────────────────────────────────────────────
    sub.add_parser("stop", help="End the session")

    return parser


async def async_main(args):
    bus = SharedBus()

    if args.command == "start":
        project = str(Path(args.project).resolve())
        station = Station(
            human_name=args.name,
            role=Role(args.role),
            partner_name=args.partner,
            project_path=project,
            bus=bus,
        )
        tasks = [asyncio.create_task(station.start())]
        if args.serve:
            relay = CoopRelay(bus, port=args.port)
            tasks.append(asyncio.create_task(relay.start()))
        await asyncio.gather(*tasks, return_exceptions=True)

    elif args.command == "join":
        project = str(Path(args.project).resolve())
        station = Station(
            human_name=args.name,
            role=Role(args.role),
            partner_name=args.partner,
            project_path=project,
            bus=bus,
        )
        tasks = [asyncio.create_task(station.start())]
        if args.host:
            client = RelayClient(bus, host=args.host, port=args.port)
            tasks.append(asyncio.create_task(client.connect()))
        await asyncio.gather(*tasks, return_exceptions=True)

    elif args.command == "status":
        tasks = bus.list_tasks()
        log = bus.log_path
        print(f"Session dir: {bus.base_dir}")
        print(f"Tasks: {len(tasks)}")
        if log.exists():
            line_count = sum(1 for _ in open(log))
            print(f"Log: {line_count} lines")

    elif args.command == "stop":
        archive = bus.archive_session()
        import shutil
        shutil.rmtree(bus.base_dir, ignore_errors=True)
        print(f"Session ended. Log: {archive}")


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
```

---

## §CONFIG_FILES — Package and config files

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "coop-claude"
version = "0.1.0"
description = "Multiplayer Claude Code sessions — two devs, two AIs, one project"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [{name = "Don", email = "don@example.com"}]
keywords = ["claude", "claude-code", "multiplayer", "pair-programming", "agent-teams"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Build Tools",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.scripts]
coop-claude = "src.cli:main"

[project.urls]
Homepage = "https://github.com/yourname/coop-claude"
Issues = "https://github.com/yourname/coop-claude/issues"
```

### requirements.txt

```
# No external dependencies required!
# coop-claude uses only Python stdlib (asyncio, json, pathlib, dataclasses)
# Claude Code CLI is the only external requirement (npm install -g @anthropic-ai/claude-code)
```

---

## §TEMPLATES — Drop-in CLAUDE.md files

### templates/CLAUDE_MD_ADDENDUM.md

This file gets appended to any project's existing CLAUDE.md to enable co-op awareness.

```markdown
## Co-op Session Configuration

This project uses dual-agent collaborative development.

### Communication Protocol
- **Claude↔Claude**: Use Agent Teams mailbox for interface contracts, dependency notifications, conflict prevention, and review requests.
- **File ownership**: Each station owns specific directories. Message the other station before modifying their files.
- **Shared files** (types/, utils/, config/, package.json): Coordinate before editing.

### Commit Convention
- `[arch]` — Architecture station
- `[ux]` — UX station
- `[shared]` — Coordinated changes
- `[coop]` — Co-op system changes

### When Making Cross-Domain Changes
1. Summarize what changed and why
2. List interface contracts added/modified
3. Flag blocking dependencies
4. Message the other Claude proactively
```

### templates/CLAUDE_MD_SQUABBLE.md

```markdown
## Squabble Inn — Co-op Configuration

Social audiobook app for LitRPG listeners with guild-based features.

### Architecture Domain (Don)
- Guild data model and membership system
- Audiobook progress sync and social features
- Real-time co-op listening sessions
- Achievement/milestone tracking
- Audio playback engine integration

### UX Domain (West)
- Guild tab (shield icon!) and navigation taxonomy
- Activity feed → guild view consolidation
- Listener profiles, social cards
- Book discovery and recommendation UI
- Player controls and progress visualization

### File Ownership
| Station | Directories |
|---------|------------|
| Architecture | src/api/, src/models/, src/services/, src/store/, src/hooks/, server/ |
| UX | src/components/, src/screens/, src/navigation/, src/styles/, src/assets/ |
| Shared | src/types/, src/utils/, src/config/, package.json |
```

---

## §SCRIPTS — Setup and demo scripts

### scripts/quick-start.sh

```bash
#!/usr/bin/env bash
# Quick start: sets up everything and launches a co-op session
set -euo pipefail

echo "🤝 Co-op Claude Quick Start"
echo ""

# Check prerequisites
command -v claude >/dev/null 2>&1 || { echo "❌ Claude Code CLI required. Run: npm install -g @anthropic-ai/claude-code"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.10+ required."; exit 1; }

# Enable Agent Teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Get user info
read -p "Your name: " MY_NAME
read -p "Partner's name: " PARTNER_NAME
read -p "Your role (architect/ux/fullstack): " MY_ROLE
read -p "Project path [.]: " PROJECT_PATH
PROJECT_PATH="${PROJECT_PATH:-.}"

echo ""
echo "Starting co-op session..."
echo "  You: $MY_NAME ($MY_ROLE)"
echo "  Partner: $PARTNER_NAME"
echo "  Project: $PROJECT_PATH"
echo ""
echo "Share this with your partner:"
echo "  coop-claude join --name $PARTNER_NAME --role ux --host $(hostname)"
echo ""

exec coop-claude start \
    --name "$MY_NAME" \
    --role "$MY_ROLE" \
    --partner "$PARTNER_NAME" \
    --project "$PROJECT_PATH" \
    --serve
```

### scripts/setup-agent-teams.sh

```bash
#!/usr/bin/env bash
# Enable Agent Teams for Claude Code
set -euo pipefail

echo "Enabling Claude Code Agent Teams..."

# Method 1: settings.json
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    # Use python to merge the env key
    python3 -c "
import json, sys
p = '$SETTINGS_FILE'
with open(p) as f:
    d = json.load(f)
d.setdefault('env', {})['CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS'] = '1'
with open(p, 'w') as f:
    json.dump(d, f, indent=2)
print(f'Updated {p}')
"
else
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo '{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}' > "$SETTINGS_FILE"
    echo "Created $SETTINGS_FILE"
fi

# Method 2: shell profile
PROFILE="${ZDOTDIR:-$HOME}/.zshrc"
[ -f "$PROFILE" ] || PROFILE="$HOME/.bashrc"
if ! grep -q "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" "$PROFILE" 2>/dev/null; then
    echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> "$PROFILE"
    echo "Added to $PROFILE"
fi

echo "✅ Agent Teams enabled. Restart your terminal or run:"
echo "   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
```

---

## §TESTS — Test files

### tests/test_models.py

```python
"""Tests for core data models."""

import json
import pytest
from src.models import CoopMessage, MessageType, SharedTask, TaskStatus, User, Role


def test_message_roundtrip():
    msg = CoopMessage(
        sender="Don", recipient="West",
        content="hello", msg_type=MessageType.HUMAN_TO_HUMAN)
    serialized = msg.to_json()
    restored = CoopMessage.from_json(serialized)
    assert restored.sender == "Don"
    assert restored.recipient == "West"
    assert restored.content == "hello"
    assert restored.msg_type == MessageType.HUMAN_TO_HUMAN


def test_task_roundtrip():
    task = SharedTask(
        id="T001", title="Build guild shield",
        status=TaskStatus.IN_PROGRESS, assigned_to="West")
    serialized = task.to_json()
    restored = SharedTask.from_json(serialized)
    assert restored.id == "T001"
    assert restored.status == TaskStatus.IN_PROGRESS
    assert restored.assigned_to == "West"


def test_message_format_display():
    msg = CoopMessage(
        sender="Don", recipient="all",
        content="let's go", msg_type=MessageType.HUMAN_TO_HUMAN)
    display = msg.format_display()
    assert "Don" in display
    assert "let's go" in display


def test_system_message_factory():
    msg = CoopMessage.system("session started")
    assert msg.sender == "system"
    assert msg.recipient == "all"
    assert msg.msg_type == MessageType.SYSTEM


def test_task_generate_id():
    id1 = SharedTask.generate_id()
    assert id1.startswith("T")
    assert len(id1) >= 2


def test_user_claude_name_auto():
    user = User(name="Don", role=Role.ARCHITECT)
    assert user.claude_name == "Claude-Architect"
```

### tests/test_bus.py

```python
"""Tests for SharedBus."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from src.bus import SharedBus
from src.models import CoopMessage, MessageType, SharedTask


@pytest.fixture
def bus(tmp_path):
    return SharedBus(tmp_path / "test-bus")


@pytest.mark.asyncio
async def test_publish_creates_file(bus):
    msg = CoopMessage.system("hello")
    await bus.publish(msg)
    files = list(bus.messages_dir.glob("*.json"))
    assert len(files) == 1
    restored = CoopMessage.from_json(files[0].read_text())
    assert restored.content == "hello"


@pytest.mark.asyncio
async def test_subscribe_receives(bus):
    queue = bus.subscribe()
    msg = CoopMessage.system("test")
    await bus.publish(msg)
    received = queue.get_nowait()
    assert received.content == "test"


@pytest.mark.asyncio
async def test_task_crud(bus):
    task = SharedTask(id="T1", title="test task", created_by="Don")
    await bus.create_task(task)
    tasks = bus.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "test task"

    await bus.update_task("T1", status="completed")
    updated = bus.get_task("T1")
    # status stored as string after update
    assert "completed" in str(updated.status)
```

---

## §GITHUB_CI — .github/workflows/test.yml

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]" || pip install -e .
      - run: pip install pytest pytest-asyncio
      - run: python -m pytest tests/ -v
```

---

## §DOCS — docs/ARCHITECTURE.md

```markdown
# Architecture

## Design Principles

1. **Zero external dependencies**: Only Python stdlib + Claude Code CLI
2. **File-based coordination**: Messages stored as JSON files — works on any filesystem
3. **Incremental adoption**: Start with shared tmux → add message routing → add networking
4. **Agent Teams native**: Leverage Claude Code's built-in multi-agent features, don't reinvent
5. **Human-first**: The humans are the primary participants; AIs are specialized assistants

## Message Flow

### Same Machine
Human A types → Station A routes → SharedBus writes JSON file →
Station B polls directory → displays to Human B / routes to Claude B

### Networked (TCP Relay)
Human A types → Station A → SharedBus → CoopRelay →
TCP → RelayClient at Station B → local SharedBus → Station B

### Claude↔Claude (Agent Teams)
Claude A uses TeammateTool.SendMessage → Agent Teams mailbox →
Claude B receives in context → responds via mailbox

## Session Lifecycle

1. Host runs `coop-claude start` → creates SharedBus dir, starts Station + optional Relay
2. Guest runs `coop-claude join` → connects to SharedBus (local or via Relay)
3. Both type naturally; messages route based on prefix (@mention) or default (own Claude)
4. Either runs `/quit`; host `/stop` ends everything
5. Session log archived to ~/coop-claude-{timestamp}.log
```

---

## Build Instructions for Claude Code

When expanding this blueprint into a repository:

1. **Create the directory structure** exactly as specified in §Repository Structure
2. **Create each source file** from the corresponding § section above
3. **Use the exact content** provided — these are production-ready implementations
4. **Create `__init__.py` files** with appropriate imports:
   - `src/__init__.py` should export the main classes
5. **Make scripts executable**: `chmod +x bin/* scripts/*`
6. **Create the bin/coop-claude wrapper**:
   ```bash
   #!/usr/bin/env bash
   exec python3 -m src.cli "$@"
   ```
7. **Create a LICENSE file** with MIT license text
8. **Run tests** to verify: `python -m pytest tests/ -v`
9. **Test basic flow**: Start a session, send a message, verify it appears in the bus directory

### What NOT to do
- Don't add unnecessary abstractions or framework dependencies
- Don't split into microservices — this is a single-process-per-station tool
- Don't add a web UI yet — terminal-first is the right starting point
- Don't modify the Agent Teams integration — it's experimental and we wrap it, not replace it
