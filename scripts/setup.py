#!/usr/bin/env python3
"""
GAAP Setup - Interactive configuration wizard
"""

import os
import sys
import json

CONFIG_DIR = os.path.expanduser("~/.claude")
CONFIG_PATH = os.path.join(CONFIG_DIR, "gaap.json")
WEBHOOK_PATH = os.path.join(CONFIG_DIR, "feishu-webhook-url")

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


def setup_webhook():
    print_step(1, 3, "配置飞书 Webhook")

    print(f"""
{YELLOW}如何获取 Webhook URL:{RESET}
1. 打开飞书群聊
2. 点击右上角 ... → 设置 → 群机器人
3. 添加自定义机器人
4. 复制 Webhook 地址
""")

    current = ""
    if os.path.exists(WEBHOOK_PATH):
        with open(WEBHOOK_PATH) as f:
            current = f.read().strip()
        print(f"当前配置: {GREEN}{current[:50]}...{RESET}\n")

    webhook = get_input("Webhook URL", current if current else None)

    if webhook and webhook.startswith("http"):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(WEBHOOK_PATH, 'w') as f:
            f.write(webhook)
        os.chmod(WEBHOOK_PATH, 0o600)
        print(f"\n{GREEN}✓ Webhook 已保存{RESET}")
        return True
    else:
        print(f"\n{RED}✗ 无效的 URL{RESET}")
        return False


def setup_compression():
    print_step(2, 3, "配置消息压缩 (可选)")

    print(f"""
{YELLOW}消息压缩功能:{RESET}
飞书不渲染 Markdown，使用 LLM 将消息压缩成口语化格式。
压缩失败会自动回退到全量发送。

{YELLOW}支持的 API 格式:{RESET}
• OpenAI 兼容格式 (DeepSeek, GLM, Ollama, vLLM 等)
• Anthropic 格式 (base_url 包含 "anthropic")
""")

    choice = get_input("启用消息压缩? (y/N)", "n").lower()

    if choice != 'y':
        config = {"message_format": "full"}
        save_config(config)
        print(f"\n{GREEN}✓ 将发送全量消息{RESET}")
        return True

    # Get custom endpoint configuration
    print(f"\n{BOLD}配置 LLM Endpoint:{RESET}\n")

    base_url = get_input("Base URL (如 https://api.deepseek.com)")
    model = get_input("Model 名称 (如 deepseek-chat)")

    print(f"\n{YELLOW}API Key 支持环境变量格式，如 $DEEPSEEK_API_KEY{RESET}")
    api_key = get_input("API Key (无需则留空)", "")

    # Save config
    config = {
        "message_format": "compressed",
        "compress": {
            "base_url": base_url,
            "model": model,
            "api_key": api_key
        }
    }
    save_config(config)

    print(f"\n{GREEN}✓ 压缩配置已保存{RESET}")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    return True


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    os.chmod(CONFIG_PATH, 0o600)


def show_summary():
    print_step(3, 3, "配置完成!")

    print(f"""
{GREEN}╔══════════════════════════════════════════════════════════╗
║  ✓ GAAP 配置成功!                                        ║
╚══════════════════════════════════════════════════════════╝{RESET}

{BOLD}配置文件:{RESET}
  • Webhook: {CYAN}~/.claude/feishu-webhook-url{RESET}
  • 设置:    {CYAN}~/.claude/gaap.json{RESET}

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
