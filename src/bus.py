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
