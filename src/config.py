"""Configuration management for Co-op Claude."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


DEFAULT_CONFIG = {
    "bus_dir": "/tmp/coop-claude",
    "relay_port": 7723,
    "poll_interval": 0.3,
    "claude_timeout": 300,
    "max_message_display": 500,
}


def load_config(path: Optional[Path] = None) -> dict:
    """Load config from file, falling back to defaults."""
    config = dict(DEFAULT_CONFIG)
    if path and path.exists():
        with open(path) as f:
            config.update(json.load(f))
    return config
