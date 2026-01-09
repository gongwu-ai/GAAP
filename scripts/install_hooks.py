#!/usr/bin/env python3
"""
GAAP - Install hooks to project .claude/settings.json
Workaround for Claude Code bug: plugin hooks don't execute
"""

import json
import os
import sys

# Find plugin root
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.getcwd()
SETTINGS_PATH = os.path.join(PROJECT_DIR, ".claude/settings.json")

HOOKS_CONFIG = {
    "hooks": {
        "PermissionRequest": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{PLUGIN_ROOT}/scripts/permission_notify.sh",
                        "timeout": 10
                    }
                ]
            }
        ],
        "Notification": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{PLUGIN_ROOT}/scripts/notify.sh",
                        "timeout": 10
                    }
                ]
            }
        ],
        "Stop": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"{PLUGIN_ROOT}/scripts/notify.sh",
                        "timeout": 10
                    }
                ]
            }
        ]
    }
}


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=2)


def main():
    print(f"Project dir: {PROJECT_DIR}")
    print(f"Plugin root: {PLUGIN_ROOT}")

    settings = load_settings()

    # Merge hooks
    if "hooks" not in settings:
        settings["hooks"] = {}

    for hook_name, hook_config in HOOKS_CONFIG["hooks"].items():
        if hook_name not in settings["hooks"]:
            settings["hooks"][hook_name] = []
        settings["hooks"][hook_name].extend(hook_config)

    save_settings(settings)
    print(f"✓ Hooks installed to: {SETTINGS_PATH}")
    print("\nInstalled hooks:")
    for hook in HOOKS_CONFIG["hooks"].keys():
        print(f"  - {hook}")


if __name__ == "__main__":
    main()
