#!/usr/bin/env python3
"""
Standalone stock screening script that runs the scanner and sends results to Telegram
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# Install ta stub before importing streamlit_app
sys.path.insert(0, '/tmp')
import ta_stub
sys.modules['ta'] = ta_stub

# Import the scanner class from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

def send_to_telegram(message: str, telegram_token: str = None, telegram_chat_id: str = None) -> bool:
    """
    Send message to Telegram using bot API

    Args:
        message: Message to send
        telegram_token: Bot token (can also come from env var TELEGRAM_BOT_TOKEN)
        telegram_chat_id: Chat ID (can also come from env var TELEGRAM_CHAT_ID)

    Returns:
        True if sent successfully, False otherwise
    """
    token = telegram_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = telegram_chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("⚠️  Telegram credentials not found.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send to Telegram: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False


def format_results_for_telegram(results: list) -> str:
    """
    Format stock screening results for Telegram message
    """
    if not results:
        return "🔍 No stocks found matching the filter criteria."

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%d-%m-%Y %H:%M IST')

    message = f"""<b>📊 Stock Screening Results</b>
<i>Time: {timestamp}</i>
<i>Found: {len(results)} stocks</i>

"""

    for i, result in enumerate(results, 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        patterns = result['patterns']

        if patterns:
            pattern_names = [p['type'] for p in patterns[:2]]  # Top 2 patterns
            pattern_str = ", ".join(pattern_names)
            strength = max(p['strength'] for p in patterns)
        else:
            pattern_str = "N/A"
            strength = 0

        message += f"""{i}. <b>{symbol}</b>
   Price: ₹{price:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}
   Patterns: {pattern_str}
   Strength: {strength:.0f}%

