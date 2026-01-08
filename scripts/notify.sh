#!/bin/bash
###############################################################################
# GAAP - Smart Feishu Notification Script
# Only sends notifications when Claude needs user input
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read hook input
read -r input || true

# Find webhook URL
WEBHOOK_URL=""
[ -n "$FEISHU_WEBHOOK_URL" ] && WEBHOOK_URL="$FEISHU_WEBHOOK_URL"
[ -z "$WEBHOOK_URL" ] && [ -f "$HOME/.claude/feishu-webhook-url" ] && \
    WEBHOOK_URL=$(cat "$HOME/.claude/feishu-webhook-url" 2>/dev/null | tr -d '\n')

# Try project config
if [ -z "$WEBHOOK_URL" ]; then
    PROJECT_DIR=$(echo "$input" | grep -o '"cwd":"[^"]*"' | sed 's/"cwd":"//;s/"$//' || true)
    [ -n "$PROJECT_DIR" ] && [ -f "$PROJECT_DIR/.claude/.feishu-webhook-url" ] && \
        WEBHOOK_URL=$(cat "$PROJECT_DIR/.claude/.feishu-webhook-url" 2>/dev/null | tr -d '\n')
fi

[ -z "$WEBHOOK_URL" ] && exit 0

# Parse hook input
PERMISSION_MODE=$(echo "$input" | grep -o '"permission_mode":"[^"]*"' | sed 's/"permission_mode":"//;s/"$//' || echo "default")
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)
CWD=$(echo "$input" | grep -o '"cwd":"[^"]*"' | sed 's/"cwd":"//;s/"$//' || true)
SESSION_NAME=$(basename "$CWD" 2>/dev/null || echo "unknown")

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
        SUMMARY=$(echo "$LAST_CONTENT" | tail -c 60 | tr '\n' ' ')
        MESSAGE="[$SESSION_NAME] $SUMMARY"
    else
        MESSAGE="[$SESSION_NAME] Claude Code 等待输入"
    fi

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
