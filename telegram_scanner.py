#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Automation Script
Runs the stock scanner and sends qualifying stocks to Telegram
"""

import os
import sys
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Get Telegram configuration from environment variables or config file
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DRY_RUN = os.getenv('TELEGRAM_DRY_RUN', 'false').lower() == 'true'

# Try loading from config file if env vars not set
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    config_file = os.path.expanduser("~/.nsepcs_telegram.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                TELEGRAM_BOT_TOKEN = config.get('token')
                TELEGRAM_CHAT_ID = config.get('chat_id')
        except Exception as e:
            print(f"Error reading config file: {e}")
            pass

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("WARNING: Telegram credentials not found!")
    print("Set environment variables:")
    print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
    print("  export TELEGRAM_CHAT_ID='your_chat_id'")
    print("\nOR run setup: python setup_telegram.py")
    print("\nRunning in DRY-RUN mode (will not send to Telegram)")
    DRY_RUN = True

# Import the scanner class from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner

def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send message to Telegram"""
    if DRY_RUN:
        print("\n[DRY-RUN] Would send to Telegram:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        return True

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def get_fno_stocks():
    """Get list of F&O stocks to scan"""
    return [
        # Tier 1 - Ultra High Liquidity
        'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY',
        'ICICIBANK', 'SBIN', 'LT', 'ITC',
        # Tier 2 - High Liquidity
        'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT',
        'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT',
        # Tier 3 - Medium Liquidity
        'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND',
        'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL',
        'TATASTEEL', 'HINDALCO'
    ]

def run_scanner(stocks_list, filters=None):
    """Run the PCS scanner with specified filters"""

    # Default filters
    if filters is None:
        filters = {
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20,
            'ma_support': True,
            'ma_type': 'EMA',
            'ma_tolerance': 3,
            'min_volume_ratio': 1.2,
            'volume_breakout_ratio': 2.0,
            'lookback_days': 20,
            'pattern_strength_min': 65,
            'pattern_filters': {
                'current_day_breakout': True,
                'cup_and_handle': True,
                'flat_base': True,
                'bump_and_run': True,
                'rectangle_bottom': True,
                'head_shoulders_bottom': True,
                'double_bottom': True,
                'rounding_bottom': True,
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
        }

    scanner = ProfessionalPCSScanner()
    qualifying_stocks = []

    print(f"Starting scan of {len(stocks_list)} stocks...")
    print(f"Filters: RSI({filters['rsi_min']}-{filters['rsi_max']}), "
          f"ADX(>{filters['adx_min']}), Pattern Strength(>{filters['pattern_strength_min']})")

    # Process stocks
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for symbol in stocks_list:
            future = executor.submit(process_stock, scanner, symbol, filters)
            futures[future] = symbol

        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result()
                if result:
                    qualifying_stocks.append(result)
                    print(f"✓ {symbol}: {result['patterns_found']} patterns, "
                          f"Strength: {result['avg_strength']:.1f}")
            except Exception as e:
                print(f"✗ {symbol}: Error - {str(e)[:50]}")

    # Sort by average strength descending
    qualifying_stocks.sort(key=lambda x: x['avg_strength'], reverse=True)
    return qualifying_stocks

def process_stock(scanner, symbol, filters):
    """Process a single stock and return results if it meets criteria"""
    try:
        symbol_with_ns = f"{symbol}.NS"

        # Get stock data
        data = scanner.get_stock_data(symbol_with_ns, period="3mo")
        if data is None or len(data) < 20:
            return None

        weekly_data = scanner.get_weekly_stock_data(symbol_with_ns, period="6mo")

        # Detect patterns
        patterns = scanner.detect_patterns(data, symbol_with_ns, filters)

        if not patterns:
            return None

        # Calculate average strength
        avg_strength = np.mean([p['strength'] for p in patterns])

        if avg_strength < filters['pattern_strength_min']:
            return None

        # Get current price and change
        current_price = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
        change_pct = ((current_price - previous_close) / previous_close) * 100

        return {
            'symbol': symbol,
            'patterns': [p['pattern'] for p in patterns],
            'patterns_found': len(patterns),
            'avg_strength': avg_strength,
            'price': current_price,
            'change_pct': change_pct,
            'confidence': patterns[0].get('confidence', 'MEDIUM') if patterns else 'LOW'
        }
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        return None

def format_telegram_message(qualifying_stocks):
    """Format the results as a Telegram message"""
    if not qualifying_stocks:
        return "❌ No stocks matched the filter criteria today."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S %Z")

    message = f"""
🚀 <b>NSE F&O PCS Scanner Results</b>
<i>{current_time}</i>

📊 <b>Stocks Meeting Filter Criteria:</b> {len(qualifying_stocks)}

"""

    for i, stock in enumerate(qualifying_stocks[:15], 1):  # Top 15
        patterns_str = ", ".join(stock['patterns'][:2])  # Show first 2 patterns
        change_sign = "+" if stock['change_pct'] >= 0 else ""

        message += f"""<b>{i}. {stock['symbol']}</b>
   💰 Price: ₹{stock['price']:.2f} ({change_sign}{stock['change_pct']:.2f}%)
   📈 Patterns: {patterns_str}{'...' if len(stock['patterns']) > 2 else ''}
   💪 Strength: {stock['avg_strength']:.1f}/100
   🎯 Confidence: {stock['confidence']}

"""

    if len(qualifying_stocks) > 15:
        message += f"\n<i>... and {len(qualifying_stocks) - 15} more stocks</i>\n"

    message += """
⚠️ <i>Disclaimer: This is for educational purposes only. Always do your own research before trading.</i>
"""

    return message

def main():
    """Main execution function"""
    print("=" * 60)
    print("NSE F&O PCS Screener - Telegram Automation")
    print("=" * 60)

    # Get stocks to scan
    stocks = get_fno_stocks()
    print(f"Scanning {len(stocks)} F&O stocks...")

    # Run scanner
    qualifying_stocks = run_scanner(stocks)

    # Format and send message
    message = format_telegram_message(qualifying_stocks)

    print("\n" + "=" * 60)
    print(f"Found {len(qualifying_stocks)} qualifying stocks")
    print("=" * 60)
    print(message)

    # Send to Telegram
    print("\nSending to Telegram...")
    if send_telegram_message(message):
        print("✓ Message sent successfully to Telegram!")
        return 0
    else:
        print("✗ Failed to send message to Telegram")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        error_msg = f"🔴 <b>Scanner Error</b>\n\n{str(e)[:500]}"
        send_telegram_message(error_msg)
        sys.exit(1)