"""

    return message


def run_screening(
    stocks_to_scan: list = None,
    rsi_min: int = 30,
    rsi_max: int = 75,
    adx_min: int = 20,
    min_volume_ratio: float = 1.2,
    pattern_strength_min: int = 65,
    max_workers: int = 10,
    limit: int = None
) -> list:
    """
    Run the stock screening with given filters

    Args:
        stocks_to_scan: List of stock symbols to scan
        rsi_min: Minimum RSI value
        rsi_max: Maximum RSI value
        adx_min: Minimum ADX value
        min_volume_ratio: Minimum volume ratio
        pattern_strength_min: Minimum pattern strength
        max_workers: Number of concurrent workers
        limit: Limit number of results

    Returns:
        List of stocks meeting criteria
    """

    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    scanner = ProfessionalPCSScanner()

    # Prepare config
    config = {
        'stocks_to_scan': stocks_to_scan,
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'adx_min': adx_min,
        'min_volume_ratio': min_volume_ratio,
        'pattern_strength_min': pattern_strength_min,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
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

    results = []
    print(f"🚀 Starting scan of {len(stocks_to_scan)} stocks...")
    print(f"⚙️  Filters: RSI({rsi_min}-{rsi_max}), ADX>{adx_min}, Volume>{min_volume_ratio}x, Strength>{pattern_strength_min}%")
    print()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {}

        for symbol in stocks_to_scan:
            future = executor.submit(_scan_single_stock, scanner, symbol, config)
            future_to_symbol[future] = symbol

        completed = 0
        for future in as_completed(future_to_symbol):
            completed += 1
            symbol = future_to_symbol[future]
            clean_symbol = symbol.replace('.NS', '')

            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"✅ {clean_symbol:<12} - Found {len(result['patterns'])} pattern(s)")
            except Exception as e:
                print(f"❌ {clean_symbol:<12} - Error: {str(e)[:50]}")

            # Progress update every 20 stocks
            if completed % 20 == 0:
                print(f"   Progress: {completed}/{len(stocks_to_scan)}")

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Apply limit if specified
    if limit:
        results = results[:limit]

    return results


def _scan_single_stock(scanner, symbol: str, config: dict) -> dict:
    """
    Scan a single stock
    """
    try:
        # Get recent data
        data = scanner.get_stock_data(symbol, period="3mo")
        if data is None:
            return None

        # Check volume criteria
        volume_ok, volume_ratio, _ = scanner.check_volume_criteria(data, config['min_volume_ratio'])
        if not volume_ok:
            return None

        # Detect patterns
        patterns = scanner.detect_patterns(data, symbol, config)
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
            'data': data
        }
    except Exception as e:
        return None


def save_results_to_file(results: list, filename: str = None) -> str:
    """
    Save results to a JSON file
    """
    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/claude-0/-home-user-nsepcs/3f2b3d83-9feb-56b3-a2cf-c917d295ccd7/scratchpad/stock_scan_{timestamp}.json"

    # Convert results to JSON-serializable format
    json_results = []
    for r in results:
        json_results.append({
            'symbol': r['symbol'],
            'current_price': float(r['current_price']),
            'rsi': float(r['rsi']),
            'adx': float(r['adx']),
            'volume_ratio': float(r['volume_ratio']),
            'patterns': [
                {
                    'type': p['type'],
                    'strength': float(p['strength']),
                    'confidence': p.get('confidence', 'N/A'),
                    'description': p.get('description', '')
                }
                for p in r['patterns']
            ]
        })

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2)

    return filename


def main():
    """Main function to run screening and send to Telegram"""

    print("\n" + "="*60)
    print("NSE F&O PCS Stock Screening - Telegram Integration")
    print("="*60 + "\n")

    # Get parameters from environment or use defaults
    rsi_min = int(os.getenv('SCAN_RSI_MIN', 30))
    rsi_max = int(os.getenv('SCAN_RSI_MAX', 75))
    adx_min = int(os.getenv('SCAN_ADX_MIN', 20))
    min_volume_ratio = float(os.getenv('SCAN_MIN_VOLUME_RATIO', 1.2))
    pattern_strength_min = int(os.getenv('SCAN_PATTERN_STRENGTH_MIN', 65))
    max_stocks = int(os.getenv('SCAN_MAX_STOCKS', 219))
    max_results = int(os.getenv('SCAN_MAX_RESULTS', 20))

    print(f"📋 Configuration:")
    print(f"   RSI Range: {rsi_min}-{rsi_max}")
    print(f"   ADX Minimum: {adx_min}")
    print(f"   Min Volume Ratio: {min_volume_ratio}x")
    print(f"   Pattern Strength: {pattern_strength_min}%")
    print(f"   Max Stocks to Scan: {max_stocks}")
    print(f"   Max Results to Report: {max_results}")
    print()

    # Run scanning
    stocks = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]
    results = run_screening(
        stocks_to_scan=stocks,
        rsi_min=rsi_min,
        rsi_max=rsi_max,
        adx_min=adx_min,
        min_volume_ratio=min_volume_ratio,
        pattern_strength_min=pattern_strength_min,
        limit=max_results
    )

    print()
    print(f"✅ Scan complete! Found {len(results)} stocks meeting criteria.")
    print()

    if results:
        # Save to file
        filename = save_results_to_file(results)
        print(f"💾 Results saved to: {filename}")
        print()

        # Format for Telegram
        telegram_message = format_results_for_telegram(results)

        # Try to send to Telegram
        print("📤 Attempting to send to Telegram...")
        telegram_sent = send_to_telegram(telegram_message)

        if telegram_sent:
            print("\n✅ All done! Results sent to Telegram.")
        else:
            print("\n⚠️  Results saved locally but not sent to Telegram.")
            print("   To enable Telegram, set:")
            print("   - TELEGRAM_BOT_TOKEN: Your Telegram bot token")
            print("   - TELEGRAM_CHAT_ID: Your Telegram chat ID")

        # Also print summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(telegram_message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<br>', '\n'))
    else:
        print("❌ No stocks found matching the criteria.")

        # Try to send empty result to Telegram
        empty_message = "🔍 Stock scan completed: <b>No stocks found</b> matching the current filter criteria.\n\nTry adjusting:\n• RSI range\n• ADX minimum\n• Volume ratio\n• Pattern strength threshold"
        send_to_telegram(empty_message)


if __name__ == "__main__":
    main()
