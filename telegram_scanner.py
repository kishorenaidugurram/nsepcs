#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Integration for Automated Results Sharing
"""

import os
import requests
import json
from datetime import datetime
import pytz

def get_telegram_config():
    """Get Telegram configuration from environment"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    return {
        'token': token,
        'chat_id': chat_id,
        'configured': token is not None and chat_id is not None
    }

def send_telegram_message(message, token=None, chat_id=None):
    """Send message to Telegram"""
    if token is None:
        config = get_telegram_config()
        token = config['token']
        chat_id = config['chat_id']

    if not token or not chat_id:
        print("⚠️  ERROR: Telegram not configured!")
        print("   Please set environment variables:")
        print("   - TELEGRAM_BOT_TOKEN: Your bot token from @BotFather")
        print("   - TELEGRAM_CHAT_ID: Your chat ID (can be found by messaging @userinfobot)")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)

        if response.status_code == 200:
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def send_scan_results(stocks_list, scan_timestamp=None):
    """Send scan results to Telegram"""
    if not stocks_list:
        message = "📊 <b>NSE F&O PCS Scanner</b>\n❌ No stocks found matching the filter criteria today."
        send_telegram_message(message)
        return

    if scan_timestamp is None:
        ist = pytz.timezone('Asia/Kolkata')
        scan_timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

    # Build message
    message = f"""<b>📊 NSE F&O PCS Scanner Results</b>
<i>{scan_timestamp}</i>

<b>✅ Found {len(stocks_list)} stocks matching criteria:</b>
"""

    # Sort by strength if available
    if stocks_list and isinstance(stocks_list[0], dict) and 'strength' in stocks_list[0]:
        stocks_list = sorted(stocks_list, key=lambda x: x.get('strength', 0), reverse=True)

    # Add stocks (limit to 20 to avoid message size limits)
    for i, stock in enumerate(stocks_list[:20], 1):
        if isinstance(stock, dict):
            symbol = stock.get('symbol', 'N/A')
            pattern = stock.get('pattern', 'Unknown')
            strength = stock.get('strength', 0)
            price = stock.get('current_price', 0)
            rsi = stock.get('rsi', 0)

            message += f"\n<b>{i}. {symbol}</b> - {pattern}"
            if strength > 0:
                message += f" ({strength:.0f}%)"
            if price > 0:
                message += f"\n   Price: ₹{price:.2f}"
            if rsi > 0:
                message += f" | RSI: {rsi:.1f}"
        else:
            # Simple string format
            message += f"\n{i}. <code>{stock}</code>"

    if len(stocks_list) > 20:
        message += f"\n\n... and <b>{len(stocks_list) - 20} more stocks</b>"

    message += "\n\n<i>🔗 Check the Streamlit app for detailed analysis and charts</i>"

    return send_telegram_message(message)

def test_telegram_connection():
    """Test Telegram connection"""
    print("\n🔧 Testing Telegram Configuration...")
    print("=" * 60)

    config = get_telegram_config()

    if not config['configured']:
        print("❌ Telegram not configured!")
        print("\nTo set up Telegram notifications:")
        print("1. Create a bot via @BotFather on Telegram")
        print("2. Get your chat ID by messaging @userinfobot")
        print("3. Set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id_here'")
        print("\nOr add to ~/.bashrc or set in your scheduled task configuration")
        return False

    print("✅ Telegram credentials found!")
    print(f"   Bot Token: {config['token'][:20]}...")
    print(f"   Chat ID: {config['chat_id']}")

    # Send test message
    print("\nSending test message...")
    test_msg = """<b>NSE PCS Scanner - Telegram Connection Test</b>
✅ Telegram integration is working!
Test sent at: """ + datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')

    if send_telegram_message(test_msg, config['token'], config['chat_id']):
        print("✅ Test message sent successfully!")
        return True
    else:
        print("❌ Failed to send test message")
        return False

def setup_example_results():
    """Return example results for testing"""
    return [
        {
            'symbol': 'RELIANCE',
            'pattern': 'Cup with Handle',
            'strength': 85.5,
            'current_price': 3245.50,
            'rsi': 62.3,
            'adx': 28.5
        },
        {
            'symbol': 'TCS',
            'pattern': 'Flat Base Breakout',
            'strength': 78.2,
            'current_price': 4128.75,
            'rsi': 58.9,
            'adx': 25.1
        },
        {
            'symbol': 'HDFCBANK',
            'pattern': 'Double Bottom',
            'strength': 72.1,
            'current_price': 1856.40,
            'rsi': 55.6,
            'adx': 22.3
        },
    ]

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            # Test Telegram connection
            test_telegram_connection()
        elif sys.argv[1] == 'demo':
            # Send demo results
            print("\n📤 Sending demo scan results to Telegram...")
            demo_stocks = setup_example_results()
            if send_scan_results(demo_stocks):
                print("✅ Demo results sent!")
            else:
                print("❌ Failed to send demo results")
        elif sys.argv[1] == 'config':
            # Show configuration status
            config = get_telegram_config()
            print("\n📋 Telegram Configuration Status")
            print("=" * 60)
            if config['configured']:
                print(f"✅ Configured")
                print(f"   Token: {config['token'][:20]}...")
                print(f"   Chat ID: {config['chat_id']}")
            else:
                print("❌ Not configured")
                if not config['token']:
                    print("   Missing: TELEGRAM_BOT_TOKEN")
                if not config['chat_id']:
                    print("   Missing: TELEGRAM_CHAT_ID")
    else:
        # Default: show usage
        print("\n📱 NSE F&O PCS Scanner - Telegram Integration")
        print("=" * 60)
        print("\nUsage:")
        print("  python telegram_scanner.py test    - Test Telegram connection")
        print("  python telegram_scanner.py config  - Show configuration status")
        print("  python telegram_scanner.py demo    - Send demo results")
        print("\nOr import in your code:")
        print("  from telegram_scanner import send_scan_results")
        print("\nSetup Telegram (one-time):")
        print("  1. Create bot via @BotFather")
        print("  2. Get chat ID via @userinfobot")
        print("  3. Set environment variables:")
        print("     export TELEGRAM_BOT_TOKEN='token'")
        print("     export TELEGRAM_CHAT_ID='chat_id'")
        print("\n" + "=" * 60)

        # Auto-test if configured
        config = get_telegram_config()
        if config['configured']:
            print("\n🔧 Telegram is configured. Run with 'test' to verify.")
        else:
            print("\n⚠️  Telegram not configured yet.")
