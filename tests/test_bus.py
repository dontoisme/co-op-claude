"""Tests for SharedBus."""

import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from src.bus import SharedBus
from src.models import CoopMessage, MessageType, SharedTask, TaskStatus


@pytest.fixture
def bus(tmp_path):
    return SharedBus(tmp_path / "test-bus")


@pytest.mark.asyncio
async def test_publish_creates_file(bus):
    msg = CoopMessage.system("hello")
    await bus.publish(msg)
    files = list(bus.messages_dir.glob("*.json"))
    assert len(files) == 1
    restored = CoopMessage.from_json(files[0].read_text())
    assert restored.content == "hello"


@pytest.mark.asyncio
async def test_subscribe_receives(bus):
    queue = bus.subscribe()
    msg = CoopMessage.system("test")
    await bus.publish(msg)
    received = queue.get_nowait()
    assert received.content == "test"


@pytest.mark.asyncio
async def test_task_crud(bus):
    task = SharedTask(id="T1", title="test task", created_by="Don")
    await bus.create_task(task)
    tasks = bus.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "test task"

    await bus.update_task("T1", status=TaskStatus.COMPLETED)
    updated = bus.get_task("T1")
    assert updated.status == TaskStatus.COMPLETED
