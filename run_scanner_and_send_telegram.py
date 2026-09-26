#!/usr/bin/env python3
"""
Standalone stock scanner that sends qualifying stocks to Telegram.
This script extracts scanning logic from streamlit_app.py and sends results via Telegram.
"""

import os
import sys
import json
from datetime import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import yfinance as yf

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

# Import the scanner class from streamlit_app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

def send_to_telegram(message, telegram_bot_token, telegram_chat_id):
    """Send message to Telegram chat"""
    if not telegram_bot_token or not telegram_chat_id:
        print("Warning: Telegram credentials not configured. Skipping Telegram send.")
        return False

    try:
        import requests
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

        # Split message if too long (Telegram max is 4096 chars)
        max_length = 4000
        if len(message) > max_length:
            messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        else:
            messages = [message]

        for msg in messages:
            payload = {
                'chat_id': telegram_chat_id,
                'text': msg,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Error sending Telegram message: {response.text}")
                return False

        return True
    except Exception as e:
        print(f"Error sending to Telegram: {str(e)}")
        return False

def get_telegram_config():
    """Get Telegram bot token and chat ID from environment or file"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # Also check for local config file
    config_file = os.path.expanduser('~/.telegram_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                token = token or config.get('bot_token')
                chat_id = chat_id or config.get('chat_id')
        except:
            pass

    return token, chat_id

def create_default_filters():
    """Create default filter configuration for scanning"""
    return {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
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
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_news': False,
        'enhancements': {
            'delivery_volume': False,
            'fno_consolidation': False,
            'breakout_pullback': False,
            'enhanced_sr': False,
        }
    }

def scan_stocks(stocks_to_scan, filters, max_workers=5):
    """Scan stocks for patterns with parallel processing"""
    scanner = ProfessionalPCSScanner()
    results = []

    print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks...")
    print(f"📅 Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(scan_single_stock, scanner, symbol, filters): symbol
            for symbol in stocks_to_scan
        }

        # Process results as they complete
        completed = 0
        for future in as_completed(future_to_symbol):
            completed += 1
            symbol = future_to_symbol[future]

            try:
                result = future.result()
                if result:
                    results.append(result)
                    # Print progress
                    if completed % 10 == 0:
                        print(f"✓ Processed {completed}/{len(stocks_to_scan)} stocks...")
            except Exception as e:
                print(f"Error scanning {symbol}: {str(e)}")
                continue

    print(f"\n✅ Scan complete! Found {len(results)} stocks matching criteria.\n")
    return results

def scan_single_stock(scanner, symbol, filters):
    """Scan a single stock"""
    try:
        # Get stock data
        data = scanner.get_stock_data(symbol, period="3mo")
        if data is None:
            return None

        # Check volume criteria
        volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
            data, filters['min_volume_ratio']
        )
        if not volume_ok:
            return None

        # Detect patterns
        patterns = scanner.detect_patterns(data, symbol, filters)
        if not patterns:
            return None

        # Get current metrics
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]

        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume_ratio': volume_ratio,
            'rsi': current_rsi,
            'adx': current_adx,
            'patterns': patterns,
            'data': data,
        }
    except Exception as e:
        return None

def format_telegram_message(results, limit=30):
    """Format scan results for Telegram message"""
    if not results:
        return "No stocks found matching the filter criteria."

    # Sort by strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Limit results for Telegram message length
    results = results[:limit]

    message = "📊 <b>NSE STOCK SCAN RESULTS</b>\n"
    message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"
    message += f"<b>Total Stocks Found:</b> {len(results)}\n\n"

    for idx, result in enumerate(results, 1):
        symbol = result['symbol'].replace('.NS', '').replace('^', '')
        max_strength = max(p['strength'] for p in result['patterns'])
        pattern_type = result['patterns'][0]['type'] if result['patterns'] else 'Unknown'

        # Determine emoji based on strength
        if max_strength >= 85:
            emoji = "🔴"  # High confidence
        elif max_strength >= 70:
            emoji = "🟠"  # Medium confidence
        else:
            emoji = "🟡"  # Low confidence

        message += f"{idx}. {emoji} <b>{symbol}</b>\n"
        message += f"   Price: ₹{result['current_price']:.2f}\n"
        message += f"   Pattern: {pattern_type}\n"
        message += f"   Strength: {max_strength:.0f}% | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"   Volume: {result['volume_ratio']:.1f}x avg\n\n"

    # Add footer
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 <i>Note: Do your own research before trading. Past performance doesn't guarantee future results.</i>"

    return message

def main():
    """Main function to run scanner and send to Telegram"""
    try:
        # Get Telegram config
        telegram_bot_token, telegram_chat_id = get_telegram_config()

        if not telegram_bot_token or not telegram_chat_id:
            print("⚠️ Warning: Telegram credentials not found!")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables, or")
            print("Create ~/.telegram_config.json with bot_token and chat_id")
            print("\nRunning scanner but results will only be printed to console.\n")

        # Create default filters
        filters = create_default_filters()

        # Scan stocks
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        results = scan_stocks(stocks_to_scan, filters, max_workers=8)

        if not results:
            print("❌ No stocks found matching criteria.")
            message = "❌ Scan completed with no results."
        else:
            # Format message
            message = format_telegram_message(results)

        # Print to console
        print("\n" + "="*50)
        print("SCAN RESULTS FOR TELEGRAM:")
        print("="*50)
        print(message)
        print("="*50 + "\n")

        # Send to Telegram
        if telegram_bot_token and telegram_chat_id:
            print("📤 Sending results to Telegram...")
            if send_to_telegram(message, telegram_bot_token, telegram_chat_id):
                print("✅ Successfully sent to Telegram!")
            else:
                print("❌ Failed to send to Telegram")

        # Also save results to file
        if results:
            output_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                # Prepare data for JSON serialization
                json_results = []
                for r in results:
                    json_results.append({
                        'symbol': r['symbol'],
                        'current_price': float(r['current_price']),
                        'volume_ratio': float(r['volume_ratio']),
                        'rsi': float(r['rsi']),
                        'adx': float(r['adx']),
                        'patterns': [
                            {
                                'type': p['type'],
                                'strength': float(p['strength']),
                                'success_rate': p.get('success_rate', 0),
                                'confidence': p.get('confidence', 'UNKNOWN'),
                            }
                            for p in r['patterns']
                        ]
                    })
                json.dump(json_results, f, indent=2)
            print(f"💾 Results saved to {output_file}")

        return 0

    except KeyboardInterrupt:
        print("\n⛔ Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
