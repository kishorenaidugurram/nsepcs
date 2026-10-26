#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Alert (Demo Version)
Demo with sample data to show Telegram integration
"""

import os
import requests
import pytz
from datetime import datetime

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Sample stock data (what would be screened from live data)
SAMPLE_RESULTS = [
    {
        'symbol': 'RELIANCE',
        'price': 3245.75,
        'rsi': 58.3,
        'adx': 28.5,
        'volume_ratio': 1.45,
        'score': 82,
        'signals': [
            'Optimal RSI: 58.3',
            'Strong uptrend (Price > SMA20 > SMA50)',
            'MACD bullish (above signal)',
            'Strong trend (ADX: 28.5)',
            'High volume: 1.45x'
        ]
    },
    {
        'symbol': 'TCS',
        'price': 4156.20,
        'rsi': 52.1,
        'adx': 24.8,
        'volume_ratio': 1.32,
        'score': 78,
        'signals': [
            'Optimal RSI: 52.1',
            'Strong uptrend (Price > SMA20 > SMA50)',
            'MACD above signal line',
            'Strong trend (ADX: 24.8)'
        ]
    },
    {
        'symbol': 'HDFCBANK',
        'price': 1892.50,
        'rsi': 55.7,
        'adx': 26.2,
        'volume_ratio': 1.38,
        'score': 75,
        'signals': [
            'Optimal RSI: 55.7',
            'Strong uptrend (Price > SMA20 > SMA50)',
            'MACD bullish (above signal)',
            'High volume: 1.38x'
        ]
    },
    {
        'symbol': 'INFY',
        'price': 2785.90,
        'rsi': 49.5,
        'adx': 22.1,
        'volume_ratio': 1.28,
        'score': 68,
        'signals': [
            'Good RSI: 49.5',
            'Price above SMA20',
            'MACD above signal line',
            'Moderate trend (ADX: 22.1)'
        ]
    },
    {
        'symbol': 'ICICIBANK',
        'price': 1256.75,
        'rsi': 61.2,
        'adx': 29.5,
        'volume_ratio': 1.52,
        'score': 85,
        'signals': [
            'Optimal RSI: 61.2',
            'Strong uptrend (Price > SMA20 > SMA50)',
            'MACD bullish (above signal)',
            'Strong trend (ADX: 29.5)',
            'High volume: 1.52x'
        ]
    },
    {
        'symbol': 'SBIN',
        'price': 892.30,
        'rsi': 53.8,
        'adx': 25.4,
        'volume_ratio': 1.41,
        'score': 76,
        'signals': [
            'Optimal RSI: 53.8',
            'Strong uptrend (Price > SMA20 > SMA50)',
            'MACD above signal line',
            'High volume: 1.41x'
        ]
    },
]

def send_telegram_message(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if bot_token is None or chat_id is None:
        print("⚠️ Telegram credentials not configured.")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_telegram_message(results):
    """Format results for Telegram"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")

    message = f"<b>📈 NSE F&O PCS Screener Results</b>\n"
    message += f"<i>{current_time}</i>\n\n"
    message += f"<b>Found {len(results)} stocks with bullish signals</b>\n"
    message += "═" * 50 + "\n\n"

    for idx, result in enumerate(results, 1):
        score = result['score']
        emoji = '🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'

        message += f"<b>{idx}. {result['symbol']}</b> {emoji} [{score:.0f}/100]\n"
        message += f"Price: ₹{result['price']:.2f} | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"Volume: {result['volume_ratio']:.1f}x\n"

        for signal in result['signals']:
            message += f"  • {signal}\n"
        message += "─" * 50 + "\n\n"

    message += "\n<b>Disclaimer:</b> Not financial advice. Always do your own research."

    return message

def main():
    """Main execution"""
    print("=" * 60)
    print("NSE F&O PCS Screener - Telegram Alert")
    print("(Demo Version - Using Sample Data)")
    print("=" * 60)
    print()

    # Format message
    message = format_telegram_message(SAMPLE_RESULTS)

    # Print to console
    print("📋 Sample Results to Send:")
    print()
    print(message)
    print()
    print("=" * 60)

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n📤 Sending to Telegram...")
        if send_telegram_message(message, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID):
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
    else:
        print("\n⚠️ Telegram credentials not configured.")
        print("\nTo enable Telegram notifications, set:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nThen run this script again.")

    print("=" * 60)

if __name__ == "__main__":
    main()
