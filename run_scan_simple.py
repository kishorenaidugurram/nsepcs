#!/usr/bin/env python3
"""
Simplified PCS Scanner - runs screening without external dependencies beyond core ones
Sends results to Telegram
"""

import os
import json
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import warnings
warnings.filterwarnings('ignore')

# NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS',
]

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi[-1] if len(rsi) > 0 else None

def calculate_adx(high, low, close, period=14):
    """Calculate ADX indicator (simplified)"""
    if len(high) < period * 2:
        return None

    # True Range
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))[1:]
    atr = np.mean(tr[-period:])

    # For simplification, return a normalized value based on volatility
    return min(100, (atr / close[-1] * 1000)) if atr > 0 else 20

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data.empty or len(data) < 20:
            return None
        return data
    except:
        return None

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def analyze_stock(symbol):
    """Analyze a single stock"""
    try:
        # Fetch data
        data = fetch_stock_data(symbol)
        if data is None:
            return None

        # Calculate indicators
        close = data['Close'].values
        high = data['High'].values
        low = data['Low'].values
        volume = data['Volume'].values

        rsi = calculate_rsi(close)
        adx = calculate_adx(high, low, close)
        current_price = close[-1]

        # Volume analysis
        avg_volume = np.mean(volume[-20:])
        current_volume = volume[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # Simple pattern detection: check if RSI is in good range (45-65 is sweet spot)
        if rsi is None or adx is None:
            return None

        # Create a simple quality score
        score = 0
        if 45 <= rsi <= 65:
            score += 40
        elif 40 <= rsi <= 70:
            score += 30

        if adx >= 20:
            score += 30

        if volume_ratio >= 1.2:
            score += 30

        # Recent uptrend check (last 5 days close > open)
        uptrend_days = sum(1 for i in range(-5, 0) if data['Close'].iloc[i] > data['Open'].iloc[i])
        score += uptrend_days * 2

        if score < 50:  # Skip low scores
            return None

        return {
            'symbol': symbol,
            'current_price': float(current_price),
            'rsi': float(rsi),
            'adx': float(adx),
            'volume_ratio': float(volume_ratio),
            'score': score,
            'uptrend_days': uptrend_days
        }
    except Exception as e:
        return None

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found matching the criteria."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
    message += f"<b>Time:</b> {current_time}\n"
    message += f"<b>Stocks Found:</b> {len(results)}\n"
    message += "─" * 40 + "\n\n"

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    for i, result in enumerate(results[:20], 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        score = result['score']

        message += f"<b>{i}. {symbol}</b>\n"
        message += f"   💰 ₹{price:.2f} | RSI: {rsi:.1f} | ADX: {adx:.1f}\n"
        message += f"   🎯 Score: {score:.0f}/100 | Vol: {result['volume_ratio']:.1f}x\n\n"

    if len(results) > 20:
        message += f"\n... and {len(results) - 20} more stocks"

    return message

def main():
    """Main function"""
    print("=" * 60)
    print("NSE F&O PCS Screener - Automated Scan")
    print("=" * 60)
    print(f"📊 Starting scan of {len(COMPLETE_NSE_FO_UNIVERSE[:50])} stocks...")

    results = []
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:50]  # Limit to first 50 for speed

    for i, symbol in enumerate(stocks_to_scan):
        print(f"[{i+1:2d}/{len(stocks_to_scan)}] {symbol.replace('.NS', ''):15s}", end='\r')
        result = analyze_stock(symbol)
        if result:
            results.append(result)

    print(f"\n\n✅ Scan complete! Found {len(results)} stocks meeting criteria.\n")

    if results:
        # Display top results
        results.sort(key=lambda x: x['score'], reverse=True)
        print("📋 Top 10 Results:")
        print("-" * 60)
        for i, r in enumerate(results[:10], 1):
            print(f"{i:2d}. {r['symbol']:15s} | ₹{r['current_price']:8.2f} | "
                  f"RSI: {r['rsi']:5.1f} | ADX: {r['adx']:5.1f} | Score: {r['score']:3.0f}")

        # Format and send to Telegram
        telegram_msg = format_telegram_message(results)

        print("\n📤 Sending to Telegram...")
        if send_to_telegram(telegram_msg):
            print("✅ Results sent to Telegram successfully!")
        else:
            print("⚠️  Could not send to Telegram")
            print("\nSet Telegram credentials:")
            print("  export TELEGRAM_BOT_TOKEN='your_bot_token'")
            print("  export TELEGRAM_CHAT_ID='your_chat_id'")

        # Save results
        results_file = '/tmp/pcs_scan_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")
    else:
        print("No stocks found meeting the filter criteria")

if __name__ == '__main__':
    main()
