---
description: Configure Feishu webhook for Claude Code notifications
---

# GAAP Setup Wizard

Help the user set up Feishu notifications step by step.

## Step 1: Create Feishu Bot

Guide the user:

1. Open Feishu app (desktop or mobile)
2. Go to the group chat where you want notifications
3. Click "..." menu at top right
4. Select "Settings" > "Bots"
5. Click "Add Bot"
6. Choose "Custom Bot"
7. Set bot name (e.g., "Claude Code")
8. Click "Add"
9. **Copy the webhook URL** (starts with `https://open.feishu.cn/open-apis/bot/v2/hook/`)

## Step 2: Store Webhook URL

After user provides the webhook URL, help them store it:

### Option A: User scope (recommended)

```bash
mkdir -p ~/.claude
echo "WEBHOOK_URL_HERE" > ~/.claude/feishu-webhook-url
chmod 600 ~/.claude/feishu-webhook-url
```

### Option B: Project scope

```bash
mkdir -p .claude
echo "WEBHOOK_URL_HERE" > .claude/.feishu-webhook-url
echo ".claude/.feishu-webhook-url" >> .gitignore
```

## Step 3: Test

Send a test message:

```bash
curl -X POST "WEBHOOK_URL_HERE" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"GAAP test notification"}}'
```

If the message appears in Feishu, setup is complete!

## Troubleshooting

- **No notification?** Check if webhook URL is correct
- **Permission denied?** Run `chmod 600 ~/.claude/feishu-webhook-url`
- **Still not working?** Check `~/.claude/logs/claude-code.log` for errors
