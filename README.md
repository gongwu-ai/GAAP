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

Then restart Claude Code.

## Setup

Run `/gaap:setup` in Claude Code, or manually configure:

1. Create a custom bot in your Feishu group
2. Copy the webhook URL
3. Store it in your project:

```bash
mkdir -p .claude
echo "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN" > .claude/feishu-webhook-url
chmod 600 .claude/feishu-webhook-url
```

## Configuration

| File | Purpose |
|------|---------|
| `.env` | `FEISHU_WEBHOOK_URL`, `GAAP_API_KEY` (auto-ignored by git) |
| `.claude/gaap.json` | Compression settings (base_url, model, lang) |

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
    "api_key": "$ANTHROPIC_API_KEY",
    "lang": "zh"
  }
}
```

Works with any Anthropic-compatible API. Get your API key from your provider.

## Update

```bash
claude plugin update gaap@gaap
```

## Uninstall

```bash
claude plugin uninstall gaap@gaap
rm .claude/feishu-webhook-url .claude/gaap.json
```

## License

MIT
