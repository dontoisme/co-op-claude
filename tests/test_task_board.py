"""Tests for task board formatting."""

from src.models import SharedTask, TaskStatus
from src.task_board import format_task_board, format_task_detail


def test_format_empty_board():
    result = format_task_board([])
    assert "No tasks" in result


def test_format_board_with_tasks():
    tasks = [
        SharedTask(id="T1", title="Build API", status=TaskStatus.IN_PROGRESS, assigned_to="Don"),
        SharedTask(id="T2", title="Build UI", status=TaskStatus.PENDING),
    ]
    result = format_task_board(tasks)
    assert "T1" in result
    assert "Build API" in result
    assert "Don" in result
    assert "T2" in result


def test_format_task_detail():
    task = SharedTask(
        id="T1", title="Build API",
        description="REST endpoints for guild",
        status=TaskStatus.IN_PROGRESS,
        assigned_to="Don",
        tags=["arch"],
    )
    result = format_task_detail(task)
    assert "T1" in result
    assert "Build API" in result
    assert "Don" in result
    assert "REST endpoints" in result
    assert "arch" in result
