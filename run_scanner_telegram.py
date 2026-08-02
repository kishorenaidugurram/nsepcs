#!/usr/bin/env python3
"""
Standalone scanner script - runs the NSE F&O stock scanner without Streamlit UI
and sends results to Telegram.
"""

import sys
import os
import json
from datetime import datetime
import pytz
import pandas as pd
import requests
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner from streamlit app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

def send_to_telegram(message: str, chat_id: str = None, bot_token: str = None) -> bool:
    """
    Send message to Telegram chat

    Environment variables:
    - TELEGRAM_BOT_TOKEN: Telegram bot token
    - TELEGRAM_CHAT_ID: Telegram chat ID (can also be passed as parameter)
    """
    if not bot_token:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not chat_id:
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("❌ Telegram credentials not configured")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def format_results_for_telegram(results: list, config: dict) -> str:
    """Format scan results into a Telegram message"""
    if not results:
        return "No stocks met the filter criteria today."

    # Sort by pattern strength
    sorted_results = sorted(results, key=lambda x: x.get('pattern_strength', 0), reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%d-%b-%Y %H:%M IST')

    message = f"<b>NSE F&O Stock Scanner Results</b>\n"
    message += f"<i>Generated: {current_time}</i>\n"
    message += f"📊 Stocks Found: <b>{len(sorted_results)}</b>\n"
    message += "─" * 40 + "\n\n"

    for idx, result in enumerate(sorted_results[:20], 1):  # Limit to top 20
        symbol = result['symbol'].replace('.NS', '')
        price = result.get('current_price', 'N/A')
        patterns = result.get('patterns', [])
        pattern_names = [p.get('name', 'Unknown') for p in patterns[:2]]  # Top 2 patterns
        strength = result.get('pattern_strength', 0)

        pattern_str = ' + '.join(pattern_names) if pattern_names else 'N/A'

        message += f"{idx}. <b>{symbol}</b>\n"
        message += f"   💰 Price: ₹{price}\n"
        message += f"   📈 Patterns: {pattern_str}\n"
        message += f"   💪 Strength: {strength:.0f}%\n"
        message += "\n"

    if len(sorted_results) > 20:
        message += f"... and {len(sorted_results) - 20} more stocks\n"

    message += "─" * 40 + "\n"
    message += "⚠️ <i>This is for informational purposes only. Not financial advice.</i>\n"
    message += "🔗 <i>Access full analysis: Run streamlit locally or deploy</i>"

    return message

def run_scanner_with_defaults():
    """
    Run scanner with default filter criteria
    Default settings from create_professional_sidebar():
    - RSI Min: 30, Max: 75
    - ADX Min: 20
    - Moving Average: EMA, 3% tolerance
    - Min Volume Ratio: 1.2
    - Breakout Volume Ratio: 2.0
    - Lookback: 20 days
    - Pattern Strength Min: 65
    - Analysis Mode: Daily + Weekly Combined
    """

    print("🚀 Starting NSE F&O Stock Scanner")
    print(f"📅 Date: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d-%b-%Y %H:%M:%S IST')}")
    print(f"📊 Stocks to scan: {len(COMPLETE_NSE_FO_UNIVERSE)}")
    print("─" * 60)

    # Configuration with defaults
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
        'show_charts': False,
        'show_news': False,
    }

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []

    # Scan stocks
    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            if i % 20 == 0:
                print(f"⏳ Progress: {i}/{len(config['stocks_to_scan'])} ({100*i//len(config['stocks_to_scan'])}%)")

            # Get data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or data.empty:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Calculate average pattern strength
            avg_strength = sum(p.get('strength', 0) for p in patterns) / len(patterns) if patterns else 0

            result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'current_rsi': current_rsi,
                'current_adx': current_adx,
                'patterns': patterns,
                'pattern_strength': avg_strength,
                'volume_ratio': volume_ratio,
            }

            results.append(result)
            print(f"✓ {clean_symbol}: {len(patterns)} pattern(s) detected")

        except Exception as e:
            pass  # Silently skip failed stocks

    return results, config

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("NSE F&O PCS SCANNER - TELEGRAM NOTIFIER")
    print("="*60 + "\n")

    # Run scanner
    results, config = run_scanner_with_defaults()

    print(f"\n📊 SCAN COMPLETE")
    print(f"✅ Total stocks meeting criteria: {len(results)}")
    print("─" * 60)

    # Format message
    telegram_message = format_results_for_telegram(results, config)

    # Print to console
    print("\n📱 Message to be sent to Telegram:")
    print("─" * 60)
    print(telegram_message)
    print("─" * 60)

    # Save results to JSON
    results_file = '/tmp/scanner_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            'stocks_found': len(results),
            'results': [
                {
                    'symbol': r['clean_symbol'],
                    'price': float(r['current_price']),
                    'rsi': float(r['current_rsi']),
                    'adx': float(r['current_adx']),
                    'patterns': [p.get('name') for p in r.get('patterns', [])],
                    'strength': float(r.get('pattern_strength', 0)),
                }
                for r in results[:50]
            ]
        }, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")

    # Send to Telegram
    print(f"\n📤 Sending to Telegram...")
    send_to_telegram(telegram_message)

    print("\n✅ Scanner execution completed!")
    return results

if __name__ == "__main__":
    main()
