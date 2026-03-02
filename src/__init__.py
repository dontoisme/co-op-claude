"""Co-op Claude: Multiplayer Claude Code sessions."""

from .models import CoopMessage, MessageType, SharedTask, TaskStatus, User, Role
from .bus import SharedBus
from .claude_bridge import ClaudeBridge
from .station import Station
from .relay import CoopRelay, RelayClient
from .roles import build_system_prompt, ROLE_PROMPTS, ROLE_OWNED_PATHS, SHARED_PATHS

__all__ = [
    "CoopMessage", "MessageType", "SharedTask", "TaskStatus", "User", "Role",
    "SharedBus", "ClaudeBridge", "Station", "CoopRelay", "RelayClient",
    "build_system_prompt", "ROLE_PROMPTS", "ROLE_OWNED_PATHS", "SHARED_PATHS",
]
