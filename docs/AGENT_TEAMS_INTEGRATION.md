# Agent Teams Integration

## Overview

Co-op Claude leverages Claude Code's experimental Agent Teams feature for native Claude↔Claude communication. This provides a built-in mailbox system where Claude instances can send messages to each other without routing through the shared bus.

## Setup

Enable Agent Teams:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Or in `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## How It Works

- Each Claude instance in a co-op session is aware of its partner via the system prompt
- Claude↔Claude messages use the Agent Teams `TeammateTool.SendMessage` natively
- The shared bus also carries notifications about Claude↔Claude exchanges (truncated)
- Humans can see summaries of inter-Claude communication in the bus log

## Important Notes

- Agent Teams is experimental — the API may change
- Co-op Claude wraps Agent Teams; it does not replace or modify the feature
- If Agent Teams is unavailable, Claudes can still coordinate via the shared bus (human-relayed)
