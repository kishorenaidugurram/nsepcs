#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Bot Integration
Runs stock scanner and sends filtered results to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to Python path to import from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# Import the scanner from streamlit app
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    logger.info("✅ Successfully imported ProfessionalPCSScanner")
except ImportError as e:
    logger.error(f"❌ Failed to import ProfessionalPCSScanner: {e}")
    sys.exit(1)

class TelegramScannerBot:
    """Telegram Bot for sending stock scanner results"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not found in environment variables")
            logger.info("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Telegram bot configured (Chat ID: {self.chat_id[:8]}...)")

    def send_message(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.enabled:
            logger.warning("Telegram not enabled. Message not sent.")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            return False

    def send_file(self, file_path, caption=""):
        """Send file to Telegram"""
        if not self.enabled:
            logger.warning("Telegram not enabled. File not sent.")
            return False

        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                payload = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(f"{self.api_url}/sendDocument",
                                        files=files, data=payload, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ File sent to Telegram: {file_path}")
                return True
            else:
                logger.error(f"❌ Failed to send file: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending file: {e}")
            return False


def run_scanner(telegram_bot, filter_config=None):
    """Run the stock scanner and send results to Telegram"""

    # Default filter configuration (from Streamlit defaults)
    if filter_config is None:
        filter_config = {
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
            'show_news': True,
            'show_charts': False,
            'enhancements': {
                'delivery_volume': True,
                'fno_consolidation': True,
                'breakout_pullback': True,
                'enhanced_sr': True
            }
        }

    logger.info(f"🚀 Starting scan of {len(filter_config['stocks_to_scan'])} stocks...")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []
    errors = []

    # Progress tracking
    total_stocks = len(filter_config['stocks_to_scan'])

    # Scan stocks
    for i, symbol in enumerate(filter_config['stocks_to_scan']):
        try:
            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i+1}/{total_stocks} stocks analyzed")

            # Get data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, filter_config['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filter_config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Get news if enabled
            news_data = None
            if filter_config['show_news']:
                try:
                    clean_symbol = symbol.replace('.NS', '').replace('^', '')
                    news_data = scanner.get_fundamental_news(symbol, clean_symbol)
                except:
                    pass

            # Create result object
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data,
                'news_data': news_data
            }

            results.append(stock_result)

        except Exception as e:
            error_msg = f"Error scanning {symbol}: {str(e)}"
            logger.warning(error_msg)
            errors.append(error_msg)
            continue

    logger.info(f"✅ Scan complete. Found {len(results)} stocks matching criteria")

    # Send results to Telegram
    if results:
        send_results_to_telegram(telegram_bot, results, filter_config)
    else:
        msg = "❌ No stocks found matching the filter criteria today."
        telegram_bot.send_message(msg)
        logger.info(msg)

    if errors and len(errors) <= 5:
        logger.info(f"Errors encountered: {len(errors)}")
        for error in errors[:5]:
            logger.debug(error)

    return results


def send_results_to_telegram(telegram_bot, results, config):
    """Format and send results to Telegram"""

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%H:%M IST')

    # Sort results by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Create header message
    total_patterns = sum(len(r['patterns']) for r in results)
    high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')
    current_day_breakouts = sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])

    header = f"""
<b>📊 NSE F&O PCS SCAN RESULTS</b>
<b>Time:</b> {current_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📈 Summary:</b>
• <b>Total Stocks:</b> {len(results)}
• <b>Total Patterns:</b> {total_patterns}
• <b>🔥 Today's Breakouts:</b> {current_day_breakouts}
• <b>🏆 High Confidence:</b> {high_confidence}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎯 FILTERED STOCKS:</b>
"""

    # Send header
    telegram_bot.send_message(header)

    # Send each stock result in detail
    for idx, result in enumerate(results[:20], 1):  # Limit to top 20 results
        clean_symbol = result['symbol'].replace('.NS', '').replace('^', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        stock_msg = f"""
<b>{idx}. {clean_symbol}</b>
━━━━━━━━━━━━━━━━
<b>Price:</b> ₹{result['current_price']:.2f}
<b>RSI:</b> {result['rsi']:.1f} | <b>ADX:</b> {result['adx']:.1f}
<b>Volume:</b> {result['volume_ratio']:.1f}x | <b>Confidence:</b> {confidence}
<b>Pattern Strength:</b> {max_strength:.0f}%

<b>Patterns Detected ({len(result['patterns'])}):</b>
"""

        for pattern in result['patterns'][:2]:  # Show top 2 patterns
            confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡"
            stock_msg += f"\n{confidence_emoji} {pattern['type']} ({pattern['strength']:.0f}%)"

        stock_msg += "\n━━━━━━━━━━━━━━━━\n"

        # Check for news
        if result.get('news_data') and result['news_data'].get('news_count', 0) > 0:
            news_sentiment = result['news_data'].get('overall_sentiment', 'neutral').upper()
            stock_msg += f"📰 News: {news_sentiment} Sentiment\n"

        telegram_bot.send_message(stock_msg)

    # Send summary
    if len(results) > 20:
        summary = f"\n... and <b>{len(results) - 20} more stocks</b> matching criteria.\n\nFor complete list, check the full scan."
        telegram_bot.send_message(summary)

    # Final summary
    footer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Scan completed at {current_time}
Use filters: RSI {config['rsi_min']}-{config['rsi_max']}, ADX ≥ {config['adx_min']}, Volume ≥ {config['min_volume_ratio']:.1f}x
"""
    telegram_bot.send_message(footer)

    logger.info(f"📩 Sent {len(results)} results to Telegram")


def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("NSE F&O PCS SCANNER - TELEGRAM BOT")
    logger.info("=" * 50)

    # Initialize Telegram bot
    telegram_bot = TelegramScannerBot()

    # Check if we have telegram credentials
    if not telegram_bot.enabled:
        logger.error("Cannot run in Telegram mode without credentials.")
        logger.error("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

        # Still run the scan and print results locally
        logger.info("Running local scan without Telegram...")
        results = run_scanner(telegram_bot)

        if results:
            print(f"\n✅ Found {len(results)} stocks matching criteria")
            for result in results[:10]:
                clean_symbol = result['symbol'].replace('.NS', '')
                max_strength = max(p['strength'] for p in result['patterns'])
                print(f"  • {clean_symbol}: ₹{result['current_price']:.2f} (Strength: {max_strength:.0f}%)")
        return 1

    # Run scanner with Telegram integration
    results = run_scanner(telegram_bot)

    logger.info("=" * 50)
    logger.info("✅ Process completed successfully")
    logger.info("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
