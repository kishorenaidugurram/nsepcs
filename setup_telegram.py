#!/usr/bin/env python3
"""
Interactive Setup Wizard for Telegram Integration
"""

import os
import sys
import requests
import json
from pathlib import Path

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    print("\n" + "=" * 60)
    print("  NSE F&O PCS SCANNER - TELEGRAM SETUP WIZARD")
    print("=" * 60 + "\n")

def print_step(num, title):
    print(f"\n{'='*60}")
    print(f"STEP {num}: {title}")
    print('='*60)

def get_input(prompt, default=""):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("❌ Cannot be empty!")

def test_telegram_connection(token, chat_id):
    """Test Telegram API connection"""
    print("\n🧪 Testing Telegram connection...")

    try:
        # Test 1: Verify token
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            print(f"❌ Invalid token: {response.text}")
            return False

        bot_info = response.json()
        if not bot_info.get('ok'):
            print(f"❌ Invalid response: {bot_info}")
            return False

        bot_name = bot_info['result']['first_name']
        print(f"✅ Bot verified: @{bot_info['result']['username']} ({bot_name})")

        # Test 2: Send test message
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': '✅ *NSE PCS Scanner Connected!*\n\nYour Telegram integration is working correctly. You will receive scan results here.'
        }

        response = requests.post(send_url, json=payload, timeout=5)

        if response.status_code == 200:
            print(f"✅ Test message sent to chat ID: {chat_id}")
            return True
        else:
            error = response.json()
            print(f"❌ Could not send message: {error.get('description', 'Unknown error')}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Connection timeout - check internet connection")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_env_file(token, chat_id):
    """Create .env file"""
    env_content = f"""# NSE F&O PCS Scanner - Telegram Configuration
# Generated: {__import__('datetime').datetime.now()}

TELEGRAM_BOT_TOKEN={token}
TELEGRAM_CHAT_ID={chat_id}

# Scanner Configuration
MIN_VOLUME_RATIO=0.8
MIN_MOMENTUM=40
MAX_VOLATILITY=50
PRICE_ABOVE_SMA20=true
"""

    env_path = Path('.env')
    env_path.write_text(env_content)
    print(f"\n✅ Configuration saved to: .env")
    return env_path

def create_bash_script(token, chat_id):
    """Create bash script for easy running"""
    script_content = f"""#!/bin/bash
# NSE F&O PCS Scanner - Automated Run Script
# Generated: {__import__('datetime').datetime.now()}

export TELEGRAM_BOT_TOKEN="{token}"
export TELEGRAM_CHAT_ID="{chat_id}"

python3 run_scanner.py
"""

    script_path = Path('run_scan.sh')
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    print(f"✅ Bash script created: run_scan.sh")
    return script_path

def show_configuration(token, chat_id):
    """Display final configuration"""
    print("\n" + "=" * 60)
    print("FINAL CONFIGURATION")
    print("=" * 60)
    print(f"\n📱 Telegram Bot Token: {token[:20]}...{token[-5:]}")
    print(f"💬 Chat ID: {chat_id}")
    print("\n✅ Configuration looks good!")

def show_next_steps():
    """Show next steps"""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    steps = [
        "1. Run your first scan:",
        "   python3 run_scanner.py",
        "",
        "2. Or use the bash script:",
        "   ./run_scan.sh",
        "",
        "3. To schedule automated scanning (Linux/Mac):",
        "   crontab -e",
        "   Add: 30 9 * * 1-5 /path/to/run_scan.sh",
        "",
        "4. Customize filters in run_scanner.py",
        "",
        "5. See TELEGRAM_SETUP.md for full documentation"
    ]

    for step in steps:
        print(step)

def main():
    clear_screen()
    print_header()

    print("""
Welcome to the NSE F&O PCS Scanner Setup Wizard!

This wizard will help you:
✅ Get your Telegram Bot Token
✅ Find your Chat ID
✅ Test the connection
✅ Create configuration files

Let's get started!
    """)

    input("Press Enter to continue...")

    # Step 1: Bot Token
    print_step(1, "Telegram Bot Token")
    print("""
To get your bot token:
1. Open Telegram and search for @BotFather
2. Send /start then /newbot
3. Give your bot a name (e.g., "PCS Scanner Bot")
4. Give it a username (e.g., "pcs_scanner_bot")
5. Copy the API Token (looks like: 123456:ABC-DEF...)
    """)

    token = get_input("Enter your Bot Token")

    # Step 2: Chat ID
    print_step(2, "Your Chat ID")
    print("""
To get your Chat ID:
Method 1: Search for @userinfobot in Telegram, send /start
Method 2: Use curl to get it from getUpdates
Method 3: Look at the test message you'll receive

Chat ID is a number, e.g., 123456789
    """)

    chat_id = get_input("Enter your Chat ID")

    # Step 3: Test Connection
    print_step(3, "Test Connection")
    print("""
Now let's test if everything works...
    """)

    if test_telegram_connection(token, chat_id):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed. Please check:")
        print("   • Bot token is correct")
        print("   • Chat ID is correct")
        print("   • You have internet connection")
        print("   • Telegram API is accessible")

        retry = input("\nRetry? (y/n): ").lower().strip()
        if retry == 'y':
            main()
            return
        else:
            print("\n⚠️  Skipping configuration save...")
            return

    # Step 4: Save Configuration
    print_step(4, "Save Configuration")
    print("""
Creating configuration files...
    """)

    create_env_file(token, chat_id)
    create_bash_script(token, chat_id)

    # Step 5: Display Results
    print_step(5, "Configuration Complete")
    show_configuration(token, chat_id)

    # Show Next Steps
    show_next_steps()

    print("\n" + "=" * 60 + "\n")
    print("✅ Setup complete! You can now run your scanner.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        sys.exit(1)
