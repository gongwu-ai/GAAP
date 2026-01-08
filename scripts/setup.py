#!/usr/bin/env python3
"""
GAAP Setup - Interactive configuration wizard
"""

import os
import sys
import json
import re

# Project-level config
ENV_PATH = ".env"
CONFIG_DIR = ".claude"
CONFIG_PATH = os.path.join(CONFIG_DIR, "gaap.json")

# ANSI colors
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    print(f"""
{BOLD}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   {CYAN}🕊️  GAAP - Get Alerted by A Pigeon{RESET}{BOLD}                     ║
║                                                          ║
║   飞书通知插件配置向导                                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def print_step(num, total, title):
    print(f"\n{BOLD}[{num}/{total}] {title}{RESET}\n")


def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{CYAN}{default}{RESET}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def load_env():
    """Load existing .env file as dict"""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip().strip('"\'')
    return env


def save_env(env):
    """Save dict to .env file, preserving comments"""
    lines = []
    existing_keys = set()

    # Read existing file to preserve comments and order
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    lines.append(line.rstrip())
                elif '=' in line:
                    key = line.split('=', 1)[0].strip()
                    existing_keys.add(key)
                    if key in env:
                        lines.append(f'{key}={env[key]}')
                    else:
                        lines.append(line.rstrip())

    # Add new keys
    for key, value in env.items():
        if key not in existing_keys:
            lines.append(f'{key}={value}')

    with open(ENV_PATH, 'w') as f:
        f.write('\n'.join(lines) + '\n')


def setup_webhook():
    print_step(1, 3, "配置飞书 Webhook")

    print(f"""
{YELLOW}如何获取 Webhook URL:{RESET}
1. 打开飞书群聊
2. 点击右上角 ... → 设置 → 群机器人
3. 添加自定义机器人
4. 复制 Webhook 地址
""")

    env = load_env()
    current = env.get("FEISHU_WEBHOOK_URL", "")
    if current:
        print(f"当前配置: {GREEN}{current[:50]}...{RESET}\n")

    webhook = get_input("Webhook URL", current if current else None)

    if webhook and webhook.startswith("http"):
        env["FEISHU_WEBHOOK_URL"] = webhook
        save_env(env)
        print(f"\n{GREEN}✓ Webhook 已保存到 .env{RESET}")
        return True
    else:
        print(f"\n{RED}✗ 无效的 URL{RESET}")
        return False


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def setup_compression():
    print_step(2, 3, "配置消息压缩 (可选)")

    existing = load_config()
    compress_cfg = existing.get("compress", {})
    is_compressed = existing.get("message_format") == "compressed"

    print(f"""
{YELLOW}消息压缩功能:{RESET}
飞书不渲染 Markdown，使用 LLM 将消息压缩成口语化格式。
压缩失败会自动回退到全量发送。
""")

    default_enable = "y" if is_compressed else "n"
    choice = get_input(f"启用消息压缩? (y/N)", default_enable).lower()

    if choice != 'y':
        config = {"message_format": "full"}
        save_config(config)
        print(f"\n{GREEN}✓ 将发送全量消息{RESET}")
        return True

    print(f"\n{BOLD}配置 LLM Endpoint:{RESET}\n")

    base_url = get_input("Base URL", compress_cfg.get("base_url", "https://api.anthropic.com"))
    model = get_input("Model", compress_cfg.get("model", "claude-3-haiku-20240307"))

    print(f"\n{YELLOW}API Key 会保存到 .env 文件{RESET}")

    # Load existing key from env
    env = load_env()
    existing_key = env.get("GAAP_API_KEY", "")
    if existing_key:
        # Show masked key
        masked = existing_key[:8] + "..." + existing_key[-4:] if len(existing_key) > 12 else "***"
        api_key = get_input(f"API Key (当前: {masked})", existing_key)
    else:
        api_key = get_input("API Key")

    # Save API key to .env
    if api_key and not api_key.startswith("$"):
        env["GAAP_API_KEY"] = api_key
        save_env(env)
        api_key_ref = "$GAAP_API_KEY"
    else:
        api_key_ref = api_key if api_key else "$GAAP_API_KEY"

    existing_lang = compress_cfg.get("lang", "zh")
    print(f"\n{BOLD}压缩语言:{RESET}")
    print(f"  {CYAN}1{RESET}. 中文 (zh)")
    print(f"  {CYAN}2{RESET}. English (en)")
    default_lang = "2" if existing_lang == "en" else "1"
    lang_choice = get_input("\n选择", default_lang)
    lang = "en" if lang_choice == "2" else "zh"

    config = {
        "message_format": "compressed",
        "compress": {
            "base_url": base_url,
            "model": model,
            "api_key": api_key_ref,
            "lang": lang
        }
    }
    save_config(config)

    print(f"\n{GREEN}✓ 压缩配置已保存{RESET}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(f"  Language: {'中文' if lang == 'zh' else 'English'}")
    return True


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def show_summary():
    print_step(3, 3, "配置完成!")

    print(f"""
{GREEN}╔══════════════════════════════════════════════════════════╗
║  ✓ GAAP 配置成功!                                        ║
╚══════════════════════════════════════════════════════════╝{RESET}

{BOLD}配置文件:{RESET}
  • {CYAN}.env{RESET} - FEISHU_WEBHOOK_URL, GAAP_API_KEY
  • {CYAN}.claude/gaap.json{RESET} - 压缩设置

{YELLOW}提示: .env 通常已在 .gitignore 中{RESET}

{BOLD}测试通知:{RESET}
  重启 Claude Code，然后让 Claude 问你一个问题。

{BOLD}修改配置:{RESET}
  再次运行 /gaap:setup 或直接编辑配置文件。
""")


def main():
    clear_screen()
    print_header()

    if not setup_webhook():
        sys.exit(1)

    print()
    setup_compression()

    print()
    show_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}已取消{RESET}")
        sys.exit(0)
