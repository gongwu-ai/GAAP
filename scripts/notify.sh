#!/bin/bash
###############################################################################
# GAAP - Smart Feishu Notification Script (Project-level)
# Only sends notifications when Claude needs user input
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

read -r input || true

# Parse project directory from hook input
CWD=$(echo "$input" | grep -o '"cwd":"[^"]*"' | sed 's/"cwd":"//;s/"$//' || true)

# Find webhook URL (env var > project config)
WEBHOOK_URL=""
[ -n "$FEISHU_WEBHOOK_URL" ] && WEBHOOK_URL="$FEISHU_WEBHOOK_URL"
[ -z "$WEBHOOK_URL" ] && [ -n "$CWD" ] && [ -f "$CWD/.claude/feishu-webhook-url" ] && \
    WEBHOOK_URL=$(cat "$CWD/.claude/feishu-webhook-url" 2>/dev/null | tr -d '\n')

[ -z "$WEBHOOK_URL" ] && exit 0

# Parse hook input
PERMISSION_MODE=$(echo "$input" | grep -o '"permission_mode":"[^"]*"' | sed 's/"permission_mode":"//;s/"$//' || echo "default")
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)

# Get hostname (short form)
HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "?")

# Extract session name from transcript (first summary line)
SESSION_NAME=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    SESSION_NAME=$(head -1 "$TRANSCRIPT_PATH" | grep -o '"summary":"[^"]*"' | sed 's/"summary":"//;s/"$//' | head -c 30 || true)
fi
[ -z "$SESSION_NAME" ] && SESSION_NAME=$(basename "$CWD" 2>/dev/null || echo "?")

# Check auto-approve mode
AUTO_APPROVE=false
case "$PERMISSION_MODE" in
    acceptEdits|dontAsk|bypassPermissions) AUTO_APPROVE=true ;;
esac

# Read last message and detect questions
NEEDS_INPUT=false
LAST_CONTENT=""

if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    LAST_CONTENT=$(tail -50 "$TRANSCRIPT_PATH" | grep '"type":"assistant"' | tail -1 | \
        grep -o '"text":"[^"]*"' | tail -1 | \
        sed 's/"text":"//;s/"$//' | sed 's/\\n/ /g' || true)
fi

if [ -n "$LAST_CONTENT" ]; then
    echo "$LAST_CONTENT" | grep -qE '\?|？' && NEEDS_INPUT=true
    echo "$LAST_CONTENT" | grep -qE '要不要|是否|可以吗|怎么样|如何|什么|哪个|吗$|呢$|确认|选择|输入|告诉我' && NEEDS_INPUT=true
    echo "$LAST_CONTENT" | grep -qiE 'need|want|should|would you|can you|please|let me know|confirm|choose|select|prefer|approve|accept|reject' && NEEDS_INPUT=true
fi

# Decide whether to notify
SEND_NOTIFICATION=false
if [ "$AUTO_APPROVE" = false ]; then
    [ "$NEEDS_INPUT" = true ] || [ -z "$LAST_CONTENT" ] && SEND_NOTIFICATION=true
else
    [ "$NEEDS_INPUT" = true ] && SEND_NOTIFICATION=true
fi

# Send notification
if [ "$SEND_NOTIFICATION" = true ]; then
    if [ -n "$LAST_CONTENT" ]; then
        # Try to compress message using LLM (fallback to original)
        COMPRESSED=$(echo "$LAST_CONTENT" | GAAP_PROJECT_DIR="$CWD" python3 "$SCRIPT_DIR/compress.py" 2>/dev/null || echo "$LAST_CONTENT")
        MESSAGE="[$HOST|$SESSION_NAME] $COMPRESSED"
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
