#!/usr/bin/env python3
"""
NSE PCS Scanner - Telegram Integration Script
Sends scan results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz
import requests

def send_telegram_message(message, parse_mode='HTML'):
    """Send message to Telegram"""
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Telegram credentials not configured!")
        print("\nPlease set the following environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nThen run: python3 send_to_telegram.py")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def load_scan_results(filename=None):
    """Load scan results from JSON file"""
    if filename is None:
        # Find the most recent scan results file
        import glob
        files = glob.glob('/tmp/claude-0/-home-user-nsepcs/*/scratchpad/scan_results_*.json')
        if not files:
            return None
        filename = max(files, key=os.path.getctime)

    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def format_results(data):
    """Format scan results for Telegram"""
    if not data or not data.get('results'):
        return "No stocks found in scan results."

    results = data['results']

    message = f"<b>🎯 NSE PCS Scanner Results</b>\n"
    message += f"<b>Scan Time:</b> {data.get('timestamp', 'N/A')}\n"
    message += f"<b>Stocks Found:</b> {len(results)}\n\n"

    # Sort by score
    sorted_results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

    for i, stock in enumerate(sorted_results[:20], 1):
        symbol = stock.get('symbol', 'N/A').replace('.NS', '')
        price = stock.get('price', 0)
        rsi = stock.get('rsi', 0)
        score = stock.get('score', 0)

        message += f"<b>{i}. {symbol}</b>\n"
        message += f"   Price: ₹{price:.2f} | RSI: {rsi:.1f} | Score: {score:.0f}\n"

    if len(results) > 20:
        message += f"\n📊 ... and {len(results) - 20} more stocks"

    message += f"\n\nℹ️ Scan Report Generated\n"
    return message

def main():
    """Main entry point"""
    print("=" * 70)
    print("NSE PCS Scanner - Telegram Integration")
    print("=" * 70)
    print()

    # Load scan results
    data = load_scan_results()

    if not data:
        print("⚠️  No scan results found.")
        print("\nFirst, run the scanner to generate results:")
        print("  python3 -m streamlit run streamlit_app.py")
        print("\nOr use the automated scanner (requires network access to Yahoo Finance):")
        print("  python3 send_to_telegram.py --run-scan")
        sys.exit(1)

    # Format and send
    message = format_results(data)
    print("📝 Message to send:")
    print("-" * 70)
    print(message)
    print("-" * 70)
    print()

    if send_telegram_message(message):
        print("\n✅ Successfully sent to Telegram!")
    else:
        print("\n❌ Failed to send to Telegram")
        sys.exit(1)

if __name__ == "__main__":
    main()
