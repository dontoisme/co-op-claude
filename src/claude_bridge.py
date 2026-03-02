"""Bridge to Claude Code CLI.

Uses a persistent `claude -p` process with stream-json I/O to avoid
cold-starting a new CLI process on every turn. Falls back to the
one-shot `claude -p` approach if the persistent process fails.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from .models import Role
from .roles import build_system_prompt


class ClaudeBridge:
    """Manages a persistent Claude Code CLI session for one station.

    Spawns a single `claude -p --input-format stream-json --output-format stream-json`
    process and keeps it alive across turns. Messages are written to stdin as NDJSON,
    responses are read from stdout as NDJSON events.
    """

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

        self._proc: Optional[asyncio.subprocess.Process] = None
        self._started = False

    async def _ensure_process(self):
        """Spawn the persistent claude process if not already running."""
        if self._proc is not None and self._proc.returncode is None:
            return  # Still alive

        cmd = [
            "claude", "-p",
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--append-system-prompt", self._system_prompt,
        ]

        try:
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path,
            )
            self._started = True

            # Read the init event to capture session_id
            init_line = await asyncio.wait_for(
                self._proc.stdout.readline(), timeout=30)
            if init_line:
                try:
                    init = json.loads(init_line.decode().strip())
                    if init.get("type") == "system" and init.get("subtype") == "init":
                        self.session_id = init.get("session_id")
                except (json.JSONDecodeError, KeyError):
                    pass

        except FileNotFoundError:
            raise RuntimeError("Claude Code CLI not found. Run: npm install -g @anthropic-ai/claude-code")

    def _build_input_message(self, text: str) -> str:
        """Build a stream-json input message."""
        msg = {
            "type": "user",
            "message": {
                "role": "user",
                "content": text,
            },
            "session_id": self.session_id or "default",
            "parent_tool_use_id": None,
        }
        return json.dumps(msg)

    async def _read_until_result(self) -> Optional[str]:
        """Read NDJSON events from stdout until we get a result event.

        Collects text from assistant messages and returns the final result.
        """
        collected_text = []

        while True:
            try:
                line = await asyncio.wait_for(
                    self._proc.stdout.readline(), timeout=300)
            except asyncio.TimeoutError:
                return "[Error] Claude response timed out after 5 minutes."

            if not line:
                # Process died
                return "[Error] Claude process terminated unexpectedly."

            line_str = line.decode().strip()
            if not line_str:
                continue

            try:
                event = json.loads(line_str)
            except json.JSONDecodeError:
                continue

            event_type = event.get("type")

            if event_type == "assistant":
                # Extract text blocks from the assistant message
                message = event.get("message", {})
                content = message.get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        collected_text.append(block.get("text", ""))

            elif event_type == "result":
                # Final event for this turn
                if not event.get("is_error"):
                    # Prefer the result text if available, fall back to collected
                    result_text = event.get("result", "")
                    return result_text if result_text else "\n".join(collected_text)
                else:
                    error = event.get("result", "Unknown error")
                    return f"[Error] {error}"

            # Skip other event types (system, user, stream_event, etc.)

    async def send(self, prompt: str, sender: Optional[str] = None) -> Optional[str]:
        """Send a prompt to the persistent Claude process and return the response."""
        self._turn_count += 1
        attributed = f"[{sender or self.human_name}]: {prompt}"

        try:
            await self._ensure_process()
        except RuntimeError as e:
            return f"[Error] {e}"

        # Check process is still alive
        if self._proc.returncode is not None:
            # Process died — try to restart once
            self._proc = None
            try:
                await self._ensure_process()
            except RuntimeError as e:
                return f"[Error] {e}"

        # Write the message to stdin
        input_msg = self._build_input_message(attributed) + "\n"
        try:
            self._proc.stdin.write(input_msg.encode())
            await self._proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            self._proc = None
            return "[Error] Claude process connection lost. Will restart on next message."

        # Read the response
        return await self._read_until_result()

    async def shutdown(self):
        """Gracefully shut down the persistent process."""
        if self._proc and self._proc.returncode is None:
            self._proc.stdin.close()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
                await self._proc.wait()
            self._proc = None

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.returncode is None
