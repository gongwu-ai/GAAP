---
description: Configure GAAP Feishu notifications
---

# GAAP Setup

Help the user configure GAAP (Feishu/飞书 notifications for Claude Code).

## Step 1: Webhook URL

Ask the user for their Feishu webhook URL. They can get this by:
1. Creating a custom bot in their Feishu group
2. Copying the webhook URL (format: `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`)

Save it to the project's `.claude/feishu-webhook-url`:
```bash
mkdir -p .claude
echo "WEBHOOK_URL" > .claude/feishu-webhook-url
chmod 600 .claude/feishu-webhook-url
```

## Step 2: Message Compression (Optional)

Ask if they want to enable message compression. Feishu doesn't render Markdown, so compression converts messages to plain text using an LLM.

If yes, ask for:
- **base_url**: API endpoint (default: `https://api.anthropic.com`)
- **model**: Model name (default: `claude-3-haiku-20240307`)
- **api_key**: API key (supports `$ENV_VAR` format, e.g. `$ANTHROPIC_API_KEY`)
- **lang**: Output language - `zh` (中文) or `en` (English)

Save config to `.claude/gaap.json`:
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

If they don't want compression, save:
```json
{
  "message_format": "full"
}
```

## Step 3: Test

Send a test notification:
```bash
curl -s -X POST "$(cat .claude/feishu-webhook-url)" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"GAAP test - setup complete!"}}'
```

## Fallback

If the interactive setup doesn't work, user can run:
```bash
python3 ~/.claude/plugins/marketplaces/gaap/scripts/setup.py
# or if installed via fallback:
python3 ~/.gaap/scripts/setup.py
```
