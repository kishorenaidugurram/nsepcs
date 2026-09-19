#!/usr/bin/env python3
"""
Test Telegram Bot Configuration
Verifies that Telegram bot token and chat ID are correctly configured
"""

import os
import requests
import sys
from datetime import datetime
import pytz

def test_telegram_setup():
    """Test Telegram configuration"""

    print("=" * 70)
    print("TELEGRAM CONFIGURATION TEST")
    print("=" * 70)
    print()

    # Check environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    print("📋 Environment Variables Status")
    print("-" * 70)

    if telegram_token:
        # Mask token for security
        masked_token = telegram_token[:10] + "..." + telegram_token[-5:]
        print(f"✅ TELEGRAM_BOT_TOKEN: {masked_token}")
    else:
        print("❌ TELEGRAM_BOT_TOKEN: NOT SET")

    if telegram_chat_id:
        print(f"✅ TELEGRAM_CHAT_ID: {telegram_chat_id}")
    else:
        print("❌ TELEGRAM_CHAT_ID: NOT SET")

    print()

    # Check if credentials are available
    if not telegram_token or not telegram_chat_id:
        print("⚠️  Missing Telegram Credentials")
        print("-" * 70)
        print("""
To configure Telegram:

1. Create a Telegram Bot:
   - Open Telegram and find @BotFather
   - Send /newbot
   - Follow the prompts
   - Save the bot token (e.g., 123456789:ABCDefGhIjKlMnOpQrStUvWxYz)

2. Get your Chat ID:
   - Start the bot by sending it a message
   - Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   - Look for "chat":{"id":...} in the response
   - Save this ID (e.g., 9876543210)

3. Set environment variables:
   export TELEGRAM_BOT_TOKEN="your_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"

4. Run this test again to verify
""")
        return False

    # Test bot token validity
    print("🔍 Testing Bot Token")
    print("-" * 70)

    url = f"https://api.telegram.org/bot{telegram_token}/getMe"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                bot_name = bot_info.get('first_name', 'Unknown')
                bot_id = bot_info.get('id', 'Unknown')

                print(f"✅ Bot Token Valid")
                print(f"   Bot Name: {bot_name}")
                print(f"   Bot ID: {bot_id}")
                print()

                # Test chat ID
                print("🔍 Testing Chat ID")
                print("-" * 70)

                ist = pytz.timezone('Asia/Kolkata')
                test_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

                test_message = f"""<b>✅ Telegram Test Successful</b>

<b>Configuration Status:</b>
✅ Bot Token: Valid
✅ Chat ID: Valid

<b>Test Details:</b>
🤖 Bot: {bot_name} (ID: {bot_id})
💬 Chat ID: {telegram_chat_id}
📅 Time: {test_time}
📍 Status: READY FOR SCANNING

<b>Next Steps:</b>
Run the scanner with:
<code>python3 scanner_telegram.py</code>

Scanner will automatically send results to this chat."""

                send_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                payload = {
                    "chat_id": telegram_chat_id,
                    "text": test_message,
                    "parse_mode": "HTML"
                }

                try:
                    send_response = requests.post(send_url, json=payload, timeout=10)

                    if send_response.status_code == 200:
                        send_data = send_response.json()
                        if send_data.get('ok'):
                            print(f"✅ Chat ID Valid: {telegram_chat_id}")
                            print(f"✅ Test message sent successfully!")
                            print()
                            print("=" * 70)
                            print("✅ ALL TESTS PASSED - TELEGRAM READY!")
                            print("=" * 70)
                            print()
                            print("You should receive a test message in your Telegram chat.")
                            print("The scanner is now ready to run!")
                            print()
                            print("Run the scanner with:")
                            print("  python3 scanner_telegram.py")
                            return True
                        else:
                            print(f"❌ Chat ID Invalid or Blocked")
                            error = send_data.get('description', 'Unknown error')
                            print(f"   Error: {error}")
                            print()
                            print("Possible causes:")
                            print("  - Chat ID is incorrect")
                            print("  - Bot hasn't been started in the chat")
                            print("  - Chat is blocked or archived")
                            return False
                    else:
                        print(f"❌ Failed to send message (Status: {send_response.status_code})")
                        print(f"   Response: {send_response.text}")
                        return False

                except requests.exceptions.Timeout:
                    print("❌ Timeout sending test message")
                    print("   Check your internet connection")
                    return False
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error sending test message: {e}")
                    return False
            else:
                print("❌ Bot Token Invalid")
                error = data.get('description', 'Unknown error')
                print(f"   Error: {error}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Connection Timeout")
        print("   Cannot reach Telegram API")
        print("   Check your internet connection")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print("   Cannot reach Telegram API")
        return False

if __name__ == "__main__":
    success = test_telegram_setup()
    sys.exit(0 if success else 1)
