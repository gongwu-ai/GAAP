# GAAP - Get Alerted by A Pigeon (鴿)

<p align="center">
  <img src="logo.svg" width="128" height="128" alt="GAAP Logo">
</p>

Smart Feishu/Lark notifications for Claude Code. Get notified only when Claude needs your input.

## Features

- **Smart notifications**: Only alerts when Claude asks a question or needs confirmation
- **Cross-platform**: Works on Linux, macOS, and WSL
- **Flexible config**: User-scope, project-scope, or environment variable
- **Non-blocking**: Notification failures never interrupt Claude Code

## Installation

```bash
# Add marketplace
claude plugin marketplace add gongwu-ai/GAAP

# Install (with TMPDIR workaround for Linux, see issue #14799)
mkdir -p ~/.claude/tmp
TMPDIR=~/.claude/tmp claude plugin install gaap@gaap
```

**Fallback** (if plugin install fails):
```bash
curl -fsSL https://raw.githubusercontent.com/gongwu-ai/GAAP/main/install.sh | bash
```

Then restart Claude Code.

## Setup

Run the setup wizard:

```bash
# If installed via plugin
python3 ~/.claude/plugins/marketplaces/gaap/scripts/setup.py

# If installed via fallback
python3 ~/.gaap/scripts/setup.py
```

Or manually configure:

1. Create a custom bot in your Feishu group
2. Copy the webhook URL
3. Store it:

```bash
mkdir -p ~/.claude
echo "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN" > ~/.claude/feishu-webhook-url
chmod 600 ~/.claude/feishu-webhook-url
```

## Configuration Priority

The plugin looks for webhook URL in this order:

1. `$FEISHU_WEBHOOK_URL` environment variable
2. `~/.claude/feishu-webhook-url` (user scope)
3. `.claude/.feishu-webhook-url` in project root (project scope)
4. `/etc/claude-code/feishu-webhook-url` (enterprise scope)

## How It Works

When Claude Code finishes responding, the plugin:

1. Reads the last assistant message
2. Checks if it contains question marks or request keywords
3. Only sends notification if user input is needed

This means you won't be spammed with notifications for every response.

## Message Compression (Optional)

Feishu doesn't render Markdown. Enable LLM compression for cleaner messages.

Run the setup wizard or create `~/.claude/gaap.json`:

```json
{
  "message_format": "compressed",
  "compress": {
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key": "$ANTHROPIC_API_KEY"
  }
}
```

Works with any Anthropic-compatible API. Get your API key from your provider.

API key supports `$ENV_VAR` format. Compression failure auto-falls back to full message.

## Update

```bash
# If installed via plugin
claude plugin update gaap@gaap

# If installed via fallback
cd ~/.gaap && git pull
```

Restart Claude Code to apply changes.

## Uninstall

```bash
# If installed via plugin
claude plugin uninstall gaap@gaap

# If installed via fallback (also remove hooks from ~/.claude/settings.json)
rm -rf ~/.gaap

# Clean up config
rm ~/.claude/feishu-webhook-url ~/.claude/gaap.json
```

## License

MIT
