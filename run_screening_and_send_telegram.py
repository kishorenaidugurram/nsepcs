#!/usr/bin/env python3
"""
Standalone Stock Screening Script with Telegram Notification
Runs the NSE F&O PCS screening with default parameters and sends results to Telegram
"""

import sys
import os
import time
import asyncio
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Try importing ta, if fails use numpy-based calculations
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False

# Import from streamlit_app
try:
    from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
except ImportError as e:
    print(f"Error importing from streamlit_app: {e}")
    # Define stocks here as fallback
    COMPLETE_NSE_FO_UNIVERSE = []

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter parameters (matching Streamlit defaults)
DEFAULT_FILTERS = {
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
    'pattern_priority': 'All Patterns (Comprehensive)',
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
}


def calculate_rsi(prices, period=14):
    """Calculate RSI without ta library"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = 100 - 100 / (1 + rs)

    rsis = [rsi]
    for delta in deltas[period+1:]:
        if delta > 0:
            up = (up * (period - 1) + delta) / period
            down = (down * (period - 1)) / period
        else:
            up = (up * (period - 1)) / period
            down = (down * (period - 1) - delta) / period

        rs = up / down if down != 0 else 0
        rsi = 100 - 100 / (1 + rs)
        rsis.append(rsi)

    return rsis[-1] if rsis else 50


def calculate_adx(high, low, close, period=14):
    """Calculate ADX without ta library (simplified)"""
    try:
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]

        # Calculate DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # DI calculation (simplified)
        di_plus = (plus_dm.rolling(window=period).mean() / atr * 100).iloc[-1]
        di_minus = (minus_dm.rolling(window=period).mean() / atr * 100).iloc[-1]

        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus

        adx = 100 if di_sum == 0 else 100 * di_diff / di_sum
        return min(max(adx, 0), 100)  # Clamp between 0-100
    except:
        return 50  # Default value


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False, timeout=10)
        if data.empty or len(data) < 30:
            return None
        return data
    except Exception as e:
        return None


def run_screening(max_stocks=None):
    """Run screening analysis on F&O stocks"""
    if not COMPLETE_NSE_FO_UNIVERSE:
        print("❌ No stocks available for screening")
        return []

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    print(f"\n📊 Starting screening on {len(stocks_to_scan)} stocks...")
    print(f"⚙️ Filter criteria: Pattern Strength Min = {DEFAULT_FILTERS['pattern_strength_min']}")

    try:
        scanner = ProfessionalPCSScanner()
    except:
        print("⚠️ ProfessionalPCSScanner not available, using basic analysis...")
        scanner = None

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(analyze_stock, symbol, scanner): symbol
            for symbol in stocks_to_scan
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            symbol = futures[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                print(f"✓ {completed}/{len(stocks_to_scan)}", end='\r')
            except Exception as e:
                pass

    print(f"\n✅ Screening complete. Found {len(results)} stocks with valid patterns.\n")

    return results


def analyze_stock(symbol, scanner):
    """Analyze a single stock"""
    try:
        # Fetch data
        data = fetch_stock_data(symbol)
        if data is None:
            return None

        # Get current prices and indicators
        current_price = data['Close'].iloc[-1]

        # Calculate RSI
        if HAS_TA:
            try:
                current_rsi = ta.momentum.rsi(data['Close'], window=14).iloc[-1]
            except:
                current_rsi = calculate_rsi(data['Close'].values, period=14)
        else:
            current_rsi = calculate_rsi(data['Close'].values, period=14)

        # Calculate ADX
        if HAS_TA:
            try:
                current_adx = ta.trend.adx(data['High'], data['Low'], data['Close'], window=14).iloc[-1]
            except:
                current_adx = calculate_adx(data['High'], data['Low'], data['Close'], period=14)
        else:
            current_adx = calculate_adx(data['High'], data['Low'], data['Close'], period=14)

        # Volume ratio
        avg_volume_20 = data['Volume'].tail(20).mean()
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0

        # Detect patterns
        if scanner:
            patterns = scanner.detect_patterns(data, symbol, DEFAULT_FILTERS)
        else:
            patterns = []

        if not patterns:
            return None

        # Filter by pattern strength
        strong_patterns = [
            p for p in patterns
            if p['strength'] >= DEFAULT_FILTERS['pattern_strength_min']
        ]

        if not strong_patterns:
            return None

        return {
            'symbol': symbol,
            'clean_symbol': symbol.replace('.NS', '').replace('^', ''),
            'current_price': current_price,
            'volume_ratio': volume_ratio,
            'rsi': current_rsi,
            'adx': current_adx,
            'patterns': strong_patterns,
            'max_strength': max(p['strength'] for p in strong_patterns)
        }

    except Exception as e:
        return None


def format_results_for_telegram(results):
    """Format screening results for Telegram message"""
    if not results:
        return "❌ No stocks found meeting the filter criteria."

    # Sort by max pattern strength
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""
🎯 *NSE F&O PCS Screening Results*
━━━━━━━━━━━━━━━━━━━━━━━
📅 {current_time}
✅ Stocks Found: {len(results)}

*Filter Criteria:*
• Pattern Strength Min: {DEFAULT_FILTERS['pattern_strength_min']}
• RSI Range: {DEFAULT_FILTERS['rsi_min']}-{DEFAULT_FILTERS['rsi_max']}
• ADX Min: {DEFAULT_FILTERS['adx_min']}

━━━━━━━━━━━━━━━━━━━━━━━
*Top Results:*
"""

    for i, result in enumerate(results[:15], 1):
        symbol = result['clean_symbol']
        price = result['current_price']
        strength = result['max_strength']
        patterns_count = len(result['patterns'])

        # Confidence level
        if strength >= 85:
            confidence = "🟢 HIGH"
        elif strength >= 70:
            confidence = "🟡 MED"
        else:
            confidence = "🔴 LOW"

        message += f"\n{i}. *{symbol}* - ₹{price:.2f}"
        message += f"\n   Strength: {strength:.0f}% {confidence}"
        message += f"\n   Patterns: {patterns_count} | RSI: {result['rsi']:.0f} | Vol: {result['volume_ratio']:.1f}x"

    if len(results) > 15:
        message += f"\n\n... and {len(results) - 15} more stocks"

    message += "\n━━━━━━━━━━━━━━━━━━━━━━━"
    message += f"\n\n📊 Full List: Check CSV export for detailed analysis"

    return message


