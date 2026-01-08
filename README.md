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

**Option 1: From GitHub (recommended)**
```bash
claude plugin add github:gongwu-ai/GAAP
```

**Option 2: Via Marketplace**
```bash
/plugin marketplace add gongwu-ai/GAAP
/plugin install gaap@gaap
```

**Option 3: Local install**
```bash
git clone https://github.com/gongwu-ai/GAAP.git
claude plugin install ./GAAP
```

## Setup

Run the setup wizard:

```
/gaap:setup
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

Run `/gaap:setup` or create `~/.claude/gaap.json`:

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

For local installations:

```bash
cd ~/projects/GAAP && git pull
# Restart Claude Code to apply changes
```

## Uninstall

```bash
claude plugin uninstall gaap
rm ~/.claude/feishu-webhook-url
rm ~/.claude/gaap.json
```

## License

MIT
