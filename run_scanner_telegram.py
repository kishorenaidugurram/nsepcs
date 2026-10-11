#!/usr/bin/env python3
"""
Standalone Scanner - Runs stock analysis and sends results to Telegram
This script extracts the core scanner logic and runs it without the Streamlit UI
"""

import sys
import os
import asyncio
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Import from streamlit_app
sys.path.insert(0, os.path.dirname(__file__))

try:
    from streamlit_app import (
        ProfessionalPCSScanner,
        COMPLETE_NSE_FO_UNIVERSE
    )
except ImportError as e:
    print(f"Error importing from streamlit_app: {e}")
    sys.exit(1)

# Try to import telegram
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️  python-telegram-bot not installed. Installing...")
    os.system("pip install -q python-telegram-bot")
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        TELEGRAM_AVAILABLE = True
    except ImportError:
        TELEGRAM_AVAILABLE = False
        print("⚠️  Telegram integration unavailable - results will be saved to file instead")


class StandaloneScanner:
    """Standalone version of the scanner without Streamlit UI"""

    def __init__(self):
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')
        self.results = []

    def get_default_filters(self):
        """Get default filter configuration"""
        return {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
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
                'three_rising_valleys': False,
                'rounding_bottom': True,
                'rounding_top_upside': False,
                'inverted_scallop': False,
            },
            'pattern_priority': 'High Success Rate Only (>80%)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
        }

    def scan_stocks(self, max_stocks=None):
        """Scan stocks with default filters"""
        config = self.get_default_filters()
        stocks_to_scan = config['stocks_to_scan']

        if max_stocks:
            stocks_to_scan = stocks_to_scan[:max_stocks]

        print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks")
        print(f"📊 Filters: RSI {config['rsi_min']}-{config['rsi_max']}, ADX>{config['adx_min']}, Strength>{config['pattern_strength_min']}%")
        print(f"⏰ Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("-" * 80)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for symbol in stocks_to_scan:
                future = executor.submit(self._analyze_stock, symbol, config)
                futures[future] = symbol

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        print(f"✅ [{completed}/{len(stocks_to_scan)}] {symbol}: {len(result['patterns'])} patterns")
                    else:
                        print(f"⊘ [{completed}/{len(stocks_to_scan)}] {symbol}: No patterns")
                except Exception as e:
                    print(f"❌ [{completed}/{len(stocks_to_scan)}] {symbol}: {str(e)[:50]}")

        # Sort by pattern strength
        self.results.sort(key=lambda x: x.get('pattern_strength', 0), reverse=True)

        print("-" * 80)
        print(f"\n✅ SCAN COMPLETE: Found {len(self.results)} stocks with patterns")

        return self.results

    def _analyze_stock(self, symbol, config):
        """Analyze a single stock"""
        try:
            data = self.scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            patterns = self.scanner.detect_patterns(data, symbol, config)

            if patterns:
                # Get current price
                current_price = data['Close'].iloc[-1]
                return {
                    'symbol': symbol,
                    'patterns': patterns,
                    'current_price': current_price,
                    'pattern_strength': patterns[0].get('strength', 0) if patterns else 0,
                    'data': data
                }
            return None

        except Exception as e:
            return None

    def format_telegram_message(self):
        """Format results for Telegram"""
        if not self.results:
            return "📊 **NSE Scanner Report**\n\nNo stocks found meeting criteria today."

        message = "📊 **NSE PCS Scanner Report**\n"
        message += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n"
        message += f"📈 Found: {len(self.results)} stocks\n"
        message += "=" * 50 + "\n\n"

        for i, result in enumerate(self.results[:20], 1):  # Top 20 results
            symbol = result['symbol'].replace('.NS', '')
            strength = int(result.get('pattern_strength', 0))
            price = result.get('current_price', 0)
            patterns = [p.get('name', 'Unknown') for p in result.get('patterns', [])]

            message += f"{i}. **{symbol}** - ₹{price:.2f}\n"
            message += f"   💪 Strength: {strength}%\n"
            message += f"   📍 Patterns: {', '.join(patterns[:2])}\n"
            message += "\n"

        return message

    def format_text_report(self):
        """Format results as text report"""
        if not self.results:
            return "No stocks found meeting criteria today."

        report = "NSE PCS SCANNER REPORT\n"
        report += f"Report Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        report += f"Total Stocks Scanned: {len(COMPLETE_NSE_FO_UNIVERSE)}\n"
        report += f"Stocks with Patterns: {len(self.results)}\n"
        report += "=" * 80 + "\n\n"

        for i, result in enumerate(self.results, 1):
            symbol = result['symbol'].replace('.NS', '')
            strength = int(result.get('pattern_strength', 0))
            price = result.get('current_price', 0)
            patterns = [p.get('name', 'Unknown') for p in result.get('patterns', [])]

            report += f"{i}. {symbol}\n"
            report += f"   Price: ₹{price:.2f}\n"
            report += f"   Strength: {strength}%\n"
            report += f"   Patterns: {', '.join(patterns)}\n"
            report += "\n"

        return report


async def send_to_telegram(message, chat_id, bot_token):
    """Send message to Telegram"""
    if not TELEGRAM_AVAILABLE:
        print("⚠️  Telegram not available")
        return False

    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
        print("✅ Message sent to Telegram successfully!")
        return True
    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False


def main():
    """Main execution"""
    # Get configuration
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    max_stocks = int(os.getenv('SCAN_LIMIT', '219'))  # Default: scan all

    print("\n" + "=" * 80)
    print("NSE F&O PCS SCANNER - AUTOMATED RUN")
    print("=" * 80)

    # Run scanner
    scanner = StandaloneScanner()
    results = scanner.scan_stocks(max_stocks=max_stocks)

    # Generate reports
    text_report = scanner.format_text_report()
    telegram_message = scanner.format_telegram_message()

    # Save text report
    report_filename = f"/tmp/nse_scan_{datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write(text_report)
    print(f"\n📄 Report saved: {report_filename}")

    # Send to Telegram if configured
    if telegram_token and telegram_chat_id:
        print("\n📱 Attempting to send to Telegram...")
        success = asyncio.run(send_to_telegram(
            telegram_message,
            telegram_chat_id,
            telegram_token
        ))
        if not success and results:
            print("⚠️  Failed to send via Telegram, but results saved locally")
    else:
        if not telegram_token:
            print("\n⚠️  TELEGRAM_BOT_TOKEN not set")
        if not telegram_chat_id:
            print("⚠️  TELEGRAM_CHAT_ID not set")
        print("   Set these environment variables to enable Telegram notifications")
        print(f"   Results available in: {report_filename}")

    # Print summary
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(results)} stocks found meeting criteria")
    if results:
        print("\nTop 5 Results:")
        for i, result in enumerate(results[:5], 1):
            symbol = result['symbol'].replace('.NS', '')
            strength = int(result.get('pattern_strength', 0))
            print(f"  {i}. {symbol} (Strength: {strength}%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
