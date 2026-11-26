#!/usr/bin/env python3
"""
Standalone Stock Scanner - Runs PCS screening and sends results to Telegram
Designed to run as a scheduled routine/cron job
"""

import sys
import os
import json
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Import the scanner from streamlit app
sys.path.insert(0, '/home/user/nsepcs')

# Import classes and functions from streamlit_app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

class TelegramNotifier:
    """Send notifications to Telegram"""

    def __init__(self, bot_token=None, chat_id=None):
        """Initialize with Telegram credentials from env or parameters"""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def is_configured(self):
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.is_configured():
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_results(self, results, scan_time):
        """Format and send scan results to Telegram"""
        if not results:
            message = f"<b>🚫 No stocks found</b>\n📅 {scan_time}\n\nTry adjusting filter criteria."
            self.send_message(message)
            return True

        # Sort by strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        # Build message in chunks (Telegram has message length limit)
        total_stocks = len(results)
        message_parts = []

        # Header
        header = f"""<b>📊 NSE F&O PCS Scanner Results</b>
<b>{'='*40}</b>
📅 Scan Time: {scan_time}
📈 Stocks Found: <b>{total_stocks}</b>

<b>Top Opportunities:</b>"""

        message_parts.append(header)

        # Top 10 stocks
        for idx, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            patterns = [p['type'] for p in result['patterns']]

            stock_info = f"""
<b>{idx}. {symbol}</b>
   💪 Strength: {max_strength:.0f}%
   💰 Price: ₹{result['current_price']:.2f}
   📊 Volume: {result['volume_ratio']:.1f}x
   📈 RSI: {result['rsi']:.1f}
   ⚡ ADX: {result['adx']:.1f}
   🎯 Pattern: {patterns[0] if patterns else 'N/A'}"""

            message_parts.append(stock_info)

        # Summary
        if total_stocks > 10:
            summary = f"\n\n... and {total_stocks - 10} more stocks\n\nFull list saved to file."
        else:
            summary = ""

        message_parts.append(summary)

        # Send main message
        full_message = "\n".join(message_parts)
        self.send_message(full_message)

        # Send detailed list as follow-up if many stocks
        if total_stocks > 10:
            detail_message = f"<b>📋 Full List ({total_stocks} stocks):</b>\n\n"
            for idx, result in enumerate(results, 1):
                symbol = result['symbol'].replace('.NS', '')
                max_strength = max(p['strength'] for p in result['patterns'])
                detail_message += f"{idx}. <b>{symbol}</b> - {max_strength:.0f}%\n"

            # Send in chunks if too long
            if len(detail_message) > 4000:
                # Split into chunks
                lines = detail_message.split('\n')
                chunk = ""
                for line in lines:
                    if len(chunk) + len(line) > 4000:
                        self.send_message(chunk)
                        chunk = ""
                    chunk += line + "\n"
                if chunk:
                    self.send_message(chunk)
            else:
                self.send_message(detail_message)

        return True


def run_stock_scan(stocks_list=None, min_volume_ratio=1.2, max_stocks=50, pattern_strength_min=70):
    """Run the PCS scan on the given stocks"""

    if stocks_list is None:
        stocks_list = COMPLETE_NSE_FO_UNIVERSE

    stocks_list = stocks_list[:max_stocks]

    print(f"\n🚀 Starting scan of {len(stocks_list)} stocks...")
    print(f"Filter criteria:")
    print(f"  - Min Volume Ratio: {min_volume_ratio}x")
    print(f"  - Pattern Strength Min: {pattern_strength_min}%")

    scanner = ProfessionalPCSScanner()
    results = []

    # Create filter config
    filters = {
        'rsi_min': 25,
        'rsi_max': 75,
        'adx_min': 15,
        'ma_support': True,
        'ma_type': 'SMA',
        'ma_tolerance': 5,
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'flat_base': True,
            'bump_and_run': True,
            'rectangle_bottom': True,
            'rectangle_top': False,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'pattern_strength_min': pattern_strength_min,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    }

    for i, symbol in enumerate(stocks_list, 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        progress = (i / len(stocks_list)) * 100
        print(f"[{progress:5.1f}%] Analyzing {clean_symbol}...", end='\r')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, min_volume_ratio)
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

            # Create result entry
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
            }

            results.append(stock_result)
            print(f"{'':80}", end='\r')  # Clear line
            print(f"✅ Found: {clean_symbol} - {len(patterns)} pattern(s)")

        except Exception as e:
            # Silently skip failed stocks
            continue

    print(f"\n✨ Scan complete! Found {len(results)} stocks meeting criteria.\n")
    return results


def save_results_to_file(results, filename=None):
    """Save results to a file"""

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/scan_results_{timestamp}.csv"

    if not results:
        print(f"No results to save")
        return None

    # Prepare data for CSV
    data = []
    for result in results:
        symbol = result['symbol'].replace('.NS', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        patterns = ', '.join([p['type'] for p in result['patterns']])

        data.append({
            'Symbol': symbol,
            'Price': result['current_price'],
            'Volume_Ratio': result['volume_ratio'],
            'RSI': result['rsi'],
            'ADX': result['adx'],
            'Max_Strength': max_strength,
            'Patterns': patterns,
            'Timestamp': datetime.now().isoformat()
        })

    df = pd.DataFrame(data)
    df = df.sort_values('Max_Strength', ascending=False)
    df.to_csv(filename, index=False)

    print(f"📁 Results saved to: {filename}")
    return filename


def main():
    """Main execution function"""

    print(f"""
{'='*60}
🤖 NSE F&O PCS Scanner - Automated Routine
{'='*60}
📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    # Configuration
    min_volume_ratio = float(os.getenv('SCAN_MIN_VOLUME', 1.2))
    max_stocks = int(os.getenv('SCAN_MAX_STOCKS', 100))
    pattern_strength_min = float(os.getenv('SCAN_PATTERN_STRENGTH', 70))

    # Initialize Telegram notifier
    notifier = TelegramNotifier()

    if notifier.is_configured():
        print(f"✅ Telegram configured - will send results")
    else:
        print(f"⚠️  Telegram NOT configured - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    # Run scan
    results = run_stock_scan(
        stocks_list=COMPLETE_NSE_FO_UNIVERSE,
        min_volume_ratio=min_volume_ratio,
        max_stocks=max_stocks,
        pattern_strength_min=pattern_strength_min
    )

    # Save results
    csv_file = save_results_to_file(results)

    # Send to Telegram
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if notifier.is_configured():
        print("📤 Sending results to Telegram...")
        notifier.send_results(results, scan_time)
        print("✅ Telegram notification sent!")
    else:
        print("⚠️  Skipping Telegram notification (not configured)")

    # Print summary
    print(f"""
{'='*60}
📊 Scan Summary
{'='*60}
Total Stocks Scanned: {max_stocks}
Stocks Found: {len(results)}
Timestamp: {scan_time}
Results File: {csv_file}
{'='*60}
""")

    # Display top 5 stocks
    if results:
        print("\n🏆 Top 5 Stocks by Strength:\n")
        sorted_results = sorted(results, key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)
        for idx, result in enumerate(sorted_results[:5], 1):
            symbol = result['symbol'].replace('.NS', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            print(f"{idx}. {symbol:12} - {max_strength:6.1f}% strength")

    return results


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
