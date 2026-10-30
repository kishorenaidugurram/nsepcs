#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner with Telegram Integration
Runs the scanner and sends results to Telegram
"""

import sys
import os
import json
from datetime import datetime
import traceback
from pathlib import Path

# Add repo to path
sys.path.insert(0, '/home/user/nsepcs')

# Import the scanner class from streamlit_app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("Installing python-telegram-bot...")
    os.system("pip install python-telegram-bot -q")
    from telegram import Bot
    from telegram.error import TelegramError


class TelegramStockScanner:
    def __init__(self, bot_token=None, chat_id=None):
        """Initialize scanner with Telegram credentials"""

        # Try to get credentials from environment
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram credentials not found!")
            print("Please set environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\nOr pass them as arguments to the script")
            sys.exit(1)

        self.bot = Bot(token=self.bot_token)
        self.scanner = ProfessionalPCSScanner()

    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    def run_scan(self, stocks_limit=50, pattern_strength_min=70):
        """Run the scanner with default filters"""

        print(f"🚀 Starting scan of {stocks_limit} stocks...")
        self.send_message(f"<b>🚀 NSE F&O Stock Scanner Started</b>\n<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>")

        # Configure scanner with default filters
        filters = {
            'rsi_min': 30,
            'rsi_max': 85,
            'adx_min': 15,
            'ma_support': False,
            'ma_tolerance': 5,
            'min_volume_ratio': 1.0,
            'pattern_strength_min': pattern_strength_min,
            'volume_breakout_ratio': 2.0,
            'lookback_days': 20,
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
                'inverted_scallop': True,
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False
        }

        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:stocks_limit]
        results = []

        for i, symbol in enumerate(stocks_to_scan):
            try:
                print(f"  [{i+1}/{len(stocks_to_scan)}] Analyzing {symbol}...", end='\r')

                # Fetch stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, _ = self.scanner.check_volume_criteria(data, filters['min_volume_ratio'])
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, filters)
                if not patterns:
                    continue

                # Get stock metrics
                current_price = data['Close'].iloc[-1]
                rsi = data['RSI'].iloc[-1]
                adx = data['ADX'].iloc[-1]

                # Prepare result
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'adx': adx,
                    'volume_ratio': volume_ratio,
                    'patterns': patterns,
                    'timestamp': datetime.now().isoformat()
                }

                results.append(result)

            except Exception as e:
                print(f"  Error analyzing {symbol}: {str(e)}")
                continue

        print(f"\n✅ Scan complete! Found {len(results)} stocks with patterns")

        return results

    def format_results(self, results):
        """Format scan results for Telegram"""

        if not results:
            return "<b>No stocks found matching criteria</b>"

        # Sort by max pattern strength
        results_sorted = sorted(
            results,
            key=lambda x: max([p['strength'] for p in x['patterns']], default=0),
            reverse=True
        )

        message = f"<b>📊 Scan Results - {len(results)} Stocks Found</b>\n\n"

        for idx, result in enumerate(results_sorted[:20], 1):  # Limit to top 20
            symbol_clean = result['symbol'].replace('.NS', '')
            max_strength = max([p['strength'] for p in result['patterns']], default=0)
            pattern_types = ', '.join([p['type'][:15] for p in result['patterns'][:2]])

            message += f"<b>{idx}. {symbol_clean}</b>\n"
            message += f"   💰 Price: ₹{result['current_price']:.2f}\n"
            message += f"   📈 Strength: {max_strength:.0f}%\n"
            message += f"   📊 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
            message += f"   🎯 Patterns: {pattern_types}\n\n"

        return message

    def send_results(self, results):
        """Send scan results to Telegram"""

        if not results:
            message = "⚠️ <b>No stocks found</b> matching the filter criteria.\n\nTry adjusting:\n• Lower pattern strength\n• Increase RSI range\n• Reduce volume ratio"
            self.send_message(message)
            return

        # Send summary
        message = self.format_results(results)

        # Split into chunks if too long (Telegram limit is 4096 characters)
        chunk_size = 3500
        for i in range(0, len(message), chunk_size):
            chunk = message[i:i+chunk_size]
            self.send_message(chunk)

        # Send completion message
        summary = f"\n✅ <b>Scan Complete</b>\n"
        summary += f"Total Stocks: {len(results)}\n"
        summary += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
        self.send_message(summary)


def main():
    """Main execution"""

    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O Stock Scanner with Telegram Integration')
    parser.add_argument('--token', help='Telegram Bot Token')
    parser.add_argument('--chat-id', help='Telegram Chat ID')
    parser.add_argument('--limit', type=int, default=50, help='Number of stocks to scan')
    parser.add_argument('--strength', type=int, default=70, help='Minimum pattern strength')

    args = parser.parse_args()

    try:
        scanner = TelegramStockScanner(bot_token=args.token, chat_id=args.chat_id)
        results = scanner.run_scan(stocks_limit=args.limit, pattern_strength_min=args.strength)
        scanner.send_results(results)

        # Save results to file as well
        results_file = f'/tmp/scan_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📁 Results saved to: {results_file}")

    except KeyboardInterrupt:
        print("\n⏹️  Scan interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
