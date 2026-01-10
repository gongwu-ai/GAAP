#!/bin/bash
###############################################################################
# GAAP - Smart Feishu Notification Script (Project-level)
#
# LLM Modes:
#   - none:         Rule-based filter + plain text (no LLM)
#   - smart:        Rule-based filter + LLM compress (saves tokens)
#   - compress_all: Always LLM compress (costly but informative)
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Debug log (for troubleshooting hook execution)
DEBUG_LOG="${TMPDIR:-/tmp}/gaap_debug.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] GAAP hook triggered (Stop/Notification). CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-not_set}" >> "$DEBUG_LOG"

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

# Parse hook input
PERMISSION_MODE=$(echo "$input" | grep -o '"permission_mode":"[^"]*"' | sed 's/"permission_mode":"//;s/"$//' || echo "default")
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)

# Load LLM mode from config (none | smart | compress_all)
LLM_MODE="none"
CONFIG_FILE="$CWD/.claude/gaap.json"
if [ -f "$CONFIG_FILE" ]; then
    LLM_MODE=$(grep -o '"llm_mode":"[^"]*"' "$CONFIG_FILE" | sed 's/"llm_mode":"//;s/"$//' || echo "none")
    [ -z "$LLM_MODE" ] && LLM_MODE="none"
fi

# Get hostname (short form)
HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "?")

# Get session title (cached, LLM-generated if API configured)
SESSION_NAME=$(GAAP_PROJECT_DIR="$CWD" GAAP_API_KEY="$GAAP_API_KEY" python3 "$SCRIPT_DIR/get_session_title.py" "$TRANSCRIPT_PATH" "$CWD" 2>/dev/null || basename "$CWD" 2>/dev/null || echo "?")

# Check auto-approve mode
AUTO_APPROVE=false
case "$PERMISSION_MODE" in
    acceptEdits|dontAsk|bypassPermissions) AUTO_APPROVE=true ;;
esac

# Read last message from transcript
LAST_CONTENT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    LAST_CONTENT=$(tail -50 "$TRANSCRIPT_PATH" | grep '"type":"assistant"' | tail -1 | \
        grep -o '"text":"[^"]*"' | tail -1 | \
        sed 's/"text":"//;s/"$//' | sed 's/\\n/ /g' || true)
fi

# Rule-based detection for questions/input needed
detect_needs_input() {
    local content="$1"
    [ -z "$content" ] && return 1
    echo "$content" | grep -qE '\?|？' && return 0
    echo "$content" | grep -qE '要不要|是否|可以吗|怎么样|如何|什么|哪个|吗$|呢$|确认|选择|输入|告诉我' && return 0
    echo "$content" | grep -qiE 'need|want|should|would you|can you|please|let me know|confirm|choose|select|prefer|approve|accept|reject' && return 0
    return 1
}

# Decide whether to send notification and how to format message
SEND_NOTIFICATION=false
USE_LLM_COMPRESS=false
MESSAGE=""

case "$LLM_MODE" in
    compress_all)
        # Always send, always use LLM compression
        SEND_NOTIFICATION=true
        USE_LLM_COMPRESS=true
        ;;
    smart)
        # Rule-based filter first, then LLM compress if sending
        if detect_needs_input "$LAST_CONTENT"; then
            SEND_NOTIFICATION=true
            USE_LLM_COMPRESS=true
        elif [ "$AUTO_APPROVE" = false ] && [ -z "$LAST_CONTENT" ]; then
            # No content available, still notify
            SEND_NOTIFICATION=true
            USE_LLM_COMPRESS=false
        fi
        ;;
    none|*)
        # Rule-based filter, plain text delivery (no LLM)
        if [ "$AUTO_APPROVE" = false ]; then
            detect_needs_input "$LAST_CONTENT" && SEND_NOTIFICATION=true
            [ -z "$LAST_CONTENT" ] && SEND_NOTIFICATION=true
        else
            detect_needs_input "$LAST_CONTENT" && SEND_NOTIFICATION=true
        fi
        USE_LLM_COMPRESS=false
        ;;
esac

# Send notification
if [ "$SEND_NOTIFICATION" = true ]; then
    if [ -n "$LAST_CONTENT" ]; then
        if [ "$USE_LLM_COMPRESS" = true ]; then
            # Try to compress message using LLM (fallback to plain text)
            COMPRESSED=$(echo "$LAST_CONTENT" | GAAP_PROJECT_DIR="$CWD" GAAP_API_KEY="$GAAP_API_KEY" python3 "$SCRIPT_DIR/compress.py" 2>/dev/null || echo "$LAST_CONTENT")
            MESSAGE="[$HOST|$SESSION_NAME] $COMPRESSED"
        else
            # Plain text delivery
            MESSAGE="[$HOST|$SESSION_NAME] $LAST_CONTENT"
        fi
    else
        MESSAGE="[$HOST|$SESSION_NAME] 等待输入"
    fi

    # Escape special chars for JSON
    MESSAGE=$(echo "$MESSAGE" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr '\n' ' ')

    for i in 1 2 3; do
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" \
            --connect-timeout 5 --max-time 10 || echo "000")
        [ "${HTTP_STATUS:0:1}" = "2" ] && break
        [ $i -lt 3 ] && sleep 1
    done
fi

exit 0
