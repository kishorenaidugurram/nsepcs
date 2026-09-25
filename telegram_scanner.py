#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notification Script
Scans stocks for PCS opportunities and sends results to Telegram
"""

import os
import json
import requests
import sys
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import from streamlit_app
sys.path.insert(0, os.path.dirname(__file__))
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Configuration file
CONFIG_FILE = '/tmp/telegram_scanner_config.json'

def load_telegram_config():
    """Load Telegram config from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('bot_token'), config.get('chat_id')
        except:
            pass
    return None, None

def save_telegram_config(bot_token, chat_id):
    """Save Telegram config to file"""
    config = {
        'bot_token': bot_token,
        'chat_id': chat_id,
        'saved_at': datetime.now().isoformat()
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_stock_result(result):
    """Format a stock result for display"""
    symbol = result['symbol'].replace('.NS', '')
    score = result.get('score', 0)
    confidence = result.get('confidence', 'N/A')
    patterns = result.get('patterns', [])

    pattern_str = ', '.join([p['type'] for p in patterns[:2]]) if patterns else 'N/A'

    return f"<b>{symbol}</b>\nScore: {score:.0f} | {confidence}\nPattern: {pattern_str}"

def scan_stocks_batch(scanner, symbols, config):
    """Scan a batch of stocks"""
    results = []

    for symbol in symbols:
        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check basic criteria
            current_close = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Apply filters
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                continue

            if current_adx < config['adx_min']:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, _ = scanner.check_volume_criteria(
                data, min_ratio=config['min_volume_ratio']
            )

            if not volume_ok:
                continue

            # Detect patterns
            patterns = []

            # Check current day breakout
            breakout_detected, breakout_strength, breakout_details = scanner.detect_current_day_breakout(
                data, lookback_days=config['lookback_days'],
                min_volume_ratio=config['volume_breakout_ratio']
            )

            if breakout_detected and breakout_strength >= config['pattern_strength_min']:
                patterns.append({
                    'type': 'Current Day Breakout',
                    'strength': breakout_strength,
                    'confidence': scanner.get_confidence_level(breakout_strength)
                })

            # Check other patterns (cup and handle, double bottom, etc.)
            weekly_data = scanner.get_weekly_stock_data(symbol, period="6mo")

            if weekly_data is not None:
                # Cup and handle
                cup_detected, cup_strength = scanner.detect_weekly_cup_and_handle(weekly_data)
                if cup_detected and cup_strength >= config['pattern_strength_min']:
                    patterns.append({
                        'type': 'Cup & Handle',
                        'strength': cup_strength,
                        'confidence': scanner.get_confidence_level(cup_strength)
                    })

                # Double bottom
                double_bottom_detected, double_bottom_strength = scanner.detect_weekly_double_bottom(weekly_data)
                if double_bottom_detected and double_bottom_strength >= config['pattern_strength_min']:
                    patterns.append({
                        'type': 'Double Bottom',
                        'strength': double_bottom_strength,
                        'confidence': scanner.get_confidence_level(double_bottom_strength)
                    })

            # Calculate score based on patterns
            if patterns:
                avg_strength = sum([p['strength'] for p in patterns]) / len(patterns)

                results.append({
                    'symbol': symbol,
                    'score': avg_strength,
                    'confidence': patterns[0]['confidence'],
                    'patterns': patterns,
                    'data': data
                })

        except Exception as e:
            continue

    return results

def main():
    """Main function"""
    print("=" * 60)
    print("NSE F&O PCS Scanner - Telegram Notifier")
    print("=" * 60)

    # Check for Telegram credentials
    bot_token, chat_id = load_telegram_config()

    if not bot_token or not chat_id:
        print("\n⚠️  Telegram credentials not found.")
        print("\nPlease provide your Telegram credentials:")
        bot_token = input("Enter your Telegram Bot Token: ").strip()
        chat_id = input("Enter your Chat ID: ").strip()

        if save_telegram_config(bot_token, chat_id):
            print("✅ Credentials saved for future use")
        else:
            print("⚠️  Could not save credentials, will use for this run only")
    else:
        print(f"✅ Using saved Telegram credentials")

    # Test Telegram connection
    print("\n📤 Testing Telegram connection...")
    test_msg = "🤖 PCS Scanner initialized at " + datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M IST')
    if not send_telegram_message(bot_token, chat_id, test_msg):
        print("❌ Could not connect to Telegram. Please check your token and chat ID.")
        sys.exit(1)

    print("✅ Connected to Telegram")

    # Initialize scanner
    print("\n🔍 Initializing PCS Scanner...")
    scanner = ProfessionalPCSScanner()

    # Default configuration
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65
    }

    print(f"Filter Settings:")
    print(f"  RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"  ADX Min: {config['adx_min']}")
    print(f"  Min Volume Ratio: {config['min_volume_ratio']}x")
    print(f"  Pattern Strength Min: {config['pattern_strength_min']}%")

    # Scan stocks
    print(f"\n📊 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} NSE F&O stocks...")

    results = scan_stocks_batch(scanner, COMPLETE_NSE_FO_UNIVERSE, config)

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    # Prepare telegram message
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"<b>📊 PCS Scanner Results</b>\n"
    message += f"<i>{current_time.strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"
    message += f"<b>Found {len(results)} qualifying stocks</b>\n"
    message += f"<i>(Strength ≥ {config['pattern_strength_min']}%)</i>\n\n"

    # Add top 10 stocks
    if results:
        message += "<b>TOP 10 PICKS:</b>\n"
        message += "=" * 30 + "\n"

        for i, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            score = result['score']
            patterns = ' + '.join([p['type'][:15] for p in result['patterns'][:2]])

            message += f"{i}. <b>{symbol}</b> ({score:.0f})\n"
            message += f"   {patterns}\n"

        # Send results
        print("\n📤 Sending results to Telegram...")
        if send_telegram_message(bot_token, chat_id, message):
            print(f"✅ Sent {len(results)} results to Telegram")
        else:
            print("❌ Failed to send results")

        # Also save to file
        results_file = '/tmp/pcs_scanner_results.json'
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': current_time.isoformat(),
                    'total_results': len(results),
                    'top_10': [{
                        'symbol': r['symbol'],
                        'score': r['score'],
                        'confidence': r['confidence'],
                        'patterns': [p['type'] for p in r['patterns']]
                    } for r in results[:10]]
                }, f, indent=2)
            print(f"✅ Results saved to {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results to file: {e}")
    else:
        message += "<i>No stocks found meeting the criteria.</i>\n"
        message += "Try adjusting filter settings."

        if send_telegram_message(bot_token, chat_id, message):
            print("✅ Notification sent to Telegram")
        else:
            print("❌ Failed to send notification")

    print("\n✅ Scanner completed")

if __name__ == '__main__':
    main()
