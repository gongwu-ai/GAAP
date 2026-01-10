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


def setup_llm_mode():
    print_step(2, 3, "配置 LLM 模式")

    existing = load_config()
    current_mode = existing.get("llm_mode", "none")
    compress_cfg = existing.get("compress", {})

    print(f"""
{YELLOW}LLM 模式选择:{RESET}

  {CYAN}1{RESET}. {BOLD}none{RESET} - 仅规则过滤 + 纯文本
     无需 LLM，使用正则检测是否需要输入，直接发送原始消息。
     {GREEN}(免费，无 API 调用){RESET}

  {CYAN}2{RESET}. {BOLD}smart{RESET} - 规则过滤 + LLM 压缩
     先用规则判断是否需要通知，再用 LLM 压缩消息。
     {YELLOW}(节省 tokens，仅在需要时调用 API){RESET}

  {CYAN}3{RESET}. {BOLD}compress_all{RESET} - 全量 LLM 压缩
     每次停止都用 LLM 压缩消息并发送。
     {RED}(成本较高，但信息最完整){RESET}
""")

    # Determine default based on current config
    mode_map = {"none": "1", "smart": "2", "compress_all": "3"}
    default_choice = mode_map.get(current_mode, "1")

    choice = get_input("选择模式", default_choice)

    if choice == "1":
        config = {"llm_mode": "none"}
        save_config(config)
        print(f"\n{GREEN}✓ 已设置为 none 模式 (规则过滤 + 纯文本){RESET}")
        return True

    # For smart and compress_all, need LLM config
    llm_mode = "smart" if choice == "2" else "compress_all"

    print(f"\n{BOLD}配置 Anthropic 兼容 API:{RESET}")
    print(f"{YELLOW}GAAP 只支持 Anthropic 协议，SDK 会自动处理路径{RESET}")
    print(f"  Anthropic: https://api.anthropic.com")
    print(f"  GLM: https://open.bigmodel.cn/api/anthropic")
    print(f"  其他兼容服务: 填写其 Anthropic 兼容端点\n")

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
        "llm_mode": llm_mode,
        "compress": {
            "base_url": base_url,
            "model": model,
            "api_key": api_key_ref,
            "lang": lang
        }
    }
    save_config(config)

    mode_desc = "规则过滤 + LLM 压缩" if llm_mode == "smart" else "全量 LLM 压缩"
    print(f"\n{GREEN}✓ 已设置为 {llm_mode} 模式 ({mode_desc}){RESET}")
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

    # Load and display current config
    config = load_config()
    llm_mode = config.get("llm_mode", "none")
    mode_desc = {
        "none": "规则过滤 + 纯文本",
        "smart": "规则过滤 + LLM 压缩",
        "compress_all": "全量 LLM 压缩"
    }.get(llm_mode, "未知")

    print(f"""
{GREEN}╔══════════════════════════════════════════════════════════╗
║  ✓ GAAP 配置成功!                                        ║
╚══════════════════════════════════════════════════════════╝{RESET}

{BOLD}当前 LLM 模式:{RESET} {CYAN}{llm_mode}{RESET} ({mode_desc})

{BOLD}配置文件:{RESET}
  • {CYAN}.env{RESET} - FEISHU_WEBHOOK_URL, GAAP_API_KEY
  • {CYAN}.claude/gaap.json{RESET} - LLM 模式设置

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
    setup_llm_mode()

    print()
    show_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}已取消{RESET}")
        sys.exit(0)
