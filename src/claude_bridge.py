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
