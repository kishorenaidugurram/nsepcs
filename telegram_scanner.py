#!/usr/bin/env python3
"""
NSE Stock Scanner with Telegram Integration
Runs the stock scanner with default filter settings and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE, fetch_stock_data_cached

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramStockNotifier:
    """Send stock scan results to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text, parse_mode='HTML'):
        """Send a message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Message sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_document(self, file_data, filename):
        """Send a document to Telegram"""
        try:
            url = f"{self.base_url}/sendDocument"
            files = {'document': (filename, file_data, 'text/csv')}
            data = {'chat_id': self.chat_id}
            response = requests.post(url, files=files, data=data, timeout=10)
            response.raise_for_status()
            logger.info(f"Document sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram document: {e}")
            return False


def create_default_config():
    """Create default scanner configuration"""
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
        'export_results': True,
        'stocks_limit': len(COMPLETE_NSE_FO_UNIVERSE),
    }


def run_scanner(config, max_stocks=None):
    """Run the stock scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    stocks_to_scan = config['stocks_to_scan']
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks...")

    for i, symbol in enumerate(stocks_to_scan):
        try:
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(stocks_to_scan)}")

            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
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

            # Store result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
            }

            results.append(stock_result)

        except Exception as e:
            logger.debug(f"Error processing {symbol}: {e}")
            continue

    # Sort results by pattern strength
    if results:
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    logger.info(f"Scan complete. Found {len(results)} qualifying stocks.")
    return results


def format_telegram_message(results, limit=10):
    """Format scan results for Telegram message"""
    if not results:
        return "❌ No stocks found matching the filter criteria."

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%d-%m-%Y %H:%M IST')

    # Sort and limit
    results_sorted = results[:limit]

    message = f"""
<b>📊 NSE F&O Stock Scanner Results</b>
<i>{timestamp}</i>

<b>✅ Found {len(results)} stocks matching filters</b>
(Showing top {min(limit, len(results))})

"""

    for idx, stock in enumerate(results_sorted, 1):
        symbol = stock['symbol'].replace('.NS', '')
        price = stock['current_price']
        volume = stock['volume_ratio']
        rsi = stock['rsi']
        adx = stock['adx']

        max_strength = max(p['strength'] for p in stock['patterns'])
        pattern_type = stock['patterns'][0]['type']

        # Emoji indicators
        strength_emoji = "🔥" if max_strength >= 85 else "⚡" if max_strength >= 70 else "⭐"
        volume_emoji = "📈" if volume >= 2 else "📊" if volume >= 1.2 else ""

        message += f"""
<b>{idx}. {symbol}</b> {strength_emoji}
💰 ₹{price:.2f} | 📊 Volume: {volume:.1f}x {volume_emoji}
📈 RSI: {rsi:.1f} | ⚡ ADX: {adx:.1f}
🎯 {pattern_type} ({max_strength:.0f}%)
"""

    message += f"""
<b>━━━━━━━━━━━━━━━━━━━━</b>
⚠️ <i>Disclaimer: For educational purpose only. Not investment advice.</i>
"""

    return message


def format_csv_export(results):
    """Format results as CSV"""
    data_rows = []

    for stock in results:
        symbol = stock['symbol'].replace('.NS', '')
        for pattern in stock['patterns']:
            data_rows.append({
                'Symbol': symbol,
                'Price': f"{stock['current_price']:.2f}",
                'Volume_Ratio': f"{stock['volume_ratio']:.2f}",
                'RSI': f"{stock['rsi']:.1f}",
                'ADX': f"{stock['adx']:.1f}",
                'Pattern': pattern['type'],
                'Strength': f"{pattern['strength']:.1f}",
                'Confidence': pattern.get('confidence', 'N/A'),
                'Success_Rate': pattern.get('success_rate', 0)
            })

    df = pd.DataFrame(data_rows)
    return df.to_csv(index=False)


def main():
    """Main entry point"""
    # Get Telegram credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        logger.error("""
❌ Missing Telegram credentials!

Please set the following environment variables:
  export TELEGRAM_BOT_TOKEN='your_bot_token'
  export TELEGRAM_CHAT_ID='your_chat_id'

To get these:
1. Create a bot with @BotFather on Telegram (get BOT_TOKEN)
2. Message your bot and get your CHAT_ID from /start command
3. Set these as environment variables
        """)
        sys.exit(1)

    # Initialize notifier
    notifier = TelegramStockNotifier(bot_token, chat_id)

    # Create config and run scanner
    config = create_default_config()

    logger.info("=" * 60)
    logger.info("NSE Stock Scanner Starting")
    logger.info("=" * 60)
    logger.info(f"Universe: {len(config['stocks_to_scan'])} F&O stocks")
    logger.info(f"RSI Range: {config['rsi_min']} - {config['rsi_max']}")
    logger.info(f"ADX Minimum: {config['adx_min']}")
    logger.info(f"Volume Ratio: {config['min_volume_ratio']}x")
    logger.info("=" * 60)

    # Run scan
    results = run_scanner(config)

    if not results:
        message = "❌ No stocks found matching the filter criteria."
        logger.info(message)
        notifier.send_message(message)
    else:
        # Send summary message
        summary_message = format_telegram_message(results, limit=15)
        notifier.send_message(summary_message)

        # Create and send CSV export
        csv_data = format_csv_export(results)
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"nsepcs_results_{timestamp}.csv"
        notifier.send_document(csv_data.encode(), filename)

        logger.info(f"Results sent to Telegram ({len(results)} stocks)")


if __name__ == "__main__":
    main()
