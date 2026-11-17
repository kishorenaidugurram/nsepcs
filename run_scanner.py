#!/usr/bin/env python3
"""
Standalone NSE PCS Scanner - Runs without Streamlit and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz
import pandas as pd
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, '/home/user/nsepcs')

# Import the scanner class from streamlit_app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

def get_default_filters():
    """Get default filter configuration"""
    return {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:100],  # Scan first 100 F&O stocks
        'rsi_min': 30,
        'rsi_max': 70,
        'adx_min': 15,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.0,
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
        'analysis_mode': 'Daily + Weekly',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'export_results': False,
        'stocks_limit': 100
    }

def run_scanner(config):
    """Run the scanner and return results"""
    scanner = ProfessionalPCSScanner()
    results = []

    total_stocks = len(config['stocks_to_scan'])
    print(f"\n🔍 Starting scan of {total_stocks} stocks...")

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        print(f"[{i:3d}/{total_stocks}] Scanning {symbol.replace('.NS', ''):<15}", end='\r')

        try:
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

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
            result = {
                'symbol': symbol.replace('.NS', ''),
                'current_price': float(current_price),
                'volume_ratio': float(volume_ratio),
                'rsi': float(current_rsi),
                'adx': float(current_adx),
                'patterns': [
                    {
                        'type': p['type'],
                        'strength': float(p['strength']),
                        'confidence': p['confidence'],
                        'success_rate': float(p['success_rate']),
                        'pcs_suitability': float(p['pcs_suitability'])
                    }
                    for p in patterns
                ]
            }

            results.append(result)

        except Exception as e:
            continue

    print(f"\n✅ Scan complete! Found {len(results)} stocks with patterns\n")
    return results

def format_telegram_message(results, max_stocks=20):
    """Format results for Telegram message"""
    if not results:
        return "❌ No stocks found matching the filter criteria."

    # Sort by pattern strength
    results_sorted = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )[:max_stocks]

    # Build message
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"🎯 *NSE PCS Stock Scanner Results*\n"
    message += f"⏰ {timestamp}\n"
    message += f"📊 Found: *{len(results)} stocks* with valid patterns\n"
    message += "━" * 50 + "\n\n"

    for i, result in enumerate(results_sorted, 1):
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
        pattern_types = ', '.join([p['type'] for p in result['patterns'][:2]])

        emoji = "🟢" if confidence == 'HIGH' else "🟡" if confidence == 'MEDIUM' else "🔴"

        message += f"{i:2d}. *{result['symbol']}* {emoji}\n"
        message += f"    💰 ₹{result['current_price']:.2f}\n"
        message += f"    📈 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"    🔥 Strength: {max_strength:.0f}% ({confidence})\n"
        message += f"    🎯 Pattern: {pattern_types}\n"
        message += f"    📊 Volume: {result['volume_ratio']:.1f}x\n"
        message += "\n"

    message += "━" * 50 + "\n"
    message += "_Use web scanner for detailed charts and analysis_"

    return message

def send_to_telegram(message, telegram_token=None, telegram_chat_id=None):
    """Send message to Telegram"""
    if not telegram_token or not telegram_chat_id:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("⚠️  Telegram credentials not found in environment variables")
        print("    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to send results")
        print("\n📋 Would have sent the following to Telegram:\n")
        print(message)
        return False

    try:
        import requests

        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False

def save_results_to_file(results):
    """Save results to JSON file"""
    output_file = '/tmp/claude-0/-home-user-nsepcs/58571b9b-3a7d-5f8c-b559-fcc07912d4e8/scratchpad/scan_results.json'

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return output_file

def main():
    print("\n" + "="*60)
    print("🚀 NSE PCS Stock Scanner - Automated Run")
    print("="*60)

    # Get default filters
    config = get_default_filters()

    # Run scanner
    results = run_scanner(config)

    if not results:
        print("❌ No stocks found matching filter criteria")
        message = "❌ No stocks found matching the filter criteria."
        send_to_telegram(message)
        return 1

    # Format and send message
    message = format_telegram_message(results, max_stocks=20)

    # Save results to file
    results_file = save_results_to_file(results)
    print(f"📁 Results saved to: {results_file}")

    # Send to Telegram
    send_to_telegram(message)

    # Display message locally as well
    print("\n" + message)

    return 0

if __name__ == "__main__":
    sys.exit(main())
