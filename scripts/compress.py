#!/usr/bin/env python3
"""
GAAP - Message Compression using LLM
Supports: Anthropic, OpenAI-compatible APIs (DeepSeek, GLM, Ollama, etc.)
"""

import json
import sys
import os
import urllib.request
import urllib.error

CONFIG_PATH = os.path.expanduser("~/.claude/gaap.json")

SYSTEM_PROMPT = """将消息压缩成简短口语化的中文，去除所有Markdown格式（代码块、表格、加粗、列表等）。
保留核心信息，最多100字。只输出压缩结果，不要任何前缀或解释。"""


def load_config():
    """Load GAAP config from ~/.claude/gaap.json"""
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return None


def compress_anthropic(message: str, config: dict) -> str:
    """Compress using Anthropic API"""
    api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    model = config.get("model", "claude-3-haiku-20240307")
    base_url = config.get("base_url", "https://api.anthropic.com")

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
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.load(resp)
            return result["content"][0]["text"]
    except:
        return None


def compress_openai(message: str, config: dict) -> str:
    """Compress using OpenAI-compatible API (DeepSeek, GLM, Ollama, etc.)"""
    api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
    base_url = config.get("base_url", "https://api.openai.com/v1")
    model = config.get("model", "gpt-4o-mini")

    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data = {
        "model": model,
        "max_tokens": 200,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.load(resp)
            return result["choices"][0]["message"]["content"]
    except:
        return None


def compress(message: str) -> str:
    """
    Compress message using configured LLM.
    Returns compressed message or None (fallback to original).
    """
    config = load_config()
    if not config:
        return None

    if config.get("message_format") != "compressed":
        return None

    compress_config = config.get("compress", {})
    provider = compress_config.get("provider", "anthropic")

    if provider == "anthropic":
        return compress_anthropic(message, compress_config)
    else:  # openai-compatible
        return compress_openai(message, compress_config)


def main():
    """Read message from stdin, output compressed or original"""
    message = sys.stdin.read().strip()
    if not message:
        return

    compressed = compress(message)
    if compressed:
        print(compressed)
    else:
        print(message)


if __name__ == "__main__":
    main()
