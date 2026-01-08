#!/bin/bash
###############################################################################
# GAAP One-Click Installer
###############################################################################

set -e

REPO="https://github.com/gongwu-ai/GAAP.git"
INSTALL_DIR="$HOME/.gaap"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing GAAP..."

# Workaround for EXDEV bug (https://github.com/anthropics/claude-code/issues/14799)
mkdir -p "$HOME/.claude/tmp"
export TMPDIR="$HOME/.claude/tmp"

# Try official plugin install first
if command -v claude &> /dev/null; then
    echo "Trying official plugin install..."
    claude plugin marketplace add gongwu-ai/GAAP 2>/dev/null || true
    if claude plugin install gaap@gaap 2>/dev/null; then
        echo ""
        echo "✓ GAAP installed via plugin system!"
        echo ""
        echo "Next steps:"
        echo "  1. Run: claude  (then /gaap:setup)"
        echo "  2. Or run: python3 ~/.claude/plugins/marketplaces/gaap/scripts/setup.py"
        echo ""
        exit 0
    fi
    echo "Plugin install failed, falling back to hooks method..."
fi

# Fallback: clone and configure hooks
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
fi

mkdir -p "$HOME/.claude"

if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
    if grep -q "notify.sh" "$SETTINGS_FILE" 2>/dev/null; then
        echo "Hooks already configured."
    else
        python3 << 'PYTHON'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
install_dir = os.path.expanduser("~/.gaap")

with open(settings_file, 'r') as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})
hooks["Stop"] = [{"hooks": [{"type": "command", "command": f"{install_dir}/scripts/notify.sh"}]}]
hooks["PermissionRequest"] = [{"matcher": "", "hooks": [{"type": "command", "command": f"{install_dir}/scripts/permission_notify.sh"}]}]
settings["hooks"] = hooks

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
PYTHON
        echo "Hooks configured."
    fi
else
    cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "Stop": [{"hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/notify.sh"}]}],
    "PermissionRequest": [{"matcher": "", "hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/permission_notify.sh"}]}]
  }
}
EOF
    echo "Created settings.json."
fi

echo ""
echo "✓ GAAP installed!"
echo ""
echo "Next steps:"
echo "  1. Run: python3 ~/.gaap/scripts/setup.py"
echo "  2. Restart Claude Code"
echo ""
