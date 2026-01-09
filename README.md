# GAAP - Get Alerted by A Pigeon (鴿)

<p align="center">
  <img src="logo.svg" width="128" height="128" alt="GAAP Logo">
</p>

**Project-level** Feishu/Lark notifications for Claude Code. Get notified only when Claude needs your input.

## Features

- **Smart notifications**: Only alerts when Claude asks a question or needs confirmation
- **Project-scoped**: Config stays in your project's `.claude/` directory
- **Non-blocking**: Notification failures never interrupt Claude Code

## Installation

```bash
# Add marketplace
claude plugin marketplace add gongwu-ai/GAAP

# Install (with TMPDIR workaround for Linux, see issue #14799)
mkdir -p ~/.claude/tmp
TMPDIR=~/.claude/tmp claude plugin install gaap@gaap --scope project
```

**Fallback** (if plugin install fails):
```bash
curl -fsSL https://raw.githubusercontent.com/gongwu-ai/GAAP/main/install.sh | bash
```

## Setup

Run `/gaap:setup` in Claude Code. It will guide you through:
1. Feishu webhook URL configuration
2. (Optional) Message compression using LLM

## Known Issues & Workarounds

### Plugin Hooks Not Executing

Due to [Claude Code bug #14410](https://github.com/anthropics/claude-code/issues/14410), plugin hooks may not execute automatically.

**Workaround**: Install hooks directly to your project:

```bash
# After plugin install, run this in your project directory
python3 ~/.claude/plugins/marketplaces/gaap/scripts/install_hooks.py
# or for fallback install:
python3 ~/.gaap/scripts/install_hooks.py
```

This writes hooks to your project's `.claude/settings.json`, bypassing the plugin system limitation.

### Configuration

| File | Purpose |
|------|---------|
| `.env` | `FEISHU_WEBHOOK_URL`, `GAAP_API_KEY` (auto-ignored by git) |
| `.claude/gaap.json` | Compression settings (base_url, model, lang) |
| `.claude/settings.json` | Hook configuration (via install_hooks.py) |

## How It Works

When Claude Code finishes responding, the plugin:

1. Reads the last assistant message
2. Checks if it contains question marks or request keywords
3. Only sends notification if user input is needed

## Message Compression (Optional)

Feishu doesn't render Markdown. Enable LLM compression for cleaner messages.

Run `/gaap:setup` or create `.claude/gaap.json`:

```json
{
  "message_format": "compressed",
  "compress": {
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

Works with any Anthropic-compatible API.

## Troubleshooting

**Hooks not triggering?**

Check debug log:
```bash
cat /tmp/gaap_debug.log
```

If empty, verify hooks are installed:
```bash
# Check project settings
cat .claude/settings.json | grep -A5 hooks

# Re-install hooks if needed
python3 ~/.claude/plugins/marketplaces/gaap/scripts/install_hooks.py
```

**Manual test:**
```bash
echo '{"cwd":"'"$(pwd)"'"}' | ~/.claude/plugins/marketplaces/gaap/scripts/notify.sh
```

## Update

```bash
claude plugin update gaap@gaap
python3 ~/.claude/plugins/marketplaces/gaap/scripts/install_hooks.py  # Re-install hooks
```

## Uninstall

```bash
claude plugin uninstall gaap@gaap
rm .env .claude/gaap.json
# Edit .claude/settings.json to remove GAAP hooks
```

## License

MIT
