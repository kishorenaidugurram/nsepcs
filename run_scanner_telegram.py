#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Integration
Runs the stock scanner and sends results to Telegram
"""

import os
import sys
from datetime import datetime
import pandas as pd
import requests
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        print("   Please set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your-bot-token'")
        print("   export TELEGRAM_CHAT_ID='your-chat-id'")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False

def format_results_for_telegram(results: list, total_stocks: int) -> str:
    """Format scanner results for Telegram message"""
    if not results:
        return f"<b>📊 NSE F&O PCS Scanner Results</b>\n\n❌ No stocks found meeting the criteria\n\n<i>Scanned {total_stocks} stocks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>"

    message = f"<b>📊 NSE F&O PCS Scanner Results</b>\n"
    message += f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>\n"
    message += f"<i>Stocks found: {len(results)} out of {total_stocks} scanned</i>\n\n"

    # Sort by pattern count and strength
    sorted_results = sorted(results, key=lambda x: (len(x.get('patterns', [])), x.get('latest_price', 0)), reverse=True)

    for idx, stock in enumerate(sorted_results[:15], 1):  # Limit to top 15 due to message length
        symbol = stock['symbol'].replace('.NS', '')
        patterns = stock.get('patterns', [])
        price = stock.get('latest_price', 'N/A')

        pattern_str = ", ".join([p['type'][:15] for p in patterns[:2]])  # Show top 2 patterns

        message += f"<b>{idx}. {symbol}</b> - ₹{price}\n"
        message += f"   📈 Patterns: {pattern_str}\n"
        message += f"   📊 Count: {len(patterns)} pattern(s)\n\n"

    if len(results) > 15:
        message += f"<i>... and {len(results) - 15} more stocks</i>\n"

    message += "<i>Use the web app for detailed analysis: https://nse-fo-pcs-screener.streamlit.app</i>"

    return message

def run_scanner(max_stocks: int = 50, pattern_strength_min: int = 50) -> dict:
    """Run the PCS scanner with default filters"""
    scanner = ProfessionalPCSScanner()

    # Default filters for PCS screening
    filters = {
        'rsi_min': 35,
        'rsi_max': 65,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'SMA',
        'ma_tolerance': 2,
        'pattern_strength_min': pattern_strength_min,
        'lookback_days': 20,
        'volume_breakout_ratio': 2.0,
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'flat_base': True,
            'double_bottom': True,
            'rectangle_bottom': True,
            'head_shoulders_bottom': True,
            'bump_and_run': True,
            'three_rising_valleys': True,
            'rounding_bottom': True
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True
    }

    print(f"🔍 Starting PCS Scanner on {len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")
    print(f"   Max analysis: {max_stocks} stocks")
    print(f"   Pattern strength threshold: {pattern_strength_min}+")
    print()

    results = []
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    for idx, symbol in enumerate(stocks_to_scan, 1):
        try:
            stock_name = symbol.replace('.NS', '')
            print(f"[{idx}/{min(max_stocks, len(COMPLETE_NSE_FO_UNIVERSE))}] Analyzing {stock_name}...", end='', flush=True)

            # Get stock data
            data = scanner.get_stock_data(symbol, period='3mo')

            if data is None or len(data) < 30:
                print(" ⏭️  Skip (insufficient data)")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)

            if patterns:
                latest_price = data['Close'].iloc[-1]
                results.append({
                    'symbol': symbol,
                    'latest_price': round(latest_price, 2),
                    'patterns': patterns,
                    'num_patterns': len(patterns)
                })
                print(f" ✅ {len(patterns)} pattern(s) found")
            else:
                print(" ✗ No patterns")

        except Exception as e:
            print(f" ❌ Error: {str(e)[:30]}")
            continue

    print()
    print(f"✅ Scan complete: Found {len(results)} stocks with patterns")

    return {
        'results': results,
        'total_scanned': len(stocks_to_scan),
        'timestamp': datetime.now()
    }

def main():
    """Main function"""
    print("=" * 60)
    print("NSE F&O PCS Scanner with Telegram Integration")
    print("=" * 60)
    print()

    # Run scanner
    scan_data = run_scanner(max_stocks=50, pattern_strength_min=50)

    # Format results for Telegram
    results = scan_data['results']
    total_scanned = scan_data['total_scanned']

    message = format_results_for_telegram(results, total_scanned)

    # Send to Telegram
    print()
    print("📤 Sending results to Telegram...")
    success = send_telegram_message(message)

    if success:
        print()
        print("✅ All done! Results sent to Telegram")
        return 0
    else:
        print()
        print("❌ Failed to send Telegram message")
        print("   Please check your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print()
        print("📋 Found Stocks (for reference):")
        for stock in results[:10]:
            print(f"   - {stock['symbol']}: {len(stock['patterns'])} patterns")
        return 1

if __name__ == "__main__":
    sys.exit(main())
