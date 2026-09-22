#!/usr/bin/env python3
"""
Send status message to Telegram about scanner setup
"""
import os
import sys
import requests
import json
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not found!")
        print(f"   TELEGRAM_BOT_TOKEN: {'✓' if TELEGRAM_BOT_TOKEN else '✗'}")
        print(f"   TELEGRAM_CHAT_ID: {'✓' if TELEGRAM_CHAT_ID else '✗'}")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✓ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def main():
    # Check environment
    print("\n" + "="*60)
    print("NSE PCS Scanner - Status Check")
    print("="*60 + "\n")

    print("Checking environment...")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Telegram Bot Token: {'✓ Set' if TELEGRAM_BOT_TOKEN else '✗ Not Set'}")
    print(f"  Telegram Chat ID: {'✓ Set' if TELEGRAM_CHAT_ID else '✗ Not Set'}")

    # Build status message
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        # Setup needed
        message = f"""
🔧 <b>NSE PCS Scanner - Setup Required</b>

<b>⏰ Time:</b> {timestamp}

❌ <b>Status:</b> Scanner not configured

<b>⚠️ What's Missing:</b>
• TELEGRAM_BOT_TOKEN environment variable
• TELEGRAM_CHAT_ID environment variable

<b>📝 Setup Instructions:</b>

1. <b>Create a Telegram Bot:</b>
   - Chat with @BotFather on Telegram
   - Create a new bot
   - Copy the bot token

2. <b>Get Your Chat ID:</b>
   - Send a message to your bot
   - Visit: https://api.telegram.org/bot[TOKEN]/getUpdates
   - Find your chat_id in the response

3. <b>Set Environment Variables:</b>
   - Set TELEGRAM_BOT_TOKEN=[your_bot_token]
   - Set TELEGRAM_CHAT_ID=[your_chat_id]

4. <b>Install Dependencies:</b>
   - Run: pip install -r requirements.txt

5. <b>Run Scanner:</b>
   - Run: python run_scanner.py

<b>📚 Scanner Features:</b>
✓ Scans 208 NSE F&O stocks
✓ Detects 12+ chart patterns
✓ Validates with weekly timeframe
✓ Sends results via Telegram
✓ Tracks volume and technical indicators

<b>📊 Default Scan Settings:</b>
• RSI: 30-75
• ADX Min: 20
• Volume Ratio: 1.0x+
• Pattern Strength: 70%+

Need help? Check the README.md file.
"""
    else:
        # Ready to scan
        message = f"""
✅ <b>NSE PCS Scanner - Ready to Scan</b>

<b>⏰ Time:</b> {timestamp}

<b>✓ Status:</b> Scanner configured and ready

<b>📊 Scanner Configuration:</b>
• Telegram Bot: ✓ Connected
• Chat ID: ✓ Configured
• F&O Stocks: 208 available
• Scan Interval: Scheduled

<b>🚀 To Run Scanner:</b>
python run_scanner.py

<b>⚙️ Default Parameters:</b>
• RSI Range: 30-75
• ADX Minimum: 20
• Volume Ratio: 1.0x+
• Pattern Strength: 70%+
• Patterns: 12 types
• Weekly Validation: Enabled

<b>📈 Expected Results:</b>
High-probability bullish patterns
suitable for Put Credit Spreads (PCS)

Scanner will send results here!
"""

    print(f"\nMessage prepared ({len(message)} chars)")
    print("\nAttempting to send to Telegram...")

    success = send_telegram_message(message)

    print("\n" + "="*60)
    if success:
        print("✓ Status notification sent successfully!")
    else:
        print("❌ Failed to send notification")
        print("\nMessage content:")
        print(message)
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
