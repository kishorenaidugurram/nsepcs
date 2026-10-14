#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Automation
Runs stock screening and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import pytz
import asyncio

# Add the project directory to path
sys.path.insert(0, '/home/user/nsepcs')

def run_telegram_screener():
    """Run the screener and send results to Telegram"""

    # Import the required modules
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
        import ta
        from bs4 import BeautifulSoup
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import warnings
        warnings.filterwarnings('ignore')
    except ImportError as e:
        print(f"Error importing required libraries: {e}")
        print("Please install dependencies: pip install yfinance pandas numpy ta beautifulsoup4 requests")
        return False

    print("=" * 60)
    print("NSE F&O PCS SCREENER - TELEGRAM AUTOMATION")
    print("=" * 60)

    # Get Telegram credentials from environment
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("\n⚠️  WARNING: Telegram credentials not found!")
        print("   Set environment variables:")
        print("   - TELEGRAM_BOT_TOKEN: Your bot token")
        print("   - TELEGRAM_CHAT_ID: Your chat ID")
        print("\nProceeding with file output only...\n")
        send_telegram = False
    else:
        print(f"\n✓ Telegram configured")
        print(f"  Chat ID: {telegram_chat_id}")
        send_telegram = True

    # Import scanner class from streamlit app
    # We'll execute only the necessary parts without Streamlit
    try:
        # Read and parse the streamlit app to extract the scanner class
        with open('/home/user/nsepcs/streamlit_app.py', 'r') as f:
            content = f.read()

        # Extract everything up to the main() function
        scanner_code = content.split('def main():')[0]

        # Remove Streamlit-specific decorators and calls
        scanner_code = scanner_code.replace('@st.', '@')
        scanner_code = scanner_code.replace('st.', '')

        # Execute the code to get the classes
        exec_globals = {}
        exec(scanner_code, exec_globals)

        ProfessionalPCSScanner = exec_globals['ProfessionalPCSScanner']
        COMPLETE_NSE_FO_UNIVERSE = exec_globals['COMPLETE_NSE_FO_UNIVERSE']

    except Exception as e:
        print(f"Error loading scanner: {e}")
        return False

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Default configuration for automated screening
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50],  # Scan first 50 stocks for speed
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
        'analysis_mode': 'Daily Only (V6.0 Style)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': False,
    }

    print(f"\n📊 Scanning {len(config['stocks_to_scan'])} stocks...")
    print(f"   Filter: RSI {config['rsi_min']}-{config['rsi_max']}, ADX min {config['adx_min']}")
    print(f"   Min Pattern Strength: {config['pattern_strength_min']}%")

    results = []
    failed_stocks = []

    # Scan stocks
    for i, symbol in enumerate(config['stocks_to_scan']):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                failed_stocks.append(clean_symbol)
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
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

            # Calculate strength
            max_strength = max(p['strength'] for p in patterns)
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            # Add to results
            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'max_strength': max_strength,
                'confidence': overall_confidence
            }
            results.append(result)

            print(f"  ✓ {clean_symbol} - {overall_confidence} ({max_strength:.0f}%)")

        except Exception as e:
            failed_stocks.append(clean_symbol)
            continue

    print(f"\n" + "=" * 60)
    print(f"SCREENING RESULTS")
    print("=" * 60)

    if not results:
        message = "❌ No stocks found matching the filter criteria today"
        print(f"\n{message}")
    else:
        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        # Prepare message
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        message = f"""
🎯 NSE F&O PCS SCREENER RESULTS
📅 {current_time}

📊 STOCKS FOUND: {len(results)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        for i, result in enumerate(results, 1):
            confidence_emoji = '🟢' if result['confidence'] == 'HIGH' else '🟡' if result['confidence'] == 'MEDIUM' else '🔴'

            stock_msg = f"""{i}. {result['symbol']} {confidence_emoji}
   Price: ₹{result['price']:.2f}
   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f} | Vol: {result['volume_ratio']:.1f}x
   Strength: {result['max_strength']:.0f}%
   Patterns: {len(result['patterns'])}

"""
            message += stock_msg

        message += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  DISCLAIMER: This is for informational purposes only.
    Not financial advice. Trade at your own risk.
    Always use proper risk management and stop losses.

🔗 Open Scanner: https://nse-fo-pcs-screener.streamlit.app
"""

        print("\n" + message)

    # Save results to file
    output_file = f"/home/user/nsepcs/screening_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(output_file, 'w') as f:
            f.write(message)
        print(f"\n✓ Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")

    # Send to Telegram
    if send_telegram:
        try:
            print(f"\n📤 Sending to Telegram...")
            send_to_telegram(telegram_token, telegram_chat_id, message)
            print(f"✓ Message sent to Telegram!")
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")
            print("   Results saved to file instead")

    return True


def send_to_telegram(token, chat_id, message):
    """Send message to Telegram"""
    try:
        from telegram import Bot

        bot = Bot(token=token)
        # Run async function in a new event loop
        asyncio.run(bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML' if '<' in message else None
        ))
        return True
    except Exception as e:
        # Fallback to requests library
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(f"Telegram API error: {response.text}")
        return True


if __name__ == "__main__":
    print("\n🚀 Starting NSE F&O PCS Screener - Telegram Edition\n")

    success = run_telegram_screener()

    if success:
        print("\n✅ Screening completed successfully!")
    else:
        print("\n❌ Screening failed!")
        sys.exit(1)
