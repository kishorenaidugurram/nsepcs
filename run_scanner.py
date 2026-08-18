#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Runs without Streamlit UI
Sends results to Telegram if credentials are available
"""

import sys
import os
import json
from datetime import datetime
import pytz
from pathlib import Path

# Add the repo directory to path
sys.path.insert(0, '/home/user/nsepcs')

import numpy as np
import pandas as pd
import yfinance as yf
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached,
    create_excel_stock_list
)

def send_to_telegram(message, results=None):
    """Send results to Telegram if credentials available"""
    try:
        import requests

        # Try to get credentials from environment
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("⚠️  Telegram credentials not found in environment variables")
            print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram notifications")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Prepare message
        full_message = message
        if results and len(results) > 0:
            full_message += f"\n\n📊 **Stocks Found: {len(results)}**\n\n"

            # Add first 10 stocks
            for i, result in enumerate(results[:10], 1):
                symbol = result['symbol'].replace('.NS', '')
                max_strength = max(p['strength'] for p in result['patterns'])
                full_message += f"{i}. {symbol} - Strength: {max_strength:.0f}%\n"

            if len(results) > 10:
                full_message += f"\n... and {len(results) - 10} more stocks\n"

        payload = {
            'chat_id': chat_id,
            'text': full_message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Results sent to Telegram successfully!")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️  Could not send Telegram message: {str(e)}")
        return False

def run_scanner_with_filters():
    """Run the scanner with configured filters"""

    # DEFAULT FILTERS (matching common settings from sidebar)
    filters = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:100],  # Scan first 100 for speed
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
            'rectangle_top': True,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True,
        },
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_news': False,
    }

    print("🚀 Starting NSE F&O PCS Scanner")
    print(f"📅 Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Scanning {len(filters['stocks_to_scan'])} stocks from F&O universe")
    print(f"⚙️  Pattern Strength Min: {filters['pattern_strength_min']}%")
    print("---")

    scanner = ProfessionalPCSScanner()
    results = []
    failed_stocks = []

    # Scan each stock
    for i, symbol in enumerate(filters['stocks_to_scan'], 1):
        clean_symbol = symbol.replace('.NS', '')

        try:
            print(f"[{i}/{len(filters['stocks_to_scan'])}] Analyzing {clean_symbol}...", end=" ", flush=True)

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                failed_stocks.append(symbol)
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                filters['min_volume_ratio']
            )
            if not volume_ok:
                print("❌ Volume too low")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                print("❌ No patterns")
                continue

            # Check if any pattern meets strength threshold
            strong_patterns = [p for p in patterns if p['strength'] >= filters['pattern_strength_min']]
            if not strong_patterns:
                print("❌ Pattern strength too low")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': strong_patterns,
                'max_strength': max(p['strength'] for p in strong_patterns),
            }

            results.append(stock_result)
            print(f"✅ {len(strong_patterns)} pattern(s) - Strength: {stock_result['max_strength']:.0f}%")

        except Exception as e:
            print(f"⚠️  Error: {str(e)[:30]}")
            failed_stocks.append(symbol)
            continue

    print("\n" + "="*60)
    print(f"📊 SCAN COMPLETE")
    print(f"✅ Found: {len(results)} stocks matching criteria")
    print(f"❌ Failed: {len(failed_stocks)} stocks")
    print("="*60)

    if results:
        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        print("\n📈 TOP RESULTS:")
        print("-" * 60)
        for i, result in enumerate(results[:10], 1):
            print(f"{i}. {result['clean_symbol']:12} | Price: ₹{result['current_price']:8.2f} | "
                  f"Strength: {result['max_strength']:5.1f}% | RSI: {result['rsi']:5.1f} | "
                  f"ADX: {result['adx']:5.1f} | Volume: {result['volume_ratio']:5.2f}x")

        if len(results) > 10:
            print(f"... and {len(results) - 10} more stocks")

    print("\n" + "="*60)

    # Save results to JSON
    results_file = f"/tmp/scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'total_found': len(results),
                'stocks': [
                    {
                        'symbol': r['clean_symbol'],
                        'price': float(r['current_price']),
                        'strength': float(r['max_strength']),
                        'rsi': float(r['rsi']),
                        'adx': float(r['adx']),
                        'volume': float(r['volume_ratio']),
                        'patterns': len(r['patterns'])
                    }
                    for r in results
                ]
            }, f, indent=2)
        print(f"💾 Results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Could not save results file: {e}")

    # Save as Excel if results found
    if results:
        try:
            excel_file = f"/tmp/scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            excel_data = create_excel_stock_list(results)
            with open(excel_file, 'wb') as f:
                f.write(excel_data)
            print(f"📊 Excel file saved to: {excel_file}")
        except Exception as e:
            print(f"⚠️  Could not create Excel file: {e}")

    # Send to Telegram
    if results:
        message = f"""📊 **NSE F&O PCS Scanner Results**

🎯 Stocks Found: {len(results)}
⏰ Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}

**Top Picks:**
"""
        send_to_telegram(message, results)
    else:
        send_to_telegram("❌ No stocks found matching the filter criteria today.", None)

    return results

if __name__ == "__main__":
    try:
        results = run_scanner_with_filters()
        sys.exit(0 if results else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
