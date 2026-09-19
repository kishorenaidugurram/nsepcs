#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Standalone implementation without streamlit dependency
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default stock list for F&O scanning
DEFAULT_STOCKS = [
    'NIFTY50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK',
    'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI',
    'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA', 'TATAMOTORS', 'ADANIENT',
    'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN'
]

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured")
        print(f"  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def calculate_rsi(data, window=14):
    """Calculate RSI indicator"""
    close = data['Close']
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(data, window=14):
    """Calculate ADX indicator"""
    high = data['High']
    low = data['Low']
    close = data['Close']

    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(window=window).mean()
    plus_di = 100 * (plus_dm.rolling(window=window).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=window).mean() / atr)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=window).mean()

    return adx

def calculate_sma(data, window=20):
    """Calculate Simple Moving Average"""
    return data['Close'].rolling(window=window).mean()

def calculate_ema(data, window=20):
    """Calculate Exponential Moving Average"""
    return data['Close'].ewm(span=window, adjust=False).mean()

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands"""
    sma = data['Close'].rolling(window=window).mean()
    std = data['Close'].rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, sma, lower

def get_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS'):
            symbol = f"{symbol}.NS"

        data = yf.download(symbol, period=period, progress=False, threads=False)

        if data.empty or len(data) < 30:
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data)
        data['ADX'] = calculate_adx(data)
        data['SMA_20'] = calculate_sma(data, 20)
        data['SMA_50'] = calculate_sma(data, 50)
        data['EMA_20'] = calculate_ema(data, 20)

        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(data)
        data['BB_upper'] = bb_upper
        data['BB_middle'] = bb_middle
        data['BB_lower'] = bb_lower

        return data
    except Exception as e:
        print(f"   Error: {e}")
        return None

def analyze_stock(symbol, data):
    """Analyze stock for PCS opportunities"""
    try:
        if data is None or len(data) < 2:
            return None

        # Get latest values
        latest = data.iloc[-1]
        current_price = latest['Close']
        current_rsi = latest['RSI']
        current_adx = latest['ADX']
        current_volume = latest['Volume']

        # Get average volume from last 20 days
        avg_volume = data['Volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        # Check filters
        if pd.isna(current_rsi) or pd.isna(current_adx):
            return None

        # Filter 1: RSI between 30-75
        if not (30 <= current_rsi <= 75):
            return None

        # Filter 2: ADX > 20
        if current_adx < 20:
            return None

        # Filter 3: Volume ratio > 1.2
        if volume_ratio < 1.2:
            return None

        # Filter 4: Price support analysis
        sma_20 = latest['SMA_20']
        ema_20 = latest['EMA_20']

        if pd.isna(sma_20) or pd.isna(ema_20):
            return None

        # Check if price is near support
        support_distance = min(abs(current_price - sma_20), abs(current_price - ema_20))
        support_pct = (support_distance / current_price) * 100

        if support_pct > 3:  # Price is too far from support (>3%)
            return None

        # Calculate trend strength
        close_prices = data['Close'].tail(20).values
        trend_strength = ((close_prices[-1] - close_prices[0]) / close_prices[0]) * 100

        # Determine confidence
        if current_rsi < 50 and current_adx > 30:
            confidence = 'HIGH'
            strength = min(100, 65 + abs(trend_strength))
        elif current_rsi < 60:
            confidence = 'MEDIUM'
            strength = 70 + abs(trend_strength)
        else:
            confidence = 'LOW'
            strength = 60 + abs(trend_strength)

        strength = min(100, max(50, strength))

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': current_rsi,
            'adx': current_adx,
            'volume_ratio': volume_ratio,
            'confidence': confidence,
            'strength': strength,
            'trend': trend_strength,
            'data': data
        }
    except Exception as e:
        return None

def run_scan():
    """Run the complete scan"""
    print("🚀 Starting NSE F&O PCS Scanner...")
    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.now(ist)
    print(f"⏰ Time: {scan_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print()

    results = []

    print(f"📊 Scanning {len(DEFAULT_STOCKS)} stocks...\n")

    for i, symbol in enumerate(DEFAULT_STOCKS, 1):
        print(f"[{i:2d}/{len(DEFAULT_STOCKS)}] Analyzing {symbol:15s}...", end=" ", flush=True)

        # Get data
        data = get_stock_data(symbol, period="3mo")

        if data is None:
            print("⏭️  (No data)")
            continue

        # Analyze
        result = analyze_stock(symbol, data)

        if result is None:
            print("⏭️  (Filters)")
            continue

        results.append(result)
        print(f"✅ ({result['strength']:.0f}% {result['confidence']})")

    print()

    if not results:
        print("❌ No stocks found meeting criteria")
        send_telegram_message("❌ NSE F&O PCS Scan Complete\n\nNo stocks matched the filter criteria today.")
        return

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print(f"✅ Found {len(results)} stocks with confirmed patterns!")
    print()
    print("=" * 90)
    print("SCAN RESULTS - STOCKS MEETING PCS CRITERIA")
    print("=" * 90)
    print()

    for i, stock in enumerate(results, 1):
        print(f"{i:2d}. {stock['symbol']:12s} | Strength: {stock['strength']:5.0f}% | Confidence: {stock['confidence']:6s} | Price: ₹{stock['price']:8.2f} | RSI: {stock['rsi']:5.1f} | ADX: {stock['adx']:5.1f}")

    print()
    print("=" * 90)
    print()

    # Prepare Telegram message
    telegram_message = f"""<b>🚀 NSE F&O PCS SCAN RESULTS</b>

<b>📊 Scan Summary</b>
📅 Time: {scan_time.strftime('%Y-%m-%d %H:%M IST')}
✅ Stocks Found: {len(results)}
🏆 High Confidence: {sum(1 for r in results if r['confidence'] == 'HIGH')}
🟡 Medium Confidence: {sum(1 for r in results if r['confidence'] == 'MEDIUM')}

<b>📋 Stocks Sorted by Strength</b>
"""

    for i, stock in enumerate(results[:15], 1):  # Send top 15
        telegram_message += f"\n{i:2d}. <b>{stock['symbol']}</b> - {stock['strength']:.0f}% ({stock['confidence']})"
        telegram_message += f"\n    Price: ₹{stock['price']:.2f} | RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f} | Vol: {stock['volume_ratio']:.1f}x\n"

    if len(results) > 15:
        telegram_message += f"\n... and <b>{len(results) - 15} more stocks</b>"

    telegram_message += "\n\n<i>PCS = Put Credit Spread | Filters: RSI 30-75, ADX>20, Volume>1.2x</i>"

    # Send to Telegram
    print("📤 Sending results to Telegram...")
    send_telegram_message(telegram_message)

    print("✅ Scan complete!")

if __name__ == "__main__":
    run_scan()
