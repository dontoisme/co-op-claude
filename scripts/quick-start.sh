#!/usr/bin/env bash
# Quick start: sets up everything and launches a co-op session
set -euo pipefail

echo "Co-op Claude Quick Start"
echo ""

# Check prerequisites
command -v claude >/dev/null 2>&1 || { echo "Claude Code CLI required. Run: npm install -g @anthropic-ai/claude-code"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.10+ required."; exit 1; }

# Enable Agent Teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Get user info
read -p "Your name: " MY_NAME
read -p "Partner's name: " PARTNER_NAME
read -p "Your role (architect/ux/fullstack): " MY_ROLE
read -p "Project path [.]: " PROJECT_PATH
PROJECT_PATH="${PROJECT_PATH:-.}"

echo ""
echo "Starting co-op session..."
echo "  You: $MY_NAME ($MY_ROLE)"
echo "  Partner: $PARTNER_NAME"
echo "  Project: $PROJECT_PATH"
echo ""
echo "Share this with your partner:"
echo "  coop-claude join --name $PARTNER_NAME --role ux --host $(hostname)"
echo ""

exec coop-claude start \
    --name "$MY_NAME" \
    --role "$MY_ROLE" \
    --partner "$PARTNER_NAME" \
    --project "$PROJECT_PATH" \
    --serve
