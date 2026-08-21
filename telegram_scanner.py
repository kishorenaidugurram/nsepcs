#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Results Sender
Runs the PCS scanner and sends matching stocks to Telegram
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import warnings
warnings.filterwarnings('ignore')

# Import from streamlit_app
from streamlit_app import (
    COMPLETE_NSE_FO_UNIVERSE,
    ProfessionalPCSScanner,
)

def get_telegram_config():
    """Get Telegram bot token and chat ID from environment variables"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        raise ValueError(
            "Telegram credentials not found. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
        )

    return bot_token, chat_id

def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send message: {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_results_for_telegram(results):
    """Format scanner results for Telegram"""
    if not results:
        return "❌ No stocks meeting the filter criteria found."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"""
📊 <b>NSE F&O PCS Scanner Results</b>
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}
✨ <b>Stocks Found:</b> {len(results)}

"""

    # Sort by PCS score descending
    sorted_results = sorted(results, key=lambda x: x.get('pcs_score', 0), reverse=True)

    for i, result in enumerate(sorted_results[:25], 1):  # Limit to top 25
        symbol = result['symbol'].replace('.NS', '')
        score = result.get('pcs_score', 0)
        confidence = result.get('confidence', 'N/A')
        price = result.get('price', 'N/A')

        if isinstance(price, (int, float)):
            price_str = f"₹{price:.2f}"
        else:
            price_str = str(price)

        message += f"{i}. <b>{symbol}</b>\n"
        message += f"   PCS: {score:.0f} | {confidence}\n"
        message += f"   Price: {price_str}\n\n"

    if len(results) > 25:
        message += f"... and {len(results) - 25} more stocks\n\n"

    message += """
📈 <b>Analysis Settings:</b>
• RSI: 30-75
• ADX Min: 20
• Volume Ratio: 1.2x
• Pattern Strength: 65%+
• Timeframe: Daily + Weekly
"""

    return message

def run_scanner(stocks_to_scan=None, pattern_strength_min=65):
    """Run the PCS scanner with default settings"""
    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    print(f"Starting PCS scanner on {len(stocks_to_scan)} stocks...")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Configuration with defaults
    config = {
        'stocks_to_scan': stocks_to_scan,
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': pattern_strength_min,
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
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'export_results': False,
    }

    results = []

    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            print(f"[{i}/{len(stocks_to_scan)}] Analyzing {symbol.replace('.NS', '')}...", end='\r')

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")

            if data is None or data.empty:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)

            if patterns:
                # Calculate PCS score
                pcs_score = sum([p.get('strength', 0) for p in patterns]) / len(patterns) if patterns else 0

                if pcs_score >= pattern_strength_min:
                    result = {
                        'symbol': symbol,
                        'pcs_score': pcs_score,
                        'patterns': patterns,
                        'price': data['Close'].iloc[-1] if len(data) > 0 else None,
                        'confidence': patterns[0].get('confidence', 'MEDIUM') if patterns else 'LOW'
                    }
                    results.append(result)
                    print(f"✓ {symbol.replace('.NS', '')}: {pcs_score:.0f}")

        except Exception as e:
            print(f"✗ Error analyzing {symbol}: {e}")
            continue

    print(f"\n✅ Scan complete. Found {len(results)} qualifying stocks.")
    return results

def main():
    """Main execution function"""
    try:
        # Get Telegram credentials
        bot_token, chat_id = get_telegram_config()
        print(f"✓ Telegram credentials loaded")

        # Run scanner
        results = run_scanner()

        # Format and send results
        message = format_results_for_telegram(results)

        print(f"📤 Sending {len(results)} results to Telegram...")
        if send_telegram_message(bot_token, chat_id, message):
            print("✅ Message sent successfully!")
            return 0
        else:
            print("❌ Failed to send message")
            return 1

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nUsage:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("  python telegram_scanner.py")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
