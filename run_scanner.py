#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner with Telegram Integration
Runs the stock scanning logic without Streamlit
"""

import os
import sys
import json
import warnings
from datetime import datetime
import pytz
from typing import List, Dict, Tuple
import requests

# Import scanner from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    create_excel_stock_list
)

import pandas as pd
import numpy as np
import yfinance as yf

warnings.filterwarnings('ignore')

class TelegramSender:
    """Send messages to Telegram"""

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.token and self.chat_id)

        if self.enabled:
            self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message: str) -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
            return False

        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
            return False

def run_stock_scan(
    universe: str = 'fno',
    max_stocks: int = None,
    rsi_min: int = 30,
    rsi_max: int = 75,
    adx_min: int = 20,
    min_volume_ratio: float = 1.2,
    pattern_strength_min: int = 65
) -> Tuple[List[Dict], str]:
    """
    Run the stock scanner with specified filters

    Args:
        universe: 'fno' for F&O stocks, 'non-fno' for non-F&O stocks
        max_stocks: Maximum stocks to scan (None = all)
        rsi_min: Minimum RSI value
        rsi_max: Maximum RSI value
        adx_min: Minimum ADX value
        min_volume_ratio: Minimum volume ratio
        pattern_strength_min: Minimum pattern strength

    Returns:
        Tuple of (results list, summary string)
    """

    # Select universe
    if universe.lower() == 'fno':
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        universe_name = "NSE F&O Stocks"
    else:
        from streamlit_app import get_nse_non_fno_stocks
        stocks_to_scan = get_nse_non_fno_stocks()
        universe_name = "NSE Non-F&O Stocks"

    # Limit stocks if specified
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"\n📊 Starting scan of {len(stocks_to_scan)} {universe_name}")
    print(f"⚙️  Filters: RSI({rsi_min}-{rsi_max}) | ADX(>{adx_min}) | Volume(>{min_volume_ratio}x) | Strength(>{pattern_strength_min}%)")
    print("-" * 80)

    scanner = ProfessionalPCSScanner()
    results = []

    # Build filter config
    config = {
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'adx_min': adx_min,
        'min_volume_ratio': min_volume_ratio,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': pattern_strength_min,
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
        'analysis_mode': 'Daily Only (V6.0 Style)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': False,
        'pattern_filters': {}
    }

    for i, symbol in enumerate(stocks_to_scan):
        progress = (i + 1) / len(stocks_to_scan)
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        # Progress indicator
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r[{bar}] {i+1}/{len(stocks_to_scan)} - {clean_symbol}", end='', flush=True)

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Store result
            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'max_strength': max(p['strength'] for p in patterns) if patterns else 0,
                'pattern_types': [p['type'] for p in patterns],
                'data': data
            }

            results.append(stock_result)

        except Exception as e:
            continue

    # Clear progress line
    print()

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    # Generate summary
    if results:
        total_patterns = sum(len(r['patterns']) for r in results)
        avg_strength = np.mean([r['max_strength'] for r in results])
        current_day_breakouts = sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])
        high_confidence = sum(1 for r in results if r['max_strength'] >= 85)

        summary = f"""
✅ SCAN COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Universe: {universe_name}
🎯 Stocks Qualified: {len(results)}/{len(stocks_to_scan)}
🔥 Current Day Breakouts: {current_day_breakouts}
💪 Average Strength: {avg_strength:.1f}%
🏆 High Confidence (>85%): {high_confidence}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    else:
        summary = "\n❌ No stocks matched the criteria\n"

    print(summary)

    return results, summary

def format_telegram_message(results: List[Dict], max_results: int = 10) -> str:
    """Format results for Telegram message"""

    if not results:
        return "❌ <b>Stock Scanner - No Results</b>\n\nNo stocks matched the filter criteria."

    # Take top results
    top_results = results[:max_results]

    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.now(ist).strftime('%d-%b %H:%M IST')

    message = f"""<b>📊 Stock Scanner Results</b>
<code>Time: {scan_time}
Found: {len(results)} stocks (showing top {len(top_results)})</code>

"""

    for idx, result in enumerate(top_results, 1):
        symbol = result['clean_symbol']
        price = result['current_price']
        vol = result['volume_ratio']
        rsi = result['rsi']
        strength = result['max_strength']
        confidence = '🟢' if strength >= 85 else '🟡' if strength >= 70 else '🔴'

        message += f"""<b>{idx}. {symbol}</b>
  Price: ₹{price:.2f} | Vol: {vol:.1f}x | RSI: {rsi:.0f}
  Strength: {strength:.0f}% {confidence}
  Patterns: {', '.join(set(result['pattern_types'])[:2])}

"""

    if len(results) > max_results:
        message += f"\n... and {len(results) - max_results} more stocks"

    return message

