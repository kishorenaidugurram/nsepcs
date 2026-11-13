#!/usr/bin/env python3
"""
Generate sample PCS scanner results and send to Telegram
This is useful when live data is unavailable
"""

import json
import os
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')

# Sample qualifying stocks with realistic data
SAMPLE_RESULTS = [
    {
        'symbol': 'RELIANCE.NS',
        'current_price': 2845.50,
        'volume_ratio': 2.3,
        'rsi': 62.5,
        'adx': 28.3,
        'patterns': [
            {
                'type': 'Current Day Breakout',
                'strength': 87.5,
                'confidence': 'HIGH'
            }
        ]
    },
    {
        'symbol': 'HDFCBANK.NS',
        'current_price': 1624.75,
        'volume_ratio': 1.8,
        'rsi': 58.2,
        'adx': 25.1,
        'patterns': [
            {
                'type': 'Flat Base Breakout',
                'strength': 79.3,
                'confidence': 'MEDIUM'
            }
        ]
    },
    {
        'symbol': 'INFY.NS',
        'current_price': 2234.25,
        'volume_ratio': 2.1,
        'rsi': 64.8,
        'adx': 30.2,
        'patterns': [
            {
                'type': 'Cup and Handle',
                'strength': 85.0,
                'confidence': 'HIGH'
            }
        ]
    },
    {
        'symbol': 'ICICIBANK.NS',
        'current_price': 1125.50,
        'volume_ratio': 1.9,
        'rsi': 61.3,
        'adx': 26.7,
        'patterns': [
            {
                'type': 'Double Bottom (Eve & Eve)',
                'strength': 78.5,
                'confidence': 'MEDIUM'
            }
        ]
    },
    {
        'symbol': 'TCS.NS',
        'current_price': 3654.80,
        'volume_ratio': 2.0,
        'rsi': 63.1,
        'adx': 27.5,
        'patterns': [
            {
                'type': 'Rectangle Bottom',
                'strength': 76.2,
                'confidence': 'MEDIUM'
            }
        ]
    },
    {
        'symbol': 'LT.NS',
        'current_price': 2456.30,
        'volume_ratio': 1.7,
        'rsi': 59.4,
        'adx': 24.8,
        'patterns': [
            {
                'type': 'Rounding Bottom',
                'strength': 72.1,
                'confidence': 'MEDIUM'
            }
        ]
    },
    {
        'symbol': 'AXISBANK.NS',
        'current_price': 1098.75,
        'volume_ratio': 2.2,
        'rsi': 65.2,
        'adx': 29.1,
        'patterns': [
            {
                'type': 'Current Day Breakout',
                'strength': 84.0,
                'confidence': 'HIGH'
            }
        ]
    },
    {
        'symbol': 'KOTAKBANK.NS',
        'current_price': 1852.50,
        'volume_ratio': 1.9,
        'rsi': 60.7,
        'adx': 25.9,
        'patterns': [
            {
                'type': 'Head-and-Shoulders Bottom',
                'strength': 80.5,
                'confidence': 'MEDIUM'
            }
        ]
    },
]

def send_to_telegram(results, telegram_token=None, telegram_chat_id=None):
    """Send results to Telegram"""
    if not telegram_token or not telegram_chat_id:
        print("ℹ️  Telegram credentials not provided.")
        print("   Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables to send results.")
        return False

    try:
        import requests

        # Format message
        message = f"🎯 NSE F&O PCS Scanner Results\n"
        message += f"📅 {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
        message += f"✅ Found {len(results)} stocks meeting filter criteria\n\n"

        # Add top stocks
        message += "📋 Top Stocks:\n"
        for i, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            price = result['current_price']
            pattern = result['patterns'][0]['type']
            message += f"{i}. {symbol:12s} - {confidence:6s} ({max_strength:5.1f}%) @ ₹{price:8.2f}\n"

        if len(results) > 10:
            message += f"\n... and {len(results) - 10} more stocks"

        # Send to Telegram
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            print("✅ Results sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def display_results(results):
    """Display results in console"""
    print("\n" + "=" * 100)
    print("🎯 NSE F&O PCS SCANNER - SAMPLE RESULTS")
    print("=" * 100)
    print(f"📅 Generated: {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📈 Total Stocks Found: {len(results)}\n")

    print(f"{'#':<3} {'Symbol':<15} {'Confidence':<12} {'Strength':<10} {'Price':<12} {'Volume':<10} {'Patterns':<30}")
    print("-" * 100)

    for i, result in enumerate(results, 1):
        symbol = result['symbol'].replace('.NS', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
        price = result['current_price']
        volume = f"{result['volume_ratio']:.1f}x"
        patterns = ', '.join([p['type'][:25] for p in result['patterns']])

        print(f"{i:<3} {symbol:<15} {confidence:<12} {max_strength:>6.1f}%    ₹{price:<10.2f} {volume:<10} {patterns:<30}")

    print("=" * 100)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner - Sample Results Generator')
    parser.add_argument('--telegram-token', type=str, help='Telegram bot token')
    parser.add_argument('--telegram-chat-id', type=str, help='Telegram chat ID')

    args = parser.parse_args()

    # Check for environment variables
    telegram_token = args.telegram_token or os.environ.get('TELEGRAM_TOKEN')
    telegram_chat_id = args.telegram_chat_id or os.environ.get('TELEGRAM_CHAT_ID')

    # Display results
    display_results(SAMPLE_RESULTS)

    # Send to Telegram
    if telegram_token and telegram_chat_id:
        print("\n📤 Sending to Telegram...")
        send_to_telegram(SAMPLE_RESULTS, telegram_token, telegram_chat_id)
    else:
        print("\n💡 To send these results to Telegram:")
        print("   export TELEGRAM_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print("   python3 generate_sample_results.py")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
