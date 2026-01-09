#!/usr/bin/env python3
"""
GAAP - Session Title Generator with Caching
Generates intelligent session titles using LLM or falls back to folder_uuid
"""

import json
import sys
import os
import hashlib
import re
import urllib.request
import urllib.error
from pathlib import Path

# Project-level config (via GAAP_PROJECT_DIR env var)
PROJECT_DIR = os.environ.get("GAAP_PROJECT_DIR", ".")
CONFIG_PATH = os.path.join(PROJECT_DIR, ".claude/gaap.json")
CACHE_PATH = os.path.join(PROJECT_DIR, ".claude/.gaap_session_cache.json")

TITLE_PROMPTS = {
    "zh": "将下面的用户消息总结为一个简短的标题（5-10个字），只输出标题，不要引号或其他内容：\n\n",
    "en": "Summarize the user message below into a short title (3-6 words). Output only the title, no quotes or extra text:\n\n"
}


def load_config():
    """Load GAAP configuration"""
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return None


def load_cache():
    """Load session title cache"""
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_cache(cache):
    """Save session title cache"""
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, 'w') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except:
        pass


def resolve_api_key(key_str):
    """Resolve API key - supports $ENV_VAR format"""
    if not key_str:
        return None
    if key_str.startswith("$"):
        return os.environ.get(key_str[1:])
    return key_str


def call_api(base_url, api_key, model, message, lang="zh"):
    """Call Anthropic-compatible API to generate title"""
    url = f"{base_url}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    prompt = TITLE_PROMPTS.get(lang, TITLE_PROMPTS["zh"]) + message

    data = {
        "model": model,
        "max_tokens": 50,
        "messages": [{"role": "user", "content": prompt}]
    }

    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req, timeout=5) as resp:
        result = json.load(resp)
        title = result["content"][0]["text"].strip()
        # Clean quotes if present
        title = re.sub(r'^["\']|["\']$', '', title)
        return title


def extract_first_message(transcript_path):
    """Extract first meaningful user message from transcript"""
    try:
        with open(transcript_path) as f:
            for line in f:
                data = json.loads(line)
                if data.get('type') == 'user':
                    content = data.get('message', {}).get('content', '')
                    # Skip commands and login messages
                    if any(x in content for x in ['<command-', '<local-command-', 'Login successful', '/login']):
                        continue
                    # Clean HTML tags
                    text = re.sub(r'<[^>]+>', '', content).strip()
                    if len(text) > 10:
                        return text[:200]  # Return first 200 chars for title generation
        return None
    except:
        return None


def generate_fallback_title(cwd):
    """Generate fallback title: folder_name + 6-char UUID"""
    folder_name = os.path.basename(cwd) if cwd else "session"
    # Generate deterministic 6-char hash from cwd
    hash_obj = hashlib.md5(cwd.encode() if cwd else b"unknown")
    short_uuid = hash_obj.hexdigest()[:6]
    return f"{folder_name}_{short_uuid}"


def get_session_id(transcript_path):
    """Extract session ID from transcript path"""
    # Path format: .../.claude/projects/{encoded_path}/{session_id}.jsonl
    return Path(transcript_path).stem


def get_message_hash(message):
    """Generate hash of first message for cache validation"""
    if not message:
        return ""
    return hashlib.md5(message.encode()).hexdigest()[:8]


def generate_title(transcript_path, cwd):
    """
    Generate session title with caching
    - Uses API if configured
    - Falls back to folder_name_uuid
    - Caches result to avoid repeated API calls
    """
    session_id = get_session_id(transcript_path)
    first_message = extract_first_message(transcript_path)
    message_hash = get_message_hash(first_message)

    # Check cache
    cache = load_cache()
    if session_id in cache:
        cached = cache[session_id]
        if cached.get("message_hash") == message_hash:
            return cached["title"]

    # Generate new title
    config = load_config()
    title = None

    # Try API if configured
    if config and config.get("message_format") == "compressed" and first_message:
        compress_cfg = config.get("compress", {})
        base_url = compress_cfg.get("base_url", "").rstrip("/")
        model = compress_cfg.get("model", "claude-3-haiku-20240307")
        api_key = resolve_api_key(compress_cfg.get("api_key"))
        lang = compress_cfg.get("lang", "zh")

        if api_key and base_url:
            try:
                title = call_api(base_url, api_key, model, first_message, lang)
            except:
                pass  # Fall through to fallback

    # Fallback
    if not title:
        title = generate_fallback_title(cwd)

    # Save to cache
    cache[session_id] = {
        "title": title,
        "message_hash": message_hash
    }
    save_cache(cache)

    return title


def main():
    """
    Usage: get_session_title.py <transcript_path> <cwd>
    Returns: session title
    """
    if len(sys.argv) < 3:
        print("?")
        return

    transcript_path = sys.argv[1]
    cwd = sys.argv[2]

    if not os.path.exists(transcript_path):
        print(generate_fallback_title(cwd))
        return

    title = generate_title(transcript_path, cwd)
    print(title)


if __name__ == "__main__":
    main()
