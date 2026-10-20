#!/usr/bin/env python3
"""
NSE Stock Screener Demo - Using sample data to demonstrate functionality
"""

import os
import json
import requests
from datetime import datetime

# Sample stocks that meet screening criteria
SAMPLE_RESULTS = [
    {'symbol': 'RELIANCE', 'price': 2945.50, 'rsi': 65.2, 'adx': 28.5, 'ema_20': 2920.30},
    {'symbol': 'TCS', 'price': 3850.25, 'rsi': 58.9, 'adx': 25.3, 'ema_20': 3800.15},
    {'symbol': 'HDFCBANK', 'price': 1820.75, 'rsi': 62.4, 'adx': 27.8, 'ema_20': 1795.40},
    {'symbol': 'INFY', 'price': 2420.50, 'rsi': 55.6, 'adx': 23.2, 'ema_20': 2395.70},
    {'symbol': 'ICICIBANK', 'price': 1285.30, 'rsi': 68.1, 'adx': 30.5, 'ema_20': 1250.80},
    {'symbol': 'SBIN', 'price': 820.45, 'rsi': 61.3, 'adx': 26.7, 'ema_20': 805.20},
    {'symbol': 'LT', 'price': 3250.75, 'rsi': 59.2, 'adx': 24.1, 'ema_20': 3220.30},
    {'symbol': 'MARUTI', 'price': 11850.25, 'rsi': 63.8, 'adx': 29.2, 'ema_20': 11800.50},
]

def format_telegram_message(stocks):
    """Format message for Telegram"""

    msg = f"🎯 *NSE SCREENER - {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    msg += f"✅ Found: {len(stocks)} stocks\n"
    msg += f"📊 Filters: RSI 30-75 | ADX≥20 | Price≥EMA20\n\n"

    for i, stock in enumerate(stocks, 1):
        msg += f"{i}. *{stock['symbol']}*\n"
        msg += f"   Price: ₹{stock['price']:.2f}\n"
        msg += f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
        msg += f"   EMA20: ₹{stock['ema_20']:.2f}\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📈 Professional stock screening results\n"
    msg += "🔗 For detailed analysis, visit the app"

    return msg

def send_telegram(message):
    """Send message to Telegram"""

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not configured!")
        print("\nTo set up Telegram:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Run this in your browser to get chat_id:")
        print("   https://api.telegram.org/bot<BOT_TOKEN>/getUpdates")
        print("\n3. Set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nMessage to send:")
        print("=" * 70)
        print(message)
        print("=" * 70)
        return False

    try:
        print("📤 Sending to Telegram...")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""

    print(f"🎯 NSE Stock Screener Demo")
    print(f"📊 Demo Mode (Sample Data)")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Sort by RSI
    stocks = sorted(SAMPLE_RESULTS, key=lambda x: x['rsi'], reverse=True)

    print("QUALIFIED STOCKS (Demo Data):")
    print("=" * 80)
    print(f"{'#':<3} {'Symbol':<12} {'Price':<10} {'RSI':<8} {'ADX':<8} {'EMA20':<10}")
    print("=" * 80)

    for i, stock in enumerate(stocks, 1):
        print(f"{i:<3} {stock['symbol']:<12} ₹{stock['price']:<9.2f} {stock['rsi']:<7.1f}  "
              f"{stock['adx']:<7.1f}  ₹{stock['ema_20']:<9.2f}")

    print("=" * 80)
    print()

    # Format and send message
    message = format_telegram_message(stocks)
    print("Message Preview:")
    print("-" * 70)
    print(message)
    print("-" * 70)
    print()

    # Try to send
    send_telegram(message)

    # Save results
    output_file = f"demo_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w') as f:
        json.dump(stocks, f, indent=2)

    print(f"\n📄 Demo results saved: {output_file}")

if __name__ == "__main__":
    main()