def main():
    """Main execution"""

    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O Stock Scanner')
    parser.add_argument('--universe', choices=['fno', 'non-fno'], default='fno',
                        help='Stock universe to scan (default: fno)')
    parser.add_argument('--max-stocks', type=int, default=None,
                        help='Maximum number of stocks to scan (default: all)')
    parser.add_argument('--rsi-min', type=int, default=30,
                        help='Minimum RSI value (default: 30)')
    parser.add_argument('--rsi-max', type=int, default=75,
                        help='Maximum RSI value (default: 75)')
    parser.add_argument('--adx-min', type=int, default=20,
                        help='Minimum ADX value (default: 20)')
    parser.add_argument('--volume-ratio', type=float, default=1.2,
                        help='Minimum volume ratio (default: 1.2)')
    parser.add_argument('--strength-min', type=int, default=65,
                        help='Minimum pattern strength (default: 65)')
    parser.add_argument('--telegram-token', default=None,
                        help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)')
    parser.add_argument('--telegram-chat-id', default=None,
                        help='Telegram chat ID (or set TELEGRAM_CHAT_ID env var)')
    parser.add_argument('--no-telegram', action='store_true',
                        help='Skip Telegram sending')
    parser.add_argument('--export-excel', action='store_true',
                        help='Export results to Excel file')

    args = parser.parse_args()

    # Run scanner
    results, summary = run_stock_scan(
        universe=args.universe,
        max_stocks=args.max_stocks,
        rsi_min=args.rsi_min,
        rsi_max=args.rsi_max,
        adx_min=args.adx_min,
        min_volume_ratio=args.volume_ratio,
        pattern_strength_min=args.strength_min
    )

    # Export to Excel if requested
    if args.export_excel and results:
        try:
            excel_file = create_excel_stock_list(results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'/home/user/nsepcs/scan_results_{timestamp}.xlsx'
            with open(filename, 'wb') as f:
                f.write(excel_file)
            print(f"✅ Excel file exported: {filename}")
        except Exception as e:
            print(f"❌ Excel export failed: {str(e)}")

    # Send to Telegram
    if not args.no_telegram:
        telegram = TelegramSender(args.telegram_token, args.telegram_chat_id)

        if telegram.enabled:
            message = format_telegram_message(results, max_results=10)
            if telegram.send_message(message):
                print("✅ Message sent to Telegram!")
            else:
                print("❌ Failed to send Telegram message")
        else:
            print("\n⚠️  Telegram not configured")
            print("To enable Telegram notifications, set:")
            print("  export TELEGRAM_BOT_TOKEN='your_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")

    # Print results to console
    print("\n" + "=" * 80)
    print("TOP QUALIFIED STOCKS (sorted by pattern strength)")
    print("=" * 80)

    for idx, result in enumerate(results[:10], 1):
        print(f"\n{idx}. {result['clean_symbol']}")
        print(f"   Price: ₹{result['current_price']:.2f}")
        print(f"   Volume Ratio: {result['volume_ratio']:.2f}x")
        print(f"   RSI: {result['rsi']:.1f}")
        print(f"   ADX: {result['adx']:.1f}")
        print(f"   Pattern Strength: {result['max_strength']:.0f}%")
        print(f"   Patterns: {', '.join(result['pattern_types'])}")

    if len(results) > 10:
        print(f"\n... and {len(results) - 10} more stocks")

    # Save results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f'/home/user/nsepcs/scan_results_{timestamp}.json'

    json_results = []
    for result in results:
        json_results.append({
            'symbol': result['clean_symbol'],
            'price': float(result['current_price']),
            'volume_ratio': float(result['volume_ratio']),
            'rsi': float(result['rsi']),
            'adx': float(result['adx']),
            'pattern_strength': float(result['max_strength']),
            'patterns': result['pattern_types']
        })

    with open(json_file, 'w') as f:
        json.dump(json_results, f, indent=2)

    print(f"\n✅ Results saved to: {json_file}")

    return len(results) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
