#!/bin/bash
###############################################################################
# GAAP Installer
###############################################################################

set -e

echo "Installing GAAP..."

# Workaround for EXDEV bug (https://github.com/anthropics/claude-code/issues/14799)
mkdir -p "$HOME/.claude/tmp"
export TMPDIR="$HOME/.claude/tmp"

# Check if claude CLI exists
if ! command -v claude &> /dev/null; then
    echo "❌ Error: 'claude' command not found."
    echo "   Please install Claude Code first: https://claude.ai/code"
    exit 1
fi

# Add marketplace
echo "Adding GAAP marketplace..."
claude plugin marketplace add gongwu-ai/GAAP

# Install plugin
echo "Installing GAAP plugin..."
if ! claude plugin install gaap@gaap --scope project; then
    echo ""
    echo "❌ Plugin installation failed."
    echo "   Please check your network connection and try again."
    exit 1
fi

PLUGIN_ROOT="$HOME/.claude/plugins/marketplaces/gaap"

echo ""
echo "✓ GAAP installed!"
echo ""
echo "⚠️  Due to Claude Code bug #14410, plugin hooks don't auto-execute."
echo ""
echo "Next steps:"
echo "  1. In your project directory, run:"
echo "     python3 $PLUGIN_ROOT/scripts/install_hooks.py"
echo ""
echo "  2. Run /gaap:setup in Claude Code to configure"
echo ""
