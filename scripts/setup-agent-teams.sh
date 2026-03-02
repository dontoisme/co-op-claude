#!/usr/bin/env bash
# Enable Agent Teams for Claude Code
set -euo pipefail

echo "Enabling Claude Code Agent Teams..."

# Method 1: settings.json
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    # Use python to merge the env key
    python3 -c "
import json, sys
p = '$SETTINGS_FILE'
with open(p) as f:
    d = json.load(f)
d.setdefault('env', {})['CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS'] = '1'
with open(p, 'w') as f:
    json.dump(d, f, indent=2)
print(f'Updated {p}')
"
else
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo '{"env":{"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS":"1"}}' > "$SETTINGS_FILE"
    echo "Created $SETTINGS_FILE"
fi

# Method 2: shell profile
PROFILE="${ZDOTDIR:-$HOME}/.zshrc"
[ -f "$PROFILE" ] || PROFILE="$HOME/.bashrc"
if ! grep -q "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" "$PROFILE" 2>/dev/null; then
    echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> "$PROFILE"
    echo "Added to $PROFILE"
fi

echo "Agent Teams enabled. Restart your terminal or run:"
echo "   export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
