#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - Telegram Integration
Runs the stock scanner without complex dependencies
"""

import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import warnings
warnings.filterwarnings('ignore')

# NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS'
]

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def calculate_rsi(prices, period=14):
    """Calculate RSI using numpy"""
    delta = np.diff(prices)
    seed = delta[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta_up = delta[i] if delta[i] > 0 else 0
        delta_down = -delta[i] if delta[i] < 0 else 0
        up = (up * (period - 1) + delta_up) / period
        down = (down * (period - 1) + delta_down) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def simple_pattern_detection(data):
    """Detect simple bullish patterns"""
    if len(data) < 20:
        return []

    patterns = []
    close = data['Close'].values
    high = data['High'].values
    low = data['Low'].values
    volume = data['Volume'].values

    # Pattern 1: Breakout from consolidation (last 20 days)
    recent_high = high[-20:].max()
    recent_low = low[-20:].min()
    current_close = close[-1]
    current_high = high[-1]
    current_volume = volume[-1]
    avg_volume = volume[-20:].mean()

    # Consolidation range (tight)
    consolidation_range = ((recent_high - recent_low) / recent_low) * 100
    if consolidation_range < 12 and current_close > recent_high * 1.005:
        # Breakout detected
        if current_volume > avg_volume * 1.5:
            patterns.append({
                'type': 'Consolidation Breakout',
                'strength': 'High' if current_volume > avg_volume * 2 else 'Medium',
                'score': 70 if current_volume > avg_volume * 2 else 60
            })

    # Pattern 2: Higher Lows (bullish trend)
    if len(data) >= 10:
        recent_lows = []
        for i in range(-10, -1, 3):
            segment_low = low[i:i+3].min()
            recent_lows.append(segment_low)

        if len(recent_lows) >= 2:
            if all(recent_lows[i] < recent_lows[i+1] for i in range(len(recent_lows)-1)):
                patterns.append({
                    'type': 'Higher Lows Trend',
                    'strength': 'Medium',
                    'score': 65
                })

    # Pattern 3: RSI Oversold Bounce
    rsi = calculate_rsi(close)
    if len(rsi) > 0:
        current_rsi = rsi[-1]
        if 30 <= current_rsi <= 50:  # Oversold but recovering
            if rsi[-2] < rsi[-1]:  # RSI increasing
                patterns.append({
                    'type': 'RSI Bounce',
                    'strength': 'Medium',
                    'score': 55,
                    'rsi': round(current_rsi, 2)
                })

    # Pattern 4: Momentum (Volume increase)
    vol_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    if vol_ratio > 1.5:
        patterns.append({
            'type': 'Volume Surge',
            'strength': 'High' if vol_ratio > 2 else 'Medium',
            'score': 70 if vol_ratio > 2 else 60,
            'volume_ratio': round(vol_ratio, 2)
        })

    return patterns

def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Note: Telegram credentials not configured")
        print("   To enable Telegram notifications, set:")
        print("   export TELEGRAM_BOT_TOKEN='your-bot-token'")
        print("   export TELEGRAM_CHAT_ID='your-chat-id'")
        print()
        print("   For now, here are the results:")
        print("   " + "\n   ".join(message.split("\n")[:10]))
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False

def format_results_for_telegram(results: list, total_stocks: int) -> str:
    """Format scanner results for Telegram message"""
    if not results:
        return f"<b>📊 NSE F&O PCS Scanner Results</b>\n\n❌ No stocks found meeting the criteria\n\n<i>Scanned {total_stocks} stocks at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>"

    message = f"<b>📊 NSE F&O PCS Scanner Results</b>\n"
    message += f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>\n"
    message += f"<i>Stocks found: {len(results)} out of {total_stocks} scanned</i>\n\n"

    # Sort by pattern count and score
    sorted_results = sorted(
        results,
        key=lambda x: (len(x.get('patterns', [])), sum(p.get('score', 0) for p in x.get('patterns', []))),
        reverse=True
    )

    for idx, stock in enumerate(sorted_results[:15], 1):  # Limit to top 15 due to message length
        symbol = stock['symbol'].replace('.NS', '')
        patterns = stock.get('patterns', [])
        price = stock.get('latest_price', 'N/A')
        avg_score = sum(p.get('score', 0) for p in patterns) / len(patterns) if patterns else 0

        pattern_str = ", ".join([p['type'][:12] for p in patterns[:2]])

        message += f"<b>{idx}. {symbol}</b> - ₹{price}\n"
        message += f"   📈 Patterns: {pattern_str}\n"
        message += f"   📊 Score: {avg_score:.0f}/100 ({len(patterns)} pattern{'s' if len(patterns) != 1 else ''})\n\n"

    if len(results) > 15:
        message += f"<i>... and {len(results) - 15} more stocks</i>\n"

    message += "\n<i>Run the full scan for detailed analysis</i>"

    return message

def run_scanner(max_stocks: int = 50) -> dict:
    """Run the simplified PCS scanner"""
    print(f"🔍 Starting Simplified PCS Scanner...")
    print(f"   Analyzing: {len(COMPLETE_NSE_FO_UNIVERSE[:max_stocks])} stocks")
    print()

    results = []
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    for idx, symbol in enumerate(stocks_to_scan, 1):
        try:
            stock_name = symbol.replace('.NS', '')
            print(f"[{idx:2d}/{max_stocks}] {stock_name:10s} ", end='', flush=True)

            # Get stock data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="3mo")

            if data is None or len(data) < 20:
                print("⏭️ Skip (insufficient data)")
                continue

            # Detect patterns
            patterns = simple_pattern_detection(data)

            if patterns:
                latest_price = data['Close'].iloc[-1]
                results.append({
                    'symbol': symbol,
                    'latest_price': round(latest_price, 2),
                    'patterns': patterns,
                    'num_patterns': len(patterns)
                })

                avg_score = sum(p.get('score', 0) for p in patterns) / len(patterns)
                print(f"✅ {len(patterns)} pattern(s) | Score: {avg_score:.0f}")
            else:
                print("✗")

        except Exception as e:
            print(f"❌ Error: {str(e)[:25]}")
            continue

    print()
    print(f"✅ Scan complete: Found {len(results)} stocks with bullish patterns")

    return {
        'results': results,
        'total_scanned': len(stocks_to_scan),
        'timestamp': datetime.now()
    }

def main():
    """Main function"""
    print("=" * 70)
    print(" " * 15 + "NSE F&O PCS Scanner - Telegram Integration")
    print("=" * 70)
    print()

    # Run scanner
    scan_data = run_scanner(max_stocks=50)

    # Format results for Telegram
    results = scan_data['results']
    total_scanned = scan_data['total_scanned']

    message = format_results_for_telegram(results, total_scanned)

    # Send to Telegram
    print()
    print("📤 Sending results to Telegram...")
    success = send_telegram_message(message)

    if not success and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print()
        print("❌ Failed to send Telegram message")
        return 1

    print()
    if results:
        print("📋 Top Stocks Found:")
        for i, stock in enumerate(sorted(results, key=lambda x: sum(p.get('score', 0) for p in x.get('patterns', [])), reverse=True)[:5], 1):
            symbol = stock['symbol'].replace('.NS', '')
            patterns = stock.get('patterns', [])
            score = sum(p.get('score', 0) for p in patterns) / len(patterns) if patterns else 0
            print(f"   {i}. {symbol:10s} - Score: {score:.0f} - ₹{stock['latest_price']}")
    else:
        print("No stocks found matching the criteria.")

    print()
    print("✅ Scanner completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
