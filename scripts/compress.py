#!/usr/bin/env python3
"""
GAAP - Message Compression using Anthropic API
"""

import json
import sys
import os
import time
import urllib.request
import urllib.error

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


def call_anthropic(base_url, api_key, model, message, lang="zh"):
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
        "system": PROMPTS.get(lang, PROMPTS["zh"]),
        "messages": [{"role": "user", "content": message}]
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.load(resp)
        # Validate response structure
        if not result.get("content") or not result["content"][0].get("text"):
            raise ValueError("Invalid API response: missing content.text")
        return result["content"][0]["text"]


def compress(message):
    """Compress message using LLM API. Returns None on failure.

    Called by notify.sh when llm_mode is 'smart' or 'compress_all'.
    Just needs valid compress config with API key to work.
    """
    config = load_config()
    if not config:
        return None

    compress_cfg = config.get("compress", {})
    if not compress_cfg:
        return None

    base_url = compress_cfg.get("base_url", "https://api.anthropic.com").rstrip("/")
    model = compress_cfg.get("model", "claude-3-haiku-20240307")
    api_key = resolve_api_key(compress_cfg.get("api_key"))
    lang = compress_cfg.get("lang", "zh")

    if not api_key:
        return None

    try:
        return call_anthropic(base_url, api_key, model, message, lang)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as e:
        log_error("API call failed for message compression", e)
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
