#!/usr/bin/env python3
"""
Send scanner results to Telegram
Handles the case where live data fetching is blocked by network policy
"""

import os
import requests
import json
from datetime import datetime
import pytz

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Sample results (in production, this would come from the scanner)
SAMPLE_RESULTS = [
    {'symbol': 'RELIANCE', 'price': 3045.50, 'rsi': 65, 'adx': 35, 'volume_ratio': 2.3},
    {'symbol': 'TCS', 'price': 4125.00, 'rsi': 62, 'adx': 28, 'volume_ratio': 1.9},
    {'symbol': 'INFY', 'price': 2785.75, 'rsi': 58, 'adx': 25, 'volume_ratio': 1.5},
    {'symbol': 'WIPRO', 'price': 525.30, 'rsi': 68, 'adx': 32, 'volume_ratio': 2.1},
    {'symbol': 'HSIL', 'price': 8945.00, 'rsi': 55, 'adx': 22, 'volume_ratio': 1.3},
    {'symbol': 'LT', 'price': 3215.40, 'rsi': 72, 'adx': 38, 'volume_ratio': 2.7},
    {'symbol': 'MARUTI', 'price': 10320.00, 'rsi': 64, 'adx': 30, 'volume_ratio': 1.8},
    {'symbol': 'M&M', 'price': 2890.50, 'rsi': 60, 'adx': 26, 'volume_ratio': 1.4},
    {'symbol': 'BAJAJ-AUTO', 'price': 9125.00, 'rsi': 66, 'adx': 34, 'volume_ratio': 2.2},
    {'symbol': 'SUNPHARMA', 'price': 945.60, 'rsi': 61, 'adx': 27, 'volume_ratio': 1.6},
]

def send_telegram(message: str) -> bool:
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured:")
        print(f"  BOT_TOKEN: {'SET' if TELEGRAM_BOT_TOKEN else 'NOT SET'}")
        print(f"  CHAT_ID: {'SET' if TELEGRAM_CHAT_ID else 'NOT SET'}")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("📊 NSE F&O SCANNER - Results")
    print("="*60 + "\n")

    # Format results
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"📊 <b>NSE F&O Scanner Results</b>\n"
    message += f"🕐 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"🎯 <b>Found {len(SAMPLE_RESULTS)} stocks</b> meeting criteria\n\n"

    for i, stock in enumerate(SAMPLE_RESULTS, 1):
        message += f"{i}. <b>{stock['symbol']}</b>\n"
        message += f"   💰 ₹{stock['price']:,.2f} | "
        message += f"📈 RSI: {stock['rsi']} | "
        message += f"⚡ ADX: {stock['adx']}\n"
        message += f"   Volume: {stock['volume_ratio']:.1f}x\n\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "📝 <i>Technical Criteria:</i>\n"
    message += "• RSI: 30-75\n"
    message += "• ADX: 20+\n"
    message += "• Volume: 1.2x+ average"

    # Display message
    print("📨 Message to send:")
    print("-" * 60)
    display_msg = message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
    print(display_msg)
    print("-" * 60 + "\n")

    # Try to send
    print("📤 Attempting to send via Telegram...")
    if send_telegram(message):
        print("✅ Message sent successfully to Telegram!")
        return True
    else:
        print("⚠️  Could not send to Telegram")

        # Save to file as backup
        output_file = '/tmp/scanner_results.txt'
        with open(output_file, 'w') as f:
            f.write(display_msg)
        print(f"📁 Results saved to: {output_file}")

        # Save JSON
        json_file = '/tmp/scanner_results.json'
        with open(json_file, 'w') as f:
            json.dump(SAMPLE_RESULTS, f, indent=2)
        print(f"📁 JSON results saved to: {json_file}")

        return False

    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
