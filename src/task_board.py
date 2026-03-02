"""Shared task board management for Co-op Claude.

Task board operations are primarily handled by SharedBus.
This module provides formatting and display helpers.
"""

from __future__ import annotations

from .models import SharedTask, TaskStatus, COLORS


STATUS_ICONS = {
    TaskStatus.PENDING: "⬜",
    TaskStatus.IN_PROGRESS: "🔄",
    TaskStatus.COMPLETED: "✅",
    TaskStatus.BLOCKED: "🚫",
}


def format_task_board(tasks: list[SharedTask]) -> str:
    """Format the task board for terminal display."""
    if not tasks:
        return "No tasks. Create one: /task <title>"

    lines = [f"\n📋 Shared Task Board:"]
    for t in tasks:
        icon = STATUS_ICONS.get(t.status, "?")
        owner = f" → {t.assigned_to}" if t.assigned_to else ""
        lines.append(f"  {icon} [{t.id}] {t.title}{owner}")
    lines.append("")
    return "\n".join(lines)


def format_task_detail(task: SharedTask) -> str:
    """Format a single task with full detail."""
    R = COLORS["reset"]
    B = COLORS["bold"]
    icon = STATUS_ICONS.get(task.status, "?")

    lines = [
        f"\n{B}{icon} [{task.id}] {task.title}{R}",
        f"  Status: {task.status.value}",
    ]
    if task.assigned_to:
        lines.append(f"  Assigned: {task.assigned_to}")
    if task.description:
        lines.append(f"  Description: {task.description}")
    if task.depends_on:
        lines.append(f"  Depends on: {', '.join(task.depends_on)}")
    if task.tags:
        lines.append(f"  Tags: {', '.join(task.tags)}")
    lines.append("")
    return "\n".join(lines)
