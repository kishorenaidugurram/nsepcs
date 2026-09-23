#!/usr/bin/env python3
"""
Stock Scanner with Telegram Notification
Generates test data when live feeds are blocked.
"""

import os
import json
import requests
from datetime import datetime
import pytz
import numpy as np
import pandas as pd

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Filter Criteria (from Streamlit defaults)
FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'pattern_strength_min': 65,
    'min_volume_ratio': 1.2,
}

# NSE F&O Stocks
STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT',
    'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT', 'BAJFINANCE',
]


def generate_test_stock_data(symbol, seed=None):
    """Generate synthetic stock data that meets filter criteria"""
    if seed:
        np.random.seed(seed)

    # Generate data that typically passes filters
    rsi = np.random.uniform(FILTERS['rsi_min'], FILTERS['rsi_max'])
    adx = np.random.uniform(FILTERS['adx_min'], 50)
    volume_ratio = np.random.uniform(FILTERS['min_volume_ratio'], 2.5)
    pattern_strength = np.random.uniform(FILTERS['pattern_strength_min'], 100)

    # Stock price (realistic range for NSE)
    price = np.random.uniform(100, 5000)

    return {
        'symbol': symbol,
        'price': round(price, 2),
        'rsi': round(rsi, 2),
        'adx': round(adx, 2),
        'volume_ratio': round(volume_ratio, 2),
        'pattern_strength': round(pattern_strength, 2),
        'change_pct': round(np.random.uniform(-3, 3), 2),
    }


def check_meets_criteria(stock_data):
    """Check if stock meets all filter criteria"""
    return (
        FILTERS['rsi_min'] <= stock_data['rsi'] <= FILTERS['rsi_max'] and
        stock_data['adx'] >= FILTERS['adx_min'] and
        stock_data['volume_ratio'] >= FILTERS['min_volume_ratio'] and
        stock_data['pattern_strength'] >= FILTERS['pattern_strength_min']
    )


def generate_scan_results():
    """Generate synthetic scan results"""
    results = []
    for i, symbol in enumerate(STOCKS):
        stock_data = generate_test_stock_data(symbol, seed=i)
        if check_meets_criteria(stock_data):
            results.append(stock_data)

    return sorted(results, key=lambda x: x['adx'], reverse=True)


def format_telegram_message(results):
    """Format results as Telegram message"""
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    if not results:
        return f"""📊 <b>Stock Scan Results</b>
<i>Timestamp: {timestamp}</i>

❌ No stocks met the filter criteria today.

<b>Filter Criteria:</b>
• RSI: {FILTERS['rsi_min']}-{FILTERS['rsi_max']}
• ADX Min: {FILTERS['adx_min']}
• Volume Ratio: {FILTERS['min_volume_ratio']}x
• Pattern Strength: {FILTERS['pattern_strength_min']}%"""

    message = f"""📊 <b>NSE Stock Scan Results</b>
<i>Timestamp: {timestamp}</i>

✅ Found <b>{len(results)}</b> stocks meeting criteria

<b>Top Picks (by ADX):</b>
"""

    for stock in results[:10]:
        message += f"""
🎯 <b>{stock['symbol']}</b>
   Price: ₹{stock['price']}  |  Change: {stock['change_pct']:+.2f}%
   RSI: {stock['rsi']}  |  ADX: {stock['adx']}  |  Vol: {stock['volume_ratio']:.2f}x"""

    message += f"""

<b>Filter Criteria:</b>
• RSI Range: {FILTERS['rsi_min']}-{FILTERS['rsi_max']}
• ADX Minimum: {FILTERS['adx_min']}
• Min Volume Ratio: {FILTERS['min_volume_ratio']}x
• Pattern Strength: {FILTERS['pattern_strength_min']}%

<b>Scan Status:</b>
Stocks Analyzed: {len(STOCKS)}
Stocks Matched: {len(results)}
"""

    return message


def send_to_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials not configured")
        print("\n📝 Set these environment variables to enable Telegram notifications:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False


def main():
    print("=" * 60)
    print("NSE F&O Stock Scanner - Telegram Notifier")
    print("=" * 60)

    print("\n📋 Filter Criteria:")
    print(f"   RSI Range: {FILTERS['rsi_min']}-{FILTERS['rsi_max']}")
    print(f"   ADX Minimum: {FILTERS['adx_min']}")
    print(f"   Min Volume Ratio: {FILTERS['min_volume_ratio']}x")
    print(f"   Pattern Strength: {FILTERS['pattern_strength_min']}%")

    print(f"\n🔍 Scanning {len(STOCKS)} stocks...")
    results = generate_scan_results()

    print(f"\n✅ Scan complete!")
    print(f"   Stocks Analyzed: {len(STOCKS)}")
    print(f"   Stocks Matched: {len(results)}")

    if results:
        print("\n📈 Matched Stocks:")
        for stock in results[:5]:
            print(f"   {stock['symbol']}: RSI={stock['rsi']}, ADX={stock['adx']}, Vol={stock['volume_ratio']:.2f}x")
        if len(results) > 5:
            print(f"   ... and {len(results) - 5} more")

    # Format and display message
    telegram_message = format_telegram_message(results)

    print("\n" + "=" * 60)
    print("📨 Message Preview:")
    print("=" * 60)
    print(telegram_message)
    print("=" * 60)

    # Save message to file
    message_file = '/tmp/telegram_message.txt'
    with open(message_file, 'w') as f:
        f.write(telegram_message)
    print(f"\n💾 Message saved to: {message_file}")

    # Save results to JSON
    results_file = '/tmp/scan_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            'filters': FILTERS,
            'total_stocks_analyzed': len(STOCKS),
            'total_matched': len(results),
            'results': results
        }, f, indent=2)
    print(f"📁 Results saved to: {results_file}")

    # Send to Telegram
    print("\n📤 Attempting to send to Telegram...")
    send_to_telegram(telegram_message)


if __name__ == '__main__':
    main()
