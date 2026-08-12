#!/usr/bin/env python3
"""
Standalone Stock Scanner with Telegram Integration
Runs the NSE F&O PCS scanner and sends results to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Add the repo to path to import from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# Import the scanner class from streamlit_app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

class TelegramScanner:
    def __init__(self):
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.scanner = ProfessionalPCSScanner()
        self.results = []

    def send_telegram_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️  Telegram credentials not configured. Results will be saved locally only.")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': parse_mode
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Failed to send Telegram message: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending Telegram message: {str(e)}")
            return False

    def get_default_config(self):
        """Get default configuration for scanning"""
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
                'three_rising_valleys': True,
                'rounding_bottom': True,
                'rounding_top_upside': False,
                'inverted_scallop': True,
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True,
            'show_charts': False,
            'show_news': False,
            'enhancements': {
                'delivery_volume': True,
                'fno_consolidation': True,
                'breakout_pullback': True,
                'enhanced_sr': True
            }
        }

    def run_scan(self, max_stocks=50):
        """Run the stock scanner"""
        config = self.get_default_config()
        config['stocks_to_scan'] = config['stocks_to_scan'][:max_stocks]

        print(f"\n🚀 Starting scan of {len(config['stocks_to_scan'])} stocks...")
        print(f"⏰ Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}\n")

        results = []

        for i, symbol in enumerate(config['stocks_to_scan']):
            progress = (i + 1) / len(config['stocks_to_scan'])
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"[{progress*100:3.0f}%] 🔍 Analyzing {clean_symbol}...", end='\r')

            try:
                # Get recent data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue

                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create result
                stock_result = {
                    'symbol': clean_symbol,
                    'price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'max_strength': max(p['strength'] for p in patterns)
                }

                results.append(stock_result)

            except Exception as e:
                continue

        print(f"\n✅ Scan complete! Found {len(results)} stocks.\n")

        # Sort by pattern strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)
        self.results = results
        return results

    def format_results_for_telegram(self, limit=20):
        """Format results for Telegram message"""
        if not self.results:
            return "No stocks found matching the criteria."

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        message = f"""
<b>📊 NSE F&O PCS Scanner Results</b>
<i>{timestamp}</i>

<b>Summary:</b>
• Total stocks found: {len(self.results)}
• Scan universe: NSE F&O Stocks
• Default filters: RSI(30-75), ADX>20, Volume>1.2x

"""

        # Add top stocks
        message += "<b>🏆 Top Performing Patterns:</b>\n"

        for idx, result in enumerate(self.results[:limit], 1):
            confidence = 'HIGH' if result['max_strength'] >= 85 else 'MEDIUM' if result['max_strength'] >= 70 else 'LOW'
            confidence_emoji = '🟢' if confidence == 'HIGH' else '🟡' if confidence == 'MEDIUM' else '🔴'

            message += f"\n{idx}. <b>{result['symbol']}</b> {confidence_emoji}"
            message += f"\n   💰 Price: ₹{result['price']:.2f}"
            message += f"\n   📊 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}"
            message += f"\n   📈 Volume: {result['volume_ratio']:.1f}x | Strength: {result['max_strength']:.0f}%"
            message += f"\n   🎯 Patterns: {len(result['patterns'])} detected"

        message += "\n\n<i>🔗 View full analysis at: https://nse-fo-pcs-screener.streamlit.app</i>"
        message += f"\n<i>⚙️ Scan ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}</i>"

        return message

    def save_results_to_file(self, filename=None):
        """Save results to a JSON file"""
        if not filename:
            filename = f"/tmp/nse_pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert results to serializable format
        serializable_results = []
        for result in self.results:
            serializable_result = {
                'symbol': result['symbol'],
                'price': float(result['price']),
                'volume_ratio': float(result['volume_ratio']),
                'rsi': float(result['rsi']),
                'adx': float(result['adx']),
                'max_strength': float(result['max_strength']),
                'patterns': [
                    {
                        'type': p['type'],
                        'strength': float(p['strength']),
                        'confidence': p['confidence'],
                        'success_rate': float(p.get('success_rate', 0))
                    }
                    for p in result['patterns']
                ]
            }
            serializable_results.append(serializable_result)

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'total_stocks': len(serializable_results),
                'stocks': serializable_results
            }, f, indent=2)

        print(f"✅ Results saved to: {filename}")
        return filename

    def run_and_send(self, max_stocks=50):
        """Run scan and send results to Telegram"""
        print("=" * 60)
        print("NSE F&O PCS SCANNER - TELEGRAM INTEGRATION")
        print("=" * 60)

        # Run the scan
        self.run_scan(max_stocks=max_stocks)

        # Save results
        results_file = self.save_results_to_file()

        # Format for Telegram
        message = self.format_results_for_telegram(limit=20)

        # Send to Telegram
        if self.telegram_token and self.telegram_chat_id:
            self.send_telegram_message(message)
        else:
            print("\n⚠️  Telegram credentials not configured.")
            print("\nTo enable Telegram notifications, set these environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            print("\nResults preview:")
            print(message)

        print("\n" + "=" * 60)
        print("Scan completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    scanner = TelegramScanner()

    # Run with max 50 stocks by default (adjust as needed)
    max_stocks = int(os.environ.get('MAX_STOCKS', '50'))
    scanner.run_and_send(max_stocks=max_stocks)
