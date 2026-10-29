#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Bot Version
Scans stocks for PCS patterns and sends results to Telegram
"""

import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import pytz
import requests
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Import from streamlit app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

class TelegramSender:
    """Send messages to Telegram"""
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text, parse_mode='HTML'):
        """Send text message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_document(self, document_path, caption=""):
        """Send document (file) to Telegram"""
        try:
            url = f"{self.api_url}/sendDocument"
            with open(document_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram document: {e}")
            return False


class StandaloneScanner:
    """Standalone scanner without Streamlit UI"""

    def __init__(self, config=None):
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

        # Default configuration with reasonable filters
        self.config = config or self._get_default_config()

    def _get_default_config(self):
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
            'show_charts': False,  # Disabled for headless mode
            'show_news': True,
            'export_results': True,
            'enhancements': {
                'delivery_volume': False,
                'fno_consolidation': False,
                'breakout_pullback': False,
                'enhanced_sr': False
            }
        }

    def scan(self, limit=None, verbose=True):
        """
        Scan stocks and return results

        Args:
            limit: Maximum number of stocks to scan (None = all)
            verbose: Print progress to console

        Returns:
            List of stock results meeting criteria
        """
        stocks = self.config['stocks_to_scan']
        if limit:
            stocks = stocks[:limit]

        results = []

        if verbose:
            print(f"Starting scan of {len(stocks)} stocks...")
            print(f"Filter criteria:")
            print(f"  RSI: {self.config['rsi_min']}-{self.config['rsi_max']}")
            print(f"  ADX Min: {self.config['adx_min']}")
            print(f"  Volume Ratio Min: {self.config['min_volume_ratio']}x")
            print(f"  Pattern Strength Min: {self.config['pattern_strength_min']}%")
            print()

        for i, symbol in enumerate(stocks):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')

                if verbose and (i + 1) % 10 == 0:
                    print(f"Progress: {i + 1}/{len(stocks)} stocks analyzed...")

                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, self.config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, self.config)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create result
                stock_result = {
                    'symbol': symbol,
                    'clean_symbol': clean_symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                }

                results.append(stock_result)

                if verbose:
                    pattern_names = [p['type'] for p in patterns]
                    max_strength = max(p['strength'] for p in patterns)
                    print(f"  ✓ {clean_symbol}: {', '.join(pattern_names)} (Strength: {max_strength:.0f}%)")

            except Exception as e:
                if verbose:
                    print(f"  ✗ {symbol}: Error - {str(e)[:50]}")
                continue

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        if verbose:
            print(f"\n{'='*60}")
            print(f"SCAN COMPLETE: Found {len(results)} stocks with patterns")
            print(f"{'='*60}\n")

        return results

    def format_telegram_message(self, results, include_full_details=True):
        """
        Format results for Telegram message

        Args:
            results: List of stock results
            include_full_details: Include detailed info per stock

        Returns:
            Formatted message string for Telegram
        """
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)

        if not results:
            return "🔍 <b>NSE PCS Scanner Report</b>\n\n❌ No stocks found matching the filter criteria.\n\nTry adjusting:\n• Lower pattern strength threshold\n• Increase RSI range\n• Lower volume ratio requirement"

        # Header
        msg = f"🔍 <b>NSE PCS Scanner Report</b>\n"
        msg += f"📅 <i>{current_time.strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"

        # Summary
        total_patterns = sum(len(r['patterns']) for r in results)
        msg += f"<b>📊 Summary:</b>\n"
        msg += f"  • Stocks Found: <b>{len(results)}</b>\n"
        msg += f"  • Total Patterns: <b>{total_patterns}</b>\n\n"

        msg += f"<b>📈 Top Stocks:</b>\n"
        msg += "─" * 40 + "\n\n"

        # Show top 10 results
        for i, result in enumerate(results[:10], 1):
            symbol = result['clean_symbol']
            price = result['current_price']
            patterns = result['patterns']

            # Get best pattern
            best_pattern = max(patterns, key=lambda p: p['strength'])
            pattern_type = best_pattern['type']
            strength = best_pattern['strength']

            msg += f"{i}. <b>{symbol}</b>\n"
            msg += f"   Price: ₹{price:.2f}\n"
            msg += f"   Pattern: {pattern_type}\n"
            msg += f"   Strength: {strength:.0f}%\n"
            msg += f"   RSI: {result['rsi']:.1f}\n"

            if len(patterns) > 1:
                msg += f"   Also: {', '.join(p['type'][:15] for p in patterns[1:3])}\n"

            msg += "\n"

        if len(results) > 10:
            msg += f"\n<i>... and {len(results) - 10} more stocks</i>\n"

        msg += "\n" + "─" * 40 + "\n"
        msg += f"<i>Scan completed with filter criteria:</i>\n"
        msg += f"RSI: {self.config['rsi_min']}-{self.config['rsi_max']} | "
        msg += f"ADX: {self.config['adx_min']}+ | "
        msg += f"Vol: {self.config['min_volume_ratio']}x"

        return msg

    def export_to_csv(self, results, filename=None):
        """Export results to CSV file"""
        if not filename:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime("%Y%m%d_%H%M%S")
            filename = f"/tmp/pcs_scan_results_{timestamp}.csv"

        data = []
        for result in results:
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])
            data.append({
                'Symbol': result['clean_symbol'],
                'Price': result['current_price'],
                'RSI': result['rsi'],
                'ADX': result['adx'],
                'Volume_Ratio': result['volume_ratio'],
                'Pattern': best_pattern['type'],
                'Strength': best_pattern['strength'],
                'Confidence': best_pattern.get('confidence', 'N/A'),
                'Pattern_Count': len(result['patterns'])
            })

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)

        print(f"Results exported to: {filename}")
        return filename


def main():
    """Main execution"""

    # Get Telegram credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()

    if not bot_token or not chat_id:
        print("ERROR: Telegram credentials not found!")
        print("\nPlease set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        sys.exit(1)

    print("🚀 NSE PCS Scanner - Telegram Edition")
    print("=" * 60)

    # Initialize scanner
    scanner = StandaloneScanner()

    # Run scan
    results = scanner.scan(limit=None, verbose=True)

    # Initialize Telegram sender
    telegram = TelegramSender(bot_token, chat_id)

    # Send results to Telegram
    message = scanner.format_telegram_message(results)

    print("\n📨 Sending results to Telegram...")
    success = telegram.send_message(message)

    if success:
        print("✅ Message sent successfully!")
    else:
        print("❌ Failed to send message. Check Telegram credentials.")

    # Export results to CSV if any found
    if results:
        csv_file = scanner.export_to_csv(results)
        print(f"💾 CSV exported: {csv_file}")

        # Try to send CSV file to Telegram
        print("📎 Sending CSV file to Telegram...")
        file_success = telegram.send_document(csv_file, caption="📊 PCS Scanner Results (CSV)")
        if file_success:
            print("✅ CSV file sent!")
        else:
            print("⚠️  Could not send CSV file (but scan results message was sent)")

    print("\n" + "=" * 60)
    print("✨ Scan completed!")

    return len(results)


if __name__ == "__main__":
    try:
        stock_count = main()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
