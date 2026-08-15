#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner with Telegram Integration
Runs the stock scanner and sends qualifying stocks to Telegram
"""

import sys
import os
import json
from datetime import datetime
import pytz
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from main app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Telegram imports
try:
    import requests
except ImportError:
    logger.warning("requests library not available, will install")
    os.system("pip install requests -q")
    import requests


class TelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self, bot_token=None, chat_id=None):
        """Initialize with bot token and chat ID"""
        # Try to get from environment variables or parameters
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Telegram notifier initialized (Chat ID: {self.chat_id})")

    def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        if not self.enabled:
            logger.warning("Telegram not enabled, skipping notification")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }

            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    def send_stock_list(self, stocks):
        """Send list of stocks to Telegram"""
        if not stocks:
            self.send_message("❌ No stocks found meeting the filter criteria")
            return

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")

        # Build message
        message = f"📊 <b>NSE F&O PCS Scanner Results</b>\n"
        message += f"⏰ {timestamp}\n"
        message += f"📈 Found <b>{len(stocks)}</b> stocks\n\n"

        message += "<b>Qualifying Stocks:</b>\n"

        for i, stock in enumerate(stocks[:20], 1):  # Limit to 20 for message size
            symbol = stock['symbol'].replace('.NS', '')
            price = stock['current_price']
            strength = stock.get('patterns', [{}])[0].get('strength', 0) if stock.get('patterns') else 0
            confidence = stock.get('patterns', [{}])[0].get('confidence', 'N/A') if stock.get('patterns') else 'N/A'

            message += f"{i}. <b>{symbol}</b> - ₹{price:.2f} | "
            message += f"Strength: {strength:.0f}% | {confidence}\n"

        if len(stocks) > 20:
            message += f"\n... and {len(stocks) - 20} more stocks\n"

        message += f"\n💾 Full Excel export available in results\n"
        message += f"🔗 Run Streamlit app for detailed analysis\n"

        self.send_message(message)


def run_scanner(stocks_to_scan, config):
    """Run the stock scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks...")

    for i, symbol in enumerate(stocks_to_scan, 1):
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(stocks_to_scan)}")

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
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

            # Create result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data
            }

            results.append(stock_result)

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {str(e)}")
            continue

    logger.info(f"Scan complete. Found {len(results)} stocks with patterns")
    return results


def create_default_config():
    """Create default scanner configuration"""
    return {
        'rsi_min': 30,
        'rsi_max': 80,
        'adx_min': 15,
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
            'inverted_scallop': True
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True
    }


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner with Telegram Integration")
    logger.info("=" * 60)

    # Get stocks to scan
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:50]  # Scan top 50 for faster execution

    # Create configuration
    config = create_default_config()

    # Run scanner
    results = run_scanner(stocks_to_scan, config)

    if results:
        # Sort by strength
        results.sort(
            key=lambda x: max(p['strength'] for p in x['patterns']),
            reverse=True
        )

        logger.info(f"✅ Found {len(results)} qualifying stocks")

        # Send to Telegram
        notifier = TelegramNotifier()
        if notifier.enabled:
            notifier.send_stock_list(results)
        else:
            # Print to console if Telegram not configured
            logger.warning("Telegram not configured. Printing results:")
            for result in results[:10]:
                symbol = result['symbol'].replace('.NS', '')
                price = result['current_price']
                strength = result['patterns'][0]['strength']
                logger.info(f"  {symbol}: ₹{price:.2f} (Strength: {strength:.0f}%)")

        # Save to JSON
        output_file = '/tmp/claude-0/-home-user-nsepcs/ca12a9e7-0f2a-59d1-a829-3fe74b60cf4c/scratchpad/scan_results.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        results_data = []
        for result in results:
            results_data.append({
                'symbol': result['symbol'].replace('.NS', ''),
                'price': result['current_price'],
                'volume_ratio': result['volume_ratio'],
                'rsi': result['rsi'],
                'adx': result['adx'],
                'pattern': result['patterns'][0]['type'] if result['patterns'] else 'N/A',
                'strength': result['patterns'][0]['strength'] if result['patterns'] else 0,
                'confidence': result['patterns'][0]['confidence'] if result['patterns'] else 'N/A'
            })

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        logger.info(f"Results saved to {output_file}")

    else:
        logger.warning("❌ No stocks found meeting the filter criteria")
        notifier = TelegramNotifier()
        if notifier.enabled:
            notifier.send_message("❌ No stocks found meeting the filter criteria")


if __name__ == "__main__":
    main()
