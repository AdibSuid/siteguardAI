#!/usr/bin/env python3
"""
Telegram Bot Setup Script
Helps configure Telegram bot token and channel ID for SiteGuard AI.
"""

import os
import yaml
from pathlib import Path


def setup_telegram_config():
    """Interactive setup for Telegram configuration."""

    print("🤖 SiteGuard AI - Telegram Bot Setup")
    print("=" * 40)

    # Check if config.yaml exists
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found!")
        return

    # Load current config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print("\n📱 Telegram Bot Configuration")
    print("Follow these steps to set up Telegram notifications:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot and follow the instructions")
    print("3. Copy the bot token you receive")
    print("4. Create a channel or group for notifications")
    print("5. Add your bot as an administrator to the channel/group")
    print("6. Get the channel/group ID (see README for details)")

    # Get bot token
    current_token = config.get('telegram', {}).get('bot_token', '')
    if current_token and current_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print(f"\nCurrent bot token: {current_token[:10]}...{current_token[-5:]}")
        change_token = input("Change bot token? (y/N): ").lower().strip()
        if change_token != 'y':
            bot_token = current_token
        else:
            bot_token = input("Enter your Telegram bot token: ").strip()
    else:
        bot_token = input("Enter your Telegram bot token: ").strip()

    # Get channel ID
    current_channel = config.get('telegram', {}).get('channel_id', '')
    if current_channel and current_channel != "YOUR_TELEGRAM_CHANNEL_ID_HERE":
        print(f"\nCurrent channel ID: {current_channel}")
        change_channel = input("Change channel ID? (y/N): ").lower().strip()
        if change_channel != 'y':
            channel_id = current_channel
        else:
            channel_id = input("Enter your Telegram channel/group ID: ").strip()
    else:
        channel_id = input("Enter your Telegram channel/group ID: ").strip()

    # Validate inputs
    if not bot_token or not channel_id:
        print("❌ Both bot token and channel ID are required!")
        return

    # Update config
    if 'telegram' not in config:
        config['telegram'] = {}

    config['telegram']['bot_token'] = bot_token
    config['telegram']['channel_id'] = channel_id
    config['telegram']['enabled'] = True

    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("\n✅ Telegram configuration updated successfully!")
    print(f"Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"Channel ID: {channel_id}")
    print("Enabled: True")

    # Test connection
    print("\n🧪 Testing Telegram connection...")
    try:
        import requests

        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Bot connected successfully: @{bot_info['result']['username']}")
            else:
                print("❌ Bot token is invalid")
        else:
            print("❌ Failed to connect to Telegram API")

    except Exception as e:
        print(f"❌ Connection test failed: {e}")

    print("\n📋 Next steps:")
    print("1. Make sure your bot is added as an administrator to your channel/group")
    print("2. Run the SiteGuard AI application")
    print("3. Telegram notifications will be automatically enabled")


if __name__ == "__main__":
    setup_telegram_config()