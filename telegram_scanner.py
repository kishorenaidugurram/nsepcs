#!/usr/bin/env python3
"""
Standalone scanner script for NSE F&O stocks with Telegram integration
Runs the scanner with default filter criteria and sends results to Telegram
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

# Import scanner from the main app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

class TelegramScanner:
    def __init__(self, bot_token=None, chat_id=None):
        """Initialize telegram scanner with credentials"""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

    def send_telegram_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram credentials not configured")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False

    def send_telegram_document(self, file_data, filename):
        """Send file to Telegram"""
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram credentials not configured")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        files = {'document': (filename, file_data)}
        data = {'chat_id': self.chat_id}

        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error sending document: {e}")
            return False

    def run_scan(self, stocks_limit=None, pattern_strength_min=65):
        """Run the scanner with default settings"""

        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        if stocks_limit:
            stocks_to_scan = stocks_to_scan[:stocks_limit]

        # Default filter configuration
        filters = {
            'stocks_to_scan': stocks_to_scan,
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20,
            'ma_support': True,
            'ma_type': 'EMA',
            'ma_tolerance': 3,
            'min_volume_ratio': 1.0,
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
                'double_top': False,
                'triple_bottom': True,
                'triangle_ascending': True,
                'triangle_descending': False,
                'wedge_rising': True,
                'wedge_falling': False,
                'flag_bullish': True,
                'flag_bearish': False,
                'pennant_bullish': True,
                'rounding_bottom': True,
                'rounding_top_upside': False,
                'inverted_scallop': True
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False,
            'show_news': True,
            'export_results': False,
        }

        print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks...")
        print(f"⏰ Time: {datetime.now(self.ist).strftime('%H:%M IST')}")

        results = []
        scanned_count = 0
        failed_count = 0

        # Send start notification
        start_msg = f"<b>🚀 Scanner Started</b>\n\nScanning {len(stocks_to_scan)} stocks\nFilter: Pattern Strength ≥ {pattern_strength_min}"
        self.send_telegram_message(start_msg)

        for i, symbol in enumerate(stocks_to_scan, 1):
            clean_symbol = symbol.replace('.NS', '')

            try:
                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    failed_count += 1
                    continue

                scanned_count += 1

                # Check volume criteria
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, filters['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, filters)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Store result
                stock_result = {
                    'symbol': clean_symbol,
                    'price': current_price,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'volume_ratio': volume_ratio,
                    'patterns': patterns,
                    'pattern_count': len(patterns),
                    'max_strength': max(p['strength'] for p in patterns)
                }

                results.append(stock_result)
                print(f"✅ [{i}/{len(stocks_to_scan)}] {clean_symbol} - {len(patterns)} pattern(s) found")

            except Exception as e:
                failed_count += 1
                continue

            # Update status every 20 stocks
            if i % 20 == 0:
                status_msg = f"<b>📊 Scan Progress</b>\n\nProcessed: {i}/{len(stocks_to_scan)}\nMatches: {len(results)}"
                self.send_telegram_message(status_msg)

        print(f"\n✅ Scan completed!")
        print(f"Total scanned: {scanned_count}")
        print(f"Failed: {failed_count}")
        print(f"Stocks with patterns: {len(results)}")

        return results

    def format_results_for_telegram(self, results):
        """Format results as Telegram message"""
        if not results:
            return "<b>No stocks found matching the criteria.</b>"

        # Sort by pattern strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        message = f"<b>📈 Scanner Results</b>\n"
        message += f"<i>{datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"
        message += f"<b>Found: {len(results)} stocks</b>\n"
        message += "=" * 40 + "\n\n"

        for i, stock in enumerate(results[:20], 1):  # Top 20 results
            patterns_str = ", ".join([f"{p['type']}({p['strength']:.0f})" for p in stock['patterns'][:2]])

            message += f"{i}. <b>{stock['symbol']}</b>\n"
            message += f"   Price: ₹{stock['price']:.2f}\n"
            message += f"   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
            message += f"   Vol Ratio: {stock['volume_ratio']:.2f}\n"
            message += f"   Patterns: {patterns_str}\n"
            message += f"   Strength: {stock['max_strength']:.0f}/100\n\n"

        if len(results) > 20:
            message += f"... and {len(results) - 20} more stocks\n"

        return message

    def export_to_excel(self, results, filename='scanner_results.xlsx'):
        """Export results to Excel"""
        if not results:
            print("No results to export")
            return None

        # Prepare data
        export_data = []
        for stock in results:
            patterns_str = ", ".join([f"{p['type']}({p['strength']:.0f})" for p in stock['patterns']])

            export_data.append({
                'Symbol': stock['symbol'],
                'Price': f"₹{stock['price']:.2f}",
                'RSI': f"{stock['rsi']:.1f}",
                'ADX': f"{stock['adx']:.1f}",
                'Vol Ratio': f"{stock['volume_ratio']:.2f}",
                'Patterns': patterns_str,
                'Max Strength': f"{stock['max_strength']:.0f}",
                'Pattern Count': stock['pattern_count']
            })

        df = pd.DataFrame(export_data)
        df.to_excel(filename, index=False)
        print(f"✅ Results exported to {filename}")
        return filename

    def run_and_send(self, stocks_limit=50):
        """Run scan and send results to Telegram"""

        # Run scan
        results = self.run_scan(stocks_limit=stocks_limit)

        if not results:
            print("⚠️ No stocks found matching criteria")
            self.send_telegram_message("⚠️ No stocks found matching the filter criteria.")
            return

        # Format and send results message
        message = self.format_results_for_telegram(results)
        print("\n📤 Sending results to Telegram...")
        self.send_telegram_message(message)

        # Export to Excel if results are significant
        if len(results) > 0:
            excel_file = self.export_to_excel(results,
                                            f'/tmp/scanner_results_{datetime.now(self.ist).strftime("%Y%m%d_%H%M%S")}.xlsx')

            if excel_file and os.path.exists(excel_file):
                print("📎 Sending Excel file...")
                with open(excel_file, 'rb') as f:
                    self.send_telegram_document(f.read(), os.path.basename(excel_file))

        # Send completion message
        completion_msg = f"<b>✅ Scan Complete</b>\n\n<b>Summary:</b>\n<b>{len(results)}</b> stocks found with patterns"
        self.send_telegram_message(completion_msg)

        print("\n✅ Results sent to Telegram!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE Stock Scanner with Telegram Integration')
    parser.add_argument('--token', help='Telegram Bot Token', default=None)
    parser.add_argument('--chat-id', help='Telegram Chat ID', default=None)
    parser.add_argument('--limit', type=int, default=None, help='Stock limit (default: all)')
    parser.add_argument('--strength', type=int, default=65, help='Pattern strength minimum (default: 65)')
    parser.add_argument('--no-telegram', action='store_true', help='Run without Telegram integration')

    args = parser.parse_args()

    scanner = TelegramScanner(bot_token=args.token, chat_id=args.chat_id)

    # Run scan
    results = scanner.run_scan(stocks_limit=args.limit, pattern_strength_min=args.strength)

    if not args.no_telegram:
        # Send to Telegram
        if args.token and args.chat_id:
            message = scanner.format_results_for_telegram(results)
            scanner.send_telegram_message(message)

            # Export and send Excel
            if results:
                excel_file = scanner.export_to_excel(results,
                    f'/tmp/scanner_results_{datetime.now(scanner.ist).strftime("%Y%m%d_%H%M%S")}.xlsx')
                if excel_file and os.path.exists(excel_file):
                    with open(excel_file, 'rb') as f:
                        scanner.send_telegram_document(f.read(), os.path.basename(excel_file))
        else:
            print("\n⚠️ Telegram credentials not provided. Use --token and --chat-id flags.")
            print("Or set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")

    # Print results summary
    if results:
        print(f"\n✅ Found {len(results)} stocks")
        for stock in results[:10]:
            print(f"  - {stock['symbol']}: {stock['max_strength']:.0f}/100")
    else:
        print("\n⚠️ No stocks found matching criteria")


if __name__ == "__main__":
    main()
