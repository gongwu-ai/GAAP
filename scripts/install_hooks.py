#!/usr/bin/env python3
"""
GAAP - Install hooks to project .claude/settings.json
Workaround for Claude Code bug: plugin hooks don't execute
"""

import json
import os

# Find plugin root
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.getcwd()
SETTINGS_PATH = os.path.join(PROJECT_DIR, ".claude/settings.json")

HOOKS_CONFIG = {
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


def is_gaap_hook(hook_entry):
    """Check if a hook entry is from GAAP"""
    for h in hook_entry.get("hooks", []):
        cmd = h.get("command", "")
        if "gaap" in cmd.lower() or "notify.sh" in cmd or "permission_notify.sh" in cmd:
            return True
    return False


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

    # Initialize hooks if not present
    if "hooks" not in settings:
        settings["hooks"] = {}

    # Remove old GAAP hooks first (prevent duplicates)
    for hook_name in HOOKS_CONFIG.keys():
        if hook_name in settings["hooks"]:
            # Filter out existing GAAP hooks
            settings["hooks"][hook_name] = [
                h for h in settings["hooks"][hook_name]
                if not is_gaap_hook(h)
            ]

    # Add new GAAP hooks
    for hook_name, hook_config in HOOKS_CONFIG.items():
        if hook_name not in settings["hooks"]:
            settings["hooks"][hook_name] = []
        settings["hooks"][hook_name].extend(hook_config)

    # Ensure plugin is enabled
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}
    settings["enabledPlugins"]["gaap@gaap"] = True

    save_settings(settings)
    print(f"✓ Hooks installed to: {SETTINGS_PATH}")
    print("\nInstalled hooks:")
    for hook in HOOKS_CONFIG.keys():
        print(f"  - {hook}")


if __name__ == "__main__":
    main()
