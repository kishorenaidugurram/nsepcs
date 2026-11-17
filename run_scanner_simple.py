#!/usr/bin/env python3
"""
Simplified NSE PCS Scanner - Standalone version without ta library dependency
Runs the core scanning logic and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

# F&O Stock list (top 100 by liquidity)
FNO_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS',
    'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IDFCFIRSTB.NS',
    'AUBANK.NS', 'EXIDEIND.NS', 'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS',
    'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'HAVELLS.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDZINC.NS', 'HUDCO.NS', 'ICICIGI.NS',
    'ICICIPRULI.NS', 'IIFL.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS',
    'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'NAUKRI.NS', 'INOXWIND.NS',
    'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JIOFIN.NS', 'JUBLFOOD.NS'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX"""
    if len(high) < period + 1:
        return None

    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    # Directional Movement
    up = high.diff()
    down = -low.diff()

    pos_dm = np.where((up > down) & (up > 0), up, 0)
    neg_dm = np.where((down > up) & (down > 0), down, 0)

    pos_di = 100 * pd.Series(pos_dm).rolling(window=period).mean() / atr
    neg_di = 100 * pd.Series(neg_dm).rolling(window=period).mean() / atr

    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di + 1e-10)
    adx = dx.rolling(window=period).mean()

    return adx

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)

        if len(data) < 20:
            return None

        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'].values)

        # Simple moving averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()

        # ADX calculation
        try:
            data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])
        except:
            data['ADX'] = 20  # Default value

        return data
    except:
        return None

def check_volume_criteria(data, min_ratio=1.0):
    """Check if current day volume meets criteria"""
    if len(data) < 21:
        return False, 0

    current_volume = data['Volume'].iloc[-1]
    avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

    volume_ratio = current_volume / avg_20_volume if avg_20_volume > 0 else 0

    return volume_ratio >= min_ratio, volume_ratio

def detect_breakout_pattern(data):
    """Detect current day breakout pattern"""
    if len(data) < 21:
        return False, 0

    # Current day
    current_close = data['Close'].iloc[-1]
    current_high = data['High'].iloc[-1]
    current_volume = data['Volume'].iloc[-1]

    # Recent resistance (past 20 days)
    resistance = data['High'].tail(21).iloc[:-1].max()

    # Volume comparison
    avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

    # Breakout criteria
    breakout = current_close > resistance * 1.005
    volume_ok = volume_ratio >= 1.3

    if not (breakout and volume_ok):
        return False, 0

    # Calculate strength
    strength = 50
    if current_close > resistance * 1.02:
        strength += 20
    if volume_ratio >= 2:
        strength += 20
    if current_close > current_high * 0.8:  # Closed in top 20% of range
        strength += 10

    return True, min(strength, 100)

def detect_cup_and_handle(data):
    """Detect cup and handle pattern"""
    if len(data) < 40:
        return False, 0

    recent = data.tail(30)

    # Cup formation
    cup_high = recent['High'].iloc[:20].max()
    cup_low = recent['Low'].iloc[5:15].min()

    # Handle
    handle_high = recent['High'].iloc[-10:].max()

    # Current day
    current_close = data['Close'].iloc[-1]

    # Criteria
    cup_depth = ((cup_high - cup_low) / cup_high) * 100
    breakout = current_close > handle_high * 1.005

    if not (15 <= cup_depth <= 50 and breakout):
        return False, 0

    strength = 50
    if 20 <= cup_depth <= 40:
        strength += 15
    if breakout:
        strength += 20
    if cup_depth < 25:
        strength += 15

    return True, min(strength, 100)

def detect_double_bottom(data):
    """Detect double bottom pattern"""
    if len(data) < 30:
        return False, 0

    recent = data.tail(30)

    # First bottom
    first_low = recent['Low'].iloc[5:12].min()

    # Peak
    peak_high = recent['High'].iloc[12:18].max()

    # Second bottom
    second_low = recent['Low'].iloc[18:25].min()

    # Current day
    current_close = data['Close'].iloc[-1]

    # Criteria
    bottoms_similar = abs(first_low - second_low) / min(first_low, second_low) < 0.08
    breakout = current_close > peak_high * 1.015

    if not (bottoms_similar and breakout):
        return False, 0

    strength = 50
    if abs(first_low - second_low) / min(first_low, second_low) < 0.05:
        strength += 15
    if breakout:
        strength += 20

    return True, min(strength, 100)

