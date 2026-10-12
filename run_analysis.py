#!/usr/bin/env python3
"""
Run NSE PCS analysis using streamlit_app logic
"""

import sys
import os

# Suppress streamlit warnings
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

# Import the scanner class
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
    print("✓ Successfully imported streamlit_app modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import requests
import json

def get_default_config():
    """Default filter configuration"""
    return {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:50],  # First 50 stocks
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
    }

def run_analysis():
    """Run the analysis"""
    print("=" * 60)
    print("NSE PCS Scanner - Running Analysis")
    print("=" * 60)

    config = get_default_config()
    scanner = ProfessionalPCSScanner()
    results = []

    stocks_to_scan = config['stocks_to_scan']
    total = len(stocks_to_scan)

    print(f"\nAnalyzing {total} stocks with filter criteria:")
    print(f"  RSI: {config['rsi_min']}-{config['rsi_max']}")
    print(f"  ADX Min: {config['adx_min']}")
    print(f"  Volume Ratio: {config['min_volume_ratio']}x")
    print(f"  Pattern Strength: {config['pattern_strength_min']}+\n")

    for i, symbol in enumerate(stocks_to_scan, 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print(f"[{i}/{total}] {clean_symbol:<15} - No data", flush=True)
                continue

            # Check volume
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
            if not volume_ok:
                print(f"[{i}/{total}] {clean_symbol:<15} - Low volume", flush=True)
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print(f"[{i}/{total}] {clean_symbol:<15} - No patterns", flush=True)
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            print(f"[{i}/{total}] {clean_symbol:<15} ✓ {len(patterns)} pattern(s)", flush=True)

            # Create result
            stock_result = {
                'symbol': clean_symbol,
                'price': round(current_price, 2),
                'rsi': round(current_rsi, 1),
                'adx': round(current_adx, 1),
                'volume_ratio': round(volume_ratio, 2),
                'patterns': len(patterns),
                'strength': round(max(p['strength'] for p in patterns), 0),
                'pattern': patterns[0]['type'].split('(')[0].strip() if patterns else 'Unknown',
                'confidence': patterns[0].get('confidence', 'N/A') if patterns else 'N/A'
            }

            results.append(stock_result)

        except Exception as e:
            print(f"[{i}/{total}] {clean_symbol:<15} - Error: {str(e)[:30]}", flush=True)
            continue

    return results

def format_telegram_message(results):
    """Format message for Telegram"""
    if not results:
        return "📊 NSE PCS Scanner: No stocks found meeting filter criteria."

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""🚀 NSE PCS Scanner Results
{timestamp}

📊 Found {len(results)} stocks with patterns

"""

    for i, stock in enumerate(results[:15], 1):
        message += f"""{i}. {stock['symbol']}
   Price: ₹{stock['price']} | RSI: {stock['rsi']} | ADX: {stock['adx']}
   Pattern: {stock['pattern']} ({int(stock['strength'])}/100)
   Patterns: {stock['patterns']} | Confidence: {stock['confidence']}

"""

    return message

def send_to_telegram(message):
    """Send message to Telegram"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("\n⚠ Telegram not configured")
        print("  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"✗ Telegram send failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Telegram error: {str(e)[:50]}")
        return False

def main():
    """Main execution"""
    results = run_analysis()

    print(f"\n{'='*60}")
    print(f"✓ Analysis complete: Found {len(results)} stocks")
    print(f"{'='*60}\n")

    if results:
        # Format message
        message = format_telegram_message(results)
        print(message)

        # Save to CSV
        csv_file = "/home/user/nsepcs/pcs_results.csv"
        df = pd.DataFrame(results)
        df = df[['symbol', 'price', 'rsi', 'adx', 'volume_ratio', 'strength', 'pattern', 'confidence']]
        df.to_csv(csv_file, index=False)
        print(f"✓ Results saved to: {csv_file}\n")

        # Send to Telegram
        print("Sending to Telegram...")
        if send_to_telegram(message):
            print("✓ Message sent to Telegram successfully!")
        else:
            print("⚠ Could not send to Telegram (check credentials)")
    else:
        print("No stocks found meeting the filter criteria")
        print("This could be due to:")
        print("  - Network connectivity issues")
        print("  - Market data unavailability")
        print("  - No stocks matching strict filter criteria")

if __name__ == "__main__":
    main()
