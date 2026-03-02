## Squabble Inn — Co-op Configuration

Social audiobook app for LitRPG listeners with guild-based features.

### Architecture Domain (Don)
- Guild data model and membership system
- Audiobook progress sync and social features
- Real-time co-op listening sessions
- Achievement/milestone tracking
- Audio playback engine integration

### UX Domain (West)
- Guild tab (shield icon!) and navigation taxonomy
- Activity feed → guild view consolidation
- Listener profiles, social cards
- Book discovery and recommendation UI
- Player controls and progress visualization

### File Ownership
| Station | Directories |
|---------|------------|
| Architecture | src/api/, src/models/, src/services/, src/store/, src/hooks/, server/ |
| UX | src/components/, src/screens/, src/navigation/, src/styles/, src/assets/ |
| Shared | src/types/, src/utils/, src/config/, package.json |
