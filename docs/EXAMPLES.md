# Usage Examples

## Basic Dual Session

### Terminal 1 — Architecture Station
```bash
coop-claude start --name Don --role architect --partner West
```
```
═══ Co-op Claude: Don's Station ═══
Role: Architect | Claude: Claude-Architect
Partner: West | Project: /Users/don/myproject

> Let's add a guild data model with members and settings
Claude-Architect thinking...

Claude-Architect: I'll create a Guild model...
```

### Terminal 2 — UX Station
```bash
coop-claude join --name West --role ux
```
```
═══ Co-op Claude: West's Station ═══
Role: Ux | Claude: Claude-Ux
Partner: Don | Project: /Users/don/myproject

> @Don I see the guild model — starting on the tab UI
```

## Task Board Workflow

```
> /task Build guild API endpoints | REST endpoints for CRUD operations
📋 New task [T42301]: Build guild API endpoints

> /tasks
📋 Shared Task Board:
  ⬜ [T42301] Build guild API endpoints

> /claim T42301
Task [T42301] updated: in_progress, assigned to Don

> /done T42301
Task [T42301] updated: completed
```

## Cross-Station Messaging

```
> @claude-ux What component structure are you using for the guild tab?
[Don → Claude-Ux] What component structure are you using for the guild tab?
```

The UX station's Claude will receive and respond to this message.

## Remote Session

Host:
```bash
coop-claude start --name Don --role architect --partner West --serve --port 7723
```

Guest (different machine):
```bash
coop-claude join --name West --role ux --host 192.168.1.42 --port 7723
```
