#!/usr/bin/env python3
"""
Setup Telegram bot credentials for the scanner automation
"""

import os
import json

def setup_telegram_credentials():
    """Setup Telegram bot token and chat ID"""

    print("=" * 60)
    print("NSE F&O PCS Scanner - Telegram Setup")
    print("=" * 60)
    print()

    print("To use this scanner with Telegram, you need:")
    print("1. A Telegram Bot Token from BotFather")
    print("2. Your Telegram Chat ID (where messages will be sent)")
    print()

    print("Steps to get these:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Use /newbot to create a new bot")
    print("3. Copy the bot token provided")
    print()
    print("To get your Chat ID:")
    print("1. Search for @userinfobot in Telegram")
    print("2. Start the bot and it will show your chat ID")
    print()

    config_file = os.path.expanduser("~/.nsepcs_telegram.json")

    # Check if config already exists
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            existing = json.load(f)
        print(f"Existing configuration found at {config_file}")
        print(f"Bot Token: {existing.get('token', 'NOT SET')[:20]}...")
        print(f"Chat ID: {existing.get('chat_id', 'NOT SET')}")
        update = input("\nDo you want to update it? (y/n): ").strip().lower()
        if update != 'y':
            return

    token = input("\nEnter your Telegram Bot Token: ").strip()
    if not token:
        print("Error: Bot token is required")
        return

    chat_id = input("Enter your Telegram Chat ID: ").strip()
    if not chat_id:
        print("Error: Chat ID is required")
        return

    # Save configuration
    config = {
        'token': token,
        'chat_id': chat_id,
        'created': str(__import__('datetime').datetime.now())
    }

    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    os.chmod(config_file, 0o600)  # Restrict permissions for security

    print(f"\n✓ Configuration saved to {config_file}")
    print("\nTo use this in your scheduler, add these environment variables:")
    print(f"export TELEGRAM_BOT_TOKEN='{token[:20]}...'")
    print(f"export TELEGRAM_CHAT_ID='{chat_id}'")
    print("\nOr set them in your cron job or task scheduler.")

if __name__ == "__main__":
    setup_telegram_credentials()