async def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not configured.")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    try:
        from telegram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        print("✅ Message sent to Telegram successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False


def export_to_csv(results, filename='screening_results.csv'):
    """Export results to CSV"""
    if not results:
        print("No results to export")
        return

    # Create summary data
    summary_data = []
    for result in results:
        max_strength = result['max_strength']

        summary_data.append({
            'Symbol': result['clean_symbol'],
            'Current Price': result['current_price'],
            'Volume Ratio': result['volume_ratio'],
            'RSI': result['rsi'],
            'ADX': result['adx'],
            'Pattern Strength': max_strength,
            'Confidence': 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW',
            'Pattern Count': len(result['patterns']),
            'Top Pattern': result['patterns'][0]['type'] if result['patterns'] else 'N/A'
        })

    df = pd.DataFrame(summary_data)
    df = df.sort_values('Pattern Strength', ascending=False)
    df.to_csv(filename, index=False)
    print(f"✅ Results exported to {filename}")

    return df


def main():
    """Main execution function"""
    print("\n" + "="*50)
    print("🚀 NSE F&O PCS Screener - Batch Mode")
    print("="*50)

    # Run screening
    results = run_screening(max_stocks=None)

    if results:
        # Export to CSV
        df = export_to_csv(results, '/tmp/nsepcs_screening_results.csv')
        print(f"\n📊 Screening Summary:")
        print(f"   Total Stocks Analyzed: {len(COMPLETE_NSE_FO_UNIVERSE)}")
        print(f"   Stocks Meeting Criteria: {len(results)}")
        print(f"   Success Rate: {len(results)/len(COMPLETE_NSE_FO_UNIVERSE)*100:.1f}%")

        # Format and send Telegram message
        message = format_results_for_telegram(results)
        print(f"\n📱 Telegram Message:\n{message}")

        # Send to Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            asyncio.run(send_telegram_message(message))
        else:
            print("\n⚠️ Telegram credentials not configured.")
            print("To enable Telegram notifications, set:")
            print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")
    else:
        print("❌ No stocks found meeting the filter criteria.")


if __name__ == "__main__":
    main()
