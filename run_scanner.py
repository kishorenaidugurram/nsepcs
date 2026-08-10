#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Non-Streamlit Version
Runs the scanner and sends results to Telegram
"""

import sys
import os
import json
import requests
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# Import the scanner from the streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    create_excel_stock_list
)

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if not bot_token or not chat_id:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not set. Results will be saved locally only.")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print(f"✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Failed to send to Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def run_scanner(
    stocks_to_scan=None,
    rsi_min=30,
    rsi_max=75,
    adx_min=20,
    ma_support=True,
    min_volume_ratio=1.2,
    volume_breakout_ratio=2.0,
    lookback_days=20,
    pattern_strength_min=65,
    max_stocks=50
):
    """Run PCS scanner with given parameters"""

    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    print(f"🚀 Starting NSE F&O PCS Scanner")
    print(f"📊 Scanning {len(stocks_to_scan)} stocks")
    print(f"⚙️  Filters: RSI({rsi_min}-{rsi_max}), ADX(>{adx_min}), Vol({min_volume_ratio}x)")
    print("-" * 60)

    scanner = ProfessionalPCSScanner()
    results = []

    config = {
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'adx_min': adx_min,
        'ma_support': ma_support,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': min_volume_ratio,
        'volume_breakout_ratio': volume_breakout_ratio,
        'lookback_days': lookback_days,
        'pattern_strength_min': pattern_strength_min,
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
        }
    }

    for i, symbol in enumerate(stocks_to_scan):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        progress = ((i + 1) / len(stocks_to_scan)) * 100
        print(f"[{progress:5.1f}%] 🔍 Analyzing {clean_symbol}...", end='\r')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
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

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'max_strength': max(p['strength'] for p in patterns) if patterns else 0,
                'pattern_count': len(patterns)
            }

            results.append(stock_result)

        except Exception as e:
            continue

    print(" " * 80)  # Clear progress line
    return results

def format_results_for_telegram(results):
    """Format scan results for Telegram message"""
    if not results:
        return "❌ <b>No stocks found matching criteria</b>"

    # Sort by strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"📊 <b>NSE F&O PCS Scanner Results</b>\n"
    message += f"⏰ {current_time}\n"
    message += f"✅ Found <b>{len(results)} stocks</b>\n"
    message += "━" * 40 + "\n\n"

    # Top 15 stocks
    for i, result in enumerate(results[:15], 1):
        strength = result['max_strength']
        confidence = '🟢 HIGH' if strength >= 85 else '🟡 MEDIUM' if strength >= 70 else '🔴 LOW'

        message += f"{i}. <b>{result['clean_symbol']}</b>\n"
        message += f"   💪 Strength: {strength:.0f}% | {confidence}\n"
        message += f"   💰 Price: ₹{result['current_price']:.2f} | Volume: {result['volume_ratio']:.1f}x\n"
        message += f"   📊 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"   🎯 Patterns: {result['pattern_count']}\n\n"

    if len(results) > 15:
        message += f"... and {len(results) - 15} more stocks\n\n"

    message += "━" * 40 + "\n"
    message += f"📈 Avg Strength: {sum(r['max_strength'] for r in results) / len(results):.1f}%\n"
    message += "🔔 For detailed analysis, visit the web app"

    return message

def save_results_to_file(results):
    """Save results to JSON and CSV files"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON
    json_file = f"/tmp/nsepcs_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json_data = []
        for r in results:
            json_data.append({
                'symbol': r['clean_symbol'],
                'price': float(r['current_price']),
                'strength': float(r['max_strength']),
                'volume_ratio': float(r['volume_ratio']),
                'rsi': float(r['rsi']),
                'adx': float(r['adx']),
                'patterns': r['pattern_count']
            })
        json.dump(json_data, f, indent=2)

    # CSV
    csv_file = f"/tmp/nsepcs_results_{timestamp}.csv"
    df_data = []
    for r in results:
        df_data.append({
            'Symbol': r['clean_symbol'],
            'Price': f"₹{r['current_price']:.2f}",
            'Strength': f"{r['max_strength']:.0f}%",
            'Volume': f"{r['volume_ratio']:.1f}x",
            'RSI': f"{r['rsi']:.1f}",
            'ADX': f"{r['adx']:.1f}",
            'Patterns': r['pattern_count']
        })
    df = pd.DataFrame(df_data)
    df.to_csv(csv_file, index=False)

    return json_file, csv_file

def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("NSE F&O PCS SCANNER - AUTOMATED RUN")
    print("=" * 60 + "\n")

    # Run scanner with default settings
    results = run_scanner(
        stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:100],  # Scan first 100 stocks
        rsi_min=30,
        rsi_max=75,
        adx_min=20,
        min_volume_ratio=1.2,
        max_stocks=100
    )

    print(f"\n✅ Scan Complete!")
    print(f"📊 Found {len(results)} qualifying stocks\n")

    if results:
        # Display top 10
        print("🏆 Top 10 Stocks by Strength:")
        print("-" * 60)
        sorted_results = sorted(results, key=lambda x: x['max_strength'], reverse=True)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. {result['clean_symbol']:12s} | Strength: {result['max_strength']:5.0f}% | "
                  f"Price: ₹{result['current_price']:8.2f} | RSI: {result['rsi']:5.1f} | "
                  f"ADX: {result['adx']:5.1f}")

        # Save results
        json_file, csv_file = save_results_to_file(results)
        print(f"\n💾 Results saved to:")
        print(f"   📄 {csv_file}")
        print(f"   📋 {json_file}")

        # Format and send to Telegram
        telegram_message = format_results_for_telegram(results)
        print(f"\n📤 Sending to Telegram...")
        sent = send_to_telegram(telegram_message)

        if sent:
            print("✅ Telegram notification sent successfully!")
        else:
            print("⚠️  Results saved locally but Telegram send failed")
            print("\n📌 Message preview:")
            print(telegram_message)
    else:
        print("❌ No stocks found matching the criteria")

if __name__ == "__main__":
    main()
