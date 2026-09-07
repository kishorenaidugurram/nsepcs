#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Screener
Runs pattern detection and sends results to Telegram
"""

import sys
import os
import numpy as np
from datetime import datetime
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
from telegram_notifier import TelegramNotifier

# Configuration
DEFAULT_CONFIG = {
    'min_score': 55,  # Minimum pattern strength to report
    'min_volume_ratio': 1.0,
    'max_stocks': 50,  # Scan max 50 stocks per run for speed
    'patterns_to_detect': {
        'current_day_breakout': True,
        'cup_and_handle': True,
        'double_bottom': True,
        'flat_base': True,
        'rectangle_bottom': True,
        'head_shoulders_bottom': True,
        'rounding_bottom': True,
        'bump_and_run': True,
    },
    'pattern_strength_min': 50,
    'rsi_min': 30,
    'rsi_max': 80,
    'adx_min': 15,
    'ma_support': True,
    'ma_tolerance': 2,
    'enable_weekly_validation': True,
}

def get_stocks_to_scan():
    """Get list of stocks to scan - focusing on Nifty 50 for faster execution"""
    nifty_50 = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS',
        'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'JSWSTEEL.NS',
        'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'EICHERMOT.NS',
        'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS', 'BPCL.NS',
        'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS',
        'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS', 'HDFCLIFE.NS',
        'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS',
    ]
    return nifty_50[:50]  # Limit to first 50 for speed

def run_scan():
    """Run the PCS scanner"""
    print(f"🚀 Starting NSE F&O PCS Scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Scanning {len(get_stocks_to_scan())} stocks...\n")

    scanner = ProfessionalPCSScanner()
    stocks_to_scan = get_stocks_to_scan()
    results = []

    for i, symbol in enumerate(stocks_to_scan, 1):
        clean_symbol = symbol.replace('.NS', '')
        print(f"[{i:2d}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end=' ')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                print("❌ No data")
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, DEFAULT_CONFIG['min_volume_ratio']
            )
            if not volume_ok:
                print(f"❌ Low volume ({volume_ratio:.1f}x)")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, DEFAULT_CONFIG)
            if not patterns:
                print("❌ No patterns")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Filter by strength
            strong_patterns = [p for p in patterns if p.get('strength', 0) >= DEFAULT_CONFIG['min_score']]
            if not strong_patterns:
                print(f"⚠️  Found {len(patterns)} patterns but below score threshold")
                continue

            max_strength = max(p['strength'] for p in strong_patterns)
            print(f"✅ FOUND! Strength: {max_strength:.0f}%")

            # Create result
            stock_result = {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'volume_details': volume_details,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': strong_patterns,
                'data': data
            }

            results.append(stock_result)

        except Exception as e:
            print(f"⚠️  Error: {str(e)[:50]}")
            continue

    return results

def send_to_telegram(results):
    """Send results to Telegram"""
    try:
        # Check if Telegram is configured
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("\n⚠️  Telegram not configured")
            print("To enable Telegram notifications, set:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")
            return False

        notifier = TelegramNotifier(bot_token=bot_token, chat_id=chat_id)

        # Send summary
        print(f"\n📤 Sending results to Telegram...")
        if notifier.send_stocks_summary(results):
            print("✅ Summary sent to Telegram")
        else:
            print("❌ Failed to send summary")
            return False

        return True

    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def display_results(results):
    """Display results in terminal"""
    if not results:
        print("\n❌ No qualifying stocks found")
        return

    # Sort by strength
    sorted_results = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )

    print(f"\n{'='*80}")
    print(f"✅ SCAN COMPLETE: Found {len(sorted_results)} qualifying stocks")
    print(f"{'='*80}\n")

    print(f"{'Symbol':<10} {'Price':<12} {'Volume':<10} {'RSI':<8} {'Strength':<12} {'Confidence':<12}")
    print("-" * 80)

    for result in sorted_results[:20]:  # Show top 20
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        volume = result['volume_ratio']
        rsi = result['rsi']

        best_pattern = max(result['patterns'], key=lambda p: p['strength'])
        strength = best_pattern['strength']
        confidence = best_pattern['confidence']

        print(f"{symbol:<10} ₹{price:<11.2f} {volume:<10.1f}x {rsi:<8.1f} {strength:<12.0f}% {confidence:<12}")

    print("\n📊 Sample of Top Patterns:")
    print("-" * 80)
    for i, result in enumerate(sorted_results[:5], 1):
        symbol = result['symbol'].replace('.NS', '')
        for pattern in result['patterns'][:2]:
            print(f"{i}. {symbol}: {pattern['type']} ({pattern['confidence']}, Strength: {pattern['strength']:.0f}%)")

def main():
    """Main function"""
    try:
        # Run scan
        results = run_scan()

        # Display results
        display_results(results)

        # Send to Telegram if configured
        send_to_telegram(results)

        print(f"\n✅ Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
