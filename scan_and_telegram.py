#!/usr/bin/env python3
"""
Standalone script to run NSE F&O PCS Scanner and send results to Telegram
"""

import sys
import os
sys.path.insert(0, '/home/user/nsepcs')

import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import requests
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Telegram configuration from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_to_telegram(message: str, parse_mode: str = "HTML"):
    """Send message to Telegram chat"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured")
        print("Message would be sent to Telegram:")
        print(message)
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send to Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def run_scanner(stocks_to_scan=None, min_pattern_strength=65, max_stocks=50):
    """Run the PCS scanner with specified criteria"""

    if stocks_to_scan is None:
        # Use F&O universe
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    scanner = ProfessionalPCSScanner()
    results = []

    print(f"🚀 Starting scan of {len(stocks_to_scan)} stocks...")

    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"  [{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end="", flush=True)

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                print(" ✗ (No data)")
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, min_volume_ratio=1.2)
            if not volume_ok:
                print(" ✗ (Low volume)")
                continue

            # Detect patterns
            config = {
                'min_volume_ratio': 1.2,
                'pattern_strength_min': min_pattern_strength,
                'enable_daily_analysis': True,
                'enable_weekly_validation': True,
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
                }
            }

            patterns = scanner.detect_patterns(data, symbol, config)

            if not patterns:
                print(" ✗ (No patterns)")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            max_strength = max(p['strength'] for p in patterns)

            stock_result = {
                'symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'max_strength': max_strength,
                'patterns_count': len(patterns),
                'patterns': patterns,
            }

            results.append(stock_result)
            print(f" ✓ (Strength: {max_strength:.0f}%)")

        except Exception as e:
            print(f" ✗ (Error: {str(e)[:30]})")
            continue

    return results

def format_results_for_telegram(results):
    """Format scan results for Telegram message"""

    if not results:
        message = "🚫 <b>NSE F&O PCS Scanner</b>\n\nNo stocks met the filter criteria today.\n\n"
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        message += f"<i>Scanned at {current_time.strftime('%H:%M IST')}</i>"
        return message

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    # Create header
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"🎯 <b>NSE F&O PCS Scanner Results</b>\n"
    message += f"<i>{current_time.strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"

    # Summary
    message += f"<b>📊 Summary:</b>\n"
    message += f"✅ Stocks Found: <b>{len(results)}</b>\n"

    total_patterns = sum(r['patterns_count'] for r in results)
    avg_strength = np.mean([r['max_strength'] for r in results])

    message += f"🎯 Total Patterns: <b>{total_patterns}</b>\n"
    message += f"💪 Avg Strength: <b>{avg_strength:.1f}%</b>\n\n"

    # Top 10 results
    message += "<b>🏆 Top Stocks:</b>\n"
    message += "─" * 40 + "\n"

    for rank, result in enumerate(results[:10], 1):
        confidence = "🟢 HIGH" if result['max_strength'] >= 85 else "🟡 MED" if result['max_strength'] >= 70 else "🔴 LOW"

        message += f"{rank}. <b>{result['symbol']}</b>\n"
        message += f"   💰 Price: ₹{result['current_price']:.2f}\n"
        message += f"   📊 Strength: {result['max_strength']:.0f}% {confidence}\n"
        message += f"   📈 RSI: {result['rsi']:.1f} | ⚡ ADX: {result['adx']:.1f}\n"
        message += f"   📊 Volume: {result['volume_ratio']:.1f}x\n"
        message += f"   🎯 Patterns: {result['patterns_count']}\n\n"

    if len(results) > 10:
        message += f"\n... and {len(results) - 10} more stocks\n"

    message += "\n"
    message += "📋 <i>Use /nse-fo-pcs-screener.streamlit.app for detailed analysis</i>\n"
    message += "⚠️  <i>Always verify before trading. Past performance ≠ future results.</i>"

    return message

def main():
    """Main execution"""
    print("=" * 60)
    print("NSE F&O PCS Scanner - Telegram Edition")
    print("=" * 60)
    print()

    # Configuration
    max_stocks = 50  # Scan first 50 F&O stocks
    min_pattern_strength = 65  # Minimum pattern strength

    print(f"⚙️  Configuration:")
    print(f"   Max Stocks: {max_stocks}")
    print(f"   Min Pattern Strength: {min_pattern_strength}%")
    print()

    # Run scanner
    results = run_scanner(
        stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:max_stocks],
        min_pattern_strength=min_pattern_strength,
        max_stocks=max_stocks
    )

    print()
    print(f"✅ Scan complete. Found {len(results)} stocks meeting criteria.")
    print()

    # Format message
    telegram_message = format_results_for_telegram(results)

    # Send to Telegram
    print("📤 Sending results to Telegram...")
    send_to_telegram(telegram_message)

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
