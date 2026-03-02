# Architecture

## Design Principles

1. **Zero external dependencies**: Only Python stdlib + Claude Code CLI
2. **File-based coordination**: Messages stored as JSON files — works on any filesystem
3. **Incremental adoption**: Start with shared tmux → add message routing → add networking
4. **Agent Teams native**: Leverage Claude Code's built-in multi-agent features, don't reinvent
5. **Human-first**: The humans are the primary participants; AIs are specialized assistants

## Message Flow

### Same Machine
Human A types → Station A routes → SharedBus writes JSON file →
Station B polls directory → displays to Human B / routes to Claude B

### Networked (TCP Relay)
Human A types → Station A → SharedBus → CoopRelay →
TCP → RelayClient at Station B → local SharedBus → Station B

### Claude↔Claude (Agent Teams)
Claude A uses TeammateTool.SendMessage → Agent Teams mailbox →
Claude B receives in context → responds via mailbox

## Session Lifecycle

1. Host runs `coop-claude start` → creates SharedBus dir, starts Station + optional Relay
2. Guest runs `coop-claude join` → connects to SharedBus (local or via Relay)
3. Both type naturally; messages route based on prefix (@mention) or default (own Claude)
4. Either runs `/quit`; host `/stop` ends everything
5. Session log archived to ~/coop-claude-{timestamp}.log
