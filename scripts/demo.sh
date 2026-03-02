#!/usr/bin/env bash
# Simulated demo of Co-op Claude (no Claude CLI needed)
set -euo pipefail

echo ""
echo "Co-op Claude Demo"
echo "════════════════════════════════════════"
echo ""
echo "This simulates a co-op session between two developers."
echo "No Claude CLI required — messages are echoed locally."
echo ""

BUS_DIR="/tmp/coop-claude-demo"
mkdir -p "$BUS_DIR/messages" "$BUS_DIR/tasks"

# Simulate messages
write_msg() {
    local sender="$1" recipient="$2" content="$3" type="$4"
    local ts=$(date +%s%N)
    local file="$BUS_DIR/messages/${ts}.json"
    cat > "$file" <<EOF
{"sender":"$sender","recipient":"$recipient","content":"$content","msg_type":"$type","timestamp":"$(date -Iseconds)","metadata":{}}
EOF
    echo "  [$sender → $recipient] $content"
}

echo "--- Session Start ---"
echo ""
write_msg "system" "all" "Don joined as architect" "system"
sleep 0.5
write_msg "system" "all" "West joined as ux" "system"
sleep 0.5
echo ""

write_msg "Don" "Claude-Architect" "Let's add a guild data model" "human_to_claude"
sleep 1
write_msg "Claude-Architect" "all" "I'll create a Guild model with name, members[], and settings. Let me notify Claude-Ux about the interface." "claude_to_human"
sleep 0.5
write_msg "Claude-Architect" "Claude-Ux" "New interface: Guild { id, name, members: Member[], settings: GuildSettings }" "claude_to_claude"
sleep 1

write_msg "West" "Don" "Looks good — I'll build the guild tab with that shape" "human_to_human"
sleep 0.5
write_msg "system" "all" "New task [T001]: Build guild tab UI → West" "task_update"
sleep 0.5
write_msg "system" "all" "New task [T002]: Implement guild API endpoints → Don" "task_update"

echo ""
echo "--- Demo Complete ---"
echo ""
echo "Session data in: $BUS_DIR"
echo "Messages: $(ls "$BUS_DIR/messages/" | wc -l | tr -d ' ')"
echo ""

# Cleanup
rm -rf "$BUS_DIR"
