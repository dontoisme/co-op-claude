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
        d["status"] = self.status.value if isinstance(self.status, TaskStatus) else self.status
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
