#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner
Runs stock analysis and sends results to Telegram
"""

import sys
import os
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import json

warnings.filterwarnings('ignore')

# Import from streamlit_app
sys.path.insert(0, os.path.dirname(__file__))
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter criteria
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'EMA',
    'ma_tolerance': 3,
    'min_volume_ratio': 1.2,
    'volume_breakout_ratio': 2.0,
    'lookback_days': 20,
    'pattern_strength_min': 65,  # Main filter criteria
    'pattern_filters': {
        'current_day_breakout': True,
        'cup_and_handle': True,
        'flat_base': True,
        'bump_and_run': True,
        'rectangle_bottom': True,
        'rectangle_top': True,
        'head_shoulders_bottom': True,
        'double_bottom': True,
        'three_rising_valleys': True,
        'rounding_bottom': True,
        'rounding_top_upside': True,
        'inverted_scallop': True,
    },
    'pattern_priority': 'All Patterns (Comprehensive)',
    'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
    'show_charts': False,
    'show_news': False,
    'export_results': False,
}


def send_to_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured. Skipping Telegram notification.")
        print(f"Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
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
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False


def run_scanner(max_stocks=None, pattern_strength_min=65):
    """
    Run the stock scanner with specified filters

    Args:
        max_stocks: Maximum number of stocks to scan (None = all)
        pattern_strength_min: Minimum pattern strength to include in results
    """

    print("\n" + "="*60)
    print("🚀 NSE F&O PCS SCANNER - STARTING")
    print("="*60)

    # Update filter
    filters = DEFAULT_FILTERS.copy()
    filters['pattern_strength_min'] = pattern_strength_min

    # Get stock list
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"📊 Scanning {len(stocks_to_scan)} stocks")
    print(f"🎯 Minimum pattern strength: {pattern_strength_min}%")
    print(f"📈 Analysis mode: {filters['analysis_mode']}")
    print()

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Results storage
    results = []
    failed_stocks = []

    # Scan each stock
    for i, symbol in enumerate(stocks_to_scan, 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        progress = f"[{i}/{len(stocks_to_scan)}]"

        try:
            print(f"{progress} Analyzing {clean_symbol}...", end=' ')

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("⚠️  No data")
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, filters['min_volume_ratio'])
            if not volume_ok:
                print(f"❌ Low volume ({volume_ratio:.1f}x)")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                print("❌ No patterns")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Check if any pattern meets minimum strength
            max_strength = max(p['strength'] for p in patterns)
            if max_strength < pattern_strength_min:
                print(f"⚠️  Below threshold ({max_strength:.0f}%)")
                continue

            print(f"✅ Found (Strength: {max_strength:.0f}%)")

            # Add to results
            stock_result = {
                'symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'max_strength': max_strength,
            }
            results.append(stock_result)

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            failed_stocks.append((clean_symbol, str(e)[:50]))

    print()
    print("="*60)
    print("📊 SCAN COMPLETE")
    print("="*60)

    return results, failed_stocks


def format_telegram_message(results):
    """Format results for Telegram"""

    if not results:
        return "❌ No stocks found meeting the filter criteria.\n\nScanned with minimum pattern strength: 65%"

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    # Build message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""<b>📈 NSE F&O PCS Scanner Results</b>
<b>Time:</b> {current_time}

<b>Found {len(results)} stocks meeting criteria:</b>
Min Pattern Strength: <b>65%</b>

"""

    for i, stock in enumerate(results[:15], 1):  # Limit to 15 stocks per message
        symbol = stock['symbol']
        price = stock['current_price']
        rsi = stock['rsi']
        adx = stock['adx']
        strength = stock['max_strength']
        patterns = stock['patterns']

        # Get top pattern
        top_pattern = patterns[0]['type'] if patterns else 'N/A'
        confidence = patterns[0]['confidence'] if patterns else 'N/A'

        # Format confidence
        conf_emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'

        message += f"""{i}. <b>{symbol}</b> {conf_emoji}
   Price: ₹{price:.2f} | Strength: {strength:.0f}% | RSI: {rsi:.0f} | ADX: {adx:.0f}
   Pattern: {top_pattern}

"""

    if len(results) > 15:
        message += f"\n... and {len(results) - 15} more stocks"

    message += f"\n<i>Run: <code>streamlit run streamlit_app.py</code> for detailed analysis</i>"

    return message


def main():
    """Main execution"""

    # Parse arguments
    max_stocks = None
    min_strength = 65

    if len(sys.argv) > 1:
        try:
            max_stocks = int(sys.argv[1])
        except ValueError:
            pass

    if len(sys.argv) > 2:
        try:
            min_strength = int(sys.argv[2])
        except ValueError:
            pass

    # Run scanner
    results, failed_stocks = run_scanner(max_stocks=max_stocks, pattern_strength_min=min_strength)

    # Print summary
    print(f"\n📊 Results Summary:")
    print(f"   ✅ Stocks Found: {len(results)}")
    print(f"   ❌ Failed: {len(failed_stocks)}")

    if results:
        print(f"\n🏆 Top 5 Stocks:")
        for i, stock in enumerate(sorted(results, key=lambda x: x['max_strength'], reverse=True)[:5], 1):
            print(f"   {i}. {stock['symbol']} - Strength: {stock['max_strength']:.0f}%")

    # Send to Telegram
    print(f"\n📲 Sending to Telegram...")
    message = format_telegram_message(results)
    send_to_telegram(message)

    # Save results to file
    if results:
        output_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump([{
                'symbol': r['symbol'],
                'price': float(r['current_price']),
                'strength': float(r['max_strength']),
                'rsi': float(r['rsi']),
                'adx': float(r['adx']),
                'volume_ratio': float(r['volume_ratio']),
                'patterns': [p['type'] for p in r['patterns']]
            } for r in results], f, indent=2)
        print(f"✅ Results saved to {output_file}")


if __name__ == "__main__":
    main()
