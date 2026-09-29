#!/usr/bin/env python3
"""
Standalone NSE PCS Scanner with Telegram Integration
Runs the stock screening and sends results to Telegram
"""

import sys
import os
import json
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to path to import from streamlit_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from streamlit app (without the UI)
import pandas as pd
import yfinance as yf
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

# Try to import telegram library
try:
    import requests
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("Telegram library not available. Install with: pip install requests")


class TelegramScanner:
    """Telegram-enabled stock scanner"""

    def __init__(self, bot_token=None, chat_id=None):
        """
        Initialize the scanner with Telegram credentials

        Args:
            bot_token: Telegram bot token (or env variable TELEGRAM_BOT_TOKEN)
            chat_id: Telegram chat ID to send messages to (or env variable TELEGRAM_CHAT_ID)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

        if self.bot_token and self.chat_id:
            self.telegram_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            logger.info("Telegram integration enabled")
        else:
            logger.warning("Telegram credentials not provided. Results will be displayed in console only.")

    def send_to_telegram(self, message, parse_mode='Markdown'):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Cannot send to Telegram: credentials not provided")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(self.telegram_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def scan_stocks(self, filters=None):
        """
        Scan stocks with given filters

        Args:
            filters: Dictionary with filter settings

        Returns:
            List of stocks meeting criteria
        """
        if filters is None:
            filters = self._get_default_filters()

        results = []
        stocks = filters.get('stocks_to_scan', COMPLETE_NSE_FO_UNIVERSE[:100])  # Default to first 100

        logger.info(f"Starting scan of {len(stocks)} stocks with filters: {filters}")

        # Send initial notification
        self.send_to_telegram(
            f"🚀 *NSE Stock Scanner Started*\n"
            f"Scanning {len(stocks)} stocks at {datetime.now(self.ist).strftime('%H:%M %Z')}\n"
            f"Pattern Strength: {filters['pattern_strength_min']}%+"
        )

        # Scan stocks
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._scan_stock, symbol, filters): symbol
                for symbol in stocks
            }

            completed = 0
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    completed += 1
                    if completed % 10 == 0:
                        logger.info(f"Progress: {completed}/{len(stocks)} stocks analyzed")
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    completed += 1

        logger.info(f"Scan complete. Found {len(results)} stocks meeting criteria.")
        return results

    def _scan_stock(self, symbol, filters):
        """Scan a single stock"""
        try:
            # Get stock data
            data = self.scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Check volume criteria
            volume_ok, volume_ratio, _ = self.scanner.check_volume_criteria(
                data, filters.get('min_volume_ratio', 1.2)
            )
            if not volume_ok:
                return None

            # Detect patterns
            patterns = self.scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_date = data.index[-1].strftime('%Y-%m-%d')

            # Calculate max strength
            max_strength = max(p['strength'] for p in patterns)
            if max_strength < filters.get('pattern_strength_min', 65):
                return None

            return {
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'max_strength': max_strength,
                'date': current_date,
                'data': data
            }

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    def _get_default_filters(self):
        """Get default filter configuration"""
        return {
            'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:100],  # First 100 stocks
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
            'show_charts': False,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False,
            }
        }

    def format_results_for_telegram(self, results):
        """Format scan results for Telegram message"""
        if not results:
            return "❌ No stocks found meeting the filter criteria."

        # Group by confidence level
        high_conf = [r for r in results if r['max_strength'] >= 85]
        med_conf = [r for r in results if 70 <= r['max_strength'] < 85]
        low_conf = [r for r in results if r['max_strength'] < 70]

        message = f"✅ *NSE Stock Scanner Results*\n"
        message += f"Time: {datetime.now(self.ist).strftime('%H:%M %Z')}\n"
        message += f"Total Found: {len(results)}\n\n"

        # High confidence
        if high_conf:
            message += f"🟢 *HIGH CONFIDENCE ({len(high_conf)})*\n"
            for r in sorted(high_conf, key=lambda x: x['max_strength'], reverse=True)[:10]:
                message += (
                    f"  {r['symbol']}: {r['max_strength']:.0f}% | "
                    f"₹{r['price']:.2f} | RSI:{r['rsi']:.0f} | Vol:{r['volume_ratio']:.1f}x\n"
                )
            message += "\n"

        # Medium confidence
        if med_conf:
            message += f"🟡 *MEDIUM CONFIDENCE ({len(med_conf)})*\n"
            for r in sorted(med_conf, key=lambda x: x['max_strength'], reverse=True)[:5]:
                message += (
                    f"  {r['symbol']}: {r['max_strength']:.0f}% | "
                    f"₹{r['price']:.2f} | RSI:{r['rsi']:.0f}\n"
                )
            message += "\n"

        if low_conf:
            message += f"🔴 *LOWER CONFIDENCE ({len(low_conf)})*\n"

        # Excel export
        message += f"\n📊 *Full List* (See Excel export for details)"

        return message

    def export_to_excel(self, results, filename=None):
        """Export results to Excel"""
        if not results:
            logger.warning("No results to export")
            return None

        if filename is None:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
            filename = f"stock_scan_results_{timestamp}.xlsx"

        # Create summary table
        summary_data = []
        for result in results:
            summary_data.append({
                'Symbol': result['symbol'],
                'Price': f"₹{result['price']:.2f}",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Volume': f"{result['volume_ratio']:.1f}x",
                'Strength': f"{result['max_strength']:.0f}%",
                'Patterns': ', '.join([p['type'] for p in result['patterns'][:2]]),
                'Date': result['date']
            })

        df = pd.DataFrame(summary_data)
        df.to_excel(filename, index=False)
        logger.info(f"Results exported to {filename}")
        return filename

    def run_full_scan(self, filters=None):
        """Run complete scan and send results to Telegram"""
        # Scan stocks
        results = self.scan_stocks(filters)

        # Format message
        message = self.format_results_for_telegram(results)

        # Send to Telegram
        if self.bot_token and self.chat_id:
            self.send_to_telegram(message)
        else:
            logger.info("Scan Results:\n" + message)

        # Export to Excel
        excel_file = self.export_to_excel(results)

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"SCAN COMPLETE - Found {len(results)} stocks")
        logger.info(f"Results exported to: {excel_file}")
        logger.info(f"{'='*50}")

        return results, excel_file


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE Stock Scanner with Telegram Integration')
    parser.add_argument('--bot-token', help='Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)')
    parser.add_argument('--chat-id', help='Telegram chat ID (or set TELEGRAM_CHAT_ID env var)')
    parser.add_argument('--stocks', type=int, default=100, help='Number of stocks to scan (default: 100)')
    parser.add_argument('--strength', type=int, default=65, help='Minimum pattern strength (default: 65)')
    parser.add_argument('--no-telegram', action='store_true', help='Skip Telegram, just export Excel')

    args = parser.parse_args()

    # Initialize scanner
    scanner = TelegramScanner(
        bot_token=args.bot_token,
        chat_id=args.chat_id
    )

    # Get filters
    filters = scanner._get_default_filters()
    filters['stocks_to_scan'] = COMPLETE_NSE_FO_UNIVERSE[:args.stocks]
    filters['pattern_strength_min'] = args.strength

    if args.no_telegram:
        scanner.bot_token = None
        scanner.chat_id = None

    # Run scan
    results, excel_file = scanner.run_full_scan(filters)

    return results


if __name__ == "__main__":
    main()
