# Co-op Claude

**Multiplayer Claude Code sessions. Two developers. Two specialized AIs. One project.**

Co-op Claude lets two (or more) developers share a Claude Code session where each person has their own specialized Claude instance. The Claudes communicate with each other via Agent Teams, and everyone coordinates through a shared message bus and task board.

## Quick Start

### Same Machine (30 seconds)

Terminal 1 (Host):
```bash
cd your-project
coop-claude start --name Don --role architect --partner West
```

Terminal 2 (Guest):
```bash
coop-claude join --name West --role ux
```

### Different Machines (60 seconds)

Host machine:
```bash
coop-claude start --name Don --role architect --partner West --serve
```

Guest machine:
```bash
coop-claude join --name West --role ux --host dons-ip --port 7723
```

### What You Can Do

```
Type normally → talks to YOUR Claude (specialized for your role)
@West message → chat with your partner
@claude-ux question → ask your partner's Claude directly
/task title → create a shared task visible to everyone
/tasks → view the shared task board
/broadcast msg → announce to all participants
/status → session info
```

## How It Works

Each "station" is a developer + their specialized Claude Code instance:

- **Your Claude** gets a role-specific system prompt (architecture, UX, etc.)
- **Claude↔Claude** communication uses Agent Teams' native mailbox
- **Human↔Human** messages route through a shared bus (file-based or TCP)
- **Cross-station** messages (@claude-ux) get routed to the right Claude
- **Shared task board** is visible to all humans and all Claudes

## Prerequisites

- Claude Code CLI installed and authenticated
- Python 3.10+
- tmux (recommended, not required)

## Installation

```bash
pip install coop-claude
# or
git clone https://github.com/yourname/coop-claude && cd coop-claude && pip install -e .
```

## Configuration

Enable Agent Teams for Claude↔Claude communication:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
# or add to ~/.claude/settings.json:
# { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

Drop the CLAUDE.md addendum into your project:

```bash
cp templates/CLAUDE_MD_ADDENDUM.md your-project/CLAUDE.md  # or append to existing
```

## Roles

Built-in roles with specialized system prompts:

| Role | Focus Areas |
|------|------------|
| architect | System design, APIs, data models, backend, state management |
| ux | Components, design system, navigation, styling, accessibility |
| fullstack | General purpose, no domain restriction |
| devops | CI/CD, infrastructure, deployment, monitoring |
| custom | User-defined (provide --system-prompt) |

## License

MIT
