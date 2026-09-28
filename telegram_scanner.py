#!/usr/bin/env python3
"""
Automated NSE F&O PCS Scanner with Telegram Integration
Runs stock screening with default filter criteria and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Use simple indicators instead of ta library
sys.path.insert(0, '/home/user/nsepcs')
from simple_indicators import ta

# Patch the ta module in sys.modules before importing streamlit_app
sys.modules['ta'] = ta

# Import the scanner class from the main app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

class AutomatedTelegramScanner:
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        """Initialize scanner with optional Telegram credentials"""
        self.scanner = ProfessionalPCSScanner()
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

    def get_default_config(self):
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
            'show_charts': False,
            'show_news': False,
            'export_results': False,
            'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
            'enhancements': {
                'delivery_volume': True,
                'fno_consolidation': True,
                'breakout_pullback': True,
                'enhanced_sr': True
            }
        }

    def run_scan(self, max_stocks=None):
        """Run the scanning analysis"""
        config = self.get_default_config()

        if max_stocks:
            config['stocks_to_scan'] = config['stocks_to_scan'][:max_stocks]
            config['stocks_limit'] = max_stocks

        results = []
        total_stocks = len(config['stocks_to_scan'])

        print(f"\n🚀 Starting scan of {total_stocks} stocks with default filter criteria")
        print(f"RSI: {config['rsi_min']}-{config['rsi_max']} | ADX Min: {config['adx_min']} | Pattern Strength Min: {config['pattern_strength_min']}%")
        print("-" * 80)

        for i, symbol in enumerate(config['stocks_to_scan'], 1):
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"[{i:3d}/{total_stocks}] Analyzing {clean_symbol:15s}", end=" ", flush=True)

            try:
                # Get recent data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    print("❌ No data")
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    print("❌ Volume")
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    print("❌ No patterns")
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
                }

                results.append(stock_result)
                max_strength = max(p['strength'] for p in patterns)
                print(f"✅ Found {len(patterns)} pattern(s) | Strength: {max_strength:.0f}%")

            except Exception as e:
                print(f"⚠️  Error: {str(e)[:30]}")
                continue

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        return results

    def format_results_for_telegram(self, results):
        """Format results as a Telegram message"""
        if not results:
            return "No stocks found matching the filter criteria."

        # IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%H:%M IST, %b %d, %Y')

        # Build message
        message = f"📊 NSE F&O PCS Scanner Results\n"
        message += f"⏰ {current_time}\n"
        message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        message += f"🎯 Found {len(results)} stocks with patterns\n\n"

        # Show top 10 results
        for i, result in enumerate(results[:10], 1):
            symbol = result['clean_symbol']
            price = result['current_price']
            rsi = result['rsi']
            adx = result['adx']
            patterns = result['patterns']
            max_strength = max(p['strength'] for p in patterns)
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            # Pattern types
            pattern_types = [p['type'].replace(' Pattern', '').replace('Current Day ', 'EOD ')
                           for p in patterns[:2]]  # Show top 2 patterns
            pattern_str = ' + '.join(pattern_types) if pattern_types else 'Multiple'

            message += f"{i}. <b>{symbol}</b>\n"
            message += f"   💰 ₹{price:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}\n"
            message += f"   📈 {pattern_str}\n"
            message += f"   💪 Strength: {max_strength:.0f}% | 🎯 {confidence}\n\n"

        if len(results) > 10:
            message += f"... and {len(results) - 10} more stocks\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += "📱 View full analysis at:\n"
        message += "https://nse-fo-pcs-screener.streamlit.app\n"

        return message

    def format_results_as_csv(self, results):
        """Format results as CSV"""
        data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            pattern_types = ', '.join([p['type'] for p in result['patterns']])

            data.append({
                'Symbol': result['clean_symbol'],
                'Price': f"₹{result['current_price']:.2f}",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Patterns': pattern_types,
                'Strength': f"{max_strength:.0f}%",
                'Confidence': confidence,
                'Volume_Ratio': f"{result['volume_ratio']:.2f}",
            })

        df = pd.DataFrame(data)
        return df

    def send_to_telegram(self, message):
        """Send message to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("\n⚠️  Telegram credentials not configured.")
            print("To send results to Telegram, set these environment variables:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            return False

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload, timeout=10)

            if response.status_code == 200:
                print("\n✅ Message sent to Telegram successfully!")
                return True
            else:
                print(f"\n❌ Failed to send Telegram message. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"\n❌ Error sending Telegram message: {e}")
            return False

    def save_results(self, results, filename=None):
        """Save results to CSV file"""
        if not results:
            print("No results to save.")
            return

        if not filename:
            ist = pytz.timezone('Asia/Kolkata')
            timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/claude-0/-home-user-nsepcs/scratchpad/pcs_scan_{timestamp}.csv"

        df = self.format_results_as_csv(results)
        df.to_csv(filename, index=False)
        print(f"\n📁 Results saved to: {filename}")
        return filename

def main():
    """Main execution"""
    print("\n" + "="*80)
    print("   NSE F&O PCS Scanner - Automated Mode with Telegram Integration")
    print("="*80)

    scanner = AutomatedTelegramScanner()

    # Run scan (limit to 50 stocks for initial test, can be increased)
    results = scanner.run_scan(max_stocks=50)

    if results:
        print(f"\n✅ Scan complete! Found {len(results)} stocks with patterns.")

        # Format and send to Telegram
        message = scanner.format_results_for_telegram(results)
        print("\n📨 Telegram Message Preview:")
        print("-" * 80)
        print(message)
        print("-" * 80)

        # Try to send to Telegram
        scanner.send_to_telegram(message)

        # Save results to CSV
        scanner.save_results(results)
    else:
        print("\n❌ No stocks found matching the filter criteria.")

if __name__ == "__main__":
    main()
