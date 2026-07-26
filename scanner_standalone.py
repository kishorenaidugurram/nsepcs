#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Standalone Mode
Runs the scanner with predefined filter criteria and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
from io import StringIO

# Import scanner from streamlit app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter configuration
DEFAULT_FILTERS = {
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
    'pattern_priority': 'All Patterns (Comprehensive)',
    'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
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
    }
}


def validate_telegram_credentials():
    """Validate Telegram credentials are available"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return False
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID not set")
        return False
    return True


def send_telegram_message(text, parse_mode='HTML'):
    """Send message to Telegram"""
    if not validate_telegram_credentials():
        logger.warning("Telegram credentials not configured. Would have sent:")
        logger.info(text)
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info("Message sent to Telegram successfully")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {str(e)}")
        return False


def format_scan_results_for_telegram(results):
    """Format scan results as a Telegram message"""
    if not results:
        return "<b>📊 NSE F&O PCS Scanner</b>\n\n❌ No stocks found meeting criteria"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"<b>📊 NSE F&O PCS Scanner Results</b>\n"
    message += f"<b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}\n\n"
    message += f"<b>✅ Found {len(results)} stocks</b>\n"
    message += "─" * 40 + "\n\n"

    # Sort by strength
    sorted_results = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )

    for i, result in enumerate(sorted_results[:15], 1):  # Limit to top 15 for Telegram
        symbol = result['symbol'].replace('.NS', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        message += f"<b>{i}. {symbol}</b>\n"
        message += f"   Price: ₹{result['current_price']:.2f}\n"
        message += f"   Strength: {max_strength:.0f}% | Confidence: {confidence}\n"
        message += f"   Volume: {result['volume_ratio']:.1f}x | RSI: {result['rsi']:.1f}\n"

        # List patterns
        patterns_text = ", ".join([p['type'].split(' - ')[0] for p in result['patterns'][:3]])
        message += f"   Patterns: {patterns_text}\n"
        message += "\n"

    if len(results) > 15:
        message += f"\n... and {len(results) - 15} more stocks\n"

    return message


def format_stock_list_for_telegram(results):
    """Format just the stock symbols as a simple list for Telegram"""
    if not results:
        return "❌ No stocks found meeting criteria"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"<b>📊 NSE F&O PCS Scanner - Stock List</b>\n"
    message += f"<b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"<b>Count:</b> {len(results)} stocks\n\n"

    # Sort by strength
    sorted_results = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )

    message += "<b>Qualifying Stocks:</b>\n"
    message += "─" * 40 + "\n"

    symbols = []
    for result in sorted_results[:20]:  # Show top 20
        symbol = result['symbol'].replace('.NS', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        symbols.append(f"{symbol} ({max_strength:.0f}%)")

    # Add symbols in chunks
    for i in range(0, len(symbols), 5):
        message += " | ".join(symbols[i:i+5]) + "\n"

    if len(results) > 20:
        message += f"\n... and {len(results) - 20} more\n"

    return message


def run_scanner(filters=None):
    """Run the PCS scanner with given filters"""
    if filters is None:
        filters = DEFAULT_FILTERS

    logger.info("Starting NSE F&O PCS Scanner")
    logger.info(f"Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} F&O stocks")

    scanner = ProfessionalPCSScanner()
    results = []

    for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE):
        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                filters['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Add to results
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
            }

            results.append(stock_result)

            if (i + 1) % 20 == 0:
                logger.info(f"Scanned {i + 1} stocks, found {len(results)} qualifying")

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {str(e)}")
            continue

    logger.info(f"Scan complete: Found {len(results)} qualifying stocks")
    return results


def save_results_to_file(results):
    """Save results to CSV file"""
    if not results:
        logger.warning("No results to save")
        return None

    try:
        data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            data.append({
                'Symbol': result['symbol'].replace('.NS', ''),
                'Price': result['current_price'],
                'Volume_Ratio': result['volume_ratio'],
                'RSI': result['rsi'],
                'ADX': result['adx'],
                'Strength': max_strength,
                'Confidence': confidence,
                'Pattern_Count': len(result['patterns']),
            })

        df = pd.DataFrame(data)
        df = df.sort_values('Strength', ascending=False)

        filename = f"/tmp/claude-0/-home-user-nsepcs/7b1f6c1a-168e-5d87-8199-b06c9ca257a1/scratchpad/pcs_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)

        logger.info(f"Results saved to {filename}")
        return filename

    except Exception as e:
        logger.error(f"Failed to save results: {str(e)}")
        return None


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Standalone Mode")
    logger.info("=" * 60)

    # Validate Telegram setup
    telegram_available = validate_telegram_credentials()
    if not telegram_available:
        logger.warning("Telegram credentials not configured - results will only be logged")

    # Run scanner
    try:
        results = run_scanner(DEFAULT_FILTERS)

        # Save results to file
        csv_file = save_results_to_file(results)

        # Send to Telegram
        if telegram_available:
            logger.info("Sending results to Telegram...")

            # Send main results message
            message = format_scan_results_for_telegram(results)
            send_telegram_message(message)

            # Send simple stock list
            if results:
                stock_list = format_stock_list_for_telegram(results)
                send_telegram_message(stock_list)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SCAN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total qualifying stocks: {len(results)}")

        if results:
            sorted_results = sorted(
                results,
                key=lambda x: max(p['strength'] for p in x['patterns']),
                reverse=True
            )
            logger.info("\nTop 10 Stocks:")
            for i, result in enumerate(sorted_results[:10], 1):
                symbol = result['symbol'].replace('.NS', '')
                max_strength = max(p['strength'] for p in result['patterns'])
                logger.info(f"  {i}. {symbol}: {max_strength:.0f}% strength")

        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Scanner failed: {str(e)}")
        if telegram_available:
            send_telegram_message(f"❌ <b>Scanner Error</b>\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
