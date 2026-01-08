#!/usr/bin/env python3
"""
GAAP - Message Compression using Anthropic API
"""

import json
import sys
import os
import urllib.request
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.claude/gaap.json")

SYSTEM_PROMPT = """将消息压缩成简短口语化的中文，去除所有Markdown格式。保留核心信息，最多100字。只输出压缩结果。"""


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return None


def resolve_api_key(key_str):
    """Resolve API key - supports $ENV_VAR format"""
    if not key_str:
        return None
    if key_str.startswith("$"):
        return os.environ.get(key_str[1:])
    return key_str


def call_anthropic(base_url, api_key, model, message):
    """Call Anthropic API"""
    url = f"{base_url}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": model,
        "max_tokens": 200,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": message}]
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.load(resp)
        return result["content"][0]["text"]


def compress(message):
    """Compress message using Anthropic API. Returns None on failure."""
    config = load_config()
    if not config or config.get("message_format") != "compressed":
        return None

    compress_cfg = config.get("compress", {})
    base_url = compress_cfg.get("base_url", "https://api.anthropic.com").rstrip("/")
    model = compress_cfg.get("model", "claude-3-haiku-20240307")
    api_key = resolve_api_key(compress_cfg.get("api_key"))

    if not api_key:
        return None

    try:
        return call_anthropic(base_url, api_key, model, message)
    except:
        return None


def main():
    message = sys.stdin.read().strip()
    if not message:
        return

    compressed = compress(message)
    print(compressed if compressed else message)


if __name__ == "__main__":
    main()
