#!/usr/bin/env python3
"""
Standalone script to run PCS analysis and send results to Telegram.
Run with: python3 run_analysis.py
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import warnings
warnings.filterwarnings('ignore')

# Import from the streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE,
    fetch_stock_data_cached
)

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured. Skipping Telegram notification.")
        return False

    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False

def format_telegram_message(results, total_scanned):
    """Format results for Telegram"""
    if not results:
        return "📊 <b>PCS Analysis Complete</b>\n\nNo stocks met the filter criteria.\n\n⏰ Check back later for new opportunities."

    message = f"📊 <b>PCS Analysis Results</b>\n\n"
    message += f"<i>Scanned: {total_scanned} stocks</i>\n"
    message += f"<i>Found: {len(results)} stocks</i>\n"
    message += f"<i>Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M IST')}</i>\n\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Group by confidence
    high_conf = [r for r in results if r['confidence'] == 'HIGH']
    med_conf = [r for r in results if r['confidence'] == 'MEDIUM']
    low_conf = [r for r in results if r['confidence'] == 'LOW']

    if high_conf:
        message += "🟢 <b>HIGH Confidence</b>\n"
        for stock in high_conf[:5]:  # Top 5
            message += f"• <b>{stock['symbol']}</b> - {stock['strength']:.0f}% | ₹{stock['price']:.2f} | RSI: {stock['rsi']:.0f}\n"
        if len(high_conf) > 5:
            message += f"  ... and {len(high_conf) - 5} more\n"
        message += "\n"

    if med_conf:
        message += "🟡 <b>MEDIUM Confidence</b>\n"
        for stock in med_conf[:3]:
            message += f"• <b>{stock['symbol']}</b> - {stock['strength']:.0f}%\n"
        if len(med_conf) > 3:
            message += f"  ... and {len(med_conf) - 3} more\n"
        message += "\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "View detailed analysis: <a href='https://nse-fo-pcs-screener.streamlit.app'>NSE F&O PCS Screener</a>"

    return message

def run_analysis(min_pattern_strength=70, max_stocks=None, focus_high_confidence=True):
    """
    Run PCS analysis with given parameters

    Args:
        min_pattern_strength: Minimum pattern strength percentage (default: 70%)
        max_stocks: Maximum stocks to scan (default: None = all)
        focus_high_confidence: Focus on high confidence patterns (default: True)
    """
    ist = pytz.timezone('Asia/Kolkata')
    print(f"\n🚀 Starting PCS Analysis")
    print(f"⏰ Time: {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Filter Criteria:")
    print(f"   - Minimum Pattern Strength: {min_pattern_strength}%")
    print(f"   - Focus on High Confidence: {focus_high_confidence}")
    print(f"   - Stocks to Scan: {max_stocks if max_stocks else 'All'}")
    print("━" * 60)

    scanner = ProfessionalPCSScanner()

    # Get stocks to scan
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    total_scanned = len(stocks_to_scan)
    results = []

    print(f"\n📈 Scanning {total_scanned} stocks...")

    for i, symbol in enumerate(stocks_to_scan, 1):
        clean_symbol = symbol.replace('.NS', '')

        try:
            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, min_volume_ratio=1.2)
            if not volume_ok:
                continue

            # Detect patterns
            config = {
                'rsi_min': 30,
                'rsi_max': 75,
                'adx_min': 20,
                'ma_support': True,
                'ma_type': 'SMA',
                'ma_tolerance': 3,
                'min_volume_ratio': 1.2,
                'volume_breakout_ratio': 2.0,
                'lookback_days': 20,
                'pattern_strength_min': min_pattern_strength,
                'pattern_filters': {
                    'current_day_breakout': True,
                    'cup_and_handle': True,
                    'flat_base': True,
                    'bump_and_run': True,
                    'rectangle_bottom': True,
                    'head_shoulders_bottom': True,
                    'double_bottom': True,
                    'three_rising_valleys': True,
                    'rounding_bottom': True,
                },
                'pattern_priority': 'All Patterns (Comprehensive)',
                'analysis_mode': 'Daily Only (V6.0 Style)',
                'enable_daily_analysis': True,
                'enable_weekly_validation': False,
            }

            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            # Get metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Calculate confidence and strength
            max_strength = max(p['strength'] for p in patterns)

            # Determine confidence
            if max_strength >= 85:
                confidence = 'HIGH'
            elif max_strength >= 70:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

            # Skip if focusing on high confidence only
            if focus_high_confidence and confidence != 'HIGH':
                continue

            # Get pattern types
            pattern_types = [p['type'] for p in patterns]
            has_current_breakout = any('Current Day' in pt for pt in pattern_types)

            result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'strength': max_strength,
                'confidence': confidence,
                'volume_ratio': volume_ratio,
                'patterns': ', '.join(pattern_types[:2]),  # First 2 patterns
                'current_breakout': has_current_breakout,
            }

            results.append(result)
            print(f"✅ [{i}/{total_scanned}] {clean_symbol:12} - {confidence:6} - {max_strength:.0f}% - {result['patterns'][:40]}")

        except Exception as e:
            print(f"⚠️  [{i}/{total_scanned}] {clean_symbol:12} - Error: {str(e)[:40]}")
            continue

    print("\n" + "━" * 60)
    print(f"\n📊 Analysis Complete!")
    print(f"   - Scanned: {total_scanned} stocks")
    print(f"   - Found: {len(results)} stocks meeting criteria")

    if results:
        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)

        print(f"\n✅ Top Results:")
        for i, r in enumerate(results[:10], 1):
            print(f"   {i}. {r['symbol']:10} - {r['confidence']:6} - {r['strength']:.0f}% - ₹{r['price']:.2f}")

    return results, total_scanned

def save_results_to_csv(results, filename=None):
    """Save results to CSV file"""
    if not results:
        return None

    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"/tmp/pcs_results_{timestamp}.csv"

    df = pd.DataFrame(results)
    df = df[['symbol', 'confidence', 'strength', 'price', 'rsi', 'adx', 'volume_ratio', 'patterns', 'current_breakout']]
    df.to_csv(filename, index=False)

    print(f"\n💾 Results saved to: {filename}")
    return filename

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("   NSE F&O PCS SCREENER - AUTOMATED ANALYSIS")
    print("="*60)

    # Run analysis with default parameters
    # Adjust these values as needed:
    # - min_pattern_strength: 70% is a good middle ground (higher = fewer stocks but higher quality)
    # - max_stocks: None for all stocks, or a number to limit
    # - focus_high_confidence: True to only show HIGH confidence stocks

    results, total_scanned = run_analysis(
        min_pattern_strength=70,
        max_stocks=None,  # Scan all stocks
        focus_high_confidence=False  # Include all confidence levels
    )

    # Save results to file
    csv_file = save_results_to_csv(results)

    # Send to Telegram if configured
    if results:
        telegram_message = format_telegram_message(results, total_scanned)
        print(f"\n📱 Telegram Message Preview:")
        print(f"   {telegram_message[:100]}...")

        telegram_sent = send_telegram_message(telegram_message)

        if not telegram_sent and TELEGRAM_BOT_TOKEN is None:
            print("\n⚠️  To enable Telegram notifications, set these environment variables:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")
    else:
        print("\nℹ️  No stocks met the filter criteria.")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            msg = "📊 PCS Analysis: No stocks met filter criteria today."
            send_telegram_message(msg)

    print("\n" + "="*60)
    print("✨ Analysis complete!")
    print("="*60 + "\n")

    return results

if __name__ == "__main__":
    main()
