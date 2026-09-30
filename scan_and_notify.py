#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Automated script with Telegram notification
Runs the stock scanner with default filters and sends results to Telegram
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the scanner from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached,
    fetch_weekly_data_cached
)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Use default demo chat if not set (user can provide via env vars)
if not TELEGRAM_BOT_TOKEN:
    logger.warning("TELEGRAM_BOT_TOKEN not set. Results will not be sent to Telegram.")
if not TELEGRAM_CHAT_ID:
    logger.warning("TELEGRAM_CHAT_ID not set. Results will not be sent to Telegram.")


def send_telegram_message(message, parse_mode="HTML"):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not configured. Skipping notification.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            logger.info("Telegram notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return False


def run_scanner_with_defaults():
    """Run the scanner with default filters"""
    logger.info("Starting NSE F&O PCS Scanner with default filters")

    # Default filter values (from sidebar)
    filters = {
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
        'export_results': False,
    }

    scanner = ProfessionalPCSScanner()
    results = []

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    logger.info(f"Scanning {len(stocks_to_scan)} stocks")

    # Send start notification
    start_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    send_telegram_message(
        f"🚀 <b>NSE F&O PCS Scanner Started</b>\n"
        f"⏰ Time: {start_time.strftime('%Y-%m-%d %H:%M IST')}\n"
        f"📊 Universe: {len(stocks_to_scan)} F&O stocks\n"
        f"⚙️ Mode: Daily + Weekly Combined"
    )

    try:
        for idx, symbol in enumerate(stocks_to_scan, 1):
            if idx % 20 == 0:
                logger.info(f"Processed {idx}/{len(stocks_to_scan)} stocks")

            try:
                # Get recent data
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                    data, filters['min_volume_ratio']
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

                # Build result
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'volume_ratio': volume_ratio,
                    'patterns': patterns,
                    'data': data
                }

                results.append(result)
                logger.info(f"✓ Found patterns in {symbol.replace('.NS', '')}")

            except Exception as e:
                logger.debug(f"Error processing {symbol}: {str(e)}")
                continue

        logger.info(f"Scan complete. Found {len(results)} stocks with patterns")
        return results

    except Exception as e:
        logger.error(f"Error during scan: {str(e)}")
        send_telegram_message(f"❌ <b>Scanner Error</b>\n{str(e)}")
        return []


def format_results_for_telegram(results, max_items=15):
    """Format scan results for Telegram message"""
    if not results:
        return "❌ <b>No stocks found matching criteria</b>"

    # Sort by pattern strength (highest first)
    sorted_results = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )[:max_items]

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = (
        f"✅ <b>Scan Results - {current_time.strftime('%H:%M IST')}</b>\n"
        f"📊 Found: <b>{len(results)} stocks</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for idx, result in enumerate(sorted_results, 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']

        # Get best pattern
        best_pattern = max(result['patterns'], key=lambda p: p['strength'])
        pattern_type = best_pattern['type']
        pattern_strength = best_pattern['strength']
        confidence = best_pattern['confidence']

        # Emoji for confidence
        conf_emoji = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"

        message += (
            f"<b>{idx}. {symbol}</b> {conf_emoji}\n"
            f"   💰 ₹{price:.2f} | RSI: {rsi:.0f} | ADX: {adx:.0f}\n"
            f"   📈 {pattern_type}\n"
            f"   💪 Strength: {pattern_strength:.0f}%\n\n"
        )

    # Add footer
    if len(results) > max_items:
        message += f"... and {len(results) - max_items} more stocks\n\n"

    message += (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Filters: RSI(30-75), ADX>20, Vol>1.2x\n"
        "Mode: Daily + Weekly Combined\n"
    )

    return message


def export_results_to_csv(results, filename="/tmp/scan_results.csv"):
    """Export results to CSV"""
    if not results:
        return None

    data = []
    for result in results:
        best_pattern = max(result['patterns'], key=lambda p: p['strength'])
        data.append({
            'Symbol': result['symbol'].replace('.NS', ''),
            'Price': f"₹{result['current_price']:.2f}",
            'RSI': f"{result['rsi']:.1f}",
            'ADX': f"{result['adx']:.1f}",
            'Volume_Ratio': f"{result['volume_ratio']:.1f}x",
            'Pattern': best_pattern['type'],
            'Strength': f"{best_pattern['strength']:.0f}%",
            'Confidence': best_pattern['confidence'],
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    logger.info(f"Results exported to {filename}")
    return filename


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Automated Run")
    logger.info("=" * 60)

    # Run scanner
    results = run_scanner_with_defaults()

    if results:
        logger.info(f"✓ Found {len(results)} stocks with patterns")

        # Format and send to Telegram
        message = format_results_for_telegram(results)
        send_telegram_message(message)

        # Export to CSV
        csv_file = export_results_to_csv(results)

        # Print results summary
        print("\n" + "=" * 60)
        print("SCAN RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total stocks found: {len(results)}\n")

        for idx, result in enumerate(sorted(
            results,
            key=lambda x: max(p['strength'] for p in x['patterns']),
            reverse=True
        )[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            best_pattern = max(result['patterns'], key=lambda p: p['strength'])
            print(f"{idx:2d}. {symbol:12s} - {best_pattern['type']:25s} ({best_pattern['strength']:.0f}%)")

        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more stocks")

        print(f"\nResults saved to: {csv_file}")
        print("=" * 60)

    else:
        logger.warning("No stocks found matching the criteria")
        send_telegram_message("❌ <b>No stocks found</b>\nTry adjusting filter criteria")

    logger.info("Scan complete")


if __name__ == "__main__":
    main()
