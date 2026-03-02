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
