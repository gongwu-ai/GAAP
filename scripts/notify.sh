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

# DEBUG: trace webhook loading
echo "[$(date '+%Y-%m-%d %H:%M:%S')] CWD=$CWD, WEBHOOK_URL set=${WEBHOOK_URL:+yes}" >> "${CWD:-.}/.claude/.gaap_trace.log" 2>/dev/null || true
[ -z "$WEBHOOK_URL" ] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] EXIT: no webhook URL" >> "${CWD:-.}/.claude/.gaap_trace.log" 2>/dev/null && exit 0

# Parse hook input
PERMISSION_MODE=$(echo "$input" | grep -o '"permission_mode":"[^"]*"' | sed 's/"permission_mode":"//;s/"$//' || echo "default")
TRANSCRIPT_PATH=$(echo "$input" | grep -o '"transcript_path":"[^"]*"' | sed 's/"transcript_path":"//;s/"$//' || true)

# Load config from gaap.json
LLM_MODE="none"
PYTHON=""
CONFIG_FILE="$CWD/.claude/gaap.json"
if [ -f "$CONFIG_FILE" ]; then
    LLM_MODE=$(grep -o '"llm_mode"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | sed 's/"llm_mode"[[:space:]]*:[[:space:]]*"//;s/"$//' || echo "none")
    [ -z "$LLM_MODE" ] && LLM_MODE="none"
    # Get Python path (saved by install_hooks.py)
    PYTHON_PATH=$(grep -o '"python_path"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | sed 's/"python_path"[[:space:]]*:[[:space:]]*"//;s/"$//' || true)
    if [ -n "$PYTHON_PATH" ] && [ -x "$PYTHON_PATH" ]; then
        PYTHON="$PYTHON_PATH"
    fi
fi

# Fallback to system python3 if not configured
if [ -z "$PYTHON" ]; then
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
    fi
fi

# Helper: send error to Feishu
send_error() {
    local error_msg="$1"
    local host=$(hostname -s 2>/dev/null || echo "?")
    local msg="[$host|GAAP] ⚠️ $error_msg"
    curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$msg\"}}" \
        --connect-timeout 5 --max-time 10 > /dev/null 2>&1 || true
}

# Get hostname (short form)
HOST=$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo "?")

# Check Python availability
if [ -z "$PYTHON" ]; then
    send_error "Python未找到! 请运行: python3 ~/.claude/plugins/marketplaces/gaap/scripts/install_hooks.py"
    exit 1
fi

# Get session title (cached, LLM-generated if API configured)
SESSION_NAME=$(GAAP_PROJECT_DIR="$CWD" GAAP_API_KEY="$GAAP_API_KEY" "$PYTHON" "$SCRIPT_DIR/get_session_title.py" "$TRANSCRIPT_PATH" "$CWD" 2>&1)
if [ $? -ne 0 ]; then
    # Script failed, send error with details
    send_error "get_session_title.py 失败: $SESSION_NAME"
    SESSION_NAME=$(basename "$CWD" 2>/dev/null || echo "?")
fi

# Check auto-approve mode
AUTO_APPROVE=false
case "$PERMISSION_MODE" in
    acceptEdits|dontAsk|bypassPermissions) AUTO_APPROVE=true ;;
esac

# Read last message from transcript
# Format: {"message":{"role":"assistant","content":[{"type":"text","text":"..."}]}}
LAST_CONTENT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    # Try new format first (role:assistant), fallback to old format (type:assistant)
    LAST_LINE=$(tail -50 "$TRANSCRIPT_PATH" | grep '"role":"assistant"' | tail -1 || true)
    if [ -z "$LAST_LINE" ]; then
        LAST_LINE=$(tail -50 "$TRANSCRIPT_PATH" | grep '"type":"assistant"' | tail -1 || true)
    fi
    if [ -n "$LAST_LINE" ]; then
        # Extract text from content array or direct text field
        LAST_CONTENT=$(echo "$LAST_LINE" | grep -o '"text":"[^"]*"' | tail -1 | \
            sed 's/"text":"//;s/"$//' | sed 's/\\n/ /g' || true)
    fi
    # DEBUG: Log to file
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] LAST_LINE len=${#LAST_LINE}, LAST_CONTENT len=${#LAST_CONTENT}" >> "$CWD/.claude/.gaap_trace.log"
    if [ -z "$LAST_CONTENT" ]; then
        CONTENT_TYPES=$(echo "$LAST_LINE" | grep -o '"type":"[^"]*"' | tr '\n' ',' || echo "unknown")
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] No text found. types=$CONTENT_TYPES" >> "$CWD/.claude/.gaap_trace.log"
        send_error "DEBUG: 没找到text. types=$CONTENT_TYPES"
    fi
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
echo "[$(date '+%Y-%m-%d %H:%M:%S')] SEND_NOTIFICATION=$SEND_NOTIFICATION, USE_LLM_COMPRESS=$USE_LLM_COMPRESS, LLM_MODE=$LLM_MODE" >> "$CWD/.claude/.gaap_trace.log"
if [ "$SEND_NOTIFICATION" = true ]; then
    if [ -n "$LAST_CONTENT" ]; then
        if [ "$USE_LLM_COMPRESS" = true ]; then
            # Try to compress message using LLM (fallback to plain text)
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Calling compress.py with PYTHON=$PYTHON" >> "$CWD/.claude/.gaap_trace.log"
            COMPRESS_OUTPUT=$(echo "$LAST_CONTENT" | GAAP_PROJECT_DIR="$CWD" GAAP_API_KEY="$GAAP_API_KEY" "$PYTHON" "$SCRIPT_DIR/compress.py" 2>&1)
            COMPRESS_STATUS=$?
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] compress.py status=$COMPRESS_STATUS, output_len=${#COMPRESS_OUTPUT}" >> "$CWD/.claude/.gaap_trace.log"
            if [ $COMPRESS_STATUS -ne 0 ]; then
                # Compression failed, send error and use plain text
                send_error "compress.py 失败: $COMPRESS_OUTPUT"
                COMPRESSED="$LAST_CONTENT"
            else
                COMPRESSED="$COMPRESS_OUTPUT"
            fi
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
