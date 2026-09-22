#!/usr/bin/env python3
"""
Standalone Stock Scanner Script
Runs the PCS scanner and sends results to Telegram
"""

import sys
import os
import logging
from datetime import datetime
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Check for required environment variables
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram credentials not found in environment variables")
    logger.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
    TELEGRAM_ENABLED = False
else:
    TELEGRAM_ENABLED = True

# Import scanner from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

def send_telegram_message(message, parse_mode='HTML'):
    """Send message to Telegram"""
    if not TELEGRAM_ENABLED:
        logger.info("Telegram disabled - would send: " + message[:50])
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logger.info("Message sent to Telegram")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False

def run_scanner(stocks_to_scan=None, **config):
    """
    Run the stock scanner with given configuration

    Args:
        stocks_to_scan: List of stock symbols to scan
        **config: Scanner configuration parameters

    Returns:
        List of matching stocks with their patterns
    """

    # Default configuration
    default_config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.0,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 70,
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
        'enable_daily_analysis': True,
        'enable_weekly_validation': True
    }

    # Update with provided config
    default_config.update(config)
    config = default_config

    # Use provided stocks or default to F&O universe
    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:100]  # Scan first 100 by default

    logger.info(f"Starting scan of {len(stocks_to_scan)} stocks")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Progress tracking
    total = len(stocks_to_scan)
    processed = 0

    for i, symbol in enumerate(stocks_to_scan):
        processed = i + 1
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                logger.debug(f"Skipping {clean_symbol} - insufficient data")
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config['min_volume_ratio']
            )
            if not volume_ok:
                logger.debug(f"Skipping {clean_symbol} - volume criteria not met")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                logger.debug(f"Skipping {clean_symbol} - no patterns detected")
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
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata'))
            }

            results.append(stock_result)
            logger.info(f"[{processed}/{total}] ✓ {clean_symbol} - {len(patterns)} pattern(s) found")

        except Exception as e:
            logger.error(f"Error processing {clean_symbol}: {str(e)}")
            continue

    logger.info(f"Scan complete! Found {len(results)} stocks with patterns")
    return results

def format_results_for_telegram(results):
    """Format scanner results for Telegram message"""
    if not results:
        return "🔍 <b>Stock Scanner Results</b>\n\nNo stocks found matching the criteria."

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Build message
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')

    message = f"🔍 <b>Stock Scanner Results</b>\n"
    message += f"📅 {timestamp}\n\n"
    message += f"✅ Found <b>{len(results)} stocks</b> with patterns\n"
    message += "=" * 50 + "\n\n"

    for idx, result in enumerate(results[:20], 1):  # Limit to top 20 for message size
        symbol = result['clean_symbol']
        price = result['current_price']
        volume = result['volume_ratio']
        rsi = result['rsi']

        # Get best pattern
        best_pattern = max(result['patterns'], key=lambda x: x['strength'])
        pattern_type = best_pattern['type']
        strength = best_pattern['strength']
        confidence = best_pattern['confidence']

        message += f"<b>{idx}. {symbol}</b>\n"
        message += f"  💰 Price: ₹{price:.2f}\n"
        message += f"  📊 Volume: {volume:.1f}x\n"
        message += f"  📈 RSI: {rsi:.1f}\n"
        message += f"  🎯 Pattern: {pattern_type}\n"
        message += f"  💪 Strength: {strength:.0f}% ({confidence})\n"
        message += "\n"

    if len(results) > 20:
        message += f"\n... and {len(results) - 20} more stocks\n"

    message += "=" * 50 + "\n"
    message += "📊 Summary:\n"
    message += f"  • Total: {len(results)}\n"
    message += f"  • Current Day Breakouts: {sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])}\n"
    message += f"  • Avg Strength: {sum(max(p['strength'] for p in r['patterns']) for r in results) / len(results):.0f}%\n"

    return message

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Stock Scanner - Telegram Mode")
    logger.info("=" * 60)

    # Run scanner with default parameters
    logger.info("Running scanner with default parameters...")

    try:
        results = run_scanner(
            stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:100],  # Scan first 100 F&O stocks
            rsi_min=30,
            rsi_max=75,
            adx_min=20,
            min_volume_ratio=1.0,
            pattern_strength_min=70
        )

        if results:
            logger.info(f"✓ Found {len(results)} stocks with patterns")

            # Format and send to Telegram
            message = format_results_for_telegram(results)

            if TELEGRAM_ENABLED:
                logger.info("Sending results to Telegram...")
                success = send_telegram_message(message)
                if success:
                    logger.info("✓ Results sent to Telegram successfully")
                else:
                    logger.error("✗ Failed to send results to Telegram")
                    print("\n" + message + "\n")
            else:
                logger.warning("Telegram not enabled - printing results instead:")
                print("\n" + message + "\n")
        else:
            logger.warning("No stocks found matching the criteria")
            message = "🔍 <b>Stock Scanner Results</b>\n\nNo stocks found matching the criteria."
            if TELEGRAM_ENABLED:
                send_telegram_message(message)

    except Exception as e:
        logger.error(f"Scanner error: {str(e)}", exc_info=True)
        error_msg = f"❌ <b>Scanner Error</b>\n\n{str(e)}"
        if TELEGRAM_ENABLED:
            send_telegram_message(error_msg)
        else:
            print(error_msg)

if __name__ == "__main__":
    main()
