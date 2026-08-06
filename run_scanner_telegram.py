#!/usr/bin/env python3
"""
Standalone scanner script that runs technical analysis and sends results to Telegram
"""

import sys
import os
import json
from datetime import datetime
import pytz

# Try importing Telegram lib - install if needed
try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests -q")
    import requests

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def run_scanner():
    """Run the stock scanner with default configuration"""

    print("🚀 Starting NSE F&O Scanner...")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Default configuration matching Streamlit defaults
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
    }

    results = []
    total_stocks = len(config['stocks_to_scan'])

    print(f"📊 Scanning {total_stocks} F&O stocks...")

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        try:
            # Show progress
            if i % 20 == 0:
                print(f"  Progress: {i}/{total_stocks} ({100*i/total_stocks:.0f}%)")

            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get pattern strength
            max_strength = max(p['strength'] for p in patterns)
            if max_strength < config['pattern_strength_min']:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Filter by RSI
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                continue

            # Filter by ADX
            if current_adx < config['adx_min']:
                continue

            # Stock passed all filters
            stock_result = {
                'symbol': clean_symbol,
                'price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'pattern_strength': max_strength,
                'pattern_type': patterns[0]['type'] if patterns else 'Unknown',
                'confidence': 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            }

            results.append(stock_result)
            print(f"✅ {clean_symbol}: {max_strength:.0f}% - {stock_result['pattern_type']}")

        except Exception as e:
            continue

    return results

def format_telegram_message(results: list) -> str:
    """Format results for Telegram"""
    if not results:
        return "📊 <b>NSE F&O Scanner Results</b>\n\n❌ No stocks matched the filter criteria."

    # Sort by pattern strength
    results.sort(key=lambda x: x['pattern_strength'], reverse=True)

    # Create message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"📊 <b>NSE F&O Scanner Results</b>\n"
    message += f"🕐 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"🎯 Found <b>{len(results)}</b> stocks matching criteria\n\n"

    # Top 15 stocks
    for i, stock in enumerate(results[:15], 1):
        confidence_emoji = "🟢" if stock['confidence'] == 'HIGH' else "🟡" if stock['confidence'] == 'MEDIUM' else "🔴"
        message += f"{i}. <b>{stock['symbol']}</b> {confidence_emoji}\n"
        message += f"   💪 Strength: {stock['pattern_strength']:.0f}% | "
        message += f"💰 ₹{stock['price']:.2f} | "
        message += f"📈 RSI: {stock['rsi']:.0f}\n"
        message += f"   📊 {stock['pattern_type']}\n"
        message += f"   Volume: {stock['volume_ratio']:.1f}x | ADX: {stock['adx']:.0f}\n\n"

    if len(results) > 15:
        message += f"... and <b>{len(results) - 15}</b> more stocks\n\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"Total analyzed: {len(COMPLETE_NSE_FO_UNIVERSE)} stocks"

    return message

def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("🚀 NSE F&O PCS Scanner - Telegram Edition")
    print("="*50 + "\n")

    # Run scanner
    results = run_scanner()

    print(f"\n✅ Scan complete! Found {len(results)} matching stocks\n")

    # Format message
    message = format_telegram_message(results)

    # Print results
    print("\n📨 Message to send:")
    print("-" * 50)
    print(message)
    print("-" * 50 + "\n")

    # Send to Telegram
    print("📤 Sending to Telegram...")
    if send_telegram_message(message):
        print("✅ Message sent successfully!")
    else:
        print("⚠️  Could not send to Telegram")
        print(f"\n💾 Results saved: {len(results)} stocks")

        # Save to JSON as backup
        with open('/tmp/scanner_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("Backup saved to: /tmp/scanner_results.json")

    print("\n" + "="*50)

if __name__ == "__main__":
    main()
