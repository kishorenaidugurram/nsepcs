#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notification Script
Scans stocks for PCS opportunities and sends results to Telegram
"""

import os
import json
import sys
from datetime import datetime
import pytz
import pandas as pd

# Import from streamlit_app
sys.path.insert(0, os.path.dirname(__file__))
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

def send_telegram_message(bot_token, chat_id, message):
    """Send message to Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def scan_stocks(scanner, symbols, config):
    """Scan stocks and return qualifying results"""
    print(f"\nScanning {len(symbols)} stocks...")
    results = []
    processed = 0

    for idx, symbol in enumerate(symbols, 1):
        processed = idx
        if idx % 20 == 0:
            print(f"  Progress: {idx}/{len(symbols)}")

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 30:
                continue

            # Check basic criteria
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Apply RSI filter
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                continue

            # Apply ADX filter
            if current_adx < config['adx_min']:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, vol_details = scanner.check_volume_criteria(
                data, min_ratio=config['min_volume_ratio']
            )
            if not volume_ok:
                continue

            # Detect current day breakout
            breakout_detected, breakout_strength, breakout_details = scanner.detect_current_day_breakout(
                data, lookback_days=config['lookback_days'],
                min_volume_ratio=config['volume_breakout_ratio']
            )

            if breakout_detected and breakout_strength >= config['pattern_strength_min']:
                # Get additional info
                current_price = data['Close'].iloc[-1]

                results.append({
                    'symbol': symbol.replace('.NS', ''),
                    'score': breakout_strength,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'price': current_price,
                    'pattern': 'Current Day Breakout',
                    'volume_ratio': volume_ratio
                })

        except Exception as e:
            continue

    print(f"Processed {processed} stocks, found {len(results)} matches")
    return results

def main():
    """Main function"""
    print("=" * 70)
    print("NSE F&O PCS Scanner - Telegram Notifier")
    print("=" * 70)

    # Get Telegram credentials from environment variables
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    telegram_available = bot_token and chat_id

    if telegram_available:
        print("\n[INFO] Telegram credentials found in environment variables")
    else:
        print("\n[INFO] Telegram not configured. Results will be saved to file.")
        print("[INFO] To enable Telegram, set:")
        print("       export TELEGRAM_BOT_TOKEN=<your_token>")
        print("       export TELEGRAM_CHAT_ID=<your_chat_id>")

    # Initialize scanner
    print("\n[*] Initializing PCS Scanner...")
    scanner = ProfessionalPCSScanner()

    # Default configuration (matching Streamlit defaults)
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65
    }

    print("\n[*] Filter Configuration:")
    print(f"    RSI Range: {config['rsi_min']}-{config['rsi_max']}")
    print(f"    ADX Min: {config['adx_min']}")
    print(f"    Min Volume Ratio: {config['min_volume_ratio']}x")
    print(f"    Breakout Volume: {config['volume_breakout_ratio']}x")
    print(f"    Lookback Days: {config['lookback_days']}")
    print(f"    Pattern Strength Min: {config['pattern_strength_min']}%")

    # Scan stocks
    results = scan_stocks(scanner, COMPLETE_NSE_FO_UNIVERSE, config)

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    # Prepare timestamp
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    timestamp_str = current_time.strftime('%Y-%m-%d %H:%M IST')

    # Prepare message
    message = f"[PCS SCANNER RESULTS]\nTime: {timestamp_str}\n\n"
    message += f"Found: {len(results)} qualifying stocks\n"
    message += f"(Pattern Strength >= {config['pattern_strength_min']}%)\n\n"

    if results:
        message += "TOP 10 PICKS:\n"
        message += "=" * 50 + "\n"

        # Format results
        for i, r in enumerate(results[:10], 1):
            message += f"{i}. {r['symbol']:12s} Score: {r['score']:3.0f}  RSI: {r['rsi']:5.1f}  ADX: {r['adx']:5.1f}\n"

        # Save to JSON file
        json_file = '/tmp/pcs_scanner_results.json'
        try:
            with open(json_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp_str,
                    'total_results': len(results),
                    'stocks': results[:10]
                }, f, indent=2)
            print(f"\n[+] Results saved to {json_file}")
        except Exception as e:
            print(f"[-] Could not save results: {e}")

        # Send to Telegram if available
        if telegram_available:
            print("\n[*] Sending to Telegram...")
            telegram_message = f"<b>PCS Scanner Results</b>\n"
            telegram_message += f"<i>{timestamp_str}</i>\n\n"
            telegram_message += f"<b>{len(results)} stocks found</b>\n\n"
            telegram_message += "<b>Top 10:</b>\n"
            for i, r in enumerate(results[:10], 1):
                telegram_message += f"{i}. <b>{r['symbol']}</b> - Score: {r['score']:.0f}\n"

            if send_telegram_message(bot_token, chat_id, telegram_message):
                print("[+] Results sent to Telegram successfully")
            else:
                print("[-] Failed to send to Telegram")
    else:
        message += "No stocks found matching the filter criteria.\n"
        print("\n[!] No qualifying stocks found")

        if telegram_available:
            print("[*] Sending notification to Telegram...")
            if send_telegram_message(bot_token, chat_id, message):
                print("[+] Notification sent")

    # Print results to stdout
    print("\n" + "=" * 70)
    print(message)
    print("=" * 70)

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
