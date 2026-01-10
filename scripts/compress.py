#!/usr/bin/env python3
"""
GAAP - Message Compression using Anthropic SDK

Only supports Anthropic protocol compatible APIs.
"""

import json
import sys
import os
import time

try:
    import anthropic
except ImportError:
    print("Error: anthropic package required. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Project-level config (via GAAP_PROJECT_DIR env var)
PROJECT_DIR = os.environ.get("GAAP_PROJECT_DIR", ".")
CONFIG_PATH = os.path.join(PROJECT_DIR, ".claude/gaap.json")
ERROR_LOG_PATH = os.path.join(PROJECT_DIR, ".claude/.gaap_error.log")

PROMPTS = {
    "zh": "将消息压缩成简短口语化的中文，去除所有Markdown格式。保留核心信息，最多100字。只输出压缩结果。",
    "en": "Compress the message into concise conversational English. Remove all Markdown formatting. Keep core info only, max 50 words. Output only the result."
}


def log_error(message, error=None):
    """Log errors to a file for debugging"""
    try:
        os.makedirs(os.path.dirname(ERROR_LOG_PATH), exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        error_detail = f": {type(error).__name__}: {error}" if error else ""
        with open(ERROR_LOG_PATH, 'a') as f:
            f.write(f"[{timestamp}] compress.py: {message}{error_detail}\n")
    except Exception:
        pass  # Don't fail if we can't write to log


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        log_error(f"Failed to load config from {CONFIG_PATH}", e)
        return None


def resolve_api_key(key_str):
    """Resolve API key - supports $ENV_VAR format"""
    if not key_str:
        return None
    if key_str.startswith("$"):
        return os.environ.get(key_str[1:])
    return key_str


def call_api(base_url, api_key, model, message, lang="zh"):
    """Call Anthropic-compatible API using SDK (handles /v1/messages automatically)"""
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url,
        timeout=15.0,
    )

    response = client.messages.create(
        model=model,
        max_tokens=200,
        system=PROMPTS.get(lang, PROMPTS["zh"]),
        messages=[{"role": "user", "content": message}]
    )

    return response.content[0].text


def compress(message):
    """Compress message using Anthropic SDK. Returns None on failure.

    Called by notify.sh when llm_mode is 'smart' or 'compress_all'.
    Only supports Anthropic protocol compatible APIs.
    """
    config = load_config()
    if not config:
        return None

    compress_cfg = config.get("compress", {})
    if not compress_cfg:
        return None

    # base_url - SDK automatically handles /v1/messages
    base_url = compress_cfg.get("base_url", "https://api.anthropic.com")
    model = compress_cfg.get("model", "claude-3-haiku-20240307")
    api_key = resolve_api_key(compress_cfg.get("api_key"))
    lang = compress_cfg.get("lang", "zh")

    if not api_key:
        return None

    try:
        return call_api(base_url, api_key, model, message, lang)
    except anthropic.APIError as e:
        log_error("Anthropic API error", e)
        return None
    except Exception as e:
        log_error("Unexpected error during compression", e)
        return None


def main():
    message = sys.stdin.read().strip()
    if not message:
        return

    compressed = compress(message)
    print(compressed if compressed else message)


if __name__ == "__main__":
    main()
