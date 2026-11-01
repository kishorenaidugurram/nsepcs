#!/usr/bin/env python3
"""
Standalone scanner script - runs the NSE F&O PCS scanner and sends results to Telegram
Usage: python scan_and_send.py [--token YOUR_BOT_TOKEN] [--chat_id YOUR_CHAT_ID]
Or set environment variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import sys
import os
import json
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import requests

warnings.filterwarnings('ignore')

# Import the scanner from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# We need to mock streamlit since the scanner imports it
class StreamlitMock:
    pass

sys.modules['streamlit'] = StreamlitMock()

from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached,
    fetch_weekly_data_cached
)

def get_default_config():
    """Get default scanner configuration for automated runs"""
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
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False
        }
    }

def run_scan(config):
    """Run the stock scanner with given configuration"""
    scanner = ProfessionalPCSScanner()
    results = []

    total_stocks = len(config['stocks_to_scan'])
    print(f"\n📊 Starting scan of {total_stocks} stocks...")
    print(f"⏰ Scan started at {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}\n")

    for i, symbol in enumerate(config['stocks_to_scan']):
        # Print progress every 20 stocks
        if (i + 1) % 20 == 0 or i == 0:
            print(f"  [{i+1}/{total_stocks}] Processing {symbol.replace('.NS', '')}")

        try:
            # Get recent data focused on current day
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume (current day focused)
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns (current day confirmation)
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create the stock result
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
            continue

    # Sort by pattern strength
    if results:
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    print(f"\n✅ Scan completed! Found {len(results)} stocks meeting criteria.\n")
    return results

def send_to_telegram(stocks, bot_token, chat_id):
    """Send stock results to Telegram"""
    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not provided. Skipping Telegram notification.")
        return False

    try:
        # Prepare message
        message = "🎯 **NSE F&O PCS Scanner Results**\n"
        message += f"⏰ {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}\n\n"

        if not stocks:
            message += "❌ No stocks found matching criteria today."
        else:
            message += f"✅ Found **{len(stocks)} stocks** with current day confirmed patterns!\n\n"

            # Add top 10 stocks
            for idx, stock in enumerate(stocks[:10], 1):
                symbol = stock['symbol'].replace('.NS', '')
                max_strength = max(p['strength'] for p in stock['patterns'])
                confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

                message += f"{idx}. **{symbol}** - {confidence}\n"
                message += f"   Price: ₹{stock['current_price']:.2f} | "
                message += f"RSI: {stock['rsi']:.1f} | "
                message += f"ADX: {stock['adx']:.1f} | "
                message += f"Strength: {max_strength:.0f}%\n"

            if len(stocks) > 10:
                message += f"\n... and {len(stocks) - 10} more stocks."

        # Send to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def save_results_to_file(stocks, filename=None):
    """Save results to a JSON file"""
    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f'/tmp/claude-0/-home-user-nsepcs/ad59d2ce-88fa-57a6-ab8b-7cbaf51b3e1b/scratchpad/scan_results_{timestamp}.json'

    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Prepare data for JSON serialization
    results_data = []
    for stock in stocks:
        stock_data = {
            'symbol': stock['symbol'].replace('.NS', ''),
            'current_price': float(stock['current_price']),
            'volume_ratio': float(stock['volume_ratio']),
            'rsi': float(stock['rsi']),
            'adx': float(stock['adx']),
            'patterns': [
                {
                    'type': p['type'],
                    'strength': float(p['strength']),
                    'confidence': p['confidence'],
                    'success_rate': float(p['success_rate']),
                    'pcs_suitability': float(p['pcs_suitability']),
                }
                for p in stock['patterns']
            ]
        }
        results_data.append(stock_data)

    with open(filename, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"💾 Results saved to: {filename}")
    return filename

def main():
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Scanner with Telegram Integration')
    parser.add_argument('--token', help='Telegram bot token')
    parser.add_argument('--chat_id', help='Telegram chat ID')
    parser.add_argument('--no-telegram', action='store_true', help='Skip Telegram notification')
    parser.add_argument('--save-only', action='store_true', help='Only save results, do not send to Telegram')

    args = parser.parse_args()

    # Get Telegram credentials from args or environment
    telegram_token = args.token or os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = args.chat_id or os.getenv('TELEGRAM_CHAT_ID')

    # Get default configuration
    config = get_default_config()

    # Run the scan
    try:
        stocks = run_scan(config)

        # Save results
        save_results_to_file(stocks)

        # Send to Telegram (unless disabled)
        if not args.no_telegram and not args.save_only:
            send_to_telegram(stocks, telegram_token, telegram_chat_id)

        return 0

    except Exception as e:
        print(f"❌ Error during scan: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
