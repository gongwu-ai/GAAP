---
description: Configure GAAP Feishu notifications
---

# GAAP Setup

Help the user configure GAAP (Feishu/飞书 notifications for Claude Code).

## Step 1: Webhook URL

Ask the user for their Feishu webhook URL. They can get this by:
1. Creating a custom bot in their Feishu group
2. Copying the webhook URL (format: `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`)

Save it to the project's `.env` file. **IMPORTANT**:
- First Read `.env` to check existing content
- If `FEISHU_WEBHOOK_URL` exists, use Edit to update it
- If not, append the new line (preserve existing content!)
- Never overwrite or duplicate existing keys

Example (if .env doesn't exist or key is missing):
```
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

Note: `.env` is typically auto-ignored by git and many IDEs.

## Step 2: Message Compression (Optional)

Ask if they want to enable message compression. Feishu doesn't render Markdown, so compression converts messages to plain text using an LLM.

If yes, ask for:
- **base_url**: API endpoint (default: `https://api.anthropic.com`)
- **model**: Model name (default: `claude-3-haiku-20240307`)
- **api_key**: API key from their provider
- **lang**: Output language - `zh` (中文) or `en` (English)

Save the API key to `.env` (same merge logic as Step 1 - update if exists, append if not):
```
GAAP_API_KEY=sk-xxx
```

Save config to `.claude/gaap.json` (references the env var):
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

If they don't want compression, save:
```json
{
  "message_format": "full"
}
```

## Step 3: Test

Send a test notification:
```bash
source .env && curl -s -X POST "$FEISHU_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"GAAP test - setup complete!"}}'
```

## Step 4: Install Hooks (Required!)

Due to a [Claude Code bug](https://github.com/anthropics/claude-code/issues/14410), plugin hooks don't execute automatically.

Install hooks directly to the project:
```bash
python3 ~/.claude/plugins/marketplaces/gaap/scripts/install_hooks.py
```

This writes hooks to `.claude/settings.json`. Verify with:
```bash
cat .claude/settings.json | grep -A5 hooks
```

**Note**: Running `install_hooks.py` multiple times is safe - it removes old GAAP hooks before adding new ones.

## Fallback

If the interactive setup doesn't work, user can run:
```bash
python3 ~/.claude/plugins/marketplaces/gaap/scripts/setup.py
```
