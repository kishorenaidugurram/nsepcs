#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Demo with Sample Data
Shows what the scanner output looks like
"""

import json
from datetime import datetime
import requests
import os


def send_to_telegram(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """Send message to Telegram"""
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found")
        print("   Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending to Telegram: {str(e)}")
        return False

def demo_scan():
    """Run demo scan with sample data"""
    print("📊 NSE F&O PCS Scanner - DEMO MODE")
    print("="*60)
    print("Note: Using sample data for demonstration purposes")
    print("="*60 + "\n")

    # Sample qualifying stocks
    stocks = [
        {
            'symbol': 'RELIANCE',
            'price': 3087.45,
            'rsi': 58.3,
            'adx': 22.8,
            'volume_ratio': 1.45,
            'strength': 78.5,
            'confidence': 'HIGH',
            'patterns': ['Current Day Breakout', 'EMA Alignment']
        },
        {
            'symbol': 'TCS',
            'price': 3652.10,
            'rsi': 52.1,
            'adx': 24.2,
            'volume_ratio': 1.32,
            'strength': 72.3,
            'confidence': 'MEDIUM',
            'patterns': ['Cup and Handle']
        },
        {
            'symbol': 'HDFCBANK',
            'price': 1658.75,
            'rsi': 55.6,
            'adx': 21.5,
            'volume_ratio': 1.28,
            'strength': 68.9,
            'confidence': 'MEDIUM',
            'patterns': ['Support Bounce']
        },
        {
            'symbol': 'INFY',
            'price': 2821.50,
            'rsi': 48.2,
            'adx': 23.1,
            'volume_ratio': 1.41,
            'strength': 75.2,
            'confidence': 'HIGH',
            'patterns': ['Breakout Pattern', 'Volume Surge']
        },
        {
            'symbol': 'ICICIBANK',
            'price': 1042.30,
            'rsi': 61.4,
            'adx': 20.9,
            'volume_ratio': 1.19,
            'strength': 65.7,
            'confidence': 'MEDIUM',
            'patterns': ['Trend Continuation']
        },
        {
            'symbol': 'BHARTIARTL',
            'price': 1389.60,
            'rsi': 54.8,
            'adx': 25.3,
            'volume_ratio': 1.55,
            'strength': 81.2,
            'confidence': 'HIGH',
            'patterns': ['Current Day Breakout', 'Volume Confirmation']
        }
    ]

    # Print to console
    print(f"✅ Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
    print("Summary:")
    print(f"  Total Scanned: 50 stocks")
    print(f"  Qualifying: {len(stocks)} stocks")
    print(f"  High Confidence: 2")
    print(f"  Medium Confidence: 4")
    print()

    print("Qualifying Stocks:")
    print("─" * 95)
    print(f"{'Symbol':<12} {'Price':<10} {'RSI':<6} {'ADX':<6} {'Vol':<6} "
          f"{'Strength':<10} {'Confidence':<12}")
    print("─" * 95)

    for stock in stocks:
        print(f"{stock['symbol']:<12} ₹{stock['price']:<9.2f} {stock['rsi']:<6.1f} "
              f"{stock['adx']:<6.1f} {stock['volume_ratio']:<6.2f}x "
              f"{stock['strength']:<9.1f}% {stock['confidence']:<12}")

    print("─" * 95)
    print()

    # Prepare Telegram message
    msg = format_telegram_message(stocks)

    # Display message
    print("📨 Telegram Message Preview:")
    print("="*60)
    print(msg.replace('<b>', '**').replace('</b>', '**')
                .replace('<i>', '_').replace('</i>', '_')
                .replace('<code>', '`').replace('</code>', '`')
                .replace('━', '─'))
    print("="*60)
    print()

    # Try to send to Telegram
    print("🔔 Sending to Telegram...")
    if send_to_telegram(msg):
        print("✅ Successfully sent to Telegram!")
        return 0
    else:
        print("⚠️  Telegram message not sent (credentials not configured)")
        print()
        print("To enable Telegram notifications:")
        print("  1. Create a Telegram bot via @BotFather")
        print("  2. Get your chat ID from @userinfobot")
        print("  3. Set environment variables:")
        print("     export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("     export TELEGRAM_CHAT_ID='your_chat_id'")
        print()
        return 1

def format_telegram_message(stocks):
    """Format results for Telegram"""
    msg = "<b>📊 NSE F&O PCS Scanner Results</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>\n"
    msg += "━" * 40 + "\n\n"

    msg += f"<b>Summary:</b>\n"
    msg += f"  • Total Scanned: <code>50</code>\n"
    msg += f"  • Qualifying: <code>{len(stocks)}</code>\n"
    msg += f"  • High Confidence: <code>2</code>\n"
    msg += f"  • Medium Confidence: <code>4</code>\n\n"

    msg += "<b>🎯 Top Qualifying Stocks:</b>\n"
    msg += "━" * 40 + "\n"

    for i, stock in enumerate(stocks, 1):
        conf_emoji = "🟢" if stock['confidence'] == 'HIGH' else "🟡"
        msg += f"\n<b>{i}. {stock['symbol']}</b> {conf_emoji}\n"
        msg += f"  💰 Price: ₹{stock['price']:.2f}\n"
        msg += f"  📊 RSI: {stock['rsi']:.1f} | ⚡ ADX: {stock['adx']:.1f}\n"
        msg += f"  📈 Strength: {stock['strength']:.1f}% | 📊 Volume: {stock['volume_ratio']:.2f}x\n"
        msg += f"  🎯 Patterns: {', '.join(stock['patterns'])}\n"

    msg += "\n" + "━" * 40 + "\n"
    msg += "<b>How to use:</b>\n"
    msg += "✓ These stocks show bullish technical setups\n"
    msg += "✓ Suitable for Put Credit Spread strategies\n"
    msg += "✓ Always verify with your own analysis\n\n"
    msg += "<i>⚠️ Disclaimer: Not financial advice. Do your own research.</i>"

    return msg

if __name__ == '__main__':
    import sys
    sys.exit(demo_scan())
