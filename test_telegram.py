#!/usr/bin/env python3
"""
Test Telegram Bot Connection
Verifies that Telegram credentials are properly configured
"""

import os
import requests
import sys
from datetime import datetime
import pytz

def test_telegram_setup():
    """Test Telegram bot configuration"""

    print("=" * 60)
    print("🤖 TELEGRAM BOT CONFIGURATION TEST")
    print("=" * 60)
    print()

    # Check environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not set")
        print("\nSet it with:")
        print('   export TELEGRAM_BOT_TOKEN="your_bot_token"')
        return False

    if not chat_id:
        print("❌ ERROR: TELEGRAM_CHAT_ID not set")
        print("\nSet it with:")
        print('   export TELEGRAM_CHAT_ID="your_chat_id"')
        return False

    print(f"✅ Bot Token found: {bot_token[:20]}...")
    print(f"✅ Chat ID found: {chat_id}")
    print()

    # Test bot connectivity
    print("🔍 Testing bot connectivity...")
    try:
        api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                bot_name = bot_info['result']['first_name']
                bot_username = bot_info['result']['username']
                print(f"✅ Bot is valid!")
                print(f"   Bot Name: {bot_name}")
                print(f"   Bot Username: @{bot_username}")
            else:
                print(f"❌ Bot token is invalid")
                print(f"   Error: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

    print()

    # Test sending message
    print("🔍 Testing message sending...")
    try:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

        test_message = f"""
<b>✅ Telegram Setup Verified!</b>

<b>Test Sent At:</b> {timestamp}
<b>Bot Connection:</b> ✅ Working
<b>Status:</b> Ready to receive stock scanner alerts

Your stock scanner is now configured to send:
• Daily scan results
• Filtered stock lists
• Technical analysis
• News updates
"""

        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }

        response = requests.post(api_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            print(f"   Check your Telegram chat for the test message")
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("You can now run the stock scanner:")
    print("   python3 /home/user/nsepcs/telegram_scanner.py")
    print()

    return True


if __name__ == "__main__":
    success = test_telegram_setup()
    sys.exit(0 if success else 1)
