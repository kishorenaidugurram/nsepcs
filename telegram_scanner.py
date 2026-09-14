#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Runs analysis and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path to import from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a better mock for streamlit BEFORE any imports
class StreamlitMock:
    def set_page_config(self, **kwargs):
        pass
    def markdown(self, *args, **kwargs):
        pass
    def cache_data(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def __getattr__(self, name):
        def stub(*args, **kwargs):
            return None
        return stub

sys.modules['streamlit'] = StreamlitMock()

# Now import the libraries
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema

# Import the stock universe and scanner class from streamlit_app
import importlib.util
spec = importlib.util.spec_from_file_location("streamlit_app_module", "/home/user/nsepcs/streamlit_app.py")
app_module = importlib.util.module_from_spec(spec)

# Now load the module
try:
    spec.loader.exec_module(app_module)
    COMPLETE_NSE_FO_UNIVERSE = app_module.COMPLETE_NSE_FO_UNIVERSE
    ProfessionalPCSScanner = app_module.ProfessionalPCSScanner
    logger.info("Successfully loaded scanner module")
except Exception as e:
    logger.error(f"Failed to load scanner module: {e}")
    sys.exit(1)

def send_to_telegram(message, telegram_token=None, telegram_chat_id=None):
    """Send message to Telegram"""

    if not telegram_token:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not telegram_chat_id:
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        logger.warning("Telegram credentials not found in environment variables")
        logger.warning(f"Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Message sent to Telegram successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending to Telegram: {e}")
        return False

def run_scan(max_stocks=None, min_volume_ratio=1.2):
    """Run the PCS scanner with default settings"""

    logger.info("Initializing scanner...")
    scanner = ProfessionalPCSScanner()

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks")

    results = []

    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                logger.debug(f"No data for {clean_symbol}")
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, min_volume_ratio
            )
            if not volume_ok:
                logger.debug(f"Volume criteria not met for {clean_symbol}")
                continue

            # Detect patterns with default configuration
            config = {
                'rsi_min': 30,
                'rsi_max': 75,
                'adx_min': 20,
                'ma_support': True,
                'ma_type': 'EMA',
                'ma_tolerance': 3,
                'min_volume_ratio': min_volume_ratio,
                'volume_breakout_ratio': 2.0,
                'lookback_days': 20,
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
                'pattern_strength_min': 65,
                'enable_daily_analysis': True,
                'enable_weekly_validation': True,
            }

            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                logger.debug(f"No patterns found for {clean_symbol}")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
            stock_result = {
                'symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'pattern_count': len(patterns),
                'max_strength': max(p['strength'] for p in patterns)
            }

            results.append(stock_result)
            logger.info(f"Found patterns for {clean_symbol}: {len(patterns)} pattern(s)")

        except Exception as e:
            logger.debug(f"Error processing {symbol}: {str(e)}")
            continue

        # Progress
        if (i + 1) % 10 == 0:
            logger.info(f"Progress: {i + 1}/{len(stocks_to_scan)} stocks processed")

    logger.info(f"Scan complete: Found {len(results)} stocks with patterns")
    return results

def format_telegram_message(results):
    """Format results into a Telegram message"""

    if not results:
        return "❌ No stocks meeting criteria found in today's scan"

    # Sort by pattern strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    message = f"""<b>📊 NSE F&O PCS Scanner Results</b>
<i>{timestamp}</i>

<b>✅ Found {len(results)} stocks with patterns</b>

"""

    for i, stock in enumerate(results[:20], 1):  # Limit to top 20
        confidence = '🟢 HIGH' if stock['max_strength'] >= 85 else '🟡 MEDIUM' if stock['max_strength'] >= 70 else '🔴 LOW'

        message += f"""<b>{i}. {stock['symbol']}</b>
Price: ₹{stock['current_price']:.2f} | RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}
Patterns: {stock['pattern_count']} | Strength: {stock['max_strength']:.0f}% {confidence}
Patterns: {', '.join(p['type'] for p in stock['patterns'][:2])}

"""

    if len(results) > 20:
        message += f"\n... and {len(results) - 20} more stocks"

    # Add trading disclaimer
    message += """
⚠️ <i>Disclaimer: This is educational analysis only. Always do your own research and consult financial advisors before trading.</i>
"""

    return message

def main():
    """Main execution"""

    logger.info("=" * 60)
    logger.info("Starting NSE F&O PCS Telegram Scanner")
    logger.info("=" * 60)

    # Check for Telegram credentials
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        logger.error("❌ Telegram credentials not configured!")
        logger.error("Please set environment variables:")
        logger.error("  - TELEGRAM_BOT_TOKEN")
        logger.error("  - TELEGRAM_CHAT_ID")

        # Still run the scan and save results locally
        logger.info("Running scan anyway and saving results locally...")
        results = run_scan()

        # Save results to JSON
        output_file = '/tmp/pcs_scan_results.json'
        with open(output_file, 'w') as f:
            json.dump([{
                'symbol': r['symbol'],
                'price': r['current_price'],
                'rsi': r['rsi'],
                'adx': r['adx'],
                'patterns': len(r['patterns']),
                'strength': r['max_strength']
            } for r in results], f, indent=2)
        logger.info(f"Results saved to {output_file}")

        # Print results
        message = format_telegram_message(results)
        print("\n" + message)

        return 1

    # Run the scan
    results = run_scan()

    # Format and send message
    message = format_telegram_message(results)

    logger.info(f"Message preview:\n{message}")
    logger.info("Sending to Telegram...")

    if send_to_telegram(message, telegram_token, telegram_chat_id):
        logger.info("✅ Successfully sent results to Telegram")
        return 0
    else:
        logger.error("❌ Failed to send results to Telegram")

        # Save results as fallback
        output_file = '/tmp/pcs_scan_results.json'
        with open(output_file, 'w') as f:
            json.dump([{
                'symbol': r['symbol'],
                'price': r['current_price'],
                'rsi': r['rsi'],
                'adx': r['adx'],
                'patterns': len(r['patterns']),
                'strength': r['max_strength']
            } for r in results], f, indent=2)
        logger.info(f"Results saved to {output_file}")

        return 1

if __name__ == "__main__":
    sys.exit(main())
