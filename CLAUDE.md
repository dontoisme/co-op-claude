# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Co-op Claude enables multiplayer Claude Code sessions — two developers each get a specialized Claude Code instance, and all four participants (2 humans + 2 AIs) communicate through a shared message bus and task board. Claude↔Claude communication uses Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`).

**Status**: This repo contains `COOP_CLAUDE_BLUEPRINT.md`, a prompt-as-installer that defines the full project. To scaffold the codebase from the blueprint:
```bash
claude "Read COOP_CLAUDE_BLUEPRINT.md and build everything it describes. Create all files, install dependencies, and make it runnable."
```

## Tech Stack

- **Language**: Python 3.10+ (stdlib only — no external dependencies)
- **Async**: asyncio throughout (bus polling, TCP relay, Claude CLI bridge)
- **Packaging**: pyproject.toml with setuptools, entry point `coop-claude = "src.cli:main"`
- **External requirement**: Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)

## Build & Run Commands

```bash
# Install (editable)
pip install -e .

# Run tests
python -m pytest tests/ -v

# Run a single test
python -m pytest tests/test_models.py::test_message_roundtrip -v

# Async tests require pytest-asyncio
pip install pytest pytest-asyncio

# Start a session (host)
coop-claude start --name Don --role architect --partner West --serve

# Join a session (guest, same machine)
coop-claude join --name West --role ux

# Join a session (remote)
coop-claude join --name West --role ux --host <ip> --port 7723

# Session management
coop-claude status
coop-claude stop
```

## Architecture

### Core Components

- **Station** (`src/station.py`) — One human + their Claude. Handles input routing: plain text → own Claude, `@mention` → shared bus, `/command` → task board. Runs three concurrent asyncio tasks: input loop, output loop, remote message watcher.
- **SharedBus** (`src/bus.py`) — File-based pub/sub. Messages are timestamped JSON files in `/tmp/coop-claude/messages/`. Stations poll for new files. Also manages the task board (`/tmp/coop-claude/tasks/`).
- **ClaudeBridge** (`src/claude_bridge.py`) — Wraps `claude -p` (headless mode) with `--resume` for session continuity. First turn sends `--append-system-prompt` with role-specific prompt.
- **CoopRelay / RelayClient** (`src/relay.py`) — TCP bridge (port 7723) for networked sessions. Bidirectionally forwards JSON messages between remote buses.
- **Roles** (`src/roles.py`) — System prompts that specialize each Claude (architect, ux, fullstack, devops, custom). Includes file ownership rules per role.
- **Models** (`src/models.py`) — Dataclasses: `CoopMessage`, `SharedTask`, `User`. Enums: `MessageType`, `Role`, `TaskStatus`. JSON serialization via `to_json()`/`from_json()`.

### Message Routing

```
Human types text     → Station._send_to_own_claude() → ClaudeBridge.send()
Human types @name    → Station._handle_mention()     → SharedBus.publish()
Human types /command → Station._handle_command()      → task board or broadcast
Remote message       → SharedBus.poll_new_messages()  → routed to local Claude if targeted
```

### Session Data

All session state lives in `/tmp/coop-claude/`:
- `messages/` — JSON files (one per message)
- `tasks/` — JSON files (one per task)
- `state/` — Session state
- `session.log` — Human-readable log

## Design Constraints

- Zero external Python dependencies — stdlib only
- Single process per station — no microservices
- Terminal-first — no web UI
- Wrap Agent Teams, don't replace it
- File-based coordination for same-machine; TCP relay for remote

## Conventions

- Commit prefixes by role: `[arch]`, `[ux]`, `[fs]`, `[ops]`, `[shared]`, `[coop]`
- File ownership enforced per role (see `ROLE_OWNED_PATHS` in `src/roles.py`)
- Shared paths (types/, utils/, config/, package.json) require coordination before editing
