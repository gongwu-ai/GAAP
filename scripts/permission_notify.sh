#!/bin/bash
###############################################################################
# GAAP - Permission Request Notification
# Sends notification when Claude requests permission for a tool
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

read -r input || true

# Find webhook URL
WEBHOOK_URL=""
[ -n "$FEISHU_WEBHOOK_URL" ] && WEBHOOK_URL="$FEISHU_WEBHOOK_URL"
[ -z "$WEBHOOK_URL" ] && [ -f "$HOME/.claude/feishu-webhook-url" ] && \
    WEBHOOK_URL=$(cat "$HOME/.claude/feishu-webhook-url" 2>/dev/null | tr -d '\n')

[ -z "$WEBHOOK_URL" ] && exit 0

# Get hostname
HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "?")

# Extract tool name and session name
TOOL_NAME=$(echo "$input" | grep -o '"tool_name":"[^"]*"' | sed 's/"tool_name":"//;s/"$//' || echo "?")
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)
CWD=$(echo "$input" | grep -o '"cwd":"[^"]*"' | sed 's/"cwd":"//;s/"$//' || true)

# Extract session name from transcript
SESSION_NAME=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    SESSION_NAME=$(head -1 "$TRANSCRIPT_PATH" | grep -o '"summary":"[^"]*"' | sed 's/"summary":"//;s/"$//' | head -c 30 || true)
fi
[ -z "$SESSION_NAME" ] && SESSION_NAME=$(basename "$CWD" 2>/dev/null || echo "?")

# Send notification
MESSAGE="[$HOST|$SESSION_NAME] 权限: $TOOL_NAME"
curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" \
    --connect-timeout 5 --max-time 10 > /dev/null 2>&1 || true

exit 0
