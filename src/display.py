"""Terminal display formatting and colors for Co-op Claude."""

from __future__ import annotations

from .models import COLORS, user_color, CoopMessage


def format_header(human_name: str, role: str, claude_name: str,
                  partner_name: str, project_path: str) -> str:
    """Format the station startup header."""
    R = COLORS["reset"]
    B = COLORS["bold"]
    D = COLORS["dim"]

    lines = [
        f"\n{B}═══ Co-op Claude: {human_name}'s Station ═══{R}",
        f"Role: {role} | Claude: {claude_name}",
        f"Partner: {partner_name} | Project: {project_path}",
        f"\n{D}Commands:{R}",
        f"  {D}@{partner_name} <msg>{R}  → Chat with partner",
        f"  {D}@claude-* <msg>{R}           → Message other Claude",
        f"  {D}/task <title>{R}             → Create shared task",
        f"  {D}/tasks{R}                    → View task board",
        f"  {D}/status{R}                   → Session info",
        f"  {D}/quit{R}                     → Leave session",
        f"{'─' * 55}\n",
    ]
    return "\n".join(lines)
