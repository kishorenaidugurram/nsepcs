#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Runs scanning without Streamlit UI and sends results to Telegram
"""

import sys
import os
from datetime import datetime
import pytz
import requests
import json

# Add the repo directory to path for importing streamlit_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress streamlit warnings since we're not running streamlit
os.environ["STREAMLIT_CLIENT_LOGGER_ENABLED"] = "false"

# Import scanner from streamlit app (we'll use the ProfessionalPCSScanner class)
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    STOCK_CATEGORIES
)


def get_telegram_config():
    """Get Telegram bot token and chat ID from environment"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    return token, chat_id


def send_telegram_message(message, token, chat_id):
    """Send message to Telegram"""
    if not token or not chat_id:
        print("⚠️  Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to send to Telegram: {e}")
        return False


def run_scanner():
    """Run the stock scanner with default filter criteria"""

    print("🚀 Starting NSE F&O PCS Scanner...")
    print(f"⏰ Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("-" * 60)

    # Default filter criteria (reasonable defaults for PCS trading)
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50],  # First 50 stocks for speed
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
            'cup_handle': True,
            'flat_base': True,
            'bump_and_run': True,
            'rectangle_bottom': True,
            'rectangle_top': True,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_charts': False,
        'show_news': False,
        'export_results': False,
        'stocks_limit': 50,
        'enhancements': {
            'delivery_volume': True,
            'fno_consolidation': True,
            'breakout_pullback': True,
            'enhanced_sr': True
        }
    }

    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    results = []
    failed_stocks = []

    print(f"📊 Scanning {len(config['stocks_to_scan'])} stocks...\n")

    for i, symbol in enumerate(config['stocks_to_scan']):
        progress = (i + 1) / len(config['stocks_to_scan'])
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        print(f"[{i+1}/{len(config['stocks_to_scan'])}] Analyzing {clean_symbol}...", end=" ")

        try:
            # Get recent data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                failed_stocks.append(clean_symbol)
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                print("⏭️  Volume low")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print("⏭️  No patterns")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'volume_ratio': volume_ratio
            }
            results.append(result)
            print(f"✅ Found {len(patterns)} pattern(s)")

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            failed_stocks.append(clean_symbol)
            continue

    return results, failed_stocks


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return None

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    # Build message
    message = f"""
<b>📊 NSE F&O PCS Scanner Results</b>
<i>{timestamp}</i>

<b>✅ Stocks Meeting Criteria:</b> {len(results)}

"""

    # Add stock details (limit to 10 for Telegram message size)
    for i, result in enumerate(results[:10]):
        patterns_str = ", ".join([p['name'] for p in result['patterns']])
        message += f"""
<b>{i+1}. {result['symbol']}</b>
  💰 Price: ₹{result['price']:.2f}
  📊 RSI: {result['rsi']:.1f}
  📈 ADX: {result['adx']:.1f}
  🔄 Vol Ratio: {result['volume_ratio']:.2f}x
  🎯 Patterns: {patterns_str}
"""

    if len(results) > 10:
        message += f"\n... and {len(results) - 10} more stocks"

    message += f"\n\n<i>Run 'streamlit run streamlit_app.py' to see full analysis</i>"

    return message


def main():
    """Main execution"""

    # Run scanner
    results, failed_stocks = run_scanner()

    print("\n" + "=" * 60)
    print(f"📈 Scanner Complete")
    print(f"✅ Stocks found: {len(results)}")
    print(f"❌ Failed stocks: {len(failed_stocks)}")
    print("=" * 60)

    if results:
        print("\n🎯 Stocks Meeting Criteria:")
        for i, result in enumerate(results, 1):
            patterns_str = ", ".join([p['name'] for p in result['patterns']])
            print(f"{i}. {result['symbol']:<12} | Price: ₹{result['price']:>8.2f} | Patterns: {patterns_str}")

    # Send to Telegram
    token, chat_id = get_telegram_config()

    if token and chat_id:
        print("\n📨 Sending to Telegram...")
        message = format_telegram_message(results)
        if message:
            send_telegram_message(message, token, chat_id)
        else:
            print("No results to send")
    else:
        print("\n⚠️  Telegram not configured")
        print("\nTo enable Telegram notifications, set these environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nThen run this script again")

    return results


if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0 if results else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scanner interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
