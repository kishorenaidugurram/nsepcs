#!/usr/bin/env python3
"""
Standalone script to run NSE PCS scanner and send results to Telegram
"""

import sys
import os
import json
from datetime import datetime
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the scanner from streamlit_app
sys.path.insert(0, '/home/user/nsepcs')

# Read environment variables for Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default configuration for scanning
DEFAULT_CONFIG = {
    'min_pcs_score': 55,
    'min_liquidity_tier': 3,
    'max_stocks': 40,
    'min_volume_ratio': 1.0,
    'show_news': False,
    'rsi_min': 30,
    'rsi_max': 80,
    'adx_min': 15,
    'ma_support': True,
    'ma_type': 'SMA',
    'ma_tolerance': 5,
    'pattern_strength_min': 0.4,
    'lookback_days': 20,
    'volume_breakout_ratio': 2.0,
    'enable_daily_analysis': True,
    'enable_weekly_validation': False,
    'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    'pattern_priority': 'All Patterns (Comprehensive)',
    'pattern_filters': {
        'current_day_breakout': True,
        'cup_and_handle': True,
        'flat_base': True,
        'rectangle_bottom': True,
        'double_bottom': True,
        'head_and_shoulders': True,
        'bump_and_run': True,
        'three_rising_valleys': True,
        'rounding_bottom': True,
    },
    'enhancements': {
        'delivery_volume': False,
        'fno_consolidation': False,
        'breakout_pullback': False,
        'enhanced_sr': False,
    }
}

# Define comprehensive F&O universe
COMPLETE_NSE_FO_UNIVERSE = [
    # Tier 1 - Ultra High Liquidity
    'NIFTY.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
    # Tier 2 - High Liquidity
    'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS',
    'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS',
    'TATAMOTORS.NS', 'ADANIENT.NS',
    # Tier 3 - Medium Liquidity
    'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS',
    'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS',
    'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS',
    'TATASTEEL.NS', 'HINDALCO.NS', 'ADANIPORTS.NS', 'GAIL.NS',
    'EICHERMOT.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS'
]


def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False


