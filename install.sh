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

PLUGIN_ROOT=""
INSTALL_METHOD=""

# Try official plugin install first
if command -v claude &> /dev/null; then
    echo "Trying official plugin install..."
    claude plugin marketplace add gongwu-ai/GAAP 2>/dev/null || true
    if claude plugin install gaap@gaap 2>/dev/null; then
        PLUGIN_ROOT="$HOME/.claude/plugins/marketplaces/gaap"
        INSTALL_METHOD="plugin"
        echo ""
        echo "✓ GAAP installed via plugin system!"
    fi
fi

# Fallback: clone to ~/.gaap
if [ -z "$PLUGIN_ROOT" ]; then
    echo "Plugin install failed, using fallback method..."
    if [ -d "$INSTALL_DIR" ]; then
        echo "Updating existing installation..."
        cd "$INSTALL_DIR" && git pull
    else
        echo "Cloning repository..."
        git clone "$REPO" "$INSTALL_DIR"
    fi
    PLUGIN_ROOT="$INSTALL_DIR"
    INSTALL_METHOD="fallback"
    echo ""
    echo "✓ GAAP installed!"
fi

# Configure hooks in current project or global settings
echo ""
echo "Configuring hooks..."

if [ "$INSTALL_METHOD" = "plugin" ]; then
    # For plugin install, suggest running install_hooks.py in project
    echo ""
    echo "⚠️  Due to Claude Code bug #14410, plugin hooks don't auto-execute."
    echo ""
    echo "In EACH project where you want GAAP notifications, run:"
    echo "  cd /path/to/your/project"
    echo "  python3 $PLUGIN_ROOT/scripts/install_hooks.py"
    echo ""
else
    # For fallback install, configure global hooks
    mkdir -p "$HOME/.claude"

    if [ -f "$SETTINGS_FILE" ]; then
        cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
        if grep -q "notify.sh" "$SETTINGS_FILE" 2>/dev/null; then
            echo "Hooks already configured."
        else
            python3 << PYTHON
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
install_dir = os.path.expanduser("~/.gaap")

with open(settings_file, 'r') as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})
hooks["Notification"] = [{"hooks": [{"type": "command", "command": f"{install_dir}/scripts/notify.sh", "timeout": 10}]}]
hooks["Stop"] = [{"matcher": "", "hooks": [{"type": "command", "command": f"{install_dir}/scripts/notify.sh", "timeout": 10}]}]
hooks["PermissionRequest"] = [{"matcher": "", "hooks": [{"type": "command", "command": f"{install_dir}/scripts/permission_notify.sh", "timeout": 10}]}]
settings["hooks"] = hooks

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
PYTHON
            echo "✓ Hooks configured globally."
        fi
    else
        cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "Notification": [{"hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/notify.sh", "timeout": 10}]}],
    "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/notify.sh", "timeout": 10}]}],
    "PermissionRequest": [{"matcher": "", "hooks": [{"type": "command", "command": "$INSTALL_DIR/scripts/permission_notify.sh", "timeout": 10}]}]
  }
}
EOF
        echo "✓ Created settings.json with hooks."
    fi
fi

echo ""
echo "Next steps:"
echo "  1. Run: python3 $PLUGIN_ROOT/scripts/setup.py"
echo "  2. Restart Claude Code"
if [ "$INSTALL_METHOD" = "plugin" ]; then
    echo "  3. In each project: python3 $PLUGIN_ROOT/scripts/install_hooks.py"
fi
echo ""
