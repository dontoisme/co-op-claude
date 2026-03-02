## Co-op Session Configuration

This project uses dual-agent collaborative development.

### Communication Protocol
- **Claude↔Claude**: Use Agent Teams mailbox for interface contracts, dependency notifications, conflict prevention, and review requests.
- **File ownership**: Each station owns specific directories. Message the other station before modifying their files.
- **Shared files** (types/, utils/, config/, package.json): Coordinate before editing.

### Commit Convention
- `[arch]` — Architecture station
- `[ux]` — UX station
- `[shared]` — Coordinated changes
- `[coop]` — Co-op system changes

### When Making Cross-Domain Changes
1. Summarize what changed and why
2. List interface contracts added/modified
3. Flag blocking dependencies
4. Message the other Claude proactively