def send_telegram_file(file_path, caption=""):
    """Send file to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data, timeout=30)

        if response.status_code == 200:
            print(f"✅ File sent to Telegram: {file_path}")
            return True
        else:
            print(f"❌ Failed to send file: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending file: {e}")
        return False


def run_scanner(config, stocks=None):
    """Run the scanner with given config"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting NSE PCS Scanner Analysis")
    print(f"{'='*60}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Configuration:")
    print(f"   - Min PCS Score: {config.get('min_pcs_score', 55)}")
    print(f"   - Max Stocks: {config.get('max_stocks', 40)}")
    print(f"{'='*60}\n")

    # Import scanner here to avoid issues if streamlit is not installed
    try:
        from streamlit_app import ProfessionalPCSScanner
    except ImportError as e:
        print(f"❌ Error importing scanner: {e}")
        return None

    scanner = ProfessionalPCSScanner()

    # Use provided stocks or default universe
    stocks_to_scan = stocks if stocks else COMPLETE_NSE_FO_UNIVERSE[:config['max_stocks']]

    results = []
    failed_stocks = []

    print(f"📈 Scanning {len(stocks_to_scan)} stocks...\n")

    for i, symbol in enumerate(stocks_to_scan, 1):
        clean_symbol = symbol.replace('.NS', '')
        print(f"[{i:2d}/{len(stocks_to_scan)}] Analyzing {clean_symbol}...", end=" ", flush=True)

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 2:
                print("❌ No data")
                failed_stocks.append(clean_symbol)
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data,
                config.get('min_volume_ratio', 1.0)
            )

            if not volume_ok:
                print("❌ Volume criteria not met")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)

            if not patterns:
                print("❌ No patterns detected")
                continue

            # Get current metrics
            current_price = float(data['Close'].iloc[-1])
            current_rsi = float(data['RSI'].iloc[-1])
            current_adx = float(data['ADX'].iloc[-1])

            # Calculate pattern strength (average of all detected patterns)
            pattern_strength = np.mean([p['strength'] for p in patterns])
            confidence_level = patterns[0]['confidence'] if patterns else 'UNKNOWN'

            stock_result = {
                'symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'pattern_strength': pattern_strength,
                'confidence': confidence_level
            }

            results.append(stock_result)
            print(f"✅ {len(patterns)} pattern(s) - Strength: {pattern_strength:.2f}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")
            failed_stocks.append(clean_symbol)
            continue

    print(f"\n{'='*60}")
    print(f"📊 Analysis Complete!")
    print(f"{'='*60}")
    print(f"✅ Successful: {len(results)} stocks")
    print(f"❌ Failed: {len(failed_stocks)} stocks")

    if failed_stocks:
        print(f"Failed stocks: {', '.join(failed_stocks[:10])}")
        if len(failed_stocks) > 10:
            print(f"   ... and {len(failed_stocks) - 10} more")

    return results


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ <b>No stocks found matching criteria</b>"

    # Sort by pattern strength
    results.sort(key=lambda x: x['pattern_strength'], reverse=True)

    message = f"<b>📊 NSE PCS Scanner Results</b>\n"
    message += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n\n"
    message += f"<b>✅ Found {len(results)} stocks with patterns:</b>\n"
    message += "─" * 40 + "\n\n"

    for i, stock in enumerate(results[:10], 1):  # Show top 10
        message += f"<b>{i}. {stock['symbol']}</b>\n"
        message += f"💰 Price: ₹{stock['current_price']:.2f}\n"
        message += f"📈 RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}\n"
        message += f"🎯 Pattern Strength: {stock['pattern_strength']:.2f}\n"
        message += f"🔐 Confidence: {stock['confidence']}\n"

        # Show pattern types
        pattern_types = ", ".join(set(p['type'] for p in stock['patterns'][:2]))
        message += f"📊 Patterns: {pattern_types}\n"

        if i < len(results[:10]):
            message += "─" * 40 + "\n"

    if len(results) > 10:
        message += f"\n... and {len(results) - 10} more stocks\n"

    message += f"\n<i>Scan time: {datetime.now().strftime('%H:%M:%S')}</i>"

    return message


def save_results_to_csv(results):
    """Save results to CSV file"""
    if not results:
        print("No results to save")
        return None

    # Flatten results for CSV
    data = []
    for stock in results:
        for pattern in stock['patterns']:
            data.append({
                'Symbol': stock['symbol'],
                'Current_Price': f"{stock['current_price']:.2f}",
                'RSI': f"{stock['rsi']:.1f}",
                'ADX': f"{stock['adx']:.1f}",
                'Volume_Ratio': f"{stock['volume_ratio']:.2f}",
                'Pattern_Type': pattern['type'],
                'Pattern_Strength': f"{pattern['strength']:.2f}",
                'Confidence': pattern['confidence'],
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

    df = pd.DataFrame(data)

    # Save to file
    filename = f"/tmp/nse_pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"\n✅ Results saved to: {filename}")

    return filename


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("NSE PCS Scanner - Telegram Integration")
    print("="*60)

    # Check Telegram configuration
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  WARNING: Telegram not configured!")
        print("Set these environment variables:")
        print("  - TELEGRAM_BOT_TOKEN")
        print("  - TELEGRAM_CHAT_ID")
        print("\nResults will still be saved locally but not sent to Telegram.\n")

    # Run scanner
    results = run_scanner(DEFAULT_CONFIG)

    if not results:
        print("\n❌ Scanner returned no results")
        message = "❌ NSE PCS Scanner ran but found no stocks matching criteria"
        send_telegram_message(message)
        return

    # Format and send Telegram message
    telegram_message = format_telegram_message(results)
    print(f"\n📱 Telegram Message Preview:\n{telegram_message}\n")

    send_telegram_message(telegram_message)

    # Save to CSV
    csv_file = save_results_to_csv(results)
    if csv_file and os.path.exists(csv_file):
        send_telegram_file(csv_file, caption="NSE PCS Scanner Results (CSV)")

    print("\n" + "="*60)
    print("✅ Scanner execution complete!")
    print("="*60)


if __name__ == "__main__":
    main()
