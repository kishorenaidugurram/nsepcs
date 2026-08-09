#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner with Telegram Integration
Runs the scanner with default filters and sends results to Telegram
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Add the repo to path
sys.path.insert(0, '/home/user/nsepcs')

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import ta, fallback if not available
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False
    print("Warning: 'ta' package not available, using fallback indicators")

# Import the scanner from streamlit_app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

def send_to_telegram(message, telegram_token=None, chat_id=None):
    """Send message to Telegram"""
    if not telegram_token or not chat_id:
        telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not telegram_token or not chat_id:
        print("⚠️  Telegram credentials not found. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars")
        return False

    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"Telegram error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False

def run_scan(max_stocks=50, use_f_and_o=True):
    """Run the PCS scanner with default filters"""

    print("=" * 60)
    print("🚀 NSE F&O PCS Scanner - Automated Run")
    print("=" * 60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

    # Setup filters (defaults from streamlit app)
    filters = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'SMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65,
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
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

    # Select stocks
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]
    print(f"📊 Scanning {len(stocks_to_scan)} stocks")
    print("-" * 60)

    scanner = ProfessionalPCSScanner()
    results = []

    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            print(f"[{i+1}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end=' ', flush=True)

            # Get data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                print("❌ No data")
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, filters['min_volume_ratio'])
            if not volume_ok:
                print("❌ Volume check failed")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                print("❌ No patterns")
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'strength': max(p['strength'] for p in patterns),
                'confidence': 'HIGH' if max(p['strength'] for p in patterns) >= 85 else 'MEDIUM' if max(p['strength'] for p in patterns) >= 70 else 'LOW'
            }

            results.append(result)
            print(f"✅ Found {len(patterns)} pattern(s)")

        except Exception as e:
            print(f"⚠️  Error: {str(e)[:30]}")
            continue

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print("\n" + "=" * 60)
    print(f"📈 Results: {len(results)} stocks found")
    print("=" * 60)

    return results, filters

def format_results_for_telegram(results):
    """Format scan results as Telegram message"""
    if not results:
        return "❌ No stocks found meeting criteria today"

    msg = "<b>📊 NSE F&O PCS Scan Results</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"

    for i, r in enumerate(results[:15], 1):  # Top 15
        confidence_emoji = "🟢" if r['confidence'] == 'HIGH' else "🟡" if r['confidence'] == 'MEDIUM' else "🔴"
        pattern_count = len(r['patterns'])
        pattern_types = ", ".join([p['type'].split('-')[0][:10] for p in r['patterns'][:3]])

        msg += f"{i}. <b>{r['symbol']}</b> {confidence_emoji}\n"
        msg += f"   💰 ₹{r['price']:.2f} | 📊 Strength: {r['strength']:.0f}%\n"
        msg += f"   📈 {pattern_count} pattern(s): {pattern_types}\n"
        msg += f"   📋 RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f}\n\n"

    if len(results) > 15:
        msg += f"\n... and {len(results) - 15} more stocks\n"

    msg += f"\n✅ Total: {len(results)} stocks found\n"
    msg += "🔗 View full analysis: https://nse-fo-pcs-screener.streamlit.app"

    return msg

def save_results_to_csv(results):
    """Save results to CSV"""
    if not results:
        return None

    df = pd.DataFrame([{
        'Symbol': r['symbol'],
        'Price': f"₹{r['price']:.2f}",
        'RSI': f"{r['rsi']:.1f}",
        'ADX': f"{r['adx']:.1f}",
        'Volume Ratio': f"{r['volume_ratio']:.2f}x",
        'Strength': f"{r['strength']:.0f}%",
        'Confidence': r['confidence'],
        'Patterns': len(r['patterns'])
    } for r in results])

    filename = f"/tmp/pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"📁 Results saved to: {filename}")
    return filename

def main():
    """Main execution"""
    # Run scan
    results, filters = run_scan(max_stocks=100)

    if not results:
        print("\n❌ No stocks meeting criteria found")
        return

    # Display top results
    print("\n📊 TOP 10 STOCKS:\n")
    for i, r in enumerate(results[:10], 1):
        print(f"{i}. {r['symbol']:<12} | Strength: {r['strength']:>5.0f}% | {r['confidence']:<6} | ₹{r['price']:>8.2f}")

    # Save to CSV
    csv_file = save_results_to_csv(results)

    # Send to Telegram
    print("\n📱 Sending to Telegram...")
    telegram_msg = format_results_for_telegram(results)

    if send_to_telegram(telegram_msg):
        print("✅ Successfully sent to Telegram!")
    else:
        print("⚠️  Could not send to Telegram (no credentials or network error)")
        print(f"\nTo enable Telegram, set these environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")

    print("\n" + "=" * 60)
    print("✅ Scan completed successfully")
    print("=" * 60)

if __name__ == "__main__":
    main()
