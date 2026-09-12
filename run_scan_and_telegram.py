#!/usr/bin/env python3
"""
Standalone Stock Scanner with Telegram Integration
Runs NSE F&O stock screening and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz

# Add current directory to path to import from streamlit_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner and utilities from main app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

import requests

class TelegramReporter:
    """Send scan results to Telegram"""

    def __init__(self, bot_token=None, chat_id=None):
        """Initialize Telegram reporter with credentials"""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.ist = pytz.timezone('Asia/Kolkata')

    def validate_credentials(self):
        """Validate that Telegram credentials are set"""
        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "Telegram credentials not found! Please set:\n"
                "  export TELEGRAM_BOT_TOKEN='your_bot_token'\n"
                "  export TELEGRAM_CHAT_ID='your_chat_id'"
            )

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        try:
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    def send_scan_results(self, results, config):
        """Format and send scan results to Telegram"""
        if not results:
            message = "⚠️ <b>NSE F&O PCS Scan Complete</b>\n\n"
            message += "No stocks matched the filter criteria.\n"
            message += f"Scan time: {datetime.now(self.ist).strftime('%H:%M IST')}"
            self.send_message(message)
            return

        # Send header with scan details
        ist = self.ist
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        header = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
        header += f"<i>{current_time}</i>\n\n"
        header += f"<b>Stocks Found: {len(results)}</b>\n"
        header += f"<b>RSI Range:</b> {config['rsi_min']}-{config['rsi_max']}\n"
        header += f"<b>ADX Min:</b> {config['adx_min']}\n"
        header += f"<b>Pattern Strength Min:</b> {config['pattern_strength_min']}\n"
        header += "─" * 40 + "\n\n"

        self.send_message(header)

        # Send results in batches (Telegram message limit is 4096 chars)
        batch_message = ""
        for i, result in enumerate(results[:50], 1):  # Limit to 50 stocks per scan
            symbol = result.get('Symbol', 'N/A')
            price = result.get('Current_Price', 0)
            rsi = result.get('RSI', 0)
            patterns = result.get('Patterns', [])

            stock_info = f"<b>{i}. {symbol}</b> | ₹{price:.2f}\n"
            stock_info += f"   RSI: {rsi:.1f} | Patterns: {', '.join(patterns[:2])}\n"

            # Check if adding this would exceed message limit
            if len(batch_message) + len(stock_info) > 3500:
                self.send_message(batch_message)
                batch_message = stock_info
            else:
                batch_message += stock_info

        # Send remaining batch
        if batch_message:
            self.send_message(batch_message)

        # Send footer with summary
        footer = f"\n{'─' * 40}\n"
        footer += f"✅ Scan completed at {datetime.now(ist).strftime('%H:%M IST')}\n"
        footer += f"Total matches: <b>{len(results)}</b>"
        self.send_message(footer)


def run_standalone_scan(config=None):
    """Run the scanner with default or provided configuration"""

    # Default filter configuration
    if config is None:
        config = {
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
        }

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    print(f"🚀 Starting NSE F&O PCS Scan...")
    print(f"📊 Scanning {len(config['stocks_to_scan'])} stocks")
    print(f"⚙️ Filter Criteria:")
    print(f"   - RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"   - ADX Min: {config['adx_min']}")
    print(f"   - Pattern Strength Min: {config['pattern_strength_min']}")
    print(f"   - MA Support: {config['ma_support']}")

    # Scan each stock
    for idx, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            # Progress
            if idx % 10 == 0:
                print(f"  Progress: {idx}/{len(config['stocks_to_scan'])}")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, _ = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Format result
            result = {
                'Symbol': symbol.replace('.NS', '').replace('^', ''),
                'Current_Price': current_price,
                'RSI': current_rsi,
                'ADX': current_adx,
                'Patterns': patterns,
                'Volume_Ratio': volume_ratio,
                'Timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            }

            results.append(result)
            print(f"✓ {result['Symbol']}: {len(patterns)} pattern(s) matched")

        except Exception as e:
            # Continue on individual stock errors
            pass

    print(f"\n✅ Scan complete! Found {len(results)} matching stocks")
    return results, config


def main():
    """Main entry point"""
    try:
        # Run scan
        results, config = run_standalone_scan()

        # Initialize Telegram reporter
        telegram = TelegramReporter()
        telegram.validate_credentials()

        # Send results to Telegram
        print("\n📱 Sending results to Telegram...")
        telegram.send_scan_results(results, config)
        print("✅ Telegram message sent successfully!")

        # Also save results locally
        output_file = '/tmp/claude-0/-home-user-nsepcs/7ef0a07e-499f-538b-906e-094cae0bf786/scratchpad/scan_results.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'config': config,
                'results': results
            }, f, indent=2, default=str)
        print(f"💾 Results saved to {output_file}")

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
