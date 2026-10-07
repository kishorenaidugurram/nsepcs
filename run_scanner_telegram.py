#!/usr/bin/env python3
"""
Standalone scanner script that runs the stock scanner and sends results to Telegram.
This script is designed to run as a scheduled task without Streamlit.
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import pytz
import warnings
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

warnings.filterwarnings('ignore')

# Add repo to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner class from streamlit app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE, fetch_stock_data_cached

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

class StandaloneScanner:
    """Standalone scanner that doesn't require Streamlit"""

    def __init__(self):
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

    def create_default_filters(self):
        """Create default filter configuration (matches UI defaults)"""
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
            'show_charts': False,
            'show_news': True,
            'export_results': False,
        }

    def scan_stocks(self, config, max_workers=4):
        """Scan stocks with given configuration"""
        results = []
        stocks = config['stocks_to_scan']

        print(f"[{datetime.now(self.ist).strftime('%H:%M:%S')}] Starting scan of {len(stocks)} stocks...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._scan_single_stock, symbol, config): symbol
                for symbol in stocks
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"[{completed}/{len(stocks)}] ✓ {symbol.replace('.NS', '')} - Found patterns")
                    else:
                        print(f"[{completed}/{len(stocks)}] - {symbol.replace('.NS', '')}")
                except Exception as e:
                    print(f"[{completed}/{len(stocks)}] ✗ {symbol.replace('.NS', '')} - Error: {str(e)[:50]}")

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        print(f"\n✅ Scan complete! Found {len(results)} stocks meeting criteria.\n")
        return results

    def _scan_single_stock(self, symbol, config):
        """Scan a single stock"""
        try:
            # Fetch stock data
            data = fetch_stock_data_cached(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Get technical indicators
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            ema_20 = data['EMA_20'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]

            # Apply basic filters
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                return None

            if current_adx < config['adx_min']:
                return None

            if config['ma_support']:
                if config['ma_type'] == 'SMA':
                    if current_price < sma_20 * (1 - config['ma_tolerance']/100):
                        return None
                else:
                    if current_price < ema_20 * (1 - config['ma_tolerance']/100):
                        return None

            # Detect patterns
            patterns = self.scanner.detect_patterns(data, symbol, config)

            if not patterns:
                return None

            # Get weekly data for validation
            try:
                daily_data = fetch_stock_data_cached(symbol, period="6mo")
                if daily_data is not None and len(daily_data) >= 50:
                    weekly_data = daily_data.resample('W-FRI').agg({
                        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                    }).dropna()
                else:
                    weekly_data = None
            except:
                weekly_data = None

            # Get volume info
            volume_met, volume_ratio, volume_details = self.scanner.check_volume_criteria(data, min_ratio=config['min_volume_ratio'])

            return {
                'symbol': symbol,
                'current_price': current_price,
                'patterns': patterns,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'data': data,
                'weekly_data': weekly_data
            }

        except Exception as e:
            return None

    def send_to_telegram(self, results):
        """Send scan results to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️  Telegram not configured. Skipping Telegram notification.")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable.")
            return False

        try:
            # Format message
            timestamp = datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')
            message = f"📊 *NSE F&O PCS Scanner Results*\n"
            message += f"🕐 {timestamp}\n"
            message += f"✅ Found: *{len(results)} stocks*\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━\n"

            # Add top results (limit to 10 due to message length)
            for i, result in enumerate(results[:10], 1):
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                max_strength = max(p['strength'] for p in result['patterns'])

                pattern_types = set(p['type'] for p in result['patterns'])
                pattern_str = ', '.join(list(pattern_types)[:2])

                message += f"\n{i}. *{symbol}* - ₹{price:.2f}\n"
                message += f"   💪 Strength: {max_strength:.0f}%\n"
                message += f"   📈 Patterns: {pattern_str}\n"

            if len(results) > 10:
                message += f"\n... and {len(results) - 10} more stocks\n"

            message += "\n━━━━━━━━━━━━━━━━━━━━━\n"
            message += "🚀 Full report available in web app"

            # Send to Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                print("✅ Results sent to Telegram successfully!")
                return True
            else:
                print(f"❌ Failed to send to Telegram: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False

    def save_results_to_csv(self, results, filename=None):
        """Save results to CSV"""
        if not results:
            print("No results to save.")
            return None

        if filename is None:
            timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/claude-0/-home-user-nsepcs/017d6679-e0bc-5a5b-9f16-933803b74eb9/scratchpad/scanner_results_{timestamp}.csv"

        # Create output directory if needed
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Prepare data
        data = []
        for result in results:
            symbol = result['symbol'].replace('.NS', '')
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            volume_ratio = result['volume_ratio']

            # Get best pattern
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])

            data.append({
                'Symbol': symbol,
                'Price': f"₹{price:.2f}",
                'RSI': f"{rsi:.1f}",
                'ADX': f"{adx:.1f}",
                'Best_Pattern': best_pattern['type'],
                'Strength': f"{best_pattern['strength']:.0f}%",
                'Volume_Ratio': f"{volume_ratio:.2f}x",
                'Confidence': best_pattern.get('confidence', 'MEDIUM'),
                'Timestamp': datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S IST')
            })

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"📁 Results saved to: {filename}")
        return filename

    def print_summary(self, results):
        """Print a nice summary"""
        if not results:
            print("❌ No stocks found matching the criteria.")
            return

        print("\n" + "="*60)
        print("📊 SCAN RESULTS SUMMARY")
        print("="*60)
        print(f"Total Stocks Found: {len(results)}\n")

        for i, result in enumerate(results[:15], 1):
            symbol = result['symbol'].replace('.NS', '')
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']

            # Get best pattern
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])

            print(f"{i:2}. {symbol:12} @ ₹{price:8.2f} | RSI:{rsi:6.1f} ADX:{adx:6.1f}")
            print(f"    → {best_pattern['type']} ({best_pattern['strength']:.0f}%) | {best_pattern['confidence']}")
            print()

        if len(results) > 15:
            print(f"... and {len(results) - 15} more stocks\n")

        print("="*60)


def main():
    """Main execution"""
    print("\n🚀 NSE F&O PCS Scanner - Automated Scan")
    print("="*60)

    # Initialize scanner
    scanner = StandaloneScanner()

    # Create default configuration
    config = scanner.create_default_filters()

    # Run scan
    results = scanner.scan_stocks(config, max_workers=6)

    # Display summary
    scanner.print_summary(results)

    # Save results
    if results:
        csv_file = scanner.save_results_to_csv(results)

        # Send to Telegram
        scanner.send_to_telegram(results)

        print(f"\n✅ Scan completed successfully!")
        print(f"   📊 Found: {len(results)} stocks")
        print(f"   📁 Saved to: {csv_file}")
    else:
        print("\n⚠️  No stocks found matching the criteria.")

    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
