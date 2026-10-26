#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Telegram Integration Script
Simplified version without TA library dependency
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import pytz
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Stock list to scan
STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'ULTRACEMCO.NS'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_dm = high.diff().where(high.diff() > 0, 0)
    minus_dm = (-low.diff()).where(-low.diff() > 0, 0)

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx

def get_stock_data(symbol, period="3mo"):
    """Fetch and analyze stock data"""
    try:
        print(f"  Fetching {symbol}...", end=' ', flush=True)
        data = yf.download(symbol, period=period, progress=False)

        if data is None or len(data) < 20:
            print("❌ Insufficient data")
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()

        macd, macd_signal, macd_hist = calculate_macd(data['Close'])
        data['MACD'] = macd
        data['MACD_Signal'] = macd_signal
        data['MACD_Hist'] = macd_hist

        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

        # Bollinger Bands
        data['BB_SMA'] = data['Close'].rolling(20).mean()
        data['BB_STD'] = data['Close'].rolling(20).std()
        data['BB_Upper'] = data['BB_SMA'] + (data['BB_STD'] * 2)
        data['BB_Lower'] = data['BB_SMA'] - (data['BB_STD'] * 2)

        return data
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}")
        return None

def analyze_stock(symbol, data):
    """Analyze stock and return metrics"""
    try:
        # Get latest values
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        current_macd = data['MACD'].iloc[-1]
        current_macd_signal = data['MACD_Signal'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]

        # Volume analysis
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Calculate score
        score = 0
        signals = []

        # RSI signals (optimal range 45-65)
        if 45 <= current_rsi <= 65:
            score += 20
            signals.append(f"Optimal RSI: {current_rsi:.1f}")
        elif 30 <= current_rsi <= 80:
            score += 10
            signals.append(f"Good RSI: {current_rsi:.1f}")

        # Trend signals
        if current_price > sma_20 > sma_50:
            score += 25
            signals.append("Strong uptrend (Price > SMA20 > SMA50)")
        elif current_price > sma_20:
            score += 15
            signals.append("Price above SMA20")

        # MACD signals
        if current_macd > current_macd_signal and current_macd > 0:
            score += 15
            signals.append("MACD bullish (above signal)")
        elif current_macd > current_macd_signal:
            score += 10
            signals.append("MACD above signal line")

        # ADX signals (trend strength)
        if current_adx >= 25:
            score += 15
            signals.append(f"Strong trend (ADX: {current_adx:.1f})")
        elif current_adx >= 20:
            score += 10
            signals.append(f"Moderate trend (ADX: {current_adx:.1f})")

        # Volume signals
        if volume_ratio >= 1.2:
            score += 10
            signals.append(f"High volume: {volume_ratio:.1f}x")

        return {
            'symbol': symbol.replace('.NS', ''),
            'price': current_price,
            'rsi': current_rsi,
            'adx': current_adx,
            'volume_ratio': volume_ratio,
            'score': min(score, 100),
            'signals': signals
        }
    except Exception as e:
        return None

def send_telegram_message(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if bot_token is None or chat_id is None:
        print("⚠️ Telegram credentials not configured.")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "<b>🔔 NSE F&O PCS Screener</b>\n\n❌ No stocks found meeting criteria."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S IST")

    message = f"<b>📈 NSE F&O PCS Screener Results</b>\n"
    message += f"<i>{current_time}</i>\n\n"
    message += f"<b>Found {len(results)} stocks with bullish signals</b>\n"
    message += "═" * 50 + "\n\n"

    for idx, result in enumerate(results[:10], 1):
        score = result['score']
        emoji = '🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'

        message += f"<b>{idx}. {result['symbol']}</b> {emoji} [{score:.0f}/100]\n"
        message += f"Price: ₹{result['price']:.2f} | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"Volume: {result['volume_ratio']:.1f}x\n"

        for signal in result['signals']:
            message += f"  • {signal}\n"
        message += "─" * 50 + "\n\n"

    if len(results) > 10:
        message += f"<i>...and {len(results) - 10} more stocks</i>\n"

    message += "\n<b>Disclaimer:</b> Not financial advice. Always do your own research."

    return message

def main():
    """Main execution"""
    print("=" * 60)
    print("NSE F&O PCS Screener - Telegram Alert")
    print("=" * 60)
    print()

    print("🚀 Starting stock screening...\n")

    results = []
    for idx, symbol in enumerate(STOCKS, 1):
        print(f"[{idx}/{len(STOCKS)}]", end=' ')

        data = get_stock_data(symbol)
        if data is None:
            continue

        analysis = analyze_stock(symbol, data)
        if analysis and analysis['score'] >= 40:
            results.append(analysis)
            print(f"✅ Score: {analysis['score']:.0f}")
        else:
            print("⏭️ Skipped")

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n✅ Screening complete. Found {len(results)} qualifying stocks.\n")

    # Format message
    message = format_telegram_message(results)

    # Print to console
    print("📋 Results Summary:")
    print(message)
    print("\n" + "=" * 60)

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n📤 Sending to Telegram...")
        if send_telegram_message(message, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID):
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
    else:
        print("\n⚠️ Telegram not configured.")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")

    print("=" * 60)

if __name__ == "__main__":
    main()
