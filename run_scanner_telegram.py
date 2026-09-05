#!/usr/bin/env python3
"""
Standalone scanner script that runs the NSE F&O PCS screener and sends results to Telegram
"""

import sys
import os
import json
import subprocess
from datetime import datetime
import numpy as np

# Set up path to import streamlit app components
sys.path.insert(0, '/home/user/nsepcs')

# Import required modules
import pandas as pd
import requests
import warnings
warnings.filterwarnings('ignore')

# Import the scanner class from streamlit app
# We'll need to extract the class definition since streamlit_app uses streamlit
print("Loading scanner module...")

# Load the main app to get the constants and classes
try:
    # Try direct import first
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    print(f"✓ Loaded scanner with {len(COMPLETE_NSE_FO_UNIVERSE)} stocks in F&O universe")
except ImportError as e:
    print(f"Error loading scanner: {e}")
    sys.exit(1)

class TelegramNotifier:
    """Send messages to Telegram"""
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.token and self.chat_id)

    def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_results(self, results, filters):
        """Format and send results to Telegram"""
        if not self.enabled:
            print("Telegram not configured. Results not sent.")
            return

        if not results:
            message = "⚠️ <b>NSE PCS Scan Complete</b>\n\nNo stocks found meeting filter criteria."
            self.send_message(message)
            return

        # Sort results by pattern strength
        sorted_results = sorted(results, key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        # Build message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🎯 <b>NSE PCS Scan Results</b>\n"
        message += f"📅 {timestamp}\n\n"
        message += f"<b>Found {len(sorted_results)} stocks with patterns</b>\n"
        message += f"├─ RSI Range: {filters['rsi_min']}-{filters['rsi_max']}\n"
        message += f"├─ Min ADX: {filters['adx_min']}\n"
        message += f"└─ Volume Ratio: {filters['min_volume_ratio']}\n\n"

        # Add top 10 results
        for i, result in enumerate(sorted_results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']

            # Get best pattern
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])
            pattern_type = best_pattern['type']
            strength = best_pattern['strength']

            message += f"{i}. <b>{symbol}</b> ₹{price:.2f}\n"
            message += f"   📊 {pattern_type} ({strength:.0f}%)\n"
            message += f"   RSI: {rsi:.1f} | ADX: {adx:.1f}\n\n"

        if len(sorted_results) > 10:
            message += f"... and {len(sorted_results) - 10} more stocks\n\n"

        message += "🔗 View full results at: <code>https://nse-fo-pcs-screener.streamlit.app</code>"

        self.send_message(message)

def run_scanner():
    """Run the scanner with default filters"""

    # Default filters from sidebar
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
        'pattern_strength_min': 50,
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
        'show_news': False,
        'enhancements': {
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False,
        }
    }

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    print(f"🔄 Starting scan of {len(stocks_to_scan)} stocks...")
    print(f"📋 Filters: RSI {filters['rsi_min']}-{filters['rsi_max']}, ADX>{filters['adx_min']}")

    scanner = ProfessionalPCSScanner()
    results = []
    errors = []

    for i, symbol in enumerate(stocks_to_scan):
        progress = (i + 1) / len(stocks_to_scan) * 100
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        if (i + 1) % 20 == 0:
            print(f"  [{progress:5.1f}%] Processing {clean_symbol}...")

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, filters['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
            }

            results.append(stock_result)

        except Exception as e:
            errors.append((clean_symbol, str(e)))

    print(f"\n✓ Scan complete!")
    print(f"  Found: {len(results)} stocks")
    print(f"  Errors: {len(errors)}")

    if errors and len(errors) <= 5:
        print(f"\nError details:")
        for symbol, error in errors[:5]:
            print(f"  {symbol}: {error[:50]}...")

    return results, filters

def save_results_to_file(results, filters):
    """Save results to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/home/user/nsepcs/scan_results_{timestamp}.json"

    data = {
        'timestamp': datetime.now().isoformat(),
        'filters': {k: v for k, v in filters.items() if k not in ['pattern_filters', 'enhancements']},
        'results': [
            {
                'symbol': r['symbol'],
                'current_price': r['current_price'],
                'rsi': r['rsi'],
                'adx': r['adx'],
                'volume_ratio': r['volume_ratio'],
                'patterns': r['patterns']
            }
            for r in results
        ]
    }

    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"📄 Results saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

def main():
    print("=" * 60)
    print("NSE F&O PCS Screener - Scheduled Scan")
    print("=" * 60)
    print()

    # Run scanner
    results, filters = run_scanner()

    # Save results
    result_file = save_results_to_file(results, filters)

    # Send to Telegram
    print("\n📱 Sending results to Telegram...")
    notifier = TelegramNotifier()

    if notifier.enabled:
        print("✓ Telegram credentials found")
        notifier.send_results(results, filters)
        print("✓ Telegram message sent")
    else:
        print("⚠️  Telegram credentials not configured")
        print("   Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables")

    print("\n" + "=" * 60)
    print("Scan completed!")
    print("=" * 60)

    # Return results count for exit code
    return len(results)

if __name__ == "__main__":
    result_count = main()
    sys.exit(0)
