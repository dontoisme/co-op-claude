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
        print(f"\n{D}Routing:{R}")
        print(f"  {D}just type{R}                 → Broadcast to everyone")
        print(f"  {D}@{self.claude.claude_name} <msg>{R}  → Ask your Claude")
        print(f"  {D}@claude-* <msg>{R}           → Ask partner's Claude")
        print(f"  {D}@{self.partner_name} <msg>{R}           → DM your partner")
        print(f"\n{D}Commands:{R}")
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

        # Graceful shutdown — cancel all tasks on Ctrl+C
        def _shutdown():
            self.is_running = False
            for t in tasks:
                t.cancel()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _shutdown)
            except NotImplementedError:
                pass

        await asyncio.gather(*tasks, return_exceptions=True)

        R = COLORS["reset"]
        D = COLORS["dim"]
        print(f"\n{D}Session ended.{R}")
        await self.claude.shutdown()

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
                # Default: broadcast to all (open group chat)
                await self._broadcast(line)

    async def _broadcast(self, text: str):
        """Broadcast a message to all participants (default behavior)."""
        await self.bus.publish(CoopMessage(
            sender=self.human_name, recipient="all",
            content=text, msg_type=MessageType.HUMAN_TO_HUMAN))

    async def _send_to_own_claude(self, prompt: str):
        """Send a message directly to this station's Claude."""
        D = COLORS["dim"]
        W = COLORS["white"]
        R = COLORS["reset"]

        print(f"{D}{self.claude.claude_name} thinking...{R}")
        response = await self.claude.send(prompt)

        if response:
            print(f"\n{W}{self.claude.claude_name}:{R} {response}\n")

            # Broadcast response so everyone sees it
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

        # @claude-architect (own Claude) → send directly
        if target.lower() == self.claude.claude_name.lower():
            await self._send_to_own_claude(content)
        elif target.lower().startswith("claude"):
            # Other station's Claude → route through bus
            await self.bus.publish(CoopMessage(
                sender=self.human_name, recipient=target,
                content=content, msg_type=MessageType.HUMAN_TO_OTHER_CLAUDE))
            D = COLORS["dim"]
            R = COLORS["reset"]
            print(f"{D}Sent to {target} (waiting for response...){R}")
        else:
            # Human DM
            await self.bus.publish(CoopMessage(
                sender=self.human_name, recipient=target,
                content=content, msg_type=MessageType.HUMAN_TO_HUMAN))

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
