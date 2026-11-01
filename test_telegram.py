#!/usr/bin/env python3
"""
Test Telegram integration without needing market data
"""

import os
import requests
from datetime import datetime
import pytz

def test_telegram_connection(token, chat_id):
    """Test if Telegram credentials are valid"""
    print("\n🧪 Testing Telegram Connection...\n")

    if not token or not chat_id:
        print("❌ Missing credentials!")
        print("   - TELEGRAM_BOT_TOKEN:", "SET" if token else "NOT SET")
        print("   - TELEGRAM_CHAT_ID:", "SET" if chat_id else "NOT SET")
        return False

    try:
        # Test message
        message = """✅ *Telegram Integration Test*

🎯 NSE F&O PCS Scanner
⏰ Test sent at: """ + datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST') + """

This is a test message to verify your Telegram bot is working correctly!

*Sample Results Format:*
1. RELIANCE - Breakout (₹2850.50)
2. INFY - MA Bullish (₹2120.25)
3. TCS - Support Test (₹3850.00)
"""

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        print(f"📤 Sending test message to Telegram...")
        print(f"   Bot Token: {token[:20]}...")
        print(f"   Chat ID: {chat_id}\n")

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ SUCCESS! Telegram connection is working!")
            print("   Message delivered successfully.")
            print("\n📍 You should see the test message in your Telegram chat.")
            print("   Scanner will send results to this same chat.\n")
            return True
        else:
            print(f"❌ FAILED! Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   - Check your internet connection")
        print("   - Check proxy settings if applicable")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🤖 NSE F&O Scanner - Telegram Integration Tester")
    print("="*60)

    # Get credentials from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

    # If not set, ask for input
    if not token:
        print("\n⚠️  TELEGRAM_BOT_TOKEN not found in environment")
        print("   Get it from @BotFather on Telegram")
        token = input("\n   Enter your bot token: ").strip()

    if not chat_id:
        print("\n⚠️  TELEGRAM_CHAT_ID not found in environment")
        print("   Get it from: https://api.telegram.org/bot<TOKEN>/getUpdates")
        chat_id = input("\n   Enter your chat ID: ").strip()

    # Test connection
    success = test_telegram_connection(token, chat_id)

    if success:
        print("\n💾 To save these credentials for future use:")
        print("   Add to your ~/.bashrc or ~/.zshrc:")
        print(f"\n   export TELEGRAM_BOT_TOKEN='{token}'")
        print(f"   export TELEGRAM_CHAT_ID='{chat_id}'")
        print("\n   Then run: source ~/.bashrc (or ~/.zshrc)\n")
        return 0
    else:
        print("\n❌ Connection failed. Please check your credentials:")
        print("   1. Verify bot token is correct")
        print("   2. Verify chat ID is correct")
        print("   3. Make sure bot is not blocked")
        print("   4. Check internet connection\n")
        return 1

if __name__ == '__main__':
    exit(main())