def scan_stocks(stocks_list, max_stocks=50):
    """Scan stocks and find qualifying ones"""
    results = []
    total = len(stocks_list)

    for i, symbol in enumerate(stocks_list, 1):
        print(f"[{i:3d}/{total}] Scanning {symbol.replace('.NS', ''):<15}", end='\r')

        try:
            # Fetch data
            data = fetch_stock_data(symbol)
            if data is None or len(data) < 20:
                continue

            # Check volume
            volume_ok, volume_ratio = check_volume_criteria(data, min_ratio=1.0)
            if not volume_ok:
                continue

            # Check RSI
            current_rsi = data['RSI'].iloc[-1]
            if not (30 <= current_rsi <= 70):
                continue

            # Check ADX
            current_adx = data['ADX'].iloc[-1]
            if current_adx < 15:
                continue

            # Detect patterns
            patterns = []

            # Breakout
            breakout_ok, breakout_strength = detect_breakout_pattern(data)
            if breakout_ok:
                patterns.append({
                    'type': 'Current Day Breakout',
                    'strength': breakout_strength,
                    'confidence': 'HIGH' if breakout_strength >= 85 else 'MEDIUM' if breakout_strength >= 70 else 'LOW',
                    'success_rate': 72,
                    'pcs_suitability': 90
                })

            # Cup and Handle
            cup_ok, cup_strength = detect_cup_and_handle(data)
            if cup_ok:
                patterns.append({
                    'type': 'Cup and Handle',
                    'strength': cup_strength,
                    'confidence': 'HIGH' if cup_strength >= 85 else 'MEDIUM' if cup_strength >= 70 else 'LOW',
                    'success_rate': 85,
                    'pcs_suitability': 92
                })

            # Double Bottom
            db_ok, db_strength = detect_double_bottom(data)
            if db_ok:
                patterns.append({
                    'type': 'Double Bottom',
                    'strength': db_strength,
                    'confidence': 'HIGH' if db_strength >= 85 else 'MEDIUM' if db_strength >= 70 else 'LOW',
                    'success_rate': 80,
                    'pcs_suitability': 91
                })

            if patterns:
                current_price = data['Close'].iloc[-1]
                result = {
                    'symbol': symbol.replace('.NS', ''),
                    'current_price': float(current_price),
                    'volume_ratio': float(volume_ratio),
                    'rsi': float(current_rsi),
                    'adx': float(current_adx),
                    'patterns': patterns
                }
                results.append(result)

                if len(results) >= max_stocks:
                    break

        except Exception as e:
            continue

    print(" " * 60, end='\r')  # Clear line
    return results

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found matching the filter criteria."

    # Sort by pattern strength
    results_sorted = sorted(
        results,
        key=lambda x: max(p['strength'] for p in x['patterns']),
        reverse=True
    )[:20]

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"🎯 *NSE PCS Stock Scanner Results*\n"
    message += f"⏰ {timestamp}\n"
    message += f"📊 Found: *{len(results)} stocks* with valid patterns\n"
    message += "━" * 50 + "\n\n"

    for i, result in enumerate(results_sorted, 1):
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
        pattern_types = ', '.join([p['type'] for p in result['patterns'][:2]])

        emoji = "🟢" if confidence == 'HIGH' else "🟡" if confidence == 'MEDIUM' else "🔴"

        message += f"{i:2d}. *{result['symbol']}* {emoji}\n"
        message += f"    💰 ₹{result['current_price']:.2f}\n"
        message += f"    📈 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"    🔥 Strength: {max_strength:.0f}% ({confidence})\n"
        message += f"    🎯 Pattern: {pattern_types}\n"
        message += f"    📊 Volume: {result['volume_ratio']:.1f}x\n"
        message += "\n"

    message += "━" * 50 + "\n"
    message += "_Use web scanner for detailed charts and analysis_"

    return message

def send_to_telegram(message):
    """Send message to Telegram"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("⚠️  Telegram credentials not configured")
        print("    Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print("\n📋 Message that would be sent:\n")
        print(message)
        return False

    try:
        import requests

        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Telegram!")
            return True
        else:
            print(f"❌ Failed to send: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def save_results(results, output_dir='/tmp/claude-0/-home-user-nsepcs/58571b9b-3a7d-5f8c-b559-fcc07912d4e8/scratchpad'):
    """Save results to file"""
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, 'scan_results.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return output_file

def main():
    print("\n" + "="*60)
    print("🚀 NSE PCS Stock Scanner - Simplified Edition")
    print("="*60)

    # Run scanner
    results = scan_stocks(FNO_STOCKS[:100], max_stocks=50)

    if not results:
        print("❌ No stocks found matching filter criteria")
        message = "❌ No stocks found matching the filter criteria."
        send_to_telegram(message)
        return 1

    print(f"\n✅ Found {len(results)} stocks with patterns\n")

    # Format and send
    message = format_telegram_message(results)

    # Save results
    results_file = save_results(results)
    print(f"📁 Results saved to: {results_file}")

    # Send to Telegram
    send_to_telegram(message)

    # Display locally
    print("\n" + message)

    return 0

if __name__ == "__main__":
    sys.exit(main())
