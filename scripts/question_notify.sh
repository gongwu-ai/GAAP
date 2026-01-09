#!/bin/bash
###############################################################################
# GAAP - AskUserQuestion Notification (Project-level)
###############################################################################

# Debug log (for troubleshooting hook execution)
DEBUG_LOG="${TMPDIR:-/tmp}/gaap_debug.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] AskUserQuestion hook triggered. CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-not_set}" >> "$DEBUG_LOG"

read -r input || true

# Parse project directory from hook input
CWD=$(echo "$input" | grep -o '"cwd":"[^"]*"' | sed 's/"cwd":"//;s/"$//' || true)

# Load .env if exists
[ -n "$CWD" ] && [ -f "$CWD/.env" ] && set -a && . "$CWD/.env" && set +a

# Find webhook URL (env var > file fallback)
WEBHOOK_URL=""
[ -n "$FEISHU_WEBHOOK_URL" ] && WEBHOOK_URL="$FEISHU_WEBHOOK_URL"
[ -z "$WEBHOOK_URL" ] && [ -n "$CWD" ] && [ -f "$CWD/.claude/feishu-webhook-url" ] && \
    WEBHOOK_URL=$(cat "$CWD/.claude/feishu-webhook-url" 2>/dev/null | tr -d '\n')

[ -z "$WEBHOOK_URL" ] && exit 0

# Get hostname
HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "?")

# Get session title (cached, LLM-generated if API configured)
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME=$(GAAP_PROJECT_DIR="$CWD" GAAP_API_KEY="$GAAP_API_KEY" python3 "$SCRIPT_DIR/get_session_title.py" "$TRANSCRIPT_PATH" "$CWD" 2>/dev/null || basename "$CWD" 2>/dev/null || echo "?")

# Send notification
MESSAGE="[$HOST|$SESSION_NAME] 有问题等你回答"
curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" \
    --connect-timeout 5 --max-time 10 > /dev/null 2>&1 || true

exit 0
