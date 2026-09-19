#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner Runner
Runs the scanner with default filters and sends results to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import scanner from streamlit app (remove streamlit dependency)
import importlib.util
spec = importlib.util.spec_from_file_location("streamlit_app", "/home/user/nsepcs/streamlit_app.py")
streamlit_module = importlib.util.module_from_spec(spec)

# Mock streamlit module before loading
class MockStreamlit:
    def __init__(self):
        self.session_state = {}
        self.text = lambda x: None
        self.markdown = lambda x, unsafe_allow_html=False: None
        self.info = lambda x: None
        self.success = lambda x: None
        self.warning = lambda x: None
        self.error = lambda x: None
        self.progress = lambda x: None
        self.metric = lambda x, y, z=None, delta_color=None: None
        self.empty = lambda: None
        self.columns = lambda x: [self] * x
        self.__enter__ = lambda: self
        self.__exit__ = lambda *args: None

    def set_page_config(self, **kwargs):
        pass

    def button(self, *args, **kwargs):
        return False

    def slider(self, label, min_val, max_val, default, step=1):
        return default

    def number_input(self, label, **kwargs):
        return kwargs.get('value', 0)

    def selectbox(self, label, options, **kwargs):
        return options[0] if options else None

    def checkbox(self, label, **kwargs):
        return False

    def dataframe(self, df, **kwargs):
        pass

    def json(self, data):
        pass

    def tabs(self, tabs):
        return [self] * len(tabs)

    def write(self, text):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['streamlit'] = MockStreamlit()

# Now load the module
spec.loader.exec_module(streamlit_module)
ProfessionalPCSScanner = streamlit_module.ProfessionalPCSScanner

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured")
        print(f"  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def format_stock_for_telegram(stock_result):
    """Format a single stock result for Telegram"""
    symbol = stock_result['symbol'].replace('.NS', '').replace('^', '')
    max_strength = max(p['strength'] for p in stock_result['patterns'])
    confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

    pattern_count = len(stock_result['patterns'])
    current_price = stock_result['current_price']
    rsi = stock_result['rsi']
    adx = stock_result['adx']
    volume_ratio = stock_result['volume_ratio']

    primary_pattern = stock_result['patterns'][0]['type'] if stock_result['patterns'] else 'Unknown'

    text = f"""<b>{symbol}</b>
💪 Strength: {max_strength:.0f}% ({confidence})
📊 Price: ₹{current_price:.2f}
📈 RSI: {rsi:.1f} | ⚡ ADX: {adx:.1f}
📊 Volume: {volume_ratio:.1f}x
🎯 Pattern: {primary_pattern}
📍 Patterns Found: {pattern_count}"""

    return text

def run_scanner():
    """Run the PCS scanner with default filters"""
    print("🚀 Starting NSE F&O PCS Scanner...")
    print(f"⏰ Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print()

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Default filter configuration
    config = {
        'stocks_to_scan': [
            'NIFTY50.NS', 'BANKNIFTY50.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
            'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
            'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS',
            'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS',
            'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS'
        ],
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
            'rectangle_top': False,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': False,
            'inverted_scallop': True
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'stocks_limit': 25,
        'enhancements': {}
    }

    results = []
    failed_stocks = []

    print(f"📊 Scanning {len(config['stocks_to_scan'])} stocks...\n")

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i:2d}/{len(config['stocks_to_scan'])}] Analyzing {clean_symbol}...", end=" ", flush=True)

        try:
            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("⏭️  (No data)")
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                print("⏭️  (Volume)")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print("⏭️  (No patterns)")
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_details': volume_details,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data
            }

            results.append(stock_result)
            max_strength = max(p['strength'] for p in patterns)
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            print(f"✅ ({max_strength:.0f}% {confidence})")

        except Exception as e:
            print(f"❌ (Error)")
            failed_stocks.append((clean_symbol, str(e)))

    print()

    if not results:
        print("❌ No stocks found matching the filter criteria")
        send_telegram_message("❌ NSE F&O PCS Scan Complete\n\nNo stocks matched the filter criteria")
        return

    # Sort results by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    print(f"✅ Found {len(results)} stocks with confirmed patterns!")
    print()

    # Display results
    print("=" * 80)
    print("SCAN RESULTS")
    print("=" * 80)
    print()

    for i, stock in enumerate(results, 1):
        symbol = stock['symbol'].replace('.NS', '').replace('^', '')
        max_strength = max(p['strength'] for p in stock['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        print(f"{i:2d}. {symbol:12s} | Strength: {max_strength:5.0f}% | Confidence: {confidence:6s} | Price: ₹{stock['current_price']:8.2f} | RSI: {stock['rsi']:5.1f} | ADX: {stock['adx']:5.1f}")

    print()
    print("=" * 80)
    print()

    # Prepare Telegram message
    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    telegram_message = f"""<b>🚀 NSE F&O PCS SCAN RESULTS</b>

<b>📊 Scan Summary</b>
📅 Time: {scan_time}
✅ Stocks Found: {len(results)}
📈 Total Patterns: {sum(len(r['patterns']) for r in results)}
🏆 High Confidence: {sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')}

<b>📋 Top Stocks (Sorted by Strength)</b>
"""

    for i, stock in enumerate(results[:10], 1):  # Send top 10
        telegram_message += f"\n{format_stock_for_telegram(stock)}\n"

    if len(results) > 10:
        telegram_message += f"\n... and <b>{len(results) - 10} more stocks</b>"

    # Send to Telegram
    send_telegram_message(telegram_message)

    # Also send a summary message with all stocks if there are more than 10
    if len(results) > 10:
        summary_text = "<b>📋 All Stocks Found</b>\n"
        for stock in results:
            symbol = stock['symbol'].replace('.NS', '').replace('^', '')
            max_strength = max(p['strength'] for p in stock['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            summary_text += f"{symbol}: {max_strength:.0f}% ({confidence})\n"

        send_telegram_message(summary_text)

    print("✅ Scan complete!")

if __name__ == "__main__":
    run_scanner()
