#!/usr/bin/env python3
"""
Standalone PCS Scanner - runs the screening without Streamlit UI
Sends results to Telegram
"""

import sys
import os
import json
import requests
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import from streamlit app (we'll extract the necessary class)
sys.path.insert(0, '/home/user/nsepcs')

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    # Get credentials from environment or config
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not configured.")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

def format_results_for_telegram(results):
    """Format scan results as Telegram message"""
    if not results:
        return "❌ No stocks found matching the criteria."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
    message += f"<b>Time:</b> {current_time}\n"
    message += f"<b>Stocks Found:</b> {len(results)}\n"
    message += "─" * 50 + "\n\n"

    # Sort by pattern strength
    results.sort(key=lambda x: max(p.get('strength', 0) for p in x.get('patterns', [])), reverse=True)

    for i, result in enumerate(results[:20], 1):  # Limit to top 20 for Telegram
        symbol = result['symbol'].replace('.NS', '').replace('^', '')
        price = result.get('current_price', 0)
        rsi = result.get('rsi', 0)
        adx = result.get('adx', 0)
        volume_ratio = result.get('volume_ratio', 0)

        patterns = result.get('patterns', [])
        max_strength = max(p.get('strength', 0) for p in patterns) if patterns else 0
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        # Pattern names
        pattern_types = [p.get('type', 'Unknown') for p in patterns]

        message += f"<b>{i}. {symbol}</b>\n"
        message += f"   💰 Price: ₹{price:.2f}\n"
        message += f"   📈 RSI: {rsi:.1f} | ADX: {adx:.1f}\n"
        message += f"   📊 Volume: {volume_ratio:.1f}x\n"
        message += f"   🎯 Strength: {max_strength:.0f}% ({confidence})\n"
        message += f"   🔍 Patterns: {', '.join(pattern_types[:2])}\n"
        message += "\n"

    if len(results) > 20:
        message += f"\n... and {len(results) - 20} more stocks"

    return message

def run_scan():
    """Run the PCS scan"""
    print("🚀 Starting NSE F&O PCS Scan...")

    # Check if we can import the scanner
    try:
        from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    except ImportError as e:
        print(f"❌ Failed to import scanner: {e}")
        return None

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Use first 50 stocks for faster scanning in production
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:50]

    # Default config
    config = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65
    }

    results = []

    # Scan stocks
    for i, symbol in enumerate(stocks_to_scan):
        print(f"[{i+1}/{len(stocks_to_scan)}] Scanning {symbol.replace('.NS', '')}...", end='\r')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
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

            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns
            }

            results.append(stock_result)

        except Exception as e:
            continue

    print(f"\n✅ Scan complete! Found {len(results)} stocks with patterns.")
    return results

def main():
    """Main function"""
    print("=" * 60)
    print("NSE F&O PCS Screener - Automated Scan")
    print("=" * 60)

    # Run scan
    results = run_scan()

    if not results:
        print("No stocks found matching criteria")
        return

    # Format for display
    print("\n📋 Top Results:")
    print("-" * 60)

    results.sort(key=lambda x: max(p.get('strength', 0) for p in x.get('patterns', [])), reverse=True)

    for i, result in enumerate(results[:10], 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        strength = max(p.get('strength', 0) for p in result['patterns'])
        print(f"{i:2d}. {symbol:15s} | ₹{price:8.2f} | Strength: {strength:.0f}%")

    # Format for Telegram
    telegram_message = format_results_for_telegram(results)

    # Try to send to Telegram
    print("\n📤 Attempting to send results to Telegram...")
    if send_to_telegram(telegram_message):
        print("✅ Results sent to Telegram successfully!")
    else:
        print("⚠️  Could not send to Telegram (credentials may not be set)")
        print("\nTo enable Telegram notifications, set these environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")

    # Save results to file
    results_file = '/tmp/pcs_scan_results.json'
    with open(results_file, 'w') as f:
        # Clean results for JSON serialization
        clean_results = []
        for r in results:
            clean_results.append({
                'symbol': r['symbol'],
                'current_price': float(r['current_price']),
                'rsi': float(r['rsi']),
                'adx': float(r['adx']),
                'volume_ratio': float(r['volume_ratio']),
                'patterns_count': len(r.get('patterns', []))
            })
        json.dump(clean_results, f, indent=2)
    print(f"\n💾 Results saved to {results_file}")

if __name__ == '__main__':
    main()
