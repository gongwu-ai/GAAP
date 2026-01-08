#!/bin/bash
###############################################################################
# GAAP One-Click Installer
###############################################################################

set -e

REPO="https://github.com/gongwu-ai/GAAP.git"
INSTALL_DIR="$HOME/.gaap"
SETTINGS_FILE="$HOME/.claude/settings.json"

echo "Installing GAAP..."

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR" && git pull
else
    echo "Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
fi

# Ensure .claude directory exists
mkdir -p "$HOME/.claude"

# Merge hooks into settings.json
if [ -f "$SETTINGS_FILE" ]; then
    # Backup existing settings
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"

    # Check if hooks already configured
    if grep -q "notify.sh" "$SETTINGS_FILE" 2>/dev/null; then
        echo "Hooks already configured, skipping..."
    else
        # Use python to merge JSON (more reliable than jq)
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
    # Create new settings.json
    cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "Stop": [{"hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/notify.sh"}]}],
    "PermissionRequest": [{"matcher": "", "hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/permission_notify.sh"}]}]
  }
}
EOF
    echo "Created settings.json with hooks."
fi

echo ""
echo "✓ GAAP installed!"
echo ""
echo "Next steps:"
echo "  1. Run: python3 ~/.gaap/scripts/setup.py"
echo "  2. Restart Claude Code"
echo ""
